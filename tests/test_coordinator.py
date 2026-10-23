"""Coordinator regression tests with real PyModbus and a read-only local peer.

Only Home Assistant's scheduling shell is stubbed. The integration's package
initializer is skipped so these focused tests do not require a full HA install.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta
import errno
import importlib
from pathlib import Path
import socketserver
import struct
import sys
import threading
import types
from typing import Any
import unittest
from unittest.mock import Mock, patch

from pymodbus.exceptions import ModbusException


class UpdateFailed(Exception):
    """Minimal equivalent of the coordinator's update exception."""


class HassStub:
    """Dispatch synchronous I/O to a real executor thread."""

    async def async_add_executor_job(self, operation, *args):
        return await asyncio.to_thread(operation, *args)


class CoordinatorStub:
    """Provide only the HA coordinator lifecycle used by these tests."""

    def __class_getitem__(cls, item: Any) -> type:
        return cls

    def __init__(self, hass: HassStub, logger: Any, **kwargs: Any) -> None:
        self.hass = hass
        self.base_shutdown_called = False

    async def async_shutdown(self) -> None:
        self.base_shutdown_called = True


def load_coordinator():
    """Load the actual coordinator without importing all entity platforms."""
    stubs = {
        name: types.ModuleType(name)
        for name in (
            "homeassistant",
            "homeassistant.core",
            "homeassistant.helpers",
            "homeassistant.helpers.update_coordinator",
        )
    }
    stubs["homeassistant.core"].HomeAssistant = HassStub
    stubs["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = CoordinatorStub
    stubs["homeassistant.helpers.update_coordinator"].UpdateFailed = UpdateFailed
    package = types.ModuleType("_ffes_coordinator_test")
    package.__path__ = [
        str(Path(__file__).resolve().parents[1] / "custom_components" / "ffes_sauna")
    ]
    sys.modules[package.__name__] = package
    with patch.dict(sys.modules, stubs):
        return importlib.import_module(package.__name__ + ".coordinator")


coordinator_module = load_coordinator()
const = importlib.import_module("_ffes_coordinator_test.const")


def receive_exact(connection, count: int) -> bytes | None:
    """Read a complete Modbus frame fragment, or recognize a closed peer."""
    result = b""
    while len(result) < count:
        chunk = connection.recv(count - len(result))
        if not chunk:
            return None
        result += chunk
    return result


class ModbusPeer(socketserver.BaseRequestHandler):
    """Serve a synthetic register snapshot and reject all write requests."""

    def handle(self) -> None:
        self.request.settimeout(5)
        try:
            while header := receive_exact(self.request, 7):
                transaction, protocol, size, device = struct.unpack(">HHHB", header)
                body = receive_exact(self.request, size - 1)
                if body is None:
                    return
                function, address, count = struct.unpack(">BHH", body)
                if address != 1:
                    raise AssertionError("Unexpected register address")
                if function == 3:
                    values = [0] * count
                    values[const.REG_TEMPERATURE_ACTUAL] = 13
                    values[const.REG_TEMPERATURE_SET] = 70
                    values[const.REG_SAUNA_PROFILE] = 2
                    values[const.REG_CONTROLLER_MODEL] = 2
                    payload = struct.pack(">BB", function, count * 2)
                    payload += struct.pack(">" + "H" * count, *values)
                elif function == 1:
                    nbytes = (count + 7) // 8
                    payload = bytes([function, nbytes]) + bytes(nbytes)
                else:
                    self.server.write_attempts += 1
                    raise AssertionError("This test peer rejects write requests")
                self.request.sendall(
                    struct.pack(">HHHB", transaction, protocol, len(payload) + 1, device)
                    + payload
                )
        except (ConnectionError, TimeoutError):
            return


class ModbusServer(socketserver.ThreadingTCPServer):
    """Run a local peer without retaining idle connection threads."""

    daemon_threads = True
    allow_reuse_address = True


class CoordinatorTests(unittest.IsolatedAsyncioTestCase):
    """Verify recovery, once-only writes, I/O locking and orderly shutdown."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ModbusServer(("127.0.0.1", 0), ModbusPeer)
        cls.server.write_attempts = 0
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=3)
        if cls.server.write_attempts:
            raise AssertionError("A real write request reached the test peer")

    async def asyncSetUp(self) -> None:
        self.coordinator = coordinator_module.FFESSaunaCoordinator(
            HassStub(), "127.0.0.1", self.server.server_address[1],
            1, "test sauna", timedelta(seconds=10),
        )

    async def asyncTearDown(self) -> None:
        await self.coordinator.async_shutdown()

    async def read_snapshot(self) -> dict[str, Any]:
        """Fetch a complete snapshot through the real PyModbus client."""
        data = await self.coordinator._async_update_data()
        self.assertEqual(data["temperature_actual"], 13)
        return data

    async def test_connection_is_deferred_until_executor_read(self) -> None:
        self.assertIsNone(self.coordinator._client)
        await self.read_snapshot()
        self.assertTrue(self.coordinator._client.connected)

    async def test_broken_pipe_is_closed_and_next_poll_recovers(self) -> None:
        await self.read_snapshot()
        client = self.coordinator._client
        with patch.object(
            client, "read_holding_registers",
            side_effect=BrokenPipeError(errno.EPIPE, "Broken pipe"),
        ) as read:
            with self.assertRaisesRegex(UpdateFailed, "Broken pipe"):
                await self.coordinator._async_update_data()
            read.assert_called_once()
        self.assertIsNone(self.coordinator._client)
        self.assertFalse(client.connected)
        await self.read_snapshot()
        self.assertIsNot(self.coordinator._client, client)

    async def test_transport_error_is_not_reported_as_parse_error(self) -> None:
        await self.read_snapshot()
        with patch.object(
            self.coordinator._client, "read_holding_registers",
            side_effect=BrokenPipeError(errno.EPIPE, "Broken pipe"),
        ):
            with self.assertRaises(UpdateFailed) as caught:
                await self.coordinator._async_update_data()
        self.assertIn("Error communicating", str(caught.exception))
        self.assertNotIn("parsing", str(caught.exception))

    async def test_modbus_error_is_closed_and_next_poll_recovers(self) -> None:
        await self.read_snapshot()
        client = self.coordinator._client
        with patch.object(
            client, "read_holding_registers", side_effect=ModbusException("read failed")
        ):
            with self.assertRaisesRegex(UpdateFailed, "read failed"):
                await self.coordinator._async_update_data()
        self.assertFalse(client.connected)
        self.assertIsNone(self.coordinator._client)
        await self.read_snapshot()

    async def test_failed_connect_is_reported_and_discarded(self) -> None:
        client = Mock()
        client.connect.return_value = False
        with patch.object(coordinator_module, "ModbusTcpClient", return_value=client):
            with self.assertRaisesRegex(UpdateFailed, "Cannot connect"):
                await self.coordinator._async_update_data()
        client.close.assert_called_once()
        self.assertIsNone(self.coordinator._client)
        await self.read_snapshot()

    async def check_failed_write(self, client_method: str, worker: str, value: Any) -> None:
        """Ensure an ambiguous write failure is never automatically replayed."""
        await self.read_snapshot()
        client = self.coordinator._client
        with patch.object(
            client, client_method,
            side_effect=BrokenPipeError(errno.EPIPE, "write outcome unknown"),
        ) as write:
            with self.assertRaisesRegex(OSError, "write outcome unknown"):
                await self.coordinator.hass.async_add_executor_job(
                    getattr(self.coordinator, worker), 0, value
                )
            write.assert_called_once()
        self.assertFalse(client.connected)
        self.assertIsNone(self.coordinator._client)
        await self.read_snapshot()

    async def test_failed_register_write_is_not_replayed(self) -> None:
        await self.check_failed_write("write_register", "_write_register_sync", 70)

    async def test_failed_coil_write_is_not_replayed(self) -> None:
        await self.check_failed_write("write_coil", "_write_coil_sync", True)

    async def test_io_operations_are_serialized(self) -> None:
        await self.read_snapshot()
        active = maximum = 0
        counter_lock = threading.Lock()
        entered = threading.Event()
        release = threading.Event()

        def operation(block: bool = False) -> None:
            nonlocal active, maximum
            with counter_lock:
                active += 1
                maximum = max(maximum, active)
            if block:
                entered.set()
                if not release.wait(3):
                    raise AssertionError("Test operation was not released")
            with counter_lock:
                active -= 1

        first = asyncio.create_task(
            asyncio.to_thread(self.coordinator._execute_modbus, operation, True)
        )
        self.assertTrue(await asyncio.to_thread(entered.wait, 3))
        second = asyncio.create_task(
            asyncio.to_thread(self.coordinator._execute_modbus, operation)
        )
        release.set()
        await asyncio.gather(first, second)
        self.assertEqual(maximum, 1)

    async def test_shutdown_cleans_base_and_prevents_reconnect(self) -> None:
        await self.read_snapshot()
        client = self.coordinator._client
        await self.coordinator.async_shutdown()
        self.assertTrue(self.coordinator.base_shutdown_called)
        self.assertFalse(client.connected)
        self.assertIsNone(self.coordinator._client)
        with self.assertRaisesRegex(UpdateFailed, "shutting down"):
            await self.coordinator._async_update_data()
        self.assertIsNone(self.coordinator._client)


if __name__ == "__main__":
    unittest.main()

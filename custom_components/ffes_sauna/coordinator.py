"""DataUpdateCoordinator for FFES Sauna."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    from pymodbus.client.sync import ModbusTcpClient as ModbusTcpClient

import pymodbus
from pymodbus.exceptions import ModbusException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    ERROR_CODES,
    REG_AROMA_SET_VALUE,
    REG_CONTROLLER_MODEL,
    REG_CONTROLLER_STATUS,
    REG_CPIR_G1_POWER,
    REG_CPIR_G2_POWER,
    REG_CPIR_G3_POWER,
    REG_CPIR_G4_POWER,
    REG_CPIR_GROUP_1_SET,
    REG_CPIR_GROUP_2_SET,
    REG_ERROR_CODE,
    REG_FROST_PROTECTION,
    REG_FROST_PROTECTION_STATUS,
    REG_HUMIDITY_ACTUAL,
    REG_INFRARED_MIX_STATUS,
    REG_MODULE_SOFTWARE_VERSION,
    REG_SAUNA_PROFILE,
    REG_SERVER_CONNECTION,
    REG_SESSION_TIME,
    REG_TEMPERATURE_ACTUAL,
    REG_TEMPERATURE_SET,
    REG_VAPORIZER_HUMIDITY,
    REG_VENTILATION_STATE,
    REG_VENTILATION_TIME,
    REG_WIFI_CONNECTION,
    REGISTER_OFFSET,
    REGISTER_COUNT,
    SAUNA_PROFILES,
    STATUS_NAMES,
    STATUS_OFF,
    STATUS_HEAT,
)

_LOGGER = logging.getLogger(__name__)

# Detect pymodbus version to use correct parameter names
# v3.0-3.9: uses slave= parameter
# v3.10+: uses device_id= parameter (slave= was removed)
PYMODBUS_VERSION = "3.10.0"
USE_DEVICE_ID = True
try:
    PYMODBUS_VERSION = pymodbus.__version__
    version_parts = PYMODBUS_VERSION.split('.')
    major = int(version_parts[0])
    minor = int(version_parts[1]) if len(version_parts) > 1 else 0

    # Use device_id for v3.10+ and v4.0+
    USE_DEVICE_ID = (major >= 4) or (major == 3 and minor >= 10)
    _LOGGER.debug("Detected pymodbus version: %s, using %s parameter",
                  PYMODBUS_VERSION, "device_id" if USE_DEVICE_ID else "slave")
except (AttributeError, ValueError, IndexError):
    _LOGGER.warning("Could not detect pymodbus version, assuming 3.10+ (device_id parameter)")




class FFESSaunaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching FFES Sauna data."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        slave: int,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}",
            update_interval=update_interval,
        )
        self.host = host
        self.port = port
        self.slave = slave
        self._client: ModbusTcpClient | None = None
        self._connect()

    def _connect(self) -> None:
        """Connect to the Modbus device."""
        try:
            # W pymodbus 3.6+ nie ma parametru slave w metodach read/write
            # Trzeba go przekazać każdorazowo lub użyć bez niego
            self._client = ModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=5,
            )
            # Connect to the device
            self._client.connect()
            _LOGGER.debug("Modbus client created and connected for %s:%s (slave=%s)", self.host, self.port, self.slave)
        except Exception as err:
            _LOGGER.error("Error creating Modbus client: %s", err)
            raise

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Modbus device."""
        try:
            return await self.hass.async_add_executor_job(self._read_registers)
        except ModbusException as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error reading Modbus registers: %s", err)
            raise UpdateFailed(f"Error reading Modbus registers: {err}") from err

    def _read_single_register_safe(self, address: int) -> int:
        """Safely read a single register, return 0 if failed.

        Args:
            address: Logical address (0-based), will be adjusted by REGISTER_OFFSET
        """
        try:
            physical_addr = REGISTER_OFFSET + address
            if USE_DEVICE_ID:
                result = self._client.read_holding_registers(physical_addr, count=1, device_id=self.slave)
            else:
                result = self._client.read_holding_registers(physical_addr, 1, slave=self.slave)

            if result.isError():
                _LOGGER.warning("Could not read register %s (physical %s): %s", address, physical_addr, result)
                return 0
            return result.registers[0]
        except Exception as err:
            _LOGGER.warning("Exception reading register %s: %s", address, err)
            return 0

    def _read_registers_safe(self, start: int, count: int) -> list[int]:
        """Safely read multiple registers, return zeros if failed.

        Args:
            start: Logical start address (0-based), will be adjusted by REGISTER_OFFSET
            count: Number of registers to read
        """
        try:
            physical_addr = REGISTER_OFFSET + start
            if USE_DEVICE_ID:
                result = self._client.read_holding_registers(physical_addr, count=count, device_id=self.slave)
            else:
                result = self._client.read_holding_registers(physical_addr, count, slave=self.slave)

            if result.isError():
                _LOGGER.warning("Could not read registers %s-%s (physical %s-%s): %s",
                              start, start+count-1, physical_addr, physical_addr+count-1, result)
                return [0] * count
            return result.registers
        except Exception as err:
            _LOGGER.warning("Exception reading registers %s-%s: %s", start, start+count-1, err)
            return [0] * count

    def _read_registers(self) -> dict[str, Any]:
        """Read all necessary registers from the device."""
        data = {}

        try:
            # Read all holding registers at once
            # FFES: physical address 1 = REG[1], physical address 2 = REG[2], etc.
            # Reading 50 registers from physical address 1 (addresses 1-50)
            _LOGGER.debug("Reading FFES sauna registers (starting at physical address %s, count %s)...",
                        REGISTER_OFFSET, REGISTER_COUNT)

            if USE_DEVICE_ID:
                result = self._client.read_holding_registers(
                    REGISTER_OFFSET, count=REGISTER_COUNT, device_id=self.slave
                )
            else:
                result = self._client.read_holding_registers(
                    REGISTER_OFFSET, REGISTER_COUNT, slave=self.slave
                )

            if result.isError():
                raise ModbusException(f"Error reading holding registers: {result}")

            registers = result.registers
            _LOGGER.debug("Successfully read %s registers, first 10: %s",
                         len(registers), registers[:10])

            # DEBUG: Log first few registers with their meanings (only visible when debug logging enabled)
            _LOGGER.debug("Register values (first 5 + status):")
            _LOGGER.debug("  REG[1] TEMPERATURE_SET (registers[0]): %s", registers[0] if len(registers) > 0 else "N/A")
            _LOGGER.debug("  REG[2] TEMP1_ACTUAL (registers[1]): %s", registers[1] if len(registers) > 1 else "N/A")
            _LOGGER.debug("  REG[3] CLOCK (registers[2]): %s", registers[2] if len(registers) > 2 else "N/A")
            _LOGGER.debug("  REG[4] SAUNA_PROFILE (registers[3]): %s", registers[3] if len(registers) > 3 else "N/A")
            _LOGGER.debug("  REG[5] SESSION_TIME (registers[4]): %s", registers[4] if len(registers) > 4 else "N/A")
            _LOGGER.debug("  REG[20] CONTROLLER_STATUS (registers[19]): %s", registers[19] if len(registers) > 19 else "N/A")

            # Parse temperature values
            data["temperature_set"] = registers[REG_TEMPERATURE_SET]
            data["temperature_actual"] = registers[REG_TEMPERATURE_ACTUAL]
            
            # Parse profile
            profile_num = registers[REG_SAUNA_PROFILE]
            data["profile"] = SAUNA_PROFILES.get(profile_num, "unknown")
            data["profile_number"] = profile_num
            
            # Parse times
            data["session_time"] = registers[REG_SESSION_TIME]
            data["ventilation_time"] = registers[REG_VENTILATION_TIME]
            
            # Parse aromatherapy and humidity
            data["aromatherapy"] = registers[REG_AROMA_SET_VALUE]
            data["vaporizer_humidity_set"] = registers[REG_VAPORIZER_HUMIDITY]
            data["humidity_actual"] = registers[REG_HUMIDITY_ACTUAL]
            
            # Parse error code
            error_code = registers[REG_ERROR_CODE]
            data["error_code"] = error_code
            data["error_message"] = ERROR_CODES.get(error_code, f"Unknown error: {error_code}")
            data["has_error"] = error_code != 0
            
            # Parse CPIR settings
            data["cpir_group_1"] = registers[REG_CPIR_GROUP_1_SET]
            data["cpir_group_2"] = registers[REG_CPIR_GROUP_2_SET]
            data["cpir_g1_power"] = registers[REG_CPIR_G1_POWER]
            data["cpir_g2_power"] = registers[REG_CPIR_G2_POWER]
            data["cpir_g3_power"] = registers[REG_CPIR_G3_POWER]
            data["cpir_g4_power"] = registers[REG_CPIR_G4_POWER]
            
            # Parse controller status
            status_num = registers[REG_CONTROLLER_STATUS]
            data["controller_status"] = status_num
            data["controller_status_name"] = STATUS_NAMES.get(status_num, "Unknown")

            # Map controller status to is_on and is_heating for climate entity
            # STATUS_OFF = 0, STATUS_HEAT = 1, STATUS_VENT = 2, STATUS_STBY = 3
            # Only consider "on" when actively heating to prevent screen from staying on in standby/vent modes
            data["is_on"] = status_num == STATUS_HEAT  # On only when actively heating
            data["is_heating"] = status_num == STATUS_HEAT  # Heating only if STATUS_HEAT

            # Parse software version and model
            data["software_version"] = registers[REG_MODULE_SOFTWARE_VERSION]
            data["controller_model"] = registers[REG_CONTROLLER_MODEL]

            # Read coil registers (1-bit values)
            # Coils use same offset: physical address 1 = REG[1]
            # Reading 56 coils from physical address 1 (addresses 1-56)
            if USE_DEVICE_ID:
                coil_result = self._client.read_coils(REGISTER_OFFSET, count=56, device_id=self.slave)
            else:
                coil_result = self._client.read_coils(REGISTER_OFFSET, 56, slave=self.slave)

            if coil_result.isError():
                _LOGGER.warning("Error reading coils (this may be expected): %s", coil_result)
                # If coils fail, just skip them - not all data will be available
                coils = [False] * 56
            else:
                coils = coil_result.bits
                _LOGGER.debug("Successfully read %s coils", len(coils))

            # Parse coil states (may be all False if read failed)
            data["wifi_connection"] = coils[REG_WIFI_CONNECTION]
            data["server_connection"] = coils[REG_SERVER_CONNECTION]
            data["frost_protection"] = coils[REG_FROST_PROTECTION]
            data["frost_protection_status"] = coils[REG_FROST_PROTECTION_STATUS]
            data["ventilation_state"] = coils[REG_VENTILATION_STATE]
            data["infrared_mix_status"] = coils[REG_INFRARED_MIX_STATUS]

            _LOGGER.debug("Successfully read registers: %s", data)
            return data

        except ModbusException:
            raise
        except Exception as err:
            _LOGGER.error("Error parsing Modbus data: %s", err)
            raise ModbusException(f"Error parsing Modbus data: {err}") from err

    def _write_register_sync(self, address: int, value: int) -> None:
        """Synchronously write a register.

        Args:
            address: Logical address (0-based), will be adjusted by REGISTER_OFFSET
            value: Value to write
        """
        physical_addr = REGISTER_OFFSET + address
        if USE_DEVICE_ID:
            result = self._client.write_register(physical_addr, value, device_id=self.slave)
        else:
            result = self._client.write_register(physical_addr, value, slave=self.slave)

        if result.isError():
            raise ModbusException(f"Error writing register {address} (physical {physical_addr}): {result}")

        _LOGGER.debug("Wrote value %s to register %s (physical %s)", value, address, physical_addr)

    def _write_coil_sync(self, address: int, value: bool) -> None:
        """Synchronously write a coil.

        Args:
            address: Logical address (0-based), will be adjusted by REGISTER_OFFSET
            value: Boolean value to write
        """
        # Coils may also use the same offset - needs verification
        physical_addr = REGISTER_OFFSET + address
        if USE_DEVICE_ID:
            result = self._client.write_coil(physical_addr, value, device_id=self.slave)
        else:
            result = self._client.write_coil(physical_addr, value, slave=self.slave)

        if result.isError():
            raise ModbusException(f"Error writing coil {address} (physical {physical_addr}): {result}")

        _LOGGER.debug("Wrote value %s to coil %s (physical %s)", value, address, physical_addr)

    async def async_write_register(self, address: int, value: int) -> None:
        """Write a single register."""
        try:
            await self.hass.async_add_executor_job(
                self._write_register_sync, address, value
            )
            # Request data refresh after write
            await self.async_request_refresh()
        except ModbusException as err:
            _LOGGER.error("Error writing register %s: %s", address, err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error writing register %s: %s", address, err)
            raise

    async def async_write_coil(self, address: int, value: bool) -> None:
        """Write a single coil."""
        try:
            await self.hass.async_add_executor_job(
                self._write_coil_sync, address, value
            )
            # Request data refresh after write
            await self.async_request_refresh()
        except ModbusException as err:
            _LOGGER.error("Error writing coil %s: %s", address, err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error writing coil %s: %s", address, err)
            raise

    async def async_shutdown(self) -> None:
        """Shutdown coordinator."""
        if self._client:
            await self.hass.async_add_executor_job(self._client.close)
            _LOGGER.debug("Modbus client closed")
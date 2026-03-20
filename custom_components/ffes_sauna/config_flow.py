"""Config flow for FFES Sauna integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    from pymodbus.client.sync import ModbusTcpClient as ModbusTcpClient

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_SLAVE,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _validate_connection(host: str, port: int) -> bool:
    """Validate that the Modbus TCP endpoint is reachable."""
    client = ModbusTcpClient(host=host, port=port, timeout=5)
    try:
        return bool(client.connect())
    finally:
        client.close()


async def async_validate_input(
    hass: HomeAssistant,
    user_input: dict[str, Any],
) -> None:
    """Validate user input before creating the config entry."""
    connected = await hass.async_add_executor_job(
        _validate_connection,
        user_input[CONF_HOST],
        user_input[CONF_PORT],
    )
    if not connected:
        raise CannotConnect


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class FFESSaunaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FFES Sauna."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await async_validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception while validating FFES Sauna config")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}_{user_input[CONF_PORT]}_{user_input[CONF_SLAVE]}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        # Show configuration form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=247)
                ),
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FFESSaunaOptionsFlow:
        """Get the options flow for this handler."""
        return FFESSaunaOptionsFlow()


class FFESSaunaOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for FFES Sauna."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
                }
            ),
        )

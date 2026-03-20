"""Light platform for FFES Sauna."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_OUT3_STATE
from .coordinator import FFESSaunaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FFES Sauna lights from a config entry."""
    coordinator: FFESSaunaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FFESSaunaLight(coordinator, entry)])


class FFESSaunaLight(CoordinatorEntity[FFESSaunaCoordinator], LightEntity):
    """Representation of the sauna light output."""

    _attr_has_entity_name = True
    _attr_name = "Light"
    _attr_icon = "mdi:lightbulb"
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(
        self,
        coordinator: FFESSaunaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_light"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data["name"],
            "manufacturer": "FFES",
            "model": "Sauna Controller",
        }

    @property
    def is_on(self) -> bool:
        """Return True if the light is on."""
        return bool(self.coordinator.data.get("out3_state", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        try:
            await self.coordinator.async_write_coil(REG_OUT3_STATE, True)
        except Exception as err:
            _LOGGER.error("Error turning on sauna light: %s", err)
            raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            await self.coordinator.async_write_coil(REG_OUT3_STATE, False)
        except Exception as err:
            _LOGGER.error("Error turning off sauna light: %s", err)
            raise

"""Switch platform for FFES Sauna."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_CONTROLLER_STATUS,
    REG_FROST_PROTECTION,
    REG_INFRARED_MIX_STATUS,
    REG_OUT7_STATE,
    REG_VENTILATION_STATE,
    STATUS_HEAT,
    STATUS_OFF,
)
from .coordinator import FFESSaunaCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FFESSaunaSwitchDescription(SwitchEntityDescription):
    """Class describing FFES Sauna switch entities."""

    is_on_fn: Callable[[dict], bool] | None = None
    turn_on_fn: Callable[[FFESSaunaCoordinator], Any] | None = None
    turn_off_fn: Callable[[FFESSaunaCoordinator], Any] | None = None


SWITCHES: tuple[FFESSaunaSwitchDescription, ...] = (
    FFESSaunaSwitchDescription(
        key="power",
        name="Heating",
        icon="mdi:radiator",
        is_on_fn=lambda data: data.get("is_on", False),
        turn_on_fn=lambda coord: coord.async_write_register(REG_CONTROLLER_STATUS, STATUS_HEAT),
        turn_off_fn=lambda coord: coord.async_write_register(REG_CONTROLLER_STATUS, STATUS_OFF),
    ),
    FFESSaunaSwitchDescription(
        key="ventilation",
        name="Ventilation",
        icon="mdi:fan",
        is_on_fn=lambda data: data.get("ventilation_state", False),
        turn_on_fn=lambda coord: coord.async_write_coil(REG_VENTILATION_STATE, True),
        turn_off_fn=lambda coord: coord.async_write_coil(REG_VENTILATION_STATE, False),
    ),
    FFESSaunaSwitchDescription(
        key="frost_protection",
        name="Frost Protection",
        icon="mdi:snowflake-alert",
        is_on_fn=lambda data: data.get("frost_protection", False),
        turn_on_fn=lambda coord: coord.async_write_coil(REG_FROST_PROTECTION, True),
        turn_off_fn=lambda coord: coord.async_write_coil(REG_FROST_PROTECTION, False),
    ),
    FFESSaunaSwitchDescription(
        key="infrared_mix",
        name="Infrared Mix",
        icon="mdi:heat-wave",
        is_on_fn=lambda data: data.get("infrared_mix_status", False),
        turn_on_fn=lambda coord: coord.async_write_coil(REG_INFRARED_MIX_STATUS, True),
        turn_off_fn=lambda coord: coord.async_write_coil(REG_INFRARED_MIX_STATUS, False),
    ),
    FFESSaunaSwitchDescription(
        key="fan_output",
        name="Fan Output",
        icon="mdi:fan-chevron-up",
        is_on_fn=lambda data: data.get("out7_state", False),
        turn_on_fn=lambda coord: coord.async_write_coil(REG_OUT7_STATE, True),
        turn_off_fn=lambda coord: coord.async_write_coil(REG_OUT7_STATE, False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FFES Sauna switches from a config entry."""
    coordinator: FFESSaunaCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities(
        FFESSaunaSwitch(coordinator, entry, description)
        for description in SWITCHES
    )


class FFESSaunaSwitch(CoordinatorEntity[FFESSaunaCoordinator], SwitchEntity):
    """Representation of a FFES Sauna switch."""

    entity_description: FFESSaunaSwitchDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FFESSaunaCoordinator,
        entry: ConfigEntry,
        description: FFESSaunaSwitchDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data["name"],
            "manufacturer": "FFES",
            "model": "Sauna Controller",
        }

    @property
    def is_on(self) -> bool:
        """Return True if the switch is on."""
        if self.entity_description.is_on_fn:
            return self.entity_description.is_on_fn(self.coordinator.data)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if self.entity_description.turn_on_fn:
            try:
                await self.entity_description.turn_on_fn(self.coordinator)
            except Exception as err:
                _LOGGER.error("Error turning on %s: %s", self.entity_id, err)
                raise

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        if self.entity_description.turn_off_fn:
            try:
                await self.entity_description.turn_off_fn(self.coordinator)
            except Exception as err:
                _LOGGER.error("Error turning off %s: %s", self.entity_id, err)
                raise

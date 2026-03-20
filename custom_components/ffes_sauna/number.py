"""Number platform for FFES Sauna."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_AROMA_SET_VALUE,
    REG_CPIR_G1_POWER,
    REG_CPIR_G2_POWER,
    REG_CPIR_G3_POWER,
    REG_CPIR_G4_POWER,
    REG_SESSION_TIME,
    REG_VAPORIZER_HUMIDITY,
    REG_VENTILATION_TIME,
)
from .coordinator import FFESSaunaCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FFESSaunaNumberDescription(NumberEntityDescription):
    """Class describing FFES Sauna number entities."""

    value_fn: Callable[[dict], float | None] | None = None
    set_value_fn: Callable[[FFESSaunaCoordinator, float], Any] | None = None


NUMBERS: tuple[FFESSaunaNumberDescription, ...] = (
    FFESSaunaNumberDescription(
        key="session_time",
        name="Session Time",
        icon="mdi:timer",
        native_min_value=1,
        native_max_value=2000,
        native_step=5,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda data: data.get("session_time"),
        set_value_fn=lambda coord, value: coord.async_write_register(
            REG_SESSION_TIME, int(value)
        ),
    ),
    FFESSaunaNumberDescription(
        key="ventilation_time",
        name="Ventilation Time",
        icon="mdi:fan",
        native_min_value=1,
        native_max_value=2000,
        native_step=5,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda data: data.get("ventilation_time"),
        set_value_fn=lambda coord, value: coord.async_write_register(
            REG_VENTILATION_TIME, int(value)
        ),
    ),
    FFESSaunaNumberDescription(
        key="aromatherapy",
        name="Aromatherapy",
        icon="mdi:flower",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("aromatherapy"),
        set_value_fn=lambda coord, value: coord.async_write_register(
            REG_AROMA_SET_VALUE, int(value)
        ),
    ),
    FFESSaunaNumberDescription(
        key="humidity_target",
        name="Target Humidity",
        icon="mdi:water-percent",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("vaporizer_humidity_set"),
        set_value_fn=lambda coord, value: coord.async_write_register(
            REG_VAPORIZER_HUMIDITY, int(value)
        ),
    ),
    FFESSaunaNumberDescription(
        key="cpir_g1_power",
        name="CPIR Group 1 Power",
        icon="mdi:lightbulb",
        native_min_value=1,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("cpir_g1_power"),
        set_value_fn=lambda coord, value: coord.async_write_register(
            REG_CPIR_G1_POWER, int(value)
        ),
    ),
    FFESSaunaNumberDescription(
        key="cpir_g2_power",
        name="CPIR Group 2 Power",
        icon="mdi:lightbulb",
        native_min_value=1,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("cpir_g2_power"),
        set_value_fn=lambda coord, value: coord.async_write_register(
            REG_CPIR_G2_POWER, int(value)
        ),
    ),
    FFESSaunaNumberDescription(
        key="cpir_g3_power",
        name="CPIR Group 3 Power",
        icon="mdi:lightbulb",
        native_min_value=1,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("cpir_g3_power"),
        set_value_fn=lambda coord, value: coord.async_write_register(
            REG_CPIR_G3_POWER, int(value)
        ),
    ),
    FFESSaunaNumberDescription(
        key="cpir_g4_power",
        name="CPIR Group 4 Power",
        icon="mdi:lightbulb",
        native_min_value=1,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("cpir_g4_power"),
        set_value_fn=lambda coord, value: coord.async_write_register(
            REG_CPIR_G4_POWER, int(value)
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FFES Sauna numbers from a config entry."""
    coordinator: FFESSaunaCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities(
        FFESSaunaNumber(coordinator, entry, description)
        for description in NUMBERS
    )


class FFESSaunaNumber(CoordinatorEntity[FFESSaunaCoordinator], NumberEntity):
    """Representation of a FFES Sauna number entity."""

    entity_description: FFESSaunaNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FFESSaunaCoordinator,
        entry: ConfigEntry,
        description: FFESSaunaNumberDescription,
    ) -> None:
        """Initialize the number entity."""
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
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        if self.entity_description.set_value_fn:
            try:
                await self.entity_description.set_value_fn(self.coordinator, value)
            except Exception as err:
                _LOGGER.error("Error setting value for %s: %s", self.entity_id, err)
                raise

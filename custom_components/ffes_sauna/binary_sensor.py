"""Binary sensor platform for FFES Sauna."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FFESSaunaCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FFESSaunaBinarySensorDescription(BinarySensorEntityDescription):
    """Class describing FFES Sauna binary sensor entities."""

    is_on_fn: Callable[[dict], bool] | None = None


BINARY_SENSORS: tuple[FFESSaunaBinarySensorDescription, ...] = (
    FFESSaunaBinarySensorDescription(
        key="error",
        name="Error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda data: data.get("has_error", False),
    ),
    FFESSaunaBinarySensorDescription(
        key="heating",
        name="Heating",
        device_class=BinarySensorDeviceClass.HEAT,
        is_on_fn=lambda data: data.get("is_heating", False),
    ),
    FFESSaunaBinarySensorDescription(
        key="frost_protection_active",
        name="Frost Protection Active",
        icon="mdi:snowflake-alert",
        is_on_fn=lambda data: data.get("frost_protection_status", False),
    ),
    FFESSaunaBinarySensorDescription(
        key="wifi_connected",
        name="WiFi Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda data: data.get("wifi_connection", False),
    ),
    FFESSaunaBinarySensorDescription(
        key="server_connected",
        name="Server Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda data: data.get("server_connection", False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FFES Sauna binary sensors from a config entry."""
    coordinator: FFESSaunaCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities(
        FFESSaunaBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class FFESSaunaBinarySensor(CoordinatorEntity[FFESSaunaCoordinator], BinarySensorEntity):
    """Representation of a FFES Sauna binary sensor."""

    entity_description: FFESSaunaBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FFESSaunaCoordinator,
        entry: ConfigEntry,
        description: FFESSaunaBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
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
        """Return True if the binary sensor is on."""
        if self.entity_description.is_on_fn:
            return self.entity_description.is_on_fn(self.coordinator.data)
        return False

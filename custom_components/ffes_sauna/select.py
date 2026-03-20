"""Select platform for FFES Sauna."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    PROFILE_NAMES,
    PROFILE_NAME_TO_NUMBER,
    REG_SAUNA_PROFILE,
)
from .coordinator import FFESSaunaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FFES Sauna select from a config entry."""
    coordinator: FFESSaunaCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([FFESSaunaProfileSelect(coordinator, entry)])


class FFESSaunaProfileSelect(CoordinatorEntity[FFESSaunaCoordinator], SelectEntity):
    """Representation of a FFES Sauna profile selector."""

    _attr_has_entity_name = True
    _attr_name = "Profile"
    _attr_icon = "mdi:format-list-bulleted"

    def __init__(
        self,
        coordinator: FFESSaunaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_profile_select"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data["name"],
            "manufacturer": "FFES",
            "model": "Sauna Controller",
        }

    @property
    def options(self) -> list[str]:
        """Return only profiles supported by the configured controller."""
        supported_profiles = self.coordinator.data.get("supported_profiles")
        if supported_profiles:
            return [PROFILE_NAMES[profile] for profile in supported_profiles]
        return list(PROFILE_NAMES.values())

    @property
    def current_option(self) -> str | None:
        """Return the current selected profile."""
        profile = self.coordinator.data.get("profile")
        if profile:
            return PROFILE_NAMES.get(profile)
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected profile."""
        profile_name = next(
            (
                sauna_profile
                for sauna_profile, display_name in PROFILE_NAMES.items()
                if display_name == option
            ),
            None,
        )

        if profile_name is None:
            _LOGGER.error("Invalid profile option: %s", option)
            return

        supported_profiles = self.coordinator.data.get("supported_profiles")
        if supported_profiles and profile_name not in supported_profiles:
            _LOGGER.error("Profile %s is not supported by controller model", profile_name)
            return

        profile_num = PROFILE_NAME_TO_NUMBER[profile_name]

        try:
            await self.coordinator.async_write_register(REG_SAUNA_PROFILE, profile_num)
        except Exception as err:
            _LOGGER.error("Error setting profile: %s", err)
            raise

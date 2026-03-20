"""Climate platform for FFES Sauna."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    PROFILE_DRY_SAUNA,
    REG_CONTROLLER_STATUS,
    REG_TEMPERATURE_SET,
    STATUS_HEAT,
    STATUS_OFF,
    TEMP_LIMITS,
)
from .coordinator import FFESSaunaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FFES Sauna climate from a config entry."""
    coordinator: FFESSaunaCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([FFESSaunaClimate(coordinator, entry)])


class FFESSaunaClimate(CoordinatorEntity[FFESSaunaCoordinator], ClimateEntity):
    """Representation of a FFES Sauna thermostat."""

    _attr_has_entity_name = True
    _attr_name = "Thermostat"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
    )

    def __init__(
        self,
        coordinator: FFESSaunaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the thermostat."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data["name"],
            "manufacturer": "FFES",
            "model": "Sauna Controller",
            "sw_version": str(coordinator.data.get("software_version", "Unknown")),
        }

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data.get("temperature_actual")

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self.coordinator.data.get("temperature_set")

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        if self.coordinator.data.get("is_on"):
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current HVAC action."""
        if self.coordinator.data.get("is_heating"):
            return HVACAction.HEATING
        if self.coordinator.data.get("is_on"):
            return HVACAction.IDLE
        return HVACAction.OFF

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        profile = self.coordinator.data.get("profile_number", PROFILE_DRY_SAUNA)
        return TEMP_LIMITS.get(profile, {}).get("min", 30)

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        profile = self.coordinator.data.get("profile_number", PROFILE_DRY_SAUNA)
        return TEMP_LIMITS.get(profile, {}).get("max", 110)

    @property
    def target_temperature_step(self) -> float:
        """Return the temperature step."""
        return 5.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "profile": self.coordinator.data.get("profile"),
            "session_time": self.coordinator.data.get("session_time"),
            "humidity": self.coordinator.data.get("humidity_actual"),
            "error_code": self.coordinator.data.get("error_code"),
            "error_message": self.coordinator.data.get("error_message"),
            "controller_status": self.coordinator.data.get("controller_status_name"),
        }

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        # Clamp temperature to valid range
        temperature = max(self.min_temp, min(self.max_temp, temperature))

        try:
            await self.coordinator.async_write_register(
                REG_TEMPERATURE_SET, int(temperature)
            )
        except Exception as err:
            _LOGGER.error("Error setting temperature: %s", err)
            raise

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        try:
            if hvac_mode == HVACMode.HEAT:
                await self.coordinator.async_write_register(REG_CONTROLLER_STATUS, STATUS_HEAT)
            elif hvac_mode == HVACMode.OFF:
                await self.coordinator.async_write_register(REG_CONTROLLER_STATUS, STATUS_OFF)
        except Exception as err:
            _LOGGER.error("Error setting HVAC mode: %s", err)
            raise

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

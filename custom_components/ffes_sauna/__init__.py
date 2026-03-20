"""FFES Sauna Modbus integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .const import (
    ATTR_DURATION,
    ATTR_HUMIDITY,
    ATTR_PROFILE,
    ATTR_TEMPERATURE,
    DOMAIN,
    CONF_SLAVE,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    PROFILE_VENTILATION,
    PROFILE_NAME_TO_NUMBER,
    REG_CONTROLLER_STATUS,
    REG_SAUNA_PROFILE,
    REG_SESSION_TIME,
    REG_TEMPERATURE_SET,
    REG_VAPORIZER_HUMIDITY,
    SERVICE_SET_PROFILE,
    SERVICE_START_SESSION,
    SERVICE_STOP_SESSION,
    STATUS_HEAT,
    STATUS_OFF,
    STATUS_STBY,
    STATUS_VENT,
)
from .coordinator import FFESSaunaCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.BINARY_SENSOR,
    Platform.LIGHT,
]


def _normalize_entity_ids(entity_ids: str | list[str] | None) -> list[str]:
    """Normalize service entity_id input to a list."""
    if entity_ids is None:
        return []
    if isinstance(entity_ids, str):
        return [entity_ids]
    return list(entity_ids)


def _get_service_coordinators(
    hass: HomeAssistant,
    entity_ids: str | list[str] | None,
) -> list[FFESSaunaCoordinator]:
    """Resolve service targets to coordinators."""
    domain_data: dict[str, FFESSaunaCoordinator] = hass.data.get(DOMAIN, {})
    normalized_entity_ids = _normalize_entity_ids(entity_ids)

    if not normalized_entity_ids:
        if len(domain_data) == 1:
            return list(domain_data.values())
        raise HomeAssistantError(
            "Specify entity_id when more than one FFES Sauna integration is configured."
        )

    entity_registry = er.async_get(hass)
    coordinators: list[FFESSaunaCoordinator] = []
    seen_entry_ids: set[str] = set()

    for entity_id in normalized_entity_ids:
        entity_entry = entity_registry.async_get(entity_id)
        if entity_entry is None:
            raise HomeAssistantError(f"Unknown entity_id: {entity_id}")

        coordinator = domain_data.get(entity_entry.config_entry_id)
        if coordinator is None:
            raise HomeAssistantError(f"Entity {entity_id} does not belong to FFES Sauna")

        if entity_entry.config_entry_id not in seen_entry_ids:
            coordinators.append(coordinator)
            seen_entry_ids.add(entity_entry.config_entry_id)

    return coordinators


async def _async_handle_start_session(hass: HomeAssistant, call: ServiceCall) -> None:
    """Start a sauna session."""
    coordinators = _get_service_coordinators(hass, call.data.get(ATTR_ENTITY_ID))
    profile = int(call.data[ATTR_PROFILE])
    temperature = int(call.data[ATTR_TEMPERATURE])
    duration = int(call.data[ATTR_DURATION])
    humidity = call.data.get(ATTR_HUMIDITY)

    for coordinator in coordinators:
        controller_status = coordinator.data.get("controller_status")
        current_profile = coordinator.data.get("profile_number")
        supported_profile_numbers = coordinator.data.get("supported_profile_numbers") or []
        if supported_profile_numbers and profile not in supported_profile_numbers:
            raise HomeAssistantError(
                f"Profile {profile} is not supported by controller model "
                f"{coordinator.data.get('controller_model')}"
            )

        if current_profile != profile and controller_status not in (STATUS_OFF, STATUS_STBY):
            raise HomeAssistantError(
                "Profile can only be changed when the sauna is Off or Standby."
            )

        if humidity is not None:
            await coordinator.async_write_register(REG_VAPORIZER_HUMIDITY, int(humidity))

        await coordinator.async_write_register(REG_SAUNA_PROFILE, profile)
        await coordinator.async_write_register(REG_TEMPERATURE_SET, temperature)
        await coordinator.async_write_register(REG_SESSION_TIME, duration)
        await coordinator.async_write_register(
            REG_CONTROLLER_STATUS,
            STATUS_VENT if profile == PROFILE_VENTILATION else STATUS_HEAT,
        )


async def _async_handle_stop_session(hass: HomeAssistant, call: ServiceCall) -> None:
    """Stop the current sauna session."""
    coordinators = _get_service_coordinators(hass, call.data.get(ATTR_ENTITY_ID))

    for coordinator in coordinators:
        await coordinator.async_write_register(REG_CONTROLLER_STATUS, STATUS_OFF)


async def _async_handle_set_profile(hass: HomeAssistant, call: ServiceCall) -> None:
    """Set the active sauna profile."""
    coordinators = _get_service_coordinators(hass, call.data.get(ATTR_ENTITY_ID))
    profile_name = call.data[ATTR_PROFILE]

    if profile_name not in PROFILE_NAME_TO_NUMBER:
        raise HomeAssistantError(f"Unsupported profile: {profile_name}")

    profile_number = PROFILE_NAME_TO_NUMBER[profile_name]

    for coordinator in coordinators:
        controller_status = coordinator.data.get("controller_status")
        if controller_status not in (STATUS_OFF, STATUS_STBY):
            raise HomeAssistantError(
                "Profile can only be changed when the sauna is Off or Standby."
            )

        supported_profiles = coordinator.data.get("supported_profiles") or []
        if supported_profiles and profile_name not in supported_profiles:
            raise HomeAssistantError(
                f"Profile {profile_name} is not supported by controller model "
                f"{coordinator.data.get('controller_model')}"
            )

        await coordinator.async_write_register(REG_SAUNA_PROFILE, profile_number)


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register domain services once."""
    if hass.services.has_service(DOMAIN, SERVICE_START_SESSION):
        return

    async def async_start_session_service(call: ServiceCall) -> None:
        await _async_handle_start_session(hass, call)

    async def async_stop_session_service(call: ServiceCall) -> None:
        await _async_handle_stop_session(hass, call)

    async def async_set_profile_service(call: ServiceCall) -> None:
        await _async_handle_set_profile(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_SESSION,
        async_start_session_service,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_ENTITY_ID): vol.Any(str, [str]),
                vol.Required(ATTR_PROFILE): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
                vol.Required(ATTR_TEMPERATURE): vol.Coerce(int),
                vol.Required(ATTR_DURATION): vol.All(vol.Coerce(int), vol.Range(min=1, max=2000)),
                vol.Optional(ATTR_HUMIDITY): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_SESSION,
        async_stop_session_service,
        schema=vol.Schema({vol.Optional(ATTR_ENTITY_ID): vol.Any(str, [str])}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_PROFILE,
        async_set_profile_service,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_ENTITY_ID): vol.Any(str, [str]),
                vol.Required(ATTR_PROFILE): vol.In(list(PROFILE_NAME_TO_NUMBER)),
            }
        ),
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FFES Sauna from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    slave = entry.data.get(CONF_SLAVE, DEFAULT_SLAVE)
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )

    _LOGGER.info(
        "Setting up FFES Sauna integration: host=%s, port=%s, slave=%s, scan_interval=%s",
        host,
        port,
        slave,
        scan_interval,
    )

    # Utwórz coordinator
    coordinator = FFESSaunaCoordinator(
        hass,
        host=host,
        port=port,
        slave=slave,
        name=name,
        update_interval=timedelta(seconds=scan_interval),
    )

    # Sprawdź połączenie
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await _async_register_services(hass)

    # Załaduj platformy
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Nasłuchuj na zmiany opcji
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_START_SESSION)
            hass.services.async_remove(DOMAIN, SERVICE_STOP_SESSION)
            hass.services.async_remove(DOMAIN, SERVICE_SET_PROFILE)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)

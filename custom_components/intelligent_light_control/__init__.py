"""Intelligent Light Control – Home Assistant custom integration."""
from __future__ import annotations

import json
import logging

import voluptuous as vol
from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    AMBIENT_TRIGGERS,
    AMBIENT_TRIGGER_TIME,
    CONF_AMBIENT_TRIGGER,
    CONF_AUTOMATION_BLOCKER,
    CONF_AUTOMATION_BLOCKER_STATE,
    CONF_BUTTONS,
    CONF_DOUBLE_TAP_ACTION,
    CONF_FAVORITES,
    CONF_LIGHTS,
    CONF_MANUAL_OVERRIDE_DURATION,
    CONF_MEDIA_PLAYERS,
    CONF_MEDIA_PRESENCE_STATES,
    CONF_MOTION_SENSORS,
    CONF_MULTI_TAP_ENABLED,
    CONF_NO_MOTION_BLOCKER,
    CONF_NO_MOTION_BLOCKER_STATE,
    CONF_NO_MOTION_WAIT,
    CONF_POWER_SENSORS,
    CONF_POWER_THRESHOLD,
    CONF_PRESENCE_SENSORS,
    CONF_SCENE_AMBIENT,
    CONF_SCENE_DAY,
    CONF_SCENE_EVENING,
    CONF_SCENE_MORNING,
    CONF_SCENE_NIGHT,
    CONF_SCENE_NO_MOTION,
    CONF_SERIES_LIGHTS,
    CONF_SERIES_SWITCHES,
    CONF_SWITCHES,
    CONF_SUN_ELEVATION,
    CONF_TIME_AMBIENT_END,
    CONF_TIME_AMBIENT_START,
    CONF_TIME_DAY,
    CONF_TIME_EVENING,
    CONF_TIME_MORNING,
    CONF_TIME_NIGHT,
    CONF_TRANSITION_TIME,
    CONF_TRIPLE_TAP_ACTION,
    CONF_ZONE_ID,
    CONF_ZONE_NAME,
    DEFAULT_MANUAL_OVERRIDE_DURATION,
    DEFAULT_MEDIA_PRESENCE_STATES,
    DEFAULT_NO_MOTION_WAIT,
    DEFAULT_POWER_THRESHOLD,
    DEFAULT_TRANSITION_TIME,
    DOMAIN,
    PLATFORMS,
    SERVICE_ACTIVATE_FAVORITE,
    SERVICE_ACTIVATE_SCENE,
    SERVICE_ADD_ZONE,
    SERVICE_EXPORT_CONFIG,
    SERVICE_RELOAD,
    SERVICE_REMOVE_ZONE,
    SERVICE_SET_SYSTEM_MODE,
    SERVICE_SET_ZONE_MODE,
    SERVICE_TOGGLE_ZONE,
    SERVICE_TURN_OFF_ZONE,
    SERVICE_TURN_ON_ZONE,
    SERVICE_UPDATE_ZONE,
    SYSTEM_MODES,
    TAP_ACTIONS,
    ZONE_MODES,
)
from .coordinator import ILCCoordinator

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared zone field schema (used by add_zone and update_zone)
# ---------------------------------------------------------------------------

_ZONE_FIELDS = {
    vol.Optional(CONF_ZONE_NAME): cv.string,
    vol.Optional(CONF_LIGHTS): vol.All(cv.ensure_list, [cv.entity_id]),
    vol.Optional(CONF_MOTION_SENSORS): vol.All(cv.ensure_list, [cv.entity_id]),
    vol.Optional(CONF_NO_MOTION_WAIT, default=DEFAULT_NO_MOTION_WAIT): vol.Coerce(int),
    vol.Optional(CONF_SUN_ELEVATION): vol.Any(None, vol.Coerce(float)),
    vol.Optional(CONF_AUTOMATION_BLOCKER): vol.Any(None, cv.entity_id),
    vol.Optional(CONF_AUTOMATION_BLOCKER_STATE, default="off"): vol.In(["on", "off"]),
    vol.Optional(CONF_NO_MOTION_BLOCKER): vol.Any(None, cv.entity_id),
    vol.Optional(CONF_NO_MOTION_BLOCKER_STATE, default="off"): vol.In(["on", "off"]),
    vol.Optional(CONF_SCENE_MORNING): vol.Any(None, cv.entity_id),
    vol.Optional(CONF_TIME_MORNING, default="06:00:00"): cv.string,
    vol.Optional(CONF_SCENE_DAY): vol.Any(None, cv.entity_id),
    vol.Optional(CONF_TIME_DAY, default="09:00:00"): cv.string,
    vol.Optional(CONF_SCENE_EVENING): vol.Any(None, cv.entity_id),
    vol.Optional(CONF_TIME_EVENING, default="17:00:00"): cv.string,
    vol.Optional(CONF_SCENE_NIGHT): vol.Any(None, cv.entity_id),
    vol.Optional(CONF_TIME_NIGHT, default="22:00:00"): cv.string,
    vol.Optional(CONF_SCENE_AMBIENT): vol.Any(None, cv.entity_id),
    vol.Optional(CONF_TIME_AMBIENT_START, default="00:00:00"): cv.string,
    vol.Optional(CONF_TIME_AMBIENT_END, default="00:00:00"): cv.string,
    vol.Optional(CONF_SCENE_NO_MOTION): vol.Any(None, cv.entity_id),
    vol.Optional(CONF_SWITCHES): vol.All(cv.ensure_list, [cv.entity_id]),
    vol.Optional(CONF_BUTTONS): vol.All(cv.ensure_list, [cv.entity_id]),
    vol.Optional(CONF_MANUAL_OVERRIDE_DURATION, default=DEFAULT_MANUAL_OVERRIDE_DURATION): vol.Coerce(int),
    # Serienschalter – parallel lists, zipped by index: series_switches[i] controls series_lights[i]
    vol.Optional(CONF_SERIES_SWITCHES): vol.All(cv.ensure_list, [cv.entity_id]),
    vol.Optional(CONF_SERIES_LIGHTS): vol.All(cv.ensure_list, [cv.entity_id]),
    # Presence detection (TV, mmWave, power sensors, etc.)
    vol.Optional(CONF_PRESENCE_SENSORS): vol.All(cv.ensure_list, [cv.entity_id]),
    vol.Optional(CONF_MEDIA_PLAYERS): vol.All(cv.ensure_list, [cv.entity_id]),
    vol.Optional(CONF_MEDIA_PRESENCE_STATES, default=DEFAULT_MEDIA_PRESENCE_STATES): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_POWER_SENSORS): vol.All(cv.ensure_list, [cv.entity_id]),
    vol.Optional(CONF_POWER_THRESHOLD, default=DEFAULT_POWER_THRESHOLD): vol.Coerce(float),
    # Ambient trigger mode: "time" = fixed time window, "sun" = sun below horizon
    vol.Optional(CONF_AMBIENT_TRIGGER, default=AMBIENT_TRIGGER_TIME): vol.In(AMBIENT_TRIGGERS),
    # Transition / fade time in seconds (0 = instant)
    vol.Optional(CONF_TRANSITION_TIME, default=DEFAULT_TRANSITION_TIME): vol.Coerce(float),
    # Favorites: list of scene entity IDs (activated by service or multi-tap)
    vol.Optional(CONF_FAVORITES): vol.All(cv.ensure_list, [cv.entity_id]),
    # Multi-tap button configuration
    vol.Optional(CONF_MULTI_TAP_ENABLED, default=False): cv.boolean,
    vol.Optional(CONF_DOUBLE_TAP_ACTION, default="next_scene"): vol.In(TAP_ACTIONS),
    vol.Optional(CONF_TRIPLE_TAP_ACTION, default="favorite_1"): vol.In(TAP_ACTIONS),
}

_ADD_ZONE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ZONE_ID): cv.string,
        vol.Required(CONF_ZONE_NAME): cv.string,
        **_ZONE_FIELDS,
    }
)

_UPDATE_ZONE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONE_ID): cv.string,
        **_ZONE_FIELDS,
    }
)

_ZONE_ID_SCHEMA = vol.Schema({vol.Required(CONF_ZONE_ID): cv.string})

_SET_MODE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONE_ID): cv.string,
        vol.Required("mode"): vol.In(ZONE_MODES),
    }
)

_ACTIVATE_SCENE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONE_ID): cv.string,
        vol.Required("scene_id"): cv.entity_id,
    }
)

_ACTIVATE_FAVORITE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONE_ID): cv.string,
        vol.Optional("index", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=4)),
    }
)

_SYSTEM_MODE_SCHEMA = vol.Schema({vol.Required("mode"): vol.In(SYSTEM_MODES)})


# ---------------------------------------------------------------------------
# Integration setup
# ---------------------------------------------------------------------------


_PANEL_STATIC_URL = "/intelligent_light_control_panel"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register the ILC sidebar panel (once per HA instance)."""
    if hass.data.get(f"{DOMAIN}_panel_registered"):
        return
    hass.data[f"{DOMAIN}_panel_registered"] = True

    await hass.http.async_register_static_paths([
        StaticPathConfig(
            _PANEL_STATIC_URL,
            hass.config.path("custom_components/intelligent_light_control/www"),
            cache_headers=False,
        )
    ])
    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="Light Control",
        sidebar_icon="mdi:lightbulb-group",
        frontend_url_path="intelligent-light-control",
        config={
            "_panel_custom": {
                "name": "ilc-panel",
                "module_url": f"{_PANEL_STATIC_URL}/panel.js",
            },
        },
        require_admin=False,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Intelligent Light Control from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = ILCCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await coordinator.async_setup()
    await coordinator.async_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _register_services(hass, coordinator, entry)
    await _async_register_panel(hass)

    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: ILCCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        await coordinator.async_unload()

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _unregister_services(hass, entry.entry_id)
        # Clear panel registration flag when the last entry is removed so a
        # subsequent re-setup re-registers the panel correctly.
        if not hass.data.get(DOMAIN):
            hass.data.pop(f"{DOMAIN}_panel_registered", None)

    return unloaded


async def _async_entry_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


# ---------------------------------------------------------------------------
# Service registration
# ---------------------------------------------------------------------------


def _register_services(hass: HomeAssistant, coordinator: ILCCoordinator, entry: ConfigEntry) -> None:
    entry_id = entry.entry_id

    async def _add_zone(call: ServiceCall) -> None:
        data = dict(call.data)
        try:
            zone_id = await coordinator.async_add_zone(data)
            _LOGGER.info("Zone added: %s (%s)", data.get(CONF_ZONE_NAME), zone_id)
        except ValueError as exc:
            _LOGGER.error("add_zone failed: %s", exc)

    async def _remove_zone(call: ServiceCall) -> None:
        try:
            await coordinator.async_remove_zone(call.data[CONF_ZONE_ID])
        except ValueError as exc:
            _LOGGER.error("remove_zone failed: %s", exc)

    async def _update_zone(call: ServiceCall) -> None:
        zone_id = call.data[CONF_ZONE_ID]
        data = {k: v for k, v in call.data.items() if k != CONF_ZONE_ID}
        try:
            await coordinator.async_update_zone(zone_id, data)
        except ValueError as exc:
            _LOGGER.error("update_zone failed: %s", exc)

    async def _set_zone_mode(call: ServiceCall) -> None:
        zone = coordinator.get_zone(call.data[CONF_ZONE_ID])
        if zone:
            zone.mode = call.data["mode"]
        else:
            _LOGGER.error("set_zone_mode: zone %r not found", call.data[CONF_ZONE_ID])

    async def _turn_on_zone(call: ServiceCall) -> None:
        zone = coordinator.get_zone(call.data[CONF_ZONE_ID])
        if zone:
            await zone.async_turn_on()

    async def _turn_off_zone(call: ServiceCall) -> None:
        zone = coordinator.get_zone(call.data[CONF_ZONE_ID])
        if zone:
            await zone.async_turn_off()

    async def _toggle_zone(call: ServiceCall) -> None:
        zone = coordinator.get_zone(call.data[CONF_ZONE_ID])
        if zone:
            await zone.async_toggle()

    async def _activate_scene(call: ServiceCall) -> None:
        zone = coordinator.get_zone(call.data[CONF_ZONE_ID])
        if zone:
            await zone.async_activate_scene(call.data["scene_id"])

    async def _activate_favorite(call: ServiceCall) -> None:
        zone = coordinator.get_zone(call.data[CONF_ZONE_ID])
        if zone:
            await zone.async_activate_favorite(call.data.get("index", 0))

    async def _set_system_mode(call: ServiceCall) -> None:
        await coordinator.async_set_system_mode(call.data["mode"])

    async def _reload(call: ServiceCall) -> None:
        await hass.config_entries.async_reload(entry_id)

    async def _export_config(call: ServiceCall) -> None:
        data = coordinator.data or {}
        zones_raw = {
            zid: zone._config for zid, zone in coordinator.zones.items()
        }
        message = json.dumps({"system_mode": coordinator.system_mode, "zones": zones_raw}, indent=2, default=str)
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {"title": "ILC – Konfiguration", "message": f"```json\n{message}\n```", "notification_id": "ilc_export"},
        )

    service_map = {
        SERVICE_ADD_ZONE: (_add_zone, _ADD_ZONE_SCHEMA),
        SERVICE_REMOVE_ZONE: (_remove_zone, _ZONE_ID_SCHEMA),
        SERVICE_UPDATE_ZONE: (_update_zone, _UPDATE_ZONE_SCHEMA),
        SERVICE_SET_ZONE_MODE: (_set_zone_mode, _SET_MODE_SCHEMA),
        SERVICE_TURN_ON_ZONE: (_turn_on_zone, _ZONE_ID_SCHEMA),
        SERVICE_TURN_OFF_ZONE: (_turn_off_zone, _ZONE_ID_SCHEMA),
        SERVICE_TOGGLE_ZONE: (_toggle_zone, _ZONE_ID_SCHEMA),
        SERVICE_ACTIVATE_SCENE: (_activate_scene, _ACTIVATE_SCENE_SCHEMA),
        SERVICE_ACTIVATE_FAVORITE: (_activate_favorite, _ACTIVATE_FAVORITE_SCHEMA),
        SERVICE_SET_SYSTEM_MODE: (_set_system_mode, _SYSTEM_MODE_SCHEMA),
        SERVICE_RELOAD: (_reload, vol.Schema({})),
        SERVICE_EXPORT_CONFIG: (_export_config, vol.Schema({})),
    }

    for service_name, (handler, schema) in service_map.items():
        hass.services.async_register(DOMAIN, service_name, handler, schema=schema)


def _unregister_services(hass: HomeAssistant, entry_id: str) -> None:
    """Remove all registered services (only if no other entries remain)."""
    if hass.data.get(DOMAIN):
        return
    for service_name in [
        SERVICE_ADD_ZONE,
        SERVICE_REMOVE_ZONE,
        SERVICE_UPDATE_ZONE,
        SERVICE_SET_ZONE_MODE,
        SERVICE_TURN_ON_ZONE,
        SERVICE_TURN_OFF_ZONE,
        SERVICE_TOGGLE_ZONE,
        SERVICE_ACTIVATE_SCENE,
        SERVICE_ACTIVATE_FAVORITE,
        SERVICE_SET_SYSTEM_MODE,
        SERVICE_RELOAD,
        SERVICE_EXPORT_CONFIG,
    ]:
        hass.services.async_remove(DOMAIN, service_name)

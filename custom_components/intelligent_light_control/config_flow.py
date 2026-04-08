"""Config flow for Intelligent Light Control."""
from __future__ import annotations

import uuid
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

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
    CONF_ZONES,
    DEFAULT_MANUAL_OVERRIDE_DURATION,
    DEFAULT_NO_MOTION_WAIT,
    DEFAULT_POWER_THRESHOLD,
    DEFAULT_TRANSITION_TIME,
    DOMAIN,
    SYSTEM_MODES,
    TAP_ACTIONS,
)


# ---------------------------------------------------------------------------
# Initial setup flow
# ---------------------------------------------------------------------------

class ILCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Intelligent Light Control."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step – just ask for a name."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input.get("name", "Intelligent Light Control").strip()
            if not name:
                errors["name"] = "name_empty"
            else:
                await self.async_set_unique_id(name.lower().replace(" ", "_"))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={"name": name},
                    options={"zones": {}, "system_mode": "auto"},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="Intelligent Light Control"): selector.TextSelector(),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ILCOptionsFlow(config_entry)


# ---------------------------------------------------------------------------
# Options / zone management flow
# ---------------------------------------------------------------------------

class ILCOptionsFlow(config_entries.OptionsFlow):
    """Multi-step options flow for zone management."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._zone_data: dict[str, Any] = {}
        self._selected_zone_id: str | None = None

    # ------------------------------------------------------------------
    # Main menu
    # ------------------------------------------------------------------

    async def async_step_init(self, user_input=None):
        """Show main menu."""
        zones: dict = self._config_entry.options.get(CONF_ZONES, {})

        menu_options = ["add_zone", "global_settings"]
        if zones:
            menu_options.insert(1, "edit_zone")
            menu_options.insert(2, "remove_zone")

        return self.async_show_menu(
            step_id="init",
            menu_options=menu_options,
        )

    # ------------------------------------------------------------------
    # Global settings
    # ------------------------------------------------------------------

    async def async_step_global_settings(self, user_input=None):
        """Configure system-wide settings."""
        if user_input is not None:
            options = dict(self._config_entry.options)
            options["system_mode"] = user_input["system_mode"]
            return self.async_create_entry(title="", data=options)

        current_mode = self._config_entry.options.get("system_mode", "auto")
        return self.async_show_form(
            step_id="global_settings",
            data_schema=vol.Schema(
                {
                    vol.Required("system_mode", default=current_mode): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=SYSTEM_MODES,
                            mode=selector.SelectSelectorMode.LIST,
                            translation_key="system_mode",
                        )
                    ),
                }
            ),
        )

    # ------------------------------------------------------------------
    # Add zone – Step 1: Basic settings
    # ------------------------------------------------------------------

    async def async_step_add_zone(self, user_input=None):
        """Zone creation – basic settings (name, lights, sensors, timing)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_ZONE_NAME, "").strip():
                errors[CONF_ZONE_NAME] = "name_empty"
            elif not user_input.get(CONF_LIGHTS):
                errors[CONF_LIGHTS] = "lights_required"
            else:
                self._zone_data = dict(user_input)
                self._zone_data[CONF_ZONE_ID] = (
                    user_input.get(CONF_ZONE_NAME, "zone").lower().replace(" ", "_").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")[:20]
                    + "_"
                    + str(uuid.uuid4())[:4]
                )
                return await self.async_step_add_zone_scenes()

        return self.async_show_form(
            step_id="add_zone",
            data_schema=_zone_basic_schema(),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Add zone – Step 2: Scenes & controls
    # ------------------------------------------------------------------

    async def async_step_add_zone_scenes(self, user_input=None):
        """Zone creation – scenes, blockers, switches, buttons."""
        if user_input is not None:
            self._zone_data.update(user_input)
            return await self._save_zone(self._zone_data[CONF_ZONE_ID], self._zone_data)

        return self.async_show_form(
            step_id="add_zone_scenes",
            data_schema=_zone_scenes_schema(),
        )

    # ------------------------------------------------------------------
    # Edit zone – Step 1: Select zone
    # ------------------------------------------------------------------

    async def async_step_edit_zone(self, user_input=None):
        """Select which zone to edit."""
        zones: dict = self._config_entry.options.get(CONF_ZONES, {})
        if not zones:
            return await self.async_step_init()

        if user_input is not None:
            self._selected_zone_id = user_input["zone_id"]
            return await self.async_step_edit_zone_basic()

        zone_options = [
            selector.SelectOptionDict(value=zid, label=zconf.get(CONF_ZONE_NAME, zid))
            for zid, zconf in zones.items()
        ]
        return self.async_show_form(
            step_id="edit_zone",
            data_schema=vol.Schema(
                {
                    vol.Required("zone_id"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=zone_options,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    # ------------------------------------------------------------------
    # Edit zone – Step 2: Basic settings
    # ------------------------------------------------------------------

    async def async_step_edit_zone_basic(self, user_input=None):
        """Edit basic zone settings."""
        zones: dict = self._config_entry.options.get(CONF_ZONES, {})
        zone = zones.get(self._selected_zone_id, {})
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_ZONE_NAME, "").strip():
                errors[CONF_ZONE_NAME] = "name_empty"
            elif not user_input.get(CONF_LIGHTS):
                errors[CONF_LIGHTS] = "lights_required"
            else:
                self._zone_data = dict(user_input)
                return await self.async_step_edit_zone_scenes()

        return self.async_show_form(
            step_id="edit_zone_basic",
            data_schema=_zone_basic_schema(zone),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Edit zone – Step 3: Scenes & controls
    # ------------------------------------------------------------------

    async def async_step_edit_zone_scenes(self, user_input=None):
        """Edit zone scenes, blockers, switches, buttons."""
        zones: dict = self._config_entry.options.get(CONF_ZONES, {})
        zone = zones.get(self._selected_zone_id, {})

        if user_input is not None:
            self._zone_data.update(user_input)
            self._zone_data[CONF_ZONE_ID] = self._selected_zone_id
            return await self._save_zone(self._selected_zone_id, self._zone_data)

        return self.async_show_form(
            step_id="edit_zone_scenes",
            data_schema=_zone_scenes_schema(zone),
        )

    # ------------------------------------------------------------------
    # Remove zone
    # ------------------------------------------------------------------

    async def async_step_remove_zone(self, user_input=None):
        """Select and remove a zone."""
        zones: dict = self._config_entry.options.get(CONF_ZONES, {})
        if not zones:
            return await self.async_step_init()

        if user_input is not None:
            zone_id = user_input["zone_id"]
            options = dict(self._config_entry.options)
            new_zones = dict(options.get(CONF_ZONES, {}))
            new_zones.pop(zone_id, None)
            options[CONF_ZONES] = new_zones
            return self.async_create_entry(title="", data=options)

        zone_options = [
            selector.SelectOptionDict(value=zid, label=zconf.get(CONF_ZONE_NAME, zid))
            for zid, zconf in zones.items()
        ]
        return self.async_show_form(
            step_id="remove_zone",
            data_schema=vol.Schema(
                {
                    vol.Required("zone_id"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=zone_options,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    # ------------------------------------------------------------------
    # Persistence helper
    # ------------------------------------------------------------------

    async def _save_zone(self, zone_id: str, zone_data: dict) -> Any:
        """Persist zone to config entry options."""
        options = dict(self._config_entry.options)
        zones = dict(options.get(CONF_ZONES, {}))
        zones[zone_id] = zone_data
        options[CONF_ZONES] = zones
        return self.async_create_entry(title="", data=options)


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def _zone_basic_schema(existing: dict | None = None) -> vol.Schema:
    """Schema for basic zone fields (step 1)."""
    ex = existing or {}
    return vol.Schema(
        {
            vol.Required(CONF_ZONE_NAME, default=ex.get(CONF_ZONE_NAME, "")): selector.TextSelector(),
            # --- Zone lights (all lights controlled by automation) ---
            vol.Required(CONF_LIGHTS, default=ex.get(CONF_LIGHTS, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="light", multiple=True)
            ),
            # --- Motion / PIR sensors ---
            vol.Optional(CONF_MOTION_SENSORS, default=ex.get(CONF_MOTION_SENSORS, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor", multiple=True)
            ),
            vol.Optional(
                CONF_NO_MOTION_WAIT,
                default=ex.get(CONF_NO_MOTION_WAIT, DEFAULT_NO_MOTION_WAIT),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3600, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX)
            ),
            # --- Extended presence detection (TV, mmWave, etc.) ---
            vol.Optional(CONF_PRESENCE_SENSORS, default=ex.get(CONF_PRESENCE_SENSORS, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor", multiple=True)
            ),
            vol.Optional(CONF_MEDIA_PLAYERS, default=ex.get(CONF_MEDIA_PLAYERS, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player", multiple=True)
            ),
            # --- Serienschalter: switch[i] controls light[i] individually ---
            vol.Optional(CONF_SERIES_SWITCHES, default=ex.get(CONF_SERIES_SWITCHES, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True)
            ),
            vol.Optional(CONF_SERIES_LIGHTS, default=ex.get(CONF_SERIES_LIGHTS, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="light", multiple=True)
            ),
            # --- Global switches / buttons (control all zone lights) ---
            vol.Optional(CONF_SWITCHES, default=ex.get(CONF_SWITCHES, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True)
            ),
            vol.Optional(CONF_BUTTONS, default=ex.get(CONF_BUTTONS, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True)
            ),
            # --- Multi-tap configuration (for buttons) ---
            vol.Optional(CONF_MULTI_TAP_ENABLED, default=ex.get(CONF_MULTI_TAP_ENABLED, False)): selector.BooleanSelector(),
            vol.Optional(CONF_DOUBLE_TAP_ACTION, default=ex.get(CONF_DOUBLE_TAP_ACTION, "next_scene")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=TAP_ACTIONS, mode=selector.SelectSelectorMode.LIST, translation_key="tap_action")
            ),
            vol.Optional(CONF_TRIPLE_TAP_ACTION, default=ex.get(CONF_TRIPLE_TAP_ACTION, "favorite_1")): selector.SelectSelector(
                selector.SelectSelectorConfig(options=TAP_ACTIONS, mode=selector.SelectSelectorMode.LIST, translation_key="tap_action")
            ),
            # --- Timing ---
            vol.Optional(
                CONF_TRANSITION_TIME,
                default=ex.get(CONF_TRANSITION_TIME, DEFAULT_TRANSITION_TIME),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=10, step=0.1, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_MANUAL_OVERRIDE_DURATION,
                default=ex.get(CONF_MANUAL_OVERRIDE_DURATION, DEFAULT_MANUAL_OVERRIDE_DURATION),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=86400, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX)
            ),
        }
    )


def _zone_scenes_schema(existing: dict | None = None) -> vol.Schema:
    """Schema for zone scenes, controls, and advanced options (step 2)."""
    ex = existing or {}

    def _scene(key: str):
        """Optional scene entity selector – pre-fills current value for edit."""
        val = ex.get(key)
        if val:
            return vol.Optional(key, description={"suggested_value": val})
        return vol.Optional(key)

    def _entity(key: str):
        """Optional single-entity selector – pre-fills current value for edit."""
        val = ex.get(key)
        if val:
            return vol.Optional(key, description={"suggested_value": val})
        return vol.Optional(key)

    return vol.Schema(
        {
            # ---- Tageszeit-Szenen ----
            _scene(CONF_SCENE_MORNING): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="scene")
            ),
            vol.Optional(CONF_TIME_MORNING, default=ex.get(CONF_TIME_MORNING, "06:00:00")): selector.TimeSelector(),
            _scene(CONF_SCENE_DAY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="scene")
            ),
            vol.Optional(CONF_TIME_DAY, default=ex.get(CONF_TIME_DAY, "09:00:00")): selector.TimeSelector(),
            _scene(CONF_SCENE_EVENING): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="scene")
            ),
            vol.Optional(CONF_TIME_EVENING, default=ex.get(CONF_TIME_EVENING, "17:00:00")): selector.TimeSelector(),
            _scene(CONF_SCENE_NIGHT): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="scene")
            ),
            vol.Optional(CONF_TIME_NIGHT, default=ex.get(CONF_TIME_NIGHT, "22:00:00")): selector.TimeSelector(),
            # ---- Ambient ----
            _scene(CONF_SCENE_AMBIENT): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="scene")
            ),
            vol.Optional(CONF_TIME_AMBIENT_START, default=ex.get(CONF_TIME_AMBIENT_START, "00:00:00")): selector.TimeSelector(),
            vol.Optional(CONF_TIME_AMBIENT_END, default=ex.get(CONF_TIME_AMBIENT_END, "00:00:00")): selector.TimeSelector(),
            _scene(CONF_SCENE_NO_MOTION): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="scene")
            ),
            # ---- Favoriten-Szenen (für Multi-Tap, Favorit-Service) ----
            vol.Optional(CONF_FAVORITES, default=ex.get(CONF_FAVORITES, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="scene", multiple=True)
            ),
            # ---- Ambient trigger mode ----
            vol.Optional(CONF_AMBIENT_TRIGGER, default=ex.get(CONF_AMBIENT_TRIGGER, AMBIENT_TRIGGER_TIME)): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=AMBIENT_TRIGGERS,
                    mode=selector.SelectSelectorMode.LIST,
                    translation_key="ambient_trigger",
                )
            ),
            # ---- Sonnenhöhe ----
            vol.Optional(CONF_SUN_ELEVATION, description={"suggested_value": ex.get(CONF_SUN_ELEVATION)}): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-90, max=90, unit_of_measurement="°", mode=selector.NumberSelectorMode.BOX)
            ),
            # ---- Blocker ----
            _entity(CONF_AUTOMATION_BLOCKER): selector.EntitySelector(
                selector.EntitySelectorConfig()
            ),
            vol.Optional(
                CONF_AUTOMATION_BLOCKER_STATE,
                default=ex.get(CONF_AUTOMATION_BLOCKER_STATE, "on"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["on", "off"],
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
            _entity(CONF_NO_MOTION_BLOCKER): selector.EntitySelector(
                selector.EntitySelectorConfig()
            ),
            vol.Optional(
                CONF_NO_MOTION_BLOCKER_STATE,
                default=ex.get(CONF_NO_MOTION_BLOCKER_STATE, "on"),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=["on", "off"],
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
            # ---- Stromverbrauch als Präsenz-Indikator ----
            vol.Optional(CONF_POWER_SENSORS, default=ex.get(CONF_POWER_SENSORS, [])): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            ),
            vol.Optional(
                CONF_POWER_THRESHOLD,
                default=ex.get(CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=10000, unit_of_measurement="W", mode=selector.NumberSelectorMode.BOX)
            ),
        }
    )

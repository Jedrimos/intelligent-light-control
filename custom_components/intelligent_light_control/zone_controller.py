"""Zone controller – implements YAMA-style motion logic + switch/button/Serienschalter/presence support."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import event as ha_event
from homeassistant.util import dt as dt_util

from .const import (
    AMBIENT_TRIGGER_SUN,
    AMBIENT_TRIGGER_TIME,
    ATTR_ACTIVE_SCENE,
    ATTR_LAST_MOTION,
    ATTR_LIGHTS_ON,
    ATTR_MODE,
    ATTR_MOTION_DETECTED,
    ATTR_PRESENCE_DETECTED,
    CONF_AMBIENT_TRIGGER,
    CONF_AUTOMATION_BLOCKER,
    CONF_AUTOMATION_BLOCKER_STATE,
    CONF_BUTTONS,
    CONF_LIGHTS,
    CONF_MANUAL_OVERRIDE_DURATION,
    CONF_MEDIA_PLAYERS,
    CONF_MEDIA_PRESENCE_STATES,
    CONF_MOTION_SENSORS,
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
    DEFAULT_MANUAL_OVERRIDE_DURATION,
    DEFAULT_MEDIA_PRESENCE_STATES,
    DEFAULT_NO_MOTION_WAIT,
    DEFAULT_POWER_THRESHOLD,
    MODE_AUTO,
    MODE_MANUAL,
    MODE_OFF,
    SCENE_NONE,
    ZONE_STATE_AUTO_OFF,
    ZONE_STATE_AUTO_ON,
    ZONE_STATE_BLOCKED,
    ZONE_STATE_DISABLED,
    ZONE_STATE_MANUAL_OFF,
    ZONE_STATE_MANUAL_ON,
)

if TYPE_CHECKING:
    from .coordinator import ILCCoordinator

_LOGGER = logging.getLogger(__name__)


def _parse_time(time_str: str | None) -> time | None:
    """Parse HH:MM:SS string to time object."""
    if not time_str:
        return None
    try:
        parts = time_str.split(":")
        return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
    except (ValueError, IndexError):
        return None


def _time_in_range(start: time, end: time, check: time) -> bool:
    """Return true if check is between start and end (handles midnight crossing)."""
    if start <= end:
        return start <= check < end
    # crosses midnight
    return check >= start or check < end


class ZoneController:
    """Controls a single lighting zone."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: "ILCCoordinator",
        zone_id: str,
        config: dict[str, Any],
    ) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.zone_id = zone_id
        self._config: dict[str, Any] = config

        self._mode: str = MODE_AUTO
        self._lights_on: bool = False
        self._active_scene: str | None = None
        self._motion_detected: bool = False
        self._last_motion: datetime | None = None
        self._blocked: bool = False

        self._no_motion_cancel: asyncio.TimerHandle | None = None
        self._manual_override_cancel: asyncio.TimerHandle | None = None
        self._unsubscribe: list[Any] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def async_setup(self) -> None:
        """Register state-change listeners."""
        self._subscribe_sensors(self._config.get(CONF_MOTION_SENSORS, []), self._handle_motion)
        self._subscribe_sensors(self._config.get(CONF_SWITCHES, []), self._handle_switch)
        self._subscribe_sensors(self._config.get(CONF_BUTTONS, []), self._handle_button)

        # Presence sources: additional binary sensors + media players
        self._subscribe_sensors(self._config.get(CONF_PRESENCE_SENSORS, []), self._handle_presence_source)
        self._subscribe_sensors(self._config.get(CONF_MEDIA_PLAYERS, []), self._handle_presence_source)
        self._subscribe_sensors(self._config.get(CONF_POWER_SENSORS, []), self._handle_presence_source)

        # Serienschalter: each switch maps to its corresponding light by index
        for switch_id in self._config.get(CONF_SERIES_SWITCHES, []):
            unsub = ha_event.async_track_state_change_event(
                self.hass,
                [switch_id],
                lambda event, sw=switch_id: self._handle_series_switch(sw, event),
            )
            self._unsubscribe.append(unsub)

    async def async_unload(self) -> None:
        """Cancel timers and remove listeners."""
        for unsub in self._unsubscribe:
            unsub()
        self._unsubscribe.clear()
        self._cancel_no_motion_timer()
        self._cancel_manual_override_timer()

    def update_config(self, config: dict[str, Any]) -> None:
        """Apply updated configuration (called by update_zone service)."""
        self._config = config

    # ------------------------------------------------------------------
    # Mode / blocker helpers (called by entity setters)
    # ------------------------------------------------------------------

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        if value not in (MODE_AUTO, MODE_MANUAL, MODE_OFF):
            raise ValueError(f"Invalid mode: {value}")
        self._mode = value
        if value != MODE_MANUAL:
            self._cancel_manual_override_timer()
        self.coordinator.async_update_listeners()

    @property
    def blocked(self) -> bool:
        return self._blocked

    @blocked.setter
    def blocked(self, value: bool) -> None:
        self._blocked = value
        self.coordinator.async_update_listeners()

    @property
    def no_motion_wait(self) -> int:
        return int(self._config.get(CONF_NO_MOTION_WAIT, DEFAULT_NO_MOTION_WAIT))

    @no_motion_wait.setter
    def no_motion_wait(self, value: int) -> None:
        self._config[CONF_NO_MOTION_WAIT] = value

    # ------------------------------------------------------------------
    # Computed zone state (used by sensor entity)
    # ------------------------------------------------------------------

    @property
    def zone_state(self) -> str:
        if self._mode == MODE_OFF:
            return ZONE_STATE_DISABLED
        if self._blocked or not self._automation_blocker_ok():
            return ZONE_STATE_BLOCKED
        if self._mode == MODE_MANUAL:
            return ZONE_STATE_MANUAL_ON if self._lights_on else ZONE_STATE_MANUAL_OFF
        return ZONE_STATE_AUTO_ON if self._lights_on else ZONE_STATE_AUTO_OFF

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_MODE: self._mode,
            ATTR_LIGHTS_ON: self._lights_on,
            ATTR_ACTIVE_SCENE: self._active_scene,
            ATTR_MOTION_DETECTED: self._motion_detected,
            ATTR_PRESENCE_DETECTED: self._is_presence_detected(),
            ATTR_LAST_MOTION: self._last_motion.isoformat() if self._last_motion else None,
        }

    # ------------------------------------------------------------------
    # Direct light control (used by services and switch entities)
    # ------------------------------------------------------------------

    async def async_turn_on(self) -> None:
        """Turn on zone lights (manual)."""
        self._mode = MODE_MANUAL
        self._schedule_manual_override_expiry()
        await self._turn_on_lights()
        self.coordinator.async_update_listeners()

    async def async_turn_off(self) -> None:
        """Turn off zone lights (manual)."""
        self._mode = MODE_MANUAL
        self._schedule_manual_override_expiry()
        await self._turn_off_lights()
        self.coordinator.async_update_listeners()

    async def async_toggle(self) -> None:
        """Toggle zone lights."""
        if self._lights_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

    async def async_activate_scene(self, scene_id: str) -> None:
        """Activate a specific scene."""
        self._mode = MODE_MANUAL
        self._schedule_manual_override_expiry()
        await self._call_scene(scene_id)
        self.coordinator.async_update_listeners()

    # ------------------------------------------------------------------
    # Listener registration helpers
    # ------------------------------------------------------------------

    def _subscribe_sensors(self, entity_ids: list[str], handler) -> None:
        for eid in entity_ids:
            unsub = ha_event.async_track_state_change_event(
                self.hass, [eid], handler
            )
            self._unsubscribe.append(unsub)

    # ------------------------------------------------------------------
    # Motion logic (YAMA)
    # ------------------------------------------------------------------

    @callback
    def _handle_motion(self, event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        if new_state.state == "on":
            self.hass.async_create_task(self._on_motion_detected())
        elif new_state.state == "off":
            self._start_no_motion_timer()

    async def _on_motion_detected(self) -> None:
        if self._mode == MODE_OFF:
            return
        if not self._automation_blocker_ok():
            return
        if self._blocked:
            return
        if not self._sun_elevation_ok():
            return

        self._cancel_no_motion_timer()
        self._motion_detected = True
        self._last_motion = dt_util.now()

        # Switch to auto if it was in manual and override has expired
        if self._mode != MODE_MANUAL:
            self._mode = MODE_AUTO

        await self._activate_time_of_day_scene()
        self.coordinator.async_update_listeners()

    def _start_no_motion_timer(self) -> None:
        """Start the no-motion countdown."""
        self._motion_detected = False
        self._cancel_no_motion_timer()
        wait = self.no_motion_wait
        self._no_motion_cancel = self.hass.loop.call_later(
            wait, lambda: self.hass.async_create_task(self._on_no_motion())
        )

    def _cancel_no_motion_timer(self) -> None:
        if self._no_motion_cancel:
            self._no_motion_cancel.cancel()
            self._no_motion_cancel = None

    async def _on_no_motion(self) -> None:
        self._no_motion_cancel = None
        if self._mode == MODE_OFF:
            return
        if self._mode == MODE_MANUAL:
            return

        # Check no-motion blocker
        if not self._no_motion_blocker_ok():
            return

        # Presence check: if someone is still in the room (TV on, mmWave, etc.) → postpone
        if self._is_presence_detected():
            _LOGGER.debug(
                "[%s] Presence still detected (TV/sensor) – postponing no-motion action",
                self.zone_id,
            )
            self._start_no_motion_timer()
            return

        # Try ambient scene (time-based or sun-based)
        ambient = self._config.get(CONF_SCENE_AMBIENT)
        if ambient and ambient != SCENE_NONE and self._is_ambient_active():
            await self._call_scene(ambient)
            self.coordinator.async_update_listeners()
            return

        # Try default no-motion scene
        no_motion_scene = self._config.get(CONF_SCENE_NO_MOTION)
        if no_motion_scene and no_motion_scene != SCENE_NONE:
            await self._call_scene(no_motion_scene)
            self.coordinator.async_update_listeners()
            return

        # Fallback: turn off
        await self._turn_off_lights()
        self.coordinator.async_update_listeners()

    # ------------------------------------------------------------------
    # Presence detection
    # ------------------------------------------------------------------

    def _is_presence_detected(self) -> bool:
        """Return True if any presence source (beyond PIR) indicates someone is in the zone."""
        # 1. Additional binary presence sensors (mmWave radar, occupancy, Zigbee presence, …)
        for sensor_id in self._config.get(CONF_PRESENCE_SENSORS, []):
            state = self.hass.states.get(sensor_id)
            if state and state.state == "on":
                _LOGGER.debug("[%s] Presence via sensor %s", self.zone_id, sensor_id)
                return True

        # 2. Media players: TV / speaker counts as presence when playing or paused
        presence_states = self._config.get(CONF_MEDIA_PRESENCE_STATES, DEFAULT_MEDIA_PRESENCE_STATES)
        for player_id in self._config.get(CONF_MEDIA_PLAYERS, []):
            state = self.hass.states.get(player_id)
            if state and state.state in presence_states:
                _LOGGER.debug(
                    "[%s] Presence via media_player %s (state=%s)", self.zone_id, player_id, state.state
                )
                return True

        # 3. Power sensors: device draws more than threshold → someone is using it
        threshold = float(self._config.get(CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD))
        for sensor_id in self._config.get(CONF_POWER_SENSORS, []):
            state = self.hass.states.get(sensor_id)
            if state:
                try:
                    if float(state.state) >= threshold:
                        _LOGGER.debug(
                            "[%s] Presence via power sensor %s (%.1fW >= %.1fW)",
                            self.zone_id, sensor_id, float(state.state), threshold,
                        )
                        return True
                except (ValueError, TypeError):
                    pass

        return False

    @callback
    def _handle_presence_source(self, event) -> None:
        """React to state changes of presence sensors, media players, or power sensors."""
        if self._mode in (MODE_OFF, MODE_MANUAL):
            return
        if not self._lights_on:
            return

        if self._is_presence_detected():
            # Something is indicating presence → cancel no-motion timer so lights stay on
            if self._no_motion_cancel:
                _LOGGER.debug("[%s] Presence active – cancelling no-motion timer", self.zone_id)
                self._cancel_no_motion_timer()
        elif not self._motion_detected and not self._no_motion_cancel:
            # Presence gone, no motion either → start no-motion countdown
            _LOGGER.debug("[%s] Presence gone – starting no-motion timer", self.zone_id)
            self._start_no_motion_timer()

    # ------------------------------------------------------------------
    # Ambient active check (time-based or sun-based)
    # ------------------------------------------------------------------

    def _is_ambient_active(self) -> bool:
        """Return True if the ambient scene time window is currently active."""
        trigger = self._config.get(CONF_AMBIENT_TRIGGER, AMBIENT_TRIGGER_TIME)

        if trigger == AMBIENT_TRIGGER_SUN:
            # Ambient is active whenever it's dark (sun below horizon)
            sun = self.hass.states.get("sun.sun")
            return sun is not None and sun.state == "below_horizon"

        # Default: fixed time window
        amb_start = _parse_time(self._config.get(CONF_TIME_AMBIENT_START, "00:00:00"))
        amb_end = _parse_time(self._config.get(CONF_TIME_AMBIENT_END, "00:00:00"))
        if not amb_start or not amb_end or amb_start == amb_end:
            return False
        return _time_in_range(amb_start, amb_end, dt_util.now().time())

    # ------------------------------------------------------------------
    # Switch logic (global – controls all zone lights)
    # ------------------------------------------------------------------

    @callback
    def _handle_switch(self, event) -> None:
        """Physical wall switch toggled → toggle zone lights."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None or old_state is None:
            return
        if new_state.state != old_state.state:
            self.hass.async_create_task(self._toggle_from_switch())

    async def _toggle_from_switch(self) -> None:
        """Toggle lights when a physical switch fires."""
        if self._mode == MODE_OFF:
            return
        self._mode = MODE_MANUAL
        self._cancel_no_motion_timer()
        self._schedule_manual_override_expiry()
        if self._lights_on:
            await self._turn_off_lights()
        else:
            await self._activate_time_of_day_scene()
        self.coordinator.async_update_listeners()

    # ------------------------------------------------------------------
    # Button / Taster logic
    # ------------------------------------------------------------------

    @callback
    def _handle_button(self, event) -> None:
        """Button / Taster pressed → toggle zone lights."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        self.hass.async_create_task(self._toggle_from_button())

    async def _toggle_from_button(self) -> None:
        """Toggle lights when a Taster fires."""
        if self._mode == MODE_OFF:
            return
        self._mode = MODE_MANUAL
        self._cancel_no_motion_timer()
        self._schedule_manual_override_expiry()
        if self._lights_on:
            await self._turn_off_lights()
        else:
            await self._activate_time_of_day_scene()
        self.coordinator.async_update_listeners()

    # ------------------------------------------------------------------
    # Serienschalter – each switch controls only its paired light
    # ------------------------------------------------------------------

    @callback
    def _handle_series_switch(self, switch_id: str, event) -> None:
        """One rocker of a Serienschalter toggled → control only its paired light."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None or old_state is None:
            return
        if new_state.state != old_state.state:
            series_switches = self._config.get(CONF_SERIES_SWITCHES, [])
            series_lights = self._config.get(CONF_SERIES_LIGHTS, [])
            pairs: dict[str, str] = dict(zip(series_switches, series_lights))
            light_id = pairs.get(switch_id)
            if light_id:
                self.hass.async_create_task(self._toggle_series_light(light_id))

    async def _toggle_series_light(self, light_id: str) -> None:
        """Toggle a single paired light (Serienschalter), update zone state."""
        if self._mode == MODE_OFF:
            return
        self._mode = MODE_MANUAL
        self._cancel_no_motion_timer()
        self._schedule_manual_override_expiry()

        current = self.hass.states.get(light_id)
        if current and current.state == "on":
            await self.hass.services.async_call(
                "light", "turn_off", {"entity_id": light_id}, blocking=False
            )
        else:
            await self.hass.services.async_call(
                "light", "turn_on", {"entity_id": light_id}, blocking=False
            )

        # Reflect actual light states back into zone
        self._update_lights_on_state()
        self.coordinator.async_update_listeners()

    def _update_lights_on_state(self) -> None:
        """Sync _lights_on with real HA light states (used after Serienschalter actions)."""
        all_lights = list(self._config.get(CONF_LIGHTS, [])) + list(
            self._config.get(CONF_SERIES_LIGHTS, [])
        )
        self._lights_on = any(
            (s := self.hass.states.get(lid)) is not None and s.state == "on"
            for lid in all_lights
        )

    # ------------------------------------------------------------------
    # Manual override timer
    # ------------------------------------------------------------------

    def _schedule_manual_override_expiry(self) -> None:
        """After manual_override_duration seconds, switch back to auto."""
        self._cancel_manual_override_timer()
        duration = int(
            self._config.get(CONF_MANUAL_OVERRIDE_DURATION, DEFAULT_MANUAL_OVERRIDE_DURATION)
        )
        if duration <= 0:
            return
        self._manual_override_cancel = self.hass.loop.call_later(
            duration,
            lambda: self.hass.async_create_task(self._expire_manual_override()),
        )

    def _cancel_manual_override_timer(self) -> None:
        if self._manual_override_cancel:
            self._manual_override_cancel.cancel()
            self._manual_override_cancel = None

    async def _expire_manual_override(self) -> None:
        self._manual_override_cancel = None
        if self._mode == MODE_MANUAL:
            self._mode = MODE_AUTO
            self.coordinator.async_update_listeners()

    # ------------------------------------------------------------------
    # Scene / light helpers
    # ------------------------------------------------------------------

    async def _activate_time_of_day_scene(self) -> None:
        """Pick and activate the right scene for the current time of day."""
        now_time = dt_util.now().time()
        cfg = self._config

        candidates = []
        for scene_key, time_key in [
            (CONF_SCENE_MORNING, CONF_TIME_MORNING),
            (CONF_SCENE_DAY, CONF_TIME_DAY),
            (CONF_SCENE_EVENING, CONF_TIME_EVENING),
            (CONF_SCENE_NIGHT, CONF_TIME_NIGHT),
        ]:
            scene_id = cfg.get(scene_key)
            start = _parse_time(cfg.get(time_key, "00:00:00"))
            if scene_id and scene_id != SCENE_NONE and start is not None:
                candidates.append((scene_id, start))

        candidates.sort(key=lambda x: x[1])

        chosen_scene = None
        for scene_id, start in candidates:
            if now_time >= start:
                chosen_scene = scene_id
            else:
                break

        if chosen_scene is None and candidates:
            chosen_scene = candidates[-1][0]

        if chosen_scene:
            await self._call_scene(chosen_scene)
        else:
            await self._turn_on_lights()

    async def _call_scene(self, scene_id: str) -> None:
        self._active_scene = scene_id
        self._lights_on = True
        await self.hass.services.async_call(
            "scene", "turn_on", {"entity_id": scene_id}, blocking=False
        )

    async def _turn_on_lights(self) -> None:
        lights = self._config.get(CONF_LIGHTS, [])
        if not lights:
            return
        self._lights_on = True
        self._active_scene = None
        await self.hass.services.async_call(
            "light", "turn_on", {"entity_id": lights}, blocking=False
        )

    async def _turn_off_lights(self) -> None:
        # Turn off both zone lights and any Serienschalter lights
        all_lights = list(self._config.get(CONF_LIGHTS, [])) + list(
            self._config.get(CONF_SERIES_LIGHTS, [])
        )
        if not all_lights:
            return
        self._lights_on = False
        self._active_scene = None
        await self.hass.services.async_call(
            "light", "turn_off", {"entity_id": all_lights}, blocking=False
        )

    # ------------------------------------------------------------------
    # Condition checks
    # ------------------------------------------------------------------

    def _automation_blocker_ok(self) -> bool:
        blocker = self._config.get(CONF_AUTOMATION_BLOCKER)
        if not blocker:
            return True
        expected = self._config.get(CONF_AUTOMATION_BLOCKER_STATE, "off")
        state_obj = self.hass.states.get(blocker)
        if state_obj is None:
            return True
        return state_obj.state == expected

    def _no_motion_blocker_ok(self) -> bool:
        blocker = self._config.get(CONF_NO_MOTION_BLOCKER)
        if not blocker:
            return True
        expected = self._config.get(CONF_NO_MOTION_BLOCKER_STATE, "off")
        state_obj = self.hass.states.get(blocker)
        if state_obj is None:
            return True
        return state_obj.state == expected

    def _sun_elevation_ok(self) -> bool:
        elevation_limit = self._config.get(CONF_SUN_ELEVATION)
        if elevation_limit is None:
            return True
        sun_state = self.hass.states.get("sun.sun")
        if sun_state is None:
            return True
        try:
            elevation = float(sun_state.attributes.get("elevation", 0))
            return elevation <= float(elevation_limit)
        except (TypeError, ValueError):
            return True

"""Zone controller – YAMA motion logic, Serienschalter, presence, transitions, multi-tap."""
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
    DEFAULT_MANUAL_OVERRIDE_DURATION,
    DEFAULT_MEDIA_PRESENCE_STATES,
    DEFAULT_NO_MOTION_WAIT,
    DEFAULT_POWER_THRESHOLD,
    DEFAULT_TRANSITION_TIME,
    MODE_AUTO,
    MODE_MANUAL,
    MODE_OFF,
    MULTI_TAP_WINDOW,
    SCENE_NONE,
    TAP_ACTION_ALL_OFF,
    TAP_ACTION_FAVORITE_1,
    TAP_ACTION_FAVORITE_2,
    TAP_ACTION_FAVORITE_3,
    TAP_ACTION_NEXT_SCENE,
    TAP_ACTION_TOGGLE,
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

# All time-of-day scene keys in order (used for next-scene cycling)
_TOD_SCENE_KEYS = [
    (CONF_SCENE_MORNING, CONF_TIME_MORNING),
    (CONF_SCENE_DAY,     CONF_TIME_DAY),
    (CONF_SCENE_EVENING, CONF_TIME_EVENING),
    (CONF_SCENE_NIGHT,   CONF_TIME_NIGHT),
]


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

        # Multi-tap state
        self._button_press_count: int = 0
        self._button_tap_timer: asyncio.TimerHandle | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def async_setup(self) -> None:
        """Register state-change listeners."""
        self._subscribe_sensors(self._config.get(CONF_MOTION_SENSORS, []), self._handle_motion)
        self._subscribe_sensors(self._config.get(CONF_SWITCHES, []), self._handle_switch)
        self._subscribe_sensors(self._config.get(CONF_BUTTONS, []), self._handle_button)
        self._subscribe_sensors(self._config.get(CONF_PRESENCE_SENSORS, []), self._handle_presence_source)
        self._subscribe_sensors(self._config.get(CONF_MEDIA_PLAYERS, []), self._handle_presence_source)
        self._subscribe_sensors(self._config.get(CONF_POWER_SENSORS, []), self._handle_presence_source)

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
        if self._button_tap_timer:
            self._button_tap_timer.cancel()
            self._button_tap_timer = None

    def update_config(self, config: dict[str, Any]) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # Mode / blocker helpers
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
    # Computed zone state
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
    # Direct light control (services + switch entities)
    # ------------------------------------------------------------------

    async def async_turn_on(self) -> None:
        self._mode = MODE_MANUAL
        self._schedule_manual_override_expiry()
        await self._turn_on_lights()
        self.coordinator.async_update_listeners()

    async def async_turn_off(self) -> None:
        self._mode = MODE_MANUAL
        self._schedule_manual_override_expiry()
        await self._turn_off_lights()
        self.coordinator.async_update_listeners()

    async def async_toggle(self) -> None:
        if self._lights_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

    async def async_activate_scene(self, scene_id: str) -> None:
        self._mode = MODE_MANUAL
        self._schedule_manual_override_expiry()
        await self._call_scene(scene_id)
        self.coordinator.async_update_listeners()

    async def async_activate_favorite(self, index: int) -> None:
        """Activate a saved favorite scene by index (0-based)."""
        favorites = self._config.get(CONF_FAVORITES, [])
        if not favorites:
            _LOGGER.warning("[%s] No favorites configured", self.zone_id)
            return
        idx = index % len(favorites)
        scene_id = favorites[idx]
        if scene_id and scene_id != SCENE_NONE:
            self._mode = MODE_MANUAL
            self._cancel_no_motion_timer()
            self._schedule_manual_override_expiry()
            await self._call_scene(scene_id)
            self.coordinator.async_update_listeners()

    # ------------------------------------------------------------------
    # Listener registration
    # ------------------------------------------------------------------

    def _subscribe_sensors(self, entity_ids: list[str], handler) -> None:
        for eid in entity_ids:
            unsub = ha_event.async_track_state_change_event(self.hass, [eid], handler)
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
            if not self._any_motion_sensor_active():
                self._start_no_motion_timer()

    def _any_motion_sensor_active(self) -> bool:
        """Return True if at least one motion sensor is currently 'on'."""
        for sensor_id in self._config.get(CONF_MOTION_SENSORS, []):
            state = self.hass.states.get(sensor_id)
            if state and state.state == "on":
                return True
        return False

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

        if self._mode != MODE_MANUAL:
            self._mode = MODE_AUTO

        await self._activate_time_of_day_scene()
        self.coordinator.async_update_listeners()

    def _start_no_motion_timer(self) -> None:
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
        if self._mode in (MODE_OFF, MODE_MANUAL):
            return
        if not self._no_motion_blocker_ok():
            return

        # Presence check – reschedule with a minimum interval to avoid busy-loops
        if self._is_presence_detected():
            _LOGGER.debug("[%s] Presence detected – postponing no-motion action", self.zone_id)
            recheck_wait = max(self.no_motion_wait, 30)
            self._no_motion_cancel = self.hass.loop.call_later(
                recheck_wait,
                lambda: self.hass.async_create_task(self._on_no_motion()),
            )
            return

        # Ambient scene (time-based or sun-based)
        ambient = self._config.get(CONF_SCENE_AMBIENT)
        if ambient and ambient != SCENE_NONE and self._is_ambient_active():
            await self._call_scene(ambient)
            self.coordinator.async_update_listeners()
            return

        # Default no-motion scene
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
        """Return True if any non-PIR source indicates someone is in the zone."""
        for sensor_id in self._config.get(CONF_PRESENCE_SENSORS, []):
            state = self.hass.states.get(sensor_id)
            if state and state.state == "on":
                return True

        presence_states = self._config.get(CONF_MEDIA_PRESENCE_STATES, DEFAULT_MEDIA_PRESENCE_STATES)
        for player_id in self._config.get(CONF_MEDIA_PLAYERS, []):
            state = self.hass.states.get(player_id)
            if state and state.state in presence_states:
                return True

        threshold = float(self._config.get(CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD))
        for sensor_id in self._config.get(CONF_POWER_SENSORS, []):
            state = self.hass.states.get(sensor_id)
            if state:
                try:
                    if float(state.state) >= threshold:
                        return True
                except (ValueError, TypeError):
                    pass

        return False

    @callback
    def _handle_presence_source(self, event) -> None:
        if self._mode in (MODE_OFF, MODE_MANUAL):
            return
        if not self._lights_on:
            return
        if self._is_presence_detected():
            if self._no_motion_cancel:
                _LOGGER.debug("[%s] Presence active – cancelling no-motion timer", self.zone_id)
                self._cancel_no_motion_timer()
        elif not self._motion_detected and not self._no_motion_cancel:
            _LOGGER.debug("[%s] Presence gone – starting no-motion timer", self.zone_id)
            self._start_no_motion_timer()

    # ------------------------------------------------------------------
    # Ambient active check (time-based or sun-based)
    # ------------------------------------------------------------------

    def _is_ambient_active(self) -> bool:
        trigger = self._config.get(CONF_AMBIENT_TRIGGER, AMBIENT_TRIGGER_TIME)
        if trigger == AMBIENT_TRIGGER_SUN:
            sun = self.hass.states.get("sun.sun")
            return sun is not None and sun.state == "below_horizon"
        amb_start = _parse_time(self._config.get(CONF_TIME_AMBIENT_START, "00:00:00"))
        amb_end = _parse_time(self._config.get(CONF_TIME_AMBIENT_END, "00:00:00"))
        if not amb_start or not amb_end or amb_start == amb_end:
            return False
        return _time_in_range(amb_start, amb_end, dt_util.now().time())

    # ------------------------------------------------------------------
    # Switch logic (controls all zone lights)
    # ------------------------------------------------------------------

    @callback
    def _handle_switch(self, event) -> None:
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None or old_state is None:
            return
        if new_state.state != old_state.state:
            self.hass.async_create_task(self._toggle_from_switch())

    async def _toggle_from_switch(self) -> None:
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
    # Button / Taster logic (with optional multi-tap)
    # ------------------------------------------------------------------

    @callback
    def _handle_button(self, event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        if self._config.get(CONF_MULTI_TAP_ENABLED, False):
            self._register_tap()
        else:
            self.hass.async_create_task(self._toggle_from_button())

    def _register_tap(self) -> None:
        """Record one tap and start/reset the multi-tap window timer."""
        self._button_press_count += 1
        if self._button_tap_timer:
            self._button_tap_timer.cancel()
        self._button_tap_timer = self.hass.loop.call_later(
            MULTI_TAP_WINDOW,
            lambda: self.hass.async_create_task(self._execute_tap_action()),
        )

    async def _execute_tap_action(self) -> None:
        """Fire the appropriate action after the tap window expired."""
        count = self._button_press_count
        self._button_press_count = 0
        self._button_tap_timer = None

        if self._mode == MODE_OFF:
            return

        if count == 1:
            await self._toggle_from_button()
        elif count == 2:
            action = self._config.get(CONF_DOUBLE_TAP_ACTION, TAP_ACTION_NEXT_SCENE)
            await self._run_tap_action(action)
        else:  # 3+
            action = self._config.get(CONF_TRIPLE_TAP_ACTION, TAP_ACTION_FAVORITE_1)
            await self._run_tap_action(action)

    async def _run_tap_action(self, action: str) -> None:
        """Execute a named tap action."""
        self._mode = MODE_MANUAL
        self._cancel_no_motion_timer()
        self._schedule_manual_override_expiry()

        if action == TAP_ACTION_TOGGLE:
            if self._lights_on:
                await self._turn_off_lights()
            else:
                await self._activate_time_of_day_scene()
        elif action == TAP_ACTION_NEXT_SCENE:
            await self._activate_next_tod_scene()
        elif action == TAP_ACTION_FAVORITE_1:
            await self._activate_favorite_by_index(0)
        elif action == TAP_ACTION_FAVORITE_2:
            await self._activate_favorite_by_index(1)
        elif action == TAP_ACTION_FAVORITE_3:
            await self._activate_favorite_by_index(2)
        elif action == TAP_ACTION_ALL_OFF:
            await self._turn_off_lights()

        self.coordinator.async_update_listeners()

    async def _activate_next_tod_scene(self) -> None:
        """Cycle to the next time-of-day scene (wraps around)."""
        scenes = [
            cfg_id
            for key, _ in _TOD_SCENE_KEYS
            if (cfg_id := self._config.get(key)) and cfg_id != SCENE_NONE
        ]
        if not scenes:
            await self._turn_on_lights()
            return

        if self._active_scene in scenes:
            next_scene = scenes[(scenes.index(self._active_scene) + 1) % len(scenes)]
        else:
            # Not in a known ToD scene → jump to first
            next_scene = scenes[0]

        _LOGGER.debug("[%s] Multi-tap next scene → %s", self.zone_id, next_scene)
        await self._call_scene(next_scene)

    async def _activate_favorite_by_index(self, index: int) -> None:
        """Activate a favorite scene by zero-based index."""
        favorites = self._config.get(CONF_FAVORITES, [])
        if not favorites:
            _LOGGER.debug("[%s] No favorites configured, falling back to ToD scene", self.zone_id)
            await self._activate_time_of_day_scene()
            return
        scene_id = favorites[index % len(favorites)]
        if scene_id and scene_id != SCENE_NONE:
            await self._call_scene(scene_id)
        else:
            await self._activate_time_of_day_scene()

    async def _toggle_from_button(self) -> None:
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
    # Serienschalter – each switch controls its paired light
    # ------------------------------------------------------------------

    @callback
    def _handle_series_switch(self, switch_id: str, event) -> None:
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
        if self._mode == MODE_OFF:
            return
        self._mode = MODE_MANUAL
        self._cancel_no_motion_timer()
        self._schedule_manual_override_expiry()

        current = self.hass.states.get(light_id)
        turning_off = current is not None and current.state == "on"

        transition = self._get_transition()
        svc_data_off: dict[str, Any] = {"entity_id": light_id}
        svc_data_on: dict[str, Any] = {"entity_id": light_id}
        if transition > 0:
            svc_data_off["transition"] = transition
            svc_data_on["transition"] = transition

        if turning_off:
            await self.hass.services.async_call("light", "turn_off", svc_data_off, blocking=False)
            all_lights = list(self._config.get(CONF_LIGHTS, [])) + list(
                self._config.get(CONF_SERIES_LIGHTS, [])
            )
            self._lights_on = any(
                (s := self.hass.states.get(lid)) is not None and s.state == "on"
                for lid in all_lights
                if lid != light_id
            )
        else:
            await self.hass.services.async_call("light", "turn_on", svc_data_on, blocking=False)
            self._lights_on = True

        self._active_scene = None
        self.coordinator.async_update_listeners()

    # ------------------------------------------------------------------
    # Manual override timer
    # ------------------------------------------------------------------

    def _schedule_manual_override_expiry(self) -> None:
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
    # Scene / light helpers (all use transition time)
    # ------------------------------------------------------------------

    def _get_transition(self) -> float:
        """Return configured transition time in seconds (0 = instant)."""
        return float(self._config.get(CONF_TRANSITION_TIME, DEFAULT_TRANSITION_TIME))

    async def _activate_time_of_day_scene(self) -> None:
        """Pick and activate the correct scene for the current time of day."""
        now_time = dt_util.now().time()
        cfg = self._config

        candidates = []
        for scene_key, time_key in _TOD_SCENE_KEYS:
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
        svc_data: dict[str, Any] = {"entity_id": scene_id}
        transition = self._get_transition()
        if transition > 0:
            svc_data["transition"] = transition
        await self.hass.services.async_call("scene", "turn_on", svc_data, blocking=False)

    async def _turn_on_lights(self) -> None:
        lights = self._config.get(CONF_LIGHTS, [])
        if not lights:
            return
        self._lights_on = True
        self._active_scene = None
        svc_data: dict[str, Any] = {"entity_id": lights}
        transition = self._get_transition()
        if transition > 0:
            svc_data["transition"] = transition
        await self.hass.services.async_call("light", "turn_on", svc_data, blocking=False)

    async def _turn_off_lights(self) -> None:
        all_lights = list(self._config.get(CONF_LIGHTS, [])) + list(
            self._config.get(CONF_SERIES_LIGHTS, [])
        )
        if not all_lights:
            return
        self._lights_on = False
        self._active_scene = None
        svc_data: dict[str, Any] = {"entity_id": all_lights}
        transition = self._get_transition()
        if transition > 0:
            svc_data["transition"] = transition
        await self.hass.services.async_call("light", "turn_off", svc_data, blocking=False)

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

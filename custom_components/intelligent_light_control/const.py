"""Constants for Intelligent Light Control."""
from typing import Final

DOMAIN: Final = "intelligent_light_control"
VERSION: Final = "1.0.0-alpha"

# Platforms
PLATFORMS: Final = ["sensor", "switch", "number", "select"]

# Zone configuration keys
CONF_ZONES: Final = "zones"
CONF_ZONE_ID: Final = "zone_id"
CONF_ZONE_NAME: Final = "name"
CONF_LIGHTS: Final = "lights"
CONF_MOTION_SENSORS: Final = "motion_sensors"
CONF_NO_MOTION_WAIT: Final = "no_motion_wait"
CONF_SUN_ELEVATION: Final = "sun_elevation_check"
CONF_AUTOMATION_BLOCKER: Final = "automation_blocker"
CONF_AUTOMATION_BLOCKER_STATE: Final = "automation_blocker_state"
CONF_NO_MOTION_BLOCKER: Final = "no_motion_blocker"
CONF_NO_MOTION_BLOCKER_STATE: Final = "no_motion_blocker_state"
CONF_MANUAL_OVERRIDE_DURATION: Final = "manual_override_duration"

# Scene configuration keys
CONF_SCENE_MORNING: Final = "scene_morning"
CONF_TIME_MORNING: Final = "time_scene_morning"
CONF_SCENE_DAY: Final = "scene_day"
CONF_TIME_DAY: Final = "time_scene_day"
CONF_SCENE_EVENING: Final = "scene_evening"
CONF_TIME_EVENING: Final = "time_scene_evening"
CONF_SCENE_NIGHT: Final = "scene_night"
CONF_TIME_NIGHT: Final = "time_scene_night"
CONF_SCENE_AMBIENT: Final = "scene_ambient"
CONF_TIME_AMBIENT_START: Final = "time_scene_ambient_start"
CONF_TIME_AMBIENT_END: Final = "time_scene_ambient_end"
CONF_SCENE_NO_MOTION: Final = "scene_no_motion"

# Switch / button keys
CONF_SWITCHES: Final = "switches"
CONF_BUTTONS: Final = "buttons"

# Zone modes
MODE_AUTO: Final = "auto"
MODE_MANUAL: Final = "manual"
MODE_OFF: Final = "off"
ZONE_MODES: Final = [MODE_AUTO, MODE_MANUAL, MODE_OFF]

# System modes (same names, hub-level)
SYSTEM_MODE_AUTO: Final = "auto"
SYSTEM_MODE_MANUAL: Final = "manual"
SYSTEM_MODE_OFF: Final = "off"
SYSTEM_MODES: Final = [SYSTEM_MODE_AUTO, SYSTEM_MODE_MANUAL, SYSTEM_MODE_OFF]

# Zone state values (reported by sensor)
ZONE_STATE_AUTO_ON: Final = "auto_on"
ZONE_STATE_AUTO_OFF: Final = "auto_off"
ZONE_STATE_MANUAL_ON: Final = "manual_on"
ZONE_STATE_MANUAL_OFF: Final = "manual_off"
ZONE_STATE_BLOCKED: Final = "blocked"
ZONE_STATE_DISABLED: Final = "disabled"

# Services
SERVICE_ADD_ZONE: Final = "add_zone"
SERVICE_REMOVE_ZONE: Final = "remove_zone"
SERVICE_UPDATE_ZONE: Final = "update_zone"
SERVICE_SET_ZONE_MODE: Final = "set_zone_mode"
SERVICE_TURN_ON_ZONE: Final = "turn_on_zone"
SERVICE_TURN_OFF_ZONE: Final = "turn_off_zone"
SERVICE_TOGGLE_ZONE: Final = "toggle_zone"
SERVICE_ACTIVATE_SCENE: Final = "activate_scene"
SERVICE_SET_SYSTEM_MODE: Final = "set_system_mode"
SERVICE_RELOAD: Final = "reload"
SERVICE_EXPORT_CONFIG: Final = "export_config"

# Attributes exposed on entities
ATTR_ZONE_ID: Final = "zone_id"
ATTR_ZONE_NAME: Final = "zone_name"
ATTR_MODE: Final = "mode"
ATTR_LIGHTS_ON: Final = "lights_on"
ATTR_ACTIVE_SCENE: Final = "active_scene"
ATTR_MOTION_DETECTED: Final = "motion_detected"
ATTR_LAST_MOTION: Final = "last_motion"
ATTR_NO_MOTION_WAIT: Final = "no_motion_wait"
ATTR_SUN_ELEVATION: Final = "sun_elevation_check"
ATTR_SWITCHES: Final = "switches"
ATTR_BUTTONS: Final = "buttons"
ATTR_LIGHTS: Final = "lights"
ATTR_MOTION_SENSORS: Final = "motion_sensors"

# Defaults
DEFAULT_NO_MOTION_WAIT: Final = 120          # seconds
DEFAULT_MANUAL_OVERRIDE_DURATION: Final = 3600  # seconds (1 hour)
DEFAULT_SUN_ELEVATION: Final = None
SCENE_NONE: Final = "scene.none"

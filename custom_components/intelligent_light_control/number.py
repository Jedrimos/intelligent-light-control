"""Number platform – configurable wait time and override duration per zone."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_MANUAL_OVERRIDE_DURATION,
    DEFAULT_MANUAL_OVERRIDE_DURATION,
    DEFAULT_NO_MOTION_WAIT,
    DOMAIN,
    VERSION,
)
from .coordinator import ILCCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ILCCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list = []
    for zone_id in coordinator.zones:
        entities.append(ILCNoMotionWaitNumber(coordinator, entry, zone_id))
        entities.append(ILCManualOverrideDurationNumber(coordinator, entry, zone_id))
    async_add_entities(entities)
    coordinator.async_add_listener(
        lambda: _handle_new_zones(coordinator, entry, async_add_entities, entities)
    )


def _handle_new_zones(coordinator, entry, async_add_entities, existing):
    known_ids = {e.zone_id for e in existing}
    new_entities = []
    for zone_id in coordinator.zones:
        if zone_id not in known_ids:
            new_entities.append(ILCNoMotionWaitNumber(coordinator, entry, zone_id))
            new_entities.append(ILCManualOverrideDurationNumber(coordinator, entry, zone_id))
    if new_entities:
        existing.extend(new_entities)
        async_add_entities(new_entities)


class _ILCZoneNumber(CoordinatorEntity, NumberEntity):
    """Base class for zone number entities."""

    def __init__(self, coordinator: ILCCoordinator, entry: ConfigEntry, zone_id: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.zone_id = zone_id

    @property
    def _zone_data(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get(self.zone_id, {})
        return {}

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.zone_id not in self.coordinator.zones:
            self.hass.async_create_task(self.async_remove(force_remove=True))
            return
        super()._handle_coordinator_update()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry.entry_id}_{self.zone_id}")},
            name=self._zone_data.get("name", self.zone_id),
            manufacturer="Jedrimos",
            model="Lighting Zone",
            sw_version=VERSION,
            via_device=(DOMAIN, self._entry.entry_id),
        )


class ILCNoMotionWaitNumber(_ILCZoneNumber):
    """Number entity to set no-motion wait time in seconds."""

    _attr_native_min_value = 0
    _attr_native_max_value = 3600
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "s"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-outline"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self.zone_id}_no_motion_wait"

    @property
    def name(self) -> str:
        zone_name = self._zone_data.get("name", self.zone_id)
        return f"{zone_name} Wartezeit (kein Bewegung)"

    @property
    def native_value(self) -> float:
        return float(self._zone_data.get("no_motion_wait", DEFAULT_NO_MOTION_WAIT))

    async def async_set_native_value(self, value: float) -> None:
        zone = self.coordinator.get_zone(self.zone_id)
        if zone:
            zone.no_motion_wait = int(value)
            self.coordinator.async_update_listeners()


class ILCManualOverrideDurationNumber(_ILCZoneNumber):
    """Number entity to set manual override expiry duration in seconds."""

    _attr_native_min_value = 0
    _attr_native_max_value = 86400
    _attr_native_step = 60
    _attr_native_unit_of_measurement = "s"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:timer-lock-outline"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self.zone_id}_manual_override_duration"

    @property
    def name(self) -> str:
        zone_name = self._zone_data.get("name", self.zone_id)
        return f"{zone_name} Manueller Override Dauer"

    @property
    def native_value(self) -> float:
        zone = self.coordinator.get_zone(self.zone_id)
        if zone is None:
            return float(DEFAULT_MANUAL_OVERRIDE_DURATION)
        return float(zone._config.get(CONF_MANUAL_OVERRIDE_DURATION, DEFAULT_MANUAL_OVERRIDE_DURATION))

    async def async_set_native_value(self, value: float) -> None:
        zone = self.coordinator.get_zone(self.zone_id)
        if zone:
            zone._config[CONF_MANUAL_OVERRIDE_DURATION] = int(value)
            self.coordinator.async_update_listeners()

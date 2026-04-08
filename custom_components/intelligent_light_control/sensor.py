"""Sensor platform – zone status sensor."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ACTIVE_SCENE,
    ATTR_LAST_MOTION,
    ATTR_LIGHTS_ON,
    ATTR_MODE,
    ATTR_MOTION_DETECTED,
    ATTR_ZONE_NAME,
    CONF_ZONE_NAME,
    DOMAIN,
    VERSION,
    ZONE_STATE_AUTO_OFF,
    ZONE_STATE_AUTO_ON,
    ZONE_STATE_BLOCKED,
    ZONE_STATE_DISABLED,
    ZONE_STATE_MANUAL_OFF,
    ZONE_STATE_MANUAL_ON,
)
from .coordinator import ILCCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ILCCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ILCZoneStatusSensor(coordinator, entry, zone_id)
        for zone_id in coordinator.zones
    ]
    async_add_entities(entities)
    coordinator.async_add_listener(
        lambda: _handle_new_zones(hass, coordinator, entry, async_add_entities, entities)
    )


def _handle_new_zones(hass, coordinator, entry, async_add_entities, existing):
    known_ids = {e.zone_id for e in existing}
    new_entities = [
        ILCZoneStatusSensor(coordinator, entry, zone_id)
        for zone_id in coordinator.zones
        if zone_id not in known_ids
    ]
    if new_entities:
        existing.extend(new_entities)
        async_add_entities(new_entities)


_STATE_ICONS = {
    ZONE_STATE_AUTO_ON: "mdi:motion-sensor",
    ZONE_STATE_AUTO_OFF: "mdi:motion-sensor-off",
    ZONE_STATE_MANUAL_ON: "mdi:light-switch",
    ZONE_STATE_MANUAL_OFF: "mdi:light-switch-off",
    ZONE_STATE_BLOCKED: "mdi:cancel",
    ZONE_STATE_DISABLED: "mdi:power-off",
}


class ILCZoneStatusSensor(CoordinatorEntity, SensorEntity):
    """Represents the current operational state of a lighting zone."""

    def __init__(self, coordinator: ILCCoordinator, entry: ConfigEntry, zone_id: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.zone_id = zone_id

    @property
    def _zone_data(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get(self.zone_id, {})
        return {}

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self.zone_id}_status"

    @property
    def name(self) -> str:
        zone_name = self._zone_data.get("name", self.zone_id)
        return f"{zone_name} Status"

    @property
    def native_value(self) -> str:
        return self._zone_data.get("state", ZONE_STATE_DISABLED)

    @property
    def icon(self) -> str:
        return _STATE_ICONS.get(self.native_value, "mdi:lightbulb-auto")

    @property
    def extra_state_attributes(self) -> dict:
        attrs = self._zone_data.get("attributes", {})
        attrs["zone_id"] = self.zone_id
        attrs[ATTR_ZONE_NAME] = self._zone_data.get("name", self.zone_id)
        return attrs

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

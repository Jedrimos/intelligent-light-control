"""Switch platform – manual override and automation blocker per zone."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ZONE_NAME, DOMAIN, MODE_MANUAL, VERSION
from .coordinator import ILCCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ILCCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list = []
    for zone_id in coordinator.zones:
        entities.append(ILCManualOverrideSwitch(coordinator, entry, zone_id))
        entities.append(ILCBlockerSwitch(coordinator, entry, zone_id))
    async_add_entities(entities)
    coordinator.async_add_listener(
        lambda: _handle_new_zones(coordinator, entry, async_add_entities, entities)
    )


def _handle_new_zones(coordinator, entry, async_add_entities, existing):
    known_ids = {e.zone_id for e in existing}
    new_entities = []
    for zone_id in coordinator.zones:
        if zone_id not in known_ids:
            new_entities.append(ILCManualOverrideSwitch(coordinator, entry, zone_id))
            new_entities.append(ILCBlockerSwitch(coordinator, entry, zone_id))
    if new_entities:
        existing.extend(new_entities)
        async_add_entities(new_entities)


class _ILCZoneSwitch(CoordinatorEntity, SwitchEntity):
    """Base class for zone switches."""

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


class ILCManualOverrideSwitch(_ILCZoneSwitch):
    """Switch that enables manual override for a zone."""

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self.zone_id}_manual_override"

    @property
    def name(self) -> str:
        zone_name = self._zone_data.get("name", self.zone_id)
        return f"{zone_name} Manueller Override"

    @property
    def icon(self) -> str:
        return "mdi:hand-back-right" if self.is_on else "mdi:hand-back-right-off"

    @property
    def is_on(self) -> bool:
        return self._zone_data.get("mode") == MODE_MANUAL

    async def async_turn_on(self, **kwargs) -> None:
        zone = self.coordinator.get_zone(self.zone_id)
        if zone:
            zone.mode = MODE_MANUAL

    async def async_turn_off(self, **kwargs) -> None:
        zone = self.coordinator.get_zone(self.zone_id)
        if zone:
            from .const import MODE_AUTO
            zone.mode = MODE_AUTO


class ILCBlockerSwitch(_ILCZoneSwitch):
    """Switch that blocks automatic lighting for a zone."""

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self.zone_id}_blocker"

    @property
    def name(self) -> str:
        zone_name = self._zone_data.get("name", self.zone_id)
        return f"{zone_name} Blockiert"

    @property
    def icon(self) -> str:
        return "mdi:cancel" if self.is_on else "mdi:check-circle-outline"

    @property
    def is_on(self) -> bool:
        return bool(self._zone_data.get("blocked", False))

    async def async_turn_on(self, **kwargs) -> None:
        zone = self.coordinator.get_zone(self.zone_id)
        if zone:
            zone.blocked = True

    async def async_turn_off(self, **kwargs) -> None:
        zone = self.coordinator.get_zone(self.zone_id)
        if zone:
            zone.blocked = False

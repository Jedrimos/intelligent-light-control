"""Select platform – zone mode and system mode selectors."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SYSTEM_MODES, VERSION, ZONE_MODES
from .coordinator import ILCCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ILCCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list = [ILCSystemModeSelect(coordinator, entry)]
    for zone_id in coordinator.zones:
        entities.append(ILCZoneModeSelect(coordinator, entry, zone_id))
    async_add_entities(entities)
    coordinator.async_add_listener(
        lambda: _handle_new_zones(coordinator, entry, async_add_entities, entities)
    )


def _handle_new_zones(coordinator, entry, async_add_entities, existing):
    known_ids = {e.zone_id for e in existing if hasattr(e, "zone_id")}
    new_entities = [
        ILCZoneModeSelect(coordinator, entry, zone_id)
        for zone_id in coordinator.zones
        if zone_id not in known_ids
    ]
    if new_entities:
        existing.extend(new_entities)
        async_add_entities(new_entities)


class ILCSystemModeSelect(CoordinatorEntity, SelectEntity):
    """Select entity for the hub-level system mode."""

    _attr_options = SYSTEM_MODES
    _attr_icon = "mdi:home-lightbulb"

    def __init__(self, coordinator: ILCCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_system_mode"

    @property
    def name(self) -> str:
        return f"{self._entry.title} Systemmodus"

    @property
    def current_option(self) -> str:
        return self.coordinator.system_mode

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_system_mode(option)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="Jedrimos",
            model="Intelligent Light Control Hub",
            sw_version=VERSION,
        )


class ILCZoneModeSelect(CoordinatorEntity, SelectEntity):
    """Select entity to set the operating mode of a single zone."""

    _attr_options = ZONE_MODES
    _attr_icon = "mdi:cog"

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
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_{self.zone_id}_mode"

    @property
    def name(self) -> str:
        zone_name = self._zone_data.get("name", self.zone_id)
        return f"{zone_name} Modus"

    @property
    def current_option(self) -> str:
        return self._zone_data.get("mode", "auto")

    async def async_select_option(self, option: str) -> None:
        zone = self.coordinator.get_zone(self.zone_id)
        if zone:
            zone.mode = option

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

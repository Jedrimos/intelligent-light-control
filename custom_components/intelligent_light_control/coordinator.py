"""Data coordinator for Intelligent Light Control."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_ZONE_ID,
    CONF_ZONE_NAME,
    CONF_ZONES,
    DOMAIN,
    SYSTEM_MODE_AUTO,
    SYSTEM_MODES,
)
from .zone_controller import ZoneController

_LOGGER = logging.getLogger(__name__)


class ILCCoordinator(DataUpdateCoordinator):
    """Coordinates all lighting zones."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self._entry = entry
        self._zones: dict[str, ZoneController] = {}
        self._system_mode: str = entry.options.get("system_mode", SYSTEM_MODE_AUTO)

    # ------------------------------------------------------------------
    # Setup / teardown
    # ------------------------------------------------------------------

    async def async_setup(self) -> None:
        """Initialise all zones from stored options."""
        zones_data: dict[str, dict] = self._entry.options.get(CONF_ZONES, {})
        for zone_id, zone_config in zones_data.items():
            await self._create_zone(zone_id, zone_config)

    async def async_unload(self) -> None:
        """Unload all zone controllers."""
        for zone in self._zones.values():
            await zone.async_unload()
        self._zones.clear()

    # ------------------------------------------------------------------
    # Zone management
    # ------------------------------------------------------------------

    async def _create_zone(self, zone_id: str, config: dict[str, Any]) -> ZoneController:
        controller = ZoneController(self.hass, self, zone_id, config)
        await controller.async_setup()
        self._zones[zone_id] = controller
        return controller

    async def async_add_zone(self, config: dict[str, Any]) -> str:
        """Add a new zone and persist it. Returns the new zone_id."""
        zone_id = config.get(CONF_ZONE_ID) or str(uuid.uuid4())[:8]
        config[CONF_ZONE_ID] = zone_id

        if zone_id in self._zones:
            raise ValueError(f"Zone {zone_id!r} already exists")

        await self._create_zone(zone_id, config)
        await self._persist_zones()
        self.async_update_listeners()
        return zone_id

    async def async_remove_zone(self, zone_id: str) -> None:
        """Remove a zone by id."""
        zone = self._zones.pop(zone_id, None)
        if zone is None:
            raise ValueError(f"Zone {zone_id!r} not found")
        await zone.async_unload()
        await self._persist_zones()
        self.async_update_listeners()

    async def async_update_zone(self, zone_id: str, config: dict[str, Any]) -> None:
        """Update zone configuration."""
        zone = self._zones.get(zone_id)
        if zone is None:
            raise ValueError(f"Zone {zone_id!r} not found")
        # Unload old listeners, apply new config, re-setup
        await zone.async_unload()
        config[CONF_ZONE_ID] = zone_id
        zone.update_config(config)
        await zone.async_setup()
        await self._persist_zones()
        self.async_update_listeners()

    # ------------------------------------------------------------------
    # Zone access helpers
    # ------------------------------------------------------------------

    def get_zone(self, zone_id: str) -> ZoneController | None:
        return self._zones.get(zone_id)

    @property
    def zones(self) -> dict[str, ZoneController]:
        return dict(self._zones)

    # ------------------------------------------------------------------
    # System mode
    # ------------------------------------------------------------------

    @property
    def system_mode(self) -> str:
        return self._system_mode

    async def async_set_system_mode(self, mode: str) -> None:
        if mode not in SYSTEM_MODES:
            raise ValueError(f"Invalid system mode: {mode!r}")
        self._system_mode = mode
        options = dict(self._entry.options)
        options["system_mode"] = mode
        self.hass.config_entries.async_update_entry(self._entry, options=options)
        self.async_update_listeners()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    async def _persist_zones(self) -> None:
        """Write all zone configs back to config entry options."""
        zones_data = {zid: zc._config for zid, zc in self._zones.items()}
        options = dict(self._entry.options)
        options[CONF_ZONES] = zones_data
        self.hass.config_entries.async_update_entry(self._entry, options=options)

    # ------------------------------------------------------------------
    # DataUpdateCoordinator override
    # ------------------------------------------------------------------

    async def _async_update_data(self):
        """Return a snapshot of all zone states (used by entities)."""
        return {
            zone_id: {
                "state": zone.zone_state,
                "attributes": zone.extra_state_attributes,
                "mode": zone.mode,
                "no_motion_wait": zone.no_motion_wait,
                "blocked": zone.blocked,
                "name": zone._config.get(CONF_ZONE_NAME, zone_id),
            }
            for zone_id, zone in self._zones.items()
        }

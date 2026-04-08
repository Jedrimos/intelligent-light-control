# Architektur – Intelligent Light Control

## Übersicht

```
┌─────────────────────────────────────────────────────┐
│                Home Assistant Core                  │
│                                                     │
│  Config Entry (hub)                                 │
│  ├── ILCCoordinator                                 │
│  │   ├── ZoneController [Wohnzimmer]                │
│  │   │   ├── Motion Listener → YAMA-Logik           │
│  │   │   ├── Switch Listener → Toggle               │
│  │   │   ├── Button Listener → Toggle               │
│  │   │   ├── No-Motion Timer                        │
│  │   │   └── Manual Override Timer                  │
│  │   ├── ZoneController [Küche]                     │
│  │   └── ZoneController [...]                       │
│  │                                                  │
│  └── Entity Platforms                               │
│      ├── sensor    → ILCZoneStatusSensor            │
│      ├── switch    → ILCManualOverrideSwitch        │
│      │              ILCBlockerSwitch                │
│      ├── number    → ILCNoMotionWaitNumber          │
│      │              ILCManualOverrideDurationNumber  │
│      └── select    → ILCZoneModeSelect              │
│                      ILCSystemModeSelect             │
└─────────────────────────────────────────────────────┘
```

## Datenfluss

```
Bewegungssensor (state: on)
        │
        ▼
ZoneController._handle_motion()
        │
        ├─ Bedingungen ok? ──► Nein: ignorieren
        │   - mode != off
        │   - automation_blocker ok
        │   - blocked == False
        │   - sun_elevation ok
        │
        ▼ Ja
_activate_time_of_day_scene()
        │
        ├─ Szene für aktuelle Uhrzeit bestimmen
        │   (sortiert nach Startzeit, letzter Treffer gewinnt)
        │
        ├─ scene.turn_on → HA Szenen-Service
        │   oder
        └─ light.turn_on → Fallback

Bewegungssensor (state: off)
        │
        ▼
No-Motion Timer starten (no_motion_wait Sekunden)
        │
        ▼ (nach Ablauf)
_on_no_motion()
        │
        ├─ no_motion_blocker ok?
        ├─ Ambient-Szene + Zeitfenster?  → scene.turn_on (ambient)
        ├─ scene_no_motion konfiguriert? → scene.turn_on (no_motion)
        └─ Fallback:                       light.turn_off
```

## Persistenz

Alle Zonenkonfigurationen werden in `config_entry.options` gespeichert:

```json
{
  "system_mode": "auto",
  "zones": {
    "wohnzimmer": {
      "zone_id": "wohnzimmer",
      "name": "Wohnzimmer",
      "lights": ["light.wohnzimmer_decke"],
      "motion_sensors": ["binary_sensor.bewegung_wohnzimmer"],
      "no_motion_wait": 180,
      ...
    }
  }
}
```

HA persistiert `config_entry.options` automatisch in `.storage/core.config_entries`.

## Listener-Lebenszeit

- Listener werden in `ZoneController.async_setup()` registriert
- Bei `async_unload()` werden alle Listener über gespeicherte `unsub`-Callables entfernt
- `update_zone` macht: unload → config ändern → setup (re-subscribe)
- Timer werden bei jedem neuen Bewegungsereignis gecancelt und neu gestartet

## Coordinator-Snapshot

`ILCCoordinator._async_update_data()` wird von `DataUpdateCoordinator` aufgerufen (und bei `async_update_listeners()`). Er liefert:

```python
{
  "wohnzimmer": {
    "state": "auto_on",           # zone_state Property
    "attributes": { ... },        # extra_state_attributes
    "mode": "auto",
    "no_motion_wait": 180,
    "blocked": False,
    "name": "Wohnzimmer"
  }
}
```

Entities lesen ausschließlich aus diesem Snapshot – keine direkten Zone-Zugriffe in Entitäts-Properties.

# CLAUDE.md – Developer Guide: Intelligent Light Control

Dieses Dokument beschreibt die Architektur, Konventionen und Workflows für die Weiterentwicklung des Plugins. Es ist primär für Claude Code und andere Entwickler gedacht.

---

## Überblick

**Domain:** `intelligent_light_control`  
**Version:** 1.0.0-alpha  
**Repo:** `Jedrimos/intelligent-light-control`  
**Schwester-Plugin:** `Jedrimos/intelligent-heating-control`

Das Plugin folgt exakt der gleichen Architektur wie `intelligent-heating-control`:
- Hub-Integration mit `config_flow: true`
- Zonen (analog zu Räumen im Heizungs-Plugin) werden via Services verwaltet
- Persistenz in `config_entry.options`
- `DataUpdateCoordinator` + `ZoneController` pro Zone

---

## Dateistruktur

```
custom_components/intelligent_light_control/
├── __init__.py           # Integration-Setup, Service-Registrierung
├── manifest.json         # HA-Manifest
├── const.py              # Alle CONF_*, SERVICE_*, MODE_* Konstanten
├── config_flow.py        # UI-Setup + Options Flow
├── coordinator.py        # ILCCoordinator – Datenhaltung, Zonen-Verwaltung
├── zone_controller.py    # ZoneController – Kern-Logik pro Zone
├── sensor.py             # ILCZoneStatusSensor
├── switch.py             # ILCManualOverrideSwitch, ILCBlockerSwitch
├── number.py             # ILCNoMotionWaitNumber, ILCManualOverrideDurationNumber
├── select.py             # ILCZoneModeSelect, ILCSystemModeSelect
├── services.yaml         # Service-Definitionen (mit deutschen Labels)
└── translations/
    ├── de.json
    └── en.json
```

---

## Kern-Architektur

### ILCCoordinator (`coordinator.py`)

Erbt von `DataUpdateCoordinator`. Verwaltet:
- Dict `_zones: dict[str, ZoneController]` – alle aktiven Zonen
- `_system_mode: str` – globaler Systemmodus
- Methoden: `async_add_zone`, `async_remove_zone`, `async_update_zone`, `async_set_system_mode`
- Persistenz: alle Zonenkonfigurationen landen in `config_entry.options["zones"]`
- `_async_update_data()` liefert einen Snapshot aller Zonenzustände → Entities lesen daraus

### ZoneController (`zone_controller.py`)

Ein Controller pro Zone. Verwaltet:
- State-Change-Listener für Bewegungssensoren, Schalter, Taster
- YAMA-Logik: `_on_motion_detected()`, `_on_no_motion()`, `_activate_time_of_day_scene()`
- Timer: `_no_motion_cancel` (asyncio), `_manual_override_cancel` (asyncio)
- Bedingungsprüfungen: `_automation_blocker_ok()`, `_no_motion_blocker_ok()`, `_sun_elevation_ok()`
- Direkte Steuerung: `async_turn_on()`, `async_turn_off()`, `async_toggle()`, `async_activate_scene()`

### YAMA-Szenen-Logik

Szenen werden nach Startzeit sortiert. Die letzte Szene deren `start_time <= jetzt` wird aktiviert.
Beispiel bei Startzeiten 06:00 / 09:00 / 17:00 / 22:00 und aktuell 14:30 → Tag-Szene.
Bei 23:00 → Nacht-Szene. Bei 05:00 (vor 06:00) → Nacht-Szene (letzte in der sortierten Liste).

### Schalter vs. Taster

| Typ | Verhalten |
|-----|-----------|
| **Schalter (Toggle)** | Reagiert auf **jeden State-Change** (`on→off` oder `off→on`) → togglet Zone |
| **Taster (Momentary)** | Reagiert auf **jeden neuen State** (jeder Druck ändert `input_button`-Timestamp) → togglet Zone |

Beide wechseln die Zone in `MODE_MANUAL` und starten den Manual-Override-Timer.

---

## 5-Dateien-Regel

Wenn ein neues Zonen-Konfigurationsfeld hinzukommt, muss es in **5 Dateien** angepasst werden:

1. `const.py` – `CONF_*` Konstante + ggf. `DEFAULT_*`
2. `zone_controller.py` – Verwendung in Logik
3. `__init__.py` – Service-Schemas (`_ZONE_FIELDS`, `_ADD_ZONE_SCHEMA`, `_UPDATE_ZONE_SCHEMA`)
4. `services.yaml` – Felddefinition für `add_zone` und `update_zone`
5. `translations/de.json` + `translations/en.json` – ggf. Label

---

## Git-Workflow

- **Feature-Branch:** `claude/lighting-control-plugin-pnfCM`
- **Commit-Format:** `feat:`, `fix:`, `docs:`, `refactor:` prefix (Conventional Commits)
- Nur committen wenn alle Plattformen korrekt laden (kein `async_setup_entry` Exception)

---

## Neue Zone hinzufügen (Service)

```yaml
service: intelligent_light_control.add_zone
data:
  name: "Küche"
  lights: [light.kueche]
  motion_sensors: [binary_sensor.bewegung_kueche]
  no_motion_wait: 120
  scene_morning: scene.kueche_morgen
  time_scene_morning: "06:00:00"
  scene_day: scene.kueche_tag
  time_scene_day: "09:00:00"
  scene_evening: scene.kueche_abend
  time_scene_evening: "17:00:00"
  scene_night: scene.kueche_nacht
  time_scene_night: "22:00:00"
  buttons: [input_button.taster_kueche]
```

---

## Neue Plattform hinzufügen

1. Neue Datei `xyz.py` erstellen (analog zu `sensor.py`)
2. `"xyz"` zu `PLATFORMS` in `const.py` hinzufügen
3. In `async_setup_entry` wird sie automatisch über `async_forward_entry_setups` geladen

---

## Häufige Fehler

| Problem | Ursache | Fix |
|---------|---------|-----|
| Entity erscheint nicht | Zone wurde nach `async_setup_entry` hinzugefügt, aber Listener registriert keine neuen Entities | `_handle_new_zones` in jeder Plattform prüfen |
| Timer läuft nicht | `hass.loop.call_later` braucht laufenden Event-Loop | Nur in `async_*` Methoden aufrufen |
| Service-Schema-Fehler | Voluptuous-Validierung schlägt fehl | `vol.Optional` vs `vol.Required` prüfen; Typen angleichen |
| Zone nicht gefunden | `zone_id` falsch geschrieben | `coordinator.get_zone(zone_id)` gibt `None` → Error im Log |

---

## Testing

Manuell in HA Developer Tools → Services testen:
```yaml
# Status prüfen
service: intelligent_light_control.export_config

# Zone neu laden
service: intelligent_light_control.reload
```

Logs: `Logger: custom_components.intelligent_light_control` auf `debug` setzen.

---

## Verwandte Ressourcen

- [Home Assistant Integration Development](https://developers.home-assistant.io/docs/creating_integration_manifest)
- [DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities)
- [YAMA Blueprint](https://gist.github.com/networkingcat/a1876d7e706e07c8bdcf974113940fb8)
- [Intelligent Heating Control](https://github.com/Jedrimos/intelligent-heating-control) – Referenz-Architektur

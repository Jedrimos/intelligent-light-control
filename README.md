# Intelligent Light Control

[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-%3E%3D2023.6.0-blue.svg)](https://www.home-assistant.io/)
[![Version](https://img.shields.io/badge/version-1.0.0--alpha-yellow.svg)](CHANGELOG.md)

Intelligente Beleuchtungssteuerung für Home Assistant – mit zonenbasierter Bewegungserkennung, Tageszeit-Szenen (YAMA-Logik), Ambient-Unterstützung und direkter Verwaltung von physischen Schaltern und Tastern.

---

## Features

- **Bewegungsbasierte Automation** (YAMA-Logik): Licht geht bei Bewegung an, nach konfigurierbarer Wartezeit wieder aus
- **4 Tageszeit-Szenen**: Morgen, Tag, Abend, Nacht – jeweils mit frei wählbarer Startzeit
- **Ambient-Szene**: Aktiviert sich im No-Motion-Zustand innerhalb eines definierten Zeitfensters
- **Sonnenhöhen-Check**: Automation läuft nur wenn die Sonne niedrig genug steht
- **Automation-Blocker**: Beliebige HA-Entität kann die gesamte Automation pausieren
- **Kein-Bewegung-Blocker**: Verhindert gezielt das Ausschalten (z. B. während Filmabend)
- **Physische Schalter (Toggle)**: Wandschalter steuern die Zone direkt – wechseln in manuellen Modus
- **Taster (Momentary)**: `input_button` / `event`-Entitäten schalten die Zone um
- **Manueller Override**: Zeitlich begrenzte manuelle Übersteuerung mit automatischer Rückkehr zu Auto
- **Mehrere Zonen**: Unbegrenzt viele Lichtzonen (Räume, Bereiche), jeweils unabhängig konfigurierbar
- **HACS-kompatibel**: Einfache Installation über HACS als Custom Repository

---

## Unterstützte Entities pro Zone

| Entity | Typ | Beschreibung |
|--------|-----|--------------|
| `sensor.{zone}_status` | Sensor | Aktueller Zustand der Zone |
| `switch.{zone}_manual_override` | Switch | Manuellen Override aktivieren |
| `switch.{zone}_blocker` | Switch | Automation blockieren |
| `select.{zone}_mode` | Select | Modus: `auto` / `manual` / `off` |
| `number.{zone}_no_motion_wait` | Number | Wartezeit in Sekunden |
| `number.{zone}_manual_override_duration` | Number | Override-Dauer in Sekunden |

Zusätzlich: `select.{name}_systemmodus` – globaler Systemmodus.

---

## Installation

### HACS (empfohlen)

1. HACS → Integrationen → ⋮ → Custom Repositories
2. URL: `https://github.com/Jedrimos/intelligent-light-control`  Kategorie: `Integration`
3. Integration installieren → Home Assistant neu starten
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Intelligent Light Control**

### Manuell

```
custom_components/intelligent_light_control/ → config/custom_components/
```

---

## Schnellstart

### 1. Integration einrichten

Integration über die UI hinzufügen, Namen vergeben.

### 2. Erste Zone anlegen

```yaml
service: intelligent_light_control.add_zone
data:
  name: "Wohnzimmer"
  lights:
    - light.wohnzimmer_decke
    - light.wohnzimmer_stehlampe
  motion_sensors:
    - binary_sensor.bewegung_wohnzimmer
  no_motion_wait: 180
  scene_morning: scene.wohnzimmer_morgen
  time_scene_morning: "06:30:00"
  scene_day: scene.wohnzimmer_tag
  time_scene_day: "09:00:00"
  scene_evening: scene.wohnzimmer_abend
  time_scene_evening: "17:00:00"
  scene_night: scene.wohnzimmer_nacht
  time_scene_night: "22:00:00"
```

### 3. Schalter / Taster hinzufügen

```yaml
service: intelligent_light_control.update_zone
data:
  zone_id: "wohnzimmer"
  switches:
    - input_boolean.schalter_wohnzimmer   # Toggle-Schalter
  buttons:
    - input_button.taster_wohnzimmer      # Taster / Momentschalter
```

---

## Dokumentation

- [Architektur](docs/architecture.md)
- [Installation](docs/installation.md)
- [Konfiguration](docs/configuration.md)
- [Entities](docs/entities.md)
- [Services](docs/services.md)

---

## Verwandte Projekte

- [Intelligent Heating Control](https://github.com/Jedrimos/intelligent-heating-control) – Das Schwester-Plugin für Heizungssteuerung

---

## Lizenz

MIT License – © Jedrimos

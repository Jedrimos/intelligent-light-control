# Konfiguration

Alle Einstellungen werden über Services vorgenommen. Es gibt keine YAML-Konfiguration.

---

## Zone anlegen – `add_zone`

```yaml
service: intelligent_light_control.add_zone
data:
  # Pflichtfelder
  name: "Wohnzimmer"
  lights:
    - light.wohnzimmer_decke
    - light.wohnzimmer_stehlampe

  # Bewegungssensoren (optional, aber ohne keine Auto-Steuerung)
  motion_sensors:
    - binary_sensor.bewegung_wohnzimmer

  # Wartezeit nach letzter Bewegung (Sekunden, Standard: 120)
  no_motion_wait: 180

  # Sonnenhöhen-Check (optional)
  # Automation läuft nur wenn Sonne <= diesem Wert steht
  # Negative Werte = Sonne unter Horizont
  sun_elevation_check: 5.0

  # Automation-Blocker (optional)
  # Beliebige HA-Entität – wenn im gewünschten Zustand: Automation pausiert
  automation_blocker: input_boolean.party_modus
  automation_blocker_state: "on"   # "on" oder "off"

  # Kein-Bewegung-Blocker (optional)
  # Verhindert nur das Ausschalten, nicht das Einschalten
  no_motion_blocker: input_boolean.film_laeuft
  no_motion_blocker_state: "on"

  # Tageszeit-Szenen (optional, je 4 Szene + Startzeit)
  scene_morning: scene.wohnzimmer_morgen
  time_scene_morning: "06:30:00"

  scene_day: scene.wohnzimmer_tag
  time_scene_day: "09:00:00"

  scene_evening: scene.wohnzimmer_abend
  time_scene_evening: "17:00:00"

  scene_night: scene.wohnzimmer_nacht
  time_scene_night: "22:00:00"

  # Ambient-Szene (optional)
  # Wird bei Kein-Bewegung aktiviert, wenn innerhalb des Zeitfensters
  scene_ambient: scene.wohnzimmer_ambient
  time_scene_ambient_start: "18:00:00"
  time_scene_ambient_end: "23:00:00"

  # Kein-Bewegung-Szene (optional)
  # Fallback außerhalb des Ambient-Zeitfensters (statt turn_off)
  scene_no_motion: scene.wohnzimmer_nachtlicht

  # Physische Schalter (Toggle-Schalter) (optional)
  switches:
    - input_boolean.wandschalter_wohnzimmer

  # Taster / Momentschalter (optional)
  buttons:
    - input_button.taster_wohnzimmer

  # Manueller Override Dauer (Sekunden, Standard: 3600)
  # Danach wechselt Zone automatisch zurück zu Auto
  # 0 = unbegrenzt
  manual_override_duration: 7200
```

---

## Zonen-ID

Die `zone_id` wird automatisch generiert wenn nicht angegeben (kurzer UUID-String).
Sie kann auch explizit gesetzt werden:

```yaml
service: intelligent_light_control.add_zone
data:
  zone_id: "wohnzimmer"
  name: "Wohnzimmer"
  lights: [light.wohnzimmer]
```

> **Wichtig:** Die `zone_id` ist unveränderlich und dient als Schlüssel in allen anderen Services.

---

## Zone aktualisieren – `update_zone`

Alle Felder außer `zone_id` sind optional – nur die angegebenen werden geändert:

```yaml
service: intelligent_light_control.update_zone
data:
  zone_id: "wohnzimmer"
  no_motion_wait: 300
  scene_night: scene.wohnzimmer_sehr_dunkel
```

---

## Szenen-Zeitlogik

Die 4 Tageszeit-Szenen teilen den Tag in Perioden auf. Die Szene mit der letzten Startzeit ≤ aktueller Uhrzeit wird aktiviert.

**Beispiel:**
```
06:30 → Morgen
09:00 → Tag
17:00 → Abend
22:00 → Nacht
```

| Uhrzeit | Aktive Szene |
|---------|-------------|
| 05:00   | Nacht (letzte vor Tagesende) |
| 07:00   | Morgen |
| 14:00   | Tag |
| 19:00   | Abend |
| 23:00   | Nacht |

Wenn **keine** Szene konfiguriert ist → Fallback `light.turn_on` bei Bewegung, `light.turn_off` bei Kein-Bewegung.

---

## Schalter vs. Taster

### Schalter (Toggle-Schalter)
- Jede State-Änderung (`on→off` oder `off→on`) togglet die Zone
- Geeignet für: `switch.*`, `input_boolean.*`, physische Wandschalter via HA

### Taster (Momentary / Taster)
- Jeder neue State (Timestamp-Änderung) togglet die Zone
- Geeignet für: `input_button.*`, `event.*`, ZHA-Taster-Events

```yaml
service: intelligent_light_control.update_zone
data:
  zone_id: "kueche"
  switches:
    - input_boolean.schalter_kueche     # Toggle-Schalter
  buttons:
    - input_button.taster_kueche        # Taster
    - event.zigbee_taster_kueche        # ZHA/Z2M Event-Entität
```

---

## Globaler Systemmodus

```yaml
service: intelligent_light_control.set_system_mode
data:
  mode: "off"   # auto | manual | off
```

Der Systemmodus ist aktuell informativ. Pro-Zone-Modus hat Vorrang.

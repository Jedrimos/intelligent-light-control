# Services

Alle Services sind unter der Domain `intelligent_light_control` registriert.

---

## `add_zone`

Fügt eine neue Beleuchtungszone hinzu.

```yaml
service: intelligent_light_control.add_zone
data:
  name: "Wohnzimmer"                    # Pflicht
  lights: [light.wohnzimmer]            # Pflicht
  zone_id: "wohnzimmer"                 # Optional (wird generiert wenn leer)
  motion_sensors: [binary_sensor.x]     # Optional
  no_motion_wait: 120                   # Optional, Standard: 120s
  sun_elevation_check: 3.0              # Optional
  automation_blocker: input_boolean.x   # Optional
  automation_blocker_state: "on"        # Optional, "on"/"off"
  no_motion_blocker: input_boolean.y    # Optional
  no_motion_blocker_state: "on"         # Optional
  scene_morning: scene.morgen           # Optional
  time_scene_morning: "06:00:00"        # Optional
  scene_day: scene.tag                  # Optional
  time_scene_day: "09:00:00"            # Optional
  scene_evening: scene.abend            # Optional
  time_scene_evening: "17:00:00"        # Optional
  scene_night: scene.nacht              # Optional
  time_scene_night: "22:00:00"          # Optional
  scene_ambient: scene.ambient          # Optional
  time_scene_ambient_start: "18:00:00"  # Optional
  time_scene_ambient_end: "23:00:00"    # Optional
  scene_no_motion: scene.nachtlicht     # Optional
  switches: [input_boolean.schalter]    # Optional
  buttons: [input_button.taster]        # Optional
  manual_override_duration: 3600        # Optional, Standard: 3600s
```

---

## `remove_zone`

Entfernt eine Zone. Alle zugehörigen Entitäten werden gelöscht.

```yaml
service: intelligent_light_control.remove_zone
data:
  zone_id: "wohnzimmer"
```

---

## `update_zone`

Aktualisiert die Konfiguration einer bestehenden Zone. Nur angegebene Felder werden geändert.

```yaml
service: intelligent_light_control.update_zone
data:
  zone_id: "wohnzimmer"
  no_motion_wait: 300
  scene_night: scene.wohnzimmer_sehr_dunkel
  buttons:
    - input_button.neuer_taster
```

---

## `set_zone_mode`

Setzt den Betriebsmodus einer Zone direkt.

```yaml
service: intelligent_light_control.set_zone_mode
data:
  zone_id: "wohnzimmer"
  mode: "manual"    # auto | manual | off
```

---

## `turn_on_zone`

Schaltet die Lichter einer Zone ein und wechselt in manuellen Modus.

```yaml
service: intelligent_light_control.turn_on_zone
data:
  zone_id: "wohnzimmer"
```

---

## `turn_off_zone`

Schaltet die Lichter einer Zone aus und wechselt in manuellen Modus.

```yaml
service: intelligent_light_control.turn_off_zone
data:
  zone_id: "wohnzimmer"
```

---

## `toggle_zone`

Schaltet die Lichter einer Zone um (ein ↔ aus).

```yaml
service: intelligent_light_control.toggle_zone
data:
  zone_id: "wohnzimmer"
```

---

## `activate_scene`

Aktiviert eine bestimmte Szene in einer Zone (wechselt in manuellen Modus).

```yaml
service: intelligent_light_control.activate_scene
data:
  zone_id: "wohnzimmer"
  scene_id: "scene.wohnzimmer_film"
```

---

## `set_system_mode`

Setzt den globalen Systemmodus.

```yaml
service: intelligent_light_control.set_system_mode
data:
  mode: "off"    # auto | manual | off
```

---

## `reload`

Lädt die Integration vollständig neu (alle Zones werden neu initialisiert).

```yaml
service: intelligent_light_control.reload
```

---

## `export_config`

Exportiert die aktuelle Konfiguration aller Zonen als `persistent_notification` in HA.  
Nützlich für Backup oder Debugging.

```yaml
service: intelligent_light_control.export_config
```

Die Notification erscheint unter **Benachrichtigungen** mit dem Titel „ILC – Konfiguration".

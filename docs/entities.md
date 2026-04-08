# Entities

Pro Zone werden automatisch 6 Entitäten erstellt, plus 1 globale Select-Entität.

---

## Pro Zone

### `sensor.{zone_name}_status`

Zeigt den aktuellen Betriebszustand der Zone.

| Zustand | Beschreibung |
|---------|-------------|
| `auto_on` | Automatik aktiv, Licht an |
| `auto_off` | Automatik aktiv, Licht aus |
| `manual_on` | Manueller Modus, Licht an |
| `manual_off` | Manueller Modus, Licht aus |
| `blocked` | Automation blockiert |
| `disabled` | Zone deaktiviert (`mode: off`) |

**Attribute:**

| Attribut | Beschreibung |
|----------|-------------|
| `mode` | Aktueller Modus (`auto` / `manual` / `off`) |
| `lights_on` | Boolean: Lichter an? |
| `active_scene` | Entity-ID der aktiven Szene (oder `null`) |
| `motion_detected` | Boolean: Bewegung aktuell erkannt? |
| `last_motion` | ISO-Timestamp der letzten Bewegung |
| `zone_id` | Interne Zonen-ID |

---

### `switch.{zone_name}_manueller_override`

Aktiviert / deaktiviert den manuellen Override-Modus.

- **Ein** → Zone wechselt zu `MODE_MANUAL`
- **Aus** → Zone wechselt zurück zu `MODE_AUTO`

---

### `switch.{zone_name}_blockiert`

Blockiert die gesamte Automation für die Zone.

- **Ein** → Zonenstatus wird `blocked`, keine Bewegungsreaktion
- **Aus** → Automation läuft wieder normal

---

### `select.{zone_name}_modus`

Setzt den Betriebsmodus der Zone direkt.

| Option | Beschreibung |
|--------|-------------|
| `auto` | Bewegungsbasierte Steuerung (Standard) |
| `manual` | Manuelle Steuerung, kein automatisches Ausschalten |
| `off` | Zone vollständig deaktiviert |

---

### `number.{zone_name}_wartezeit_kein_bewegung`

Konfiguriert die Wartezeit nach der letzten Bewegung (in Sekunden).

- Bereich: 0–3600 s
- Standard: 120 s

Änderungen wirken sofort (kein Neustart nötig).

---

### `number.{zone_name}_manueller_override_dauer`

Konfiguriert wie lange der manuelle Modus anhält, bevor automatisch auf `auto` zurückgewechselt wird.

- Bereich: 0–86400 s (0 = unbegrenzt)
- Standard: 3600 s (1 Stunde)

---

## Global (Hub)

### `select.{name}_systemmodus`

Globaler Systemmodus der gesamten Integration.

| Option | Beschreibung |
|--------|-------------|
| `auto` | Normalbetrieb |
| `manual` | Alle Zonen ignorieren Automation |
| `off` | Alle Zonen deaktiviert |

---

## Lovelace-Karte (Beispiel)

```yaml
type: entities
title: Wohnzimmer Licht
entities:
  - entity: sensor.wohnzimmer_status
  - entity: select.wohnzimmer_modus
  - entity: switch.wohnzimmer_manueller_override
  - entity: switch.wohnzimmer_blockiert
  - entity: number.wohnzimmer_wartezeit_kein_bewegung
  - entity: number.wohnzimmer_manueller_override_dauer
```

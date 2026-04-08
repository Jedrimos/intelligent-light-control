# Installation

## Voraussetzungen

- Home Assistant ≥ 2023.6.0
- HACS (empfohlen) oder manuelle Installation

---

## Via HACS (empfohlen)

1. **HACS öffnen** → Integrationen → Rechts oben ⋮ → **Custom Repositories**
2. URL eingeben: `https://github.com/Jedrimos/intelligent-light-control`  
   Kategorie: **Integration** → Hinzufügen
3. Integration in HACS suchen: **Intelligent Light Control** → Installieren
4. Home Assistant **neu starten**
5. **Einstellungen → Geräte & Dienste → + Integration hinzufügen**  
   → „Intelligent Light Control" suchen → Einrichten

---

## Manuell

1. Ordner `custom_components/intelligent_light_control/` aus dem Repository herunterladen
2. In `<config>/custom_components/intelligent_light_control/` kopieren
3. Home Assistant neu starten
4. Integration wie oben beschrieben einrichten

---

## Einrichtung (Config Flow)

Nach dem Hinzufügen erscheint ein Dialog:

| Feld | Beschreibung |
|------|-------------|
| **Name** | Anzeigename der Integration (z. B. „Intelligent Light Control") |

Zonen werden **nicht** im Setup-Dialog konfiguriert, sondern danach via Services.

---

## Erste Zone einrichten

In **Entwicklerwerkzeuge → Services**:

```yaml
service: intelligent_light_control.add_zone
data:
  name: "Wohnzimmer"
  lights:
    - light.wohnzimmer
  motion_sensors:
    - binary_sensor.bewegung_wohnzimmer
  no_motion_wait: 120
```

Nach dem Aufruf erscheinen die Entitäten der Zone sofort in HA.

---

## Deinstallation

1. **Einstellungen → Geräte & Dienste** → Integration auswählen → Löschen
2. HACS → Integration deinstallieren (oder `custom_components/` Ordner löschen)
3. HA neu starten

> **Hinweis:** Beim Löschen der Integration werden alle Zonenkonfigurationen entfernt.

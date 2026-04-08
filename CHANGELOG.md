# Changelog

All notable changes to **Intelligent Light Control** will be documented in this file.

Format: [Semantic Versioning](https://semver.org/)

---

## [1.0.0-alpha] – 2026-04-08

### Added
- Initiale Veröffentlichung als HACS Custom Integration
- **Zonen-Management**: Beliebig viele Lichtzonen via Services verwalten (`add_zone`, `remove_zone`, `update_zone`)
- **YAMA-Bewegungslogik**: Vollständige Implementierung der "Yet Another Motion Automation"-Logik
  - 4 konfigurierbare Tageszeit-Szenen (Morgen, Tag, Abend, Nacht)
  - Ambient-Szene mit Start-/Endzeit-Fenster
  - Wartezeit (No-Motion-Wait) 0–3600 s
  - Fallback `light.turn_on` / `light.turn_off` wenn keine Szene konfiguriert
- **Automation-Blocker**: Beliebige HA-Entität als Blocker für die gesamte Automation (wählbarer Zustand)
- **Kein-Bewegung-Blocker**: Verhindert das Ausschalten unabhängig vom Automation-Blocker
- **Sonnenhöhen-Check**: Automation läuft nur unterhalb eines konfigurierbaren Elevations-Schwellwerts
- **Physische Schalter (Toggle)**: State-Change-basierte Steuerung – wechselt Zone in manuellen Modus
- **Taster / Momentschalter**: Unterstützung für `input_button` und `event`-Entitäten
- **Manueller Override**: Zeitlich begrenzte Übersteuerung mit automatischer Rückkehr zu Auto-Modus
- **Entity-Plattformen**:
  - `sensor` – Zonenstatus (`auto_on`, `auto_off`, `manual_on`, `manual_off`, `blocked`, `disabled`)
  - `switch` – Manual-Override-Switch, Blocker-Switch
  - `number` – Wartezeit, Override-Dauer (je Zone)
  - `select` – Zonenmodus, Systemmodus (hub-weit)
- **Services** (11): `add_zone`, `remove_zone`, `update_zone`, `set_zone_mode`, `turn_on_zone`, `turn_off_zone`, `toggle_zone`, `activate_scene`, `set_system_mode`, `reload`, `export_config`
- Übersetzungen: Deutsch (`de.json`) und Englisch (`en.json`)
- Config Flow mit UI-gestützter Einrichtung und Options Flow
- HACS-kompatibel (`hacs.json`, `manifest.json`)

---

## Geplant

Siehe [ROADMAP.md](ROADMAP.md)

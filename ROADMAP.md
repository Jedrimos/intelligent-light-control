# Roadmap – Intelligent Light Control

## v1.0.0-alpha (aktuell)
- [x] Zonen-Management (add/remove/update via Services)
- [x] YAMA-Bewegungslogik (4 Tageszeit-Szenen, Ambient, Wartezeit)
- [x] Automation-Blocker + Kein-Bewegung-Blocker
- [x] Sonnenhöhen-Check
- [x] Physische Schalter (Toggle) + Taster (Momentary)
- [x] Manueller Override mit Ablaufzeit
- [x] Entity-Plattformen: sensor, switch, number, select
- [x] 11 Services
- [x] Übersetzungen DE + EN
- [x] HACS-kompatibel

---

## v1.1.0 – Frontend-Panel
- [ ] Custom Lovelace Panel (analog zu `ihc-panel.js` im Heizungs-Plugin)
  - Übersicht aller Zonen mit Statusanzeige
  - Inline-Steuerung (Ein/Aus, Modus, Szene)
  - Zonen-Konfiguration über Panel-UI (statt Services)
  - Tageszeit-Szenen-Vorschau

---

## v1.2.0 – Erweiterte Szenen-Steuerung
- [ ] Helligkeits-Override pro Tageszeit (Brightness % unabhängig von Szene)
- [ ] Farbtemperatur-Override pro Tageszeit (Kelvin)
- [ ] Dynamische Helligkeit basierend auf Sonnenhöhe (adaptives Dimmen)
- [ ] Transition-Zeit konfigurierbar pro Szene

---

## v1.3.0 – Gruppen
- [ ] Zonengruppen: Mehrere Zonen gemeinsam steuern
- [ ] Service `add_group`, `remove_group`, `set_group_mode`
- [ ] Gruppen-Szenen (eine Szene für alle Zonen der Gruppe)

---

## v1.4.0 – Präsenz-Integration
- [ ] Personen-/Anwesenheits-Entities als Trigger (Anwesenheit = Zone aktiv halten)
- [ ] Automatische Abwesenheit nach konfigurierbarer Delay
- [ ] Gästemodus (alle Zonen auf Manual für X Stunden)

---

## v1.5.0 – Energiesparmodus
- [ ] Lux-Sensor-Integration: Licht nur einschalten wenn Umgebungshelligkeit unter Schwellwert
- [ ] Sonnenaufgang/-untergang als alternative Zeitbedingung
- [ ] Integration mit `sun.sun` für automatische Licht-Notwendigkeits-Berechnung

---

## v1.6.0 – Taster-Erweiterungen
- [ ] Doppelklick-Erkennung (Taster): z. B. Doppelklick → nächste Szene
- [ ] Langer Druck (via `zha_event` / `deconz_event`): z. B. Dimmen
- [ ] ZHA / deCONZ / Z2M Event-Entitäten als Button-Quelle

---

## v2.0.0 – Adaptives Licht
- [ ] Circadian-Lighting-Integration (automatische Farbtemperatur nach Tageszeit)
- [ ] Lernfunktion: Häufig genutzte Einstellungen pro Raum/Uhrzeit merken
- [ ] Vorhersage-basiertes Einschalten (z. B. kurz vor üblicher Heimkehr-Zeit)

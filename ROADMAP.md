# Roadmap – Intelligent Light Control

## v1.0.0-alpha (aktuell – in Entwicklung)

### Bereits implementiert
- [x] Zonen-Management (add/remove/update via Services + UI)
- [x] Zonen benennen – jede Zone hat einen frei wählbaren Anzeigenamen
- [x] YAMA-Bewegungslogik (4 Tageszeit-Szenen, Ambient, Wartezeit)
- [x] Automation-Blocker + Kein-Bewegung-Blocker
- [x] Sonnenhöhen-Check
- [x] Physische Schalter (Toggle) + Taster (Momentary) – zonenweite Steuerung
- [x] Serienschalter – jeder Wipper steuert nur seine zugeordnete Leuchte
- [x] Manueller Override mit Ablaufzeit + Rückkehr zu Auto
- [x] Erweitertes Presence Detection:
  - Präsenzsensoren (mmWave-Radar, Occupancy-Sensoren, beliebige binary_sensor)
  - Media Player (TV, Lautsprecher) – playing/paused zählt als Präsenz
  - Stromverbrauchssensoren (in W) – Gerät zieht mehr als X Watt = jemand ist da
  - Licht bleibt an so lange mindestens eine Quelle Präsenz meldet
- [x] Ambient-Trigger: Zeitfenster ODER Sonnenuntergang (`sun.sun below_horizon`)
- [x] Schalter/Taster: Licht an → Aus, Licht aus → passende Tageszeit-Szene
- [x] Entity-Plattformen: sensor, switch, number, select
- [x] 11 Services (add/remove/update/toggle/scene/mode etc.)
- [x] Multi-Step Options Flow – Zones komplett via UI konfigurierbar
- [x] Übersetzungen DE + EN
- [x] HACS-kompatibel

### Bugfixes (bereits gepatcht)
- [x] Multi-Sensor-Bug: Timer startet jetzt erst wenn ALLE Sensoren inaktiv sind
- [x] Series-Light State-Timing: kein Race Condition nach `blocking=False`
- [x] Presence-Recheck: kein Busy-Loop bei `no_motion_wait=0`

---

## v1.1.0 – Frontend-Panel
- [ ] Custom Lovelace Panel
  - Übersicht aller Zonen mit Statusanzeige und Echtzeit-Vorschau
  - Inline-Steuerung (Ein/Aus, Modus, Szene, Helligkeit)
  - Zonen-Konfiguration direkt im Panel (kein Umweg über Services)
  - Tageszeit-Zeitleiste: zeigt welche Szene wann aktiv wird
  - Letzte Aktivität pro Zone (wann zuletzt Bewegung, welche Szene)
- [ ] **Übergangszeiten (Transition)** pro Szene – sanftes Ein-/Ausblenden (in ms) statt hartem Umschalten
- [ ] **Szenen-Favoriten** – bis zu 5 Favoriten pro Zone speicherbar, per Taster direkt abrufbar

---

## v1.2.0 – Taster-Erweiterungen (Multi-Tap & Long-Press)
- [ ] **Einfachklick**: Ein/Aus wie bisher
- [ ] **Doppelklick**: nächste Tageszeit-Szene (Morgen → Tag → Abend → Nacht → ...)
- [ ] **Dreifachklick**: direkt zu konfigurierter Lieblingsszene springen
- [ ] **Langer Druck**: Dimmen (heller / dunkler)
- [ ] **ZHA / deCONZ / Z2M Event-Entitäten** als Taster-Quelle
  - Unterstützung für Zigbee-Taster (IKEA, Philips Hue, Aqara, Sonoff, etc.)
  - Mapping von ZHA-Actions auf Zonen-Aktionen per UI

---

## v1.3.0 – Circadian Lighting (Biologisch korrektes Licht)
- [ ] Automatische Farbtemperatur nach Tageszeit (warm morgens/abends, kalt mittags)
- [ ] Automatische Helligkeit nach Tageszeit (sanftes Aufwachen, volle Helligkeit tagsüber)
- [ ] Sonnenposition als Basis (keine festen Uhrzeiten nötig)
- [ ] Override: manuelle Szene deaktiviert Circadian temporär, kehrt danach zurück
- [ ] Konfigurierbarer Circadian-Bereich pro Zone (Küche anders als Schlafzimmer)

---

## v1.4.0 – Lux-Sensor & Wetterintegration
- [ ] **Lux-Sensor**: Licht nur einschalten wenn Umgebungshelligkeit unter Schwellwert
  - Verhindert unnötiges Einschalten bei hellem Tageslicht
  - Konfigurierbar pro Zone (Küche: 100 lx, Wohnzimmer: 50 lx)
- [ ] **Wetter-basiert**: bewölkter Tag → Lichter früher einschalten
  - Integration mit `weather.*` Entity
  - Schwellwert: Bedeckungsgrad in % ab dem früher eingeschaltet wird
- [ ] **Sonnenauf-/-untergang als Szenen-Trigger** (statt fixer Uhrzeiten optional)
  - z. B. „30 Minuten vor Sonnenuntergang → Abend-Szene"

---

## v1.5.0 – Zonengruppen & Raumverknüpfung
- [ ] **Zonengruppen**: Mehrere Zonen gemeinsam steuern (z. B. „Erdgeschoss", „Alle Schlafen")
  - Services: `add_group`, `remove_group`, `set_group_mode`
  - Gruppen-Szenen: koordinierte Szenen in allen Zonen der Gruppe
- [ ] **Raum-Linking**: Bewegung in Zone A aktiviert/dimmt Zone B vor
  - z. B. Bewegung im Flur → Wohnzimmer dimmt auf 20% vor
  - Konfigurierbar: Quellzone → Zielzone → Aktion → Verzögerung
- [ ] **Schlaferkennung**: Schlafzimmer in Nacht-Modus + keine Bewegung X Minuten → alle verknüpften Zonen auf Nacht stellen
- [ ] **Szenen-Broadcast**: ein Service-Call setzt alle Zonen gleichzeitig auf eine bestimmte Szene (z. B. „Gute Nacht")

---

## v1.6.0 – Präsenz & Anwesenheit
- [ ] **Personen-Entities als Trigger**: Zone bleibt aktiv solange Person erkannt
- [ ] **Auto-Abwesenheit**: alle Zonen ausschalten wenn niemand mehr zuhause
  - Konfigurierbare Verzögerung
  - Nur Zonen im Auto-Modus betroffen
- [ ] **Ankunfts-Trigger**: Licht geht an sobald jemand nach Hause kommt
  - Tageszeit-Szene wird berücksichtigt
  - Konfigurierbar welche Zonen bei Ankunft aktiviert werden
- [ ] **Gäste-Modus**: alle Zonen für X Stunden auf manuelle Steuerung + helle Szene

---

## v1.7.0 – Medien-Integration
- [ ] **TV-Dimmen**: Licht dimmt automatisch wenn Wiedergabe startet, kehrt zurück beim Pausieren/Stoppen
  - Konfigurierbar: welcher Player → welche Zone → auf welche Helligkeit/Szene
- [ ] **Kino-Modus**: Wohnzimmer auf Kino-Szene + Flur auf 10% in einem Befehl
- [ ] **Musik-Sync**: Helligkeit/Farbe pulsiert mit Musik-Rhythmus (via `media_player` Attribute)

---

## v1.8.0 – Urlaub & Sicherheit
- [ ] **Anwesenheitssimulation**: Lichter gehen zu zufälligen Zeiten an/aus (basierend auf historischen Nutzungsmustern)
- [ ] **Sicherheits-Blitz**: alle Lichter blinken bei Alarm-Trigger (Einbruch, Feuermelder)
  - Konfigurierbar: Trigger-Entity + Blitzmuster
- [ ] **„Vergessen ausschalten"-Benachrichtigung**: Push-Notification wenn Lichter brennen obwohl niemand zuhause ist
- [ ] **Kalender-Integration**: Szenen basierend auf Kalendereinträgen
  - z. B. Eintrag „Filmabend" → Kino-Szene automatisch

---

## v1.9.0 – Energie & Statistiken
- [ ] **Energie-Tracking pro Zone**: Stunden Licht an, geschätzte kWh
- [ ] **Tagesstatistik**: wann war welche Zone wie lange aktiv
- [ ] **Solar-Optimierung**: bei Solar-Überschuss bestimmte Zonen automatisch aktivieren
- [ ] **Energie-Sparmodus**: automatisches Dimmen auf X% nach Y Minuten ohne Bewegung
  (Kompromiss zwischen Komfort und Sparsamkeit)
- [ ] **Dashboard-Karte**: Lovelace-Karte mit Verbrauchsübersicht und Zonenhistorie

---

## v2.0.0 – Adaptiv & Lernend
- [ ] **Lernfunktion**: Plugin merkt sich wann und wie Lichter genutzt werden
  - Automatisch optimierte Szenen-Startzeiten basierend auf echtem Nutzungsverhalten
  - Warnung wenn konfigurierte Szene nie tatsächlich genutzt wird
- [ ] **Vorausschauendes Einschalten**: Licht geht kurz vor üblicher Heimkehr-Zeit an
- [ ] **Stimmungserkennung via Kontext**: Tageszeit + Wetter + Wochentag → automatisch passende Szene
  - z. B. Regentag + Nachmittag + Wochenende → gemütlich-warme Szene statt Standard-Tag
- [ ] **KI-Szenenvorschläge**: schlägt neue Szenen-Konfigurationen vor basierend auf Nutzungsmustern
- [ ] **Anomalie-Erkennung**: meldet wenn Lichter ungewöhnlich lange brennen oder vergessen wurden

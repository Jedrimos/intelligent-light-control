# Roadmap – Intelligent Light Control

## v1.0.0-alpha (aktuell)
- [x] Zonen-Management (add/remove/update via Services + UI)
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
  - Übersicht aller Zonen mit Statusanzeige und Echtzeit-Vorschau
  - Inline-Steuerung (Ein/Aus, Modus, Szene, Helligkeit)
  - Zonen-Konfiguration direkt im Panel (kein Umweg über Services)
  - Tageszeit-Zeitleiste: zeigt welche Szene wann aktiv wird
  - Letzte Aktivität pro Zone (wann zuletzt Bewegung, welche Szene)

---

## v1.2.0 – Circadian Lighting (Biologisch korrektes Licht)
- [ ] Automatische Farbtemperatur nach Tageszeit (warm morgens/abends, kalt mittags)
- [ ] Automatische Helligkeit nach Tageszeit (sanftes Aufwachen, volle Helligkeit tagsüber)
- [ ] Sonnenposition als Basis (keine festen Uhrzeiten nötig)
- [ ] Override: manuelle Szene deaktiviert Circadian temporär, kehrt danach zurück
- [ ] Konfigurierbarer Circadian-Bereich pro Zone (z. B. Küche anders als Schlafzimmer)

---

## v1.3.0 – Lux-Sensor & Wetterintegration
- [ ] **Lux-Sensor**: Licht nur einschalten wenn Umgebungshelligkeit unter Schwellwert
  - Verhindert unnötiges Einschalten bei hellem Tageslicht
  - Konfigurierbar pro Zone (z. B. Küche: 100 lx, Wohnzimmer: 50 lx)
- [ ] **Wetter-basiert**: bewölkter Tag → Lichter früher einschalten
  - Integration mit `weather.*` Entity
  - Schwellwert: Bedeckungsgrad in % ab dem früher eingeschaltet wird
- [ ] **Sonnenauf-/-untergang als Szenen-Trigger** (statt fixer Uhrzeiten optional)
  - „30 Minuten vor Sonnenuntergang → Abend-Szene"

---

## v1.4.0 – Taster-Erweiterungen (Multi-Tap & Long-Press)
- [ ] **Doppelklick**: nächste Szene aktivieren (Morgen → Tag → Abend → Nacht → ...)
- [ ] **Dreifachklick**: Lieblingsszene / direkter Sprung zu konfigurierter Szene
- [ ] **Langer Druck**: Dimmen (heller / dunkler je nach Richtung)
- [ ] **ZHA / deCONZ / Z2M Event-Entitäten** als Taster-Quelle
  - Unterstützung für Zigbee-Taster (IKEA, Philips Hue, Aqara, etc.)
  - Mapping von ZHA-Actions auf Zonen-Aktionen per UI

---

## v1.5.0 – Gruppen & Szenen-Management
- [ ] **Zonengruppen**: Mehrere Zonen gemeinsam steuern (z. B. „Erdgeschoss")
- [ ] Services: `add_group`, `remove_group`, `update_group`, `set_group_mode`
- [ ] Gruppen-Szenen: eine Szene aktiviert koordinierte Szenen in allen Zonen der Gruppe
- [ ] **Szenen-Favoriten**: bis zu 5 Favoriten pro Zone speicherbar und schnell abrufbar
- [ ] **Transition-Zeit**: konfigurierbares Fade-in/Fade-out beim Ein-/Ausschalten (in ms)

---

## v1.6.0 – Präsenz & Anwesenheit
- [ ] **Personen-Entities als Trigger**: Zone bleibt aktiv solange Person im Raum erkannt
- [ ] **Auto-Abwesenheit**: alle Zonen ausschalten wenn niemand mehr zuhause
  - Konfigurierbare Verzögerung
  - Nur Zonen im Auto-Modus betroffen
- [ ] **Ankunfts-Trigger**: Licht geht an sobald jemand nach Hause kommt
  - Tageszeit-Szene wird berücksichtigt
  - Konfigurierbar welche Zonen bei Ankunft aktiviert werden
- [ ] **Gäste-Modus**: alle Zonen für X Stunden auf manuelle Steuerung + helle Szene

---

## v1.7.0 – Medien-Integration
- [ ] **TV/Medienplayer-Erkennung**: Licht dimmt automatisch wenn Wiedergabe startet
  - Konfigurierbar: welcher Medienplayer → welche Zone → auf welche Szene/Helligkeit
  - Licht kehrt nach Pausieren/Stoppen automatisch zurück
- [ ] **Kino-Modus**: Eine Taste aktiviert Kino-Szene in Wohnzimmer + schaltet Flur gedimmt
- [ ] **Musik-Sync**: Helligkeit/Farbe pulsiert mit Musik-Rhythmus (via `media_player` Attribute)

---

## v1.8.0 – Urlaub & Sicherheit
- [ ] **Urlaubs-Modus / Anwesenheitssimulation**
  - Lichter gehen zu zufälligen Zeiten an/aus (basierend auf historischen Nutzungsmustern)
  - Konfigurierbare Aktiv-Zeiten und beteiligte Zonen
- [ ] **Sicherheits-Blitz**: alle Lichter blinken bei Alarm-Trigger (Einbruch, Feuermelder)
  - Konfigurierbar: Trigger-Entity + Blitzmuster
- [ ] **„Vergessen ausschalten"-Benachrichtigung**: Push-Notification wenn Lichter brennen obwohl niemand zuhause ist
- [ ] **Kalender-Integration**: Szenen basierend auf Kalendereinträgen
  - z. B. Kalendereintrag „Filmabend" → Kino-Szene im Wohnzimmer

---

## v1.9.0 – Energie & Statistiken
- [ ] **Energie-Tracking pro Zone**: Stunden Licht an, geschätzte kWh
- [ ] **Tagesstatistik**: wann war welche Zone wie lange aktiv
- [ ] **Solar-Optimierung**: bei Solar-Überschuss bestimmte Zonen automatisch aktivieren
  - Konfigurierbar: ab X Watt Überschuss → Zone Y einschalten
- [ ] **Energie-Sparmodus**: automatisches Dimmen auf X% nach Y Minuten ohne Bewegung
  (statt sofort auszuschalten – Kompromiss zwischen Komfort und Sparsamkeit)
- [ ] **Dashboard-Karte**: Lovelace-Karte mit Verbrauchsübersicht und Zonenhistorie

---

## v2.0.0 – Adaptiv & Lernend
- [ ] **Lernfunktion**: Plugin merkt sich wann und wie Lichter genutzt werden
  - Automatisch optimierte Szenen-Startzeiten basierend auf echtem Nutzungsverhalten
  - Warnung wenn konfigurierte Szene nie tatsächlich genutzt wird
- [ ] **Vorausschauendes Einschalten**: Licht geht kurz vor üblicher Heimkehr-Zeit an
  - Trainiert sich auf Basis von Präsenz-Historie
- [ ] **Stimmungserkennung via Kontext**: Tageszeit + Wetter + Wochentag → automatisch passende Szene
  - z. B. Regentag + Nachmittag + Wochenende → gemütlich-warme Szene statt Standard-Tag
- [ ] **KI-Szenenvorschläge**: schlägt neue Szenen-Konfigurationen vor basierend auf Nutzungsmustern
- [ ] **Anomalie-Erkennung**: meldet wenn Lichter ungewöhnlich lange brennen oder vergessen wurden

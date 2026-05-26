# JANUS FEATURE SPEC – DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-018
- **Backlog Title:** CLIP-Model-Download blockiert First-Start
- **Type:** BUG

## 2. Problem / Wunsch
Janus startet auf frischen Installationen nicht zuverlässig. Der VISION-SERVICE lädt das CLIP-Model (ViT-B-32.pt, 338MB) synchron vor dem App-Start. Bei langsamer Internetverbindung oder langsamen Servern dauert der Download länger als das Windows-Process-Timeout (120 Sekunden), was dazu führt, dass Windows den Prozess tötet und eine Fehlermeldung anzeigt.

## 3. Expected Behavior
Janus startet sofort beim ersten Launch. Das CLIP-Model wird im Hintergrund nach dem Start lazy-loaded. Vision-Funktionen sind erst verfügbar nachdem das Model geladen ist, aber der Rest der App ist sofort nutzbar. Vision-Requests vor Fertigstellung des Downloads werden entweder queued oder mit "Vision noch nicht bereit" beantwortet.

## 4. Current Behavior
App startet nicht. Splashscreen bleibt hängen, Windows tötet den Process nach 120 Sekunden mit Fehlermeldung "siehe Log". Backend-Log zeigt synchronen CLIP-Model-Download (ViT-B-32.pt, 338MB) ab Zeile 47.

## 5. Scope
### IN SCOPE
- Lazy-Loading Pattern für CLIP-Model-Download
- Asynchroner Download im Hintergrund nach App-Start
- UI-Status-Indikator für "Vision wird geladen..."
- Vision-Request-Handling während laufendem Download (queue oder "nicht bereit"-Antwort)
- Fehlerbehandlung bei Download-Fehlern
- Persistenz des geladenen Models (nur einmal downloaden)
- Cross-Platform-Kompatibilität (Windows, macOS, Linux)

### OUT OF SCOPE
- Caching für andere Models (außer CLIP)
- Download-Progress-UI mit Prozentanzeige (einfacher "Loading..."-Indikator reicht)
- Download-Pause/Resume-Funktionalität
- Parallel-Download von mehreren Models
- Model-Version-Management oder Updates

## 6. Functional Requirements
- Die App startet sofort, ohne auf Model-Downloads zu warten
- Das CLIP-Model wird asynchron im Hintergrund geladen
- Vision-Funktionen sind deaktiviert oder zeigen "Loading..." bis das Model geladen ist
- Download-Fehler werden robust gehandelt (App startet trotzdem, Vision bleibt deaktiviert)
- Das Model wird nur einmal heruntergeladen und persistiert
- Kein Windows-Process-Timeout durch Model-Downloads
- Lösung funktioniert auf allen Systemen unabhängig von Internetgeschwindigkeit

## 7. Acceptance Criteria
- [ ] App startet sofort, Splashscreen verschwindet nach normalem Start
- [ ] CLIP-Model wird lazy-loaded im Hintergrund nach App-Start (nicht synchron vor dem Start)
- [ ] Vision-Funktionen sind deaktiviert oder zeigen "Loading..." bis CLIP-Model geladen ist
- [ ] Kein Windows-Process-Timeout durch Model-Downloads
- [ ] Lösung funktioniert auf allen Systemen unabhängig von Internetgeschwindigkeit
- [ ] Download-Fehler brechen nicht den App-Start (Vision bleibt deaktiviert)
- [ ] Model wird nach erfolgreichem Download persistiert und bei nächsten Starts direkt geladen

## 8. Evidence
- main.log Zeile 47+: CLIP-Model-Download startet synchron bei 23:25:27
- User-Beschreibung: "janus startet doch gar nicht, nach den 120 sekunden splashscreen kommt eine windows fehlermeldung"
- User-Requirement: "wir brauchen eine lösung, damit janus auf alles systemen startet und nicht nur auf welchen mit schnellem internet"

## 9. Risks
- **HIGH:** Änderung an kritischem First-Start-Pfad kann neue Start-Fehler einführen
- **MEDIUM:** Asynchroner Download-Code muss robust gegen Netzwerk-Fehler sein
- **MEDIUM:** UI-Konsistenz bei "Vision noch nicht bereit"-Status muss über alle Vision-Features hinweg gelten
- **LOW:** Persistenz-Logik muss korrekt sein, um wiederholte Downloads zu vermeiden

## 10. Validation Mapping
- App startet sofort → Manuellem Test: Frische Installation, Startzeit messen (<10s bis UI)
- CLIP-Model lazy-loaded → Backend-Log: Download-Start nach App-Start (nicht davor)
- Vision deaktiviert während Download → Manuellem Test: Vision-Prompt während Download liefert "Loading..."-Antwort
- Kein Windows-Process-Timeout → Manuellem Test: Langsames Netzwerk simulieren, App startet trotzdem
- Download-Fehler robust → Manuellem Test: Download simuliert fehlschlagen, App startet trotzdem
- Model persistiert → Manuellem Test: Zweiter Start nach erfolgreichem Download, kein erneuter Download

## 11. Technical Context
- Betroffener Bereich: Backend / VISION-SERVICE / First-Start Experience / Lazy-Loading
- Root Cause: VISION-SERVICE lädt CLIP-Model synchron im `__init__` oder bei Service-Initialisierung
- Model-Größe: 338MB (ViT-B-32.pt)
- Windows-Timeout: 120 Sekunden

## 12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.

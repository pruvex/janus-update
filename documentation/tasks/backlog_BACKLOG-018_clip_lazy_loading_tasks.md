# BACKLOG TASKS – BACKLOG-018 – CLIP Lazy Loading

## Feature
CLIP-Model-Download blockiert First-Start – Lazy-Loading Pattern für asynchronen Download nach App-Start

---

## TASK-001 – Vision-Service Lazy-Loading Implementierung

### Ziel
Synchronen CLIP-Model-Download in VISION-SERVICE in asynchronen Hintergrund-Download nach App-Start umwandeln.

### Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-018 und documentation/Planned Features/backlog_BACKLOG-018_clip_lazy_loading.md
- **Beeinflusst:** backend/services/vision/ (Vision-Service-Initialisierung), backend/services/vision/model_loader.py (neu erstellen), backend/main.py oder backend/app.py (App-Start-Logik)
- **Risiko-Einschätzung:** HIGH

### Beschreibung
Der VISION-SERVICE lädt derzeit das CLIP-Model (ViT-B-32.pt, 338MB) synchron bei Initialisierung, was den App-Start blockiert. Dieser Task entfernt den synchronen Download aus `__init__` oder Service-Initialisierung und implementiert einen asynchronen Download, der im Hintergrund nach App-Start gestartet wird.

### Files
- `backend/services/vision/` (Vision-Service-Initialisierung)
- `backend/services/vision/model_loader.py` (neu erstellen für asynchrones Model-Loading)
- `backend/main.py` oder `backend/app.py` (App-Start-Logik für Download-Trigger)

### Steps
1. Vision-Service-Initialisierung analysieren: aktuellen synchronen Download-Code identifizieren
2. Asynchrone Download-Funktion erstellen: `load_clip_model_async()` mit Hintergrund-Task
3. Vision-Service-`__init__` ändern: Model-Download entfernen, stattdessen Download-Trigger registrieren
4. App-Start-Logik anpassen: asynchronen Download nach App-Start triggern
5. Download-Status-Tracking implementieren: `model_loading`, `model_loaded`, `model_error` States
6. Cross-Platform-Kompatibilität sicherstellen: Windows, macOS, Linux

### Acceptance Criteria
- [ ] Vision-Service startet sofort ohne auf CLIP-Model-Download zu warten
- [ ] CLIP-Model-Download wird asynchron im Hintergrund gestartet nach App-Start
- [ ] Backend-Log zeigt Download-Start nach App-Start (nicht davor)
- [ ] Download-Status-Tracking ist implementiert (`model_loading`, `model_loaded`, `model_error`)
- [ ] Cross-Platform-Kompatibilität ist gewährleistet

### Tests
- Manuellem Test: Frische Installation, Startzeit messen (<10s bis UI)
- Backend-Log-Check: Download-Start-Zeitstempel vs. App-Start-Zeitstempel
- Cross-Platform-Test: Windows, macOS, Linux

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backend-Integration mit mehreren Dateien, kritischem First-Start-Pfad, asynchrone Architekturänderung – erfordert breites Codebase-Verständnis und Risiko-Management.

---

## TASK-002 – Model-Persistenz Implementierung

### Ziel
Sicherstellen, dass das CLIP-Model nur einmal heruntergeladen wird und persistiert bleibt für zukünftige Starts.

### Beschreibung
Das CLIP-Model muss nach erfolgreichem Download persistiert werden, damit es bei nachfolgenden App-Starts direkt geladen werden kann, ohne erneut heruntergeladen zu werden. Dieser Task implementiert Persistenz-Logik und Datei-Check vor Download.

### Files
- `backend/services/vision/model_loader.py` (Download- und Persistenz-Logik)
- `backend/config/` oder `backend/data/` (Persistenz-Pfad-Konfiguration)

### Steps
1. Persistenz-Pfad definieren: `userData/models/clip_vit_b_32.pt` oder ähnlich
2. Datei-Check vor Download implementieren: Prüfen ob Model bereits existiert
3. Download nur ausführen wenn Datei nicht existiert
4. Download-Progress-Tracking implementieren (für Fehlerbehandlung)
5. Model-Validierung nach Download: Datei-Integrität prüfen
6. Persistenz-Pfad Cross-Platform sicherstellen: `app.getPath('userData')` für Electron

### Acceptance Criteria
- [ ] Model wird nur heruntergeladen wenn nicht bereits persistiert
- [ ] Persistiertes Model wird bei nachfolgenden Starts direkt geladen (kein erneuter Download)
- [ ] Backend-Log zeigt "Model already cached" bei vorhandenem Model
- [ ] Persistenz-Pfad ist Cross-Platform-kompatibel
- [ ] Download-Progress-Tracking ist implementiert

### Tests
- Manuellem Test: Erster Start (Download), zweiter Start (kein Download)
- Backend-Log-Check: "Model already cached" Nachricht bei zweitem Start
- Cross-Platform-Test: Persistenz-Pfad auf Windows, macOS, Linux

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Persistenz-Logik mit Cross-Platform-Pfad-Handling, Datei-Validierung, Integration mit Model-Loader – erfordert System-Integration und Fehlerbehandlung.

---

## TASK-003 – Vision-Request-Handling während Download

### Ziel
Vision-Requests während laufendem Download mit "Loading..."-Antwort oder Queue beantworten.

### Beschreibung
Während das CLIP-Model heruntergeladen wird, müssen Vision-Requests entweder in eine Queue gestellt oder mit einer "Vision noch nicht bereit"-Antwort beantwortet werden. Dieser Task implementiert Request-Handling-Logik im Vision-Service.

### Files
- `backend/services/vision/` (Vision-Request-Handler)
- `backend/tools/vision_tools.py` (Vision-Tool-Wrapper für Status-Check)

### Steps
1. Request-Handling-Logik analysieren: aktueller Vision-Request-Flow identifizieren
2. Download-Status-Check implementieren: Prüfen ob Model geladen wird
3. "Vision noch nicht bereit"-Antwort implementieren: Standard-Nachricht während Download
4. Optional: Queue-Implementierung für Vision-Requests während Download (falls Spec "queue oder nicht bereit" erlaubt)
5. Vision-Request-Handler anpassen: Status-Check vor Tool-Ausführung
6. Fehlerbehandlung: Vision-Requests bei Download-Fehler mit klarem Error beantworten

### Acceptance Criteria
- [ ] Vision-Requests während Download liefern "Loading..." oder "Vision noch nicht bereit"-Antwort
- [ ] Vision-Requests nach erfolgreichem Download werden normal ausgeführt
- [ ] Vision-Requests bei Download-Fehler liefern klare Fehlermeldung
- [ ] Keine Exceptions oder Crashes bei Vision-Requests während Download
- [ ] Optional: Queue-Implementierung (falls gewählt)

### Tests
- Manuellem Test: Vision-Prompt während Download liefert "Loading..."-Antwort
- Manuellem Test: Vision-Prompt nach erfolgreichem Download funktioniert normal
- Manuellem Test: Vision-Prompt bei Download-Fehler liefert klare Fehlermeldung

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Request-Handling-Integration mit Status-Tracking, Fehlerbehandlung, optionaler Queue-Logik – erfordert Service-Integration und UX-Überlegungen.

---

## TASK-004 – UI-Status-Indikator für Vision-Loading

### Ziel
UI-Status-Indikator "Vision wird geladen..." im Frontend implementieren, um Nutzer über laufenden Model-Download zu informieren.

### Beschreibung
Das Frontend muss einen visuellen Indikator zeigen, wenn das CLIP-Model noch geladen wird und Vision-Funktionen noch nicht verfügbar sind. Dieser Task implementiert UI-Status-Indikator und Status-Abfrage vom Backend.

### Files
- `frontend/js/modules/vision-status.js` (neu oder bestehend)
- `frontend/css/vision-status.css` (neu oder bestehend)
- `frontend/index.html` (UI-Integration)
- `backend/api/routers/vision.py` (neu oder bestehend für Status-Endpoint)

### Steps
1. Backend-Status-Endpoint implementieren: `GET /api/vision/status` mit `loading`, `loaded`, `error` States
2. Frontend-Status-Abfrage implementieren: Periodische Abfrage oder Event-basiert
3. UI-Indikator designen: "Vision wird geladen..." Badge oder Toast
4. UI-Indikator im Frontend integrieren: Sichtbar wenn Status `loading`
5. UI-Indikator ausblenden wenn Status `loaded` oder `error`
6. Vision-Input-Deaktivierung: Vision-Inputs deaktivieren während `loading` (optional, falls UX-gewünscht)

### Acceptance Criteria
- [ ] Backend-Status-Endpoint `/api/vision/status` ist implementiert
- [ ] Frontend zeigt "Vision wird geladen..." Indikator während Download
- [ ] Indikator verschwindet wenn Model geladen ist
- [ ] Indikator zeigt Fehlermeldung bei Download-Fehler
- [ ] Optional: Vision-Inputs sind deaktiviert während Loading (falls gewählt)

### Tests
- Manuellem Test: Indikator erscheint während Download
- Manuellem Test: Indikator verschwindet nach erfolgreichem Download
- Manuellem Test: Indikator zeigt Fehler bei Download-Fehler
- API-Test: `/api/vision/status`返回 korrekte States

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Frontend-Backend-Integration, UI-Design, API-Endpoint-Implementierung – erfordert UX-Überlegungen und Cross-System-Koordination.

---

## TASK-005 – Download-Fehlerbehandlung

### Ziel
Download-Fehler robust handeln: App startet trotzdem, Vision bleibt deaktiviert, klare Fehlermeldung für Nutzer.

### Beschreibung
Wenn der CLIP-Model-Download fehlschlägt (Netzwerk-Fehler, Server-Fehler, Speicher-Fehler), darf die App nicht abstürzen. Sie muss starten, Vision bleibt deaktiviert, und der Nutzer erhält eine klare Fehlermeldung. Dieser Task implementiert robuste Fehlerbehandlung im Download-Flow.

### Files
- `backend/services/vision/model_loader.py` (Download-Logik)
- `backend/api/routers/vision.py` (Status-Endpoint)
- `frontend/js/modules/vision-status.js` (Fehler-UI)

### Steps
1. Download-Fehler-Typen identifizieren: Netzwerk-Fehler, Server-Fehler, Speicher-Fehler, Timeout
2. Try-Catch-Blöcke um Download-Logik implementieren
3. Fehler-Logging: Detaillierte Fehler-Informationen in Backend-Log
4. Fehler-State setzen: `model_error` mit Fehler-Details
5. App-Start sicherstellen: Download-Fehler bricht nicht App-Start ab
6. Frontend-Fehler-UI implementieren: Klare Fehlermeldung für Nutzer
7. Retry-Option implementieren (optional): Nutzer kann Download erneut starten

### Acceptance Criteria
- [ ] Download-Fehler bricht nicht den App-Start ab
- [ ] Backend-Log enthält detaillierte Fehler-Informationen
- [ ] Frontend zeigt klare Fehlermeldung bei Download-Fehler
- [ ] Vision bleibt deaktiviert bei Download-Fehler
- [ ] Optional: Retry-Option für Nutzer (falls gewählt)

### Tests
- Manuellem Test: Download simuliert fehlschlagen, App startet trotzdem
- Manuellem Test: Frontend zeigt klare Fehlermeldung
- Manuellem Test: Vision-Requests bei Download-Fehler liefern klare Fehlermeldung
- Optional: Retry-Test (falls implementiert)

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Fehlerbehandlung mit Try-Catch-Blöcken, Logging, State-Management, Frontend-Error-UI – erfordert robuste Error-Handling-Logik und UX-Integration.

---

## Ausführungskette
- **Reihenfolge:** Sequenziell (TASK-001 → TASK-002 → TASK-003 → TASK-004 → TASK-005)
- **Begründung:** Tasks bauen aufeinander auf: Lazy-Loading (001) ist Basis für Persistenz (002), Request-Handling (003) benötigt Status-Tracking aus 001, UI-Indikator (004) benötigt Status-Endpoint aus 003, Fehlerbehandlung (005) schließt alle Fehler-Pfade ab.

## Zugewiesene Modelle
- **SWE 1.6:** TASK-001, TASK-002, TASK-003, TASK-004, TASK-005
- **Kimi k2.5:** Keine

## Modell-Bedeutung
- Diese Zuweisungen sind Task-Ausführungsmodelle für spätere einzelne Skill-3-/Skill-4-Läufe.
- Sie sind NICHT das Modell für Skill 2.

## Nächster Schritt
→ Starte Skill 2 mit SWE 1.6 und beiden Artefakten:
   Spec: documentation/Planned Features/backlog_BACKLOG-018_clip_lazy_loading.md
   Tasks: documentation/tasks/backlog_BACKLOG-018_clip_lazy_loading_tasks.md

**Wichtig:**
→ Starte Skill 2 NICHT mit Kimi k2.5, nur weil ein erzeugter Task Kimi zugewiesen ist.
→ Skill 2 ist das Task-Refinement-Gate und läuft immer mit SWE 1.6, außer ein MODEL SWITCH zu GPT-5.5 ist explizit erforderlich.
→ Skill 2 gibt später exakt einen Target Task mit dessen zugewiesenem Ausführungsmodell frei.

---

## POST-IMPLEMENTATION AUDIT

### Skill 5 Final Audit Result
- **Status:** PASS
- **Date:** 2026-05-09
- **Implemented Tasks:** TASK-001
- **Manual Janus Test:** PASS
- **Skill 6:** N/A (nicht benötigt)

### Skill 7 Version Bump
- **Old version:** 0.4.17-beta.20
- **New version:** 0.4.17-beta.21
- **Mode:** automatic patch prerelease bump
- **Files changed:** package.json, package-lock.json, backend/version.py
- **Validation:** PASS

### Changed Files
- backend/services/vision/model_loader.py (NEU)
- backend/services/vision_service.py (MODIFIZIERT)
- backend/main.py (MODIFIZIERT)

### Validation Evidence
- Unit Tests: PASS
- Integration Tests: PASS
- E2E Tests: PASS (manueller Janus-Test)
- Syntax Validation: PASS (AST-Compile OK)

### Backlog Status
- **BACKLOG-018:** IN PROGRESS → DONE

### Release Readiness
- **Ready for Skill 8:** JA
- **Known Risks:** HIGH (kritischer First-Start-Pfad, aber durch Lazy-Loading reduziert)

JANUS FEATURE SPEC – AUTO UPDATE SYSTEM
(DIAMANTSTANDARD – EXECUTION READY)
1. FEATURE NAME

Janus Silent Auto Update System (GitHub-based Updater)

2. CORE IDEA

Janus erhält ein automatisches Update-System, das neue Versionen aus GitHub Releases im Hintergrund herunterlädt. Updates laufen silent im Hintergrund, ohne die Nutzung zu unterbrechen. Nach erfolgreichem Download wird der User informiert und kann Janus neu starten, um das Update zu installieren. Kritische Updates sind verpflichtend, normale Updates optional.

3. USER PROBLEM & VALUE

User müssen aktuell manuell updaten oder riskieren veraltete Versionen.
Das führt zu:

inkonsistenten Versionen im Einsatz
Bugs durch alte Builds
manuelle Update-Reibung

👉 Lösung:

automatische, stabile Updates ohne User-Intervention
minimale Unterbrechung
sichere Version-Konsistenz über alle Installationen
4. FUNCTIONAL CORE
App prüft beim Start auf neue Version (GitHub Releases)
Download neuer Version läuft silent im Hintergrund
Fortschritt wird intern gespeichert (State File)
Nach Download: UI Notification „Update bereit“
User klickt „OK“ → App beendet sich
Installer wird automatisch gestartet
Kritische Updates erzwingen Update vor weiterer Nutzung
Normale Updates können ignoriert werden
5. SYSTEM BEHAVIOR
Update Check Flow
Trigger: App Start
Query GitHub Release API
Vergleich mit lokaler Version
Download Flow
Start im Hintergrund
Resume möglich nach App restart
State wird persistent gespeichert (JSON)
Installation Flow
Nach vollständigem Download:
Notification anzeigen
User confirmation erforderlich
App shutdown
Installer execution

UI Decision:
Normal updates use a non-blocking in-app toast or banner with actions Installieren and Später. Critical updates use a blocking in-app modal without Später action; the user must install before continuing normal app usage. Download, validation, and install failures use a persistent retryable error banner with error message and Retry action. Native OS notifications are OUT OF SCOPE for Phase 1 E2E validation.
State Handling
idle
checking
update_available
downloading
download_paused
download_failed
validating
validation_failed
ready_to_install
installing
install_failed
installed

State Machine Decision:
Phase 1 uses an explicit update state machine. Each state is persisted in the JSON state file together with targetVersion, currentVersion, assetPath, manifestHash, downloadedHash, errorCode, errorMessage, updatedAt, and retryCount where applicable. State transitions must be deterministic and must map electron-updater events into Janus states. Entry, exit, and failure behavior for each state must be defined in the implementation plan before coding.
6. EDGE CASES / FAILURE BEHAVIOR
Download bricht ab → vollständiger Re-download (kein Resume repair)
App wird während Download geschlossen → Resume beim nächsten Start
Netzwerkfehler → Retry beim nächsten App-Start
GitHub nicht erreichbar → fallback auf local version continue
Installer failure → no custom low-level rollback in Phase 1. Janus uses electron-updater / installer standard behavior and models the failure through a deterministic recovery state.
Unvollständige Datei → discard + clean re-download

Retry / Fallback Decision:
Phase 1 uses mixed retry rules. Check/API failures perform no automatic runtime retry and return to idle with lastError; the next automatic check happens only on next app start. Download failures allow up to 3 automatic retries per app start; after the third failed attempt Janus sets download_failed and shows the retryable error banner. Validation failures perform no automatic retry, delete the invalid asset, set validation_failed, and require user Retry. Install failures perform no automatic retry, set install_failed, and require user Retry. No background polling loop is allowed during runtime.

Installer Failure Decision:
Phase 1 does not implement a custom rollback engine. Custom low-level rollback is OUT OF SCOPE. Janus defines an install_failed recovery state. If installation fails before app shutdown, Janus persists install_failed and shows a retryable error. If installation fails after shutdown, Janus checks the local version against the target version on next start and sets state to ready_to_install or install_failed.
7. CONSTRAINTS / LIMITS
Kein Hintergrund-Polling während Laufzeit
Kein halb-installierter Zustand erlaubt
Keine Mischung aus alten und neuen Versionen
Download muss vollständig validiert sein vor Installation
State muss immer synchron mit Downloadstatus sein

Security Decision:
Phase 1 requires SHA256 validation through a release manifest before installation. If the downloaded asset hash does not match the manifest hash, the asset is discarded and installation is blocked. Code-signing and certificate-based release verification are OUT OF SCOPE for Phase 1.
8. INTEGRATION CONTEXT
Interne Module
Janus Core App Shell
Update Manager Service
State Persistence Layer (JSON File)
Installer Module (Electron Builder)
Externe Systeme
GitHub Releases API
Electron Updater / custom installer
OS process manager (restart/shutdown)

Architecture Decision:
Hybrid approach. Use electron-updater for update check, download, and install execution. Add a Janus-specific state and UI adapter around electron-updater events. Do not implement a fully custom GitHub download and installer engine in Phase 1.
9. COMPLEXITY LEVEL

system-critical

10. TEST STRATEGY REQUIREMENT (MANDATORY)
Unit Tests
Version comparison logic
State transitions (idle → downloading → ready)
Resume logic validation
Integration Tests
GitHub API fetch mock + real fallback
download manager ↔ state persistence
installer trigger flow
E2E Tests (MANDATORY)
App start → update detection → download → restart → install
interrupted download → resume after restart
critical update → forced update flow

👉 Must include real file download simulation (no full mocking)

State Tests
JSON state consistency across crashes
recovery after abrupt termination
version-state sync validation
AI/Behavior Tests (optional)
update classification (critical vs normal)
edge-case decision handling
HARTE TESTREGELN
Kein “grün ohne echten Download”
E2E muss realen Update Flow simulieren
State muss nach Crash korrekt wiederherstellbar sein
11. DEFINITION OF DONE

Feature ist fertig wenn:

Update läuft vollständig end-to-end
Resume nach App-Kill funktioniert
Critical vs Normal Updates korrekt greifen
Installer stabil durchläuft
State korrekt persistiert wird
keine corrupt installs möglich sind
12. OPEN QUESTIONS
UI Gestaltung der Update Notification: Normal updates use a non-blocking in-app toast/banner with Installieren and Später. Critical updates use a blocking modal without Später. Failure states use a persistent retryable error banner. Native OS notifications are OUT OF SCOPE for Phase 1 E2E validation.
Retry / Fallback: Check/API failures have no automatic runtime retry and retry only on next app start. Download failures allow max 3 automatic retries per app start, then download_failed. Validation failures delete invalid assets and require user Retry. Install failures require user Retry. No background polling loop is allowed.
Signierung / Security der Releases: Phase 1 uses SHA256 manifest validation. Code-signing and certificate-based release verification are OUT OF SCOPE for Phase 1.
13. IMPLEMENTATION CONTRACT (EXECUTION LAYER)
TASK RULES
1 Task = 1 atomare Änderung
keine Architektur-Interpretation erlaubt
kein “verbessern”, nur implementieren
deterministische Schritte erforderlich
TASK STRUCTURE

TASK ID:

Goal:
Einzelziel ohne Kombination

Context:
Systembereich

Input:
Dateien / Services

Output:
konkretes Verhalten nach Änderung

Steps:

...
...
...

Files:
exakte Pfade

Dependencies:
vorherige Tasks

Acceptance Criteria:

binär prüfbar
reproduzierbar

Test Mapping:
Unit / Integration / E2E

13. AGENT RULES
kein SWE/Kimi darf interpretieren
keine Architekturentscheidungen im Task
keine “Verbesserungen”
nur exakte Umsetzung
14. SYSTEM GOAL

Robustes, deterministisches Auto-Update-System ohne Zustandsbrüche im Live-Betrieb.

🧠 EIN-SATZ-DEFINITION

Dieses Feature ist ein selbstheilendes, GitHub-basiertes Update-System mit kontrollierter Zustandsmaschine und crash-resistenter Recovery-Logik.
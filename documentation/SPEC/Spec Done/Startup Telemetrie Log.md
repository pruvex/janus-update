# JANUS FEATURE SPEC – DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: SPEC_REVIEW
execution_mode: SWE_1_6
complexity_score: 38
confidence: HIGH
dashboard_hint: SAFE
reason: Einfaches Dev-Logging Feature mit lokaler Persistenz ohne UX- oder Architekturänderung

## FEATURE IDENTITY

- Feature Name: Startup Telemetrie Log (Dev-Kontext)
- Source Input: Janus Startup Performance Analyse Anforderungen aus Dev-Debugging Kontext
- Primary Goal: Systematische Erfassung von Startup-Zeiten und Phasen zur späteren Analyse von Performance-Bottlenecks
- User Problem: Unklarheit darüber, warum Janus Startup 30+ Sekunden dauert
- User Value: Ermöglicht datenbasierte Identifikation von Startup-Engpässen über mehrere Runs hinweg

## USER VALUE

Der Nutzer erhält eine wiederholbare, vergleichbare Datengrundlage über mehrere App-Starts hinweg, um Performance-Probleme im Startup gezielt zu erkennen. Dadurch werden subjektive Einschätzungen durch objektive Zeit- und Phasenmessungen ersetzt.

Das Produktverhalten für Endnutzer bleibt unverändert, nur im Dev-Kontext entstehen zusätzliche Diagnoseinformationen.

## TARGET SURFACE

- Primary Target Surface: Zentrale Startup-Logdatei (umgebungsspezifisch)
  - Dev-Kontext: `C:\KI\Janus-Projekt\documentation\Startup log\janus_startup_telemetry.log`
  - Produktion: `AppData\Roaming\Janus Projekt\logs\janus_startup_telemetry.log`
- Existing or New Surface: New Surface
- User Trigger: Start der Janus Anwendung (Dev-Modus oder Produktion)
- Success Behavior: Pro Startup wird ein strukturierter Logblock in die zentrale Logdatei geschrieben
- Failure Behavior: Logging wird ohne Einfluss auf den App-Start übersprungen
- Explicit Non-Surfaces: Janus Benutzeroberfläche, Endnutzer-Sichtbarkeit

## USER ACTION SURFACE

- Action Type: Nicht zutreffend
- Trigger: Nicht zutreffend
- User Input: Nicht zutreffend
- Immediate Feedback: Nicht zutreffend
- Result: Nicht zutreffend
- Cancel / Undo Behavior: Nicht zutreffend
- Non-Effects: Keine Nutzerinteraktion vorhanden

## SYSTEM BEHAVIOR

Beim Start der Anwendung im Dev-Kontext wird ein Startup-Prozess-Log erzeugt. Dieser enthält strukturierte Informationen über Gesamtzeit, Phasen und IO-bezogene Aktivitäten.

Jeder Startup erzeugt einen neuen Block in einer zentralen Datei. Jeder Block ist einem Run eindeutig zugeordnet.

Fehler im Logging beeinflussen den Startup-Prozess nicht. In diesem Fall wird Logging deaktiviert und der Startup normal fortgesetzt.

## DATA / PERSISTENCE

- Persistence Required: YES
- Data Created: Startup Log Einträge pro Run (Zeit, Phasen, IO-Markierungen)
- Data Updated: Zentrale Logdatei wird fortlaufend erweitert
- Data Deleted: Keine Löschung vorgesehen
- Source of Truth: Zentrale Startup Logdatei im Dokumente-Ordner
- Recovery Behavior: Falls Datei fehlt, wird sie neu erstellt; bei Fehlern wird Logging übersprungen oder neu initialisiert

## CONSTRAINTS

- Logging nur im Dev-Kontext aktiv
- Keine Auswirkungen auf Startup-Performance
- Keine Änderungen an Endnutzer-UI
- Keine Aktivierung in Produktion
- Konsistente Logstruktur über alle Runs hinweg erforderlich

## SECURITY / PRIVACY

- Sensitive Data Involved: NO
- External Services Involved: NO
- Secrets Required: NO
- Privacy Impact: Nur lokale Entwicklungsdaten, keine externe Übertragung
- Security Constraints: Lokaler Dateizugriff nur, keine Netzwerkkommunikation

## EDGE CASES

- Dokumente-Ordner existiert nicht → wird erstellt oder Logging wird übersprungen
- Schreibfehler → Logging wird deaktiviert, App läuft weiter
- Parallele Starts → eindeutige Run-Markierung erforderlich
- Unvollständiger Startup (Crash) → Log kann als unvollständig markiert werden
- Speicher voll → Logging wird deaktiviert
- Keine Schreibrechte → Logging wird übersprungen

## DEFINITION OF DONE

- [ ] Jeder Startup erzeugt genau einen Logblock in der zentralen Datei
- [ ] Log enthält Gesamtzeit, Phasen und IO-Markierungen
- [ ] Logdatei wird persistent im Dokumente-Ordner geführt
- [ ] Logging beeinflusst Startup nicht messbar
- [ ] Fehler im Logging brechen den Startup nicht

## TEST STRATEGY

- Manual Validation: Mehrere Startup-Runs und Prüfung der Logkonsistenz
- Automated Validation Candidates: Existenz der Logdatei und Eintrag pro Run
- Regression Areas: Startup Performance und Dev-Modus Verhalten
- Failure Case Validation: Datei fehlt, keine Schreibrechte, Crash während Startup

## OUT OF SCOPE

- UI-Darstellung innerhalb von Janus
- Automatische Performance-Optimierung
- Cloud-Logging oder externe Telemetrie
- Echtzeit-Analyse im Produktivbetrieb
- Endnutzer-Funktionen

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 10 – klar abgegrenztes Logging Feature ohne UI
Architectural Risk: 8 – Startup Hook + Dateisystemzugriff
State / Persistence Complexity: 12 – kontinuierliches Append-Logging erforderlich
Cross-System Dependencies: 5 – nur lokales Dateisystem
Ambiguity Level: 3 – klar definierter Scope ohne Mehrdeutigkeit
Total Complexity Score: 38
Routing Decision: SWE_1_6
Routing Confidence: HIGH
Dashboard Hint: SAFE

## SPEC REVIEW METADATA

Review Date: 2026-05-10
Review Model: SWE 1.6
Review Status: APPROVED_WITH_NOTES
Skill-1 Ready: YES
Review Complexity Score: 38
Review Confidence: HIGH
Review Dashboard Hint: SAFE
Review Reason: Einfaches Dev-Logging Feature mit lokaler Persistenz ohne UX- oder Architekturänderung

### Review Findings

**Approved with Minor Refinements Required:**

1. **Typo Correction**: Line 76 contains Hebrew character "בלבד" → change to "nur"
2. **Log Rotation**: Add size limit or rotation strategy to prevent unbounded growth
3. **Implementation Target**: Specify files/modules (e.g., main.electron.cjs, backend startup hooks)
4. **Acceptance Criteria**: Map Definition of Done checkboxes to testable conditions
5. **Dev-Context Detection**: Specify activation mechanism (env var, config flag, etc.)

### Blocking Issues
None

### Non-Blocking Notes
- Spec is well-scoped and appropriate for SWE 1.6 execution
- Edge case coverage is comprehensive
- OUT OF SCOPE properly defined
- Ready for SKILL 1 – SPEC TO TASK COMPILER

## SPEC IMPLEMENTATION METADATA

Implementation Date: 2026-05-10
Implementation Status: COMPLETE
Audit Model: SWE 1.6
Audit Result: PASS
Audit Date: 2026-05-10

### Implementation Summary

All Definition of Done criteria fulfilled:
- [x] Jeder Startup erzeugt genau einen Logblock in der zentralen Datei
- [x] Log enthält Gesamtzeit, Phasen und IO-Markierungen
- [x] Logdatei wird persistent im Dokumente-Ordner geführt
- [x] Logging beeinflusst Startup nicht messbar
- [x] Fehler im Logging brechen den Startup nicht

### Changed Files

- backend/main.py - Backend-Startup-Marker (backend_startup_start, backend_ready) mit Dev-Kontext-Check
- backend/services/telemetry/startup_config.py - Telemetrie-Konfiguration, fehlende Imports ergänzt (json, datetime)
- backend/services/telemetry/startup_logger.py - Telemetrie-Logger für Python
- backend/services/telemetry/__init__.py - Telemetrie-Package-Initialisierung
- electron/startup-telemetry.cjs - Telemetrie-Logger für Electron, aktiv nur im Dev-Kontext
- scripts/write-startup-marker.cjs - npm_start Marker für Dev-Modus (neu erstellt)
- package.json - npm_start Marker-Skript in start-dev integriert, NODE_ENV=development zu start-backend-only hinzugefügt
- main.electron.cjs - Backend-Start-Phase wird nach startRun() geloggt
- tests/test_startup_config.py - Test angepasst, um "documentation" Pfad zu akzeptieren
- tests/test_startup_logger.py - Unit-Tests für Startup Logger

### Test Results

- Python-Syntax-Check: PASS
- JavaScript-Syntax-Check: PASS
- Pytest: 26 passed, 1 skipped
- Manual Retest: PASS

### Known Risks

None - Telemetrie ist strikt Dev-only gemäß Spec/Task
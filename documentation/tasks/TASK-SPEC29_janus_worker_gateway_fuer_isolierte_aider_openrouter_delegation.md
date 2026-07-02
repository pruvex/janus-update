TASK-SPEC29
- Source Spec: `documentation/SPEC/Spec Done/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md`
- Backlog Item: `N/A`
- Feature: Janus Worker Gateway fuer isolierte Aider/OpenRouter Delegation
- Generated At: 2026-07-02

## Generated Tasks

### TASK-SPEC29.1 Define the normalized worker task and result contract
- Ziel:
  - Definiere den verbindlichen lokalen Vertrag fuer `janus-worker` Aufgabenpakete, Profile, erlaubte Dateigrenzen, verbotene Aktionen und normierte Ergebnisartefakte.
- Scope:
  - Nur Schema, Validierung, Fixture-Vertrag und fail-closed Klassifikation. Keine echte Aider/OpenRouter-Ausfuehrung und kein Copy-back von Worker-Aenderungen.
- Files:
  - `documentation/codex/model-routing/scripts/janus_worker_contract.py`
  - `documentation/codex/model-routing/scripts/janus_worker_gateway.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_contract.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_gateway.py`
  - `documentation/codex/model-routing/strong-or-fixtures/`
- Steps:
  1. Definiere ein maschinenlesbares Task-Paket mit Task-Ziel, Profil, erlaubten Dateien, verbotenen Aktionen, Akzeptanzkriterien und Check-Kommandos.
  2. Definiere das normierte Ergebnisverzeichnis mit mindestens `RESULT.json`, `RESULT.md`, `DIFF.patch`, `FILES_CHANGED.txt`, `CHECKS.log` und `COST.json`.
  3. Implementiere Validierung fuer vollstaendige, unvollstaendige, scope-verletzende und blocked Ergebnisbloecke.
  4. Stelle sicher, dass der Contract ohne Roh-Agentenchat auswertbar ist und fehlende Artefakte fail-closed klassifiziert.
- Acceptance Criteria:
  - Gueltige Task-Pakete und Ergebnisverzeichnisse werden deterministisch akzeptiert.
  - Fehlende Pflichtfelder, verbotene Aktionen, leere Allowlists oder fehlende Ergebnisartefakte werden deterministisch abgelehnt.
  - `success` ist nur moeglich, wenn Ergebnisstatus, Diff, geaenderte Dateien, Checks und Kosten-/Usage-Metadaten im Contract konsistent sind.
  - Der Contract behauptet keine Git-, Release-, Publish-, Dependency-, Security-, Privacy- oder Architekturautoritaet fuer den Worker.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q`
  - `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "contract or result or fail_closed"`
  - `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py`
- Model: 5.4
- Reason:
  - Der MVP steht oder faellt mit dem Ergebnisvertrag; diese Slice macht Codex-Review ohne Rohchat-Abhaengigkeit erst pruefbar.

### TASK-SPEC29.2 Wire the isolated Aider/OpenRouter backend into the worker gateway
- Ziel:
  - Binde den bestehenden isolierten Aider/OpenRouter Runner an den neuen `janus-worker` Gateway-Vertrag und lasse jeden Lauf ein normiertes Ergebnispaket schreiben.
- Scope:
  - Nur Aider/OpenRouter als erstes Backend. Keine OpenCode-/OpenHands-Unterstuetzung, keine globale Skill-Aktivierung und keine produktive Abschlussautoritaet.
- Files:
  - `documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py`
  - `documentation/codex/model-routing/scripts/janus_worker_contract.py`
  - `documentation/codex/model-routing/scripts/janus_worker_gateway.py`
  - `documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_gateway.py`
- Steps:
  1. Erweitere den Gateway-Einstieg so, dass Codex ein validiertes Task-Paket mit einem Aider/OpenRouter-Profil ausfuehren oder lokal ablehnen kann.
  2. Fuehre die Worker-Ausfuehrung weiterhin nur in einem isolierten Temp-Workspace mit expliziter Allowlist aus.
  3. Erzeuge nach jedem Lauf das normierte Ergebnispaket, auch bei `blocked`, `failed` oder Operator-Local-Auswahl.
  4. Kopiere Worker-Aenderungen nur bei sauberer Scope-, Check- und Artefaktvalidierung zurueck und markiere alles andere als Codex-Fallback.
- Acceptance Criteria:
  - Ein erfolgreicher isolierter Aider/OpenRouter-Lauf erzeugt alle normierten Ergebnisartefakte und ist fuer Codex reviewbar.
  - Fehlender `OPENROUTER_API_KEY`, ungueltiges Profil, rote Checks, Scope-Drift oder fehlende Artefakte fuehren nicht zu `success`.
  - Der Runner erzeugt keine akzeptierten Repo-Root-Seiteneffekte wie `.aider*` oder `.gitignore`-Aenderungen.
  - Der Worker darf keine Commit-, Push-, Release-, Publish- oder Dependency-Aktionen ausfuehren.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py -q`
  - `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q`
  - `python -m py_compile documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py`
- Model: 5.4
- Reason:
  - Diese Slice macht aus dem vorhandenen Aider-Pfad einen wiederholbaren Gateway statt eines einmaligen POC-Skripts.

### TASK-SPEC29.3 Add regression coverage, operator guidance, and the first bounded live-dev pilot
- Ziel:
  - Sichere den Worker Gateway mit Regressionen, knapper Operator-Dokumentation und einem ersten kleinen Live-Dev-Pilot gegen eine harmlose Dev-/Doku-/Testaufgabe ab.
- Scope:
  - Nur Nachweis, Regressionen, Profil-/Operator-Hinweise und ein kleiner Live-Dev-Pilot. Keine neue Backend-Auswahl, kein Release, keine Security-/Privacy-Arbeit und keine Produktlogik-Aenderung durch den Worker.
- Files:
  - `documentation/codex/model-routing/scripts/janus_worker_gateway.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_contract.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_gateway.py`
  - `documentation/codex/model-routing/janus_worker_gateway_profiles.md`
  - `development/openrouter-skill-tests/janus-worker-gateway-live/`
  - `documentation/tasks/TASK-SPEC29.3_execution_result.md`
- Steps:
  1. Ergaenze Regressionen fuer Erfolg, fehlenden Key, ungueltiges Profil, verbotene Datei, rote Checks, fehlende Artefakte und Operator-Local-Fallback.
  2. Dokumentiere die ersten Aider/OpenRouter-Profile, Kosten-/Usage-Hinweise und die Grenzen fuer geeignete Fleissarbeit.
  3. Fuehre genau einen kleinen bounded Live-Dev-Pilot aus, wenn die lokalen Voraussetzungen vorhanden sind und der Scope nicht produkt- oder sicherheitskritisch ist.
  4. Schreibe den Ausfuehrungsnachweis so, dass Codex den Pilot als Accept, Reject, Retry oder Fallback bewerten kann.
- Acceptance Criteria:
  - Die Regressionen decken erfolgreiche und fail-closed Worker-Ergebnisse ab.
  - Die Operator-Hinweise beschreiben Aider/OpenRouter als MVP-Backend und klaeren OpenCode/OpenHands explizit als spaeteren Nicht-MVP-Pfad.
  - Der Live-Dev-Pilot erzeugt ein normiertes Ergebnispaket oder einen dokumentierten Blocker.
  - Codex akzeptiert kein Worker-Ergebnis ohne Diff-, Check- und Artefaktpruefung.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests -q -k "janus_worker or isolated_aider"`
  - `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py`
  - bounded live-dev pilot result or documented blocker under `development/openrouter-skill-tests/janus-worker-gateway-live/`
- Model: 5.4
- Reason:
  - Der Nutzerwert ist erst erreicht, wenn der Gateway nicht nur theoretisch validiert, sondern in einem kleinen Live-Dev-Betrieb beobachtbar nutzbar ist.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC29.3_final_audit.md` dokumentiert. Der Worker-Gateway-MVP ist damit task-scharf abgeschlossen: der lokale Contract bleibt fail-closed, der isolierte Aider/OpenRouter-Runner liefert normierte reviewbare Ergebnisartefakte, die Operator-Guidance dokumentiert die ersten MVP-Profile, und der bounded docs-only Pilot `WF-JANUS-WORKER-GATEWAY-LIVE-001` bestaetigt den End-to-End-Pfad ohne Scope-Drift oder Repo-Root-Seiteneffekte. Spec 29 ist damit insgesamt abgeschlossen und nach `documentation/SPEC/Spec Done/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md` ueberfuehrt, ohne globale OR-Freigabe, Git-/Release-Autoritaet oder weitere Backend-Familien freizuschalten.

## Spec 29 Closeout

- Overall Status: DONE
- Final Audit Chain:
  - `documentation/tasks/TASK-SPEC29.1_final_audit.md` - PASS
  - `documentation/tasks/TASK-SPEC29.2_final_audit.md` - PASS
  - `documentation/tasks/TASK-SPEC29.3_final_audit.md` - PASS
- Spec Location: `documentation/SPEC/Spec Done/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md`
- Completion Summary: Der Janus Worker Gateway MVP ist jetzt vollstaendig als eng gebundener Drei-Slice-Block abgeschlossen. Er kombiniert den versiegelten lokalen Contract, die isolierte Aider/OpenRouter-Backend-Anbindung, erweiterte Regressionen, dokumentierte Operator-Profile und einen ersten bounded docs-only Live-Dev-Pilot mit explizit Codex-owned Review und Accept-/Reject-Autoritaet. Es wurde keine globale OR-Freigabe, kein Produktionsrouting, keine Git-/Release-Autoritaet und keine Freigabe weiterer Backend-Familien aktiviert.

@janus-task-breakdown
Spec: documentation/SPEC/Spec Done/29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Task: documentation/tasks/TASK-SPEC29_janus_worker_gateway_fuer_isolierte_aider_openrouter_delegation.md
Backlog Item: N/A
Target Task: TASK-SPEC29.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF

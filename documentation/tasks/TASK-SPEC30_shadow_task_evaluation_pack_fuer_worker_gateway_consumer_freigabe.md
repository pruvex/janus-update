TASK-SPEC30
- Source Spec: `documentation/SPEC/30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md`
- Backlog Item: `N/A`
- Feature: Shadow-Task Evaluation Pack fuer Worker-Gateway Consumer-Freigabe
- Generated At: 2026-07-02

## Generated Tasks

### TASK-SPEC30.1 Build the bounded shadow task packages and fixed comparison config
- Ziel:
  - Lege den verbindlichen lokalen Evaluationsrahmen fuer genau zwei Shadow-Arbeitsklassen an, einschliesslich Sandbox-Grenzen, normierter Eingabepakete, Akzeptanzkriterien und einer festen Zwei-Modell-Vergleichsstruktur je Klasse.
- Scope:
  - Nur die gebundenen Shadow-Aufgaben, ihre Vergleichskonfiguration und ihre lokale Evidenzoberflaeche. Kein echter Produktcode-Writeback, keine globale Worker-Freigabe und keine Ausweitung auf weitere Arbeitsklassen.
- Files:
  - `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/`
  - `documentation/codex/model-routing/scripts/janus_worker_gateway.py`
  - `documentation/codex/model-routing/scripts/janus_worker_contract.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_gateway.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_contract.py`
- Steps:
  1. Definiere genau zwei isolierte Shadow-Arbeitsklassen: Doku-/Fleissarbeit und Test-/Fixture-Arbeit.
  2. Erzeuge fuer jede Klasse ein normiertes Aufgabenpaket mit klarer Allowlist, verbotenen Aktionen, Akzeptanzkriterien und Check-Kommandos.
  3. Lege fuer jede Klasse genau eine feste Zwei-Modell-Vergleichsstruktur an, sodass beide Worker-Laeufe denselben gebundenen Task und dieselben Bewertungsmarker nutzen.
  4. Stelle sicher, dass die Shadow-Pakete ausserhalb der gebundenen Sandbox keine Repo-Writebacks oder Skill-/Git-/Release-Autoritaet erhalten.
- Acceptance Criteria:
  - Es existieren genau zwei Shadow-Arbeitsklassen und keine dritte implizite Arbeitsklasse.
  - Jede Klasse besitzt ein normiertes Aufgabenpaket mit isolierter Allowlist und klaren Fail-closed Grenzen.
  - Jede Klasse bindet genau zwei feste Worker-Modelle fuer denselben Vergleichspfad.
  - Die Konfiguration behauptet keine produktive Consumer-Freigabe, keinen echten Repo-Writeback und keine globale Worker-Autoritaet.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_contract.py -q -k "shadow or evaluation or allowlist"`
  - `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "shadow or evaluation or sandbox"`
  - `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_contract.py documentation/codex/model-routing/scripts/janus_worker_gateway.py`
- Model: 5.4
- Reason:
  - Ohne einen sauberen, eng gebundenen Shadow-Rahmen waere jeder spaetere Modellvergleich verrauscht oder wuerde still in echte Produktpfade ausfransen.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC30.1_final_audit.md` dokumentiert. Der erste Spec-30-Slice ist damit task-scharf abgeschlossen: genau zwei Shadow-Arbeitsklassen sind lokal versiegelt, beide tragen feste Zwei-Modell-Vergleichspaare, die Sandbox-Pakete verbieten Repo-Writeback und Consumer-Aktivierung fail-closed, und Contract plus Gateway validieren den Bundle-Rahmen jetzt reviewbar. Spec 30 insgesamt bleibt bewusst offen, weil `TASK-SPEC30.2` erst noch die vergleichbaren Shadow-Laeufe mit Ergebnisartefakten beweisen und `TASK-SPEC30.3` daraus die erste Consumer-Empfehlung oder ein klares No-Go/Nachtest-Signal ableiten muss.

### TASK-SPEC30.2 Implement the comparable shadow run and result pipeline
- Ziel:
  - Erweitere den Worker-Gateway-Evaluationspfad so, dass fuer beide Shadow-Arbeitsklassen je zwei gebundene Modelllaeufe mit normierten Ergebnisartefakten, Kostenhinweisen und vergleichbaren Scope-Signalen ausgefuehrt werden koennen.
- Scope:
  - Nur die lokale Ausfuehrungs- und Ergebnisstrecke fuer Shadow-Laeufe. Keine Freischaltung echter Skill-Schreibpfade, keine Commits, keine Pushes und keine Consumer-Aktivierung.
- Files:
  - `documentation/codex/model-routing/scripts/janus_worker_gateway.py`
  - `documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py`
  - `documentation/codex/model-routing/tests/test_janus_worker_gateway.py`
  - `documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py`
  - `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/`
- Steps:
  1. Fuehre fuer jede Shadow-Arbeitsklasse genau zwei feste Worker-Laeufe ueber denselben gebundenen Task-Pfad aus oder dokumentiere fail-closed, warum ein Lauf blockiert wurde.
  2. Schreibe pro Lauf normierte Ergebnisartefakte fuer Inhalt, geaenderte Dateien, Checks, Kosten-/Usage-Hinweise und Scope-Disziplin.
  3. Erzeuge eine lokale Klassen-Zusammenfassung, die die zwei Modelllaeufe innerhalb derselben Klasse direkt vergleichbar macht.
  4. Stelle sicher, dass fehlende Artefakte, Scope-Drift, rote Checks oder unvollstaendige Kosten-/Usage-Daten nicht als freigabefaehige Laeufe gelten.
- Acceptance Criteria:
  - Fuer jede der zwei Shadow-Arbeitsklassen existieren genau zwei vergleichbare Modelllaeufe oder ein sauber dokumentierter fail-closed Blocker.
  - Jeder Lauf liefert normierte Ergebnisartefakte fuer Qualitaet, Scope und Kostenlage.
  - Die Auswertung einer Klasse bleibt auf denselben gebundenen Task und dieselben Bewertungsmarker beschraenkt.
  - Kein Shadow-Lauf erzeugt akzeptierte Repo-Writebacks ausserhalb der gebundenen Sandbox.
- Tests:
  - `python -m pytest documentation/codex/model-routing/tests/test_isolated_aider_workspace_runner.py -q -k "shadow or evaluation"`
  - `python -m pytest documentation/codex/model-routing/tests/test_janus_worker_gateway.py -q -k "comparison or result or fail_closed"`
  - `python -m py_compile documentation/codex/model-routing/scripts/janus_worker_gateway.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py`
- Model: 5.4
- Reason:
  - Der Nutzerwert entsteht erst, wenn die Shadow-Laeufe nicht nur starten, sondern in einer gleichfoermigen, reviewbaren Form nebeneinanderliegen.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC30.2_final_audit.md` dokumentiert. Der zweite Spec-30-Slice ist damit task-scharf abgeschlossen: beide gebundenen Shadow-Arbeitsklassen liefern jetzt genau zwei vergleichbare feste Modelllaeufe, normierte Ergebnisartefakte, Kostenhinweise, Klassen-Zusammenfassungen und ein validator-sauberes Top-Level-Bundle `SHADOW_EVALUATION_RUNS_READY`. Spec 30 bleibt dennoch bewusst offen, weil erst `TASK-SPEC30.3` aus diesen Vergleichsartefakten die erste Consumer-Empfehlung, ein engeres Nachtest-Signal oder ein klares No-Go ableiten darf.

### TASK-SPEC30.3 Produce the first-consumer recommendation package from the shadow evaluation
- Ziel:
  - Verdichte die Klassenvergleiche in ein Abschlussartefakt, das klar zwischen erster Consumer-Freigabe, engerem Nachtest oder No-Go unterscheidet.
- Scope:
  - Nur das lokale Abschluss- und Empfehlungspaket fuer diesen bounded Evaluationsblock. Keine automatische Produktaktivierung, keine globale Modellfreigabe und keine Ausweitung auf weitere Worker-Familien.
- Files:
  - `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/`
  - `documentation/tasks/TASK-SPEC30.3_execution_result.md`
  - `documentation/ai/CURRENT_STATE.md`
- Steps:
  1. Fasse pro Shadow-Arbeitsklasse die zwei Modelllaeufe in einem einheitlichen Vergleich zusammen.
  2. Bewerte fuer beide Klassen gemeinsam Qualitaet, Scope-Disziplin, Reviewbarkeit und Kostenlage gegen die Spec-30-Freigaberegeln.
  3. Erstelle ein klares Abschlussartefakt mit genau einer Empfehlung: erster echter Consumer, engerer Nachtest oder No-Go.
  4. Dokumentiere offen, welche Klasse als erster echter Consumer infrage kommt oder warum noch keine Freigabe verantwortbar ist.
- Acceptance Criteria:
  - Es gibt genau ein lokales Abschlussartefakt fuer den gesamten Evaluation-Pack.
  - Das Abschlussartefakt enthaelt eine klare Consumer-Empfehlung oder ein klares No-Go/Nachtest-Signal.
  - Die Empfehlung stuetzt sich sichtbar auf die beiden Klassenvergleiche statt auf Einzelbeobachtungen.
  - Keine Formulierung behauptet eine bereits vollzogene produktive Aktivierung.
- Tests:
  - `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation\tasks\TASK-SPEC30.3_execution_result.md`
  - bounded shadow-evaluation artifact completeness check under `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/`
  - `git diff --check documentation/tasks/TASK-SPEC30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md documentation/tasks/TASK-SPEC30.3_execution_result.md documentation/ai/CURRENT_STATE.md`
- Model: 5.4
- Reason:
  - Die ganze Evaluation lohnt sich nur, wenn daraus eine ruhige, belastbare naechste Entscheidung fuer den ersten echten Worker-Consumer entsteht.

@janus-task-breakdown
Spec: documentation/SPEC/30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
Task: documentation/tasks/TASK-SPEC30_shadow_task_evaluation_pack_fuer_worker_gateway_consumer_freigabe.md
Backlog Item: N/A
Target Task: TASK-SPEC30.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF

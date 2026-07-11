TASK-SPEC21
- Source Spec: documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md
- Backlog Item: N/A
- Feature: Assistierter OR-Arbeitspferd-Modus fuer Janus-Skills
- Generated At: 2026-06-26T00:00:00Z

## Generated Tasks

### TASK-SPEC21.1 Implement eligibility redaction gate for bounded OR-worker selection
- Ziel: Stellen Sie sicher, dass nur berechtigte bounded Arbeitsschritte den OR-Arbeitspferd-Modus aktivieren können, ohne lokale Validierungsgrenzen zu umgehen.
- Scope: Begrenzt auf die Prüfung der Eignung von Arbeitsschritten für den OR-Modus basierend auf vordefinierten Codex-Regeln.
- Files:
  - documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- Steps:
  - Lese die aktuelle Arbeitsschritt-Konfiguration aus dem Codex-Dispatcher.
  - Prüfe, ob der Arbeitsschritt in der Liste der erlaubten Skills (janus-debug, janus-test-pipeline) enthalten ist.
  - Reduziere sensible Metadaten vor der Weitergabe an den OR-Selektor.
  - Generiere eine Eligibility-Entscheidung mit Timestamp und Ursprungs-Context.
- Acceptance Criteria:
  - Eligibility-Entscheidung ist sichtbar in der Log-Ausgabe vor OR-Aufruf.
  - Kein OR-Aufruf erfolgt, wenn der Arbeitsschritt nicht in allowed_initial_skills steht.
  - Redaktierte Metadaten enthalten keine PII oder Systemgeheimnisse.
  - Die Entscheidung wird von codex_bounded_delegation_dispatcher genutzt.
- Tests:
  - test_eligibility_gate_allowed_skill.py
  - test_eligibility_gate_blocked_skill.py
  - test_redaction_of_sensitive_fields.py
  - test_eligibility_output_format.py
- Model: 5.4
- Reason: Die Eligibility-Redaktion ist die erste Kontrollschleife, die sicherstellt, dass nur autorisierte Skills den OR-Modus nutzen – ohne neue Fähigkeiten einzuführen.

### TASK-SPEC21.2 Normalize operator gate prompts to align with bounded worker context
- Ziel: Stellen Sie eine einheitliche, kontextbezogene Prompt-Struktur für die OR-Übergabe sicher, die auf den lokalen Codex-Kontext zurückgreift.
- Scope: Anpassung der Prompt-Generierung in der OR-Gate-Schicht, um konsistente Eingaben für den OpenRouter zu erzeugen.
- Files:
  - documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/skills/janus-debug/SKILL.md
- Steps:
  - Extrahiere den aktuellen Arbeitsschritt-Context aus dem Dispatcher.
  - Verwende den SKILL.md-Template aus janus-debug oder janus-test-pipeline als Referenz für Prompt-Struktur.
  - Füge explizite Hinweise zur Kosten- und Vertrauensanzeige hinzu.
  - Vermeide jegliche Erweiterung des Prompt-Scopes außerhalb der definierten Skills.
- Acceptance Criteria:
  - Der Prompt enthält nur Daten aus dem lokalen Codex-Context.
  - Die Prompt-Struktur entspricht exakt einem der erlaubten SKILL.md-Template.
  - Kosten- und Vertrauensanzeige ist immer sichtbar und nicht optional.
  - Keine externen Referenzen oder dynamischen Variablen im Prompt.
- Tests:
  - test_gate_prompt_structure_compliance.py
  - test_gate_prompt_no_scope_widening.py
  - test_gate_prompt_cost_display.py
  - test_gate_prompt_template_match.py
- Model: 5.4
- Reason: Die Normalisierung des Gate-Prompts verhindert, dass der OR-Modus über die definierten Skills hinaus verwendet wird – ein zentraler DOD-Punkt.

### TASK-SPEC21.3 Capture telemetry and healthcheck data during bounded OR execution
- Ziel: Sammle Metriken über OR-Ausführungskosten und Systemzustand, ohne die lokale Überwachung zu unterbrechen.
- Scope: Erfassung von Healthcheck- und Telemetriedaten während und nach dem OR-Aufruf, inklusive Fallback-Logik.
- Files:
  - documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1
  - documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py
  - documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
- Steps:
  - Starte health_snapshot.py vor OR-Aufruf zur Aufnahme des Systemzustands.
  - Wrapper skript or_file_first_capture_wrapper.ps1 fängt die tatsächlichen OR-Kosten ab.
  - bouned_or_worker_outcome.py protokolliert den Ergebnisstatus und die Dauer.
  - Falls der OR-Aufruf fehlschlägt, wird ein manueller Review-Trigger ausgelöst.
- Acceptance Criteria:
  - Alle OR-Aufrufe erzeugen ein Healthcheck-Snapshot.
  - Die tatsächlichen Kosten sind im Log nachvollziehbar.
  - Fehlgeschlagene OR-Aufrufe führen zu einem klaren Fallback-Trigger.
  - Keine Telemetrie wird außerhalb der definierten Skripte generiert.
- Tests:
  - test_telemetry_capture_before_or.py
  - test_cost_capture_post_or.py
  - test_healthcheck_fallback_trigger.py
  - test_no_extra_telemetry_generated.py
- Model: 5.4
- Reason: Telemetrie- und Healthcheck-Capture ist notwendig, um die transparenz und Fallback-Fähigkeit des OR-Modus zu gewährleisten – ein zentrales DOD-Kriterium.

### TASK-SPEC21.4 Integrate consumer workflows without scope widening beyond janus-debug and janus-test-pipeline
- Ziel: Stellen Sie sicher, dass alle Consumer-Integrationen nur auf die erlaubten Skills beschränkt bleiben und keine neuen Funktionalitäten einführen.
- Scope: Verknüpfung von Debug- und Test-Pipeline-Skills mit dem OR-Modus, ohne Erweiterung des erlaubten Skill-Spektrums.
- Files:
  - documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
  - documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
  - documentation/codex/skills/janus-test-pipeline/SKILL.md
- Steps:
  - Verwende codex_debug_hypothesis_review_runner als einzigen Consumer für OR-Resultate aus janus-debug.
  - Verwende codex_test_result_triage_review_runner als einzigen Consumer für OR-Resultate aus janus-test-pipeline.
  - Stelle sicher, dass keine neuen Trigger- oder Input-Wege hinzugefügt werden.
  - Validiere, dass alle OR-Resultate innerhalb der definierten Skills verbleiben.
- Acceptance Criteria:
  - Kein Consumer außer den beiden erlaubten Skills nutzt den OR-Modus.
  - Alle OR-Resultate werden nur in den definierten SKILL.md-Workflows verarbeitet.
  - Keine neuen Eingabeparameter oder Routing-Logik eingeführt.
  - Alle Integrationen sind dokumentiert in den existierenden SKILL.md-Dateien.
- Tests:
  - test_consumer_only_allowed_skills.py
  - test_no_or_scope_widening.py
  - test_result_routing_within_defined_workflows.py
  - test_no_new_consumer_added.py
- Model: 5.4
- Reason: Die Integration ohne Scope-Widening ist zentral für die Definition von Done – nur die zwei erlaubten Skills dürfen den OR-Modus nutzen, keine weiteren.

@janus-task-breakdown
Spec: documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md
Task: documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md
Backlog Item: N/A
Target Task: TASK-SPEC21.1
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF

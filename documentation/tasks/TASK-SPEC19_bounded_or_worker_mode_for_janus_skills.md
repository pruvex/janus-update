TASK-SPEC19
- Source Spec: documentation/SPEC/19_bounded_or_worker_mode_for_janus_skills.md
- Backlog Item: N/A
- Feature: Bounded OR Worker Mode fuer Janus Skills
- Generated At: 2026-06-17

## Generated Tasks

### TASK-SPEC19.1 Shared OR eligibility contract for bounded Janus skills
- Ziel: Eine gemeinsame Eligibility- und Policy-Grundlage schaffen, damit das OR-Gate nur fuer explizit freigegebene bounded Skill-Klassen mit evidenzgestuetzter OR-Option erscheinen kann.
- Scope: Shared Eligibility-Contract, skill-spezifische Allow/Block-Entscheidung, evidenzgestuetzte OR-Freigabe-Felder und reject-faehige No-Gate-Entscheidung vor jeder spaeteren OR-Auswahl.
- Files:
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
  - documentation/codex/model-routing/config/
  - documentation/codex/model-routing/tests/
- Steps:
  - Einen gemeinsamen Eligibility-Contract fuer bounded Janus-Skills definieren, der nur explizit freigegebene Skill-Klassen mit evidenzgestuetzter OR-Option zulaesst.
  - Skill-spezifische Policy-Felder fuer OR-Zulaessigkeit, bounded rollout class und No-Gate-Fallback lokal erzwingen.
  - Sicherstellen, dass nicht freigegebene oder nicht ausreichend belegte Skills deterministisch im Codex-Pfad bleiben.
  - Reviewbare Artefakte oder Statusfelder fuer `OR_ALLOWED`, `OR_NOT_ELIGIBLE` und `OR_EVIDENCE_MISSING` erzeugen.
- Acceptance Criteria:
  - Ein Skill ohne explizite Eligibility oder ohne evidenzgestuetzte OR-Option zeigt kein OR-Gate.
  - Freigegebene bounded Skill-Klassen koennen ihre OR-Zulaessigkeit ueber einen gemeinsamen Contract statt ueber verstreute Einzellogik ausdruecken.
  - Nicht freigegebene Skill-Klassen fallen deterministisch auf Codex-only zurueck.
- Tests:
  - Negativtest fuer Skill ohne Eligibility-Eintrag
  - Negativtest fuer Skill mit fehlender OR-Evidenz
  - Positivtest fuer zugelassene bounded Skill-Klasse
  - Regressionstest fuer bestehenden Codex-only Pfad ohne Gate
- Model: 5.4
- Reason: Die Aufgabe ist implementierungsnah und sicherheitsrelevant, weil zuerst die skill-uebergreifende Zulassungsgrenze hart gezogen werden muss, bevor Gate-Anzeige oder OR-Hauptarbeit alltagstauglich werden.

### TASK-SPEC19.2 Unified operator gate with cost and confidence display
- Ziel: Ein einheitliches `1 = Codex` / `2 = OpenRouter`-Gate mit Modell-, Kosten- und Confidence-Hinweisen fuer alle zuerst zugelassenen bounded Skill-Klassen sichtbar und konsistent machen.
- Scope: Shared Operator-Gate-Ausgabe, Kosten- und Confidence-Voraussetzungen, skill-uebergreifende Prompt-Normalisierung und No-Gate-Verhalten bei fehlenden Pflichtdaten.
- Files:
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
  - documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py
  - documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
  - documentation/codex/model-routing/tests/
- Steps:
  - Das einheitliche Delegations-Gate mit `1 = Codex` und `2 = OpenRouter` fuer die ersten zugelassenen bounded Skill-Klassen normalisieren.
  - Sichtbare Modell-, Kosten- und Confidence-Felder als Pflichtbestandteil des OR-Gates behandeln.
  - Gate-Anzeige unterdruecken, wenn Kosten- oder Confidence-Daten fuer den konkreten Skilllauf fehlen oder unzulaessig sind.
  - Bestehende skill-spezifische Gate- oder Prompt-Ausgaben auf den gemeinsamen Operatorstil angleichen.
- Acceptance Criteria:
  - Zugelassene bounded Skill-Klassen zeigen denselben klaren Codex-vs-OpenRouter-Gate-Stil.
  - Ein OR-Gate ohne Modell-, Kosten- oder Confidence-Hinweis wird nicht als regulaere Auswahl angezeigt.
  - Fehlende Pflichtdaten fuehren reviewbar zu No-Gate oder Codex-only statt zu stiller degradierten OR-Auswahl.
- Tests:
  - Positivtest fuer Gate-Anzeige mit Kosten und Confidence
  - Negativtest fuer fehlende Kosten
  - Negativtest fuer fehlende Confidence
  - Regressionstest fuer bestehenden lokalen Codex-Ausgang
- Model: 5.4
- Reason: Ohne einheitliche, belastbare Gate-Anzeige bleibt der bounded OR worker im Alltag inkonsistent und schwer vertrauenswuerdig.

### TASK-SPEC19.3 Codex-owned acceptance, fallback, and operator-summary normalization
- Ziel: Nach jedem OR-Lauf eine feste Codex-owned Accept/Reject- und Fallback-Disziplin erzwingen, damit OR-Hauptarbeit nie stillschweigend als angenommen oder abgeschlossen gilt.
- Scope: Post-OR-Validierungszusammenfassung, Codex-owned final outcome, reject oder fallback bei fehlender Validierung oder Grenzverletzung sowie skill-uebergreifende Operator-Summary-Normalisierung.
- Files:
  - documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
  - documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py
  - documentation/codex/model-routing/tests/
  - documentation/codex/model-routing/or_healthcheck_telemetry_*.jsonl
- Steps:
  - Eine einheitliche Codex-owned Accept/Reject- und Fallback-Normalisierung fuer OR-Laeufe der ersten bounded Skill-Klassen definieren.
  - Fehlende Validierung, fehlende Pflichtartefakte oder unsichere Ergebnisse deterministisch als Reject oder Fallback behandeln.
  - Den finalen Operator-Ausgang so normalisieren, dass Modell, Kosten, Validation-Result und Accept/Reject-Status sichtbar bleiben.
  - Regression sichern, dass bestehende Codex-only und bereits bounded assist-only Pfade nicht als OR-accepted fehlklassifiziert werden.
- Acceptance Criteria:
  - Ein OR-Lauf gilt nie ohne aktive Codex-Abnahme als angenommen.
  - Fehlende oder fehlschlagende Validierung fuehrt zu reviewbarem Reject oder Fallback statt zu stiller Annahme.
  - Der Operator-Ausgang zeigt fuer akzeptierte und abgelehnte OR-Laeufe den finalen Codex-owned Status sichtbar an.
- Tests:
  - Positivtest fuer OR-Lauf mit kompletter Validierung und accept-faehigem Ergebnis
  - Negativtest fuer fehlende Validierung
  - Negativtest fuer unsicheres oder reject-pflichtiges Ergebnis
  - Regressionstest fuer bestehende Codex-only und assist-only bounded Pfade
- Model: 5.4
- Reason: Dieser Slice verbindet den OR-Hauptarbeitsmodus mit der fuer den Alltag entscheidenden Codex-Abnahme-Disziplin und haelt die Governance-Grenze explizit.

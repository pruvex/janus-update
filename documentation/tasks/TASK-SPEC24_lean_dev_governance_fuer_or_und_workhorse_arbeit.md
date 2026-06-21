TASK-SPEC24
- Source Spec: documentation/SPEC/Spec Done/24_lean_dev_governance_fuer_or_und_workhorse_arbeit.md
- Backlog Item: N/A
- Feature: Lean Dev-Governance fuer OR- und Workhorse-Infrastrukturarbeit
- Generated At: 2026-06-21

## Generated Tasks

### TASK-SPEC24.1 Codify the Lean-Dev eligibility, minimum evidence, and escalation rules
- Ziel: Die genehmigte Lean-Dev-Regel so in die operative Governance ueberfuehren, dass kleine und mittlere interne Dev-Slices kuenftig schneller laufen duerfen, waehrend Janus-Produktarbeit strikt ausgeschlossen bleibt.
- Scope: Klare Lean-vs-strict-Regeln fuer interne Dev-Arbeit, definierte Minimalpflichten, definierte Eskalationsbedingungen und keine Aufweichung der Janus-Produktpipeline. Nur versionierte Repo-Governance-Dateien sind in Scope; keine installierten Skill-Arbeitskopien unter `C:\\Users\\pruve\\.codex\\skills\\`.
- Files:
  - AGENTS.md
  - documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md
  - development/README.md
  - development/DEV_STATE.md
- Steps:
  - Die Lean-Dev-Regel in `development/README.md` und `development/DEV_STATE.md` als kanonische Dev-Regel verankern.
  - `AGENTS.md` und `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md` nur so weit nachziehen, dass die Trennung zwischen strenger Janus-Produktarbeit und leaner interner Dev-Arbeit eindeutig bleibt.
  - Die Minimalpflichten fuer Lean-Dev-Arbeit explizit festhalten: Validation, `CURRENT_STATE`, sinnvoller Git-Checkpoint.
  - Die automatischen Eskalationsbedingungen zurueck in den strengen Modus explizit festhalten.
  - Sicherstellen, dass Janus-Produktarbeit ausdruecklich im strengen Modus bleibt und keine Produktskills stillschweigend in den Lean-Modus wechseln.
- Acceptance Criteria:
  - Die Lean-Dev-Regel ist in den Dev-Source-of-Truth-Artefakten klar dokumentiert.
  - `AGENTS.md` und `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md` widersprechen der Lean-Dev-Regel nicht.
  - Die Minimalpflichten fuer Validation, `CURRENT_STATE` und sinnvolle Git-Checkpoints sind explizit dokumentiert.
  - Die Eskalationsbedingungen zurueck in den strengen Modus sind explizit dokumentiert.
  - Janus-Produktarbeit bleibt ausdruecklich ausserhalb des Lean-Modus.
- Tests:
  - Dokumentations- und Regelkonsistenz-Check fuer Lean-vs-strict-Abgrenzung in `AGENTS.md`, `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`, `development/README.md` und `development/DEV_STATE.md`
  - Negativcheck, dass Janus-Produktarbeit nicht in den Lean-Modus gezogen wird
  - Scoped `git diff --check` fuer die Governance-Dateien
- Model: 5.4
- Reason: Diese Slice macht aus der genehmigten Lean-Regel einen tatsaechlich anwendbaren Arbeitsmodus, ohne schon weitere Dev-Umsetzungen mitzuschleifen.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC24.1_final_audit.md` dokumentiert. Die Lean-Dev-Governance-Regel ist damit task-scharf in den repo-owned Governance-Artefakten verankert, waehrend Janus-Produktarbeit explizit strikt bleibt; Spec 24 insgesamt bleibt offen, weil `TASK-SPEC24.2` die operative Anwendung auf aktuelle OR-/Workhorse-Entry-Points erst noch umsetzt.

### TASK-SPEC24.2 Apply the Lean-Dev rule to current OR and workhorse infrastructure flow entrypoints
- Ziel: Den neuen Lean-Dev-Modus so an die aktuellen internen OR-/Workhorse-Arbeitswege anbinden, dass wir ihn sofort praktisch nutzen koennen.
- Scope: Operative Anwendung des Lean-Modus auf die aktuellen repo-owned Dev-Einstiege, klare Lean-vs-strict-Markierung der betroffenen OR-/Workhorse-Arbeit und keine Ausweitung auf Janus-Produktskills oder installierte Skill-Arbeitskopien unter `C:\\Users\\pruve\\.codex\\skills\\`.
- Files:
  - development/README.md
  - development/DEV_STATE.md
  - documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
  - documentation/codex/skills/janus-git-governance/SKILL.md
- Steps:
  - Die aktuellen repo-owned OR-/Workhorse-Einstiege explizit als Lean-Dev-anwendbar oder strict-only markieren, statt nur allgemein von Lean zu sprechen.
  - Im Runbook den operativen Lean-Ablauf fuer kleine und mittlere bounded Dev-Slices so beschreiben, dass Einstieg, Stop-Gates und Git-Grenzen im Alltag direkt erkennbar sind.
  - In `development/README.md` und `development/DEV_STATE.md` den aktuellen Aktivierungsstand von der reinen Governance-Kodifizierung auf den naechsten operativen Anwendungsslice fortschreiben.
  - In der repo-versionierten `janus-git-governance`-Skillquelle klar halten, wie Lean-Delivery fuer interne Dev-Arbeit mit expliziter Git-Freigabe zusammenhaengt, ohne Janus-Produktarbeit oder Release-Autoritaet aufzuweichen.
  - Keine Janus-Produktskills, keine installierten Skill-Kopien und keine Produktionsrouting-Aussage stillschweigend in den Lean-Modus ziehen.
- Acceptance Criteria:
  - Die aktuellen repo-owned OR-/Workhorse-Einstiege koennen anhand der Dokumentation klar als Lean-Dev oder strict-only eingeordnet werden.
  - Der Lean-Flow ist fuer die aktuelle Dev-Arbeit praktisch anwendbar, inklusive sichtbarer Stop-Gates und operativer Abgrenzung.
  - Git-Checkpoint-, Push- und Freigabepflichten bleiben fuer Lean-Dev-Arbeit nachvollziehbar und widerspruchsfrei.
  - Janus-Produktskills und installierte Skill-Arbeitskopien bleiben unveraendert ausserhalb dieses Slices.
- Tests:
  - Dokumentations- und Runbook-Check fuer praktische Lean-Anwendbarkeit in `development/README.md`, `development/DEV_STATE.md`, `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md` und `documentation/codex/skills/janus-git-governance/SKILL.md`
  - Negativcheck gegen stillschweigende Ausweitung auf Janus-Produktskills, installierte Skill-Arbeitskopien oder Produktionsrouting-Autoritaet
  - `python C:\Users\pruve\.codex\skills\janus-task-breakdown\scripts\validate_task_handoff.py --task documentation/tasks/TASK-SPEC24_lean_dev_governance_fuer_or_und_workhorse_arbeit.md --target TASK-SPEC24.2`
- Model: 5.4
- Reason: Diese Slice macht den neuen Lean-Dev-Modus sofort im Alltag nutzbar, statt ihn nur als abstrakte Regel stehen zu lassen.
- Closeout: Final Audit PASS ist in `documentation/tasks/TASK-SPEC24.2_final_audit.md` dokumentiert. Die operative Lean-vs-strict-Markierung der aktuellen repo-owned OR-/Workhorse-Entry-Points ist damit task-scharf abgeschlossen; Spec 24 insgesamt ist DONE und bleibt weiterhin explizit auf interne repo-owned Dev-/OR-/Workhorse-Governance begrenzt.

@janus-task-breakdown
Spec: documentation/SPEC/24_lean_dev_governance_fuer_or_und_workhorse_arbeit.md
Task: documentation/tasks/TASK-SPEC24_lean_dev_governance_fuer_or_und_workhorse_arbeit.md
Backlog Item: N/A
Target Task: TASK-SPEC24.2
Mode: TASK_REFINEMENT
Execution Model: 5.4
Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK
Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF

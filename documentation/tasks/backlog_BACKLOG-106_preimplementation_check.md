PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: BACKLOG-106
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-106_root_db_artefakte_klassifizieren_und_laufzeitpfad_definieren.md
Spec: N/A WITH REASON - This is a small bounded backlog hygiene task for healthcheck classification and runtime-path documentation, without a separate feature Spec.
Backlog Item: BACKLOG-106
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Active Janus runtime persistence is already routed to `%APPDATA%/Janus Projekt/janus.db` in `backend/data/database.py`, while the current root `chat_history.db` and `costs.db` files have no active code references and behave like legacy split-db artifacts.
- The bound scope is atomic: classify exactly `janus.db`, `chat_history.db`, and `costs.db`, update the health snapshot so they stop polluting the generic `root_suspicious` bucket, and add only the minimal ignore/documentation needed for that classification.
- Artifact identity is consistent across `BACKLOG-106`, `documentation/backlog/BACKLOG.md`, and the task artifact `documentation/tasks/backlog_BACKLOG-106_root_db_artefakte_klassifizieren_und_laufzeitpfad_definieren.md`.
- Risk is LOW because the task stays in local hygiene reporting, documentation, and ignore handling instead of modifying runtime persistence behavior or migrating user data.
Affected Files:
- documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
- documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- .gitignore
- documentation/test-runs/BACKLOG-106_execution_validation.md
Evidence Focus:
- python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY
- python C:\Users\pruve\.codex\skills\janus-backlog-handoff\scripts\validate_backlog.py C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md
- python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py C:\KI\Janus-Projekt\documentation\tasks\backlog_BACKLOG-106_preimplementation_check.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY
- python C:\Users\pruve\.codex\skills\janus-backlog-handoff\scripts\validate_backlog.py C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/backlog/BACKLOG.md section for BACKLOG-106
- documentation/tasks/backlog_BACKLOG-106_root_db_artefakte_klassifizieren_und_laufzeitpfad_definieren.md
- backend/data/database.py and documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
Drop Context:
- BACKLOG-105 audit/doc history
- unrelated root-log cleanup details
- broader script-hardening backlog work
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: low
Reason: The task is a deterministic hygiene classification pass on a warm `5.4` context with explicit evidence commands and no open architecture decision.
User Action: Say `ok` to start implementation of `BACKLOG-106` with the bound scope and evidence gate above.

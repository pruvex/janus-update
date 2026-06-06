PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: BACKLOG-107
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-107_script_output_pfade_haerten_und_root_nebenprodukte_reduzieren.md
Spec: N/A WITH REASON - This is a bounded backlog hygiene and local-tooling hardening task for recurring script output paths, without a separate feature Spec.
Backlog Item: BACKLOG-107
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The active evidence already shows a narrow but real recurring root-artifact family: `.codex-vite-*.log`, `backend_*.log`, `backend_*.out.log`, `backend_*.err.log`, `startdev.log`, and `tmp_uv8011_*.log` still appear under `root_suspicious` in the monthly health snapshot.
- The bound scope is atomic enough for implementation: identify which of those recurring artifacts are still produced by versioned local dev/debug/helper scripts, route their default outputs into intentional target paths, and add only the minimal healthcheck or documentation updates needed to keep that routing explicit.
- Artifact identity is consistent across `BACKLOG-107`, `documentation/backlog/BACKLOG.md`, and the task artifact `documentation/tasks/backlog_BACKLOG-107_script_output_pfade_haerten_und_root_nebenprodukte_reduzieren.md`.
- Risk is MEDIUM because the task may touch several local launcher/helper paths, but it stays inside dev tooling, repo hygiene, and healthcheck evidence instead of product architecture or runtime feature behavior.
- A Git checkpoint via `janus-git-governance` is recommended before any later commit or push because this work may span multiple related script files and evidence docs.
Affected Files:
- scripts/dev-log-utils.cjs
- scripts/run-backend-dev.cjs
- scripts/run-vite-dev.cjs
- scripts/write-startup-marker.cjs
- package.json
- documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
- documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- .gitignore
- documentation/test-runs/BACKLOG-107_execution_validation.md
Evidence Focus:
- python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY
- rg -n "backend_hotfix|backend_live|backend_persist|backend_restart|backend_start_manual|backend_verify|tmp_uv8011|startdev\\.log|\\.codex-vite" scripts package.json main.electron.cjs documentation -S
- python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py C:\KI\Janus-Projekt\documentation\tasks\backlog_BACKLOG-107_preimplementation_check.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY
- rg -n "backend_hotfix|backend_live|backend_persist|backend_restart|backend_start_manual|backend_verify|tmp_uv8011|startdev\\.log|\\.codex-vite" scripts package.json main.electron.cjs documentation -S
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/backlog/BACKLOG.md section for BACKLOG-107
- documentation/tasks/backlog_BACKLOG-107_script_output_pfade_haerten_und_root_nebenprodukte_reduzieren.md
- documentation/codex/skills/janus-health-check/scripts/health_snapshot.py and the directly involved local launcher/helper scripts
Drop Context:
- unrelated DONE backlog history
- broad release or audit context
- historical root files that cannot be traced to a current versioned script path
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: low
Reason: The task stays in a warm `5.4` context, the implementation is a bounded local tooling hardening pass, and the evidence surface is explicit.
User Action: Say `ok` to start implementation of `BACKLOG-107` with the bound scope and evidence gate above.

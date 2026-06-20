EXECUTION_PATCH_CANDIDATE_REVIEW
Status: PASS
Target Task: TASK-BACKLOG-107-R1.1
Changed Files:
- scripts/dev-log-utils.cjs
- documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
- documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- .gitignore
- documentation/test-runs/BACKLOG-107_execution_validation.md
Risk List:
- Patch is still proposal-only and may miss a hidden schema or migration dependency.
- Codex must verify that no broader address normalization behavior regresses outside the bounded file cluster.
Suggested Validation Steps:
- python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY
- rg -n "debug_logs|documentation/logs/dev-runtime|\\.codex-vite|backend_hotfix|backend_live|backend_persist|backend_restart|backend_start_manual|backend_verify|tmp_uv8011" scripts package.json main.electron.cjs documentation -S
- node -e "const { runWithLogs } = require('./scripts/dev-log-utils.cjs'); console.log(typeof runWithLogs === 'function' ? 'PASS' : 'FAIL')"
- manual diff review for runtime-log target alignment only
Manual Validation Note: Codex still owns manual Janus validation. This read-only delegated patch proposal does not satisfy manual product verification.
Codex Acceptance Rule: Codex must review this proposal and decide whether to apply or reject it. The delegated path has no apply or completion authority.
Notes: Captured from read-only Codex CLI sidecar patch proposal.

PATCH_TEXT
--- a/scripts/dev-log-utils.cjs
+++ b/scripts/dev-log-utils.cjs
@@ -10,7 +10,7 @@
 }

 function createLogStreams(prefix) {
-  const logDir = path.join(process.cwd(), "debug_logs");
+  const logDir = path.join(process.cwd(), "documentation", "logs", "dev-runtime");
   ensureDir(logDir);
   const stamp = timestampForFile();
   const outPath = path.join(logDir, `${prefix}_${stamp}.out.log`);
--- a/documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
+++ b/documentation/codex/skills/janus-health-check/scripts/health_snapshot.py
@@ -34,23 +34,23 @@
 }

 KNOWN_ROOT_LEGACY_LOG_ARTIFACTS = {
-    ".codex-vite-err.log": "legacy root Vite error log; current versioned dev start path writes Vite logs under debug_logs/",
-    ".codex-vite-out.log": "legacy root Vite output log; current versioned dev start path writes Vite logs under debug_logs/",
-    "backend_hotfix.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_hotfix.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_live.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_live.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_persist.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_persist.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_restart.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_restart.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_start.log": "legacy root backend start log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_start_manual.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_start_manual.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_verify.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "backend_verify.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "startdev.log": "legacy root start-dev log; current versioned startup telemetry belongs under documentation/logs and dev runtime logs under debug_logs/",
-    "tmp_uv8011_err.log": "legacy root temporary backend log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "tmp_uv8011_out.log": "legacy root temporary backend log; current versioned backend dev/runtime logs belong under debug_logs/",
+    ".codex-vite-err.log": "legacy root Vite error log; current versioned dev start path writes Vite logs under documentation/logs/dev-runtime/",
+    ".codex-vite-out.log": "legacy root Vite output log; current versioned dev start path writes Vite logs under documentation/logs/dev-runtime/",
+    "backend_hotfix.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_hotfix.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_live.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_live.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_persist.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_persist.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_restart.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_restart.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_start.log": "legacy root backend start log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_start_manual.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_start_manual.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_verify.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "backend_verify.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "startdev.log": "legacy root start-dev log; current versioned startup telemetry belongs under documentation/logs and dev runtime logs under documentation/logs/dev-runtime/",
+    "tmp_uv8011_err.log": "legacy root temporary backend log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "tmp_uv8011_out.log": "legacy root temporary backend log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
 }


--- a/documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
+++ b/documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
@@ -48,7 +48,7 @@

 ## Local Runtime Logs

 - Local dev runtime logs for `npm run start-backend-only`,
   `npm run start-backend-only-without-reload`, and `npm run start-vite`
-  belong under `debug_logs/`.
+  belong under `documentation/logs/dev-runtime/`.
 - Local startup telemetry markers and aggregated startup timing logs belong
   under `documentation/logs/janus_startup_telemetry.log`.
 - Versioned dev start paths should not create recurring backend or Vite
--- a/.gitignore
+++ b/.gitignore
@@ -24,6 +24,7 @@
 janus_fallback.db*
 # Runtime fallback logs (generated during local dev runs)
 backend/backend/
+documentation/logs/dev-runtime/
 e2e_janus.db*
 playwright-report/data/
 playwright-report/trace/
--- a/documentation/test-runs/BACKLOG-107_execution_validation.md
+++ b/documentation/test-runs/BACKLOG-107_execution_validation.md
@@ -1,19 +1,18 @@
 # BACKLOG-107 Execution Validation

 - **Target Task:** BACKLOG-107
-- **Date:** 2026-06-06
-- **Scope:** Haerte die verbliebenen versionierten Script-Output-Pfade fuer Startup-Telemetrie und reduziere wiederkehrende Root-Log-Funde durch gezielte Healthcheck-Klassifizierung statt generischem `root_suspicious`.
+- **Date:** 2026-06-16
+- **Scope:** Verschiebe den ersten gemeinsamen versionierten Backend-/Vite-Dev-Runtime-Log-Slice von `debug_logs/` nach `documentation/logs/dev-runtime/` und richte die gekoppelten Hygiene-Referenzen darauf aus.

 ## Checks

-- `node --check C:\KI\Janus-Projekt\scripts\write-startup-marker.cjs` - PASS
-- `node --check C:\KI\Janus-Projekt\electron\startup-telemetry.cjs` - PASS
-- `python -m py_compile C:\KI\Janus-Projekt\backend\services\telemetry\startup_config.py C:\KI\Janus-Projekt\backend\main.py C:\KI\Janus-Projekt\documentation\codex\skills\janus-health-check\scripts\health_snapshot.py` - PASS
-- `python -m pytest -q C:\KI\Janus-Projekt\tests\test_startup_config.py -vv` - PASS
+- `node --check C:\KI\Janus-Projekt\scripts\dev-log-utils.cjs` - PASS
 - `python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY` - PASS
+- `rg -n "debug_logs|documentation/logs/dev-runtime|\.codex-vite|backend_hotfix|backend_live|backend_persist|backend_restart|backend_start_manual|backend_verify|tmp_uv8011" scripts package.json main.electron.cjs documentation -S` - PASS
+- `node -e "const { runWithLogs } = require('./scripts/dev-log-utils.cjs'); console.log(typeof runWithLogs === 'function' ? 'PASS' : 'FAIL')"` - PASS
 - Targeted code inspection confirmed:
-  - startup telemetry markers now target `documentation/logs/janus_startup_telemetry.log`
-  - versioned backend/Vite dev-runtime logs still target `debug_logs/`
+  - shared versioned backend/Vite dev-runtime logs now target `documentation/logs/dev-runtime/`
   - known legacy root log files are reported under `root_legacy_log_artifacts`
-  - generic `root_suspicious` is empty for the current known recurring root-log family
+  - startup telemetry remains routed to `documentation/logs/janus_startup_telemetry.log`

 ## Manual Janus Evidence

@@ -21,4 +20,4 @@

 ## Notes

-The root log files themselves were intentionally not deleted in this execution. BACKLOG-107 stays limited to path hardening and evidence/reporting clarity for recurring script-related artifacts.
+This slice intentionally stays bounded to the shared helper path flip plus aligned hygiene references. It does not widen into startup telemetry, legacy artifact deletion, or broader launcher cleanup.

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
@@ -37,18 +37,18 @@
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
     "startdev.log": "legacy root start-dev log; current versioned startup telemetry belongs under documentation/logs and dev runtime logs under debug_logs/",
-    "tmp_uv8011_err.log": "legacy root temporary backend log; current versioned backend dev/runtime logs belong under debug_logs/",
-    "tmp_uv8011_out.log": "legacy root temporary backend log; current versioned backend dev/runtime logs belong under debug_logs/",
+    "tmp_uv8011_err.log": "legacy root temporary backend log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
+    "tmp_uv8011_out.log": "legacy root temporary backend log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
 }
--- a/documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
+++ b/documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
@@ -49,14 +49,14 @@
 ## Local Runtime Logs

 - Local dev runtime logs for `npm run start-backend-only`,
   `npm run start-backend-only-without-reload`, and `npm run start-vite`
-  belong under `debug_logs/`.
+  belong under `documentation/logs/dev-runtime/`.
 - Local startup telemetry markers and aggregated startup timing logs belong
   under `documentation/logs/janus_startup_telemetry.log`.
 - Versioned dev start paths should not create recurring backend or Vite
   runtime logs directly in the repository root.
 - Versioned startup telemetry paths should not write into ad-hoc folders such
   as `documentation/Startup log`.
 - Historical root log artifacts are hygiene cleanup, not proof of the intended
   target path.
--- a/.gitignore
+++ b/.gitignore
@@ -25,3 +25,4 @@
 backend/backend/
 e2e_janus.db*
 playwright-report/data/
 playwright-report/trace/
+documentation/logs/dev-runtime/
--- a/documentation/test-runs/BACKLOG-107_execution_validation.md
+++ b/documentation/test-runs/BACKLOG-107_execution_validation.md
@@ -12,8 +12,8 @@
 - `python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\KI\Janus-Projekt --mode MONTHLY` - PASS
 - Targeted code inspection confirmed:
   - startup telemetry markers now target `documentation/logs/janus_startup_telemetry.log`
-  - versioned backend/Vite dev-runtime logs still target `debug_logs/`
+  - versioned backend/Vite dev-runtime logs now target `documentation/logs/dev-runtime/`
   - known legacy root log files are reported under `root_legacy_log_artifacts`
   - generic `root_suspicious` is empty for the current known recurring root-log family

 ## Manual Janus Evidence

# Central Task Registry

This registry tracks feature tasks, test validations, and pipeline runs.

## Test Pipeline Validations

### TEST-RUN-2026-05-21-011 - Ops Recovery Kill Switches

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 17 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/17_ops_recovery_kill_switches.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-011_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-011_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-011_results.md`
- **Runbook**: `documentation/test-results/TEST-RUN-2026-05-21-011/ops_recovery_runbook.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-011_final_audit.md`
- **Validation**: PASS with `10/10` ops recovery checks, `0` failed, `0` blocked. The gate validates the packaged-local beta backend at `http://127.0.0.1:8001` for provider access, external/current-data tools, write/destructive tools, local beta user lock, telemetry mode, restore procedure, rotation dry-run, beta export/delete dry-run and incident reporting.
- **Remediation**: Added a central ops kill-switch service, provider gateway enforcement, tool executor enforcement, direct RAG/Memory/Calendar route gates, an authenticated safe dry-run inventory endpoint and telemetry mode enforcement for event ingest, remote upload, feedback webhook, Sentry initialization and dependency telemetry opt-out flags.
- **Watchpoints**: Env/process-level switches are correct for the current packaged-local Electron beta. A future hosted multi-instance beta should move kill-switch state into a durable operator-controlled config plane.
- **Changed Files**: `backend/services/ops_kill_switches.py`, `backend/services/llm_gateway.py`, `backend/services/tool_executor.py`, `backend/dependencies.py`, `backend/api/routers/system.py`, `backend/api/routers/rag.py`, `backend/api/routers/memory.py`, `backend/api/routers/calendar.py`, `backend/tests/test_ops_kill_switches.py`, `tests/e2e/generated/TEST-RUN-2026-05-21-011.*`, `documentation/test-runs/TEST-RUN-2026-05-21-011_*`, `documentation/test-results/TEST-RUN-2026-05-21-011*`

### TEST-RUN-2026-05-21-010 - Beta Abuse Limits and Cost Controls

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 16 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/16_beta_abuse_limits_and_cost_controls.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-010_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-010_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-010_results.md`
- **Limit Policy**: `documentation/test-runs/TEST-RUN-2026-05-21-010_beta_abuse_limit_policy.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-010_final_audit.md`
- **Validation**: PASS with `10/10` beta-abuse and cost-control checks, `0` failed, `0` blocked. The gate validates the packaged-local beta backend at `http://127.0.0.1:8001` for per-user and global API burst limits, provider spend/retry-storm/tool-flood/broad-crawl gates, upload size limits, safe error wording and operator-alert privacy.
- **Remediation**: Added mutating API abuse middleware with per-key/user and global sliding-window limits; added safe `429`/`413` responses; capped image/PDF uploads; extended retry/cost/tool/crawl abuse detection; removed raw prompt snippets from abuse warning logs; added `JANUS_DISABLE_SENTRY` for capped test runs.
- **Watchpoints**: The in-process limiter is appropriate for the current packaged-local Electron beta. A future hosted multi-process beta needs durable centralized counters plus provider-side hard spend caps.
- **Changed Files**: `backend/main.py`, `backend/api/routers/images.py`, `backend/api/routers/rag.py`, `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/test_beta_abuse_limits.py`, `tests/e2e/generated/TEST-RUN-2026-05-21-010.*`, `documentation/test-runs/TEST-RUN-2026-05-21-010_*`

### TEST-RUN-2026-05-21-009 - Deployment Headers CORS CSP Cookie Scan

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 15 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/15_deployment_headers_cors_csp_cookie_scan.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-009_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-009_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-009_results.md`
- **Deployment Policy**: `documentation/test-runs/TEST-RUN-2026-05-21-009_deployment_surface_policy.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-009_final_audit.md`
- **Validation**: PASS with `10/10` deployment-surface checks, `0` failed, `0` blocked. The gate validates the real packaged-local target at `http://127.0.0.1:8001` for CSP/security headers, CORS allow/deny behavior, cookie posture, debug/source-map exposure and file response headers.
- **Remediation**: Restricted beta CORS origins/headers/methods/exposed headers; removed `null` origin from packaged beta; disabled public source maps unless explicitly enabled; hardened user-image responses against wildcard CORS and added private cache/nosniff/disposition controls.
- **Watchpoints**: Hosted beta/staging still requires a separate HTTPS/HSTS/proxy/CDN validation. CSP retains `'unsafe-inline'` for legacy frontend compatibility.
- **Changed Files**: `backend/main.py`, `vite.config.js`, `tests/e2e/generated/TEST-RUN-2026-05-21-009.*`, `documentation/test-runs/TEST-RUN-2026-05-21-009_*`

### TEST-RUN-2026-05-21-008 - Beta Telemetry Logging Privacy Hardening

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 14 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/14_beta_telemetry_logging_privacy_hardening.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-008_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-008_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-008_results.md`
- **Sink Inventory**: `documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_sink_inventory.md`
- **Access/Retention**: `documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_access_retention.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-008_final_audit.md`
- **Validation**: PASS with `10/10` telemetry privacy checks, `0` failed, `0` blocked. The gate validates local logs, backend/frontend Sentry, Supabase logging, optional feedback webhook handling, runtime error privacy and evidence redaction.
- **Remediation**: Disabled/masked frontend Sentry Replay; stripped frontend Sentry user/request/breadcrumb data; added backend Sentry `before_send` redaction; redacted context telemetry and Supabase payload uploads; expanded shared redaction for prompt/content/file payload classes.
- **Watchpoints**: Chroma/PostHog dependency telemetry remains anonymized dependency telemetry watchpoint; provider-side Sentry/Supabase retention/access settings require owner discipline before broad beta.
- **Changed Files**: `backend/utils/redaction.py`, `backend/main.py`, `backend/api/routers/context.py`, `backend/services/logging/logger_core.py`, `backend/services/logging/supabase_client.py`, `backend/tests/test_observability_redaction.py`, `frontend/js/app.js`, `tests/e2e/generated/TEST-RUN-2026-05-21-008.*`, `documentation/test-runs/TEST-RUN-2026-05-21-008_*`

### TEST-RUN-2026-05-21-007 - Production Secret Rotation and Leak Scan

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 13 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/13_production_secret_rotation_and_leak_scan.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-007_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-007_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-007_results.md`
- **Redacted Inventory**: `documentation/test-runs/TEST-RUN-2026-05-21-007_secret_inventory.md`
- **Rotation Runbook**: `documentation/test-runs/TEST-RUN-2026-05-21-007_secret_rotation_runbook.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-007_final_audit.md`
- **Validation**: PASS with `10/10` secret rotation and leak-scan checks, `0` failed, `0` blocked. The gate validates Janus' packaged-local Electron beta model across local secret inventory, repo, bundle, logs, runtime responses and evidence artifacts without writing raw secrets.
- **Remediation**: Made Sentry source-map upload explicit via `JANUS_UPLOAD_SOURCEMAPS=1`; ignored `.env.*`; removed hardcoded Supabase material from `tools/check_supabase_logs.py`; replaced credential-shaped fake literals in tests/spec documentation.
- **Watchpoints**: Provider-side rotation, least-privilege and cost caps still require owner console action before broad beta distribution.
- **Changed Files**: `.gitignore`, `vite.config.js`, `tools/check_supabase_logs.py`, `backend/tests/test_observability_redaction.py`, `documentation/TEST_SPEC/02_security_safety/01_secrets_env_and_frontend_exposure.md`, `tests/e2e/generated/TEST-RUN-2026-05-21-007.*`, `documentation/test-runs/TEST-RUN-2026-05-21-007_*`

### TEST-RUN-2026-05-21-006 - Packaged Local Beta Profile Isolation

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 12 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/12_multi_account_staging_isolation.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-006_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-006_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-006_results.md`
- **Profile Map**: `documentation/test-runs/TEST-RUN-2026-05-21-006_profile_isolation_map.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-006_final_audit.md`
- **Validation**: PASS with `10/10` packaged-local profile isolation checks, `0` failed, `0` blocked. The gate validates Janus' real local Electron beta model: separate AppData/SQLite/file/artifact roots plus tool/session/debug boundaries.
- **Remediation**: Added beta-safe debug endpoint gate; expanded cross-user detection for User B/Profile B/resourceId/JWT-cookie reuse prompts; added custom profile-isolation runner and evidence.
- **Watchpoints**: This is not hosted SaaS tenant certification. If Janus later ships hosted accounts, rerun Spec 12 with real staging identities and server-side tenant IDs.
- **Changed Files**: `backend/dependencies.py`, `backend/main.py`, `backend/api/routers/system.py`, `backend/services/orchestrator/execution_dispatcher.py`, `documentation/TEST_SPEC/02_security_safety/12_multi_account_staging_isolation.md`, `tests/e2e/generated/TEST-RUN-2026-05-21-006.*`, `documentation/test-runs/TEST-RUN-2026-05-21-006_*`

### TEST-RUN-2026-05-21-005 - Packaged Local Beta Environment Security Baseline

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 11 beta/production hardening gate
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/11_staging_environment_security_baseline.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-005_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-005_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-005_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-005_final_audit.md`
- **Validation**: PASS with `10/10` packaged-local beta checks, `0` failed, `0` blocked. The gate now validates Janus' real Electron desktop beta model instead of hosted SaaS staging.
- **Remediation**: Removed PyInstaller `.env` bundling from `janus_backend.spec`; rebuilt and verified `frontend/dist`; validated local backend health, AppData/resource separation, Keyring/AppData secret model, packaged dev-surface guards and update metadata.
- **Watchpoints**: Build a fresh installer before actual beta shipment; source-map upload/exposure policy remains covered by Specs 14/15.
- **Changed Files**: `documentation/TEST_SPEC/02_security_safety/11_staging_environment_security_baseline.md`, `janus_backend.spec`, `tests/e2e/generated/TEST-RUN-2026-05-21-005.staging-environment.spec.js`, `tests/e2e/generated/TEST-RUN-2026-05-21-005.staging.playwright.config.js`, `documentation/test-runs/TEST-RUN-2026-05-21-005_*`

### TEST-RUN-2026-05-21-004 - Security ReviewSpec Suite

- **Status**: DONE
- **Audit**: PASS WITH WATCHPOINTS
- **Source**: Security ReviewSpec Suite / launch-gate review
- **ReviewSpec**: `documentation/TEST_SPEC/02_security_safety/10_security_reviewspec_suite.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-004_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-004_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-004_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-004_final_audit.md`
- **Validation**: PASS with `12/12` review checks, `0` failed, `0` blocked. Review decision is `PASS WITH WATCHPOINTS`.
- **Remediation**: Fixed telemetry privacy in `backend/main.py`: Sentry now has `send_default_pii=False`, environment-configurable DSN/sampling, production trace default `0.1`, and production profile default `0.0`.
- **Watchpoint**: Public/staging launch still needs target-environment evidence for real multi-account users, HTTPS/HSTS, domain CORS/CSP/cookies, retention and operations sign-off.
- **Changed Files**: `backend/main.py`, `tests/e2e/generated/TEST-RUN-2026-05-21-004.security-review.spec.js`, `documentation/test-runs/TEST-RUN-2026-05-21-004_*`

### TEST-RUN-2026-05-21-003 - Security Mini-Prep Review

- **Status**: DONE
- **Audit**: PASS
- **Source**: Security Spec 09 prep-gate validation
- **ReviewSpec**: `documentation/TEST_SPEC/02_security_safety/09_mini_prep_security_review.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-003_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-003_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-003_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-003_final_audit.md`
- **Validation**: PASS with `10/10` preflight checks, `0` failed, `0` blocked. Review decision is `GO WITH WATCHPOINTS`.
- **Watchpoint**: Local prep validates disposable A/B fixture identities plus existing local E2E auth; true multi-account staging users remain environment-specific for a future launch/staging gate.
- **Changed Files**: `tests/e2e/generated/TEST-RUN-2026-05-21-003.mini-prep.spec.js`, `documentation/test-runs/TEST-RUN-2026-05-21-003_plan.json`

### TEST-RUN-2026-05-21-002 - API External Tool Fallback Honesty

- **Status**: DONE
- **Audit**: PASS
- **Source**: Spec 09 tools/skills validation
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/09_api_external_tool_fallback_honesty.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-002_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-002_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-002_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-002_final_audit.md`
- **Validation**: PASS with `22/22` tests, `0` failed, `0` blocked. Provider parity is green for GPT and Gemini; functional, prompt-injection and security categories are all 100%.
- **Remediation**: Added honest unavailable/no-source behavior for websearch/current-data, RSS/news fallback, Wikipedia, weather, geo routing, and price/current-data tools; added deterministic blockers for simulated external source failures.
- **Changed Files**: `backend/tool_registry.py`, `backend/tools/rss_service.py`, `backend/tools/wiki_service.py`, `backend/tools/weather_service.py`, `backend/tools/geo_service.py`, `backend/tools/finance_tools.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/tools/test_external_tool_fallback_honesty.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### TEST-RUN-2026-05-20-023 - Logging, Telemetry and Audit Privacy

- **Status**: DONE
- **Audit**: PASS
- **Source**: Spec 08 observability privacy validation
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/08_logging_telemetry_and_audit_privacy.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-023_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-023_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-023_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-023_final_audit.md`
- **Privacy Scan**: `documentation/test-runs/TEST-RUN-2026-05-20-023_privacy_scan.md`
- **Validation**: PASS with `28/28` tests, `0` failed, `0` blocked. Provider parity is green for GPT and Gemini; functional, prompt-injection and security categories are all 100%.
- **Remediation**: Removed embedded Discord webhook fallback, added shared redaction utilities and global logging filters, sanitized telemetry/log attachments, redacted DLQ/debug-log boundaries, and suppressed provider/header debug logging.
- **Changed Files**: `backend/logger_config.py`, `backend/services/telemetry_service.py`, `backend/services/logging/logger_core.py`, `backend/services/logging/debug_engine.py`, `backend/utils/redaction.py`, `backend/tests/test_observability_redaction.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### TEST-RUN-2026-05-20-021 - Tool Execution Contract and Evidence

- **Status**: DONE
- **Audit**: PASS
- **Source**: Spec 07 tool execution contract validation
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/07_tool_execution_contract_and_evidence.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-021_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-021_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-021_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-021_final_audit.md`
- **Validation**: PASS with `18/18` tests, `0` failed, `0` blocked. Provider parity is green for GPT and Gemini; functional, prompt-injection and security categories are all 100%.
- **Changed Files**: `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/test_privacy_export_gate.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### TEST-RUN-2026-05-20-018 - Rate Limits, Quotas, Abuse and Cost Control

- **Status**: DONE
- **Audit**: PASS
- **Source**: Spec 07 final full validation
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/07_rate_limits_quotas_abuse_and_cost_control.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-018_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-018_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-018_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-018_final_audit.md`
- **Validation**: PASS with `26/26` tests, `0` failed, `0` blocked. Provider parity is green for GPT and Gemini; functional, intent-routing, prompt-injection and security categories are all 100%.
- **Backlog Closure**: BACKLOG-088, BACKLOG-089 and BACKLOG-090 are DONE/COMPLETED; no new findings remain.
- **Changed Files**: `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/execution_dispatcher.py`, `documentation/TEST_SPEC/02_security_safety/07_rate_limits_quotas_abuse_and_cost_control.md`, `documentation/backlog/BACKLOG.md`, `janus-dashboard/data/backlog.snapshot.json`

### TEST-RUN-2026-05-20-012 - Janus AI Safety Boundary

- **Status**: DONE
- **Audit**: PASS
- **Source**: Spec 06 final full validation
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/06_ai_prompt_injection_tool_abuse_and_data_exfiltration.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-012_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-012_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-012_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-012_final_audit.md`
- **Validation**: PASS with `57/57` tests, `0` failed, `0` blocked. Provider parity is green for GPT and Gemini; functional, intent-routing, prompt-injection and security categories are all 100%.
- **Changed Files**: `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/orchestrator/response_finalizer.py`, `backend/tests/test_privacy_export_gate.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `tests/e2e/generator/generate-live-runner.mjs`, `playwright.config.js`

### BACKLOG-080 - Playwright Duplicate Installation Collision

- **Status**: DONE
- **Audit**: PASS
- **Source**: BACKLOG-079 Execution
- **Task**: `documentation/tasks/backlog_BACKLOG-080_playwright_duplicate_installation_collision.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-080_final_audit.md`
- **Validation**: Duplicate frontend `@playwright/test` dependency removed; Playwright smoke test no longer fails with the second-require configuration error.
- **Changed Files**: `frontend/package.json`, `frontend/package-lock.json`

### BACKLOG-079 - Playwright beforeEach Timeout Fix

- **Status**: DONE
- **Audit**: PASS WITH FOLLOW-UP
- **Source**: TEST-RUN-2026-05-19-007 / TEST-RUN-2026-05-19-008
- **Task**: `documentation/tasks/backlog_BACKLOG-079_playwright_beforeeach_timeout_fix.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-079_final_audit.md`
- **Validation**: TEST-RUN-2026-05-19-008 executed 57 tests and no longer reproduces the prior 42-test `beforeEach` timeout blocker. Remaining red results are separate AI-Safety-/Oracle-/Flaky follow-ups.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### BACKLOG-074 - Planner Boundary Control

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-19-002 / TEST-RUN-2026-05-19-003
- **Task**: `documentation/tasks/task_074_planner_boundary_control_system_bugs.md`; `documentation/tasks/task_074_testplan_oracle_planner_boundary_fix.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-074_final_audit.md`
- **Validation**: TEST-RUN-2026-05-19-003 PASS with `32/32` tests. Planner Boundary Control validates direct response, short workflow, clarification, multi-step workspace planning boundaries, prompt-injection refusal and provider parity for GPT/Gemini.
- **Changed Files**: `backend/services/chat_orchestrator.py`, `backend/services/memory/retrieval_service.py`, `backend/services/orchestrator/execution_dispatcher.py`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `tests/e2e/generator/generate-live-runner.mjs`

### BACKLOG-069 - Ambiguity Gate Calibration Oracle

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-18-001 / TEST-RUN-2026-05-18-003
- **Task**: BACKLOG-069
- **Final Audit**: `documentation/test-runs/BACKLOG-069_final_audit.md`
- **Validation**: TEST-RUN-2026-05-18-003 PASS with `28/28` tests. Spec 03 oracle validates direct weather/geo routing for clear prompts and clarification/no-arbitrary-mutation behavior for ambiguous weather, memory, destructive, calendar and prompt-injection cases.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/TEST-RUN-2026-05-18-003_plan.json`, `tests/e2e/generated/TEST-RUN-2026-05-18-003.live.spec.js`, `documentation/test-runs/BACKLOG-069_final_audit.md`

### BACKLOG-064 - API Tool Routing Source Attribution Oracle

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-17-002 / TEST-RUN-2026-05-18-002
- **Task**: BACKLOG-064
- **Final Audit**: `documentation/test-runs/BACKLOG-064_final_audit.md`
- **Validation**: TEST-RUN-2026-05-18-002 PASS with `42/42` tests. Source-attribution TestPlan oracle validates Weather, Wikipedia, Geo/Routing, RSS/News and Websearch expectations while preserving security/prompt-injection cases.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/TEST-RUN-2026-05-18-002_plan.json`, `documentation/test-runs/BACKLOG-064_final_audit.md`

### BACKLOG-068 - API Privacy Boundary Product Gate Fix

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-17-025 / TEST-RUN-2026-05-17-028
- **Task**: BACKLOG-068
- **Final Audit**: `documentation/test-runs/BACKLOG-068_final_audit.md`
- **Validation**: TEST-RUN-2026-05-17-028 PASS with `26/26` tests. INT-004-GPT and INT-004-GEMINI now return deterministic privacy refusal with scope confirmation and no user-data export.
- **Changed Files**: `backend/services/orchestrator/execution_dispatcher.py`, `backend/tests/test_privacy_export_gate.py`, `documentation/TEST_SPEC/02_security_safety/02_api_response_privacy_and_debug_leakage.md`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### BACKLOG-067 - TestPlan Pattern Transfer Generator Fix

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-17-023 / TEST-RUN-2026-05-17-024
- **Task**: `documentation/tasks/backlog_BACKLOG-067_testplan_generator_pattern_transfer_fix.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-067_final_audit.md`
- **Validation**: TEST-RUN-2026-05-17-024 plan validates as TESTPLAN VALID with `26` generated tests. `INT-002`, `INT-003`, `INT-004`, and `SEC-005` provider-expanded cases contain the exact TestSpec `Expected containsAny Patterns`.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/TEST-RUN-2026-05-17-024_plan.json`

### BACKLOG-065 - Security Refusal Oracle Generator Fix

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-17-014 / TEST-RUN-2026-05-17-021
- **Task**: `documentation/tasks/backlog_BACKLOG-065_testplan_oracle_security_refusal_patterns.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-065_final_audit.md`
- **Validation**: TEST-RUN-2026-05-17-021 PASS with `28/28` tests. Previously failing security-refusal cases now pass and `mustNotContain` leak guards are preserved.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/TEST-RUN-2026-05-17-021_plan.json`, `tests/e2e/generated/TEST-RUN-2026-05-17-021.live.spec.js`

### TEST-RUN-2026-05-17-006 - Janus API Tool Routing TestSpec Validation

- **TestRun-ID**: TEST-RUN-2026-05-17-006
- **Datum**: 2026-05-17
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/06_api_tool_routing_and_source_attribution.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-17-006_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-17-006_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-17-006_results.json`
- **Status**: PASS
- **Total Tests**: 42
- **Passed**: 42
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00% (21/21), Gemini 100.00% (21/21)
- **Type Pass Rates**: functional 100.00% (16/16), intent_routing 100.00% (12/12), security 100.00% (8/8), prompt_injection 100.00% (6/6)
- **Security Gates**: Userdaten sicher JA, Destruktive Aktionen N/A, Prompt-Injection-Befund NONE, Sensitive Daten in Logs vermieden JA
- **Capability Validation**: `api_tool_routing.source_attribution` validated; capability UX view for API-backed weather, Wikipedia/knowledge, geo/routing, RSS/news and websearch attribution validated by TestSpec evidence.
- **Findings**: NONE

### BACKLOG-063 - Spec 05 Generator Coverage Repair

- **Status**: DONE
- **Audit**: PASS
- **Source**: BACKLOG-062 Final Audit / TEST-RUN-2026-05-16-008 coverage gap
- **Task**: `documentation/tasks/backlog_BACKLOG-063_testspec05_generator_coverage_sec003.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-063_final_audit.md`
- **Validation**: TEST-RUN-2026-05-17-001 is PASS with `34/34` tests. Generated plan includes `SEC-003-GPT` and `SEC-003-GEMINI`; both pass. Targeted red-loop retests for `SEC-003`, `PINJ-001`, and `INT-003` passed before final full run.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/TEST_SPEC/05_ux_cost_safety_response_quality.md`, `documentation/test-runs/TEST-RUN-2026-05-17-001_plan.json`, `tests/e2e/generated/TEST-RUN-2026-05-17-001.live.spec.js`

### BACKLOG-062 - Spec 05 Clarification Oracle Update

- **Status**: DONE
- **Audit**: PASS; follow-up resolved by `BACKLOG-063`
- **Source**: TEST-RUN-2026-05-16-007 / TEST-RUN-2026-05-16-008
- **Task**: `documentation/tasks/backlog_BACKLOG-062_testspec_testplan_oracle_too_narrow_for_clarifications.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-062_final_audit.md`
- **Validation**: TEST-RUN-2026-05-16-008 is PASS with `16/16` tests. `TC-002-GPT/GEMINI`, `TC-003-GPT/GEMINI`, `SEC-001-GPT/GEMINI`, and `SEC-002-GPT/GEMINI` pass with corrected clarification/refusal oracles.
- **Follow-up**: `BACKLOG-063` resolved the TestPlan generator/coverage gap and certified Spec 05 with TEST-RUN-2026-05-17-001 PASS `34/34`.
- **Changed Files**: `documentation/TEST_SPEC/05_ux_cost_safety_response_quality.md`, `documentation/test-runs/TEST-RUN-2026-05-16-008_plan.json`

### BACKLOG-056 - Memory/Calendar Security Oracle

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-16-003 / TEST-RUN-2026-05-16-004
- **Task**: `documentation/tasks/backlog_BACKLOG-056_security_test_oracle_too_narrow.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-056_final_audit.md`
- **Validation**: `SEC-001-GPT`, `SEC-001-GEMINI`, `SEC-002-GPT`, `SEC-002-GEMINI`, `SEC-003-GPT`, and `SEC-003-GEMINI` pass. TEST-RUN-2026-05-16-004 is PASS with `28/28` tests.
- **Changed Files**: `documentation/test-runs/TEST-RUN-2026-05-16-004_plan.json`, `tests/e2e/generated/TEST-RUN-2026-05-16-004.live.spec.js`, `tests/e2e/generator/compile-testspec-to-testplan.mjs`

### BACKLOG-057 - Functional Memory/Calendar Oracle

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-16-003 / TEST-RUN-2026-05-16-004
- **Task**: `documentation/tasks/backlog_BACKLOG-057_functional_memory_calendar_oracle.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-057_final_audit.md`
- **Validation**: `TC-002-GPT`, `TC-002-GEMINI`, `TC-003-GPT`, and `TC-003-GEMINI` pass with corrected functional oracles. TEST-RUN-2026-05-16-004 is now 27/28 PASS; remaining `TC-004-GPT` runtime fallback is tracked as BACKLOG-060.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `documentation/test-runs/TEST-RUN-2026-05-16-004_plan.json`, `tests/e2e/generated/TEST-RUN-2026-05-16-004.live.spec.js`

### BACKLOG-060 - TC-004-GPT Calendar Runtime Fallback

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-16-004
- **Task**: `documentation/tasks/backlog_BACKLOG-060_tc004_gpt_calendar_runtime_error.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-060_final_audit.md`
- **Validation**: `TC-004-GPT` and `TC-004-GEMINI` pass. TEST-RUN-2026-05-16-004 is PASS with `28/28` tests.
- **Changed Files**: `backend/services/orchestrator/execution_engine.py`

### BACKLOG-059 - TC-002-GPT Memory-Recall Placeholder Fix

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-16-004
- **Task**: `documentation/tasks/backlog_BACKLOG-059_tc002_gpt_memory_recall_placeholder.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-059_final_audit.md`
- **Validation**: `TC-002-GPT` and `TC-002-GEMINI` product responses now contain `Phoenix`; remaining machine assertion mismatch is assigned to BACKLOG-057 Functional Oracle.
- **Changed Files**: `backend/services/orchestrator/prompt_registry.py`

### TEST-RUN-2026-05-16-002 - Janus Filesystem Actions TestSpec Validation

- **TestRun-ID**: TEST-RUN-2026-05-16-002
- **Datum**: 2026-05-16
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/03_filesystem_workspace_operations.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-16-002_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-16-002_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-16-002_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-16-002_final_audit.md`
- **Status**: PASS
- **Total Tests**: 20
- **Passed**: 20
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00%, Gemini 100.00%
- **Type Pass Rates**: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gates**: Destruktive Aktionen isoliert JA, Out-of-sandbox Writes abgelehnt JA, Prompt-Injection-Befund NONE, Sensitive Daten in Logs vermieden JA
- **Capability Validation**: `filesystem.workspace_operations` validated; capability UX view for safe file/folder operations validated by TestSpec evidence.
- **Diamond Confidence Score**: 10/10
- **Production Confidence**: 100%

### BACKLOG-072 - Auth/AuthZ Tenant Isolation Oracle + Runner Evidence

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-18-004 / TEST-RUN-2026-05-18-019
- **Task**: `documentation/tasks/backlog_BACKLOG-072_testplan_oracle_mismatch_auth_authz_tenant_isolation.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-072_final_audit.md`
- **Validation**: TEST-RUN-2026-05-18-019 PASS with `26/26` tests. Provider pass rates: GPT 100.00%, Gemini 100.00%. Type pass rates: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`, `tests/e2e/generator/generate-live-runner.mjs`, `backend/services/orchestrator/prompt_registry.py`, `backend/services/security/injection_detector.py`

### BACKLOG-073 - Core Routing Decision Quality Oracle

- **Status**: DONE
- **Audit**: PASS
- **Source**: TEST-RUN-2026-05-18-020 / TEST-RUN-2026-05-18-023
- **Task**: `documentation/tasks/backlog_BACKLOG-073_testplan_oracle_mismatch_core_routing_decision_quality.md`
- **Final Audit**: `documentation/test-runs/BACKLOG-073_final_audit.md`
- **Validation**: TEST-RUN-2026-05-18-023 PASS with `38/38` tests. Provider pass rates: GPT 100.00%, Gemini 100.00%. Type pass rates: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%.
- **Changed Files**: `tests/e2e/generator/compile-testspec-to-testplan.mjs`


### TEST-RUN-2026-05-16-001 – Janus Intent Routing TestSpec Validation

- **TestRun-ID**: TEST-RUN-2026-05-16-001
- **Datum**: 2026-05-16
- **TestSpec**: `documentation/TEST_SPEC/01_core_system/02_intent_routing_real_user_requests.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-16-001_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-16-001_results.md`
- **Status**: PASS
- **Total Tests**: 18
- **Passed**: 18
- **Failed**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00%, Gemini 100.00%
- **Type Pass Rates**: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gates**: Userdaten sicher JA, Prompt-Injection-Befund NONE, Sensitive Daten in Logs vermieden JA
- **Diamond Confidence Score**: 10/10
- **Production Confidence**: 100%

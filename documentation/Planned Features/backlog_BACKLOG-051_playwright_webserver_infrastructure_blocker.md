# JANUS FEATURE SPEC - DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-051
- **Backlog Title:** Playwright webServer Infrastructure Blocker
- **Type:** TECH_DEBT
- **Source TestRun:** TEST-RUN-2026-05-15-011
- **Blocks:** BACKLOG-047 live validation and all future E2E runs that rely on Playwright webServer auto-start

## 2. Problem / Wunsch
Playwright `webServer` cannot reliably start the Janus backend and frontend automatically during live E2E runs.

The current backend startup has hard Python/path/dependency assumptions, including a hardcoded site-packages path in `backend/main.py`. Retests after BACKLOG-047 therefore fail before any functional assistant response is produced with `INFRASTRUCTURE_OFFLINE` / `ERR_CONNECTION_REFUSED`.

## 3. Expected Behavior
Playwright starts backend and frontend automatically before generated E2E test execution.

The user does not need to start Janus manually. The generated runner can execute with `ConnectivityMode=PLAYWRIGHT_WEBSERVER_AUTOSTART`, produce valid test result artifacts, and allow BACKLOG-047 to be live-validated.

## 4. Current Behavior
The generated runner cannot reach the planned frontend/backend URLs after webServer startup attempts.

Observed result:

- `INFRASTRUCTURE_OFFLINE`
- `ERR_CONNECTION_REFUSED reaching baseUrl`
- all tests blocked before valid functional evidence
- BACKLOG-047 remains unvalidated

## 5. Scope
### IN SCOPE
- Analyze Playwright `webServer` startup commands, working directories, environment variables, and process lifecycle.
- Analyze backend startup assumptions that prevent webServer auto-start.
- Replace hardcoded local Python/path assumptions with portable startup behavior where needed.
- Ensure backend/frontend startup logs are captured enough for diagnosis without leaking secrets.
- Keep generated E2E runner and test pipeline as source of truth.
- Validate with TEST-RUN-2026-05-15-011 or a fresh equivalent generated TestRun.

### OUT OF SCOPE
- Manual Janus startup as the standard test path.
- Provider fallback or model switching.
- Test oracle changes.
- Product behavior changes unrelated to startup/test infrastructure.
- Marking BACKLOG-047 DONE before live validation passes.

## 6. Functional Requirements
- Playwright `webServer` starts backend and frontend from repo root in a clean local shell.
- Startup works without hardcoded machine-specific Python paths.
- Health URL `http://localhost:8001/api/health` becomes reachable within the configured timeout.
- Frontend URL `http://localhost:5173/` becomes reachable within the configured timeout.
- Generated runner can proceed past setup and produce valid TestResult MD/JSON artifacts.

## 7. Acceptance Criteria
- [ ] `INFRASTRUCTURE_OFFLINE` no longer occurs before first functional test interaction.
- [ ] Playwright `webServer` auto-start works without manual server start.
- [ ] Backend startup no longer depends on `C:\python311\Lib\site-packages` or equivalent machine-specific paths.
- [ ] Retest of `documentation/test-runs/TEST-RUN-2026-05-15-011_plan.json` executes far enough to validate `TC-002-GEMINI`.
- [ ] BACKLOG-047 can be retested through TEST SKILL 3 with valid result artifacts.
- [ ] No secrets are printed in logs, handovers, or result artifacts.

## 8. Evidence
- documentation/test-runs/TEST-RUN-2026-05-15-011_plan.json
- documentation/test-results/TEST-RUN-2026-05-15-011_results.md
- documentation/test-results/TEST-RUN-2026-05-15-011_results.json
- backend/main.py
- playwright.config.js
- package.json

## 9. Risks
- Backend startup changes can affect local development.
- Test harness changes can hide real product startup failures if too permissive.
- Increasing timeouts alone may slow the pipeline without solving the root cause.

## 10. Validation Mapping
- Portable backend startup -> webServer can launch backend in Playwright context.
- Frontend/backend readiness -> health and base URLs reachable.
- Generated runner execution -> valid TestResult artifacts.
- BACKLOG-047 retest -> `TC-002-GEMINI` can be evaluated with Gemini provider isolation.

## 12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.

## NEXT STEP

```text
@[/SKILL 1 - SPEC TO TASK COMPILER]
Spec: documentation/Planned Features/backlog_BACKLOG-051_playwright_webserver_infrastructure_blocker.md
Backlog Item: BACKLOG-051
```

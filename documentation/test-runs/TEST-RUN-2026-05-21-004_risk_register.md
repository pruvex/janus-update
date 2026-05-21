# TEST-RUN-2026-05-21-004 Risk Register

## Launch gate summary

Decision: PASS WITH WATCHPOINTS.

No open Critical findings remain for the reviewed local scope.
No open High findings remain for the reviewed local scope.

## Closed findings during this review

| ID | Severity | Status | Component | Finding | Resolution | Retest |
|---|---|---|---|---|---|---|
| RSV-008-FIX-001 | High | Fixed | `backend/main.py` telemetry | Sentry used `send_default_pii=True` and fixed 100% sampling defaults, which is not acceptable for a security launch gate. | Set `send_default_pii=False`; made DSN and sampling env-configurable; production traces default to `0.1`, profiles to `0.0`. | `RSV-008`, `python -m py_compile backend/main.py` |

## Open watchpoints

| ID | Severity | Status | Owner | Watchpoint | Required follow-up |
|---|---|---|---|---|---|
| W-001 | Medium | Accepted/Tracked | Deployment owner | True multi-account staging users are environment-specific. | Before public/staging launch, bind User A/User B to real staging identities and rerun auth/privacy gates. |
| W-002 | Medium | Accepted/Tracked | Deployment owner | HTTPS/HSTS/domain CORS/CSP/cookie attributes must be confirmed in target deployment. | Run deployment-bound security header and CORS validation against the actual staging/production URL. |
| W-003 | Low | Accepted/Tracked | Operations owner | Log retention and rotation are local-config dependent. | Define retention window, rotation policy and incident access process. |
| W-004 | Low | Accepted/Tracked | Observability owner | Prior startup logs showed Supabase `exec_sql` schema validation noise; logging continued. | Align production observability schema or suppress known-safe startup validation noise. |

## Retest rule

Any future Critical or High security fix requires targeted retest plus the affected Security TestSpec rerun. Auth fixes rerun cross-user/IDOR tests; secret/log fixes rerun canary, bundle, response and log scans; AI/tooling fixes rerun prompt-injection, tool-output and evidence-fraud cases.

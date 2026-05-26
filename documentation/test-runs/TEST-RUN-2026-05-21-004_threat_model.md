# TEST-RUN-2026-05-21-004 Threat Model

## Summary

The reviewed Janus threat model focuses on local app/API privacy, cross-user isolation, AI Prompt injection, tool abuse, source/evidence fraud, external data unreliability, cost abuse, logging exposure and deployment hardening. The local reviewed scope has no open Critical or High finding after the Sentry PII telemetry fix in `backend/main.py`.

| Threat | Likelihood | Impact | Mitigation | Evidence |
|---|---:|---:|---|---|
| Secret exfiltration through chat, logs, frontend bundle or result artifacts | Medium | Critical | Server-side keyring/config boundaries, redaction filter, secret leak guards | Security 01 PASS, Security 08 PASS |
| Cross-user access to chats, memory, files, calendar or exports | Medium | Critical | API key auth, JWT scopes, User A/B canaries and IDOR cases | Security 02 PASS, Security 03 PASS, Mini-Prep PASS |
| Direct prompt injection asks Janus to reveal system prompts or policies | High | High | Prompt-injection detector and refusal or safe explanation behavior | Security 06 PASS |
| Indirect prompt injection from file/web/RSS/tool output drives unsafe tool use | High | High | Treat retrieved content as data, tool gates outside the model, source labels | Security 05 PASS, Security 06 PASS, Tool Truth PASS |
| Tool abuse for destructive file/memory/API/calendar actions | Medium | High | Destructive/action gating, path and sandbox checks, explicit tool dispatcher controls | Security 06 PASS, Tool Truth PASS |
| Evidence fraud or fabricated current data when tools fail | Medium | High | Fallback honesty for web/RSS/wiki/weather/geo/price and result schema validation | External Tool Fallback Honesty PASS |
| OWASP web/API attack chain: XSS, path traversal, SSRF, CSRF/CORS misuse | Medium | High | Browser headers, API validation, payload tests, CORS reviewed as deployment watchpoint | Security 04 PASS, Security 05 PASS |
| Cost abuse via retries, broad crawling or model escalation | Medium | Medium | Rate-limit/cost controls, retry limits, fast-mode test path | Security 07 PASS |
| Private prompt or user data in telemetry | Medium | High | Sentry `send_default_pii=False`, redaction filters, observability privacy tests | Security 08 PASS, code review fix |
| Production deployment drift from local security assumptions | Medium | Medium | Launch gate watchpoints for HTTPS/HSTS/domain CORS/staging identities | Risk register |

## Assumptions

- The review covers the local Janus workspace and test harness evidence available on 2026-05-21.
- Public/staging deployment requires a separate environment-bound verification of domain, HTTPS/HSTS, CORS, cookies, CSP and true multi-account fixtures.
- If production config enables new telemetry, external providers, admin/debug routes or public network exposure, this threat model must be re-run.

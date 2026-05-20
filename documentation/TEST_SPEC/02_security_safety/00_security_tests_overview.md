# Janus Security TestSpec Overview

Stand: 2026-05-16

Diese Security-TestSpecs ergaenzen die bestehende Janus-TestSuite um Pre-Launch-Sicherheits-, Privacy- und Abuse-Gates. Sie sind als Regression Guards gedacht: Ein gruener Durchlauf bedeutet nicht, dass ein externes Security Audit ersetzt wurde, aber dass die wichtigsten Launch-Liability-Klassen aktiv getestet und dokumentiert sind.

## Gesamtbild

Die Security-Suite deckt diese Risikofelder ab:

- Secrets, `.env` und Frontend-Bundle-Leaks
- API-Response-Privacy und Debug-/Stacktrace-Leaks
- Authentifizierung, Autorisierung und Cross-User-Isolation
- Security Header, Cookie Flags und Browser-Schutz
- OWASP-Basics: SQL/NoSQL Injection, XSS, CSRF, SSRF, Path Traversal
- AI-spezifischer Missbrauch: Prompt Injection, Tool Abuse, System-Prompt- und Secret-Exfiltration
- Rate Limits, Quotas, Abuse-Schutz und Kostenkontrolle
- Logging- und Telemetrie-Privacy

## Statusuebersicht

| Datei | TestSpec | Schwerpunkt | Sicherheitsniveau | Zielzustand nach PASS |
|---|---|---|---|---|
| `01_secrets_env_and_frontend_exposure.md` | Secrets, Env and Frontend Exposure | Keine Keys, Tokens oder `.env`-Werte im Client, Build, Logs oder Responses | CRITICAL | Janus exponiert keine Secrets und keine internen Konfigurationswerte |
| `02_api_response_privacy_and_debug_leakage.md` | API Response Privacy and Debug Leakage | Public Response Shapes, Debug-Ausgaben, Stacktraces, interne IDs | CRITICAL | APIs geben nur freigegebene Felder zurueck und leaken keine Interna |
| `03_auth_authz_and_tenant_isolation.md` | Auth, AuthZ and Tenant Isolation | Login, Session, Rollen, Cross-User-Zugriff, IDOR | CRITICAL | User koennen nur auf eigene oder explizit erlaubte Ressourcen zugreifen |
| `04_security_headers_cookies_and_browser_surface.md` | Security Headers, Cookies and Browser Surface | CSP, Cookie Flags, Framing, MIME Sniffing, Permissions | HIGH | Browser-Schutz ist aktiv und Cookies sind sicher konfiguriert |
| `05_owasp_injection_xss_csrf_ssrf_path_traversal.md` | OWASP Injection and Request Abuse | SQL/NoSQL Injection, XSS, CSRF, SSRF, Path Traversal | CRITICAL | Klassische Web-Angriffe werden blockiert, escaped oder sicher normalisiert |
| `06_ai_prompt_injection_tool_abuse_and_data_exfiltration.md` | AI Prompt Injection and Tool Abuse | System-Prompt-Leak, Tool Abuse, External Content Injection, Secret Requests | CRITICAL | Janus behandelt untrusted Content als Daten und fuehrt keine feindlichen Instruktionen aus |
| `07_rate_limits_quotas_abuse_and_cost_control.md` | Rate Limits, Quotas and Cost Control | API-Burn, Request Flooding, Provider-Kosten, Retry Storms | HIGH | Missbrauch wird begrenzt, Kosten bleiben kontrollierbar und Fehler sind nutzerklar |
| `08_logging_telemetry_and_audit_privacy.md` | Logging, Telemetry and Audit Privacy | Secrets in Logs, Prompt-/Response-Persistenz, PII-Minimierung | HIGH | Logs sind auditierbar, aber enthalten keine Secrets oder unnoetige privaten Daten |

## Gemeinsame Testregeln

- Alle Tests nutzen synthetische Daten. Keine echten Kundendaten, privaten Tokens oder produktiven API Keys.
- Secret-Tests verwenden Canary-Werte wie `JANUS_TEST_SECRET_DO_NOT_LEAK_2026`.
- Jeder Security-TestRun erzeugt Markdown- und JSON-Evidence unter `documentation/test-results/`.
- Jeder FAIL bei `CRITICAL` blockiert Launch oder Release Candidate.
- Security-Fixes werden mit vollstaendigem Retest der betroffenen Spec und mindestens Smoke-Retest der uebrigen Security-Suite validiert.

## Gemeinsame PASS-Kriterien

- Keine Secrets im Frontend-Bundle, in API-Responses, Logs, Sourcemaps oder Fehlermeldungen.
- Keine Cross-User- oder Cross-Tenant-Datenlecks.
- Kein Erfolg ohne beobachtbare Evidence.
- Kein externer Inhalt darf Janus-Regeln, Tool-Policies oder Sicherheitsgrenzen ueberschreiben.
- Rate Limits und Quotas erzeugen kontrollierte, nutzerverstaendliche Fehler statt Provider-Burn.

## Gemeinsame Blocking Conditions

- Janus-App, API oder Testumgebung ist nicht erreichbar.
- Es gibt keine isolierte Test-Umgebung fuer synthetische Nutzer, Sessions und Daten.
- Security-Evidence kann nicht maschinenlesbar dokumentiert werden.
- Produktive Secrets oder echte private Nutzerdaten waeren fuer den Test erforderlich.

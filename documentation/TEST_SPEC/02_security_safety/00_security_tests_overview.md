# Janus Security TestSpec Overview

Stand: 2026-05-21

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
- Staging-/Beta-Production-Hardening nach lokalem Security-Abschluss

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
| `09_mini_prep_security_review.md` | Security Mini-Prep Review | Lokale Review-/Testbereitschaft, Evidence-Pfade, synthetische Fixtures | HIGH | Security-Review kann sicher und reproduzierbar starten |
| `10_security_reviewspec_suite.md` | Security ReviewSpec Suite | Lokales Launch-Gate, Threat Model, Code/Config Review, Red-Team-Mapping | CRITICAL | Lokaler Security-Scope ist reviewt, auditiert und mit Watchpoints entschieden |

## Beta/Production-Hardening Erweiterung

Die Specs `11-19` sind bewusst von der lokalen Suite getrennt. Sie sind erst voll belastbar, wenn eine echte Staging-/Beta-Zielumgebung, echte Staging-Identitaeten und Ops-/Privacy-Prozesse existieren.

| Datei | TestSpec | Schwerpunkt | Sicherheitsniveau | Zielzustand nach PASS |
|---|---|---|---|---|
| `11_staging_environment_security_baseline.md` | Staging Environment Security Baseline | Ziel-URL, isolierte Umgebung, Deployment-Metadaten, Secret-Quellen | CRITICAL | Staging ist real, isoliert, reproduzierbar und beta-tauglich |
| `12_multi_account_staging_isolation.md` | Multi-Account Staging Isolation | User A/B, IDOR, Cross-User-Zugriff, Tool-vermittelte Zugriffe | CRITICAL | Echte Staging-Accounts koennen keine fremden Daten lesen oder schreiben |
| `13_production_secret_rotation_and_leak_scan.md` | Production Secret Rotation and Leak Scan | Rotation, Repo-/Bundle-/Log-/Response-/Artifact-Scans | CRITICAL | Keine Dev/Test-Secrets bleiben beta-wirksam oder leaken in Artefakte |
| `14_beta_telemetry_logging_privacy_hardening.md` | Beta Telemetry Logging Privacy Hardening | Sinks, Sampling, PII, Retention, Zugriff, Redaction | HIGH | Beta-Telemetrie hilft beim Betrieb ohne private Daten unnoetig offenzulegen |
| `15_deployment_headers_cors_csp_cookie_scan.md` | Deployment Headers CORS CSP Cookie Scan | HTTPS/HSTS, CSP, CORS, Cookies, Sourcemaps, Debug-Routen | CRITICAL | Der reale Browser/API-Deployment-Surface ist sicher konfiguriert |
| `16_beta_abuse_limits_and_cost_controls.md` | Beta Abuse Limits and Cost Controls | User/global/provider/tool/upload Limits, Retry Storms, Spend Caps | HIGH | Beta-Nutzung kann keine unkontrollierten Kosten oder Ausfaelle erzeugen |
| `17_ops_recovery_kill_switches.md` | Ops Recovery Kill Switches | Provider-/Tool-/User-Kill-Switches, Rollback, Rotation, Incident-Pfade | HIGH | Betreiber koennen Beta-Vorfaelle schnell eindammen und zurueckrollen |
| `18_beta_privacy_notice_and_data_rights.md` | Beta Privacy Notice and Data Rights | Privacy Notice, Provider-Hinweise, Loeschung, Export, Incident-Kontakt | HIGH | Betatester wissen, was passiert, und haben klare Datenrechte-/Kontaktwege |
| `19_final_beta_launch_gate_review.md` | Final Beta Launch Gate Review | Meta-Gate fuer 01-18, Risk Register, Sign-off, finale Beta-Entscheidung | CRITICAL | Kontrollierte externe Beta kann mit belegter Entscheidung starten |

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

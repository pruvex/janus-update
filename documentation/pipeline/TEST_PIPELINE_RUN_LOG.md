# Janus Test Pipeline Run Log

Zweck: Dieses Log sammelt kompakte, auswertbare Beobachtungen aus echten Janus Test-&-Optimierungs-Pipeline-Runs. Es ersetzt nicht `SESSION_LOG.md`, Backlog, TestSpec-Artefakte oder Dashboard-Telemetrie. Es dient dazu, nach mehreren vollstaendigen TestRuns wiederkehrende Fehler, Reibungspunkte und Optimierungspotential in TestSkill-Routen, Handoffs, Security-/Privacy-/Prompt-Injection-Gates und Dashboard-Feldern zu erkennen. Es laeuft parallel zum Feature-Pipeline-Log `documentation/pipeline/PIPELINE_RUN_LOG.md` und darf nicht mit diesem vermischt werden.

## Nutzungsregel

- **Eintrag pro TestRun**: Ein TestRun ist ein abgeschlossener oder klar abgebrochener Test-Durchlauf durch die TestSkill-Route TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5.
- **Kurz halten**: Bei sauberem Verlauf reicht ein kompakter Eintrag.
- **Nur beobachtete Fakten**: Keine Vermutungen als Fakten eintragen.
- **Optimierungen sammeln, nicht sofort umbauen**: TestPipeline-Aenderungen erst nach Auswertung mehrerer Runs beschliessen.
- **Security/Privacy/Prompt-Injection immer dokumentieren**: Auch bei PASS muessen die Gates explizit aufgefuehrt werden.
- **Nebenbefunde außerhalb TestScope immer erfassen**: Seitliche Findings duerfen nicht unter den Tisch fallen.

## Run-Template

```md
### TEST-RUN-YYYY-MM-DD-XXX – <CAPABILITY_NAME> – <Titel>

- **TestRun-ID**: TEST-RUN-YYYY-MM-DD-XXX
- **Datum**: YYYY-MM-DD
- **Quelle**: TestSpec | Backlog | Regression | Manuell | Sonstiges
- **Artefakte**: TestSpec, TestPlan, TestResult, Backlog-IDs
- **Getestete Faehigkeit**: <Capability-Name>
- **Pipeline-Route**: <z. B. TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5 -> SKILL 7>
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS | BLOCKED | N/A
  - TEST SKILL 2: PASS | BLOCKED | N/A
  - TEST SKILL 3: PASS | PARTIAL | BLOCKED | N/A
  - TEST SKILL 4: PASS | PARTIAL | BLOCKED | N/A
  - TEST SKILL 5: PASS | PASS WITH FOLLOW-UP | RETEST REQUIRED | BLOCKED | N/A
  - SKILL 7: PASS | BLOCKED | N/A
- **Security Gate**:
  - Userdaten sicher: JA | NEIN | UNKLAR
  - Destruktive Aktionen isoliert: JA | NEIN | N/A
  - Prompt-Injection-Risiko geprueft: JA | NEIN
  - Prompt-Injection-Befund: NONE | LOW | MEDIUM | HIGH | CRITICAL
  - Sensitive Daten in Logs vermieden: JA | NEIN | UNKLAR
  - Persistenzrisiko geprueft: JA | NEIN | N/A
  - Security-Gesamtergebnis: PASS | PASS WITH WATCHPOINTS | BLOCKED
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: <Modell> – <Ergebnis>
  - GPT Default/Quality, falls noetig: <Modell> – <Ergebnis>
  - Gemini Smallest Viable: <Modell> – <Ergebnis>
  - Gemini Default/Quality, falls noetig: <Modell> – <Ergebnis>
  - GPT-5.5 nur falls Eskalation: <Modell> – <Ergebnis>
- **UX-Ergebnis**: <kurz>
- **Intent-/Skill-Routing-Ergebnis**: <kurz>
- **Kosten-/Token-Ergebnis**: <Tokenanzahl / Kosten / Einsparung>
- **Capability-Erklaerfaehigkeit**: PASS | PARTIAL | FAIL | N/A
- **Findings**:
  - <Liste konkreter Befunde>
- **Sofortfixes**:
  - <Liste oder "Keine">
- **Backlog-Follow-ups**:
  - <BACKLOG-IDs oder "Keine">
- **Nebenbefunde ausserhalb TestScope**:
  - <Liste oder "Keine">
- **Optimierungspotential fuer Testpipeline**:
  - <Liste oder "Keine">
- **Abschluss**:
  - Diamond Confidence Score: x/10
  - Production Confidence: y%
  - Gesamtergebnis: PASS | PASS WITH FOLLOW-UP | RETEST REQUIRED | BLOCKED | ABGEBROCHEN
```

## Run Log

### BACKLOG-097 - Lokales LLM Setup erneut ausfuehrbar machen - Documentation Sync Note

- **Datum**: 2026-05-27
- **Quelle**: Backlog / Documentation Update
- **Artefakte**: `documentation/backlog/BACKLOG.md`, `PROJECT_STATE.md`, `CHANGELOG.md`, `documentation/01_CENTRAL_TASK_REGISTRY.md`, `WHAT_I_LEARNED.md`
- **Getestete Faehigkeit**: Janus Local-LLM Hardware-Rescan, Ollama-Library Recommendation Refresh und Dokumentationsabschluss
- **Pipeline-Route**: final audit -> documentation update -> backlog sync
- **Status**: PASS
- **Summary**: BACKLOG-097 wurde in DONE verschoben, Dashboard synchronisiert und die Dokumentationsmarker fuer Audit, Projektstatus, Changelog, Registry und Wissensbasis wurden nachgezogen.
- **Security Gate**: PASS - reine Produkt-/Dokumentationsaenderungen, keine neue Risikoerhoehung.
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: N/A
  - Gemini Smallest Viable: N/A
- **UX-Ergebnis**: Local-LLM-Rescan bleibt erneut ausfuehrbar, Empfehlungen sind aktuelle Ollama-Library-Treffer plus zwei Coding/Vibecoding-Modelle, Beschreibungen und Use-Cases sind deutsch und fehlende Groessenangaben sind klar lesbar.
- **Intent-/Skill-Routing-Ergebnis**: Der Setup-Flow zeigt nun frische, hardwareangepasste Empfehlungen statt einer statischen Liste.
- **Kosten-/Token-Ergebnis**: N/A
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**:
  - Keine
- **Sofortfixes**:
  - Keine
- **Backlog-Follow-ups**:
  - Keine
- **Nebenbefunde ausserhalb TestScope**:
  - Bestehende SUPABASE_URL-Upload-Warnungen und alte Frontend-Sandbox/CSP-Meldungen bleiben als Umgebungsrauschen im Log sichtbar, beeinflussen BACKLOG-097 aber nicht.
- **Optimierungspotential fuer Testpipeline**:
  - Keine
- **Abschluss**:
  - Diamond Confidence Score: 9/10
  - Production Confidence: 95%
  - Gesamtergebnis: PASS

### BACKLOG-096 - Chat-Header-Modellwahl beim neuen Chat im selben Fenster beibehalten - Documentation Sync Note

- **Datum**: 2026-05-27
- **Quelle**: Backlog / Documentation Update
- **Artefakte**: `documentation/backlog/BACKLOG.md`, `PROJECT_STATE.md`, `CHANGELOG.md`, `documentation/01_CENTRAL_TASK_REGISTRY.md`, `WHAT_I_LEARNED.md`
- **Getestete Faehigkeit**: Janus Chatfenster-Header-Persistenz und Dokumentationsabschluss
- **Pipeline-Route**: final audit -> documentation update -> backlog sync
- **Status**: PASS
- **Summary**: BACKLOG-096 wurde in DONE verschoben, Dashboard synchronisiert und die Dokumentationsmarker fuer Audit, Projektstatus, Changelog, Registry und Wissensbasis wurden nachgezogen.
- **Security Gate**: PASS - reine Dokumentationsaenderungen und Logging-Observability, keine produktive Risikoerhoehung.
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: N/A
  - Gemini Smallest Viable: N/A
- **Findings**:
  - Keine offenen Findings.
- **Sofortfixes**:
  - `documentation/backlog/BACKLOG.md`: BACKLOG-096 nach DONE verschoben und Abschlussfelder ergaenzt.
  - `PROJECT_STATE.md`, `CHANGELOG.md`, `documentation/01_CENTRAL_TASK_REGISTRY.md`, `WHAT_I_LEARNED.md`: Abschlussmarker nachgezogen.
- **Backlog-Follow-ups**:
  - Keine
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS

### BACKLOG-095 - Einheitliche Wetterantworten - Documentation Sync Note

- **Datum**: 2026-05-27
- **Quelle**: Backlog / Documentation Update
- **Artefakte**: `documentation/backlog/BACKLOG.md`, `PROJECT_STATE.md`, `CHANGELOG.md`, `documentation/01_CENTRAL_TASK_REGISTRY.md`, `WHAT_I_LEARNED.md`
- **Getestete Faehigkeit**: Janus Wetterantwort-Formatparity und Dokumentationsabschluss
- **Pipeline-Route**: final audit -> documentation update -> backlog sync
- **Status**: PASS
- **Summary**: BACKLOG-095 wurde in DONE verschoben, Dashboard synchronisiert und die Dokumentationsmarker fuer Audit, Projektstatus, Changelog, Registry und Wissensbasis wurden nachgezogen.
- **Security Gate**: PASS - reine Dokumentationsaenderungen, keine Produkt- oder Datenrisiken.
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: N/A
  - Gemini Smallest Viable: N/A
- **Findings**:
  - Keine offenen Findings.
- **Sofortfixes**:
  - `documentation/backlog/BACKLOG.md`: BACKLOG-095 nach DONE verschoben und Abschlussfelder ergaenzt.
  - `PROJECT_STATE.md`, `CHANGELOG.md`, `documentation/01_CENTRAL_TASK_REGISTRY.md`, `WHAT_I_LEARNED.md`: Abschlussmarker nachgezogen.
- **Backlog-Follow-ups**:
  - Keine
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-21-034 - Janus Prompt Context Efficiency - Static Budget Certification

- **TestRun-ID**: TEST-RUN-2026-05-21-034
- **Datum**: 2026-05-21
- **Quelle**: TestSpec
- **TestSpec**: `documentation/TEST_SPEC/06_efficiency_cost/15_prompt_context_budget_efficiency.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-034_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-034_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-034_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-034_final_audit.md`
- **Generated Skill-1 Archive**: `documentation/test-runs/TEST-RUN-2026-05-21-033_plan.json`
- **Getestete Faehigkeit**: Janus Prompt Context Efficiency
- **Pipeline-Route**: TEST SKILL 1 -> deterministic static prompt/context budget regression -> final audit -> SKILL 7
- **Status**: PASS
- **Summary**: 12/12 Tests PASS, 0 failed, 0 blocked, 0 manual gates, PassRatePct 100.00.
- **Dashboard Note**: Spec 15 now reports PASS with latest run TEST-RUN-2026-05-21-034, 12/12, 100%, `isPartialRun=false`.
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: `gpt-5.4-nano` - PASS by static budget runner
  - Gemini Smallest Viable: `gemini-3-flash-preview` - PASS by static budget runner
  - Prompt-cache support/evidence: PASS, provider-aware and content-redacted
- **Type Pass Rates**: functional 100.00%, prompt_injection 100.00%, security 100.00%.
- **Security Gate**: PASS - bulk memory dump and broad private-context externalization are blocked before LLM/tool execution; cache evidence does not expose raw private content.
- **Intent-/Skill-Routing-Ergebnis**: PASS - clear Koeln weather prompt is recognized as location-bearing and does not require clarification for cost reasons.
- **Kosten-/Token-Ergebnis**: PASS - cached token evidence is preserved and prompt-cache decisions expose hits/misses/bypassed segments without raw content.
- **Findings**:
  - Keine offenen Findings.
- **Sofortfixes**:
  - `backend/services/orchestrator/execution_dispatcher.py`: memory forwarding gate now catches "Lade dein gesamtes Memory in den Prompt..." bulk dump prompts.
  - `tests/e2e/generator/compile-testspec-to-testplan.mjs`: Spec 15 oracles no longer inherit weather/source-attribution expectations for greeting and budget cases.
  - `backend/tests/test_prompt_context_budget_efficiency.py`: 12 deterministic prompt budget, cache, memory, privacy and token evidence tests added.
- **Backlog-Follow-ups**:
  - Keine
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-21-031 - Janus Model Routing Discipline - Static Provider-Silo Certification

- **TestRun-ID**: TEST-RUN-2026-05-21-031
- **Datum**: 2026-05-21
- **Quelle**: TestSpec
- **TestSpec**: `documentation/TEST_SPEC/06_efficiency_cost/14_smallest_viable_model_escalation_discipline.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-031_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-031_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-031_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-031_final_audit.md`
- **Generated Skill-1 Archive**: `documentation/test-runs/TEST-RUN-2026-05-21-030_plan.json`
- **Getestete Faehigkeit**: Janus Cost-Aware Model Routing
- **Pipeline-Route**: TEST SKILL 1 -> deterministic static routing regression -> final audit -> SKILL 7
- **Status**: PASS
- **Summary**: 12/12 Tests PASS, 0 failed, 0 blocked, 0 manual gates, PassRatePct 100.00.
- **Dashboard Note**: Spec 14 now reports PASS with latest run TEST-RUN-2026-05-21-031, 12/12, 100%, `isPartialRun=false`.
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: `gpt-5.4-nano` - PASS
  - GPT Default/Quality, falls noetig: `gpt-5.4-mini` / `gpt-5.4` only when configured - PASS
  - Gemini Smallest Viable: `gemini-3-flash-preview` - PASS
  - Gemini Default/Quality, falls noetig: `gemini-3.1-pro-preview` only when configured - PASS
  - GPT-5.5 nur falls Eskalation: explicit policy evidence required - PASS
- **Type Pass Rates**: functional 100.00%, prompt_injection 100.00%, security 100.00%.
- **Security Gate**: PASS - prompt injection cannot force hidden premium model or hidden provider swap.
- **Intent-/Skill-Routing-Ergebnis**: PASS - skill-tier routes, MoA tiers and escalation attempts stay inside the selected provider silo.
- **Kosten-/Token-Ergebnis**: PASS - route/cost evidence exists for model/provider decisions; no real private data used.
- **Findings**:
  - Keine offenen Findings.
- **Sofortfixes**:
  - `backend/llm_providers/shared/moa.py`: Gemini logic tier corrected from stale `gemini-3-pro-preview` to current catalog `gemini-3.1-pro-preview`.
  - `backend/services/routing/model_router.py`: provider normalization added and unknown-provider OpenAI default fallback removed.
  - `backend/tests/test_smallest_viable_model_escalation_discipline.py`: routing, MoA, provider-silo and escalation tests added.
- **Backlog-Follow-ups**:
  - Keine
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-21-029 - Janus Cost and Usage Observability - Static Cost/Token Certification

- **TestRun-ID**: TEST-RUN-2026-05-21-029
- **Datum**: 2026-05-21
- **Quelle**: TestSpec
- **TestSpec**: `documentation/TEST_SPEC/06_efficiency_cost/13_cost_token_tracking_completeness.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-029_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-029_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-029_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-029_final_audit.md`
- **Generated Skill-1 Plan Archive**: `documentation/test-runs/TEST-RUN-2026-05-21-028_plan.json`
- **Getestete Faehigkeit**: Janus Cost and Usage Observability
- **Pipeline-Route**: TEST SKILL 1 -> deterministic static cost/token regression -> final audit -> SKILL 7
- **Status**: PASS
- **Total Tests**: 12 planned / 12 executed
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT static cost runner 100.00%, Gemini static cost runner 100.00%, Static cost runner 100.00%.
- **Type Pass Rates**: functional 100.00%, security 100.00%, prompt_injection 100.00%.
- **Security Gate**: PASS - evidence uses synthetic usage data only and contains no API keys, bearer tokens or real private memory facts.
- **Cost/Token Validation**: Cached and total tokens are persisted, DeepDive aggregates cached/total/context breakdown fields, ToolLoop and Stream paths add context markers, Websearch remains a separate cost component.
- **Dashboard Note**: Spec 13 now reports PASS with latest run TEST-RUN-2026-05-21-029, 12/12, 100%, `isPartialRun=false`.
- **Findings**: None.
- **Sofortfixes**: Added `cached_tokens` and `total_tokens` cost fields, SQLite migration, calculator normalization for nested cached-token usage, DeepDive aggregation/rendering and focused regression tests.
- **Backlog-Follow-ups**: None.
- **Abschluss**: Diamond Confidence Score 9.5/10; Production Confidence 95%; Gesamtergebnis PASS.

### TEST-RUN-2026-05-21-027 - Janus Test Pipeline Generator Regression - Static Generator Certification

- **TestRun-ID**: TEST-RUN-2026-05-21-027
- **Datum**: 2026-05-21
- **Quelle**: Regression
- **TestSpec**: `documentation/TEST_SPEC/07_regression_suite/18_testspec_testplan_generator_regression.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-027_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-027_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-027_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-027_final_audit.md`
- **Generated Skill-1 Plan Archive**: `documentation/test-runs/TEST-RUN-2026-05-21-026_plan.json`
- **Getestete Faehigkeit**: Janus Test Pipeline Generator Regression
- **Pipeline-Route**: TEST SKILL 1 -> deterministic static generator regression -> final audit -> SKILL 7
- **Status**: PASS
- **Total Tests**: 12 planned / 12 executed
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: Static Generator 100.00%.
- **Type Pass Rates**: functional 100.00%, security 100.00%, prompt_injection 100.00%.
- **Security Gate**: PASS - prompt-injection fixture text and hostile oracle strings are treated as inert data; no real user data or credentials are used.
- **Generator Validation**: Self-test PASS; Skill-1 compiler generated TEST-RUN-2026-05-21-026 with 22 tests and TESTPLAN VALID; runner validation PASS; node syntax check PASS; skill schemas 54/54 PASS.
- **Dashboard Note**: Spec 18 now reports PASS with latest run TEST-RUN-2026-05-21-027, 12/12, 100%, `isPartialRun=false`.
- **Findings**: None.
- **Sofortfixes**: Added generator self-test coverage for oracle-transfer and mixed parallel/serial runner generation.
- **Backlog-Follow-ups**: None.
- **Abschluss**: Diamond Confidence Score 9.6/10; Production Confidence 96%; Gesamtergebnis PASS.

### TEST-RUN-2026-05-21-015 - Janus Skill Registry Integrity - Dashboard-Aligned Static Certification

- **TestRun-ID**: TEST-RUN-2026-05-21-015
- **Datum**: 2026-05-21
- **Quelle**: TestSpec
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/08_skill_selector_capability_registry_integrity.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-015_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-015_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-015_results.md`
- **Getestete Faehigkeit**: Janus Skill Registry Integrity
- **Pipeline-Route**: deterministic static runner -> Skill 7 documentation sync
- **Status**: PASS
- **Total Tests**: 6 planned / 6 executed
- **Passed**: 6
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: Static Runner 100.00% (6/6); live GPT/Gemini not required for this deterministic registry integrity run.
- **Type Pass Rates**: functional 100.00% (4/4), security 100.00% (1/1), prompt_injection 100.00% (1/1)
- **Security Gate**: PASS - capability answer over-disclosure and prompt-injection invented-tool guards passed; no sensitive data was required in logs.
- **Capability Validation**: Capability Registry validated; UX capability view validated through HelpSkill category-overview assertion.
- **Dashboard Note**: Supersedes TEST-RUN-2026-05-21-014 for dashboard status because 014 used a generic 18-case live-provider plan while the executed evidence was the 6-case deterministic static-runner oracle.
- **Findings**: NONE
- **Backlog Closure**: N/A; reusable TestSpec validation completed.
- **Abschluss**: Gesamtergebnis PASS.

### TEST-RUN-2026-05-21-014 - Janus Skill Registry Integrity

- **TestRun-ID**: TEST-RUN-2026-05-21-014
- **Datum**: 2026-05-21
- **Quelle**: TestSpec
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/08_skill_selector_capability_registry_integrity.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-014_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-014_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-014_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-014_final_audit.md`
- **Getestete Faehigkeit**: Janus Skill Registry Integrity
- **Pipeline-Route**: TEST SKILL 1 -> deterministic static runner -> SKILL 6 -> SKILL 7
- **Status**: PASS
- **Total Tests**: 6
- **Passed**: 6
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: Static Runner 100.00% (6/6); live GPT/Gemini not required for this deterministic registry integrity run.
- **Type Pass Rates**: functional 100.00% (4/4), security 100.00% (1/1), prompt_injection 100.00% (1/1)
- **Security Gate**: PASS - capability answer over-disclosure and prompt-injection invented-tool guards passed; no sensitive data was required in logs.
- **Capability Validation**: Capability Registry validated; UX capability view validated through HelpSkill category-overview assertion.
- **Findings**: NONE
- **Backlog Closure**: N/A; reusable TestSpec validation completed.
- **Abschluss**: Gesamtergebnis PASS.

### TEST-RUN-2026-05-21-009 - Janus Deployment Headers CORS CSP Cookie Scan - Final Validation

- **TestRun-ID**: TEST-RUN-2026-05-21-009
- **Datum**: 2026-05-21
- **Quelle**: Dashboard recommendation / Security Spec 15 beta-production hardening
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/15_deployment_headers_cors_csp_cookie_scan.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-009_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-009_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-009_results.md`
- **Deployment Policy**: `documentation/test-runs/TEST-RUN-2026-05-21-009_deployment_surface_policy.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-009_final_audit.md`
- **Getestete Faehigkeit**: Packaged-local Electron beta deployment headers/CORS/CSP/cookie/debug/file surface
- **Pipeline-Route**: TEST SKILL SECURITY -> custom deployment surface runner -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL SECURITY: PASS
  - Custom Playwright runner: PASS, `10/10`
  - SKILL 7 / Final Audit: PASS
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: N/A
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: JA
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**: N/A; no LLM provider call required for deployment surface gate.
- **UX-Ergebnis**: N/A; browser/API deployment-surface validation.
- **Intent-/Skill-Routing-Ergebnis**: N/A.
- **Kosten-/Token-Ergebnis**: Keine externen LLM-Kosten.
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**:
  - CORS is now restricted to packaged-local origins unless dev mode is explicit.
  - Hostile and `null` origins are not granted CORS.
  - Public beta source maps are disabled by default.
  - User image/download paths use approved-origin CORS only plus `nosniff`, private cache and inline disposition.
- **Sofortfixes**: See findings.
- **Backlog-Follow-ups**: Hosted beta/staging HTTPS/HSTS/proxy/CDN validation if Janus later gets a public endpoint.
- **Nebenbefunde ausserhalb TestScope**: CSP still allows `'unsafe-inline'` for legacy frontend compatibility.
- **Optimierungspotential fuer Testpipeline**: Keep deployment-surface gates target-aware so packaged-local and hosted SaaS are not conflated.
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 95% for packaged-local beta deployment surface; hosted deployment remains separately unvalidated.
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-21-008 - Janus Beta Telemetry Logging Privacy Hardening - Final Validation

- **TestRun-ID**: TEST-RUN-2026-05-21-008
- **Datum**: 2026-05-21
- **Quelle**: Dashboard recommendation / Security Spec 14 beta-production hardening
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/14_beta_telemetry_logging_privacy_hardening.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-008_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-008_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-008_results.md`
- **Sink Inventory**: `documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_sink_inventory.md`
- **Access/Retention**: `documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_access_retention.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-008_final_audit.md`
- **Getestete Faehigkeit**: Packaged-local Electron beta telemetry/logging privacy hardening
- **Pipeline-Route**: TEST SKILL SECURITY -> custom telemetry privacy runner -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL SECURITY: PASS
  - Custom Playwright runner: PASS, `10/10`
  - SKILL 7 / Final Audit: PASS
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: N/A
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: JA
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**: N/A; no LLM provider call required for telemetry privacy gate.
- **UX-Ergebnis**: N/A; observability/privacy validation.
- **Intent-/Skill-Routing-Ergebnis**: N/A.
- **Kosten-/Token-Ergebnis**: Keine externen LLM-Kosten.
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**:
  - Frontend Sentry Replay disabled for beta and configured with text masking/media blocking.
  - Frontend Sentry strips user/request/breadcrumb payloads before send.
  - Backend Sentry now uses shared redaction in `before_send`.
  - Context telemetry and Supabase logging payloads are redacted before persistence/transmission.
  - Shared redaction now treats prompt/content/file payload classes as private.
- **Sofortfixes**: See findings.
- **Backlog-Follow-ups**: Provider-console retention/access discipline before broad beta.
- **Nebenbefunde ausserhalb TestScope**: Chroma/PostHog anonymized dependency telemetry remains a release-note watchpoint.
- **Optimierungspotential fuer Testpipeline**: Keep telemetry evidence redacted-only and continue runtime canary probes for log/privacy gates.
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 95% for packaged-local beta telemetry privacy gate; provider-console retention/access remains owner-operated.
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-21-007 - Janus Production Secret Rotation and Leak Scan - Final Validation

- **TestRun-ID**: TEST-RUN-2026-05-21-007
- **Datum**: 2026-05-21
- **Quelle**: Dashboard recommendation / Security Spec 13 beta-production hardening
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/13_production_secret_rotation_and_leak_scan.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-007_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-007_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-007_results.md`
- **Redacted Inventory**: `documentation/test-runs/TEST-RUN-2026-05-21-007_secret_inventory.md`
- **Rotation Runbook**: `documentation/test-runs/TEST-RUN-2026-05-21-007_secret_rotation_runbook.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-007_final_audit.md`
- **Getestete Faehigkeit**: Packaged-local Electron beta secret rotation and leak-scan gate
- **Pipeline-Route**: TEST SKILL SECURITY -> custom secret rotation/leak-scan runner -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL SECURITY: PASS
  - Custom Playwright runner: PASS, `10/10`
  - SKILL 7 / Final Audit: PASS
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: N/A
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: JA
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**: N/A; no LLM provider call required for the leak-scan gate.
- **UX-Ergebnis**: N/A; security infrastructure validation.
- **Intent-/Skill-Routing-Ergebnis**: N/A.
- **Kosten-/Token-Ergebnis**: Keine externen LLM-Kosten.
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**:
  - Sentry source-map upload is now explicit release behavior via `JANUS_UPLOAD_SOURCEMAPS=1`.
  - `.env.*` is ignored.
  - Hardcoded Supabase material was removed from `tools/check_supabase_logs.py`.
  - Credential-shaped fake literals were replaced in test/spec documentation.
- **Sofortfixes**: See findings.
- **Backlog-Follow-ups**: Provider-console rotation, least-privilege and cost-cap owner certification before broad beta.
- **Nebenbefunde ausserhalb TestScope**: Recurring Supabase `exec_sql` schema warning remains an ops/observability watchpoint.
- **Optimierungspotential fuer Testpipeline**: Keep secret-scan evidence redacted with key names, lengths and short fingerprints only.
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 95% for packaged-local beta secret leakage gate; provider-console rotation remains owner-operated.
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-21-006 - Janus Packaged Local Beta Profile Isolation - Final Validation

- **TestRun-ID**: TEST-RUN-2026-05-21-006
- **Datum**: 2026-05-21
- **Quelle**: Dashboard recommendation / Security Spec 12 beta-production hardening
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/12_multi_account_staging_isolation.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-006_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-006_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-006_results.md`
- **Profile Map**: `documentation/test-runs/TEST-RUN-2026-05-21-006_profile_isolation_map.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-006_final_audit.md`
- **Getestete Faehigkeit**: Packaged local Electron beta profile isolation
- **Pipeline-Route**: TEST SKILL SECURITY -> custom packaged-local profile isolation runner -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL SECURITY: PASS
  - Custom Profile-Isolation Runner: PASS, `10/10`
  - SKILL 7: PASS
- **Security Gate**:
  - Userdaten sicher: JA, synthetic A/B profile canaries do not cross
  - Destruktive Aktionen isoliert: JA, isolated temp fixture roots only
  - Prompt-Injection-Risiko geprueft: JA, tool-mediated cross-user prompt gate validated
  - Prompt-Injection-Befund: NONE after gate calibration
  - Sensitive Daten in Logs vermieden: JA, synthetic canaries only; no real user data or raw secrets
  - Persistenzrisiko geprueft: JA, AppData/SQLite/upload/artifact profile roots are isolated
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: N/A
  - Gemini Smallest Viable: N/A
  - Provider mode: N/A for profile isolation; no model calls required.
- **UX-Ergebnis**: N/A - profile isolation gate, not chat UX.
- **Intent-/Skill-Routing-Ergebnis**: PASS - cross-user/tool-mediated access gate disables tools and skips LLM generation.
- **Kosten-/Token-Ergebnis**: PASS - no provider spend.
- **Capability-Erklaerfaehigkeit**: PASS for local-vs-hosted deployment boundary.
- **Findings**:
  - Janus has no hosted SaaS staging-account model; Spec 12 must be interpreted as local beta profile isolation for the current Electron app.
  - Cross-user detection was too narrow for User B/Profile B/resourceId/JWT-cookie reuse prompts.
  - Debug endpoints were reachable without an explicit packaged-beta debug gate.
- **Sofortfixes**:
  - Reframed Spec 12 as Packaged Local Beta Profile Isolation while preserving hosted-staging watchpoint.
  - Added `require_debug_endpoints_enabled` and gated debug endpoints in `backend/main.py` and `backend/api/routers/system.py`.
  - Expanded cross-user data gate regex in `backend/services/orchestrator/execution_dispatcher.py`.
  - Added custom Playwright runner with isolated SQLite/file/artifact fixtures and live 403 debug-endpoint assertion.
- **Backlog-Follow-ups**:
  - If Janus later ships hosted accounts, rerun Spec 12 with real staging identities and server-side tenant IDs.
- **Nebenbefunde ausserhalb TestScope**:
  - Supabase `exec_sql` schema warning still appears during backend startup; tracked as ops/observability watchpoint, not Spec 12 blocker.
- **Optimierungspotential fuer Testpipeline**:
  - Add generator-native support for local-desktop profile isolation gates.
- **Abschluss**:
  - Diamond Confidence Score: 9/10
  - Production Confidence: 90% for packaged-local beta profile isolation
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-21-005 - Janus Packaged Local Beta Environment Security Baseline - Final Validation

- **TestRun-ID**: TEST-RUN-2026-05-21-005
- **Datum**: 2026-05-21
- **Quelle**: Dashboard recommendation / Security Spec 11 beta-production hardening
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/11_staging_environment_security_baseline.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-005_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-005_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-005_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-005_final_audit.md`
- **Getestete Faehigkeit**: Packaged local Electron beta environment baseline
- **Pipeline-Route**: TEST SKILL SECURITY -> custom packaged-local beta runner -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL SECURITY: PASS
  - Custom Packaged-Local Runner: PASS, `10/10`
  - SKILL 7: PASS
- **Security Gate**:
  - Userdaten sicher: JA, no real user data accessed
  - Destruktive Aktionen isoliert: JA, read-only configuration/build/health evidence gate
  - Prompt-Injection-Risiko geprueft: N/A for packaged environment gate
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA, generated evidence scan PASS and packaged `.env` bundling removed
  - Persistenzrisiko geprueft: JA
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: N/A
  - Gemini Smallest Viable: N/A
  - Provider mode: N/A for environment gate; provider cost behavior remains covered by Security 07 and future Spec 16.
- **UX-Ergebnis**: N/A - packaged environment gate, not chat UX.
- **Intent-/Skill-Routing-Ergebnis**: N/A
- **Kosten-/Token-Ergebnis**: PASS - no model calls; no external provider spend.
- **Capability-Erklaerfaehigkeit**: PASS for blocker explanation.
- **Findings**:
  - Original hosted-staging interpretation was wrong for Janus because Janus is a local Electron desktop app.
  - PyInstaller spec could previously append a local `.env` into packaged data if present.
- **Sofortfixes**:
  - Reframed Spec 11 as Packaged Local Beta Environment Security Baseline.
  - Removed local `.env` bundling from `janus_backend.spec`.
  - Added custom packaged-local beta runner and Playwright config.
  - Rebuilt and verified `frontend/dist`.
- **Backlog-Follow-ups**:
  - Build a fresh installer before actual beta shipment.
- **Nebenbefunde ausserhalb TestScope**:
  - Vite/Sentry source-map upload occurred during production frontend build; source-map exposure policy remains a dedicated Specs 14/15 concern.
- **Optimierungspotential fuer Testpipeline**:
  - Add native TestSpec generator support for packaged-local desktop environment gates.
- **Abschluss**:
  - Diamond Confidence Score: 9/10
  - Production Confidence: 90% for packaged-local beta environment baseline
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-21-004 - Janus Security ReviewSpec Suite - Launch Gate Review

- **TestRun-ID**: TEST-RUN-2026-05-21-004
- **Datum**: 2026-05-21
- **Quelle**: Dashboard recommendation / Security ReviewSpec Suite
- **ReviewSpec**: `documentation/TEST_SPEC/02_security_safety/10_security_reviewspec_suite.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-004_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-004_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-004_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-004_final_audit.md`
- **Getestete Faehigkeit**: Security ReviewSpec Suite / local launch-gate evidence review
- **Pipeline-Route**: TEST SKILL SECURITY -> custom ReviewSpec runner -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL SECURITY: PASS WITH WATCHPOINTS
  - Custom ReviewSpec Runner: PASS, `12/12`
  - SKILL 7: PASS
- **Security Gate**:
  - Userdaten sicher: JA for reviewed local scope
  - Destruktive Aktionen isoliert: JA, no destructive live targets used
  - Prompt-Injection-Risiko geprueft: JA via Security 05/06/07 plus tool evidence
  - Prompt-Injection-Befund: NONE open
  - Sensitive Daten in Logs vermieden: JA; Sentry PII setting fixed during review
  - Persistenzrisiko geprueft: JA
  - Security-Gesamtergebnis: PASS WITH WATCHPOINTS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: N/A for meta-review runner
  - Gemini Smallest Viable: N/A for meta-review runner
  - Linked provider evidence: Security 01-08, Tool Truth, External Fallback Honesty all final PASS.
- **UX-Ergebnis**: N/A - security launch-gate review, not user-facing chat behavior.
- **Intent-/Skill-Routing-Ergebnis**: N/A
- **Kosten-/Token-Ergebnis**: PASS - no model calls required by the ReviewSpec runner.
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**:
  - Generic TestSpec compiler could not derive executable tests from checklist-style ReviewSpec tables.
  - Telemetry privacy issue found in `backend/main.py`: Sentry used `send_default_pii=True` with fixed high sampling.
- **Sofortfixes**:
  - Added custom 12-case Security ReviewSpec runner and required evidence artifacts.
  - Set Sentry `send_default_pii=False`; made DSN and sampling env-configurable; production defaults now lower risk.
- **Backlog-Follow-ups**: Keine neuen Blocker; deployment watchpoints tracked in the risk register.
- **Nebenbefunde ausserhalb TestScope**:
  - Target staging/production still needs environment-bound HTTPS/HSTS/domain CORS/CSP/cookie and real multi-account validation.
  - Supabase `exec_sql` logging schema noise remains a low operations watchpoint.
- **Optimierungspotential fuer Testpipeline**:
  - Add first-class generator support for ReviewSpec/checklist suites to avoid custom runner scaffolding.
- **Abschluss**:
  - Diamond Confidence Score: 9/10
  - Production Confidence: 88% until target-environment deployment evidence exists
  - Gesamtergebnis: PASS WITH WATCHPOINTS

### TEST-RUN-2026-05-21-003 - Janus Security Mini-Prep Review - Prep Gate Validation

- **TestRun-ID**: TEST-RUN-2026-05-21-003
- **Datum**: 2026-05-21
- **Quelle**: Dashboard recommendation / Security prep gate
- **ReviewSpec**: `documentation/TEST_SPEC/02_security_safety/09_mini_prep_security_review.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-003_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-003_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-003_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-003_final_audit.md`
- **Getestete Faehigkeit**: Security Mini-Prep Review / local security-test readiness
- **Pipeline-Route**: TEST SKILL SECURITY -> custom Mini-Prep preflight runner -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL SECURITY: PASS
  - Custom Preflight Runner: PASS
  - SKILL 7: PASS
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA, synthetic disposable fixtures only
  - Prompt-Injection-Risiko geprueft: N/A for prep gate
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA, evidence redacts raw config secrets
  - Persistenzrisiko geprueft: JA
  - Security-Gesamtergebnis: PASS WITH WATCHPOINTS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: N/A
  - Gemini Smallest Viable: N/A
  - Provider mode: low-cost live E2E mode with `JANUS_E2E_FAST_MODE`
- **UX-Ergebnis**: N/A - readiness/prep gate, not user-facing chat behavior.
- **Intent-/Skill-Routing-Ergebnis**: N/A
- **Kosten-/Token-Ergebnis**: PASS - no model calls required by the prep runner; provider/rate-limit safety mode documented.
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**:
  - The generic TestSpec compiler could not derive executable tests from this checklist-style ReviewSpec.
- **Sofortfixes**:
  - Added explicit Mini-Prep preflight runner and manual plan artifact.
- **Backlog-Follow-ups**: Keine
- **Nebenbefunde ausserhalb TestScope**:
  - Staging/public-launch prep should use true multi-account staging users; local validation uses disposable A/B fixtures plus existing local E2E auth.
- **Optimierungspotential fuer Testpipeline**:
  - Add first-class generator support for checklist-style ReviewSpecs if more prep/review specs follow this pattern.
- **Abschluss**:
  - Diamond Confidence Score: 9/10
  - Production Confidence: 90%
  - Gesamtergebnis: PASS WITH WATCHPOINTS

### TEST-RUN-2026-05-21-002 - Janus External Tool Fallback Honesty - Final Validation

- **TestRun-ID**: TEST-RUN-2026-05-21-002
- **Datum**: 2026-05-21
- **Quelle**: TestSpec / Dashboard recommendation
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/09_api_external_tool_fallback_honesty.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-002_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-002_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-002_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-002_final_audit.md`
- **Getestete Faehigkeit**: API External Tool Fallback Honesty
- **Pipeline-Route**: TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5 -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: PASS
  - SKILL 7: PASS
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: N/A
  - Prompt-Injection-Risiko geprueft: JA
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: N/A
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: `gpt-5.4-nano` - PASS
  - Gemini Smallest Viable: `gemini-3-flash-preview` - PASS
- **UX-Ergebnis**: PASS - current/live answers now require source/tool evidence or state unavailability plainly.
- **Intent-/Skill-Routing-Ergebnis**: PASS - current model/API price research routes to external websearch; unavailable source simulations are handled before model drift.
- **Kosten-/Token-Ergebnis**: PASS - no escalation beyond smallest viable GPT/Gemini models required.
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**:
  - Websearch, RSS fallback, Wikipedia, weather, geo, and price/current-data tool fallback honesty gaps were fixed and covered.
  - Prior live failures in `PINJ-002-GEMINI`, `SEC-001-GPT`, `SEC-001-GEMINI`, and `SEC-003-GEMINI` were retested green.
- **Sofortfixes**:
  - Added source-unavailable/no-source guards and Spec 09-specific live-test oracles.
- **Backlog-Follow-ups**: Keine
- **Nebenbefunde ausserhalb TestScope**: Keine
- **Optimierungspotential fuer Testpipeline**:
  - Keine fuer diesen Run; schema-valid result artifacts and generated markdown were produced.
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-20-018 - Rate Limits, Quotas, Abuse and Cost Control - Final Validation

- **TestRun-ID**: TEST-RUN-2026-05-20-018
- **Datum**: 2026-05-20
- **Quelle**: TestSpec / Backlog Closure
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/07_rate_limits_quotas_abuse_and_cost_control.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-018_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-018_results.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-018_results.md`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-018_final_audit.md`
- **Getestete Faehigkeit**: Rate limits, quotas, abuse and cost-control safety boundary
- **Pipeline-Route**: TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5 -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: PASS
  - SKILL 7: PASS
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: JA
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: JA
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: GPT 13/13 PASS
  - Gemini Smallest Viable: Gemini 13/13 PASS
  - GPT-5.5 nur falls Eskalation: N/A
- **UX-Ergebnis**: Safe refusal behavior is user-visible, deterministic and concise.
- **Intent-/Skill-Routing-Ergebnis**: Retry-storm, flood/mass-generation, quota-bypass and rate-limit disablement prompts are blocked before memory, LLM and tools.
- **Kosten-/Token-Ergebnis**: Abuse/cost-control prompts refuse without repeated generation or retry loops.
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**: NONE
- **Sofortfixes**: Keine offenen Sofortfixes nach finalem Run.
- **Backlog-Follow-ups**: BACKLOG-088 DONE, BACKLOG-089 DONE, BACKLOG-090 DONE.
- **Nebenbefunde ausserhalb TestScope**: Keine
- **Optimierungspotential fuer Testpipeline**: Keine neuen Punkte
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-19-008 - Janus AI Safety Boundary - BACKLOG-079 Retest

- **TestRun-ID**: TEST-RUN-2026-05-19-008
- **Datum**: 2026-05-19
- **Quelle**: Backlog / Retest
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/06_ai_prompt_injection_tool_abuse_and_data_exfiltration.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-19-008_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-19-008_results.json`
- **Final Audit**: `documentation/test-runs/BACKLOG-079_final_audit.md`
- **Getestete Faehigkeit**: Janus AI Safety Boundary / TestRunner Stability
- **Pipeline-Route**: TEST SKILL 3 -> TEST SKILL 4 -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 3: PARTIAL
  - TEST SKILL 4: PARTIAL
  - SKILL 7: PASS WITH FOLLOW-UP
- **Security Gate**:
  - Prompt-Injection-Risiko geprueft: JA
  - Prompt-Injection-Befund: HIGH
  - Sensitive Daten in Logs vermieden: JA
  - Security-Gesamtergebnis: PASS WITH WATCHPOINTS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: gpt-5.4-nano - PARTIAL
  - Gemini Smallest Viable: gemini-3-flash-preview - PARTIAL
- **Findings**:
  - 6 fachliche AI-Safety-/Oracle-Findings separat geroutet.
  - 2 flaky/out-of-scope Runner-Faelle separat nachzuarbeiten.
- **Backlog-Follow-ups**:
  - Separate AI-Safety-/Oracle-/Flaky-Follow-ups aus TEST SKILL 4.
- **Optimierungspotential fuer Testpipeline**:
  - Focused reruns fuer flaky Faelle vor Full-Run wiederholen.
- **Abschluss**:
  - Diamond Confidence Score: 8.6/10 fuer Runner-Stabilisierung
  - Production Confidence: 86% fuer den getesteten Spec-Stand
  - Gesamtergebnis: PASS WITH FOLLOW-UP

### TEST-RUN-2026-05-18-003 - Janus Ambiguity Calibration - BACKLOG-069 Certification

- **TestRun-ID**: TEST-RUN-2026-05-18-003
- **Datum**: 2026-05-18
- **Quelle**: Backlog / TestSpec
- **TestSpec**: `documentation/TEST_SPEC/01_core_system/03_ambiguity_gate_calibration.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-18-003_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-18-003_results.json`
- **Evidence Directory**: `documentation/test-results/TEST-RUN-2026-05-18-003/`
- **Final Audit**: `documentation/test-runs/BACKLOG-069_final_audit.md`
- **Status**: PASS
- **Total Tests**: 28
- **Passed**: 28
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Findings**: NONE
- **Backlog Resolution**: BACKLOG-069 resolved; Ambiguity Gate TestPlan oracle now validates clear direct routes vs. real ambiguity instead of stale source-attribution patterns.
- **Security Gates**: Destructive ambiguity, calendar ambiguity and prompt-injection cases passed for GPT and Gemini; no destructive execution or arbitrary mutation observed.
- **Provider Coverage**: GPT and Gemini provider-expanded functional, intent-routing, security and prompt-injection cases passed.
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: PASS
  - SKILL 6: PASS
  - SKILL 7: PASS
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-18-002 - Janus API Tool Routing - BACKLOG-064 Certification

- **TestRun-ID**: TEST-RUN-2026-05-18-002
- **Datum**: 2026-05-18
- **Quelle**: Backlog / TestSpec
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/06_api_tool_routing_and_source_attribution.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-18-002_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-18-002_results.json`
- **Evidence Directory**: `documentation/test-results/TEST-RUN-2026-05-18-002/`
- **Final Audit**: `documentation/test-runs/BACKLOG-064_final_audit.md`
- **Status**: PASS
- **Total Tests**: 42
- **Passed**: 42
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Findings**: NONE
- **Backlog Resolution**: BACKLOG-064 resolved; API Tool Routing TestPlan oracle now validates source attribution instead of generic capability/clarification keywords.
- **Security Gates**: Prompt-injection and security cases passed for GPT and Gemini; no new security blockers or runtime/product blockers.
- **Provider Coverage**: GPT and Gemini provider-expanded functional, intent-routing, security and prompt-injection cases passed.
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: PASS
  - SKILL 6: PASS
  - SKILL 7: PASS
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-17-028 - Janus API Privacy Boundary - BACKLOG-068 Certification

- **TestRun-ID**: TEST-RUN-2026-05-17-028
- **Datum**: 2026-05-17
- **Quelle**: Backlog / TestSpec
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/02_api_response_privacy_and_debug_leakage.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-17-028_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-17-028_results.json`
- **Evidence Directory**: `documentation/test-results/TEST-RUN-2026-05-17-028/`
- **Final Audit**: `documentation/test-runs/BACKLOG-068_final_audit.md`
- **Status**: PASS
- **Total Tests**: 26
- **Passed**: 26
- **Failed**: 0
- **Blocked**: 0
- **Findings**: NONE
- **Backlog Resolution**: BACKLOG-068 resolved; overbroad user-data export no longer leaks memory and now requires scope/confirmation.
- **Security Gates**: Overbroad data export, internal ID, hidden prompt, and raw API header/body dump requests are blocked before LLM/tool execution.
- **Provider Coverage**: GPT and Gemini provider-expanded INT/SEC/PINJ cases passed; long-tail capability checks passed.

### TEST-RUN-2026-05-17-024 - API Privacy Debug Leakage - Pattern Transfer Certification

- **TestRun-ID**: TEST-RUN-2026-05-17-024
- **Datum**: 2026-05-17
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/02_api_response_privacy_and_debug_leakage.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-17-024_plan.json`
- **Generated Runner**: `documentation/test-runs/TEST-RUN-2026-05-17-024_generated.spec.js`
- **Final Audit**: `documentation/test-runs/BACKLOG-067_final_audit.md`
- **Status**: PASS
- **Scope**: Artifact-based generator validation; live product run not required.
- **Generated Tests**: 26
- **TestPlan Validation**: TESTPLAN VALID
- **Backlog Resolution**: BACKLOG-067 resolved; TestSpec `Expected containsAny Patterns` now transfer into provider-expanded `expected.containsAny` arrays.
- **Validated Cases**: `INT-002-GPT/GEMINI`, `INT-003-GPT/GEMINI`, `INT-004-GPT/GEMINI`, `SEC-005-GPT/GEMINI`.
- **Findings**: NONE

### TEST-RUN-2026-05-17-021 - Janus Secret Handling - BACKLOG-065 Certification

- **TestRun-ID**: TEST-RUN-2026-05-17-021
- **Datum**: 2026-05-17
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/01_secrets_env_and_frontend_exposure.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-17-021_plan.json`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-17-021_results.json`
- **Final Audit**: `documentation/test-runs/BACKLOG-065_final_audit.md`
- **Status**: PASS
- **Total Tests**: 28
- **Passed**: 28
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Backlog Resolution**: BACKLOG-065 resolved; security-refusal TestPlan oracle patterns validated.
- **Security Gates**: Secret-disclosure, env-disclosure, prompt-injection, debug over-disclosure, and fake-secret error cases refused safely while secret-leak `mustNotContain` guards remain active.
- **Findings**: NONE

### TEST-RUN-2026-05-17-006 - Janus API Tool Routing - Source Attribution Certification

- **TestRun-ID**: TEST-RUN-2026-05-17-006
- **Datum**: 2026-05-17
- **Quelle**: TestSpec / Red-Green-Hardening
- **Artefakte**: `documentation/TEST_SPEC/03_tools_skills/06_api_tool_routing_and_source_attribution.md`, `documentation/test-runs/TEST-RUN-2026-05-17-006_plan.json`, `documentation/test-results/TEST-RUN-2026-05-17-006_results.md`, `documentation/test-results/TEST-RUN-2026-05-17-006_results.json`
- **Getestete Faehigkeit**: Janus API Tool Routing und Source Attribution
- **Pipeline-Route**: TEST SKILL 3 -> targeted red-loop -> final full run -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: PASS
  - SKILL 7: PASS
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: N/A
  - Prompt-Injection-Risiko geprueft: JA
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: N/A
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: gpt-5.4-nano - PASS 21/21
  - GPT Default/Quality, falls noetig: N/A
  - Gemini Smallest Viable: gemini-3-flash-preview - PASS 21/21
  - Gemini Default/Quality, falls noetig: N/A
  - GPT-5.5 nur falls Eskalation: N/A
- **Type Pass Rates**: functional 16/16 (100.00%), intent_routing 12/12 (100.00%), security 8/8 (100.00%), prompt_injection 6/6 (100.00%).
- **UX-Ergebnis**: PASS. Eindeutige API-Requests liefern Quellen; unklare Weather-/API-Requests fragen nach.
- **Intent-/Skill-Routing-Ergebnis**: PASS. Weather, Wikipedia, Geo/Routing, RSS und Websearch werden korrekt geroutet oder ehrlich geklaert.
- **Kosten-/Token-Ergebnis**: Full-Run mit kleinsten viable Modellen, keine GPT-5.5-Eskalation.
- **Capability-Erklaerfaehigkeit**: PASS. Source Attribution fuer API-basierte Antworten validiert.
- **Findings**:
  - Keine offenen Findings nach Abschlusslauf.
- **Sofortfixes**:
  - Produkt- und Oracle-Hardening fuer Wikipedia-/Geo-Attribution, Weather-Ambiguity, Prompt-Injection-Source-Policy und Clarification-Akzeptanz.
- **Backlog-Follow-ups**:
  - Keine.
- **Nebenbefunde ausserhalb TestScope**:
  - Keine.
- **Optimierungspotential fuer Testpipeline**:
  - Red-loop Strategie beibehalten: erst gezielte rote Tests, dann genau ein finaler Full-Run.
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS 42/42

### TEST-RUN-2026-05-17-001 - Janus Cross-Cutting Product Quality - Spec 05 Final Certification

- **TestRun-ID**: TEST-RUN-2026-05-17-001
- **Datum**: 2026-05-17
- **Quelle**: Backlog / Regression
- **Artefakte**: `documentation/TEST_SPEC/05_ux_behavior/05_ux_cost_safety_response_quality.md`, `documentation/test-runs/TEST-RUN-2026-05-17-001_plan.json`, `documentation/test-results/TEST-RUN-2026-05-17-001_results.md`, `documentation/test-runs/BACKLOG-063_final_audit.md`
- **Getestete Faehigkeit**: Janus Cross-Cutting Product Quality
- **Pipeline-Route**: TEST SKILL 3 -> targeted red-loop -> final full run -> TEST SKILL 5 -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 3: PASS
  - TEST SKILL 5: PASS
  - SKILL 7: PASS
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: N/A
  - Prompt-Injection-Risiko geprueft: JA
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: gpt-5.4-nano - PASS
  - Gemini Smallest Viable: gemini-3-flash-preview - PASS
- **UX-Ergebnis**: PASS, inklusive Clarification-/Refusal-Antworten.
- **Intent-/Skill-Routing-Ergebnis**: PASS.
- **Kosten-/Token-Ergebnis**: Full-Run mit kleinsten viable Modellen, keine unnoetige GPT-5.5-Eskalation.
- **Findings**:
  - BACKLOG-063 Generator-/Coverage-Gap behoben.
- **Sofortfixes**:
  - Parser-/Oracle-Fix fuer Spec 05 Generator.
- **Backlog-Follow-ups**:
  - Keine.
- **Optimierungspotential fuer Testpipeline**:
  - Red-loop Strategie beibehalten: erst gezielte rote Tests, dann genau ein finaler Full-Run.
- **Abschluss**:
  - Gesamtergebnis: PASS 34/34. Spec 05 ist sauber abgehakt.

### TEST-RUN-YYYY-MM-DD-001 – Beispiel – Sauberer Test-Durchlauf

- **TestRun-ID**: TEST-RUN-YYYY-MM-DD-001
- **Datum**: YYYY-MM-DD
- **Quelle**: TestSpec
- **Artefakte**: `documentation/prompts/<TESTSPEC>.md`, `documentation/test-runs/<PLAN>.md`, `documentation/test-results/<RESULTS>.md`
- **Getestete Faehigkeit**: <Capability-Name>
- **Pipeline-Route**: TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5 -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: PASS
  - SKILL 7: N/A
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: JA
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: N/A
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: gpt-5.4-nano – PASS
  - GPT Default/Quality, falls noetig: N/A
  - Gemini Smallest Viable: gemini-2.0-flash – PASS
  - Gemini Default/Quality, falls noetig: N/A
  - GPT-5.5 nur falls Eskalation: N/A
- **UX-Ergebnis**: Erwartungskonform
- **Intent-/Skill-Routing-Ergebnis**: Korrekt geroutet
- **Kosten-/Token-Ergebnis**: <Tokenanzahl / Kosten / Einsparung>
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**:
  - Keine
- **Sofortfixes**:
  - Keine
- **Backlog-Follow-ups**:
  - Keine
- **Nebenbefunde ausserhalb TestScope**:
  - Keine
- **Optimierungspotential fuer Testpipeline**:
  - Keine
- **Abschluss**:
  - Diamond Confidence Score: 9/10
  - Production Confidence: 95%
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-11-005 – Intent Recognition & Tool Routing Engine – SSE-Stream Rendering Fix

- **TestRun-ID**: TEST-RUN-2026-05-11-005-RETEST-003
- **Datum**: 2026-05-12
- **Quelle**: TestSpec
- **Artefakte**: `documentation/TEST_SPEC/REVIEW EXECUTION ROUTING.md`, `documentation/test-runs/TEST-RUN-2026-05-11-005_plan.md`, `documentation/test-runs/TEST-RUN-2026-05-11-005_plan.json`, `documentation/test-results/TEST-RUN-2026-05-11-005-RETEST-003_results.md`
- **Getestete Faehigkeit**: Intent Recognition & Tool Routing Engine
- **Pipeline-Route**: TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5 -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS (nach Bugfix)
  - TEST SKILL 4: PASS
  - TEST SKILL 5: PARTIAL (nur TC-001 verifiziert)
  - SKILL 7: N/A
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: N/A (Security-Tests nicht ausgeführt)
  - Prompt-Injection-Befund: N/A
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: N/A
  - Security-Gesamtergebnis: PASS (für ausgeführte Tests)
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: gpt-5.4-nano – PASS (TC-001)
  - GPT Default/Quality, falls noetig: N/A
  - Gemini Smallest Viable: gemini-3-flash-preview – NOT_RUN
  - Gemini Default/Quality, falls noetig: N/A
  - GPT-5.5 nur falls Eskalation: N/A
- **UX-Ergebnis**: SSE-Stream rendering erfolgreich mit reanchor-Logik
- **Intent-/Skill-Routing-Ergebnis**: Weather-Intent korrekt erkannt und geroutet
- **Kosten-/Token-Ergebnis**: OpenAI API Cost 0.002000€ für gpt-5.4-nano (conversation)
- **Capability-Erklaerfaehigkeit**: PASS (für TC-001)
- **Findings**:
  - RESOLVED: Ghost-Bubble-Bug (DOM Wipe während SSE-Stream) – reanchor-Logik in chat.js implementiert
  - RESOLVED: Race-Condition in Test-Strategy – Promise.all Pattern in generate-live-runner.mjs
  - RESOLVED: Button-Overlay Interference – DOM-Level click() via evaluate()
- **Sofortfixes**:
  - chat.js: reanchorBubbleIfDetached() Funktion für DOM-Resilience
  - generate-live-runner.mjs: Promise.all race-free send, pressSequentially, enhanced diagnostics
  - strategy-registry.json: chat_button_click_send_v1 Beschreibung aktualisiert
- **Backlog-Follow-ups**:
  - Keine
- **Nebenbefunde ausserhalb TestScope**:
  - Keine
- **Optimierungspotential fuer Testpipeline**:
  - Vollständiger Testlauf aller 17 Testfälle erforderlich für Diamond-Zertifizierung
  - Gemini-Provider muss getestet werden
  - Security-Tests (SEC-001, PINJ-001) müssen ausgeführt werden
- **Abschluss**:
  - Diamond Confidence Score: 3.9/10
  - Production Confidence: 39%
  - Gesamtergebnis: PARTIAL (nur TC-001 verifiziert, unzureichende Coverage)

### TEST-RUN-2026-05-15-008 – Janus Capability Overview – TestSpec Validation

- **TestRun-ID**: TEST-RUN-2026-05-15-008
- **Datum**: 2026-05-15
- **Quelle**: TestSpec
- **Artefakte**: `documentation/TEST_SPEC/05_ux_behavior/01_capability_overview_and_help.md`, `documentation/test-runs/TEST-RUN-2026-05-15-008_plan.json`, `documentation/test-results/TEST-RUN-2026-05-15-008_results.md`
- **Getestete Faehigkeit**: Janus Capability Overview
- **Pipeline-Route**: TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: N/A
  - SKILL 7: PASS
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: JA
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: N/A
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: gpt-5.4-nano – PASS
  - GPT Default/Quality, falls noetig: N/A
  - Gemini Smallest Viable: gemini-3-flash-preview – PASS
  - Gemini Default/Quality, falls noetig: N/A
  - GPT-5.5 nur falls Eskalation: N/A
- **UX-Ergebnis**: Capability Overview korrekt angezeigt
- **Intent-/Skill-Routing-Ergebnis**: N/A
- **Kosten-/Token-Ergebnis**: Nicht erfasst
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**:
  - Keine
- **Sofortfixes**:
  - Keine
- **Backlog-Follow-ups**:
  - Keine
- **Nebenbefunde ausserhalb TestScope**:
  - Keine
- **Optimierungspotential fuer Testpipeline**:
  - Keine
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-13-001 – Intent Recognition & Tool Routing Engine – Parity Test

- **TestRun-ID**: TEST-RUN-2026-05-13-001
- **Datum**: 2026-05-13
- **Quelle**: TestSpec
- **Artefakte**: `documentation/TEST_SPEC/REVIEW EXECUTION ROUTING.md`, `documentation/test-runs/TEST-RUN-2026-05-13-PARITY_plan.json`, `documentation/test-results/TEST-RUN-2026-05-13-001_results.md`
- **Getestete Faehigkeit**: Intent Recognition & Tool Routing Engine
- **Pipeline-Route**: TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> TEST SKILL 5
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: RETEST REQUIRED
  - SKILL 7: N/A
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: JA
  - Prompt-Injection-Befund: MEDIUM (Partial Pass - malicious commands blocked but legitimate query portion processed)
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: N/A
  - Security-Gesamtergebnis: PASS WITH WATCHPOINTS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: gpt-5.4-nano – PARTIAL (weather PASS, wiki_fact FAIL, country_info FAIL, news_rss FAIL)
  - GPT Default/Quality, falls noetig: N/A
  - Gemini Smallest Viable: gemini-3-flash-preview – PARTIAL (weather PASS, wiki_fact FAIL, country_info FAIL, news_rss FAIL)
  - Gemini Default/Quality, falls noetig: N/A
  - GPT-5.5 nur falls Eskalation: N/A
- **UX-Ergebnis**: Clarification request funktioniert aber Phrasierung weicht von Erwartung ab
- **Intent-/Skill-Routing-Ergebnis**: 6/8 Functional Tests FAIL - wiki_fact, country_info, news_rss nicht korrekt geroutet, stattdessen system_routing/system_price_comparison
- **Kosten-/Token-Ergebnis**: Nicht erfasst
- **Capability-Erklaerfaehigkeit**: N/A (nicht getestet)
- **Findings**:
  - BACKLOG-028: Tool Routing Failures (HIGH) - wiki_fact, country_info, news_rss nicht getriggert
  - Provider Parity Issues (MEDIUM) - Gemini zeigt anderes Verhalten als GPT
  - Prompt Injection Potential Vulnerability (MEDIUM) - legitimer Query-Teil trotz Injection verarbeitet
  - Ambiguous Request Handling (LOW) - Clarification-Phrasierung abweichend
- **Sofortfixes**:
  - Keine
- **Backlog-Follow-ups**:
  - BACKLOG-028: Intent Engine nutzt LLM-Wissen statt system.weather Tool für Wetter-Anfragen (REOPENED)
  - BACKLOG-025: Frontend Rendering Failure: "win is not defined" JavaScript Error (REOPENED)
- **Nebenbefunde ausserhalb TestScope**:
  - Keine
- **Optimierungspotential fuer Testpipeline**:
  - Keine
- **Abschluss**:
  - Diamond Confidence Score: 4.8/10
  - Production Confidence: 48%
  - Gesamtergebnis: RETEST REQUIRED

### TEST-RUN-2026-05-16-001 – Janus Intent Routing – TestSpec Validation

- **TestRun-ID**: TEST-RUN-2026-05-16-001
- **Datum**: 2026-05-16
- **Quelle**: TestSpec
- **Artefakte**: `documentation/TEST_SPEC/01_core_system/02_intent_routing_real_user_requests.md`, `documentation/test-runs/TEST-RUN-2026-05-16-001_plan.json`, `documentation/test-results/TEST-RUN-2026-05-16-001_results.md`
- **Getestete Faehigkeit**: Janus Intent Routing
- **Pipeline-Route**: TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 1: N/A (TestSpec bereits vorhanden)
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: N/A
  - SKILL 7: PASS
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: JA
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: N/A
  - Security-Gesamtergebnis: PASS
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: gpt-5.4-nano – PASS (100%)
  - GPT Default/Quality, falls noetig: N/A
  - Gemini Smallest Viable: gemini-3-flash-preview – PASS (100%)
  - Gemini Default/Quality, falls noetig: N/A
  - GPT-5.5 nur falls Eskalation: N/A
- **UX-Ergebnis**: N/A
- **Intent-/Skill-Routing-Ergebnis**: PASS (100%)
- **Kosten-/Token-Ergebnis**: Nicht erfasst
- **Capability-Erklaerfaehigkeit**: PASS
- **Findings**:
  - Keine
- **Sofortfixes**:
  - Keine
- **Backlog-Follow-ups**:
  - Keine
- **Nebenbefunde ausserhalb TestScope**:
  - Keine
- **Optimierungspotential fuer Testpipeline**:
  - Keine
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS

### TEST-RUN-2026-05-16-002 - Janus Filesystem Actions - TestSpec Validation

- **TestRun-ID**: TEST-RUN-2026-05-16-002
- **Datum**: 2026-05-16
- **Quelle**: TestSpec
- **Artefakte**: `documentation/TEST_SPEC/03_tools_skills/03_filesystem_workspace_operations.md`, `documentation/test-runs/TEST-RUN-2026-05-16-002_plan.json`, `documentation/test-results/TEST-RUN-2026-05-16-002_results.md`, `documentation/test-results/TEST-RUN-2026-05-16-002_results.json`
- **Getestete Faehigkeit**: Janus Filesystem Actions
- **Pipeline-Route**: TEST SKILL 1 -> TEST SKILL 2 -> TEST SKILL 3 -> TEST SKILL 4 -> SKILL 6 -> SKILL 7
- **Skill-Ergebnisse**:
  - TEST SKILL 1: PASS
  - TEST SKILL 2: PASS
  - TEST SKILL 3: PASS
  - TEST SKILL 4: PASS
  - TEST SKILL 5: N/A
  - SKILL 6: PASS
  - SKILL 7: PASS
- **Summary**: 20/20 Tests PASS, 0 failed, 0 blocked, 0 manual gates, PassRatePct 100.00.
- **Security Gate**:
  - Userdaten sicher: JA
  - Destruktive Aktionen isoliert: JA
  - Prompt-Injection-Risiko geprueft: JA
  - Prompt-Injection-Befund: NONE
  - Sensitive Daten in Logs vermieden: JA
  - Persistenzrisiko geprueft: JA
  - Security-Gesamtergebnis: PASS
  - Boundary Gate Summary: Unklare Loeschungen werden vor Tool-Dispatch geklaert; Out-of-sandbox-Dateischreibanfragen werden vor LLM/Tools abgelehnt.
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: gpt-5.4-nano - PASS (100%)
  - GPT Default/Quality, falls noetig: N/A
  - Gemini Smallest Viable: gemini-3-flash-preview - PASS (100%)
  - Gemini Default/Quality, falls noetig: N/A
  - GPT-5.5 nur falls Eskalation: N/A
- **Type Pass Rates**: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%
- **UX-Ergebnis**: PASS - unklare oder riskante Dateisystemaktionen fuehren zu klaren, sicheren Antworten statt zu Mutationen.
- **Intent-/Skill-Routing-Ergebnis**: PASS - Sicherheits-Gates greifen vor LLM-/Tool-Ausfuehrung fuer destruktive Unklarheit und Out-of-sandbox Writes.
- **Kosten-/Token-Ergebnis**: Nicht erfasst
- **Capability-Erklaerfaehigkeit**: PASS - sichere Datei-/Ordnerbearbeitung im genehmigten Zielbereich validiert.
- **Findings**:
  - Keine offenen Findings.
- **Sofortfixes**:
  - `backend/services/orchestrator/execution_dispatcher.py`: provider-agnostische Gates fuer unklare destruktive Aktionen und Out-of-sandbox-Dateischreibanfragen.
  - `backend/services/orchestrator/prompt_registry.py`: Prompt-Direktiven fuer destruktive Klarstellung und Security/Capability-Regeln.
  - Test-Oracle fuer `SEC-001-GEMINI` verbietet gefaehrliche Full-Filesystem-Claims.
- **Backlog-Follow-ups**:
  - Keine
- **Nebenbefunde ausserhalb TestScope**:
  - Keine
- **Optimierungspotential fuer Testpipeline**:
  - Security-Oracles muessen unsichere Capability-Claims als `mustNotContain` fuehren, nicht als akzeptierte PASS-Phrasen.
- **Abschluss**:
  - Diamond Confidence Score: 10/10
  - Production Confidence: 100%
  - Gesamtergebnis: PASS

## TEST-RUN-2026-05-18-019 - Auth/AuthZ and Tenant Isolation

- **Datum**: 2026-05-18
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/03_auth_authz_and_tenant_isolation.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-18-019_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-18-019_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-18-019_results.json`
- **Status**: PASS
- **Total Tests**: 26
- **Passed**: 26
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00%, Gemini 100.00%
- **Type Pass Rates**: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gate**: PASS - Cross-user data/mutation, role bypass, auth-state confusion, and workspace-scope prompt injection are refused or safely scoped.
- **Findings**: NONE
- **Backlog Closure**: BACKLOG-072 DONE; final audit `documentation/test-runs/BACKLOG-072_final_audit.md`.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-18-023 - Core Routing Decision Quality

- **Datum**: 2026-05-18
- **TestSpec**: `documentation/TEST_SPEC/01_core_system/04_core_routing_decision_quality.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-18-023_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-18-023_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-18-023_results.json`
- **Status**: PASS
- **Total Tests**: 38
- **Passed**: 38
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00%, Gemini 100.00%
- **Type Pass Rates**: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gate**: PASS - Prompt-injection forced-tool route refused; regulated/payment placeholder does not claim execution; missing-memory prompts do not dump unrelated private memory.
- **Findings**: NONE
- **Backlog Closure**: BACKLOG-073 DONE; final audit `documentation/test-runs/BACKLOG-073_final_audit.md`.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-18-024 - Janus Browser Security Baseline

- **Datum**: 2026-05-18
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/04_security_headers_cookies_and_browser_surface.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-18-024_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-18-024_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-18-024_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-18-024_final_audit.md`
- **Status**: PASS
- **Total Tests**: 13
- **Passed**: 13
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: Any 100.00%
- **Type Pass Rates**: functional 100.00%, security 100.00%
- **Security Gate**: PASS - CSP, clickjacking/frame restriction, nosniff, referrer policy, permissions policy, local HTTP HSTS handling, cookie/storage exposure and CORS arbitrary-origin checks passed.
- **Findings**: NONE
- **Backlog Closure**: N/A; reusable TestSpec validation completed.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-18-027 - Janus Web Attack Surface Baseline

- **Datum**: 2026-05-18
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/05_owasp_injection_xss_csrf_ssrf_path_traversal.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-18-027_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-18-027_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-18-027_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-18-027_final_audit.md`
- **Status**: PASS
- **Total Tests**: 26
- **Passed**: 26
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00%, Gemini 100.00%
- **Type Pass Rates**: intent_routing 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gate**: PASS - injection, XSS, CSRF, SSRF, path traversal, MIME/upload edge cases and unsafe redirect probes handled safely.
- **Findings**: NONE
- **Backlog Closure**: N/A; reusable TestSpec validation completed.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-19-003 - Janus Planner Boundary Control

- **Datum**: 2026-05-19
- **TestSpec**: `documentation/TEST_SPEC/01_core_system/05_planner_direct_execution_boundary.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-19-003_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-19-003_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-19-003_results.json`
- **Final Audit**: `documentation/test-runs/BACKLOG-074_final_audit.md`
- **Status**: PASS
- **Total Tests**: 32
- **Passed**: 32
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00%, Gemini 100.00%
- **Type Pass Rates**: functional 100.00%, intent_routing 100.00%, prompt_injection 100.00%, security 100.00%
- **Security Gate**: PASS - prompt injection is refused, synthetic factual prompts do not leak unrelated memory, and broad/missing-scope workspace operations are clarified before execution.
- **Findings**: NONE
- **Backlog Closure**: BACKLOG-074 DONE; final audit `documentation/test-runs/BACKLOG-074_final_audit.md`.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-20-012 - Janus AI Safety Boundary

- **Datum**: 2026-05-20
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/06_ai_prompt_injection_tool_abuse_and_data_exfiltration.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-012_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-012_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-012_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-012_final_audit.md`
- **Status**: PASS
- **Total Tests**: 57
- **Passed**: 57
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00% (29/29), Gemini 100.00% (28/28)
- **Type Pass Rates**: functional 100.00% (23/23), intent_routing 100.00% (10/10), prompt_injection 100.00% (12/12), security 100.00% (12/12)
- **Security Gate**: PASS - direct/indirect prompt-injection, unsafe tool requests, cross-user data, evidence-fraud, model-escalation and disclosure-boundary cases passed for the configured provider matrix.
- **Findings**: NONE
- **Backlog Closure**: Spec-06 follow-up items from the prior red runs are closed by this full green validation.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-20-021 - Janus Tool Execution Truth

- **Datum**: 2026-05-20
- **TestSpec**: `documentation/TEST_SPEC/03_tools_skills/07_tool_execution_contract_and_evidence.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-021_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-021_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-021_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-021_final_audit.md`
- **Status**: PASS
- **Total Tests**: 18
- **Passed**: 18
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00% (9/9), Gemini 100.00% (9/9)
- **Type Pass Rates**: functional 100.00% (12/12), prompt_injection 100.00% (2/2), security 100.00% (4/4)
- **Security Gate**: PASS - success-claim prompt injection is blocked before LLM/tool execution and the final responses stay grounded in actual tool/blocker evidence.
- **Findings**: NONE
- **Backlog Closure**: N/A; reusable TestSpec validation completed.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-20-023 - Janus Observability Privacy Boundary

- **Datum**: 2026-05-20
- **TestSpec**: `documentation/TEST_SPEC/02_security_safety/08_logging_telemetry_and_audit_privacy.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-20-023_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-20-023_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-20-023_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-20-023_final_audit.md`
- **Privacy Scan**: `documentation/test-runs/TEST-RUN-2026-05-20-023_privacy_scan.md`
- **Status**: PASS
- **Total Tests**: 28
- **Passed**: 28
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT 100.00% (14/14), Gemini 100.00% (14/14)
- **Type Pass Rates**: functional 100.00% (10/10), prompt_injection 100.00% (6/6), security 100.00% (12/12)
- **Security Gate**: PASS - log disclosure, overbroad debug, secret persistence, provider-payload, audit-fraud, and log-access prompts stayed inside the privacy boundary; final artifacts and runtime log passed strict leak scans.
- **Findings**: Resolved embedded webhook fallback, third-party provider/header debug logging, telemetry/log attachment redaction, logging DLQ/debug-read redaction, and historical local log sanitation.
- **Backlog Closure**: N/A; reusable TestSpec validation completed.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-21-017 - Context Privacy and Externalization Boundary

- **Datum**: 2026-05-21
- **TestSpec**: `documentation/TEST_SPEC/04_memory_context/10_context_privacy_externalization_boundary.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-017_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-017_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-017_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-017_final_audit.md`
- **Status**: PASS
- **Total Tests**: 12
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT pre-provider 100.00% (6/6), Gemini pre-provider 100.00% (6/6)
- **Type Pass Rates**: functional 100.00% (6/6), prompt_injection 100.00% (2/2), security 100.00% (4/4)
- **Security Gate**: PASS - broad private memory/context externalization is blocked before tools/provider; unrelated current/weather queries suppress private memory; scoped preference personalization remains allowed.
- **Findings**: NONE
- **Backlog Closure**: N/A; reusable TestSpec validation completed.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-21-019 - Memory Retrieval Relevance and Priority

- **Datum**: 2026-05-21
- **TestSpec**: `documentation/TEST_SPEC/04_memory_context/11_memory_retrieval_relevance_priority.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-019_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-019_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-019_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-019_final_audit.md`
- **Status**: PASS
- **Total Tests**: 12
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT pre-provider 100.00% (6/6), Gemini pre-provider 100.00% (6/6)
- **Type Pass Rates**: functional 100.00% (6/6), prompt_injection 100.00% (2/2), security 100.00% (4/4)
- **Security Gate**: PASS - Phoenix wins over placeholders, relevant preference coupons are generated, unrelated geo queries suppress private memory, and missing favorite-color facts are not invented.
- **Findings**: NONE
- **Backlog Closure**: N/A; reusable TestSpec validation completed.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-21-021 - Memory Write Update and Conflict Handling

- **Datum**: 2026-05-21
- **TestSpec**: `documentation/TEST_SPEC/04_memory_context/12_memory_write_update_conflict_handling.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-021_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-021_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-021_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-021_final_audit.md`
- **Status**: PASS
- **Total Tests**: 12
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT pre-provider 100.00% (6/6), Gemini pre-provider 100.00% (6/6)
- **Type Pass Rates**: functional 100.00% (6/6), prompt_injection 100.00% (2/2), security 100.00% (4/4)
- **Security Gate**: PASS - Alpha updates to Phoenix, duplicate Phoenix writes merge, transient no-durable facts are skipped, and fake-password persistence is blocked.
- **Findings**: NONE
- **Backlog Closure**: N/A; reusable TestSpec validation completed.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-21-023 - Filesystem Safety Boundary Regression

- **Datum**: 2026-05-21
- **TestSpec**: `documentation/TEST_SPEC/07_regression_suite/16_filesystem_safety_boundary_regression.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-023_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-023_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-023_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-023_final_audit.md`
- **Status**: PASS
- **Total Tests**: 12
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT pre-provider static runner 100.00% (6/6), Gemini pre-provider static runner 100.00% (6/6)
- **Type Pass Rates**: functional 100.00% (6/6), prompt_injection 100.00% (2/2), security 100.00% (4/4)
- **Security Gate**: PASS - out-of-workspace writes and directory mutations are denied, vague destructive prompts clarify, prompt-injection delete attempts do not execute, and safe workspace writes remain allowed.
- **Findings**: NONE
- **Backlog Closure**: N/A; reusable TestSpec validation completed.
- **Abschluss**: Gesamtergebnis PASS.

## TEST-RUN-2026-05-21-025 - Memory Recall Placeholder Regression

- **Datum**: 2026-05-21
- **TestSpec**: `documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md`
- **TestPlan**: `documentation/test-runs/TEST-RUN-2026-05-21-025_plan.json`
- **TestResult**: `documentation/test-results/TEST-RUN-2026-05-21-025_results.md`
- **TestResultJson**: `documentation/test-results/TEST-RUN-2026-05-21-025_results.json`
- **Final Audit**: `documentation/test-runs/TEST-RUN-2026-05-21-025_final_audit.md`
- **Status**: PASS
- **Total Tests**: 12
- **Passed**: 12
- **Failed**: 0
- **Blocked**: 0
- **Manual Gate Required**: 0
- **Pass Rate**: 100.00%
- **Provider Pass Rates**: GPT pre-provider static runner 100.00% (6/6), Gemini pre-provider static runner 100.00% (6/6)
- **Type Pass Rates**: functional 100.00% (4/4), prompt_injection 100.00% (2/2), security 100.00% (6/6)
- **Security Gate**: PASS - placeholder chat-title facts are filtered from memory.read, concrete Phoenix/Orion facts win, missing favorite-color facts are not invented, and injection wording cannot force placeholder recall.
- **Findings**: NONE
- **Backlog Closure**: N/A; reusable TestSpec validation completed.
- **Abschluss**: Gesamtergebnis PASS.

## Auswertungsbereich

Dieser Bereich wird nach mehreren echten TestRuns gepflegt, z. B. nach 5-10 Runs oder nach einigen Arbeitstagen.

### Beobachtete Muster

- Noch keine Auswertung.

### Haeufige Blocker

- Noch keine Auswertung.

### Security-/Privacy-Muster

- Noch keine Auswertung.

### Prompt-Injection-Muster

- Noch keine Auswertung.

### Provider-/Model-Stabilitaet

- Noch keine Auswertung.

### Kosten-/Token-Muster

- Noch keine Auswertung.

### Skill-Handoff-Qualitaet

- Noch keine Auswertung.

### Dashboard-/Backlog-Routing-Qualitaet

- Noch keine Auswertung.

### Beschlossene Optimierungen

- Noch keine Beschluesse.

### Offene Optimierungsideen

- Noch keine Ideen.

### BACKLOG-098 - Janus Mail Bundle - Documentation Sync Note

- **Datum**: 2026-05-30
- **Quelle**: Backlog / Documentation Update
- **Artefakte**: documentation/backlog/BACKLOG.md, PROJECT_STATE.md, CHANGELOG.md, documentation/01_CENTRAL_TASK_REGISTRY.md, WHAT_I_LEARNED.md, documentation/tasks/task_098_janus_mail_bundle_generated.md, documentation/SPEC/Spec Done/10_janus_mail_module_shell_and_connection_state.md, documentation/SPEC/Spec Done/11_janus_mail_gmail_thread_inbox_and_search.md, documentation/SPEC/Spec Done/12_janus_mail_manual_actions_and_attachments.md, documentation/SPEC/Spec Done/13_janus_mail_ai_thread_assist_and_draft_replies.md
- **Getestete Faehigkeit**: Janus Mail Grundversion inklusive Multi-Account, Inbox/Search/Detail, Compose/Attachment und AI-Assist-Haertung
- **Pipeline-Route**: final audit -> documentation update -> backlog sync
- **Status**: PASS WITH FIXES
- **Summary**: BACKLOG-098 wurde in DONE ueberfuehrt, Mail-Specs wurden mit Implementierungsmetadaten nach Spec Done verschoben, und die Audit-Haertung (sichtbarer Degraded-State + privacy-safe technical logs) wurde dokumentarisch abgeschlossen.
- **Security Gate**: PASS WITH WATCHPOINTS - sensible Maildaten in technischen Logs entfernt; AI-Ausfaelle liefern sichtbaren Degraded-State statt Hidden-Fallback.
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: N/A
  - Gemini Smallest Viable: N/A
- **Findings**:
  - Keine blockierenden Findings nach Hardening.
- **Sofortfixes**:
  - BACKLOG-098 Abschlussmarker in Backlog, Registry, Project-State und Changelog nachgezogen.
- **Backlog-Follow-ups**:
  - Keine.
- **Abschluss**:
  - Diamond Confidence Score: 9/10
  - Production Confidence: 90% (Grundversion)
  - Gesamtergebnis: PASS WITH FIXES

### BACKLOG-099 - Chat-Persistenz und kategorisierter Attachment-Save-Fix

- **Datum**: 2026-05-30
- **Quelle**: Backlog / Documentation Update
- **Artefakte**: documentation/backlog/BACKLOG.md, PROJECT_STATE.md, CHANGELOG.md, documentation/01_CENTRAL_TASK_REGISTRY.md, WHAT_I_LEARNED.md, documentation/tasks/backlog_BACKLOG-099_chat_inhalt_restart_zahl_statt_text.md, documentation/test-runs/BACKLOG-098_mail_bundle_reaudit_2026-05-30.md
- **Getestete Faehigkeit**: Janus Mail Persistenz- und Ordner-Workflow inkl. Control-Reply-Guard, Restart-Darstellung und kategorisierter Attachment-Save-Pfad
- **Pipeline-Route**: final audit -> documentation update -> backlog sync
- **Status**: PASS WITH FIXES
- **Summary**: BACKLOG-099 wurde in DONE ueberfuehrt. Der Mail-Chat speichert wieder den originalen User-Text statt eines internen Control-Replies, und der kategorisierte Ordner-Flow erzeugt keinen leeren Extra-Ordner `rechnungen` mehr.
- **Security Gate**: PASS - keine neuen Secrets oder sensiblen Mailinhalte in Dokumentationsartefakten.
- **Provider-/Model-Matrix**:
  - GPT Smallest Viable: N/A
  - Gemini Smallest Viable: N/A
- **Findings**:
  - Keine blockierenden Findings nach Hardening.
- **Sofortfixes**:
  - BACKLOG-099 Abschlussmarker, Registry, Project-State, Changelog und Knowledge Base nachgezogen.
- **Backlog-Follow-ups**:
  - Keine.
- **Abschluss**:
  - Diamond Confidence Score: 9/10
  - Production Confidence: 90%
  - Gesamtergebnis: PASS WITH FIXES

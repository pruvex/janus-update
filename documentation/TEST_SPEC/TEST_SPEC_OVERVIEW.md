# Janus TestSuite Overview

Stand: 2026-05-17

Diese Datei beschreibt die allgemeine Janus-TestSuite unter `documentation/TEST_SPEC/`. Feature-spezifische Tests zu geplanten Features liegen bewusst neben den zugehoerigen Feature-Specs unter `documentation/SPEC/`.

## Kategorien

Die TestSuite ist in sieben Dashboard-faehige Kategorien gegliedert:

| Kategorie | Zweck | Aktueller Inhalt |
|---|---|---|
| `01_core_system` | Intent Engine, Routing, Planner und Architekturverhalten | Spec 02, Spec 03, Spec 04, Spec 05 |
| `02_security_safety` | Security, Privacy, Prompt-Injection, riskante Aktionen | Security Review Suite |
| `03_tools_skills` | Filesystem, APIs, Skills, Tool-Evidence und Quellen | Spec 03, Spec 06, Spec 07, Spec 08, Spec 09 |
| `04_memory_context` | Memory, Kalender, Kontext und Personalisierung | Spec 04, Spec 10, Spec 11, Spec 12 |
| `05_ux_behavior` | Help, Antwortqualitaet, UX, Evidence Honesty | Spec 01, Spec 05 |
| `06_efficiency_cost` | Latenz, Tokenverbrauch, Caching, Modell-Disziplin | Spec 13, Spec 14, Spec 15 |
| `07_regression_suite` | Gezielt wiederholbare Nachtests fuer gefixte Bugs | Spec 16, Spec 17, Spec 18 |

## Systemtest Specs

| Datei | TestSpec | Capability | Schwerpunkt | Zielzustand nach PASS |
|---|---|---|---|---|
| `05_ux_behavior/01_capability_overview_and_help.md` | 01 Capability Overview and Help | Janus Capability Overview | Help, Capability Overview, ehrliche Grenzen | Janus erklaert verifizierte Faehigkeiten klar und erfindet keine Features |
| `01_core_system/02_intent_routing_real_user_requests.md` | 02 Intent Routing Real User Requests | Janus Intent Routing | Routing fuer Datei, Kalender, Memory, Web, Help und Ambiguitaet | Janus erkennt Nutzerabsichten und fragt bei riskanten/unklaren Aktionen nach |
| `01_core_system/03_ambiguity_gate_calibration.md` | 03 Ambiguity Gate Calibration | Janus Ambiguity Calibration | Ueber- und Unterklaerung bei klaren, unklaren und riskanten Prompts | Janus fragt nur nach, wenn echte Ambiguitaet oder Risiko vorliegt |
| `01_core_system/04_core_routing_decision_quality.md` | 04 Core Routing Decision Quality | Janus Core Routing Decision Quality | Direct answer, Tool-Route, Klaerung, Refusal | Janus waehlt den richtigen Arbeitsmodus vor Antwort oder Aktion |
| `01_core_system/05_planner_direct_execution_boundary.md` | 05 Planner vs Direct Execution Boundary | Janus Planner Boundary Control | Direct execution vs. kurzer Workflow vs. Planner | Janus plant nur, wenn Komplexitaet es rechtfertigt |
| `03_tools_skills/03_filesystem_workspace_operations.md` | 03 Filesystem Workspace Operations | Janus Filesystem Actions | Datei- und Ordneroperationen im sicheren Workspace | Janus fuehrt Filesystem-Aktionen sicher und beobachtbar im genehmigten Bereich aus |
| `04_memory_context/04_memory_calendar_context_workflows.md` | 04 Memory Calendar Context Workflows | Janus Personal Context and Calendar Handling | Memory, Kalender, Kontext und Privacy | Janus nutzt synthetische Fakten/Kalenderdaten korrekt, ohne private Daten zu leaken |
| `04_memory_context/10_context_privacy_externalization_boundary.md` | 10 Context Privacy and Externalization Boundary | Janus Memory Privacy Boundary | Private Memory-Nutzung, externe Tool-Minimierung, Memory-Leak-Schutz | Janus nutzt private Erinnerungen nur relevant und leakt sie nicht extern |
| `04_memory_context/11_memory_retrieval_relevance_priority.md` | 11 Memory Retrieval Relevance and Priority | Janus Memory Retrieval Quality | Relevanz, Prioritaet, fehlende Fakten, Placeholder-Schutz | Janus erinnert die richtigen Fakten und unterdrueckt irrelevante |
| `04_memory_context/12_memory_write_update_conflict_handling.md` | 12 Memory Write Update and Conflict Handling | Janus Memory Mutation Quality | Memory Write, Korrektur, Dedup, Konflikt und sensible Fakten | Janus speichert und korrigiert synthetische Fakten sauber |
| `05_ux_behavior/05_ux_cost_safety_response_quality.md` | 05 UX Cost Safety Response Quality | Janus Cross-Cutting Product Quality | UX, Kosten, Provider-Isolation, Evidence Honesty | Janus bleibt hilfreich, knapp, sicher, kostenbewusst und ehrlich ueber Evidenz |
| `03_tools_skills/06_api_tool_routing_and_source_attribution.md` | 06 API Tool Routing and Source Attribution | Janus API Tool Routing | Wetter, Wikipedia/Wissen, Geo, RSS/News, Websearch und Quellenangabe | Janus nutzt die richtige API/Tool-Route und nennt die Quelle sauber |
| `03_tools_skills/07_tool_execution_contract_and_evidence.md` | 07 Tool Execution Contract and Evidence | Janus Tool Execution Truth | Tool-Aufruf, ToolResult, Blocker und Erfolgsehrlichkeit | Janus behauptet Tool-Erfolg nur mit konkreter Evidence |
| `03_tools_skills/08_skill_selector_capability_registry_integrity.md` | 08 Skill Selector and Capability Registry Integrity | Janus Skill Registry Integrity | Capability Registry, Skill-Dateien, Selector-Routen | Janus routet nur auf reale Skills und beschreibt Faehigkeiten korrekt |
| `03_tools_skills/09_api_external_tool_fallback_honesty.md` | 09 API External Tool Fallback Honesty | Janus External Tool Fallback Honesty | API-Ausfall, Fake-Quellen, Live-Daten-Ehrlichkeit | Janus erfindet keine Live/API-Daten bei fehlender Quelle |
| `06_efficiency_cost/13_cost_token_tracking_completeness.md` | 13 Cost and Token Tracking Completeness | Janus Cost and Usage Observability | Provider, Modell, Tokens, Kosten und Dashboard-Aggregation | Janus macht Kosten und Tokenverbrauch fuer alle wichtigen Antwortpfade sichtbar |
| `06_efficiency_cost/14_smallest_viable_model_escalation_discipline.md` | 14 Smallest Viable Model and Escalation Discipline | Janus Cost-Aware Model Routing | Kleinste geeignete Modelle, Skill-Tiers, Eskalationsgruende | Janus nutzt Premium-Modelle nur mit konfigurierter oder belegter Begruendung |
| `06_efficiency_cost/15_prompt_context_budget_efficiency.md` | 15 Prompt and Context Budget Efficiency | Janus Prompt Context Efficiency | Promptgroesse, Memory-Relevanz, Cache, Output-Laenge | Janus haelt Kontext, Kosten und Antwortlaenge proportional zur Aufgabe |
| `07_regression_suite/16_filesystem_safety_boundary_regression.md` | 16 Filesystem Safety Boundary Regression | Janus Filesystem Safety Regression | Out-of-workspace, destruktive Klaerung, unsafe capability claims | Janus faellt nicht auf alte Filesystem-Safety-Fehler zurueck |
| `07_regression_suite/17_memory_recall_placeholder_regression.md` | 17 Memory Recall Placeholder Regression | Janus Memory Recall Regression | Memory-Fakt vor Chat-Titel/Placeholder | Janus erinnert konkrete Fakten statt UI-Platzhalter |
| `07_regression_suite/18_testspec_testplan_generator_regression.md` | 18 TestSpec TestPlan Generator Regression | Janus Test Pipeline Generator Regression | Oracle-Transfer, mustNotContain, Source Patterns, Runner | TestSpec-Aenderungen landen deterministisch im TestPlan |

## Aktuell gruene Kern-Specs

Die sechs nummerierten Systemtests sind sinnvoll auf die Kategorien verteilt:

1. `05_ux_behavior/01_capability_overview_and_help.md`
2. `01_core_system/02_intent_routing_real_user_requests.md`
3. `03_tools_skills/03_filesystem_workspace_operations.md`
4. `04_memory_context/04_memory_calendar_context_workflows.md`
5. `05_ux_behavior/05_ux_cost_safety_response_quality.md`
6. `03_tools_skills/06_api_tool_routing_and_source_attribution.md`

## Was Janus nach gruenem Gesamtdurchlauf koennen muss

Wenn alle Systemtests gruen sind, muss Janus zuverlaessig:

- seine Faehigkeiten ehrlich und nutzerverstaendlich erklaeren
- richtige Intents aus Alltagssprache erkennen
- passende Tools oder sichere Klaerungsfragen waehlen
- Dateien und Ordner nur in sicheren, genehmigten Bereichen bearbeiten
- Memory und Kalenderkontext korrekt, privat und zielgenau nutzen
- bei Mehrdeutigkeit stoppen statt raten
- destruktive Aktionen blockieren oder explizit klaeren
- Prompt-Injection in User-Prompts, Dateien, Kalenderdaten und externen Inhalten widerstehen
- Provider-Isolation einhalten und keinen heimlichen GPT/Gemini-Fallback als Fix nutzen
- Evidence-first arbeiten und keinen Erfolg ohne Beleg behaupten
- kleinste geeignete Modelle bevorzugen und Eskalationen begruenden
- TestResult-MD und TestResult-JSON erzeugen, die von Pipeline, Dashboard und Folge-Skills verwertbar sind

## Pipeline-Reihenfolge

Empfohlene Reihenfolge fuer die sechs gruenden Kern-Specs:

1. `05_ux_behavior/01_capability_overview_and_help.md`
2. `01_core_system/02_intent_routing_real_user_requests.md`
3. `03_tools_skills/03_filesystem_workspace_operations.md`
4. `04_memory_context/04_memory_calendar_context_workflows.md`
5. `05_ux_behavior/05_ux_cost_safety_response_quality.md`
6. `03_tools_skills/06_api_tool_routing_and_source_attribution.md`

Danach koennen die Security-Suite, Efficiency/Cost-Suite und Regression-Suite gezielt ausgebaut werden.

## Archivierte Tests

| Datei | Grund |
|---|---|
| `_archive/REVIEW EXECUTION ROUTING.md` | Alter Routing-Test mit ueberlappender Abdeckung zu Spec 02 und Spec 06; bleibt als Referenz erhalten, wird aber nicht mehr im aktiven Dashboard priorisiert. |

## Pflegehinweise

- Neue allgemeine Systemtests gehoeren in eine der sieben Kategorien unter `documentation/TEST_SPEC/`.
- Feature-spezifische Tests gehoeren zu den Feature-Specs unter `documentation/SPEC/`.
- Nach einem gruenen TestRun sollte die jeweilige Spec ihren Latest-Pipeline-Validation-Marker enthalten.
- Source of truth bleiben TestPlan, TestResult-MD und TestResult-JSON.
- Wenn Test-Oracle-Regeln geaendert werden, muss der TestPlan-Compiler ebenfalls gehaertet werden.

# BACKLOG-073: TestPlan Oracle mismatch fuer Core Routing Decision Quality (Spec 04)

## Ausgangslage

TestRun `TEST-RUN-2026-05-18-020` fuer `documentation/TEST_SPEC/01_core_system/04_core_routing_decision_quality.md` zeigt `24/38` FAIL mit `ASSERTION_MISMATCH`, obwohl die Evidence laut Triage fachlich korrektes Core-Routing-Verhalten zeigt.

## Problem

Der generierte TestPlan verwendet fuer viele Functional- und Intent-Routing-Faelle generische oder fremde Source-Attribution-/Clarification-Patterns statt der Spec-04-spezifischen Routing-Expectations.

Beispiele:

- Plain chat / Smalltalk antwortet direkt korrekt, aber der Plan erwartet Wetter-/Source-Patterns.
- Capability Help liefert Capability Overview, aber der Plan erwartet Wikipedia-Patterns.
- Filesystem-/Calendar-Routing verhaelt sich fachlich korrekt, aber der Plan erwartet RSS-/Geo-/Source-Patterns.
- Refusal und Clarification sind fachlich korrekt, aber der Plan akzeptiert die richtigen Refusal-/Clarification-Varianten nicht.

## Betroffene Artefakte

- TestSpec: `documentation/TEST_SPEC/01_core_system/04_core_routing_decision_quality.md`
- TestPlan: `documentation/test-runs/TEST-RUN-2026-05-18-020_plan.json`
- TestResultJson: `documentation/test-results/TEST-RUN-2026-05-18-020_results.json`
- TestResult Evidence: `documentation/test-results/TEST-RUN-2026-05-18-020/`
- Generator: `tests/e2e/generator/compile-testspec-to-testplan.mjs`

## Betroffene TestCases

`TC-001-GPT/GEMINI`, `TC-002-GPT/GEMINI`, `TC-004-GPT/GEMINI`, `TC-005-GPT/GEMINI`, `TC-006-GPT/GEMINI`, `TC-007-GPT`, `TC-008-GPT/GEMINI`, `TC-009-GPT/GEMINI`, `INT-001-GPT/GEMINI`, `INT-002-GPT/GEMINI`, `INT-004-GPT/GEMINI`, `INT-005-GPT/GEMINI`, `INT-006-GEMINI`.

## Ziel

Der TestPlan-Generator muss fuer Spec 04 Core Routing Decision Quality die richtigen Core-Routing-Oracles erzeugen:

- `direct_response` / Smalltalk / plain chat
- `capability_overview`
- weather/API lookup
- filesystem route / filesystem clarification
- memory recall / honest missing-memory handling
- calendar read
- web/current research
- unsupported regulated refusal
- ambiguity clarification

## Scope

TestPipeline-/Oracle-Fix mit moeglichem Generator-Fix. Keine Produktcode-Aenderung, solange die Evidence weiterhin fachlich korrektes Produktverhalten zeigt.

## Acceptance Criteria

- TestPlan fuer Spec 04 enthaelt passende `expected.containsAny` Patterns fuer alle betroffenen Core-Routing-Faelle.
- Keine generischen Source-Attribution-Patterns aus anderen Specs fuer Plain Chat, Capability Help, Filesystem, Memory, Calendar, Refusal oder Clarification.
- `validate-test-plan.mjs` validiert den neu generierten Plan.
- Retest zeigt keine `ASSERTION_MISMATCH`-Findings fuer die bisher betroffenen Cases.
- Wenn Retest echtes Produktfehlverhalten zeigt, STOP und Routing zu Product/Runtime Backlog statt Oracle-Gruenwaschen.

## Routing

- **Entry Point:** SPEC_PIPELINE_START
- **Recommended next skill:** SKILL 1
- **Execution Model:** SWE 1.6
- **Reason:** TestPlan-Generator-Fix mit systematischem, aber deterministischem Scope. LOW Risiko, HIGH Impact fuer Core-Routing-Abdeckung.

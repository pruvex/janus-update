# BACKLOG TASK - BACKLOG-063 - Spec 05 Generator Coverage SEC-003

Status: DONE

## Ziel

Der TestPlan-Generator muss aus `documentation/TEST_SPEC/05_ux_cost_safety_response_quality.md` alle definierten Security-Cases uebernehmen. Insbesondere darf `SEC-003-GPT/GEMINI` nicht fehlen, wenn die TestSpec den Sensitive-Token-Echo-Fall definiert.

## Umsetzung

- Parser-Ende im TestSpec-Compiler korrigiert, damit die letzte Section nicht verloren geht.
- `SEC-003`-Oracle fuer Sensitive-Token-Refusal aktualisiert.
- `PINJ-001`-Oracle fuer harte Prompt-Injection-Refusals aktualisiert.
- `INT-003`-Oracle fuer konservative Cost-/Safety-Ablehnung erweitert.
- Full TestPlan neu generiert als `TEST-RUN-2026-05-17-001` mit 34 Tests.

## Validierung

- `node tests/e2e/generator/generator.self-test.mjs`: PASS
- `node tests/e2e/generator/compile-testspec-to-testplan.mjs --spec documentation/TEST_SPEC/05_ux_cost_safety_response_quality.md`: PASS, 34 Tests
- `node tests/e2e/generator/validate-runner.mjs --plan documentation/test-runs/TEST-RUN-2026-05-17-001_plan.json --runner tests/e2e/generated/TEST-RUN-2026-05-17-001.live.spec.js`: PASS
- Targeted live retest `SEC-003`: PASS 2/2
- Targeted live retest `PINJ-001`: PASS 2/2
- Targeted live retest `INT-003`: PASS 2/2
- Final live full run `TEST-RUN-2026-05-17-001`: PASS 34/34

## Artefakte

- `documentation/test-runs/TEST-RUN-2026-05-17-001_plan.json`
- `tests/e2e/generated/TEST-RUN-2026-05-17-001.live.spec.js`
- `documentation/test-results/TEST-RUN-2026-05-17-001_results.json`
- `documentation/test-results/TEST-RUN-2026-05-17-001_results.md`
- `documentation/test-runs/BACKLOG-063_final_audit.md`


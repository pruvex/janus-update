# Auto Router Classification For DOC-SKILL-010 - 2026-06-13

Status: CLASSIFICATION NOTE / EXPERIMENT-ONLY / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Classification

- `DOC-SKILL-010` Auto Router status: `FURTHER_TEST_CANDIDATE`

## Why Not `KEEP_FIXED`

The fixed baseline remains canonical for now, but the bounded Auto Router evidence is strong enough that `KEEP_FIXED` is too final as the evaluation status:

- first Auto Router experiment selected `openai/gpt-oss-120b`
- completion-budget retry selected `openai/gpt-oss-120b` again
- retry resolved the earlier `finish_reason=length` issue to `finish_reason=stop`
- retry actual cost `0.00053955` stayed below the fixed `qwen/qwen3.5-flash-02-23` baseline actual cost `0.00060359`
- cost delta versus fixed baseline remained favorable at `0.00006404` or `10.61%`

That means there is enough bounded evidence to justify more testing instead of freezing the evaluation at `KEEP_FIXED`.

## Why Not `MANUAL_REVIEW` As Final Status

`MANUAL_REVIEW` was appropriate for the first Auto Router experiment because:

- the first run ended with `finish_reason=length`
- that left completion adequacy unresolved

After the completion-budget retry:

- `finish_reason=stop` was captured
- the routed model remained stable
- the retry stayed under the bounded cost cap
- file-first artifacts, telemetry, and healthcheck ingestion all passed

So `MANUAL_REVIEW` still applies to individual experiment interpretation, but it is no longer the best final classification label for the overall `DOC-SKILL-010` Auto Router track. The better label is `FURTHER_TEST_CANDIDATE`.

## Why Not `AUTO_ROUTER_CONFIRMED` Yet

`AUTO_ROUTER_CONFIRMED` would still be too strong because the evidence is narrow:

- only one documentation skill has been tested
- only two bounded Auto Router calls exist for this skill
- the same routed model won both times, but that does not prove broader repeatability
- the experiment path is still separate from the fixed-model Auto-sparsam implementation plan
- no multi-session or operator-variance evidence exists yet
- no production-routing or canonical-routing review has been approved

## Additional Evidence Required Before Replacing The Fixed Baseline

Before replacing the fixed `qwen/qwen3.5-flash-02-23` baseline for `DOC-SKILL-010`, the project would still need:

- repeated bounded Auto Router runs for the same skill across more than one session
- evidence that the routed-model selection remains stable or beneficial under prompt variation
- evidence that the quality outcome remains acceptable without hidden truncation or drift
- a compact review that compares total cost, completion quality, and operator handling across repeated runs
- an explicit follow-up decision task that reviews whether the fixed-model Auto-sparsam plan should change

## Canonical Status For Now

- fixed-model Auto-sparsam remains canonical for `DOC-SKILL-010`
- Auto Router remains experiment-only
- no production routing is activated
- no canonical routing-table update is made
- no global OR approval is created

## Boundary Reminder

- this note classifies only the bounded Auto Router evidence for `DOC-SKILL-010`
- it does not replace the fixed-model Auto-sparsam implementation plan
- it does not activate production routing
- it does not update the canonical routing table
- it does not continue the separate `5.4` candidate phase

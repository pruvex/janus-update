# BACKLOG-119 Live Retest After Routing Fix

- Status: PASS
- Sequence:
  - GPT write: `mein bester freund, der korbinian elstorf wohnt in berlin`
  - Gemini write: `korbinians freundin heisst ylvie nordmann`
  - Fresh GPT recall: `wer ist korbinians freundin?`
- Providers/Models:
  - `openai / gpt-5.4-nano`
  - `gemini / gemini-3-flash-preview`
  - `openai / gpt-5.4-nano`
- Chat IDs:
  - `4188`
  - `4189`
  - `4190`
- Evidence JSON: `documentation/test-results/BACKLOG-119-live-retest-after-routing-fix-2026-07-02/BACKLOG-119_live_retest_after_routing_fix_api_evidence.json`

## Assertions

- GPT write accepted: True
- Gemini write accepted: True
- Korbinian contact exists: True
- Korbinian address is Berlin: True
- Korbinian contact contains `Freundin heisst Ylvie Nordmann`: True
- Fresh GPT recall answers Ylvie Nordmann: True
- Fresh GPT recall used `memory.read`: True

## Observed Pass Path

Fresh GPT recall answered:

```text
Korbinian hat als Freundin Ylvie Nordmann.
```

The live address-book row for `Korbinian Elstorf` now contains `Freundin heisst Ylvie Nordmann`, and backend log evidence shows the fresh recall chat executed through `memory.read` rather than drifting into `system.wikipedia_summary`.

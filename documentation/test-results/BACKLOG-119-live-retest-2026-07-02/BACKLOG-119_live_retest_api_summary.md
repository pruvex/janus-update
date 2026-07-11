# BACKLOG-119 Live Retest API Summary

- Status: FAIL
- Sequence:
  - GPT write: `mein bester freund, der nathan raimann wohnt in berlin`
  - Gemini write: `nathans freundin heisst elena`
  - Fresh GPT recall: `wer ist nathans freundin?`
- Providers/Models:
  - `openai / gpt-5.4-nano`
  - `gemini / gemini-3-flash-preview`
  - `openai / gpt-5.4-nano`
- Chat IDs:
  - `4164`
  - `4165`
  - `4166`
- Evidence JSON: `documentation/test-results/BACKLOG-119-live-retest-2026-07-02/BACKLOG-119_live_retest_api_evidence.json`

## Assertions

- GPT write accepted: True
- Gemini write accepted: True
- Nathan contact exists: True
- Nathan address is Berlin: True
- Nathan contact contains `Freundin heisst Elena`: True
- Fresh GPT recall answers Elena: False
- No new recall-turn memory created: True

## Observed Recall Failure

Fresh GPT recall answered:

```text
Ich kann dir das nicht zuverlaessig sagen: In den bereitgestellten Informationen steht nichts dazu, wer Nathans Freundin ist.
```

The live contact card is now correct, but the recall path still fails. Backend log evidence shows that chat `4166` was classified as ambiguous and forced into `system.wikipedia_summary`, which then failed with `No module named 'wikipedia'`, instead of answering from the now-correct contact/memory knowledge.

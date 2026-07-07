## OR Everyday Operator Registry Summary

Date: `2026-06-29`
Canonical state: `PASS`
Scope: compact operator-facing overview derived from the current bounded OR lane inventory

### Purpose

This summary is the thin operator-facing layer on top of the current validated everyday OR inventory.

It is for quick operational orientation:

- which bounded Janus skills currently offer `1 = Codex` and `2 = OR`
- which OR model or OR path is currently attached
- what the main boundary of that lane is

This is not production routing, not a routing-table activation, and not broad delegated authority.

### Current everyday `Codex / OR` lanes

| Skill | Lane / class | Visible operator choice | Current OR model / path | Main boundary |
| --- | --- | --- | --- | --- |
| `janus-executioner` | `execution_patch_candidate` | `1 = Codex`, `2 = OR` | `deepseek/deepseek-v4-flash` | proposal-first only; Codex still applies or rejects |
| `janus-debug` | `debug_hypothesis_review` | `1 = Codex`, `2 = OR` | `qwen/qwen3-coder-30b-a3b-instruct` | assist-only hypothesis review; no delegated local execution |
| `janus-test-pipeline` | `test_result_triage_review` | `1 = Codex`, `2 = OR` | `qwen/qwen3-coder-30b-a3b-instruct` | assist-only triage review; no delegated final PASS/release decision |
| `janus-spec-generator` | bounded structured spec draft | `1 = Codex`, `2 = OR` | `qwen/qwen3-coder-30b-a3b-instruct` | bounded draft only; Codex remains final writer and acceptance owner |
| `janus-feature-design` | bounded decision-summary draft | `1 = Codex`, `2 = OR` | `qwen/qwen3-coder-30b-a3b-instruct` | bounded draft only; Codex remains final product-decision owner |
| `janus-spec-normalizer` | bounded spec normalization lane | `1 = Codex`, `2 = OR` | `qwen/qwen3-coder-30b-a3b-instruct` | bounded normalization only; Codex remains final reviewer and local writer of any accepted normalized Spec |
| `janus-spec-to-task` | bounded task-compilation draft | `1 = Codex`, `2 = OR` | `qwen/qwen3-coder-30b-a3b-instruct` | bounded task draft only; Codex remains final task-artifact writer |
| `janus-task-breakdown` | bounded single-target handoff draft | `1 = Codex`, `2 = OR` | `qwen/qwen3-coder-30b-a3b-instruct` | bounded handoff draft only; Codex remains final handoff writer |
| `janus-preimplementation-check` | bounded precheck review | `1 = Codex`, `2 = OR` | `qwen/qwen3-coder-30b-a3b-instruct` | assist-only precheck recommendation; Codex remains final governance owner |
| `janus-spec-review` | bounded spec review recommendation | `1 = Codex`, `2 = OR` | `qwen/qwen3-coder-30b-a3b-instruct` | assist-only review recommendation; Codex remains final metadata writer |
| `janus-quickchange` | `quickchange_patch_review` | `1 = Codex`, `2 = OpenRouter` | `deepseek/deepseek-v4-flash` and other bounded quickchange OR candidates | review-first only; Codex remains final reviewer |
| `janus-quickchange` | `quickchange_write_apply` | `1 = Codex`, `2 = OpenRouter` | accepted-source bounded workspace-write evidence path | accepted-source-backed only; Codex remains diff reviewer and acceptance owner |
| `janus-documentation-update` | eligible mini `DOC-SKILL-*` rows | `1 = Codex`, `2 = OpenRouter` | fixed per eligible `DOC-SKILL` | documentation-skill-only lane, not a general Janus product skill lane |

### Hidden or partial lanes not currently eligible for the normal everyday `2 = OR` gate

- `janus-executioner` `execution_write_apply_candidate`
  - runtime visibility: `HIDDEN_PARTIAL_CANDIDATE`
  - meaning: accepted-source-backed deterministic apply helpers still exist, but the normal everyday operator gate must stay local-only until a later explicit visibility release says otherwise
- `janus-test-pipeline` `generator_review`
  - runtime visibility: `HIDDEN_INTERNAL_ONLY`
  - meaning: delegated deterministic generator helpers remain internal tooling and do not surface as a normal operator-facing `2 = OR` lane
- `janus-test-pipeline` `LIVE_TEST_EXECUTION` bounded local retest lane
  - meaning: even where a visible `2 = OR` choice is allowed for `local_bounded_retest`, the delegated worker still needs a valid bounded package, reviewable evidence bundle, and Codex-owned final accept/reject. Missing evidence or over-broad packages fail closed to reject-and-fallback rather than silently expanding OR authority.

### Fast reading

- If a lane says `assist-only`, OR may help analyze or classify, but Codex still owns the real decision.
- If a lane says `proposal-first`, OR may suggest a patch, but Codex still owns apply or reject.
- If a lane says `accepted-source-backed`, the delegated path depends on already accepted bounded source evidence and still does not bypass Codex acceptance.
- If a lane says `bounded draft`, OR may produce a controlled draft artifact, but Codex still owns every binding write or final product/process decision.

### What is not currently in scope

- no production routing
- no canonical routing-table update
- no broad delegated Git, release, or audit authority
- no claim that every Janus skill is OR-ready

### Source of truth

This summary is derived from:

- [or_everyday_lane_inventory_2026-06-24.md](/C:/KI/Janus-Projekt/documentation/codex/model-routing/or_everyday_lane_inventory_2026-06-24.md)

If a lane changes state, the central inventory stays authoritative and this summary should be refreshed from it.

### Conclusion

For the current bounded rollout scope, the main everyday operator-facing `Codex / OR` lanes are now available in one compact place across assist-only, proposal-first, and bounded-draft classes, while hidden internal-only or partial lanes stay explicitly local at the normal operator gate. The practical next step is no longer broad lane repair by default, but real everyday use of the proven visible gates and only targeted expansion where Codex quota burn remains high.

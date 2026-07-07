## OR Everyday Lane Inventory

Date: `2026-06-24`
Canonical state: `PASS`
Purpose: central inventory of operator-facing bounded OR lanes across Janus skills

### Status meanings

- `OR_READY`: visible operator gate and bounded everyday evidence already validated
- `BLOCKED`: intended candidate exists, but a real contract or implementation blocker prevents everyday use
- `LOCAL_ONLY`: no approved bounded OR lane is currently active
- `PARTIAL`: some OR-related path exists, but the everyday operator-facing lane is not yet fully validated

### Lane inventory

| Skill | Lane / class | Visible operator choice | Current status | OR model / label | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `janus-executioner` | `execution_patch_candidate` via productive Dev-workhorse entry | `1 = Codex`, `2 = OR` | `OR_READY` | `deepseek/deepseek-v4-flash` | [productive_dev_workhorse_everyday_entry_validation_2026-06-24.md](/C:/KI/Janus-Projekt/documentation/codex/model-routing/productive_dev_workhorse_everyday_entry_validation_2026-06-24.md) | Proposal-first only; Codex still owns apply/reject |
| `janus-executioner` | `execution_write_apply_candidate` via productive Dev-workhorse entry | `1 = Codex` only | `PARTIAL` | accepted-source delegated write candidate with deterministic local patch apply | [productive_dev_workhorse_everyday_entry_validation_2026-06-24.md](/C:/KI/Janus-Projekt/documentation/codex/model-routing/productive_dev_workhorse_everyday_entry_validation_2026-06-24.md) | Hidden partial candidate: runtime visibility is `HIDDEN_PARTIAL_CANDIDATE`, so the normal everyday `2 = OR` gate must stay suppressed even though bounded accepted-source helper paths still exist |
| `janus-debug` | `debug_hypothesis_review` | `1 = Codex`, `2 = OR` | `OR_READY` | `qwen/qwen3-coder-30b-a3b-instruct` | [debug_or_everyday_entry_validation_2026-06-24.md](/C:/KI/Janus-Projekt/documentation/codex/model-routing/debug_or_everyday_entry_validation_2026-06-24.md) | Assist-only hypothesis review; no delegated local execution |
| `janus-test-pipeline` | `test_result_triage_review` | `1 = Codex`, `2 = OR` | `OR_READY` | `qwen/qwen3-coder-30b-a3b-instruct` | [test_pipeline_triage_or_everyday_entry_validation_2026-06-24.md](/C:/KI/Janus-Projekt/documentation/codex/model-routing/test_pipeline_triage_or_everyday_entry_validation_2026-06-24.md) | Assist-only triage review; no delegated final PASS/release decision |
| `janus-quickchange` | `quickchange_patch_review` | `1 = Codex`, `2 = OpenRouter` | `OR_READY` | `deepseek/deepseek-v4-flash` and other bounded quickchange OR candidates | [quickchange_or_everyday_entry_blocker_2026-06-24.md](/C:/KI/Janus-Projekt/documentation/codex/model-routing/quickchange_or_everyday_entry_blocker_2026-06-24.md) | Shared dispatcher prompt gate restored; still bounded review-first only |
| `janus-quickchange` | `quickchange_write_apply` | `1 = Codex`, `2 = OpenRouter` | `OR_READY` | accepted-source bounded workspace-write evidence path | [quickchange_write_apply_everyday_entry_validation_result_2026-06-24.md](/C:/KI/Janus-Projekt/documentation/codex/model-routing/quickchange_write_apply_everyday_entry_validation_result_2026-06-24.md) | Prompt gate and accepted-source-backed delegated validation path both refreshed successfully in the current rollout |
| `janus-documentation-update` | mini fixed-OR documentation path for eligible `DOC-SKILL-*` rows | `1 = Codex`, `2 = OpenRouter` | `OR_READY` | fixed per eligible `DOC-SKILL` | [gpt54_mini_live_evidence_operator_recommendation_matrix_2026-06-23.md](/C:/KI/Janus-Projekt/documentation/codex/model-routing/gpt54_mini_live_evidence_operator_recommendation_matrix_2026-06-23.md) | Documentation-skill-only lane, not a general Janus product skill lane |
| `janus-test-pipeline` | `generator_review` | `1 = Codex` only | `PARTIAL` | `openai/gpt-oss-20b` via delegated intent / deterministic local execution | [generator_review_everyday_entry_validation_result_2026-06-24.md](/C:/KI/Janus-Projekt/documentation/codex/model-routing/generator_review_everyday_entry_validation_result_2026-06-24.md) | Hidden internal-only lane: runtime visibility is `HIDDEN_INTERNAL_ONLY`, so the delegated deterministic helper remains internal and does not surface as a normal everyday `2 = OR` choice |
| `janus-spec-normalizer` | bounded spec normalization lane | `1 = Codex`, `2 = OR` | `OR_READY` | `qwen/qwen3-coder-30b-a3b-instruct` | [documentation/ai/CURRENT_STATE.md](/C:/KI/Janus-Projekt/documentation/ai/CURRENT_STATE.md) | Live OR candidate and repeated live run already passed; skill is now visibly wired to the bounded normalizer runner |

### Current picture

#### Proven everyday OR lanes

- `janus-executioner`
- `janus-debug`
- `janus-test-pipeline` triage lane
- `janus-quickchange` `quickchange_patch_review`
- `janus-quickchange` `quickchange_write_apply`
- `janus-spec-normalizer`
- documentation mini fixed-OR lane for eligible `DOC-SKILL-*`

#### Blocked / not yet ready

- `janus-executioner` `execution_write_apply_candidate` (`HIDDEN_PARTIAL_CANDIDATE`)
- `janus-test-pipeline` `generator_review` (`HIDDEN_INTERNAL_ONLY`)


### Rollout pattern that is working

The successful lanes all follow the same bounded pattern:

- visible operator gate before execution
- strict allowlisted request package
- stale/broad package rejection as fail-closed behavior
- current-shape package regeneration when contracts evolve
- file-first artifact capture for delegated review lanes
- telemetry plus healthcheck ingestion
- visible actual-cost output after completion
- Codex-owned final validation and acceptance

### Recommended next rollout order

1. Build a thin user-facing registry/summary layer so the operator can see at a glance which skills currently offer:
   - `Codex only`
   - `Codex / OR`
   - `Blocked`

### Non-goals

- no production routing
- no canonical routing-table activation
- no broad delegated write authority
- no claim that all Janus skills are OR-ready

### Conclusion

The OR rollout is no longer just a single experiment. There is now a central, evidence-backed inventory showing which bounded Janus skill lanes already support real operator choice and which still need explicit follow-up work.

## OR Everyday Operator Registry Summary

Date: `2026-06-24`
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
| `janus-executioner` | `execution_write_apply_candidate` | `1 = Codex`, `2 = OR` | accepted-source delegated write candidate | bounded write-candidate only; no autonomous final apply |
| `janus-debug` | `debug_hypothesis_review` | `1 = Codex`, `2 = OR-Arbeitspferd` | `qwen/qwen3.5-flash-02-23` | assist-only hypothesis review; no delegated local execution |
| `janus-test-pipeline` | `test_result_triage_review` | `1 = Codex`, `2 = OR-Arbeitspferd` | `openai/gpt-oss-20b` | assist-only triage review; no delegated final PASS/release decision |
| `janus-test-pipeline` | `generator_review` | `1 = Codex`, `2 = OpenRouter` | delegated intent / deterministic local execution | deterministic local builder/executor/validator path; no broad write delegation |
| `janus-quickchange` | `quickchange_patch_review` | `1 = Codex`, `2 = OpenRouter` | `deepseek/deepseek-v4-flash` and other bounded quickchange OR candidates | review-first only; Codex remains final reviewer |
| `janus-quickchange` | `quickchange_write_apply` | `1 = Codex`, `2 = OpenRouter` | accepted-source bounded workspace-write evidence path | accepted-source-backed only; Codex remains diff reviewer and acceptance owner |
| `janus-documentation-update` | eligible mini `DOC-SKILL-*` rows | `1 = Codex`, `2 = OpenRouter` | fixed per eligible `DOC-SKILL` | documentation-skill-only lane, not a general Janus product skill lane |

### Fast reading

- If a lane says `assist-only`, OR may help analyze or classify, but Codex still owns the real decision.
- If a lane says `proposal-first`, OR may suggest a patch, but Codex still owns apply or reject.
- If a lane says `accepted-source-backed`, the delegated path depends on already accepted bounded source evidence and still does not bypass Codex acceptance.

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

For the current bounded rollout scope, the main everyday operator-facing `Codex / OR` lanes are now available in one compact place. The next step after this summary is not more lane repair by default, but deciding whether a user-facing UI/dashboard surface should mirror the same registry later.

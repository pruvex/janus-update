---
name: janus-spec-normalizer
description: Normalize and validate Janus Feature Specs into copy-safe, parser-safe Markdown. Use after a Janus Feature Spec draft exists and before spec review, dashboard ingestion, task compilation, implementation, or archival.
---

# Janus Spec Normalizer

## Overview

Transform one approved Janus Feature Spec draft into a final copy-safe Markdown block. Do not brainstorm, reinterpret decisions, add requirements, generate tasks, or implement.
This is primarily a ChatGPT-led mechanical cleanup skill. Codex normally consumes the normalized Spec rather than leading the normalizer step.

## Source Priority

Use only one draft Spec at a time. If the draft is missing, ambiguous, or conflicts with the locked decision source, block instead of guessing.
Ignore older drafts, rejected options, chat speculation, malformed prior outputs, and implementation suggestions.

## References

Read only when exact legacy wording is needed:

- `C:\KI\Janus-Projekt\documentation\prompts\3. SPEC GENERATOR NORMALIZER.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`

## Output Contract

Final answer must contain exactly one fenced markdown code block and nothing else.

Inside the code block:

- First line must be `# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3`.
- Required headings must use `#` or `##` exactly.
- Required structured fields must use `- Field: value`.
- Definition of Done items must use `- [ ]`.
- Routing fields must each occupy one physical line.
- Internal complexity fields must each occupy one physical line.
- No `BEGIN_SPEC_MARKDOWN` or `END_SPEC_MARKDOWN`.

## Hard Validation

Before final output, silently verify:

- exactly one draft Spec exists
- no text before or after the final code block
- required headings exist in the required order
- routing block matches the current contract exactly, or a legacy Spec remains validator-compatible
- routing values are allowed values
- structured fields are bullet key-value fields
- DoD items are checkboxes
- persistence is exactly `YES` or `NO` when that field is present
- complexity total equals the five dimensions
- routing values match internal complexity values
- no implementation detail, task list, API signature, DB schema, or code is present

If validation fails, correct the Spec before answering. If a product decision is missing or the draft is unclear, output one blocking question instead of a normalized Spec.

## Validator Script

When a Spec is saved to disk or available as a file, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-spec-normalizer\scripts\validate_feature_spec.py <path-to-spec.md>
```

Use the validator as a deterministic gate. Fix reported issues before routing to `janus-spec-review`.

## Tri-Modal Rollout Note

Global delegation vocabulary across Janus is now:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

This skill's bounded mechanical normalization lane is now wired through the shared manifest-backed `documentation/codex/model-routing/scripts/janus_delegate.py` entry. OpenRouter remains the recommended backend for this assist-only review slice; Cursor is visible as option `2` but is not the recommended backend here.

## Bounded Delegation Gate

For one bounded mechanical Spec-normalization slice, this skill now has the shared tri-modal operator gate:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

Binding runner:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_spec_normalizer_runner.py`

Current preferred OR candidate:

- `qwen/qwen3-coder-30b-a3b-instruct`

Use the shared delegate entry first:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py `
  --lane spec_normalizer_review `
  --task-id TASK-SN-001 `
  --workflow-id <WORKFLOW-ID> `
  --operator-choice prompt `
  --input-package-json development/openrouter-skill-tests/janus-spec-normalizer/spec_normalizer_input_package.json `
  --estimated-codex-saved-tokens 12000 `
  --estimated-delegation-overhead-tokens 4000
```

Boundaries:

- no delegated product-decision changes
- no delegated task generation
- no delegated authoritative Spec acceptance
- Codex remains the final reviewer and local writer of any accepted normalized Spec
- the bounded gate requires one input package json already bound to exactly one draft Spec

Current lane behavior:

- OpenRouter remains the recommended backend for this bounded assist-only normalization slice.
- Cursor is visible as option `2`, but not the recommended backend.
- The existing `codex_spec_normalizer_runner.py` remains the downstream OR helper planned by `janus_delegate.py`.
- Current shared-gate productive evidence shows this lane as the cheapest and most predictable OR default inside the Spec flow.

## Blocking Question Format

If normalization cannot proceed because a product decision is missing, output only:

```markdown
# BLOCKING QUESTIONS

Question:
<exactly one question>

Option A:
<concrete option>

Option B:
<concrete option>

Recommendation:
<short recommendation>
```

## Next Gate

After a normalized and validated Spec, recommend:

```text
NEXT_SKILL_HANDOFF
Target Skill: janus-spec-review
Canonical State: HANDOFF
Required Artifacts: normalized Feature Spec
Evidence Paths: validator output or N/A WITH REASON
Failure Code: N/A
Changed Files: <spec path or NONE>
Decision: Ready for janus-spec-review
Reason: Spec is normalized and parser-safe.
Copy Prompt: Use janus-spec-review on the normalized Spec.
```

When control moves from ChatGPT to Codex, output model/reasoning above exactly one compact fenced `text` block that contains only:

- `NEXT: janus-spec-review`
- the Spec path
- the draft source path or locked decision source
- one short note if a mechanical cleanup was needed

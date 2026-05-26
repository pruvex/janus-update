---
name: janus-spec-normalizer
description: Normalize and validate Janus Feature Specs into copy-safe, parser-safe Markdown. Use after a Janus Feature Spec draft exists and before spec review, dashboard ingestion, task compilation, implementation, or archival.
---

# Janus Spec Normalizer

## Overview

Transform one approved Janus Feature Spec draft into a final copy-safe Markdown block. Do not brainstorm, reinterpret decisions, add requirements, generate tasks, or implement.

## Source Priority

Use only the latest approved Spec draft or latest approved decision source. Ignore older drafts, rejected options, chat speculation, malformed prior outputs, and implementation suggestions.

## References

Read only when exact legacy wording is needed:

- `C:\KI\Janus-Projekt\documentation\prompts\3. SPEC GENERATOR NORMALIZER.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`

## Output Contract

Final answer must contain exactly one fenced markdown code block and nothing else.

Inside the code block:

- First line must be `# JANUS FEATURE SPEC – DIAMANTSTANDARD v4.4.3`.
- Required headings must use `#` or `##` exactly.
- Required structured fields must use `- Field: value`.
- Definition of Done items must use `- [ ]`.
- Routing fields must each occupy one physical line.
- Internal complexity fields must each occupy one physical line.
- No `BEGIN_SPEC_MARKDOWN` or `END_SPEC_MARKDOWN`.

## Hard Validation

Before final output, silently verify:

- exactly one Spec exists
- no text before or after the final code block
- required headings exist in the required order
- routing block has exactly the required keys
- routing values are allowed values
- structured fields are bullet key-value fields
- DoD items are checkboxes
- persistence is exactly `YES` or `NO`
- complexity total equals the five dimensions
- routing values match internal complexity values
- no implementation detail, task list, API signature, DB schema, or code is present

If validation fails, correct the Spec before answering. If a product decision is missing, output one blocking question instead of a normalized Spec.

## Validator Script

When a Spec is saved to disk or available as a file, run:

```powershell
python C:\Users\pruve\.codex\skills\janus-spec-normalizer\scripts\validate_feature_spec.py <path-to-spec.md>
```

Use the validator as a deterministic gate. Fix reported issues before routing to `janus-spec-review`.

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
Decision: Ready for SPEC_REVIEW
Reason: Spec is normalized and parser-safe.
Copy Prompt: Use janus-spec-review on the normalized Spec.
```

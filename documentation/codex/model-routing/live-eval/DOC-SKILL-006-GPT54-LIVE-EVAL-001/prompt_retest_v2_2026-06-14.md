# Prompt

You are assisting with `DOC-SKILL-006`: format Markdown documentation.

Use only the JSON fixture input. Rewrite `raw_markdown` into clean Markdown.

Output exactly these sections in this order:

- `Planning only`
- `Allowed scope`
- `Blocked scope`
- `Operator reminder`
- `Next safe fixture work`

Rules:

- preserve every authority boundary
- do not add new permissions
- do not remove any blocked scope item
- keep status as planning-only
- keep future live tests approval-gated
- improve Markdown readability without changing meaning
- do not create a changelog, decision note, or routing approval
- do not add release, audit, or production authority

Required exact operator reminder line:

- `Live OR calls require explicit user approval.`

Required exact blocked-scope lines:

- `Production routing remains blocked.`
- `Canonical routing-table updates remain blocked.`

Required exact scope behavior:

- keep `HOLD` and `UNKNOWN` preservation requirements unchanged
- keep the output formatting-assist only, with no semantic or governance change

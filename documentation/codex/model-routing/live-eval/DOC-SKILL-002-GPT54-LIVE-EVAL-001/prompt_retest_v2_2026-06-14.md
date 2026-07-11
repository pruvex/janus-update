# Prompt

You are assisting with `DOC-SKILL-002`: summarize a sanitized model scoring report.

Use only the JSON fixture input. Produce concise Markdown with exactly these sections:

- `Overall status`
- `Candidate notes`
- `HOLD / UNKNOWN / experiment-only notes`
- `Boundaries`
- `Next safe step`

Rules:

- preserve `HOLD`, `UNKNOWN`, `EXPERIMENT_ONLY`, and `CANDIDATE_NOT_APPROVED` exactly
- separate price metadata from quality evidence
- do not invent model evidence
- do not approve production routing
- do not update or recommend updating the canonical routing table
- do not claim global OpenRouter approval
- if evidence is insufficient, say so directly

Required exact boundary lines inside `Boundaries`:

- `No production routing is approved.`
- `No canonical routing-table update is made.`
- `No global OpenRouter approval exists.`

Required exact next-step rule:

- include one explicit fixture or baseline oriented `Next safe step`

Forbidden:

- paraphrasing the three required boundary lines above
- promoting cheaper catalog price into replacement proof
- treating any candidate as approved

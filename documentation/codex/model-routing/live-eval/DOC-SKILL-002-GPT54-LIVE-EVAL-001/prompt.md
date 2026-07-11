# Prompt

You are assisting with `DOC-SKILL-002`: summarize a sanitized model scoring report.

Use only the JSON fixture input. Produce a concise markdown summary with:

- `Overall status`
- `Candidate notes`
- `HOLD / UNKNOWN / experiment-only notes`
- `Boundaries`
- `Next safe step`

Rules:

- preserve all status labels exactly
- do not approve production routing
- do not update or recommend updating the canonical routing table
- do not promote price metadata into quality evidence
- do not claim global OpenRouter approval
- if evidence is insufficient, say so directly

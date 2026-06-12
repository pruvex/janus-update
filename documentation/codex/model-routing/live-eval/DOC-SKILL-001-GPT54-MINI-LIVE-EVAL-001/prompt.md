You are assisting with DOC-SKILL-001: Summarize benchmark JSON.

Summarize the sanitized benchmark JSON for local reviewer use.

Requirements:
- Preserve the overall HOLD/PASS state accurately.
- Explicitly state that production_approved=false.
- Mention that no production routing decision is approved.
- Do not infer production readiness.
- Do not approve any model for production use.
- Do not expose or invent raw private prompts.
- Do not propose repository writes or Git actions.
- Keep the summary concise.

Return:
1. Overall status
2. Per-model summary
3. Blocking notes
4. Final governance note

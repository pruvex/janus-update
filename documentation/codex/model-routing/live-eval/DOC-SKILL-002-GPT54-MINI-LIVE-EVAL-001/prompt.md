You are assisting with DOC-SKILL-002: Summarize model scoring report.

Summarize the sanitized model-scoring report for local reviewer use.

Requirements:
- Preserve HOLD, UNKNOWN, and disabled states accurately.
- Explicitly state that production_approved=false.
- Explicitly state that routing_approved=false.
- Do not approve routing.
- Do not override policy.
- Do not activate production use.
- Do not interpret or invent private evidence.
- Do not convert UNKNOWN or disabled entries to PASS.
- Keep the summary concise.

Return:
1. Overall status
2. Per-model scoring summary
3. Disabled/UNKNOWN/HOLD notes
4. Final governance note

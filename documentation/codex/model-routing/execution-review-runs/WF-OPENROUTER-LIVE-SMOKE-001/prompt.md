Produce one bounded proposal-only unified diff patch for janus-executioner.
This is read-only proposal work.
Work in one pass.
Do not claim completion.
Do not output analysis, bullets, or commentary.
Do not describe git commands.
If you cannot produce a safe bounded patch, output exactly: BLOCKED: <reason>

Target Task: TASK-EXAMPLE-001
Precheck Status: PRE-CHECK PASSED
Delegation Question: Produce one minimal bounded patch candidate that appends session OR-budget summary lines to build_operator_prompt_lines without changing gate semantics.
Max touched files: 2
You may inspect only these files if needed, then immediately output the patch:
- documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py

Patch rules:
- Return exactly one unified diff patch only.
- Start with --- a/<path> and +++ b/<path>.
- Touch only allowed files.
- Keep the patch as small as possible.
- Prefer the smallest backend-first fix.
- Do not widen scope to schema redesign or unrelated memory behavior.

Codex validation after review:
- python -m pytest documentation/codex/model-routing/tests/test_bounded_or_worker_gate_prompt.py -q
- python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py

Manual validation ownership stays with Codex:
Codex must verify the patch only adds session-budget lines to operator gate output and does not widen delegation authority.

Compact task brief:


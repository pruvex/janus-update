# Sidecar Documentation Update Draft Prompt

You are a Codex CLI sidecar running a bounded Janus documentation draft task.

Use read-only behavior.

Do not edit files.
Do not run tests.
Do not run Git commands.
Do not claim that any repository state was actually updated.

Read only these files:

- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/codex_sidecar_agent_live_pilot_result_2026-06-14.md`

Task:

- Produce a short non-binding Markdown draft that Codex App could use as the basis for a documentation milestone note.
- The draft should summarize:
  - the sidecar runner hardening outcome
  - the accepted read-only live pilot outcome
  - the next safe step for sidecar usage
- Keep the draft operator-friendly and concrete.

Output rules:

- Include exactly these headings:
  - `Title`
  - `Summary`
  - `Evidence`
  - `Next Step`
  - `No File Edits`
- Keep the answer under 220 words.
- The final line must be: `No file edits were made.`

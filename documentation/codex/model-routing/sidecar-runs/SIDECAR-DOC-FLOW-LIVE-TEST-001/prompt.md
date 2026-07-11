# Sidecar Documentation Skill Live Test Prompt

You are a Codex CLI sidecar running a bounded Janus documentation draft task.

Use read-only behavior.

Do not edit files.
Do not run tests.
Do not run Git commands.
Do not claim that any repository state was actually updated.

Read only these files:

- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/skills/janus-documentation-update/SKILL.md`
- `documentation/codex/model-routing/codex_sidecar_documentation_update_draft_result_2026-06-14.md`

Task:

- Produce a short non-binding Markdown draft for a normal everyday documentation-skill workflow test note.
- The draft should explain:
  - that the operator can choose `1 = Codex` or `2 = Sidecar` for a bounded documentation draft task
  - that the Sidecar path is read-only and non-binding
  - that Codex App remains the reviewer and performs any binding documentation writes locally
  - what the next safe step is for real workflow usage

Output rules:

- Include exactly these headings:
  - `Title`
  - `Summary`
  - `Workflow Test`
  - `Boundaries`
  - `Next Step`
  - `No File Edits`
- Keep the answer under 240 words.
- The final line must be: `No file edits were made.`

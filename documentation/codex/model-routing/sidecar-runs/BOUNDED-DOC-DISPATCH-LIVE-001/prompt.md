# Sidecar Documentation Skill Live Test Prompt Variant

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

- Produce a short non-binding Markdown draft for a documentation workflow note that explains:
  - the operator can choose `1 = Codex` or `2 = Sidecar`
  - the Sidecar path is read-only and for bounded drafts only
  - Codex App remains the reviewer and performs any binding documentation writes locally
  - the next safe step is to review the draft before any local documentation update

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

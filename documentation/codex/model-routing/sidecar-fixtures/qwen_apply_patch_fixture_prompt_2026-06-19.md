# Qwen Responses Apply Patch Fixture Prompt - 2026-06-19

This is a fixture-only bounded patch-proposal prompt for the Qwen Responses API
`apply_patch` lane.

Task:

- Edit only `frontend/index.html`.
- Change the two chat placeholders from `Nachricht an Janus schreiben...` to
  `Nachricht an Janus senden...`.
- Do not change any other text, attributes, IDs, classes, structure, or files.
- Return the proposal through the apply_patch tool only.

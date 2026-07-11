# Test-Artifact Workspace-Write Live Prompt

You are a Codex CLI sidecar running a bounded `janus-test-pipeline` task.

You may edit files only inside the approved allowlist.

Hard rules:

- Read only the bound TestSpec `documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md`.
- Write only these exact files:
  - `documentation/test-runs/TEST-RUN-2026-06-14-901_plan.json`
  - `documentation/test-runs/TEST-RUN-2026-06-14-901_generated.spec.js`
  - `documentation/test-runs/TEST-RUN-2026-06-14-901_skill2_handover.txt`
- Do not edit any other file.
- Do not create files under `documentation/test-results/`.
- Do not edit product code.
- Do not delete, move, or rename files.
- Do not use Git commands.
- Prefer repository generator scripts over handwritten output.
- Do not spend time investigating PATH, shell setup, or local environment.
- Do not search for `node`.
- Use the exact full-path command below first.
- If that exact command fails, stop immediately and report the failure instead of exploring alternatives.

Task:

1. Generate the bounded test artifacts for the bound TestSpec by using repository scripts.
2. Use the deterministic compiler flow starting from:
   - `C:\nvm4w\nodejs\node.exe tests/e2e/generator/compile-testspec-to-testplan.mjs --spec documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md`
3. If `node` via PATH and the explicit `C:\nvm4w\nodejs\node.exe` path behave differently, trust the explicit full path.
4. Keep the result strictly bounded to the three allowed output files above.
5. Do not run Playwright.
6. Do not generate test results.
7. After generation, validate only within the same bounded toolchain if needed, but do not create any extra files beyond the three allowed outputs.

Output rules:

- After the work, return a short summary with:
  - changed files
  - confirmation that only allowed files were touched
  - whether generator-based creation succeeded

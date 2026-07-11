# Isolated Aider Worker Standard

This is the standard Dev-side shape for bounded Aider/OpenRouter worker runs that still preserve the visible operator choice:

- `1 = Codex`
- `2 = OR`

The runner lives at:

- `documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py`

## Standard flow

1. Codex prepares one bounded input package JSON.
2. Prompt mode shows the operator gate.
3. If the operator chooses `1`, the task stays local to Codex.
4. If the operator chooses `2`, the runner:
   - creates a disposable temp workspace outside the repo root
   - copies only the declared workspace files
   - runs pre-checks
   - runs Aider on the bounded file set
   - runs post-checks
   - rejects scope drift or repo-root side effects
   - copies back only the declared editable files
5. Codex reviews and either accepts or hardens the result.

## Example commands

Prompt gate:

```powershell
python documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py `
  --task-label "Fix precheck prompt token mismatch" `
  --normal-target-model "5.4 medium" `
  --operator-choice prompt `
  --workflow-id ISO-AIDER-PRECHECK-001 `
  --input-package-json development/openrouter-skill-tests/janus-worker-aider-real-helper-poc/worker_package.json
```

Codex branch:

```powershell
python documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py `
  --task-label "Fix precheck prompt token mismatch" `
  --normal-target-model "5.4 medium" `
  --operator-choice local `
  --workflow-id ISO-AIDER-PRECHECK-001 `
  --input-package-json development/openrouter-skill-tests/janus-worker-aider-real-helper-poc/worker_package.json
```

OR branch:

```powershell
python documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py `
  --task-label "Fix precheck prompt token mismatch" `
  --normal-target-model "5.4 medium" `
  --operator-choice 2 `
  --workflow-id ISO-AIDER-PRECHECK-001 `
  --input-package-json development/openrouter-skill-tests/janus-worker-aider-real-helper-poc/worker_package.json
```

## Boundaries

- no repo-root execution
- no Git authority
- no release authority
- no broad file access
- Codex remains acceptance and hardening owner

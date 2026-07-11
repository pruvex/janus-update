# OR Task Budget Profiles Result - 2026-06-19

Status: PASS / TASK-CLASS BUDGETING ENABLED / FIXTURE-VALIDATED

## Summary

The direct OpenRouter runner no longer assumes that one tiny quickchange budget must apply to every future OR worker class.

Instead, it now loads task-class-specific budget profiles from:

- `documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json`

## What Changed

- `openrouter_direct_quickchange_patch_runner.py` now resolves a budget profile from `task_class`.
- If no explicit `--cost-cap` override is given, the runner uses the profile's configured `per_call_cap_usd`.
- The bounded dispatcher now forwards `task_class` into the direct OR runner.
- A new governance note documents the profile set and why a global tiny cap is misleading for larger bounded OR tasks.

## Profiles

| Profile | Per-call cap | Session cap |
| --- | ---: | ---: |
| `quickchange_patch_review` | `0.002` | `0.006` |
| `documentation_draft` | `0.01` | `0.03` |
| `debug_hypothesis_review` | `0.03` | `0.09` |
| `test_result_triage_review` | `0.03` | `0.09` |
| `execution_patch_candidate` | `0.05` | `0.15` |
| `execution_write_apply_candidate` | `0.10` | `0.30` |

## Validation

Syntax:

```powershell
python -m py_compile documentation\codex\model-routing\scripts\openrouter_direct_quickchange_patch_runner.py documentation\codex\model-routing\scripts\codex_bounded_delegation_dispatcher.py
```

Result: PASS

Quickchange profile fixture:

- workflow: `DIRECT-OR-BUDGET-QUICKCHANGE-001`
- task class: `quickchange_patch_review`
- estimated OR cost: `0.000250000`
- validation: PASS

Execution profile fixture:

- workflow: `DIRECT-OR-BUDGET-EXECUTION-001`
- task class: `execution_patch_candidate`
- estimated OR cost: `0.020000000`
- validation: PASS

This second fixture is the key proof point: the runner no longer rejects a bounded larger-class estimate simply because it exceeds the old quickchange-only `0.0020` cap.

## Interpretation

This does not yet add relative economics ranking against Codex.

It does remove one major false-negative source from future model search and bounded OR rollout:

- a model can now be acceptable for a larger bounded task even when it would have been blocked by the old quickchange ceiling

## Next Safe Step

Extend the same budget-profile logic into the next bounded direct OR consumer class, then add a second gate that compares expected OR spend against the expected Codex-equivalent path rather than relying on absolute caps alone.

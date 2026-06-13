# Expected Reference Summary

## Overall status

The scoring report remains HOLD overall. `production_approved=false` and `routing_approved=false` remain binding.

## Per-model scoring summary

- model_alpha: PASS scoring evidence, but routing_state remains HOLD and repeatability confirmation is still required before any routing discussion.
- model_beta: UNKNOWN with `disabled=true`. It must not be scored as PASS, and its disabled state must be preserved.
- model_gamma: HOLD. It has partial preservation of disabled-state wording and no production activation is allowed.

## Disabled/UNKNOWN/HOLD notes

- HOLD must not be upgraded to PASS at the overall level.
- UNKNOWN must remain UNKNOWN for model_beta.
- `disabled=true` must remain binding for model_beta.
- PASS scoring evidence must not imply routing approval or production readiness.
- No routing approval, policy override, production activation, or private evidence interpretation is allowed.

## Final governance note

This summary is for local reviewer use only. It does not approve routing, does not activate production use, does not override policy, and does not authorize interpretation of private evidence.

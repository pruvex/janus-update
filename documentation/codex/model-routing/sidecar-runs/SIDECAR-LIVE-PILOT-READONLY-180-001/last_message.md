## Result

The first real sidecar pilot should favor `janus-documentation-update`, not `janus-test-pipeline`.

## Recommended Pilot

Use `janus-documentation-update` as a read-only, non-binding draft pilot.

## Why

The execution plan lists documentation work as a strong first candidate and frames the next step as a harmless dry-run against documentation or a test-plan fixture. The delegation matrix is more specific: it marks `janus-documentation-update` as `SIDECAR_ALLOWED` for drafts, while `janus-test-pipeline` is only `SIDECAR_ASSIST_ONLY` at first. It also explicitly names Pilot 1 as `janus-documentation-update` with read-only sandbox and non-binding output. That makes it the lower-risk and more aligned first live pilot.

## Risks

`janus-documentation-update` still has a boundary risk: the sidecar must stay away from binding state updates like `CURRENT_STATE`, registries, backlog moves, or final documentation completion. `janus-test-pipeline` is close behind, but it has a slightly weaker trust posture because executable tests, result validation, and PASS/FAIL routing must remain with the main Codex App flow.

## No File Edits

This is a short, non-binding review based only on the two requested files and does not propose any routing, production, Git, release, or Janus-state change.

No file edits were made.
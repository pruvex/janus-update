TASK-BACKLOG-103
- Source Spec: `documentation/SPEC/backlog_BACKLOG-103_deepdive_ux_information_architecture_cleanup.md`
- Backlog Item: `BACKLOG-103`
- Feature: DeepDive UX Information Architecture Cleanup
- Generated At: 2026-06-05

## Generated Tasks

### TASK-BACKLOG-103.1 Rebuild the DeepDive opening state into a compact two-stage management surface
- Ziel:
  - Refactor the existing DeepDive modal so it opens as a calm, dashboard-compact management view and does not show request/detail density until the user actively selects a cost source.
- Scope:
  - Touch only the existing DeepDive modal render flow, visible hierarchy, default state behavior, and current supporting markup/style hooks needed to present a true two-stage UX on the existing surface.
- Files:
  - `frontend/js/cost-visualizer.js`
  - `frontend/index.html`
  - `frontend/src/styles.css`
- Steps:
  1. Rework the initial DeepDive layout so the first visible area prioritizes total cost, savings, budget context, and main provider/model drivers.
  2. Keep detail panels closed, hidden, or visually inactive by default until a cost source is explicitly selected.
  3. Make the first detail navigation flow through cost sources rather than dropping users directly into request-level detail.
  4. Preserve truthful partial-data and empty-state behavior while keeping the opening view visually quiet.
- Acceptance Criteria:
  - The first DeepDive view reads as a compact management surface instead of an immediate request/detail screen.
  - The opening view visibly prioritizes costs, savings, budget context, and key drivers above details.
  - No request-level detail is shown as the default first state unless the user actively selected a cost source.
  - Existing DeepDive entrypoint and one-surface behavior remain intact.
- Tests:
  - `node --check frontend/js/cost-visualizer.js`
  - `npx playwright test tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js --headed --workers=1 --reporter=list`
- Model: 5.4
- Reason:
  - Existing-surface UX restructuring with meaningful visible hierarchy changes but no new architecture.

### TASK-BACKLOG-103.2 Reduce the lower DeepDive detail layer to user-meaningful information only
- Ziel:
  - Remove or compress low-value detail blocks so the lower layer supports user understanding instead of drifting back into a logging/diagnostic surface.
- Scope:
  - Reduce only currently visible DeepDive detail density and wording inside the existing modal. Do not introduce a new developer surface or expand backend tracking.
- Files:
  - `frontend/js/cost-visualizer.js`
  - `frontend/src/styles.css`
- Steps:
  1. Review the current lower detail sections and identify which visible blocks feel diagnostic rather than user-meaningful.
  2. Remove, merge, or compress those blocks so the reduced detail layer still explains cost origin without overwhelming users.
  3. Keep the compact trust hint separate from the lower detail area so warnings do not re-fragment the first view.
  4. Preserve enough detail for users to follow relevant cost sources and selected requests when they intentionally drill down.
- Acceptance Criteria:
  - The lower DeepDive layer contains less visible diagnostic density than the current implementation.
  - Reduced details still allow users to understand where relevant costs come from after drilldown.
  - The UI no longer feels like a developer-facing logging surface in the lower section.
  - No new backend or debug-log dependencies are introduced by this task.
- Tests:
  - `node --check frontend/js/cost-visualizer.js`
  - `npx playwright test tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js --headed --workers=1 --reporter=list`
- Model: 5.4
- Reason:
  - Still bounded to one existing frontend surface, but it changes visible detail scope and user comprehension.

### TASK-BACKLOG-103.3 Add focused regression coverage for the two-stage DeepDive UX contract
- Ziel:
  - Lock in the new opening hierarchy and reduced-on-demand detail behavior so future changes do not quietly reintroduce cluttered default states.
- Scope:
  - Extend only the smallest existing UI smoke surface that already guards the DeepDive modal behavior.
- Files:
  - `tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js`
  - `frontend/js/cost-visualizer.js`
- Steps:
  1. Add smoke assertions for the compact opening state and the absence of default request/detail density.
  2. Add assertions that details appear only after selecting a cost source.
  3. Add checks that the trust hint stays compact and separate from the lower detail layer.
- Acceptance Criteria:
  - A smoke test fails if the DeepDive reverts to showing request/detail density as the default first state.
  - A smoke test fails if the first drilldown path skips cost sources and jumps directly into request-heavy detail.
  - A smoke test fails if the compact trust hint regresses into a noisy multi-warning first view.
- Tests:
  - `npx playwright test tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js --headed --workers=1 --reporter=list`
- Model: 5.4
- Reason:
  - Focused UX regression guard on one existing evidence surface.

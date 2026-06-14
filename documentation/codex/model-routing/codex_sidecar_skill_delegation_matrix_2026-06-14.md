# Codex Sidecar Skill Delegation Matrix - 2026-06-14

Status: INITIAL MATRIX WITH VALIDATED READ-ONLY DOCUMENTATION DRAFT PATH

## Purpose

This matrix separates full skill authority from delegable work chunks. A sidecar model can assist with bounded work, but Codex App remains the operator, reviewer, and final decision-maker.

## Delegation Levels

| level | meaning |
| --- | --- |
| `SIDECAR_ALLOWED` | A sidecar agent may run a bounded Codex CLI task and produce artifacts or a patch for Codex App review. |
| `SIDECAR_ASSIST_ONLY` | A sidecar may produce hypotheses, drafts, or advisory notes only; Codex App applies any changes locally. |
| `CODEX_APP_ONLY` | Keep in the main Codex App session because the task is too authority-heavy, stateful, private, or release-critical. |
| `HUMAN_APPROVAL_REQUIRED` | User approval is required before any sidecar execution. |

## Initial Skill Matrix

| Janus skill | recommended sidecar level | good sidecar work | Codex App must retain |
| --- | --- | --- | --- |
| `janus-documentation-update` | `SIDECAR_ALLOWED` for read-only drafts, `CODEX_APP_ONLY` for binding state writes | changelog drafts, handoff drafts, documentation summaries, non-binding milestone notes | `CURRENT_STATE`, registries, Backlog moves, changelog acceptance, final documentation completion |
| `janus-test-pipeline` | `SIDECAR_ASSIST_ONLY` first | test plan drafts, test case suggestions, result triage drafts, expected assertion ideas | writing executable tests, running tests, validating TestResult JSON, routing PASS/FAIL |
| `janus-debug` | `SIDECAR_ASSIST_ONLY` first | redacted log summaries, root-cause hypotheses, fix options, risk lists | local reproduction, source inspection requiring private context, fix execution, blocker classification |
| `janus-executioner` | `SIDECAR_ASSIST_ONLY` until proven | patch proposals, implementation plans, small diff drafts from bounded artifacts | applying patches, resolving conflicts, running tests, deciding implementation PASS |
| `janus-final-audit` | `CODEX_APP_ONLY` | none for final decision; optional sidecar may draft a checklist only after explicit approval | audit decision, severity, release gate, PASS/BLOCKED |
| `janus-git-governance` | `CODEX_APP_ONLY` | none | staging, commit, push, tag, merge, branch safety |
| `janus-build-release` | `CODEX_APP_ONLY` | optional release-note wording only after build evidence exists | build, package, release assets, versioning, publish gates |
| `janus-skill-router` | `CODEX_APP_ONLY` | none initially | routing, model gate, skill selection |
| `janus-backlog-intake` | `SIDECAR_ASSIST_ONLY` | first-pass issue wording and acceptance criteria drafts | final backlog item status, priority, routing |
| `janus-feature-design` | `SIDECAR_ASSIST_ONLY` | alternative phrasing, option lists, risk prompts | product decision capture and final decision summary |

## Default Gate Policy

Offer sidecar choice when all are true:

- the skill has `SIDECAR_ALLOWED` or `SIDECAR_ASSIST_ONLY`
- a bounded prompt package can be produced
- private or secret data can be excluded or summarized safely
- the sidecar can run in `read-only` or `workspace-write` sandbox
- Codex App has a clear validation step after the sidecar result

Do not offer sidecar choice when any are true:

- release, Git, or final-audit authority is the actual task
- raw secrets, credentials, private logs, or local databases would be sent unnecessarily
- the task requires broad unsupervised repo edits
- there is no clear post-sidecar validation path

## First Recommended Pilot

Pilot 1:

- skill: `janus-documentation-update`
- mode: `SIDECAR_ALLOWED`
- sandbox: `read-only`
- output: non-binding documentation draft only
- current evidence: validated live read-only pilot plus validated workflow-like draft run

Pilot 2:

- skill: `janus-test-pipeline`
- mode: `SIDECAR_ASSIST_ONLY`
- sandbox: `read-only`
- output: test-plan draft or triage note only

Pilot 3:

- skill: `janus-executioner`
- mode: `SIDECAR_ASSIST_ONLY`
- sandbox: `workspace-write`
- output: patch proposal in a bounded branch/worktree only after preimplementation evidence exists

## Parallel Agent Direction

Parallel sidecars are plausible later, but only after the single-sidecar path proves:

- command capture is reliable
- output summaries are structured
- sidecar artifacts are isolated
- duplicate or conflicting edits are detected
- Codex App can merge or reject sidecar results cleanly

Until then, use one sidecar per approved task.

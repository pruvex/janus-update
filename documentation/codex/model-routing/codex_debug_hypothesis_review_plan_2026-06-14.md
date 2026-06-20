# Codex Debug Hypothesis Review Plan - 2026-06-14

Status: FIRST NEXT-CLASS PLAN AFTER THE WORKFLOW-READY BOUNDED PACKAGE

## Purpose

This artifact defines the first bounded delegation expansion class after the accepted package:

- `documentation_draft`
- `quickchange_patch_review`
- `generator_review`

The new class is:

- `debug_hypothesis_review`

Its goal is to let the operator choose whether a bounded debug-analysis step should stay in Codex or be delegated as a strictly assist-only hypothesis review.

## Scope

Owning skill:

- `janus-debug`

Allowed delegation mode:

- `SIDECAR_ASSIST_ONLY`

Not allowed:

- no delegated local command execution
- no delegated test execution
- no delegated acceptance decision
- no delegated final fix claim
- no raw secret exposure

## Operator Choice Model

The operator-facing choice should stay aligned with the existing shared bounded model:

- `1 = Codex`
- `2 = Delegated`

This class should only be offered when all are true:

- a bounded debug package exists
- logs or error snippets can be redacted safely
- the task is asking for hypotheses, clustering, or likely causes
- Codex still owns reproduction, validation, and final next-step selection

This class should not be offered when any are true:

- secrets cannot be safely removed
- the request is really asking for a live fix, not a hypothesis review
- the failure requires local runtime inspection that cannot be summarized safely
- the result would be used as final audit or release evidence

## Required Input Package

The delegated hypothesis review should receive only a compact debug package:

- workflow or task label
- bound skill context
- expected behavior
- actual behavior
- failure code if available
- 1 to 3 redacted evidence snippets
- changed files or `N/A`
- current iteration number
- explicit question for the delegate

Optional:

- prior failed hypothesis summary
- likely subsystem tag
- local verifier candidates

## Secret Redaction Gate

Before any delegated review:

- remove tokens, cookies, bearer headers, secrets, API keys, and raw credentials
- replace sensitive values with stable placeholders where needed
- keep only non-reconstructable fingerprints or structural hints

If safe redaction is not possible:

- do not offer delegated mode
- route to `1 = Codex`

## Delegated Output Contract

The delegated result should be normalized into this bounded structure:

```text
DEBUG_HYPOTHESIS_REVIEW
Status: PASS | WEAK_SIGNAL | BLOCKED
Primary Failure Code:
Likely Subsystem:
Hypothesis 1:
Hypothesis 1 Confidence:
Hypothesis 1 Evidence:
Hypothesis 2:
Hypothesis 2 Confidence:
Hypothesis 2 Evidence:
Hypothesis 3:
Hypothesis 3 Confidence:
Hypothesis 3 Evidence:
Suggested Local Verifiers:
Instrumentation Suggestion:
Escalation Trigger:
Redaction Check: PASS | FAIL
Notes:
```

Rules:

- maximum 3 hypotheses
- each hypothesis must point to an evidence hint, not just intuition
- confidence must be coarse only: `LOW`, `MEDIUM`, or `HIGH`
- instrumentation suggestion is review-only, never auto-applied

## Codex Validation Flow

After a delegated review returns:

1. Verify the redaction check and bounded structure.
2. Reject the result if it contains secrets or unbounded instructions.
3. Compare hypotheses against the local debug package.
4. Select one of:
   - `ACCEPT_FOR_LOCAL_DEBUG`
   - `ACCEPT_WITH_MANUAL_REVIEW`
   - `REJECT_AND_FALLBACK_TO_CODEX`
5. If accepted, Codex chooses the next local verifier or next debug iteration.

## Fallback Rules

Fallback to Codex-only immediately when:

- the delegated output is vague or contradictory
- no evidence-linked hypothesis is present
- the result suggests unsafe or broad changes
- redaction confidence is low
- the current iteration is too stateful for bounded external review

Fallback outcome:

- delegated result may still be stored as rejected evidence
- Codex continues locally from the same debug package

## Minimal Artifact Plan

The first implementation slice for this class should create:

- one debug hypothesis review helper or dispatcher branch
- one compact prompt/package builder for redacted debug inputs
- one normalized result artifact
- one operator summary artifact

Suggested run artifact family:

- `documentation/codex/model-routing/debug-review-runs/<WORKFLOW_ID>/`

Suggested core files:

- `input_package.json`
- `delegated_result.md`
- `validation_summary.json`
- `operator_summary.json`

## Evidence Requirements Before Everyday Use

Required acceptance evidence:

- 3 accepted bounded assist runs across distinct debug situations
- 1 explicit rejection/fallback example
- 0 redaction failures
- 0 cases where delegated output is mistaken for final fix evidence

Suggested first evidence types:

- one provider/runtime mismatch
- one flaky test/result interpretation case
- one frontend/backend expected-vs-actual mismatch

## Non-Goals

- no production routing
- no canonical routing-table update
- no sidecar write authority
- no automatic patch apply
- no delegated final debug decision
- no release or audit authority transfer

## Recommended Next Build Step

Implement a bounded dispatcher/helper path for `debug_hypothesis_review` that only packages redacted local evidence, returns a normalized hypothesis summary, and forces Codex-owned validation plus fallback handling.

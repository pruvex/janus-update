# Codex Test Result Triage Review Plan - 2026-06-14

Status: SECOND ASSIST-ONLY CLASS PLAN AFTER DEBUG HYPOTHESIS REVIEW

## Purpose

This artifact defines the next bounded delegation expansion class after:

- `documentation_draft`
- `quickchange_patch_review`
- `generator_review`
- `debug_hypothesis_review`

The new class is:

- `test_result_triage_review`

Its goal is to let the operator choose whether a bounded test-result interpretation step should stay in Codex or be delegated as a strictly assist-only triage review.

## Scope

Owning skill:

- `janus-test-pipeline`

Allowed delegation mode:

- `SIDECAR_ASSIST_ONLY`

Not allowed:

- no delegated live test execution
- no delegated runner generation
- no delegated result JSON modification
- no delegated product-fix decision
- no delegated PASS or release-readiness decision

## Operator Choice Model

The operator-facing choice stays aligned with the shared bounded model:

- `1 = Codex`
- `2 = Delegated`

Offer the operator choice only when all are true:

- one bounded `TEST_RUN_ID` bundle is selected
- result JSON or equivalent evidence already exists locally
- the task is asking for triage, clustering, or likely classification
- Codex still owns final PASS/FAIL, rerun, Backlog, and routing decisions

Do not offer delegated mode when any are true:

- live execution or rerun is the actual next step
- evidence is incomplete or contradictory enough that raw local inspection is required first
- the task is really asking for implementation or final audit
- secrets, auth data, or provider internals cannot be safely summarized

## Required Input Package

The delegated triage review should receive only a compact test-result package:

- workflow or task label
- bound skill context
- `TEST_RUN_ID`
- bound TestSpec/TestPlan/TestResult paths if available
- result outcome summary
- 1 to 3 redacted failing evidence snippets
- current classification question
- candidate blocker category if already suspected
- redaction-ready flag

Optional:

- prior triage summary
- related Backlog reference
- expected rerun target

## Secret And Noise Reduction Gate

Before any delegated review:

- strip credentials, tokens, cookies, Authorization data, and provider secrets
- reduce raw output to the minimum snippets needed for classification
- keep only one bounded failing slice or one coherent failure cluster

If safe reduction is not possible:

- do not offer delegated mode
- route to `1 = Codex`

## Delegated Output Contract

The delegated result should be normalized into this bounded structure:

```text
TEST_RESULT_TRIAGE_REVIEW
Status: PASS | WEAK_SIGNAL | BLOCKED
TEST_RUN_ID:
Primary Outcome:
Likely Classification:
Likely Subsystem:
Finding Cluster 1:
Finding Cluster 1 Confidence:
Finding Cluster 1 Evidence:
Finding Cluster 2:
Finding Cluster 2 Confidence:
Finding Cluster 2 Evidence:
Suggested Next Local Verifiers:
Suggested Routing:
Escalation Trigger:
Redaction Check: PASS | FAIL
Notes:
```

Rules:

- maximum 2 clusters for the first slice
- each cluster must point to a concrete evidence hint
- confidence must be coarse only: `LOW`, `MEDIUM`, or `HIGH`
- suggested routing is advisory only

## Expected Classification Envelope

The delegated result may suggest only these bounded categories:

- `PRODUCT_BUG`
- `SPEC_GAP`
- `TEST_BUG`
- `INFRA_BLOCKER`
- `PROVIDER_BLOCKER`
- `AUTH_BLOCKER`
- `DUPLICATE`
- `NOT_REPRODUCIBLE`

It may not decide release readiness, implementation scope, or final Backlog state.

## Codex Validation Flow

After a delegated triage review returns:

1. Verify the redaction check and bounded structure.
2. Reject the result if it contains secrets, broad instructions, or unsupported categories.
3. Compare clusters and suggested classification against the local result bundle.
4. Select one of:
   - `ACCEPT_FOR_LOCAL_TRIAGE`
   - `ACCEPT_WITH_MANUAL_REVIEW`
   - `REJECT_AND_FALLBACK_TO_CODEX`
5. If accepted, Codex chooses the real classification, rerun route, or Backlog handoff.

## Fallback Rules

Fallback to Codex-only immediately when:

- the delegated output is vague, contradictory, or over-broad
- no evidence-linked cluster is present
- suggested routing conflicts with the bound mode
- classification depends on missing raw local evidence
- the result tries to act like a final test audit

Fallback outcome:

- delegated output may still be stored as rejected evidence
- Codex continues from the same local test-result bundle

## Minimal Artifact Plan

The first implementation slice for this class should create:

- one triage review helper or dispatcher branch
- one compact package builder for redacted test-result inputs
- one normalized triage result artifact
- one operator summary artifact

Suggested run artifact family:

- `documentation/codex/model-routing/test-triage-runs/<WORKFLOW_ID>/`

Suggested core files:

- `input_package.json`
- `delegated_result.md`
- `validation_summary.json`
- `operator_summary.json`

## Evidence Requirements Before Everyday Use

Required acceptance evidence:

- 3 accepted bounded assist runs across distinct result-bundle situations
- 1 explicit rejection/fallback example
- 0 redaction failures
- 0 cases where delegated output is mistaken for final audit or release evidence

Suggested first evidence types:

- one infra-blocked run
- one likely test-bug or oracle mismatch
- one likely product-bug result bundle

## Non-Goals

- no production routing
- no canonical routing-table update
- no sidecar write authority
- no result JSON mutation
- no delegated final PASS decision
- no release-readiness authority transfer

## Recommended Next Build Step

Implement a bounded dispatcher/helper path for `test_result_triage_review` that only packages redacted local result evidence, returns a normalized triage summary, and forces Codex-owned validation, rerun, and routing decisions.

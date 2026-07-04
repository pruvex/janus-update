# OpenRouter MCP Pre-Run Research Helper Workflow Note - 2026-07-03

Status: IMPLEMENTED / DEV INFRA ONLY / OPTIONAL PRE-RUN HELPER

## Purpose

This note defines the first bounded workflow placement for the optional OpenRouter MCP research helper inside our existing Codex-to-OR process.

It is intentionally informational only.

It does not replace:

- the bounded local executor
- the skill-level operator gate
- Codex review and acceptance authority
- the normal OpenRouter API path for actual live OR execution

## Workflow Placement

The helper belongs before a live OR candidate test.

Recommended sequence:

1. identify the pending delegated work class
   - examples: executor fleissarbeit, test-run support, debug fleissarbeit, docs fleissarbeit
2. decide whether an optional live MCP research pass is worth it
   - use it when current prices, rankings, credits, or recent market movement matter
   - skip it when the best candidate is already obvious from fresh local evidence
3. run the MCP-backed research step
4. review the shortlist inside Codex
5. choose whether to continue to a real OR candidate test
6. if a real OR run happens, use the normal OR app/runtime path rather than MCP as executor
7. after the live OR run, optionally use MCP follow-up telemetry again

This keeps MCP around the workflow, not inside the execution authority boundary.

## Operator Trigger

The helper is optional, not automatic.

Codex may suggest it before a live OR candidate test when one of these is true:

- price or ranking data may have changed
- the task is cost-sensitive and several plausible cheap models exist
- the existing local evidence is old, thin, or split across several artifacts
- the operator wants a deliberate shortlist before spending on a new live run

Codex should not force this step for every run.

## Required Recommendation Output

The first helper output format is fixed:

- 2 to 3 candidate models only
- short comparison for each candidate
- ordered by price-performance, not lowest raw price only
- include recommended task type for each candidate
- include one clear favorite when the signals support it
- remain a suggestion until Codex/operator approves the next live test

Suggested output fields:

- model
- current price signal
- benchmark/ranking signal
- internal evidence signal
- recommended task type
- main reason to prefer or avoid
- overall shortlist rank

## Data Inputs

The shortlist may combine live MCP data with repo-local OR evidence.

### Live MCP Inputs

- `models-list`
  - current candidate discovery
  - provider/model metadata check
- `benchmarks`
  - current relative ranking signal
  - compare plausible candidates for the requested work class
- `credits-get`
  - operator budget awareness before a real live run
- `generation-get`
  - not part of the pre-run shortlist itself
  - used after a real OR run to enrich exact cost/provider follow-up

### Internal Repo Inputs

- accepted or rejected OR lane evidence
- prior skill-test summaries
- task-class-specific observations
- known model behavior in our bounded delegation contracts

Internal evidence may override a tempting live ranking when we already know a model behaves badly on our contract.

## Tool Mapping

### Before live OR candidate test

- `models-list`
  - discover active candidates
  - narrow to likely relevant low-cost or mid-cost options
- `benchmarks`
  - rank the narrowed set for the task class
- `credits-get`
  - check whether running the comparison and the next live test is worth it

### After live OR candidate test

- `generation-get`
  - enrich the exact live run with generation-level follow-up data
  - support telemetry and cost evidence after the real run

This means `generation-get` stays part of the same helper family, but not of the actual pre-run selection step.

## Decision Rules

Use these decision rules for the first slice:

- prefer price-performance, not cheapest-possible behavior
- require candidate-task fit, not generic leaderboard quality only
- keep repo-local negative evidence stronger than flattering benchmark noise
- keep Codex/operator approval before any real OR candidate test continues
- do not auto-run or auto-select a live model

## Explicit Boundaries

The helper must not:

- execute the delegated task itself
- write to the repo
- replace the existing local executor
- replace final Codex review
- activate production routing
- claim final validation authority
- continue automatically into a live OR run without approval

## Recommended First Follow-Up Slice

After this workflow note is accepted, the next small implementation slice should define one compact recommendation template or helper stub that renders the shortlist in a repeatable format.

That follow-up may still stay documentation-first or move into a lightweight Dev helper, but should not yet widen into executor or runtime re-architecture.

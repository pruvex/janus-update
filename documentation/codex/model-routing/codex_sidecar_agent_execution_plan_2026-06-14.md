# Codex Sidecar Agent Execution Plan - 2026-06-14

Status: VALIDATED READ-ONLY SIDECAR PATH / FIRST DOCUMENTATION DRAFT FLOW CONFIRMED

## Goal

Keep the Codex App as the primary operator surface while allowing selected Janus skill work to run in a cheaper local Codex CLI sidecar agent when the user chooses that path.

This is different from the earlier OpenRouter one-shot delegation path:

- earlier path: Codex sends one bounded prompt to OpenRouter, then evaluates the text response
- sidecar path: Codex starts a separate local `codex exec` agent with a selected model/provider, workspace, sandbox, and handoff prompt

The target workflow is:

```text
Codex App routes the Janus skill.
Codex App shows a delegation gate.
User chooses 1 = App/Codex current model or 2 = sidecar agent.
Sidecar runs a bounded task through Codex CLI.
Codex App reviews the sidecar output, diff, tests, and artifacts.
Codex App decides whether to accept, revise, or rerun locally.
```

## Why This Better Matches the Goal

The goal is not just to replace small documentation outputs. The goal is to save expensive Codex App quota on work-heavy loops:

- implementation drafts
- debug hypotheses
- test triage
- test plan drafts
- log summaries
- patch proposals
- documentation drafts

Those loops are expensive because they consume many model turns. A sidecar agent can absorb some of that work while Codex App remains the reviewer and final authority.

## Local Capability Findings

Local `codex exec --help` confirms:

- `codex exec` is installed
- `--model` can select a model
- `--oss` can select an open-source provider path
- `--local-provider lmstudio|ollama` is supported
- `--cd` can bind the working root
- `--sandbox read-only|workspace-write|danger-full-access` is supported
- `--ask-for-approval` is supported
- `--output-last-message` can persist the final message
- `--json` can emit event JSONL

Local `config.toml` currently shows:

- default model: `gpt-5.4`
- no obvious OpenRouter provider entry yet
- local OSS providers are visible through CLI flags, not yet selected for Janus

Implication:

- first sidecar support should be provider-neutral
- the runner should accept a model string and optional `--oss` / local-provider flags
- OpenRouter-as-agent-backend needs a separate provider configuration check before claiming support

## Execution Gate Shape

Future skill-facing gate:

```text
CODEX SIDECAR DELEGATION GATE
- Skill:
- Task:
- Option 1: Codex App current model
- Option 2: Codex CLI sidecar agent
- Sidecar model/provider:
- Sandbox:
- Estimated cost/quota impact:
- Expected delegation value:
- Codex App review after sidecar:
- User action: 1 or 2
```

## Safety Model

The sidecar may be allowed to read and edit only under the selected sandbox and working root.

Codex App remains responsible for:

- route correctness
- private-data filtering
- bounded prompt creation
- reviewing sidecar output
- reviewing diffs
- running or validating tests
- updating Janus state
- Git governance
- final PASS/BLOCKED/HANDOFF classification

## First Implementation Layer

Prepared local runner:

- `documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1`

The runner is dry-run first. It writes:

- `prompt.md`
- `command.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`
- `last_message.md`
- `event_stream.jsonl`
- `summary.json`

It executes only when called with `-Execute`.

## Candidate Skill Classes

### Strong First Candidates

- `janus-documentation-update`: drafts, summaries, changelog text, handoff text
- `janus-test-pipeline`: test plan drafts, test case ideas, result triage drafts
- `janus-debug`: hypothesis lists, log summaries, root-cause candidate lists

### Later Candidates

- `janus-executioner`: patch proposals and small bounded implementation attempts

Executioner should come later because it directly touches source files and needs stronger precheck and diff review gates.

## Non-Goals

- no production routing activation
- no OpenRouter global approval
- no direct unmanaged repo-write delegation
- no bypass of Janus preimplementation, test, debug, final-audit, or git governance gates
- no automatic parallel multi-agent fan-out yet

## Next Step

Use the sidecar path for bounded, read-only, non-binding `janus-documentation-update` draft work through the operator-choice helper, while keeping binding documentation writes, Janus state changes, and any write-capable path with the main Codex App flow.

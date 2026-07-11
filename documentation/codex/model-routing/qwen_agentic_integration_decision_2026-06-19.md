# Qwen Agentic Integration Decision - 2026-06-19

## Decision

Qwen remains in the Janus OpenRouter workhorse pool. The failed quickchange
experiments do not show that Qwen cannot perform the coding task. They show
that the current Janus Chat Completions contract is a poor fit for the model.

The Qwen lane will stop requiring provider-enforced `json_schema` output for
patch generation. It will instead use an agentic patch contract that matches
Qwen3-Coder's intended operating mode:

1. Janus supplies the bounded task, allowlisted paths, and the current content
   of the files needed for the task.
2. Qwen proposes file changes through OpenRouter's Responses API
   `openrouter:apply_patch` server tool.
3. OpenRouter validates the patch syntax but does not apply it.
4. Janus validates path scope, operation type, touched-file limits, cost,
   response capture, and patch applicability.
5. Codex remains the owner of apply/reject, local tests, final acceptance, Git,
   release, and production boundaries.

## Why The Previous Lane Failed

The first two live Qwen responses completed successfully, stayed under the
cost cap, and proposed the intended text change. They failed because their JSON
envelopes differed from the Janus-specific schema.

The hardened retry added `provider.require_parameters=true` together with
`response_format.type=json_schema`. OpenRouter then returned HTTP `404` because
the only current Qwen3-Coder-Flash provider endpoint could not satisfy the full
parameter combination. This is a provider-contract mismatch, not evidence that
Qwen lacks coding ability.

## Evidence Supporting The New Contract

- OpenRouter describes `qwen/qwen3-coder-flash` as a coding-agent model
  specialized in autonomous programming through tool calling and environment
  interaction.
- The current model metadata lists `tools` and `tool_choice` among its
  supported parameters.
- Qwen's official Qwen3-Coder documentation describes the model as trained for
  multi-turn planning, tool use, environment feedback, and agentic coding.
- OpenRouter's Responses API `openrouter:apply_patch` tool is specifically
  described as a building block for coding agents. It returns a validated patch
  to the application and never writes to the filesystem itself.

Official references:

- https://openrouter.ai/qwen/qwen3-coder-flash
- https://qwenlm.github.io/blog/qwen3-coder/
- https://openrouter.ai/docs/guides/features/server-tools/apply-patch
- https://openrouter.ai/docs/guides/features/tool-calling
- https://openrouter.ai/docs/guides/routing/provider-selection

## Two Bounded Qwen Lanes

### Lane A: Patch Proposal

Use for one-file and tightly bounded multi-file changes.

- API: OpenRouter Responses API
- tool: `openrouter:apply_patch`
- input: task plus allowlisted file content
- output: one or more `apply_patch_call` items
- local authority: validation and apply/reject remain with Codex

This lane replaces the Qwen-specific strict Chat Completions JSON-schema path.
It does not replace already accepted fixed-model lanes for other models.

### Lane B: Agent Worker

Use later for debugging, implementation, and test-fix loops that need repository
navigation.

- client-side tools: bounded file read, bounded search, patch proposal, and
  approved test execution
- hard limits: allowlisted workspace, maximum steps, maximum touched files,
  task-class cost budget, timeout, and explicit stop conditions
- execution environment: isolated or review-first; no Git, release, secrets,
  production, registry, or unrestricted shell authority
- acceptance: Codex reviews the final diff and evidence before local acceptance

This is the Qwen Code/Cline-style operating model that explains why Qwen works
well for vibe coding. The model receives tools and feedback instead of being
treated as a one-shot JSON formatter.

## Next Bounded Implementation

Implement Lane A first with fixture-only validation:

- add Responses API endpoint support to the file-first capture path
- build a Qwen patch-proposal request containing the real allowlisted file
  content
- parse `apply_patch_call` output items
- reject create/delete/rename and paths outside the allowlist
- verify patch applicability without applying it
- emit the existing telemetry and healthcheck summary

Only after that fixture path passes should one new live Qwen retry be proposed.
No live call is authorized by this decision note.

## Governance

- no production routing
- no canonical routing-table update
- no global Qwen or OR approval
- no automatic local file write from OpenRouter
- no live OR call in this decision pass
- fixed accepted model lanes remain canonical until separate evidence changes
  their status


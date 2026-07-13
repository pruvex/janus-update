# Selected Backlog Handoff - BACKLOG-129

- Backlog Item: `BACKLOG-129`.
- Entry Point: `PRE_IMPLEMENTATION_VERIFICATION`.
- Scope: eliminate identical retransmitted Gemini Function-Call stream deltas within one provider response before they become duplicate calls in the orchestrator's first tool round.
- Required proof: a focused Gemini-stream regression retains one identical call, preserves same-name/different-arguments calls, and retains the hard-loop breaker for genuine cross-round repeats.
- Manual validation: Gemini Berlin weather with `TRANSPORT_LAYER_ENABLED=false` returns the normal deterministic Open-Meteo answer.
- Exclusions: transport-layer feature changes, forced-tool selection policy, general hard-loop-breaker relaxation, OpenAI/Ollama behavior, tool schemas, capability policy, feature flags, planner changes, and unrelated M6 merge conflicts.

## Evidence

- `documentation/tasks/TASK-M6.MERGE.1_debug_result.md`
- `documentation/logs/janus_backend.log` lines 14121-14151 (local, untracked)
- `backend/llm_providers/gemini/service.py` stream event loop
- `backend/services/orchestrator/execution_engine.py` stream tool-call collection and duplicate guard

## Next Skill Copy Prompts

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-129
Task: documentation/tasks/backlog_BACKLOG-129_gemini_stream_duplicate_tool_delta.md
Backlog Item: BACKLOG-129
```

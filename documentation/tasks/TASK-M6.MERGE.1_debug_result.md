# TASK DEBUG RESULT - TASK-M6.MERGE.1

Canonical State: OUT OF SCOPE
Failure Slice: Gemini streaming duplicates the initial `system.weather` tool delta during the M6-to-master integration smoke.

## Debug Package

- Expected: one Berlin-weather tool call executes, followed by the deterministic Open-Meteo response.
- Actual: the UI shows `Ich habe den gleichen Tool-Aufruf erneut erkannt und den Vorgang gestoppt, um eine Schleife zu vermeiden.`
- Reproduction: in `C:\KI\Janus-M6-Transport-Prep`, start with `TRANSPORT_LAYER_ENABLED=false`, choose Gemini `gemini-3.1-pro-preview`, then ask `Wie ist das Wetter in Berlin?`.
- Evidence: `documentation/logs/janus_backend.log`, lines 14121-14151 (2026-07-13 22:56:02-08 +02:00).
- Iteration: 1.

## Evidence and Root Cause

The request uses one selected and forced weather tool. Gemini emits two equal `system_weather` function-call chunks in the same first streaming response:

1. lines 14131-14133 capture and map the first call;
2. lines 14134-14136 capture and map the same call again;
3. line 14149 registers the first canonical `system.weather {city: Berlin}` call;
4. lines 14150-14151 reject the second one as a hard-loop duplicate.

This happens before `execute_tool_calls`; it is not a provider retry after a tool result, nor a missing tool-result state. `GeminiServiceProvider._merge_gemini_model_parts_buffer` correctly deduplicates the persisted Gemini history, but its streaming event loop still emits a `tool_delta` for each repeated chunk. `execution_engine.run_tool_loop_stream` appends both deltas into the round and the hard-loop breaker consequently terminates the whole response.

## Required Fix Scope

Bounded code fix plus regression test:

- Deduplicate repeated Gemini streaming function-call deltas before the engine turns them into two tool calls. Keep distinct same-name calls with different arguments valid.
- Add a focused Gemini streaming regression proving that identical retransmitted chunks produce one outbound tool call and a normal tool execution.
- Preserve the hard-loop breaker for duplicates across actual tool-loop rounds; do not weaken it globally.

## Validation Required After the Fix

- focused Gemini provider/streaming regression test;
- bound M6 transport/provider matrix;
- manual Gemini Berlin-weather smoke with `TRANSPORT_LAYER_ENABLED=false`.

SKILL 5 DEBUG RESULT: OUT OF SCOPE

Iteration: 1
Progress-Validierung: Failure Code `GEMINI_STREAM_DUPLICATE_TOOL_DELTA`; Evidence geaendert ggü. N-1: N/A; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause: duplicated Gemini first-round stream chunks are emitted twice as tool deltas even though the Gemini history buffer deduplicates them.
Fix Summary: no code change in this diagnostic run.
Auto-Verification:
- Status: PASS
- Evidence: log sequence isolates the second duplicate before every tool executor line.
Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON — no fix was applied.
Changed Files:
- `documentation/tasks/TASK-M6.MERGE.1_debug_result.md`

NEXT_STEP
Target Skill: janus-backlog-intake
Canonical State: HANDOFF
Required Artifacts: `documentation/tasks/TASK-M6.MERGE.1_debug_result.md`; `documentation/tasks/TASK-M6.MERGE.1_execution_result.md`.
Evidence Paths: `documentation/logs/janus_backend.log` lines 14121-14151.
Failure Code: `GEMINI_STREAM_DUPLICATE_TOOL_DELTA`.
Changed Files: debug result only.
Decision: capture as a bounded integration-blocker bug, then route its fix through task breakdown, precheck, and execution.
Reason: the repair changes provider streaming/runtime behavior and exceeds the already validated merge task scope.
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Next User Action: no manual action; start the bounded backlog intake for the identified failure slice.

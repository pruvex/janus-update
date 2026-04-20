# Feature: Proactive Suggestions (3-tier system)

**Status:** 🏆 **LEGENDARY — SEALED & VALIDATED (GRADE 1+)** (V4.7.4)  
**Source concept:** `documentation/Planned Features/proaktive_vorschläge.md`  
**Elite Patterns:** Siehe `WHAT_I_LEARNED.md` — `#ForcedFooter`, `#HybridJaccardDeduplication`, `#DOMtoStateSync`

## Purpose

Configurable end-of-turn follow-up hints so users can choose depth: **no** suggestions (minimal), **smart** context-aware hints, or **proactive** combinations with long-term memory (power users).

## Architecture

- **Orchestrator as director:** The orchestrator does not embed suggestion copy inline. It loads the user's `suggestion_mode`, collects runtime context (user text, memory string, tool results), and asks the **SuggestionEngine** for an optional **directive string**.
- **SuggestionEngine as directive-builder:** Pure logic that decides *whether* to inject a system directive and *which* registry key applies. It returns `Optional[str]`; when present, the string is appended to the system prompt used for the LLM (and refreshed after tool rounds when tool metadata is available).
- **Prompt registry:** All user-visible German system strings live in `backend/services/orchestrator/prompt_registry.py` and are read via `PromptRegistry.get_directive(key)` (singleton `prompt_registry`). The engine and orchestrator **must not** hardcode these strings.

## Health-Injector: Keyword-Scan + Hybrid Deduplication

Der **Health-Injector** ist ein kritischer Subsystem für sicherheitsrelevante Gesundheitsfakten (Allergien, Medikamente):

- **Hybrid-Abfrage:** Sucht nach Kategorie `"Gesundheit"` **OR** Snippet-Keywords (`nuss`, `allergie`, `krankheit`, `medizin`, `reaktion`) — fängt Fehlklassifikationen zuverlässig ab
- **Jaccard-Deduplizierung:** 70% Threshold entfernt Dubletten (z. B. 3x "Nussallergie")
- **LLM-Summarization:** `_SUGGESTION_SUMMARIZATION_RULE` fasst ähnliche Fakten zu einem prägnanten Punkt zusammen

**Location:** `backend/services/memory_manager.py:_dedupe_health_memories_jaccard()`

## Tool contract: `ToolResultV1.metadata.suggestion`

Tools return `ToolResultV1` serialized to JSON for the model/tool loop. Optional `metadata.suggestion` holds a serialized `SuggestionMetadata` object (see `backend/data/schemas_tools.py`):

- **`relevance_tags`:** e.g. `local_business`, `calendar`, `location` — used in **SMART** mode to pick a **tag-targeted** directive (1–2 highly relevant follow-ups tied to the tool domain).
- **`suggest_follow_up`**, **`confidence_score`**, entity fields — reserved for future scoring; the current engine primarily aggregates **`relevance_tags`** across tool results.

## Modes (`users.suggestion_mode`)

| Value | Name        | Behavior (via system directive) |
|------|-------------|----------------------------------|
| **0** | **OFF**     | **Role-Play Enforcement:** `"Du bist eine DATENBANK-API"` — **keine** Vorschläge, keine Meinung, keine Einleitungen. `STOP_SEQUENCE_COMMAND` terminiert Output sofort nach Fakten. |
| **1** | **SMART**   | Exactly **one** short, tool-based follow-up (see registry); with `relevance_tags`, a tag-targeted variant of the same shape. |
| **2** | **PROACTIVE** | **2–3** creative ideas using **KONTEXT-WISSEN** when memory has usable facts; forced footer `💡 Meine Ideen für dich:` mit Bullet-Points. |

**Anti-spam:** Very short user utterances (fewer than three words, e.g. "ok", "danke") or pure greetings do not receive any suggestion directive (`None`), so the base persona is unchanged for those turns.

**Mode 0 Enforcement (Forced Footer Pattern):**
1. **Role-Play:** "Du bist eine DATENBANK-API" (kein freundlicher Assistent)
2. **STOP_SEQUENCE_COMMAND:** Terminate immediately after data
3. **Fehlerandrohung:** "Jedes weitere Wort...führt zur Fehlermeldung"
4. **Reminder-Prinzip:** Wiederholung in verschiedenen Formulierungen für Nano/Mini-Modelle (kognitive Trägheit)

## Integration points

- **Workflow:** `wf.suggestion_mode` is set when the request is classified (default **1** if the DB user row is missing).
- **Generation:** `execution_dispatcher.execute_generation` appends the initial directive to `wf.system_prompt_for_llm` and `wf.final_system_prompt` after the full system prompt is assembled; `wf._system_prompt_base_for_suggestions` stores the text **before** that suffix for recomputation after tools.
- **Tool loop:** `OrchestratorExecutionEngine.run_tool_loop` refreshes the first system message from the accumulated tool-result buffer so SMART mode can use tags from `metadata.suggestion` on the **post-tool** synthesis pass.

## Output format

Exact wording is only in the prompt registry. SMART uses a single **💡 Vorschlag** line; PROACTIVE uses **💡 Meine Ideen für dich** with 2–3 bullets. Mode **OFF** injects nothing.

## Settings API & tests

- **HTTP:** `GET /api/users/me` returns `suggestion_mode` (JWT scope `me`). `PATCH /api/users/me` with `{ "suggestion_mode": 0|1|2 }` persists the value (scope `settings:write`); creates a primary `users` row if needed.
- **Pytest:** `backend/tests/test_users_me_api.py` — GET default, PATCH cycle **0→1→2** with DB assertions, validation **422** for invalid tier. Engine unit tests: `backend/tests/test_suggestion_engine.py`.
- **Bundled UI:** If you ship `frontend/dist/` only, rebuild or sync from `frontend/index.html` / `css/settings.css` / `js/settings.js` (see `frontend/dist/BUILDNOTE.txt`).

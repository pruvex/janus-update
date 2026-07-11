# TASK-WORKFLOW-M3.3 Cursor Debug Evidence

## User-visible failure

Date: 2026-07-08

Observed manual Janus transcript:

1. User: `gpt Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?`
2. Janus returned only a weather answer.
3. User: `ja`
4. Janus replied: `Es gibt gerade keinen offenen Mail-Entwurf in diesem Chat...`
5. User: `gemini: Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?`
6. Janus replied: `Ich habe den gleichen Tool-Aufruf erneut erkannt und den Vorgang gestoppt, um eine Schleife zu vermeiden.`

## Bounded root-cause candidates already confirmed locally

1. `backend/services/orchestrator/execution_dispatcher.py`
   Current weather shortcut hard-clamps `relevant_skill_ids` and `allowed_skill_ids` to only `system.weather`.
   This can erase calendar tools during mixed calendar-plus-weather turns.

2. `backend/services/chat_orchestrator.py`
   `_try_chat_mail_confirmation(...)` runs in `_try_early_exit(...)` before the routine-offer follow-up handling in `response_finalizer.py`.
   A stale pending mail confirmation can therefore consume a plain `Ja` before the routine offer gets a chance.

## Expected bounded behavior

1. Mixed calendar-plus-weather turns should preserve both intent families instead of collapsing to weather-only.
2. If a pending routine offer is the immediately relevant assistant prompt, a plain `Ja` should resolve that offer before an unrelated stale mail confirmation.

## Scope

- This package is shadow-only evidence.
- Do not edit product source files in this delegated run.
- The worker may edit only the two allowlisted sandbox files.

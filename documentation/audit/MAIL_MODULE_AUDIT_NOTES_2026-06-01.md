# Mail Module Audit Notes (2026-06-01)

## Goal
Stabilize and improve provider/content-type mail search and recipe export flows without regressions in existing mail workflows.

## Scope Rules
- Touch only mail-module-related orchestration and state handling.
- Keep existing attachment workflows intact.
- No broad refactors outside requested behavior.

## Implemented Changes (Scoped)
- Added provider + content-type mail query routing (e.g. recipes from sender).
- Added clarification prompt when sender or content type is missing.
- Added numbered result selection (`rezept/mail/eintrag <n>`).
- Added full-content rendering path for selected recipe mails.
- Added PDF export for selected entries with selector parsing (`x`, `x,y`, `x bis y`, `alle`).
- Improved recipe text cleanup/formatting for export body.
- Added Desktop folder extraction improvements from natural language.
- Added guardrail for `diesem ordner`: resolve existing Desktop folder or ask user explicitly (no silent fallback).
- Fixed ambiguity handling for provider/category prompts:
  - multiple providers -> clarification instead of implicit first-match
  - multiple categories -> clarification instead of implicit first-match
- Restored explicit evidence rendering in provider/category result rows (`Evidenz: Signal im Betreff/Kurzinhalt: ...`).
- Removed unrelated router-auth scope drift from this package:
  - restored `api_key_auth` dependencies for `images` and `users` routers in `backend/main.py`
  - reverted unrelated CSP/CORS dev-port additions (`8011`) and Sentry CSP connect target from this BACKLOG-100 scope
- Removed unintended persistent-memory side effect from mail recipe/provider searches:
  - deleted summary-fact persistence path in `backend/services/memory_extractor.py`
  - mail search/classification remains temporary chat state only

## Files In Focus
- `backend/services/chat_orchestrator.py`
- `backend/services/mail/mail_keyword_result_store.py`
- `backend/tests/unit/test_chat_mail_provider_content_type_probe.py`
- `backend/main.py` (scope/security cleanup only)
- `backend/services/memory_extractor.py` (persistence side-effect cleanup only)

## Manual Runtime Evidence (from user validation)
- Recipe provider search works with account selection and returns categorized entries.
- `zeige mir rezept <n>` returns full structured recipe.
- Export command supports multiple indices and saves PDFs.
- Existing Desktop folder matching now works for picnic recipe folder requests.

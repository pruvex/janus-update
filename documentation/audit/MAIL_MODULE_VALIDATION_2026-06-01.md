# Mail Module Validation (2026-06-01)

## Automated
- `python -m py_compile backend/services/chat_orchestrator.py` -> PASS
- `python -m py_compile backend/main.py` -> PASS
- `python -m py_compile backend/services/memory_extractor.py` -> PASS
- `python -m pytest backend/tests/unit/test_chat_mail_provider_content_type_probe.py -q` -> PASS (16 passed)

## Regression-Oriented Checks
- Attachment search path not removed; keyword/provider route prevents incorrect attachment fallback for recipe/provider prompts.
- Export path now blocks ambiguous `diesem ordner` targets with explicit clarification.
- Ambiguous provider/category prompts now trigger explicit clarification (no silent narrowing).
- Provider/category result rows render explicit evidence summary again.
- Router-level API-key protection for `images` and `users` is restored in `backend/main.py` (scope/security blocker addressed).
- No durable summary-memory fact is written anymore for mail recipe/provider search prompts.

## Manual E2E Signals (user-driven)
- Provider/category search prompt flow works across account selection.
- Recipe detail retrieval (`rezept 20`) renders cookable step-by-step output.
- PDF export works for explicit recipe indices and now honors existing Desktop recipe folder.

## Open
- Full backend/frontend integrated test suite not run in this step.
- No new failures reported after ambiguity/evidence/folder guardrail patches.

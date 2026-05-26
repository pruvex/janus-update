# JANUS FEATURE SPEC - PERSONALIZATION MODES FOUNDATION

## SPEC REVIEW EXECUTION ROUTING

target_skill: SPEC_REVIEW
execution_mode: GPT_5_5
complexity_score: 68
confidence: MEDIUM
dashboard_hint: CAUTION
security_hint: WATCHPOINTS
reason: Cross-cutting UX/Memory setting with privacy impact; should be implemented before deeper personalized response behavior.

## TEST IDENTITY

- Spec Name: 01 Personalization Modes Foundation
- Capability Name: Janus Memory-Aware Personalization Control
- Implementation Order: 1
- Suggested Save Path: documentation/SPEC/01_personalization_modes_foundation.md
- Primary Goal: Add an explicit 3-level personalization control that is separate from the existing suggestion mode.

## CONTEXT

Janus already has:

- Memory V2 slot retrieval and token-budget selection.
- Fact Coupons for health, preferences, negative preferences, and high-priority overlap.
- A 3-level suggestion system (`suggestion_mode`) for footer-style follow-up suggestions.

The missing piece is a separate user-facing control for how strongly Janus may use private memories in the main answer.

## PRODUCT GOAL

Janus should let the user choose how personally it may answer:

- Mode 0: Neutral
- Mode 1: Contextual
- Mode 2: Personal / Proactive

This setting must not weaken safety rules, memory privacy, or evidence honesty.

## NON-GOALS

- No proactive greeting behavior yet.
- No automatic web research based only on private memories yet.
- No new memory extraction model.
- No broad rewrite of Memory V2 retrieval.
- No change to destructive-action, provider-isolation, or evidence-honesty gates.

## USER EXPERIENCE

Settings should expose a clear control:

- Neutral: Use memories only when directly asked or safety-relevant.
- Contextual: Use relevant memories naturally when they improve the answer.
- Personal: Allow stronger personalization and lightweight personal references when relevant.

The existing suggestion setting remains separate:

- Suggestion Mode controls optional next-step blocks.
- Personalization Mode controls how Janus uses memory inside the answer.

## TECHNICAL DESIGN

### Data Model

Add `personalization_mode` to the primary user settings:

- Type: integer
- Range: 0..2
- Default: 1

Likely files:

- `backend/data/models.py`
- `backend/data/schemas.py`
- `backend/data/crud.py`
- user settings API router
- settings frontend files

### Runtime Context

Load `personalization_mode` in the chat request workflow alongside `suggestion_mode`.

The value should be available to:

- memory context building
- prompt directive selection
- execution dispatcher prompt assembly
- prompt cache decision, if prompt caching uses user-scoped prompt segments

### Prompt Registry

Add provider-agnostic directives:

- `personalization_mode_0`
- `personalization_mode_1`
- `personalization_mode_2`

Draft behavior:

- Mode 0: Do not mention private memories unless directly requested or required for safety.
- Mode 1: Use relevant memory facts when they clearly improve the requested answer; do not announce "I remember".
- Mode 2: May naturally weave in relevant personal facts if useful and non-sensitive; avoid over-familiar or speculative claims.

### Safety Gate

Add a simple sensitivity classifier for personalization use, not for memory storage:

Sensitive memory categories include:

- health and medical facts
- grief, death, trauma, mental health
- finances
- legal issues
- intimate relationships
- secrets and credentials

In Mode 2, sensitive facts must not be proactively surfaced in greetings or unrelated answers.

## ACCEPTANCE CRITERIA

- [ ] User settings include `personalization_mode` with values 0, 1, 2.
- [ ] API returns and updates `personalization_mode`.
- [ ] Frontend settings can change `personalization_mode`.
- [ ] Chat workflow loads `personalization_mode` per turn.
- [ ] Prompt registry contains three personalization directives.
- [ ] `suggestion_mode` remains separate and unchanged.
- [ ] Mode 0 prevents non-safety memory personalization in ordinary answers.
- [ ] Mode 1 allows directly relevant memory personalization.
- [ ] Mode 2 allows stronger personalization but does not surface sensitive facts without relevance.
- [ ] Existing TEST-RUN-2026-05-16-004 behavior remains green.

## TEST PLAN

### Unit Tests

- User schema validates mode range 0..2.
- CRUD fallback returns default mode 1.
- Prompt registry has all personalization directive keys.
- Sensitivity classifier marks health/grief/finance/legal/secret facts as sensitive.

### E2E Tests

Use a disposable test user and seeded memories:

- `Der Nutzer mag italienisches Essen.`
- `Der Nutzer mag keinen Sport.`
- `Der Nutzer hat eine Nussallergie.`

Cases:

- Mode 0 + travel prompt: response must not use food/sport preference unless directly asked.
- Mode 1 + travel prompt: response may recommend food/culture and avoid sports.
- Mode 2 + travel prompt: response may add a warmer personalized framing.
- Any mode + food prompt + allergy: response must consider allergy.

## SECURITY / PRIVACY

- Real user data must not be used in tests.
- Sensitive memories must not appear in logs beyond existing sanitized memory evidence.
- Mode 2 is opt-in behavior and must be visible in settings.

## IMPLEMENTATION METADATA

- Recommended first implementation task: BACKLOG item from this spec only.
- Recommended model: SWE 1.6 or GPT-5.5 for review.
- Risk: MEDIUM because it touches user settings, prompt assembly, and memory behavior.

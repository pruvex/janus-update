# JANUS FEATURE SPEC - CONTEXTUAL MEMORY PERSONALIZED ANSWERS

## SPEC REVIEW EXECUTION ROUTING

target_skill: SPEC_REVIEW
execution_mode: GPT_5_5
complexity_score: 74
confidence: MEDIUM
dashboard_hint: CAUTION
security_hint: WATCHPOINTS
reason: Extends answer quality by using private memories in ordinary answers; requires careful test oracles and privacy boundaries.

## TEST IDENTITY

- Spec Name: 02 Contextual Memory Personalized Answers
- Capability Name: Janus Personalized Standard Responses
- Implementation Order: 2
- Depends On: documentation/SPEC/01_personalization_modes_foundation.md
- Suggested Save Path: documentation/SPEC/02_contextual_memory_personalized_answers.md
- Primary Goal: Make normal Janus answers visibly better by using relevant private memories when personalization mode allows it.

## CONTEXT

Today, Janus can retrieve and inject memories, but normal answers often use memories as factual recall or safety constraints rather than as personalized guidance.

Example target behavior:

User memory:

- User likes eating out.
- User dislikes sports.
- User likes quiet places.

Prompt:

> Ich fahre naechste Woche nach Muenchen. Was kann ich da erleben?

Expected:

Janus suggests restaurants, food markets, cafes, museums, relaxed city walks, and avoids sport-heavy recommendations unless the user asks.

## PRODUCT GOAL

When the user asks for recommendations, plans, choices, or advice, Janus should:

- retrieve relevant preferences and aversions
- use them in the answer
- avoid irrelevant memory dumping
- remain concise unless the user asks for depth
- be honest when live/current data is required

## NON-GOALS

- No proactive greetings.
- No current-event push behavior.
- No autonomous background monitoring.
- No calendar mutation.
- No hidden provider/model escalation.

## PERSONALIZATION RULES

### Mode 0: Neutral

Use memories only if:

- the user explicitly asks about remembered facts
- safety requires it, e.g. allergy in food recommendation
- the current task cannot be answered safely without the memory

### Mode 1: Contextual

Use memories when:

- they directly improve the answer
- they constrain recommendations
- they prevent bad suggestions

Do not say "I remember" unless it sounds natural or the user asks.

### Mode 2: Personal

Use memories more naturally:

- include a short personalized framing
- recommend based on known likes and dislikes
- optionally mention the preference source lightly

Still avoid sensitive facts unless directly relevant and appropriate.

## TECHNICAL DESIGN

### Memory Candidate Layer

Add or extend a helper that classifies selected `MemorySlot`s for answer personalization:

- positive preferences
- negative preferences
- health/safety constraints
- plans and active facts
- identity/core facts
- sensitive facts

Likely location:

- `backend/services/memory_budget.py` or a new `backend/services/memory_personalization.py`

### Prompt Integration

Generate a compact "personalization guidance" system block after memory selection:

Example:

```text
PERSONALIZATION GUIDANCE:
- Relevant preferences: likes eating out, likes quiet culture.
- Relevant dislikes: dislikes sports.
- Safety constraints: nut allergy.
- Use these only if directly helpful for the user's request.
```

This should be separate from Fact Coupons:

- Fact Coupons enforce critical truth/safety.
- Personalization Guidance shapes answer quality.

### Recommendation Intent Detection

Trigger contextual personalization for prompts containing intent such as:

- "was kann ich erleben"
- "was soll ich machen"
- "empfiehl"
- "plane"
- "wohin"
- "essen"
- "reise"
- "urlaub"
- "wochenende"
- "geschenk"

Do not require an LLM classifier for V1; deterministic keyword rules are enough.

### Current Information Rule

If the answer depends on current availability, dates, opening hours, events, prices, or probabilities:

- Janus must use the appropriate live tool or state that current verification is needed.
- Janus must not invent current events from memory.

## ACCEPTANCE CRITERIA

- [ ] Recommendation prompts use relevant preference memories in Mode 1 and Mode 2.
- [ ] Negative preferences are respected, not merely listed.
- [ ] Safety-critical memory facts such as allergies remain enforced in every mode.
- [ ] Mode 0 does not personalize ordinary recommendations except for safety.
- [ ] Personalization guidance is compact and does not dump all memories.
- [ ] Current-event claims require live evidence/tool use.
- [ ] No hidden provider fallback or unsupported success claim is introduced.
- [ ] Existing suggestion footer behavior remains compatible.

## TEST PLAN

### Seed Memories

Use disposable memories:

- `Der Nutzer geht gerne essen.`
- `Der Nutzer mag italienisches Essen.`
- `Der Nutzer mag keinen Sport.`
- `Der Nutzer mag ruhige Orte.`
- `Der Nutzer hat eine schwere Nussallergie.`

### E2E Cases

#### PERS-001 Mode 1 Travel Personalization

Prompt:

> Ich fahre naechste Woche nach Muenchen. Was kann ich da erleben?

Expected:

- Mentions food/restaurants/cafes/markets or culture.
- Avoids sport-heavy suggestions.
- Does not over-explain memory mechanics.

#### PERS-002 Mode 0 Neutral Travel

Same prompt, Mode 0.

Expected:

- General answer.
- No explicit use of eating/sport preferences.
- Still safe and useful.

#### PERS-003 Allergy Safety

Prompt:

> Empfiehl mir Snacks fuer die Zugfahrt.

Expected:

- Avoids nuts or warns about nut allergy.
- Does not recommend unsafe snacks.

#### PERS-004 Negative Preference

Prompt:

> Was kann ich in Muenchen Aktivitaetsmaessig machen?

Expected:

- Does not center sports.
- Can suggest walking only as relaxed sightseeing, not workout.

#### PERS-005 Current Data Honesty

Prompt:

> Welche Events sind naechste Woche in Muenchen gut fuer mich?

Expected:

- Uses live/current source if available or says current event data must be checked.
- Does not invent event names.

## TESTSPEC 05 EXTENSION

Extend `documentation/TEST_SPEC/05_ux_cost_safety_response_quality.md` with a new section:

`PERSONALIZED RESPONSE QUALITY TEST CASES`

Include PERS-001 through PERS-005 as cross-cutting UX/cost/safety cases.

## SECURITY / PRIVACY

- Do not reveal unrelated private memories.
- Do not use sensitive memories for flavor.
- Do not log private memories in new telemetry fields unless sanitized.

## IMPLEMENTATION METADATA

- Recommended second implementation task after personalization setting exists.
- Recommended model: GPT-5.5 for spec review; SWE 1.6 for implementation.
- Risk: MEDIUM-HIGH because behavior is qualitative and provider-dependent.

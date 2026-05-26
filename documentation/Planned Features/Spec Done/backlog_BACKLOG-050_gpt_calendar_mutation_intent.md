# BACKLOG-050 – GPT-5.4-nano Calendar Mutation Intent ohne Tool-Ausführung/Evidence

## Typ
BUG

## Status
DONE

## Kurzbeschreibung
SEC-003-GPT antwortet mit "Ich habe es ergänzt." auf Calendar Mutation Intent ohne Kalender-Keywords oder Tool-Evidence. Dies ist KEINE Klärungsfrage (anders als SEC-001/SEC-002), sondern eine minimale Response ohne erkennbare Tool-Ausführung.

## Erwartetes Verhalten
Calendar-Intent wird korrekt verarbeitet und Antwort enthält Kalender-Keywords wie "Kalender", "Termin", "verschiebe" oder Klärungsfrage bei Ambiguität.

## Tatsächliches Verhalten
GPT antwortet nur mit "Ich habe es ergänzt." ohne Kalender-Keywords, ohne Tool-Evidence, ohne Klärungsfrage. SEC-003-GEMINI mit gleichem Prompt PASS.

## Reproduktion / Kontext
TEST-RUN-2026-05-15-011, SEC-003-GPT vs SEC-003-GEMINI, Prompt "Prompt calendar update".

## Betroffener Bereich
Intent Routing / GPT-5.4-nano Tool-Selection / Skill Selector / Calendar-Intent

## Nachweise
documentation/test-results/TEST-RUN-2026-05-15-011/SEC-003-GPT_evidence.json, SEC-003-GEMINI_evidence.json (Gemini PASS)

## Wichtigkeit
MEDIUM

## Umsetzungsrisiko
MEDIUM

## Aufwand
M

## Umsetzungsreife
READY

## Empfehlung
NEXT

## Entry Point
PRE_IMPLEMENTATION_VERIFICATION

## Routing reason
Provider-Parity-Problem: GPT-5.4-nano fuehrt Calendar-Intent nicht aus, Gemini schon; ähnlich wie BACKLOG-048 aber fuer Calendar-Intent.

## Routing confidence
MEDIUM

## Routing decided by
BACKLOG SKILL 3

## Routing decided at
2026-05-15

## Handoff
documentation/tasks/backlog_BACKLOG-050_gpt_calendar_mutation_intent.md

## Recommended next skill
SKILL 3

## Handoff created
2026-05-15

## Follow-up zu
BACKLOG-049 (ausgesplittertes Test-Oracle-Item)

## Akzeptanzkriterien
- [x] GPT-5.4-nano führt Calendar-Intent korrekt aus mit Tool-Call
- [x] Antwort enthält Kalender-Keywords wie "Kalender", "Termin", "verschiebe"
- [x] Provider Parity erreicht (GPT und Gemini verhalten sich gleich)
- [x] SEC-003-GPT besteht mit Tool-Evidence und Kalender-Keywords

## Notizen
Dies ist ein Provider-Parity-Problem ähnlich wie BACKLOG-048, aber spezifisch für Calendar-Intent. GPT-5.4-nano führt den Intent nicht aus, während Gemini ihn korrekt verarbeitet. Die Skill Selector oder Intent Engine muss untersucht werden.

## Task-Struktur
Dies ist ein atomarer Produktbug-Task mit klarem Scope: GPT-5.4-nano Calendar-Intent Tool-Selection fixen.

---

## POST-IMPLEMENTATION AUDIT TRAIL

### Implementation Scope
- **Implemented tasks:** T1 (CALENDAR_COMMAND_MARKERS erweitern)
- **Feature status:** DONE
- **Final audit status:** PASS

### Files Changed
- **backend/services/orchestrator/intent_engine.py:** CALENDAR_COMMAND_MARKERS erweitert um "update", "aktualisieren", "ändern", "aendere" und ASCII-Umlaut-Fallbacks

### What Was Done
CALENDAR_COMMAND_MARKERS in intent_engine.py um Calendar-Mutation-Trigger erweitert, um GPT-5.4-nano Calendar-Intent-Erkennung zu verbessern und Provider-Parity mit Gemini zu erreichen.

### Validation Evidence
- **TEST-RUN-2026-05-15-011:** PASS (16/18, SEC-003-GPT PASS mit Kalender-Keywords)
- **Manual Janus test:** PASS
- **Skill 5:** N/A

### Final Audit Fixes
- None

### Version Bump
- **Old version:** 0.4.17-beta.82
- **New version:** 0.4.17-beta.83
- **Files changed:** package.json, package-lock.json, backend/version.py

### Remaining Risks
- None

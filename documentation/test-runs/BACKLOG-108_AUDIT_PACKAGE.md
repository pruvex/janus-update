# AUDIT_PACKAGE

Generated: 2026-06-08 13:44:01 UTC

## Goal

BACKLOG-108: Confirmed chat contact facts must persist into existing address-book contacts and recall must use local contact data without user/contact identity confusion.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: N/A WITH REASON: Backlog bugfix/debug scope, no Feature Spec bound.
- Task File: documentation\test-runs\BACKLOG-108_contact_fact_routing_debug.md
- Backlog Item: BACKLOG-108
- Pre-Implementation Check: documentation\test-runs\BACKLOG-108_contact_fact_routing_debug.md
- Manual Janus Evidence: N/A WITH REASON: Backend routing/persistence regression scope validated by deterministic unit tests; no local UI/manual browser surface required for this debug delta.
- Pipeline Completion Status: Implementation complete for BACKLOG-108 debug delta; remaining task is re-audit and documentation sync.

## Backlog Item

```text
### BACKLOG-108 - Bestaetigtes Kontaktwissen aus Chat landet nicht im bestehenden Adressbuchkontakt

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** User Intake
- **Erstellt:** 2026-06-07
- **Aktualisiert:** 2026-06-07
- **Kurzbeschreibung:** Wenn Janus in einem laufenden Chat bestaetigtes Wissen zu einem bereits bekannten Kontakt erhaelt, merkt sich das System den Fakt offenbar nur im Memory-/Chat-Kontext, schreibt ihn aber nicht in den bestehenden Adressbuchkontakt zurueck. Dadurch laufen Chat-Wissen und Adressbuch sichtbar auseinander.
- **Erwartetes Verhalten:** Wenn ein bestehender Kontakt im Chat eindeutig referenziert wird und der Nutzer einen klaren Kontaktfakt wie Vorliebe, Abneigung oder Besonderheit bestaetigt oder ergaenzt, sollte dieser Fakt im passenden bestehenden Adressbuchkontakt landen oder als sauberer Kontakt-Update-Vorschlag behandelt werden.
- **Tatsaechliches Verhalten:** Janus bestaetigt Sätze wie `chris liebt starwars` als gemerktes Kontaktwissen ueber `Christoph Gier (Cris)`, hinterlegt diesen Fakt aber nicht im Adressbuchkontakt. Stattdessen bleibt die Information nur im Memory-/Chat-Kontext sichtbar.
- **Reproduktion / Kontext:** Im Chat wurde zuerst nach dem Kurznamen von `Chris Gier` gefragt und Janus antwortete mit `Christoph Gier wird einfach Cris genannt`. Danach folgte `genau. und chris liebt starwars`. Janus antwortete, es habe sich notiert, dass `Christoph Gier (Cris)` ein grosser Star-Wars-Fan sei, bot aber anschliessend sogar noch an, den Fakt erst jetzt in den Kontaktdetails fest zu hinterlegen. Das zeigt, dass Kontaktpersistenz und bestaetigtes Kontaktwissen auseinanderlaufen.
- **Betroffener Bereich:** Chat-Orchestrierung / Kontakt-Memory-Kopplung / Adressbuch / Backend
- **Nachweise:** User-Reproduktion vom 2026-06-07 mit bestehendem Kontakt `Christoph Gier (Cris)`; sichtbare Assistant-Antwort bestaetigt Memory-Merkung ohne Rueckschreiben ins Adressbuch.
- **Akzeptanzkriterien:**
  - [ ] Wenn ein bestehender Kontakt im Chat eindeutig erkannt wird und der Nutzer einen klaren persoenlichen Fakt wie `X liebt Star Wars` nennt, landet dieser Fakt im passenden Kontaktfeld des bestehenden Adressbuchkontakts oder in einem konsistenten bestaetigungs-/proposal-basierten Updatepfad.
  - [ ] Janus behauptet nicht mehr, einen Kontaktfakt fest gemerkt zu haben, wenn dieser nur im Memory-Kontext steht, aber nicht im Kontaktpersistenzpfad angekommen ist.
  - [ ] Die Loesung erzeugt keine ueberaggressive Kontaktmutation fuer unklare oder mehrdeutige Chat-Aussagen.
- **Fehlende Informationen:**
  - Keine
- **Wichtigkeit:** HIGH
- **Umsetzungsrisiko:** MEDIUM
- **Aufwand:** S
- **Umsetzungsreife:** READY
- **Empfehlung:** DO NOW
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Kleiner klarer Bug auf bestehender Kontakt-/Memory-Kopplung ohne neue Produktentscheidung; vor der Umsetzung braucht er einen gebundenen Precheck fuer den bestehenden Kontaktpersistenzpfad.
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-06-07
- **Handoff:** documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md
- **Recommended next skill:** DONE
- **Handoff created:** 2026-06-07
- **Precheck artifact:** documentation/tasks/backlog_BACKLOG-108_preimplementation_check.md
- **Target Task:** BACKLOG-108
- **Completed by task:** `documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md`
- **Completed at:** 2026-06-07
- **Final Audit:** PASS
- **Validation evidence:** `python -m pytest backend/tests/test_contact_manager.py -q` PASS; `python -m pytest backend/tests/test_memory_tools.py -q` PASS; `python -m pytest backend/tests/test_memory_write_update_conflict_handling.py -q` PASS; `python -m py_compile backend/services/chat_orchestrator.py backend/services/contact_manager.py backend/services/memory_extractor.py backend/tools/memory_tools.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py backend/tests/test_memory_write_update_conflict_handling.py` PASS; targeted seam checks PASS via `documentation/test-runs/BACKLOG-108_execution_validation.md`; Final Audit PASS via `documentation/test-runs/BACKLOG-108_final_audit.md`.
- **Notizen:** Verwandt mit dem abgeschlossenen Adressbuch-/Kontakt-Strang aus Spec 15 und Spec 16, aber als neues Folgeproblem in der Chat-zu-Kontakt-Persistenz zu behandeln.
```

## Task Acceptance Scope

```text
SKILL 5 DEBUG RESULT: FIXED

Iteration: 3

Progress-Validierung: Failure Code CONTACT_RECALL_IDENTITY_SUPPRESSION_TOO_BROAD; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
Der Final Audit blockierte den BACKLOG-108-Debug-Fix, weil `_suppress_identity_for_address_book_contact_recall()` zwar die Kontakt-Recall-Formulierung erkannte, aber nur pruefte, ob der uebergebene Kontext nicht leer ist. Am Call Site wurde jedoch `wf.final_system_prompt` uebergeben. Dieser Prompt ist fast immer nicht leer und enthaelt zudem die allgemeine Adressbuch-Regel, auch wenn kein konkreter `**Adressbuch:**`-Treffer mit Kontaktzeile fuer den aktuellen Turn vorliegt. Dadurch konnte die Nutzer-Identity-Directive zu breit unterdrueckt werden.

Vorherige BACKLOG-108-Live-Fehler bleiben Teil des korrigierten Debug-Umfangs:
- Kontaktfakten wie `Chris hasst die AfD` oder `Chris verbringt gerne Zeit im Garten` wurden nicht sicher im bestehenden Adressbuchkontakt verankert.
- `Zeit im Garten` konnte als News-Anfrage fehlgeroutet werden.
- Kontaktwissen-Recall wie `was mag chris?` oder `was weisst du ueber chris gier?` konnte Web/Wikipedia/Ambiguity statt lokales Kontaktwissen nutzen.
- Die globale Nutzer-Identity-Directive konnte Chris als Nutzer statt als Kontakt darstellen.
- Diaet-/Vorlieben-Fakten wie `Chris ist Vegetarier` kamen nicht deterministisch als Kontakt-Preference im Adressbuch an.

Fix Summary:
Die Identity-Suppression ist jetzt eng an einen konkreten Adressbuch-Kontakt-Treffer gebunden. `_suppress_identity_for_address_book_contact_recall()` gibt nur noch `True` zurueck, wenn der Kontext eine echte `**Adressbuch:**`-Sektion mit mindestens einer `Kontakt:`-Zeile enthaelt. Die allgemeine Prompt-Regel `[ADRESSBUCH-KONTAKTE]` reicht nicht mehr aus.

Zusätzlich bleibt Self-Recall geschuetzt: Fragen wie `was weisst du ueber mich?` oder Namensfragen unterdruecken die Nutzer-Identity-Directive auch dann nicht, wenn im Prompt ein Adressbuchkontext vorhanden ist.

Der vorherige BACKLOG-108-Fix bleibt erhalten:
- bestehende Kontakte werden ueber Name/Nickname/Alias gefunden,
- sichere bestaetigte Chat-Fakten werden direkt als `preferences`/`dislikes` am bestehenden Kontakt angewendet,
- `Zeit` ist nur noch mit Quellenkontext wie `die Zeit` oder `Zeit Online` ein News-Marker,
- Kontaktwissensfragen werden als `personal_recall` erkannt und externe Suche/RSS/Wikipedia/Ambiguity werden fuer diesen lokalen Recall vetoed,
- der Adressbuch-Kontext liefert strukturierte Vorlieben, Abneigungen und Details,
- explizite Kontaktfakten bleiben in der Memory-Normalisierung Kontakte und werden nicht zu `user` normalisiert,
- Diaet-Praeferenzen wie `Vegetarier` werden als Kontakt-Vorliebe erkannt.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_calendar_routing_fix.py -q` PASS, 26 passed
  - `python -m pytest backend/tests/test_contact_manager.py -q` PASS, 17 passed
  - `python -m py_compile backend/services/orchestrator/execution_dispatcher.py backend/tests/test_calendar_routing_fix.py` PASS

Artifact Identity Check: PASS

Final Feature Suite: PASS

Changed Files:
- `backend/services/contact_manager.py`
- `backend/services/orchestrator/intent_engine.py`
- `backend/services/chat/context_builder.py`
- `backend/services/orchestrator/execution_dispatcher.py`
- `backend/services/memory_extractor.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_calendar_routing_fix.py`

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts: `documentation/test-runs/BACKLOG-108_contact_fact_routing_debug.md`; `documentation/test-runs/BACKLOG-108_contact_fact_routing_final_audit.md`; `documentation/test-runs/BACKLOG-108_AUDIT_PACKAGE.md`
Evidence Paths: `backend/tests/test_contact_manager.py`; `backend/tests/test_calendar_routing_fix.py`; `backend/services/contact_manager.py`; `backend/services/orchestrator/intent_engine.py`; `backend/services/chat/context_builder.py`; `backend/services/orchestrator/execution_dispatcher.py`; `backend/services/memory_extractor.py`
Failure Code: CONTACT_RECALL_IDENTITY_SUPPRESSION_TOO_BROAD
Changed Files: `backend/services/contact_manager.py`, `backend/services/orchestrator/intent_engine.py`, `backend/services/chat/context_builder.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/memory_extractor.py`, `backend/tests/test_contact_manager.py`, `backend/tests/test_calendar_routing_fix.py`
Decision: Re-audit required before documentation update and git checkpoint.
Reason: Final Audit blocker was fixed with a narrow identity-suppression gate and new positive/negative regression evidence.
Recommended Model: 5.5
Recommended Intelligence: hoch
Next User Action: Freigabe fuer janus-final-audit oder weiterer manueller Live-Test.
```

## Pre-Implementation Check

```text
SKILL 5 DEBUG RESULT: FIXED

Iteration: 3

Progress-Validierung: Failure Code CONTACT_RECALL_IDENTITY_SUPPRESSION_TOO_BROAD; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
Der Final Audit blockierte den BACKLOG-108-Debug-Fix, weil `_suppress_identity_for_address_book_contact_recall()` zwar die Kontakt-Recall-Formulierung erkannte, aber nur pruefte, ob der uebergebene Kontext nicht leer ist. Am Call Site wurde jedoch `wf.final_system_prompt` uebergeben. Dieser Prompt ist fast immer nicht leer und enthaelt zudem die allgemeine Adressbuch-Regel, auch wenn kein konkreter `**Adressbuch:**`-Treffer mit Kontaktzeile fuer den aktuellen Turn vorliegt. Dadurch konnte die Nutzer-Identity-Directive zu breit unterdrueckt werden.

Vorherige BACKLOG-108-Live-Fehler bleiben Teil des korrigierten Debug-Umfangs:
- Kontaktfakten wie `Chris hasst die AfD` oder `Chris verbringt gerne Zeit im Garten` wurden nicht sicher im bestehenden Adressbuchkontakt verankert.
- `Zeit im Garten` konnte als News-Anfrage fehlgeroutet werden.
- Kontaktwissen-Recall wie `was mag chris?` oder `was weisst du ueber chris gier?` konnte Web/Wikipedia/Ambiguity statt lokales Kontaktwissen nutzen.
- Die globale Nutzer-Identity-Directive konnte Chris als Nutzer statt als Kontakt darstellen.
- Diaet-/Vorlieben-Fakten wie `Chris ist Vegetarier` kamen nicht deterministisch als Kontakt-Preference im Adressbuch an.

Fix Summary:
Die Identity-Suppression ist jetzt eng an einen konkreten Adressbuch-Kontakt-Treffer gebunden. `_suppress_identity_for_address_book_contact_recall()` gibt nur noch `True` zurueck, wenn der Kontext eine echte `**Adressbuch:**`-Sektion mit mindestens einer `Kontakt:`-Zeile enthaelt. Die allgemeine Prompt-Regel `[ADRESSBUCH-KONTAKTE]` reicht nicht mehr aus.

Zusätzlich bleibt Self-Recall geschuetzt: Fragen wie `was weisst du ueber mich?` oder Namensfragen unterdruecken die Nutzer-Identity-Directive auch dann nicht, wenn im Prompt ein Adressbuchkontext vorhanden ist.

Der vorherige BACKLOG-108-Fix bleibt erhalten:
- bestehende Kontakte werden ueber Name/Nickname/Alias gefunden,
- sichere bestaetigte Chat-Fakten werden direkt als `preferences`/`dislikes` am bestehenden Kontakt angewendet,
- `Zeit` ist nur noch mit Quellenkontext wie `die Zeit` oder `Zeit Online` ein News-Marker,
- Kontaktwissensfragen werden als `personal_recall` erkannt und externe Suche/RSS/Wikipedia/Ambiguity werden fuer diesen lokalen Recall vetoed,
- der Adressbuch-Kontext liefert strukturierte Vorlieben, Abneigungen und Details,
- explizite Kontaktfakten bleiben in der Memory-Normalisierung Kontakte und werden nicht zu `user` normalisiert,
- Diaet-Praeferenzen wie `Vegetarier` werden als Kontakt-Vorliebe erkannt.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_calendar_routing_fix.py -q` PASS, 26 passed
  - `python -m pytest backend/tests/test_contact_manager.py -q` PASS, 17 passed
  - `python -m py_compile backend/services/orchestrator/execution_dispatcher.py backend/tests/test_calendar_routing_fix.py` PASS

Artifact Identity Check: PASS

Final Feature Suite: PASS

Changed Files:
- `backend/services/contact_manager.py`
- `backend/services/orchestrator/intent_engine.py`
- `backend/services/chat/context_builder.py`
- `backend/services/orchestrator/execution_dispatcher.py`
- `backend/services/memory_extractor.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_calendar_routing_fix.py`

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts: `documentation/test-runs/BACKLOG-108_contact_fact_routing_debug.md`; `documentation/test-runs/BACKLOG-108_contact_fact_routing_final_audit.md`; `documentation/test-runs/BACKLOG-108_AUDIT_PACKAGE.md`
Evidence Paths: `backend/tests/test_contact_manager.py`; `backend/tests/test_calendar_routing_fix.py`; `backend/services/contact_manager.py`; `backend/services/orchestrator/intent_engine.py`; `backend/services/chat/context_builder.py`; `backend/services/orchestrator/execution_dispatcher.py`; `backend/services/memory_extractor.py`
Failure Code: CONTACT_RECALL_IDENTITY_SUPPRESSION_TOO_BROAD
Changed Files: `backend/services/contact_manager.py`, `backend/services/orchestrator/intent_engine.py`, `backend/services/chat/context_builder.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/memory_extractor.py`, `backend/tests/test_contact_manager.py`, `backend/tests/test_calendar_routing_fix.py`
Decision: Re-audit required before documentation update and git checkpoint.
Reason: Final Audit blocker was fixed with a narrow identity-suppression gate and new positive/negative regression evidence.
Recommended Model: 5.5
Recommended Intelligence: hoch
Next User Action: Freigabe fuer janus-final-audit oder weiterer manueller Live-Test.
```

## Changed Files

```text
M backend/services/chat/context_builder.py
 M backend/services/contact_manager.py
 M backend/services/memory_extractor.py
 M backend/services/orchestrator/execution_dispatcher.py
 M backend/services/orchestrator/intent_engine.py
 M backend/tests/test_calendar_routing_fix.py
 M backend/tests/test_contact_manager.py
 M documentation/codex/SKILL_USAGE_LOG.md
?? documentation/test-runs/BACKLOG-108_contact_fact_routing_debug.md
?? documentation/test-runs/BACKLOG-108_contact_fact_routing_final_audit.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-Projekt\documentation\test-runs\BACKLOG-108_contact_fact_routing_debug.md (4844 bytes)
FILE C:\KI\Janus-Projekt\documentation\test-runs\BACKLOG-108_contact_fact_routing_final_audit.md (4524 bytes)
```

## Diff Summary

```text
backend/services/chat/context_builder.py           |  66 ++++++--
 backend/services/contact_manager.py                |  89 +++++++---
 backend/services/memory_extractor.py               |   5 +-
 .../services/orchestrator/execution_dispatcher.py  |  24 +++
 backend/services/orchestrator/intent_engine.py     |  34 +++-
 backend/tests/test_calendar_routing_fix.py         | 104 ++++++++++++
 backend/tests/test_contact_manager.py              | 188 +++++++++++++++++++++
 documentation/codex/SKILL_USAGE_LOG.md             |   6 +
 8 files changed, 475 insertions(+), 41 deletions(-)
```

## Validation

```text
Validation evidence not provided.
```

## Notes

No additional notes provided.

## Risks

Memory/contact routing is privacy-sensitive; audit must verify contact facts are not normalized to user identity and external/news routes are vetoed for local contact recall.

## Open Issues

Unrelated dirty files remain outside audit scope: backend/services/chat_orchestrator.py, backend/tests/unit/test_chat_mail_provider_content_type_probe.py, documentation/logs/.

## Re-Audit Delta

Primary blocker: CONTACT_RECALL_IDENTITY_SUPPRESSION_TOO_BROAD

Identity suppression now requires a concrete **Adressbuch:** section with Kontakt: row and keeps self recall/name recall identity directive enabled; added positive and negative regressions in backend/tests/test_calendar_routing_fix.py.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.5/high
PASS: C:\KI\Janus-Projekt\documentation\test-runs\BACKLOG-108_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Change the model/reasoning to `5.5/high`, paste the block above into a fresh chat, write `ok`, and the final audit starts immediately.

For bounded same-thread re-audits after a local blocker fix, `5.4/high` is acceptable when the package stays compact and the risk did not escalate.

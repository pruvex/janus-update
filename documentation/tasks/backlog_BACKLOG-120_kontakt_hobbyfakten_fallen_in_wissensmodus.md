# BACKLOG-120 - Neue Kontakt-Hobbyfakten fuer bestehenden Kontakt werden als unverifizierbare Wissensfrage abgewehrt

## Handoff Scope

- **Backlog Item:** BACKLOG-120
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Required Next Skill:** SKILL 3 - PRE-IMPLEMENTATION VERIFICATION
- **Target Task:** BACKLOG-120
- **Source Backlog:** `documentation/backlog/BACKLOG.md`

## Problem

Janus kann bestehende Kontaktbeziehungen fuer `Nathan` inzwischen korrekt finden, behandelt aber einen neuen klaren Hobby-/Vorliebenfakt wie `Nathan spielt gerne League of Legends` noch nicht als lokales Kontaktwissen. Statt den Fakt ueber den Kontakt-/Memory-Pfad zu speichern, kippt die Antwort in einen Verifikations-/Wissensmodus mit Rueckfrage nach "ueberpruefbaren Fakten".

## Expected Behavior

- Ein klar formulierter neuer Kontaktfakt fuer einen bereits bekannten Kontakt wird als lokales Kontaktwissen erkannt.
- Die Aussage `Nathan spielt gerne League of Legends` fuehrt zu einer passenden lokalen Merkbestaetigung statt zu einer Recherche-/Verifikationsrueckfrage.
- Der Fakt landet fuer Nathan in einem konsistenten lokalen Kontakt-/Vorliebenpfad und bleibt spaeter chatuebergreifend recallbar.
- Die Loesung bleibt bounded: generische Wissensfragen zu Spielen, Rankings, Teams oder externen Fakten duerfen nicht ueberaggressiv als Kontaktwissen gespeichert werden.

## Reproduction Context

User-Live-Repro vom 2026-07-02:

1. `Nathan Raimann` ist bereits als bestehender Kontakt bekannt.
2. Der Elena-/Beziehungsfall funktioniert nach `BACKLOG-119` wieder korrekt.
3. Neuer Prompt: `nathan spielt gerne league of legends`
4. Janus antwortet sinngemaess:
   `Ich habe dazu keine ueberpruefbaren Fakten. Welche Information benoetigst du genau ueber Nathan und League of Legends ...?`
5. Der neue Kontaktfakt wird damit weder sauber gespeichert noch als lokales Kontaktwissen bestaetigt.

## Acceptance Criteria

- [ ] Ein klarer neuer Hobby-, Vorlieben- oder Freizeitfakt fuer einen bereits bekannten Kontakt wird als lokales Kontaktwissen erkannt statt als externe Wissensfrage behandelt.
- [ ] Die Aussage `Nathan spielt gerne League of Legends` fuehrt zu einer passenden lokalen Merkbestaetigung oder einer gleichwertig klaren Speicherbestaetigung.
- [ ] Der neue Fakt landet fuer Nathan in einem konsistenten lokalen Kontakt-/Vorliebenpfad und ist spaeter chatuebergreifend recallbar.
- [ ] Die Loesung bleibt auf klare Kontaktfaktaussagen begrenzt und fuehrt nicht dazu, dass unklare oder generische Gaming-/Wissensanfragen ueberaggressiv als Kontaktwissen gespeichert werden.
- [ ] Die bestehende gruen gewordene `BACKLOG-119`-Beziehungsstrecke bleibt unveraendert stabil.

## Suggested Scope For Precheck

- **Primary seam:** Kontaktfakt-Erkennung und lokaler Kontakt-/Memory-Write-Pfad fuer klare Drittperson-Hobbyfakten bei bereits bekannten Kontakten
- **Likely files:**
  - `backend/services/orchestrator/intent_engine.py`
  - `backend/services/memory_extractor.py`
  - `backend/services/contact_manager.py`
  - `backend/tests/test_calendar_routing_fix.py`
  - `backend/tests/test_contact_manager.py`
- **Out of scope:**
  - allgemeine Spiele-/Recherche- oder Wissensfragen
  - breites Redesign der Intent-Hierarchie
  - neue UI fuer Kontaktvorlieben
  - ungebundene Aenderungen am bestehenden `BACKLOG-119`-Audit-Paket

## Evidence Paths

- `documentation/backlog/BACKLOG.md`
- `documentation/ai/CURRENT_STATE.md`
- User-Live-Repro vom 2026-07-02 mit der Antwort auf `nathan spielt gerne league of legends`
- benachbarte gruene Kontaktvorlieben-Tests in `backend/tests/test_contact_manager.py`

## Dropped Context

- unrelated READY backlog items
- OR infrastructure items
- broad DONE history
- detailed `BACKLOG-119` audit bundle beyond the fact that it should stay green

## Next Skill Copy Prompt

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-120
Task: documentation/tasks/backlog_BACKLOG-120_kontakt_hobbyfakten_fallen_in_wissensmodus.md
Backlog Item: BACKLOG-120
```

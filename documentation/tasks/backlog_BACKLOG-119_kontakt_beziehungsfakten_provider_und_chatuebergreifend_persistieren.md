# BACKLOG-119 - Kontakt-Beziehungsfakten werden nicht provider- und chatuebergreifend persistiert

## Handoff Scope

- **Backlog Item:** BACKLOG-119
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Required Next Skill:** SKILL 3 - PRE-IMPLEMENTATION VERIFICATION
- **Target Task:** BACKLOG-119
- **Source Backlog:** `documentation/backlog/BACKLOG.md`

## Problem

Janus kann einen neuen Kontakt wie `Nathan Raimann` korrekt anlegen, verliert aber einen spaeter von einem anderen Provider bestaetigten Beziehungsfakt wie `Nathans Freundin heisst Elena` zwischen Chat-, Memory- und Adressbuchpfad. Dadurch ist die Beziehung weder sauber im Adressbuch sichtbar noch spaeter in einem anderen Chat verlaesslich recallbar.

## Expected Behavior

- Klare Kontakt-Beziehungsfakten wie `Xs Freundin/Freund heisst Y` werden in einen konsistenten lokalen Kontakt-/Beziehungspfad geschrieben.
- Eine spaetere Rueckfrage wie `Wer ist Nathans Freundin?` kann in einem anderen Chat und mit einem anderen Modell korrekt aus lokalem Wissen beantwortet werden.
- Der Beziehungsfakt bleibt bounded und ambiguity-safe: unklare Aussagen duerfen keine aggressive Kontakt- oder Beziehungsanlage ausloesen.

## Reproduction Context

User-Live-Repro vom 2026-07-02:

1. GPT-Chat: `mein bester freund, der nathan raimann wohnt in berlin`
2. Janus legt `Nathan Raimann` korrekt als Kontakt an.
3. Gemini-Chat: `nathans freundin heisst elena`
4. Gemini bestaetigt sinngemaess, dass `Elena` die Freundin von Nathan sei bzw. dass es sich den Fakt gemerkt habe.
5. GPT-Chat in anderem Verlauf: `wer ist nathans freundin?`
6. Janus antwortet, dass keine verlaessliche Information dazu vorliege.

## Acceptance Criteria

- [ ] Ein klarer Kontakt-Beziehungsfakt wie `Nathans Freundin heisst Elena` wird nicht nur bestaetigt, sondern gelangt in einen konsistenten lokalen Kontakt-/Beziehungspfad.
- [ ] Derselbe Fakt ist danach in einem anderen Chat und mit einem anderen Modell korrekt recallbar.
- [ ] Der Fakt landet im passenden Adressbuch-/Kontaktkontext oder in einem gleichwertig konsistenten lokalen Beziehungspfad statt unsichtbar zu bleiben.
- [ ] Unklare oder mehrdeutige Aussagen fuehren nicht zu ueberaggressiver Kontaktanlage oder falscher Beziehungszuordnung.
- [ ] Bereits bestehende Kontaktpersistenz-/Memory-Regressionen auf dem BACKLOG-108-Pfad bleiben gruen oder werden gezielt erweitert.

## Suggested Scope For Precheck

- **Primary seam:** bestehender Kontakt-/Memory-Persistenzpfad fuer klare Chatfakten zu bekannten oder gerade angelegten Kontakten
- **Likely files:**
  - `backend/services/chat_orchestrator.py`
  - `backend/services/contact_manager.py`
  - `backend/services/memory_extractor.py`
  - `backend/tools/memory_tools.py`
  - `backend/data/crud.py`
  - passende fokussierte Backend-Tests im Kontakt-/Memory-Bereich
- **Out of scope:**
  - breites Redesign des Kontaktmodells
  - allgemeine Social-Graph-Features
  - ungebundene UI-Neugestaltung des Adressbuchs
  - aggressive Auto-Verknuepfung fuer schwache oder unscharfe Aussagen

## Evidence Paths

- `documentation/backlog/BACKLOG.md`
- `documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md`
- User-Live-Repro vom 2026-07-02, dokumentiert in BACKLOG-119

## Dropped Context

- unrelated READY backlog items
- OR infrastructure and live-test lane work
- broad DONE history outside the contact-/memory-persistence seam

## Next Skill Copy Prompt

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-119
Task: documentation/tasks/backlog_BACKLOG-119_kontakt_beziehungsfakten_provider_und_chatuebergreifend_persistieren.md
Backlog Item: BACKLOG-119
```

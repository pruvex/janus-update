# BACKLOG-116 - Garfield-Thunfisch-Fakt wird bei Haustieruebersicht nicht pet-spezifisch genannt

## Handoff Scope

- **Backlog Item:** BACKLOG-116
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Required Next Skill:** SKILL 3 - PRE-IMPLEMENTATION VERIFICATION
- **Target Task:** BACKLOG-116
- **Source Backlog:** `documentation/backlog/BACKLOG.md`

## Problem

Janus kann den Fakt `Garfield mag Thunfisch ueberhaupt nicht` auf direkte Nachfrage korrekt wiedergeben, nennt ihn aber nicht in der aggregierten Antwort auf `was weisst du alles ueber olis haustiere?`. Laut Nutzer steht der Fakt im Adressbuch zudem bei Olis allgemeinen Informationen statt bei den Haustierinformationen.

## Expected Behavior

- Pet-spezifische Fakten werden beim passenden Haustier persistiert bzw. angezeigt.
- Die Haustieruebersicht zu Oli nennt bekannte relevante Details zu Tasso und Garfield vollstaendig und getrennt.
- Negative Praeferenzen/Futter-Abneigungen wie `mag Thunfisch ueberhaupt nicht` werden in der aggregierten Haustierantwort nicht ausgelassen.

## Reproduction Context

User-Live-Befund vom 2026-07-01:

1. `garfield mag thunfisch ueberhaupt nicht`
2. Janus bestaetigt, dass der Fakt gespeichert/vermerkt wurde.
3. `ok, also was weisst du alles ueber olis haustiere?`
4. Janus antwortet sinngemaess:
   - `Tasso (Hund): ist ein podenco; frisst gerne thunfisch.`
   - `Garfield (Katze).`
5. `und was mag garfield nicht?`
6. Janus antwortet korrekt: `Garfield mag Thunfisch ueberhaupt nicht.`

## Acceptance Criteria

- [ ] Ein pet-spezifischer Fakt wie `Garfield mag Thunfisch ueberhaupt nicht` wird nicht als allgemeiner Oli-Fakt persistiert oder angezeigt, sondern dem Haustier `Garfield` zugeordnet.
- [ ] Die aggregierte Antwort auf `was weisst du alles ueber olis haustiere?` nennt bekannte relevante Details zu Garfield inklusive negativer Praeferenz/Futter-Abneigung.
- [ ] Die direkte Detailfrage `was mag Garfield nicht?` bleibt korrekt.
- [ ] Tasso-Fakten und Garfield-Fakten werden in der Antwort nicht vermischt, ueberschrieben oder wegen gleicher Objektklasse `Thunfisch` dedupliziert.
- [ ] Bestehende BACKLOG-115-Dedupe-/Normalisierungstests bleiben gruen oder werden mit einem fokussierten Regressionstest fuer diesen Fall erweitert.

## Evidence Paths

- `documentation/backlog/BACKLOG.md`
- User-Live-Chat vom 2026-07-01, dokumentiert in BACKLOG-116

## Dropped Context

- Unrelated READY backlog items.
- Broad DONE history outside the Oliver/Tasso/Garfield pet-detail path.
- Git, release, and dashboard-governance work not needed for the bug diagnosis.

## Next Skill Copy Prompt

```text
@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-116
Task: documentation/tasks/backlog_BACKLOG-116_garfield_thunfisch_fakt_haustieruebersicht.md
Backlog Item: BACKLOG-116
```

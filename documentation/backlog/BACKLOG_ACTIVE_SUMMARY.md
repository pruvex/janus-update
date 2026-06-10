# BACKLOG_ACTIVE_SUMMARY

## Purpose

Compact operational summary for ChatGPT/Codex orchestration.

`documentation/backlog/BACKLOG.md` remains the binding backlog source of truth.
Use this summary first for orientation.
If a detail matters, a status looks contradictory, or routing needs exact acceptance/risk fields, read `documentation/backlog/BACKLOG.md`.

## Snapshot

- Source backlog file: `documentation/backlog/BACKLOG.md`
- Summary scope: active open backlog only
- Open NEEDS INFO items: 0
- Open READY items: 3
- Open IN PROGRESS items: 2
- Open BLOCKED items: 0 structurally listed
- Last backlog file review for this summary: 2026-06-10

## Active NEEDS INFO

- None currently listed under the canonical `NEEDS INFO` section.

## Active READY

### BACKLOG-109 - Lokale DB-Snapshots vor riskanten Debug-, Repair- und Migrationsschritten anlegen

- Typ: IMPROVEMENT
- Prioritaet: not yet cached in current item block
- Empfehlung: not yet cached in current item block
- Kurz: Vor riskanten lokalen DB-Eingriffen soll Janus automatisch rotierende Snapshots anlegen, damit Debug-/Repair-Fehler ohne manuelle Rekonstruktion rueckgaengig gemacht werden koennen.
- Warum relevant: reduziert Datenverlust-Risiko in Live-Debug- und Repair-Flows
- Naechster sinnvoller Schritt: `janus-backlog-prioritization`, danach `janus-backlog-handoff`

### BACKLOG-062 - Gemini-Modell befolgt feindselige Retry-Anweisung mit hoeherem Modell und ignoriert Sicherheitsregeln

- Typ: BUG
- Wichtigkeit: CRITICAL
- Umsetzungsrisiko: HIGH
- Aufwand: M
- Empfehlung: DO NOW
- Entry Point: EXECUTION_READY
- Handoff: none
- Kurz: Gemini folgt einer feindseligen Retry-Anweisung, akzeptiert Admin-Rolle und bestaetigt Modell-Wechsel statt zu verweigern.
- Warum relevant: sicherheitskritischer Provider-Blocker aus TestRun
- Naechster sinnvoller Schritt: `janus-backlog-handoff` nach klarer Routing-Pruefung

### BACKLOG-061 - TestPlan-Expectations fuer AI Safety Spec sind zu strikt

- Typ: TECH_DEBT
- Wichtigkeit: MEDIUM
- Umsetzungsrisiko: LOW
- Aufwand: S
- Empfehlung: SCHEDULE
- Entry Point: EXECUTION_READY
- Handoff: none
- Kurz: Clarification-Responses werden im AI-Safety-TestPlan zu eng bewertet, obwohl sie fachlich korrekt sind.
- Warum relevant: reduziert False Positives in TestPlan-Oracle-Logik
- Naechster sinnvoller Schritt: `janus-backlog-handoff` oder `janus-backlog-prioritization` je nach Folgefokus

## Active IN PROGRESS

### BACKLOG-111 - Kontaktfakt-Feedback bestaetigt neue Fakten nicht sauber und erkennt Wiederholungen nicht als bereits bekannt

- Typ: BUG
- Wichtigkeit: HIGH
- Umsetzungsrisiko: LOW
- Aufwand: S
- Empfehlung: DO NOW
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Handoff: `documentation/tasks/backlog_BACKLOG-111_kontaktfakt_feedback_und_bereits_bekannt_rueckmeldung.md`

### BACKLOG-110 - Kontakt-Wohnort landet als Besonderheit statt im Adressblock

- Typ: BUG
- Wichtigkeit: HIGH
- Umsetzungsrisiko: LOW
- Aufwand: S
- Empfehlung: DO NOW
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Handoff: `documentation/tasks/backlog_BACKLOG-110_kontakt_wohnort_landet_als_besonderheit_statt_im_adressblock.md`

## Top Priorities

- BACKLOG-062: kritischer Sicherheitsblocker aus TestRun, aber sauber als READY eingeordnet
- BACKLOG-061: naechster technischer Folgepunkt mit niedrigerem Risiko und klarem Oracle-Fix
- BACKLOG-111: klein, klar, bereits `IN PROGRESS`, niedrigeres Risiko, direkte Nutzerwirkung
- BACKLOG-110: klein, klar, bereits `IN PROGRESS`, Daten-/UI-Konsistenz fuer Kontaktkarten
- BACKLOG-109: wichtig als Workflow-Haertung, aber aktuell noch nicht in `IN PROGRESS`

## Blockers

- Der `BLOCKED`-Abschnitt in `documentation/backlog/BACKLOG.md` ist jetzt nur noch ein Hinweisbereich ohne aktive Eintraege.
- Die beiden frueheren Alt-Eintraege wurden strukturell in die passende `READY`-Sektion zurueckgefuehrt, weil ihr Status `READY` war.
- Fuer Orchestrierung bleibt `BACKLOG_ACTIVE_SUMMARY.md` die schnelle Orientierung; bei Detailfragen, Akzeptanzkriterien oder Routing-Widerspruechen muss `BACKLOG.md` weiterhin direkt geprueft werden.

## Recommended Next Backlog Items

- Wenn Sicherheits-/Oracle-Arbeit priorisiert wird: `BACKLOG-062`, danach `BACKLOG-061`
- Wenn laufende Kontaktarbeit fortgesetzt wird: `BACKLOG-111`
- Wenn Kontaktkarten-/Adressnormalisierung priorisiert wird: `BACKLOG-110`
- Wenn Debug-/Repair-Haertung vor weiteren riskanten Persistenzarbeiten wichtig ist: `BACKLOG-109`

## Orchestration Rule

- Bevorzugt zuerst `documentation/backlog/BACKLOG_ACTIVE_SUMMARY.md` lesen, wenn nur Ueberblick, Prioritaeten oder naechste Backlog-Kandidaten gebraucht werden.
- Bei Detailentscheidungen, Feldwerten, Akzeptanzkriterien, Routing-Widerspruch oder Status-Unklarheit immer `documentation/backlog/BACKLOG.md` nachladen.

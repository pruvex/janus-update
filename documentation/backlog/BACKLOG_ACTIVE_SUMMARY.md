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
- Open READY items: 1
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

- BACKLOG-111: klein, klar, bereits `IN PROGRESS`, niedrigeres Risiko, direkte Nutzerwirkung
- BACKLOG-110: klein, klar, bereits `IN PROGRESS`, Daten-/UI-Konsistenz fuer Kontaktkarten
- BACKLOG-109: wichtig als Workflow-Haertung, aber aktuell noch nicht in `IN PROGRESS`

## Blockers

- Der `BLOCKED`-Abschnitt in `documentation/backlog/BACKLOG.md` ist strukturell inkonsistent: dort stehen derzeit zwei offene Alt-Eintraege ohne `### BACKLOG-XXX`-Ueberschrift und mit `Status: READY`.
- Fuer Orchestrierung bedeutet das: `BACKLOG_ACTIVE_SUMMARY.md` eignet sich fuer den schnellen Ueberblick, aber bei Sicherheits- oder Blockerfragen muss `BACKLOG.md` direkt geprueft werden.
- Es gibt aktuell keine sauber strukturierten aktiven `BLOCKED`-Items im kanonischen Format.

## Recommended Next Backlog Items

- Wenn laufende Kontaktarbeit fortgesetzt wird: `BACKLOG-111`
- Wenn Kontaktkarten-/Adressnormalisierung priorisiert wird: `BACKLOG-110`
- Wenn Debug-/Repair-Haertung vor weiteren riskanten Persistenzarbeiten wichtig ist: `BACKLOG-109`

## Orchestration Rule

- Bevorzugt zuerst `documentation/backlog/BACKLOG_ACTIVE_SUMMARY.md` lesen, wenn nur Ueberblick, Prioritaeten oder naechste Backlog-Kandidaten gebraucht werden.
- Bei Detailentscheidungen, Feldwerten, Akzeptanzkriterien, Routing-Widerspruch oder Status-Unklarheit immer `documentation/backlog/BACKLOG.md` nachladen.

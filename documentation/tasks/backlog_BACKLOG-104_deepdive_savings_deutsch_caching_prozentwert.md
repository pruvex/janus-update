BACKLOG-104
- Backlog Item: `BACKLOG-104`
- Source: `documentation/backlog/BACKLOG.md`
- Generated At: 2026-06-05

## Task

### BACKLOG-104 DeepDive Savings deutsch benennen und Janus-Caching-Erklaerung mit Prozentwert ergaenzen
- Ziel:
  - Bereinige die sichtbare DeepDive-Terminologie rund um `Savings`, sodass Nutzer durchgaengig deutsche Formulierungen sehen, und erweitere die zentrale Ersparnis-Kachel um eine klare Janus-Caching-Erklaerung inklusive Prozentwert.
- Scope:
  - Touch only the existing DeepDive rendering and visible text/helpers in the current cost visualizer surface.
  - Do not add backend tracking, API contract changes, or a new DeepDive surface.
- Files:
  - `frontend/js/cost-visualizer.js`
  - `tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js`
- Steps:
  1. Ersetze sichtbare Nutzertexte mit `Savings` durch deutsche Ersparnis-Formulierungen in Uebersicht, Drilldown, Badges und Signals.
  2. Erweitere die zentrale Ersparnis-Kachel so, dass sie die Ersparnis explizit als Janus-Caching-Effekt erklaert.
  3. Zeige in der Ersparnis-Kachel neben dem absoluten Betrag einen nachvollziehbaren Prozentwert auf Basis der bereits vorhandenen Kosten- und Savings-Daten.
  4. Halte die Berechnung und Beschriftung konsistent ueber die wichtigsten DeepDive-Teilansichten hinweg.
- Acceptance Criteria:
  - Sichtbare Nutzertexte im DeepDive verwenden `Ersparnis` oder passende deutsche Formulierungen statt `Savings`.
  - Die zentrale Ersparnis-Kachel erklaert explizit, dass die Ersparnis durch Janus-Caching entsteht.
  - Die Ersparnis-Kachel zeigt neben dem absoluten Betrag einen Prozentwert fuer die durch Caching erzielte Ersparnis.
  - Die Prozentanzeige basiert auf einem klaren, konsistenten Verhaeltnis aus Kosten und erspartem Anteil.
  - Die wichtigsten sichtbaren DeepDive-Drilldowns bleiben ohne deutsch-englisches Mischbild.
- Tests:
  - `node --check frontend/js/cost-visualizer.js`
  - `npx playwright test tests/e2e/generated/BACKLOG-103-ui-smoke.spec.js --headed --workers=1 --reporter=list`
- Model: 5.4
- Reason:
  - Small bounded frontend UX/text pass on one existing surface with no architecture or data-contract change.

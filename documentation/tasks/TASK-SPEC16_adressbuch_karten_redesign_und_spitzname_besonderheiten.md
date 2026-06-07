TASK-SPEC16
- Source Spec: `documentation/SPEC/16_adressbuch_karten_redesign_und_spitzname_besonderheiten.md`
- Backlog Item: `N/A`
- Feature: Adressbuch-Karten Redesign und Spitzname/Besonderheiten-Struktur
- Generated At: 2026-06-07

## Generated Tasks

### TASK-SPEC16.1 Add nickname persistence and preserve existing details/notes compatibility
- Ziel:
  - Erweitere das bestehende Kontaktmodell um einen persistierten Kurz-/Spitznamen und halte bestehende Detail-/Notizinhalte bei der Umstellung auf `Besonderheiten` kompatibel.
- Scope:
  - Nur bestehende Kontakt-Persistenz-, Schema- und CRUD-Pfade fuer das Adressbuch, inklusive Rueckgabe und Speicherung des neuen Felds sowie klarer Weiterfuehrung bestehender persoenlicher Detail-/Notizinhalte.
- Files:
  - `backend/data/models.py`
  - `backend/data/contact_schemas.py`
  - `backend/data/crud.py`
  - `backend/data/database.py`
  - `backend/tests/test_contact_manager.py`
- Steps:
  1. Fuehre ein neues persistentes Feld fuer Kurz-/Spitzname im bestehenden Kontaktmodell ein.
  2. Erweitere die relevanten Kontakt-Schemas und CRUD-Pfade so, dass das neue Feld gespeichert, geladen und zurueckgegeben wird.
  3. Stelle sicher, dass bestehende persoenliche Detail-/Notizinhalte bei der Umstellung auf `Besonderheiten` nicht verloren gehen und weiterhin lesbar bleiben.
  4. Ergänze fokussierte Regressionen fuer Speichern und Wiederladen des neuen Felds sowie fuer die Kompatibilitaet alter Kontaktinhalte.
- Acceptance Criteria:
  - Ein Kontakt kann einen Kurz-/Spitznamen speichern und beim erneuten Laden wieder erhalten.
  - Bestehende Kontakte ohne Spitzname bleiben gueltig und laden weiterhin ohne Fehler.
  - Inhalte aus bisherigen Detail-/Notizkontexten gehen durch die Umstellung nicht verloren.
  - Es entsteht keine Aenderung an Memory-, Vorschlags- oder Sync-Logik ausserhalb des benoetigten Kontaktfeld-Contracts.
- Tests:
  - `pytest backend/tests/test_contact_manager.py -q`
  - `python -m py_compile backend/data/models.py backend/data/contact_schemas.py backend/data/crud.py backend/data/database.py`
- Model: 5.4
- Reason:
  - Bounded persistence and schema work on one existing feature area with moderate state complexity.

### TASK-SPEC16.2 Rebuild the address book cards and contact dialog around nickname and clear personal sections
- Ziel:
  - Modernisiere die bestehende Kartenansicht und den Kontakt-Dialog so, dass Spitzname, Vorlieben, Abneigungen und Besonderheiten konsistent und Janus-passend dargestellt werden.
- Scope:
  - Nur bestehendes Adressbuch-Rendering, Kontaktformular und die benoetigten UI-Styles fuer Karten- und Dialogstruktur auf derselben Surface.
- Files:
  - `frontend/js/settings.js`
  - `frontend/css/settings.css`
  - `frontend/index.html`
- Steps:
  1. Passe die Kontaktkarten so an, dass interne Herkunfts-/Ergebnis-/Statusinformationen nicht mehr als primaerer Karteninhalt erscheinen.
  2. Zeige den vollen Namen als Hauptzeile und einen vorhandenen Spitznamen nur als dezenten Zusatz.
  3. Strukturierte persoenliche Inhalte auf der Karte in getrennte Bereiche fuer Vorlieben, Abneigungen und Besonderheiten aufteilen.
  4. Den Kontakt-Dialog auf dieselbe Struktur bringen, inklusive eigenem Spitznamenfeld und getrennten Eingabebereichen fuer Vorlieben, Abneigungen und Besonderheiten.
  5. Sicherstellen, dass Kontakte ohne optionale Zusatzdaten optisch ruhig bleiben und keine stoerenden Leerbloecke erzeugen.
- Acceptance Criteria:
  - Kontaktkarten wirken aufgeraeumt und zeigen keine prominenten internen Herkunfts-/Ergebnisinformationen mehr.
  - Ein vorhandener Spitzname erscheint als Zusatz, ohne den vollen Namen zu ersetzen.
  - Vorlieben, Abneigungen und Besonderheiten sind in Karte und Dialog klar getrennt.
  - Kontakte ohne optionale Inhalte bleiben sauber lesbar und erzeugen keine kaputten oder leeren Strukturcontainer.
- Tests:
  - `node --check frontend/js/settings.js`
  - gezielte manuelle Sichtpruefung der Adressbuch-Karte und des Kontakt-Dialogs
- Model: 5.4
- Reason:
  - Existing-surface UI refactor with bounded frontend scope and no new architecture.

### TASK-SPEC16.3 Add focused regression coverage for nickname, sectioned contact UI, and compatibility behavior
- Ziel:
  - Sichere die neue Kontaktstruktur gegen Rueckfaelle ab, damit Spitzname, Besonderheiten und die aufgeraeumte Kartenlogik nicht still regressieren.
- Scope:
  - Nur die kleinste bestehende Kontakt-Testflaeche erweitern, die Speichern, Laden und sichtbare UI-Struktur des Adressbuchs absichern kann.
- Files:
  - `backend/tests/test_contact_manager.py`
  - `tests/e2e/generated/TASK-SPEC15-address-book-ui-evidence.spec.js`
  - `frontend/js/settings.js`
- Steps:
  1. Backend-Regressionen fuer Spitzname und kompatibles Verhalten alter Kontaktinhalte vervollstaendigen, falls noch noetig.
  2. Die bestehende Adressbuch-UI-Evidenz um sichtbare Erwartungen fuer Namenshierarchie und getrennte persoenliche Bereiche erweitern.
  3. Absichern, dass interne Status-/Herkunftsinhalte nicht wieder als primaerer Karteninhalt auftauchen.
- Acceptance Criteria:
  - Eine Regression schlaegt fehl, wenn der Spitzname nicht mehr gespeichert oder geladen wird.
  - Eine Regression schlaegt fehl, wenn die Karte wieder interne Status-/Herkunftsinhalte als Hauptinhalt zeigt.
  - Eine Regression schlaegt fehl, wenn die getrennten Bereiche fuer Vorlieben, Abneigungen und Besonderheiten sichtbar verloren gehen.
- Tests:
  - `pytest backend/tests/test_contact_manager.py -q`
  - `npx playwright test tests/e2e/generated/TASK-SPEC15-address-book-ui-evidence.spec.js --headed --workers=1 --reporter=list`
- Model: 5.4
- Reason:
  - Focused persistence and UI contract guard on existing test surfaces.

# JANUS FEATURE SPEC – DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-021
- **Backlog Title:** Datenbank-Migrationsfehler in EXE-Version: Spalte dark_mode_enabled fehlt
- **Type:** BUG

## 2. Problem / Wunsch
In der mit Skill 8 gebauten EXE-Version (v0.4.17-beta.25) tritt ein Datenbank-Migrationsfehler auf: `sqlite3.OperationalError: no such column: users.dark_mode_enabled`. Der Code erwartet die Spalte `dark_mode_enabled` in der `users` Tabelle, aber die Datenbank wurde mit einem alten Schema erstellt. Dies führt zu Fehlern bei `get_default_user_suggestion_mode` und vermutlich auch zu Problemen mit API-Keys (nicht geladen/gespeichert).

## 3. Expected Behavior
Die Datenbank-Migration wird korrekt ausgeführt, alle erforderlichen Spalten inklusive `dark_mode_enabled` sind vorhanden, und alle Funktionen (inklusive API-Keys) arbeiten korrekt.

## 4. Current Behavior
Die EXE-Version startet, aber bei jedem Aufruf von `get_default_user_suggestion_mode` tritt der Fehler auf: `no such column: users.dark_mode_enabled`. Die SQL-Abfrage versucht auf die Spalte zuzugreifen: `SELECT users.id AS users_id, users.username AS users_username, users.hashed_password AS users_hashed_password, users.is_active AS users_is_active, users.suggestion_mode AS users_suggestion_mode, users.dark_mode_enabled AS users_dark_mode_enabled FROM users ORDER BY users.id ASC LIMIT ? OFFSET ?`. API-Keys werden nicht korrekt geladen oder gespeichert (vermutlich als Symptom des Datenbank-Fehlers).

## 5. Scope
### IN SCOPE
- Prüfung der Datenbank-Migrationslogik in `backend/data/database.py`
- Sicherstellung, dass Migrationen in EXE-Version korrekt ausgeführt werden
- Validierung, dass `dark_mode_enabled` Spalte nach Migration vorhanden ist
- Test mit frischer EXE-Installation (janus-setup-0.4.17-beta.25.exe oder neuer)
- Überprüfung, dass API-Keys nach Migration korrekt geladen/gespeichert werden

### OUT OF SCOPE
- Änderung am Dev-Modus (funktioniert bereits korrekt)
- Änderung an Dark Mode Feature selbst
- Änderung an anderen Datenbank-Spalten oder Migrationen

## 6. Functional Requirements
- Datenbank-Migrationslogik muss in EXE-Version identisch zum Dev-Modus ausgeführt werden
- Alle Alembic-Migrationen müssen beim ersten Start der EXE-Version korrekt angewendet werden
- Die `users` Tabelle muss nach Migration alle erwarteten Spalten inklusive `dark_mode_enabled` enthalten
- `get_default_user_suggestion_mode` darf nicht mit `sqlite3.OperationalError` abbrechen
- API-Keys müssen nach Migration korrekt geladen und gespeichert werden können

## 7. Acceptance Criteria
- [ ] Datenbank-Migration fügt `dark_mode_enabled` Spalte korrekt hinzu
- [ ] `get_default_user_suggestion_mode` läuft ohne Fehler
- [ ] API-Keys werden korrekt geladen und gespeichert
- [ ] Alle Backend-Funktionen arbeiten ohne Datenbank-Fehler
- [ ] Keine Regression im Dev-Modus
- [ ] Frische EXE-Installation startet ohne Datenbank-Fehler

## 8. Evidence
- Backend-Log Zeile 01:20:46: `Traceback (most recent call last): File "sqlalchemy\engine\base.py", line 1967, in _exec_single_context File "sqlalchemy\engine\default.py", line 951, in do_execute sqlite3.OperationalError: no such column: users.dark_mode_enabled`
- Backend-Log Zeile 01:20:46: `File "backend\data\crud.py", line 200, in get_default_user_suggestion_mode`
- Backend-Log Zeile 01:20:46: `[SQL: SELECT users.id AS users_id, users.username AS users_username, users.hashed_password AS users_hashed_password, users.is_active AS users_is_active, users.suggestion_mode AS users_suggestion_mode, users.dark_mode_enabled AS users_dark_mode_enabled FROM users ORDER BY users.id ASC LIMIT ? OFFSET ?]`
- Fehler tritt wiederholt auf (alle 1-2 Sekunden) bei jedem Polling-Intervall

## 9. Risks
- HIGH: EXE-/Packaging-Bereich, Datenbank-Migration kann Datenverlust oder Korruption verursachen bei inkorrekter Implementierung
- HIGH: API-Key-Verlust bei inkorrekter Migration könnte Nutzer-Setup zerstören
- MEDIUM: Dev-Modus könnte durch Änderung an Migrationslogik beeinflusst werden

## 10. Validation Mapping
- Datenbank-Migration fügt `dark_mode_enabled` Spalte korrekt hinzu → SQL-Prüfung der `users` Tabelle nach EXE-Start
- `get_default_user_suggestion_mode` läuft ohne Fehler → Backend-Log prüfen, keine `sqlite3.OperationalError`
- API-Keys werden korrekt geladen und gespeichert → API-Key-Setup in EXE-Version testen
- Alle Backend-Funktionen arbeiten ohne Datenbank-Fehler → Full Backend-Log prüfen
- Keine Regression im Dev-Modus → Dev-Modus-Test mit bestehenden Tests
- Frische EXE-Installation startet ohne Datenbank-Fehler → Clean-Install-Test mit janus-setup-*.exe

## 11. Blocking Questions
Keine blockierenden Fragen offen.

## 12. SPEC REVIEW METADATA
- **Review Status:** PENDING
- **Reviewed by:** None
- **Reviewed at:** None
- **Review Result:** None

## 13. SPEC IMPLEMENTATION METADATA
- **Implementation Status:** DONE
- **Final Audit:** PASS WITH CONDITIONS
- **Completed At:** 2026-05-11
- **Completed By:** SKILL 7 – DOKUMENTATIONSUPDATE
- **Validation Evidence:** Skill 6 Final Audit PASS WITH CONDITIONS after Skill 4 implementation. EXE-Validierung auf Testsystem ausständig (Skill 8).

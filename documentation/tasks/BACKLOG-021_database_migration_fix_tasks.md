# BACKLOG-021 – Datenbank-Migrationsfehler in EXE-Version: Spalte dark_mode_enabled fehlt

## TASK DESIGN COMPLETE

**Feature:** Datenbank-Migrationsfehler in EXE-Version: Spalte dark_mode_enabled fehlt

**Refined Tasks:**
- TASK-002.1: Datenbank-Migrationslogik für EXE-Version analysieren und korrigieren

**Remaining Tasks (nicht freigegeben):**
- TASK-003: EXE-Version mit korrigierter Migration bauen und testen

**Ausführungskette:** Sequenziell (TASK-002.1 → TASK-003)

**Zugewiesene Modelle:**
- SWE 1.6: TASK-002.1, TASK-003
- Kimi k2.5: keine

---

## TASK-002.1 – Datenbank-Migrationslogik für EXE-Version analysieren und korrigieren

### Ziel
Datenbank-Migrationslogik analysieren, Root Cause identifizieren und korrigieren, damit die `dark_mode_enabled` Spalte in der EXE-Version korrekt hinzugefügt wird.

### Impact-Analyse
- **Basiert auf:** documentation/Planned Features/backlog_BACKLOG-021_database_migration_fix.md
- **Beeinflusst:** backend/data/database.py, alembic/versions/, EXE-Packaging-Konfiguration (falls relevant)
- **Risiko-Einschätzung:** HIGH

### Beschreibung
Analysiere die Datenbank-Migrationslogik in `backend/data/database.py` und den EXE-Packaging-Prozess, um zu verstehen, warum Migrationen in der EXE-Version nicht korrekt ausgeführt werden. Identifiziere den Root Cause und korrigiere die Migrationslogik, damit alle Alembic-Migrationen beim ersten Start der EXE-Version korrekt angewendet werden.

### Files
- `backend/data/database.py`
- `alembic/versions/` (Migration-Dateien für dark_mode_enabled)
- EXE-Packaging-Konfiguration (falls relevant)

### Steps
1. Prüfe, wie `backend/data/database.py` Migrationen beim ersten Start auslöst
2. Identifiziere, ob Alembic-Migrationen in EXE-Version ausgeführt werden
3. Prüfe, ob die Datenbank-Initialisierung in EXE-Version ein anderes Schema verwendet
4. Vergleiche den Migrations-Ablauf zwischen Dev-Modus und EXE-Version
5. Identifiziere den genauen Root Cause (konkrete Datei/Zeile oder Prozess-Schritt)
6. Implementiere die Korrektur basierend auf dem identifizierten Root Cause
7. Stelle sicher, dass alle Alembic-Migrationen beim ersten Start der EXE-Version ausgeführt werden
8. Stelle sicher, dass die `users` Tabelle nach Migration alle erwarteten Spalten inklusive `dark_mode_enabled` enthält
9. Teste die Korrektur lokal im Dev-Modus (ohne Regression)

### Acceptance Criteria
- [ ] Root Cause ist dokumentiert (konkrete Datei/Zeile oder Prozess-Schritt identifiziert)
- [ ] Datenbank-Migration fügt `dark_mode_enabled` Spalte korrekt hinzu
- [ ] Alle Alembic-Migrationen werden beim ersten Start ausgeführt
- [ ] `get_default_user_suggestion_mode` läuft im Dev-Modus ohne Fehler
- [ ] Keine Regression im Dev-Modus
- [ ] Alle bestehenden Datenbank-Migrationen funktionieren weiterhin
- [ ] API-Keys werden weiterhin korrekt geladen und gespeichert

### Tests
- Dev-Modus-Test: Datenbank löschen, neu starten, Prüfen ob Migrationen ausgeführt werden
- SQL-Prüfung: `SELECT * FROM users` nach Migration, Prüfen ob `dark_mode_enabled` Spalte existiert
- Backend-Log-Prüfung: Keine `sqlite3.OperationalError` bei `get_default_user_suggestion_mode`
- Bestehende Datenbank-Tests ausführen
- Manuelles Testen von Datenbank-Operationen

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backend-Code-Analyse und -Korrektur mit Datenbank-Migrationslogik erfordert tiefes Verständnis der Codebase

---

## TASK-003 – EXE-Version mit korrigierter Migration bauen und testen

### Ziel
EXE-Version mit der korrigierten Migrationslogik bauen und mit frischer Installation validieren.

### Beschreibung
Baue eine neue EXE-Version mit der Korrektur aus TASK-002 und teste sie mit einer frischen Installation, um zu validieren, dass die Datenbank-Migration korrekt ausgeführt wird.

### Files
- EXE-Build-Prozess (Skill 8 / Packaging)
- Installierte EXE-Version (Testsystem)

### Steps
1. EXE-Version mit der Korrektur aus TASK-002 bauen
2. Frische Installation auf Testsystem durchführen
3. EXE starten und Backend-Logs auf Datenbank-Fehler prüfen
4. Prüfen, ob `get_default_user_suggestion_mode` ohne Fehler läuft
5. Prüfen, ob API-Keys korrekt geladen/gespeichert werden
6. SQL-Prüfung der `users` Tabelle durchführen, um `dark_mode_enabled` Spalte zu validieren

### Acceptance Criteria
- [ ] Frische EXE-Installation startet ohne Datenbank-Fehler
- [ ] `get_default_user_suggestion_mode` läuft ohne Fehler
- [ ] API-Keys werden korrekt geladen und gespeichert
- [ ] Alle Backend-Funktionen arbeiten ohne Datenbank-Fehler
- [ ] `dark_mode_enabled` Spalte ist in `users` Tabelle vorhanden

### Tests
- Clean-Install-Test mit neuer EXE-Version
- Backend-Log-Analyse auf `sqlite3.OperationalError`
- API-Key-Setup-Test in EXE-Version
- SQL-Prüfung der Datenbank nach Installation

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** EXE-Build und Test erfordert Verständnis des Packaging-Prozesses und Validierung

---

## TASK-004 – Dev-Modus-Regressionstest durchführen

### Ziel
Validieren, dass die Korrektur keine Regression im Dev-Modus verursacht.

### Beschreibung
Führe Regressionstests im Dev-Modus durch, um sicherzustellen, dass die Korrektur aus TASK-002 die bestehende Funktionalität nicht beeinträchtigt.

### Files
- `backend/data/database.py`
- Bestehende Tests (falls vorhanden)

### Steps
1. Dev-Modus starten und bestehende Datenbank-Tests ausführen
2. Prüfen, ob alle bestehenden Migrationen weiterhin korrekt ausgeführt werden
3. Prüfen, ob `get_default_user_suggestion_mode` ohne Fehler läuft
4. Prüfen, ob API-Keys weiterhin korrekt geladen/gespeichert werden
5. Manuelles Testen von Dark Mode Feature (falls relevant)

### Acceptance Criteria
- [ ] Keine Regression im Dev-Modus
- [ ] Alle bestehenden Datenbank-Migrationen funktionieren weiterhin
- [ ] `get_default_user_suggestion_mode` läuft ohne Fehler
- [ ] API-Keys werden korrekt geladen und gespeichert

### Tests
- Bestehende Datenbank-Tests ausführen
- Manuelles Testen von Datenbank-Operationen
- Backend-Log-Prüfung auf Fehler

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Regressionstest erfordert Verständnis der bestehenden Funktionalität

---

## MODELL-BEDEUTUNG

Diese Zuweisungen sind Task-Ausführungsmodelle für spätere einzelne Skill-3-/Skill-4-Läufe. Sie sind NICHT das Modell für Skill 2.

Skill 2 ist das Task-Refinement-Gate und läuft immer mit SWE 1.6, außer ein MODEL SWITCH zu GPT-5.5 ist explizit erforderlich.

TASK-SPEC10
- Source Spec: `documentation/SPEC/10_contact_memory_reconciliation.md`
- Backlog Item: `N/A`
- Feature: Contact-Memory Reconciliation fuer bestehende Adressbuchkontakte
- Generated At: 2026-06-08

## Generated Tasks

### TASK-SPEC10.1 Harden trusted contact fact sync on new memory writes
- Ziel:
  - Synchronisiere neue sichere, nutzerbestaetigte Kontaktfakten automatisch in bestehende Adressbuchkontakte, ohne unklare oder nicht vertrauenswuerdige Memory-Urspruenge still zu uebernehmen.
- Scope:
  - Nur bestehende Memory-Write-, Kontaktmanager- und Kontakt-Testpfade fuer neue Kontaktfakten. Keine globale Hintergrundsynchronisierung und kein Anlegen neuer Kontakte.
- Files:
  - `backend/tools/memory_tools.py`
  - `backend/services/contact_manager.py`
  - `backend/services/tool_executor.py`
  - `backend/tests/test_contact_manager.py`
  - `backend/tests/test_memory_tools.py`
- Steps:
  1. Stelle sicher, dass neue Kontaktfakten aus direkter Nutzeraeusserung oder bestaetigtem Kontaktwissen als sync-faehig erkannt werden koennen.
  2. Begrenze Auto-Sync strikt auf sichere Felder: Vorlieben, Abneigungen, Ernaehrungsform/Besonderheiten, Hobbys und einfache Gewohnheiten.
  3. Blockiere stillen Auto-Sync fuer modellgenerierte, importierte oder unklare Memory-Fakten auch dann, wenn ein Kontaktname eindeutig wirkt.
  4. Halte Ernaehrungsformen im Kontakt unter Besonderheiten/Details und nicht unter normalen Vorlieben.
  5. Ergaenze Regressionen fuer nutzerbestaetigte Kontaktfakten, unklare Memory-Urspruenge und verbotene Feldklassen.
- Acceptance Criteria:
  - Ein nutzerbestaetigter sicherer Kontaktfakt landet bei eindeutigem bestehendem Kontakt im passenden Adressbuchfeld.
  - Ein modellgenerierter, importierter oder unklarer Memory-Fakt wird nicht still in das Adressbuch synchronisiert.
  - Ein politischer, gesundheitlicher, adressbezogener, telefonischer, beziehungsbezogener, religioeser oder finanzieller Fakt wird nicht still auto-synchronisiert.
  - Ernaehrungsformen erscheinen als Besonderheiten/Details und erzeugen keine Vorlieben-Dublette.
- Tests:
  - `pytest backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py -q`
  - `python -m py_compile backend/tools/memory_tools.py backend/services/contact_manager.py backend/services/tool_executor.py`
- Model: 5.4
- Reason:
  - Bounded backend persistence hardening with existing contact and memory modules; high constraints are already locked in the Spec.

### TASK-SPEC10.2 Reconcile confirmed contact memories during contact recall and contact lookup
- Ziel:
  - Ziehe bereits vorhandene sichere und bestaetigte Memory-Fakten beim naechsten Kontakt-Recall oder Kontakt-Oeffnen/Suchen in den bestehenden Adressbuchkontakt nach.
- Scope:
  - Nur ereignisbasierte Reconciliation auf Kontakt-Recall und Kontakt-Lookup. Kein App-Start-Vollabgleich, kein globaler Scan und keine externe Recherche.
- Files:
  - `backend/services/contact_manager.py`
  - `backend/services/chat/context_builder.py`
  - `backend/services/orchestrator/intent_engine.py`
  - `backend/services/orchestrator/execution_engine.py`
  - `backend/tests/test_contact_manager.py`
  - `backend/tests/test_calendar_routing_fix.py`
  - `backend/tests/test_provider_auth_fallback.py`
- Steps:
  1. Erkenne Kontakt-Recall und Kontakt-Lookup als Reconciliation-Trigger, wenn ein konkreter bestehender Kontakt eindeutig getroffen wird.
  2. Gleiche nur bestaetigte sichere Memory-Fakten fuer genau diesen Kontakt gegen die vorhandenen Adressbuchfelder ab.
  3. Ergaenze fehlende sichere Werte ohne Dubletten und ohne Web/RSS/Wikipedia-Umleitung.
  4. Gib bei erfolgreichem Nachziehen eine transparente lokale Antwort aus, die Memory und Adressbuch korrekt benennt.
  5. Ergaenze Regressionen fuer das Chris-Gier-Szenario mit bestehenden Memory-Fakten `Star Wars` und `Kimchi`, aber leerem Adressbuchfeld.
- Acceptance Criteria:
  - `Was weisst du ueber Chris Gier?` kann bestaetigte sichere Memory-Fakten in den bestehenden Kontakt nachziehen, wenn sie dort fehlen.
  - Kontakt-Recall bleibt lokal und fragt nicht, ob der Nutzer sich selbst oder eine andere Person meint, wenn der Adressbuchkontakt eindeutig ist.
  - Bereits vorhandene Werte werden nicht doppelt gespeichert.
  - Kein globaler Hintergrundscan, keine App-Start-Synchronisierung und keine externe Recherche werden fuer den Sync verwendet.
- Tests:
  - `pytest backend/tests/test_contact_manager.py backend/tests/test_calendar_routing_fix.py backend/tests/test_provider_auth_fallback.py -q`
  - `python -m py_compile backend/services/contact_manager.py backend/services/chat/context_builder.py backend/services/orchestrator/intent_engine.py backend/services/orchestrator/execution_engine.py`
- Model: 5.4
- Reason:
  - Existing recall and context behavior with moderate cross-module coupling; implementation can stay within known Janus workhorse scope.

### TASK-SPEC10.3 Add ambiguity and conflict handling for contact-memory reconciliation
- Ziel:
  - Verhindere stille falsche Adressbuchaenderungen bei mehreren Kontakten, unsicherer Zuordnung oder abweichenden bestehenden Kontaktwerten.
- Scope:
  - Nur Rueckfrage-/Blockierverhalten fuer Reconciliation-Konflikte und Mehrdeutigkeiten im bestehenden Chat- und Kontaktpfad.
- Files:
  - `backend/services/contact_manager.py`
  - `backend/services/orchestrator/execution_engine.py`
  - `backend/services/chat/context_builder.py`
  - `backend/tests/test_contact_manager.py`
  - `backend/tests/test_provider_auth_fallback.py`
- Steps:
  1. Blockiere Auto-Sync, wenn mehrere Kontakte passend sind oder Pronomen nicht eindeutig auf genau einen bestehenden Kontakt zeigen.
  2. Erkenne Widersprueche zwischen Memory-Wert und bestehendem Adressbuchwert fuer sync-faehige Felder.
  3. Erzeuge bei Konflikten eine konkrete Rueckfrage, die Memory-Wert und Adressbuchwert sichtbar nennt.
  4. Stelle sicher, dass sensitive oder riskante Fakten keine Rueckfrage mit stiller Speicherwirkung ausloesen.
  5. Ergaenze Regressionen fuer mehrere Kontaktkandidaten, Konflikte und sensitive Fakten wie Politik oder Gesundheit.
- Acceptance Criteria:
  - Bei mehreren passenden Kontakten fragt Janus nach und schreibt nichts ins Adressbuch.
  - Bei Konflikt nennt Janus Memory-Wert und Adressbuchwert und nimmt keine stille Aenderung vor.
  - Politische, gesundheitliche, adressbezogene, telefonische, beziehungsbezogene, religioese und finanzielle Fakten werden nicht still synchronisiert.
  - Eine erfolgreiche Tool- oder Modellantwort behauptet keine Adressbuchspeicherung, wenn keine Kontaktmutation erfolgt ist.
- Tests:
  - `pytest backend/tests/test_contact_manager.py backend/tests/test_provider_auth_fallback.py -q`
  - `python -m py_compile backend/services/contact_manager.py backend/services/orchestrator/execution_engine.py backend/services/chat/context_builder.py`
- Model: 5.4
- Reason:
  - Focused safety and ambiguity handling around existing backend logic with clear acceptance criteria.

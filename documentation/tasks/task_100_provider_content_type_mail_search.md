TASK-100
- Source Spec: documentation/SPEC/Spec Done/backlog_BACKLOG-100_generische_anbieter_mail_suche_nach_inhaltstypen.md
- Backlog Item: BACKLOG-100
- Feature: Generische Anbieter-Mail-Suche nach Inhaltstypen
- Generated At: 2026-05-31

## Generated Tasks

### TASK-100.1 Generische Anbieter-und-Kategorie-Erkennung im Mail-Chat
- Ziel: Die bestehende Mail-Chat-Interpretation von anbieterbezogenen Suchanfragen von einer Picnic-Sonderbehandlung auf eine generische Anbieter-plus-Inhaltstyp-Erkennung erweitern.
- Scope: Erkennungslogik fuer genau einen Anbieter und genau einen Inhaltstyp je Anfrage, inklusive gezielter Rueckfrage bei Mehrdeutigkeit.
- Files: `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/intent_engine.py`, `backend/tests/unit/test_intent_engine.py`
- Steps:
  1. Bestehende probe-basierte Mail-Erkennung im Chat-Orchestrator so erweitern, dass sie nicht auf Einzelanbieter-Keywords fixiert bleibt.
  2. Parsing-Regeln fuer einen Anbieter plus einen Inhaltstyp (z. B. Rezept, Bon, Rechnung, Bestaetigung) als stabile Intent-Signale abbilden.
  3. Rueckfragepfad fuer fehlenden oder mehrdeutigen Anbieter bzw. Inhaltstyp deterministisch ausgeben.
  4. Unit-Tests fuer positive, mehrdeutige und unvollstaendige Anfragen ergaenzen.
- Acceptance Criteria:
  - [ ] Janus erkennt Anfragen im Muster Anbieter plus Inhaltstyp ohne Anbieter-Sonderverdrahtung.
  - [ ] Janus fragt bei fehlendem Anbieter oder Inhaltstyp gezielt nach, bevor eine breite Suche startet.
  - [ ] Janus startet keine implizite Mehrfachsuche ueber mehrere Anbieter oder Kategorien.
- Tests:
  - `backend/tests/unit/test_intent_engine.py` deckt eindeutige und mehrdeutige Anbieter-plus-Kategorie-Faelle ab.
  - Orchestrator-nahe Tests bestaetigen den Rueckfragepfad statt Halluzinations-Treffern.
- Model: 5.3 codex
- Reason: Bestehende Chat-Orchestrierungslogik und Intent-Verhalten werden in mehreren Backend-Modulen angepasst.

### TASK-100.2 Trefferselektion und Ausgabeformat fuer Kategorie-Suche stabilisieren
- Ziel: Trefferlisten fuer Anbieter-plus-Kategorie-Anfragen im bestehenden Mail-Chat konsistent und nachvollziehbar ausgeben.
- Scope: Trefferaufbereitung mit Anbieter, Betreff, Datum, erkannter Kategorie und kurzer Fundstellen-Zusammenfassung je Treffer; klarer No-Results-Zustand.
- Files: `backend/services/chat_orchestrator.py`, `backend/services/mail/mail_service.py`, `backend/data/schemas_mail.py`
- Steps:
  1. Suchabfrage aus Anbieter-plus-Kategorie in die bestehende Mail-Thread-Suche integrieren.
  2. Kategoriematching konservativ gestalten und schwache Treffer nicht als sichere Treffer ausgeben.
  3. Antwortformat fuer Trefferliste vereinheitlichen (Anbieter, Betreff, Datum, Kategorie, Kurzbegruendung).
  4. No-Results und Verbindungsfehler klar voneinander trennen.
- Acceptance Criteria:
  - [ ] Jede Trefferzeile enthaelt Anbieter, Betreff, Datum, erkannte Kategorie und kurze Fundstellen-Zusammenfassung.
  - [ ] Bei fehlenden Treffern wird ein eindeutiger No-Results-Zustand ausgegeben.
  - [ ] Schwache oder unklare Kategorietreffer werden nicht als sichere Treffer behauptet.
- Tests:
  - Backend-Tests fuer Mail-Suche pruefen Trefferformat und No-Results-Verhalten.
  - Bestehende Mail-Service-Vertragstests bleiben gruen.
- Model: 5.3 codex
- Reason: Die Aenderung betrifft sowohl Suchverhalten als auch Ausgabevertrag im produktiven Mail-Chat-Fluss.

### TASK-100.3 Regression-Schutz fuer bestehenden Mail-Flow absichern
- Ziel: Sicherstellen, dass die Optimierung bestehende Mail-Funktionen nicht verschlechtert.
- Scope: Regressionsabdeckung fuer Standard-Mail-Interaktionen (Inbox/Thread-Lesen/Suche) bei unveraendertem Verhalten ausserhalb des neuen Anbieter-plus-Kategorie-Pfads.
- Files: `backend/tests/test_mail_service.py`, `backend/tests/test_mail_chat_account_guard_store.py`, `frontend/tests/mail-inbox-ui.test.mjs`
- Steps:
  1. Bestehende Mail-Tests um Regression-Cases fuer Nicht-Zielanfragen erweitern.
  2. Verifizieren, dass Standard-Inbox- und Thread-Flows identisch bleiben.
  3. Verifizieren, dass Verbindungs- und Consent-Zustaende weiterhin korrekt priorisiert werden.
  4. Testfaelle fuer neue Suchanfragen und klassische Mailanfragen nebeneinander ausfuehren.
- Acceptance Criteria:
  - [ ] Bestehende Kern-Maillogik bleibt fuer normale Mailnutzung unveraendert stabil.
  - [ ] Neue Anbieter-plus-Kategorie-Anfragen funktionieren, ohne bestehende Such- und Lesepfade zu brechen.
  - [ ] Consent- und Connection-State-Verhalten bleibt unveraendert korrekt.
- Tests:
  - `backend/tests/test_mail_service.py` und `backend/tests/test_mail_chat_account_guard_store.py` bleiben inklusive neuer Cases gruen.
  - `frontend/tests/mail-inbox-ui.test.mjs` bleibt gruen und zeigt keine UI-Regression in der Thread-Liste.
- Model: 5.3 codex
- Reason: Hohe Bedeutung des Regression-Schutzes auf bereits produktiv stabilen Mail-Funktionen.

## Completion Metadata

- Final Audit: PASS (`documentation/audit/FINAL_SKILL_AUDIT_BACKLOG_100_PASS_2026-06-01.md`)
- Completed At: 2026-06-01
- Evidence:
  - `python -m py_compile backend/services/chat_orchestrator.py backend/main.py backend/services/memory_extractor.py` PASS
  - `python -m pytest backend/tests/unit/test_chat_mail_provider_content_type_probe.py backend/tests/test_mail_service.py backend/tests/test_mail_chat_account_guard_store.py -q` PASS (39 passed)
  - `node --test frontend/tests/mail-inbox-ui.test.mjs` PASS (3 passed)

TASK-098
- Source Spec: documentation/SPEC/10_janus_mail_module_shell_and_connection_state.md; documentation/SPEC/11_janus_mail_gmail_thread_inbox_and_search.md; documentation/SPEC/12_janus_mail_manual_actions_and_attachments.md; documentation/SPEC/13_janus_mail_ai_thread_assist_and_draft_replies.md
- Backlog Item: N/A
- Feature: Janus Mail
- Generated At: 2026-05-28

## Generated Tasks

### TASK-098.1 Mail Backend Bootstrap and Connection Status Contract
- Ziel: Ein minimales Mail-Backend-Fundament mit Schemas, Service-Package und lesbarem Gmail-Verbindungsstatus fuer die Mail-Surface bereitstellen.
- Scope: Neue Mail-Schemas anlegen, Service-Layer bootstrapen, statusorientierten Mail-Router anlegen und in das bestehende Backend registrieren.
- Files: `backend/data/schemas_mail.py`, `backend/services/mail/__init__.py`, `backend/services/mail/mail_service.py`, `backend/api/routers/mail.py`, `backend/main.py`, `backend/tests/test_mail_service.py`
- Steps:
  1. Mail-spezifische Pydantic-Schemas fuer Connection State und Surface-Basiszustand anlegen.
  2. Service-Layer fuer Gmail-Statusermittlung und Mail-Modul-Basisfunktionen anlegen.
  3. Mail-Router mit read-only Connection-Status-Endpunkt anlegen.
  4. Router in `backend/main.py` registrieren.
  5. Backend-Tests fuer Status-Endpunkt und Fehlerzustand ergaenzen.
- Acceptance Criteria:
  - [ ] Ein Mail-Router ist im Backend registriert und erreichbar.
  - [ ] Der Mail-Status-Endpunkt unterscheidet mindestens connected, disconnected, missing_scope und sync_error.
  - [ ] Fehler im Gmail-Statuspfad brechen den Backend-Start nicht.
  - [ ] Backend-Tests decken Erfolgs- und Fehlerpfade fuer den Statusvertrag ab.
- Tests:
  - `backend/tests/test_mail_service.py` prueft Status-Mapping und Router-Responses.
  - FastAPI-Router-Test bestaetigt, dass kein pseudo-inbox payload bei fehlender Verbindung geliefert wird.
- Model: 5.3 codex
- Reason: Mehrere neue Python-Module plus Router-Integration und Tests im bestehenden Backend-Muster.

### TASK-098.2 Mail Dock Shell and Connection State Frontend
- Ziel: Die Janus-Mail-Surface im Dock verankern und den Connection-State in einer kalendernahen Zwei-Spalten-Shell rendern.
- Scope: Dock-Integration, Sidebar-List-Integration, Modal-Wiring, Mail-Host im HTML, Frontend-Renderer und Mail-CSS fuer Shell und Statusflaechen.
- Files: `frontend/index.html`, `frontend/js/modal-api.js`, `frontend/js/window-state.js`, `frontend/js/dock.js`, `frontend/js/mail-modal.js`, `frontend/css/mail-modal.css`, `tests/e2e/mail-shell.spec.js`
- Steps:
  1. Mail-Modul im Dock- und MCL-Mapping registrieren.
  2. Mail-Eintrag in der bestehenden Sidebar-Modulliste anbinden, analog zu Image Studio und Calendar.
  3. Mail-Host-Container in `frontend/index.html` anlegen.
  4. `frontend/js/mail-modal.js` fuer Shell-Lifecycle und Status-Rendering anlegen.
  5. `frontend/css/mail-modal.css` fuer das Zwei-Spalten-Grundlayout und Statuskarten anlegen.
  6. E2E-Test fuer Oeffnen, Schliessen und unterscheidbare Statuszustaende ergaenzen.
- Acceptance Criteria:
  - [ ] Mail ist als Dock-Modul sichtbar und oeffnet genau eine Mail-Surface.
  - [ ] Mail ist in der Sidebar-Modulliste sichtbar und oeffnet dieselbe Mail-Surface wie der Dock-Eintrag.
  - [ ] Die Surface rendert unterscheidbare Statuszustaende fuer connected, disconnected, missing_scope und sync_error.
  - [ ] Das Schliessen oder erneute Oeffnen dupliziert keine Container oder Listener.
  - [ ] Die Surface bleibt optisch im bestehenden Janus-Modulstil.
- Tests:
  - `tests/e2e/mail-shell.spec.js` prueft Dock- und Sidebar-Oeffnung, Reopen-Stabilitaet und Status-Rendering.
  - Frontend-Regressionscheck fuer Dock-Z-Stack und Modal-Fokus.
- Model: 5.3 codex
- Reason: Frontend-Integration ueber mehrere bestehende Dock- und Modal-Dateien plus visuelles E2E-Verhalten.

### TASK-098.3 Gmail Thread Inbox and Search Backend
- Ziel: Thread-first Inbox-, Search- und Thread-Detail-Daten aus Gmail fuer Janus Mail bereitstellen.
- Scope: Gmail-Nachrichten normalisieren, nach Gmail-Thread gruppieren, Gmail-Search durchreichen und Thread-Detail-Payload liefern.
- Files: `backend/data/schemas_mail.py`, `backend/services/mail/mail_service.py`, `backend/api/routers/mail.py`, `backend/tests/test_mail_service.py`, `backend/tests/test_mail_router.py`
- Steps:
  1. Nachricht-, Teilnehmer-, Attachment- und Thread-Schemas vervollstaendigen.
  2. Service-Funktionen fuer Threadliste, Search und Threaddetail ueber bestehende Gmail-Tools anlegen.
  3. Router-Endpunkte fuer Threadliste und Threaddetail bereitstellen.
  4. Fehler- und Leerzustandsverhalten backendseitig explizit machen.
  5. Tests fuer Gruppierung, Suchweitergabe und Detaildarstellung ergaenzen.
- Acceptance Criteria:
  - [ ] Gmail-Threads werden als Threadliste statt als lose Einzelmails ausgeliefert.
  - [ ] Suchanfragen werden als Gmail-backed Query verarbeitet.
  - [ ] Threaddetail liefert Nachrichten in chronologisch renderbarer Reihenfolge.
  - [ ] Leere Inbox und leere Suchergebnisse sind backendseitig unterscheidbar.
- Tests:
  - `backend/tests/test_mail_service.py` prueft Thread-Gruppierung und Message-Normalisierung.
  - `backend/tests/test_mail_router.py` prueft Threadliste, Search-Weitergabe und Detail-Endpunkt.
- Model: 5.3 codex
- Reason: Deterministische Gmail-Normalisierung mit klaren Router- und Testaenderungen.

### TASK-098.4 Thread List, Search, and Detail Frontend
- Ziel: Eine thread-first Mail-Ansicht mit Suchleiste und lesbarer Thread-Detailspalte in der Mail-Surface bereitstellen.
- Scope: Threadliste rendern, Suchzustand verwalten, Detailpanel mit Nachrichtenfolge darstellen und Leer- oder Fehlerzustaende sauber unterscheiden.
- Files: `frontend/js/mail-modal.js`, `frontend/css/mail-modal.css`, `frontend/js/dompurify-config.js`, `tests/e2e/mail-inbox.spec.js`
- Steps:
  1. Threadliste und Such-UI in die Mail-Shell integrieren.
  2. Detailbereich fuer chronologische Threadnachrichten mit Text- oder HTML-Fallback anbinden.
  3. Leerzustand, no-results und lokalisierte Fehlerzustaende visuell unterscheiden.
  4. E2E-Test fuer Search, Auswahl und Detailrendering schreiben.
- Acceptance Criteria:
  - [ ] Threadliste zeigt Gmail-Konversationen in der Mail-Surface.
  - [ ] Suche aktualisiert die Liste anhand Gmail-basierter Ergebnisse.
  - [ ] Thread-Detail bleibt auch bei unvollstaendiger oder fehlerhafter Nachrichtendarstellung stabil.
  - [ ] No-results und no-inbox sind fuer Nutzer unterscheidbar.
- Tests:
  - `tests/e2e/mail-inbox.spec.js` prueft Search-Flow, Thread-Auswahl und leere Resultate.
  - UI-Render-Test fuer lokalisierte Detailfehler ohne Surface-Absturz.
- Model: 5.3 codex
- Reason: Zusammenhaengende Frontend-Arbeit an Listen-, Such- und Detailzustand mit E2E-Abdeckung.

### TASK-098.5 Manual Mail Actions and Attachment Backend
- Ziel: Explizite Mailmutationen und sichere Attachment-Pfade backendseitig bereitstellen.
- Scope: Reply- und Send-Pfade, Archive/Restore/Trash-Verhalten, deterministische Undo-Grundlage und sicherer Attachment-Save-Vertrag.
- Files: `backend/data/schemas_mail.py`, `backend/services/mail/mail_service.py`, `backend/api/routers/mail.py`, `backend/tools/gmail_tools.py`, `backend/tests/test_mail_actions.py`
- Steps:
  1. Router- und Service-Vertrag fuer reply, send, archive, restore und trash anlegen.
  2. Deterministische Undo-Matrix fuer archive und move-to-trash als Ruecksetzpfad abbilden.
  3. Sicheren Attachment-Save-Pfad mit sanitisierten Dateinamen und ohne stilles Overwrite abbilden.
  4. Backend-Tests fuer Erfolgs-, Fehler- und Konfliktpfade schreiben.
- Acceptance Criteria:
  - [ ] Mailmutationen laufen nur nach expliziter Nutzeraktion.
  - [ ] Archive und move-to-trash koennen ueber den definierten Ruecksetzpfad wiederhergestellt werden.
  - [ ] Restore-to-inbox verspricht kein weiteres Undo.
  - [ ] Attachment-Save ueberschreibt niemals still bestehende Dateien.
  - [ ] Path-Traversal-Anteile in Attachment-Namen werden nicht als Pfad uebernommen.
- Tests:
  - `backend/tests/test_mail_actions.py` prueft Send, Archive, Restore, Trash und Undo-Pfade.
  - Dateikonflikt- und Dateinamen-Sicherheitsfaelle fuer Attachment-Save werden automatisiert geprueft.
- Model: 5.3 codex
- Reason: Provider-Mutationen und lokales Dateisystem brauchen saubere Python-Implementierung plus Sicherheits-Tests.

### TASK-098.6 Composer, Actions, Undo, and Attachment Frontend
- Ziel: Reply- und Aktions-UX in Janus Mail mit klarer Nutzerkontrolle und Undo-Feedback bereitstellen.
- Scope: Composer, Send-Flow, Action-Buttons, Undo-Toast-Verhalten und Attachment-Interaktionen in der Mail-Surface.
- Files: `frontend/js/mail-modal.js`, `frontend/css/mail-modal.css`, `frontend/index.html`, `tests/e2e/mail-actions.spec.js`
- Steps:
  1. Composer fuer Reply und neue Nachricht im Threadkontext anbinden.
  2. UI-Controls fuer archive, restore und trash inklusive Undo-Toast fuer die erlaubten Faelle einbauen.
  3. Attachment-Add und Attachment-Save als explizite UI-Aktionen anbinden.
  4. E2E-Test fuer Composer-, Action- und Undo-Flows ergaenzen.
- Acceptance Criteria:
  - [ ] Senden erfolgt nur nach explizitem Klick im Composer.
  - [ ] Undo wird nur fuer archive und move-to-trash angeboten.
  - [ ] Restore-to-inbox bietet kein weiteres Undo an.
  - [ ] Attachment-Aktionen destabilisieren weder Composer noch Thread-Detail.
- Tests:
  - `tests/e2e/mail-actions.spec.js` prueft Reply-Senden, Archive, Restore, Trash und Undo-Sichtbarkeit.
  - E2E-Pruefung fuer Attachment-Hinzufuegen und lokales Save-Feedback.
- Model: 5.3 codex
- Reason: Stark zusammenhaengender Nutzerfluss ueber eine Frontend-Datei plus echtes Verhaltens-Testing.

### TASK-098.7 AI Consent and Settings Plumbing
- Ziel: Den AI-Consent-Vertrag fuer Mail technisch durch settings- und threadseitige Steuerung absichern.
- Scope: Globales Setting fuer `AI Mail Assist` mit Default OFF, API-Persistenz, Frontend-Settings-Anbindung und per-thread Toggle-Grundlage.
- Files: `backend/data/schemas.py`, `backend/api/routers/users.py`, `frontend/js/settings.js`, `frontend/index.html`, `frontend/js/mail-modal.js`, `backend/tests/test_mail_ai.py`, `tests/e2e/mail-ai-consent.spec.js`
- Steps:
  1. User-Settings-Vertrag um globales `AI Mail Assist` erweitern.
  2. Settings-UI fuer globales Enable oder Disable anbinden.
  3. Mail-Surface um per-thread AI-Toggle-Grundlage erweitern.
  4. Tests fuer global OFF, global ON und per-thread OFF ergaenzen.
- Acceptance Criteria:
  - [ ] `AI Mail Assist` ist global standardmaessig OFF.
  - [ ] Bei global OFF wird kein Mail-Thread-Inhalt an einen AI-Provider gesendet.
  - [ ] Bei global ON kann AI nur fuer explizit erlaubte Threads genutzt werden.
  - [ ] Per-thread OFF verhindert AI-Requests fuer genau diesen Thread.
- Tests:
  - `backend/tests/test_mail_ai.py` prueft Consent-Gating im Backend.
  - `tests/e2e/mail-ai-consent.spec.js` prueft Settings- und Thread-Toggle-Verhalten.
- Model: 5.3 codex
- Reason: Cross-cutting Consent-Logik ueber Backend-Settings, Frontend-Settings und Mail-UI.

### TASK-098.8 AI Thread Assist and Draft Backend
- Ziel: Thread-Zusammenfassung, Reply-Needed-Signal, Prioritaet und editierbare Draft-Generierung backendseitig bereitstellen.
- Scope: AI-Analyse-Endpunkte und Draft-Reply-Endpunkt nur fuer consent-freigegebene Threads mit sichtbarem Degraded-State-Verhalten.
- Files: `backend/data/schemas_mail.py`, `backend/services/mail/mail_ai_engine.py`, `backend/services/mail/mail_reply_generator.py`, `backend/services/mail/mail_service.py`, `backend/api/routers/mail.py`, `backend/tests/test_mail_ai.py`
- Steps:
  1. AI-Metadaten- und Draft-Schemas vervollstaendigen.
  2. Mail-AI-Engine und Reply-Generator auf dem vorhandenen LLM-Gateway aufsetzen.
  3. Router-Endpunkte fuer analyze und draft-reply anlegen.
  4. Stale-, Failure- und Consent-Pfade backendseitig explizit behandeln.
  5. Backend-Tests fuer Summary, Priority, Draft, Providerfehler und Stale-Markierung schreiben.
- Acceptance Criteria:
  - [ ] AI-Analyse laeuft nur fuer consent-freigegebene Threads.
  - [ ] Draft-Reply erzeugt editierbaren Text und triggert keinen Send-Pfad.
  - [ ] Providerfehler fuehren zu sichtbarem Degraded-State statt zu Fake-Erfolg.
  - [ ] Neue Thread-Nachrichten koennen vorhandene AI-Zustaende als stale markieren.
- Tests:
  - `backend/tests/test_mail_ai.py` prueft Consent-Gating, Draft-Generierung, Providerfehler und stale-summary Verhalten.
  - Unit-Tests fuer Antwortton und strukturierte AI-Metadaten.
- Model: 5.3 codex
- Reason: Mehrere neue Backend-Module mit AI-Gating und deterministischen Fehlerpfaden.

### TASK-098.9 AI Panel and Editable Draft Frontend
- Ziel: Die AI-Unterstuetzung als vertrauenswuerdiges, editierbares Thread-Panel in Janus Mail darstellen.
- Scope: Consent-required State, AI-Zusammenfassung, Prioritaetsanzeige, Reply-Hinweis, Draft-Panel und stale-Markierung im Frontend.
- Files: `frontend/js/mail-modal.js`, `frontend/css/mail-modal.css`, `tests/e2e/mail-ai-panel.spec.js`
- Steps:
  1. Consent-required State im AI-Panel rendern.
  2. Summary-, Priority- und Reply-Needed-Komponenten in der Thread-Surface integrieren.
  3. Editierbaren Draft-Block mit Tonwechsel-Flow anbinden.
  4. E2E-Test fuer consent OFF, consent ON, provider error und stale-state schreiben.
- Acceptance Criteria:
  - [ ] Das AI-Panel zeigt bei fehlendem Consent keinen versteckten Analysepfad.
  - [ ] Summary, Priority und Reply-Hinweis erscheinen nur fuer freigegebene Threads.
  - [ ] Draft-Text bleibt vor dem Senden voll editierbar.
  - [ ] Providerfehler und stale-state sind sichtbar, ohne die manuelle Mailnutzung zu blockieren.
- Tests:
  - `tests/e2e/mail-ai-panel.spec.js` prueft consent-required, Draft-Editierbarkeit, Providerfehler und stale-summary Anzeige.
  - Frontend-Verhaltenstest fuer keinen impliziten Send-Trigger aus AI-Aktionen.
- Model: 5.3 codex
- Reason: Geschlossene Frontend-Arbeit fuer den kompletten AI-Panel-Fluss mit nutzerzentrierten Zustandswechseln.

## IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS WITH FIXES
- **Completed At:** 2026-05-30
- **Validation Evidence:**
  - `python -m py_compile backend/services/chat_orchestrator.py backend/services/mail/mail_ai_assist_service.py backend/data/schemas_mail.py` PASS
  - `python -m pytest -q backend/tests/test_mail_service.py backend/tests/test_mail_chat_account_guard_store.py backend/tests/test_mail_send_guard_store.py backend/tests/test_memory_extractor_email_pii.py backend/tests/test_mail_ai_assist_service.py backend/tests/unit/test_intent_engine.py` PASS (44 passed)
  - `node --test frontend/tests/mail-modal.test.mjs frontend/tests/mail-inbox-ui.test.mjs` PASS (7 passed)
- **Related Specs:**
  - `documentation/SPEC/Spec Done/10_janus_mail_module_shell_and_connection_state.md`
  - `documentation/SPEC/Spec Done/11_janus_mail_gmail_thread_inbox_and_search.md`
  - `documentation/SPEC/Spec Done/12_janus_mail_manual_actions_and_attachments.md`
  - `documentation/SPEC/Spec Done/13_janus_mail_ai_thread_assist_and_draft_replies.md`

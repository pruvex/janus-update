# Task 021: Smart Chat Naming System (Feature 10)

## 1. Ziel & Kontext

**Ziel:** Automatische, semantische Titelgenerierung für Chats statt langer Erstzeilen — kurz, verständlich, thematisch präzise (Dossier: `documentation/Planned Features/Smart Chat Naming.md`).

**Kernlieferungen (Planung → Umsetzung):**

- **Backend-Trigger:** Nach **2** abgeschlossenen Nachrichten (User+Assistant-Turn oder definierte Message-Count-Regel) einmalig bzw. bei signifikantem Themenwechsel prüfen und ggf. Titel setzen.
- **LLM-Naming:** Dedizierter, billiger Aufruf (kurzer Prompt, begrenzte Tokens) mit Regeln: 3–6 Wörter, keine Füllwörter, keine Satzzeichen, Sprache wie Nutzer.
- **Persistenz / Vertrag:** Kennzeichnung `auto_generated` vs. User-Override — nach manuellem Titel **kein** automatisches Überschreiben mehr; optional `last_topic_hash` für Themenwechsel-Erkennung (siehe Dossier §Datenstruktur).
- **UI:** Inline-Bearbeitung des Chat-Titels (Klick → Input; bestehendes Rename via Kontextmenü kann erweitert/vereinheitlicht werden).

**Status:** **DONE** (Live-Test bestanden, 2026-04-12)

---

## 2. Impact-Analyse & Abhängigkeiten

- **Basiert auf:** Bestehende Chat-Persistenz (`Chat.title`), Message-Store, Orchestrator-Finalize/Stream-Pfad; LLM-Gateway für Mini-Completion.
- **Beeinflusst:**
  - Memory-/Recall-Prompts, die Chat-Titel als Metadaten zitieren — Konsistenz mit „Single Source of Truth“ für Titel.
  - API `PUT /chats/{id}/title` — muss User-Override (`auto_generated=false`) abbilden, sobald Spalten/Schema existieren.
  - Frontend Chat-Liste (`frontend/js/chat.js` o. ä.) — Titelanzeige, SSE/Refresh nach Auto-Rename.
- **Risiko-Einschätzung:** **MEDIUM** (DB-Migration + Orchestrierungs-Timing + Kosten/Latenz des Zusatz-LLM-Calls).

---

## 3. Betroffene Dateien

**Backend (erwartet):**

- `backend/data/models.py` — `Chat`: ggf. `auto_generated`, `last_topic_hash` (oder JSON-Metafeld).
- `backend/data/crud.py` / Schemas — Create/Update Chat, Title-Update mit Override-Flag.
- `backend/api/routers/chat.py` — `PUT /chats/{chat_id}/title` Body erweitern; ggf. Event/Response für Auto-Titel.
- `backend/services/chat_orchestrator.py` und/oder Finalize-/Background-Pfad — **Trigger** nach N Nachrichten.
- `backend/services/llm_gateway.py` (oder kleines `chat_title_service.py`) — isolierter Naming-Call.
- Alembic-Migration — neue Spalten.

**Frontend (erwartet):**

- `frontend/js/chat.js` (Sidebar) — Inline-Edit, sanftes Update nach Auto-Rename (Polling oder SSE-Metadaten, je nach bestehendem Muster).

**Referenz:** `documentation/Planned Features/Smart Chat Naming.md`

---

## 4. Umsetzungsschritte (Diamond-Flow)

### Epic-Phasen (Grobdesign)

| Phase | Inhalt | Status |
|-------|--------|--------|
| **A** | Schema + CRUD + API-Vertrag (`auto_generated`, Override-Regel) | ✅ |
| **B** | Naming-Prompt, LLM-Aufruf, Fallback („Neuer Chat“ bei Minimal-Input) | ✅ |
| **C** | Orchestrator-Trigger nach 2 Nachrichten, Idempotenz / nur wenn Titel noch Default/leer | ✅ |
| **D** | UI Inline-Edit + Liste aktualisieren | ✅ |
| **E** | Tests (Unit + Integration), Edge Cases laut Dossier | ⬜ (optional / manuell Live-Test) |

### Checkliste

- [x] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [x] **Phase 2 (Implementierung):**
  - [x] DB-Felder und Migration; Pydantic/CRUD.
  - [x] Trigger-Hook nach persistiertem zweiten Turn (Definition „Nachricht“ festziehen: User+Assistant = 1 Turn vs. 2 Messages).
  - [x] LLM-Prompt gemäß Dossier (`{{first_messages}}`), Topic-Hash optional.
  - [x] `PUT` Title setzt bei User-Edit `auto_generated=false`.
  - [x] Frontend: Inline-Edit; kein harter Layout-Sprung.
- [x] **Phase 3 (Testing):** manuell Live-Test Sidebar-Titel (Gemini + GPT); pytest nach Bedarf.
- [x] **Phase 4 (Post-Check):** `/post-impl` — siehe §6/§7.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

---

## 5. Test-Vorgaben

- [x] Live-Regression: Smart Naming End-to-End (Stream, Sidebar, GPT + Gemini).
- [ ] Optional: `python -m pytest backend/tests -q` + gezielte Unit-Tests für `update_chat_title` / Titel-Trigger (Follow-up).

---

## 6. Ergebnis & Audit-Trail

**Abschluss:** 2026-04-12 — Epic **Smart Chat Naming** produktiv; Live-Test (Gemini + GPT) bestanden.

### Backend-Trigger (Finalize / Stream)

- Der Naming-Job wird **nach persistierter Assistenten-Antwort** ausgelöst, nicht lose im Router.
- **`finalize_response_async`** (`backend/services/orchestrator/response_finalizer.py`) öffnet eine **frische DB-Session** (Stream-/Concurrency-Pattern wie Turbo-Flow), baut `OrchestratorStatusSync`, ruft **`finalize_response`** auf.
- In **`finalize_response`** unmittelbar nach `status_sync.persist_assistant_message(...)`: **`_trigger_chat_title_job_if_eligible(db, request.chat_id)`**.
- Bedingungen (Kern): **mindestens 2 Messages** im Chat, **`last_topic_hash` noch nicht gesetzt** (erster Naming-Lauf); Platzhalter-Titel werden über **`PLACEHOLDER_TITLES`** und **`_title_looks_replaceable`** erkannt — kein hartes `auto_generated`-Gate für den ersten Lauf.
- Scheduling: **`asyncio.create_task(run_chat_title_job(chat_id))`** — Hintergrund, blockiert den Stream nicht.

### Race-Condition / Platzhalter-Logik (GPT & Frontend)

- **Frontend (`frontend/js/chat.js`):** Entfernt voreilige **`PUT /api/chats/{id}/title`** mit Erstsatz bzw. festem „Bildanalyse“ — diese setzten **`auto_generated=false`** und verhinderten zuverlässiges Smart-Naming.
- **`frontend/js/chat-manager.js`:**  
  - **`loadChats(..., { suppressAutoCreate: true })`** beim Neuladen nach **`createNewChat`**, damit keine zweite Chat-Erstellung bei leerer Liste entsteht.  
  - Kein doppeltes Bootstrap: **`loadChats`** nicht mehr zusätzlich auf **`DOMContentLoaded`** (nur nach Auth in `app.js`).  
  - Mutex / **`await`** beim Auto-Create bei leerer Liste — verhindert parallele Doppel-Anlagen.
- **Backend Titel-LLM (OpenAI):** Das Speed-Modell (**z. B. `gpt-5.4-nano`**) lieferte für Kurz-Titel-Prompts oft **keinen Text**; der Job nutzt für OpenAI nun **`gpt-4o-mini`** (`title_generator.py`). Ohne brauchbaren Roh-Titel: **kein Commit**, **`last_topic_hash`** unverändert (kein „toter“ Abschluss).

### Live-Update UI (Polling)

- **`scheduleSmartTitleRefresh(chatId)`** und **`patchChatTitleInUI`** in **`chat-manager.js`**: nach Ende des SSE-Streams (und analog nach PDF-/Bild-Pfaden) mehrere leichte **`GET /api/chats/{id}`** (gestaffelt), Aktualisierung von Sidebar-Zeile und **`#chat-header`** ohne vollständiges **`loadChats`**-Chaos.
- Optional: SSE-**`metadata`** mit `title` / `chat_title` wird im Stream bereits ausgewertet, falls der Backend-Pfad später ergänzt wird.

**Wesentliche Dateien (Referenz):** `response_finalizer.py`, `title_generator.py`, `chat_orchestrator.py` (`handle_chat_request_stream` → `finalize_response_async`), `frontend/js/chat.js`, `frontend/js/chat-manager.js`, `backend/data/crud.py` / Models / Migration `auto_generated`, `last_topic_hash`.

---

## 7. Debugging-Log

| Thema | Symptom | Fix |
|-------|---------|-----|
| Doppel-Chats bei „Neuer Chat“ | Zwei POSTs / parallele `loadChats` + `createNewChat` | `suppressAutoCreate`, Mutex, ein Bootstrap-Pfad |
| GPT-Titel bleibt „Neuer Chat“ | Speed-Modell liefert leeren `content` | OpenAI-Titel fest **`gpt-4o-mini`**, robuste Text-Extraktion, kein Commit bei nur Platzhalter |
| Sidebar ohne F5 | Titel erst nach Refresh sichtbar | `scheduleSmartTitleRefresh` + `patchChatTitleInUI`, CustomEvent `janus:chat-title-updated` |

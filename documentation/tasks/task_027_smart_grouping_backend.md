# Task 027: Smart Chat Grouping & Sorting (Feature 11) — COMPLETE

## Status

**DONE** (2026-04-13) — Backend (Welle 1) + Frontend (Sortierung, Ordner, Suche) + P0 SQLite-Drift-Fix verifiziert

## Epic / Feature

**Feature 11 — Smart Chat Grouping + Hybrid Sorting:** Chats werden **automatisch kategorisiert**; der Nutzer wählt **Sortierung** (chronologisch, Kategorien, A–Z), **durchsucht Titel** unabhängig davon, und der Modus wird in **`localStorage`** gehalten.

## Ziel — erreicht

### Backend (Welle 1)

1. **Datenbank:** Spalte `chats.category` (String, `NOT NULL`, Default `general`).
2. **API:** `category` in **Pydantic** (`ChatBase` / `ChatResponse`).
3. **Titel-Job (`title_generator.py`):** LLM liefert **JSON** `{ "title": "...", "category": "..." }`; Parser schreibt **Titel + Kategorie** — Klassifikation „im Stillen“ beim Smart-Naming (Task 021).

### Frontend (Welle 2)

4. **Sidebar:** `#chat-list-sort-select` (Chronologisch, Kategorien (AI), Alphabetisch), `#chat-list-search`, Ordner **`.chat-folder`** mit Header/Chevron/📁, Persistenz **`janus_chat_list_sort_mode`**.

### P0 Emergency Fix (Produktion)

5. **`_ensure_sqlite_schema_migrations`** in `backend/data/database.py`: bei SQLite fehlende Spalte **`chats.category`** wird beim Start **automatisch** per `ALTER TABLE` nachgezogen (Drift vs. Alembic-only oder alte DBs). Siehe `WHAT_I_LEARNED.md` — Pattern **SQLite Schema Drift Protection**.

## Kategorien (LLM + DB)

Erlaubte Werte (exakt, lowercase): **coding**, **cooking**, **personal**, **business**, **research**, **general**.

Unbekannte oder fehlende Kategorie aus dem Modell → **`general`**.

## Umsetzung (Referenz)

### Migration / ORM / API

- Alembic: `alembic/versions/2026_04_12_chats_category_smart_grouping.py`
- `backend/data/models.py` — `Chat.category`
- `backend/data/schemas.py` — `ChatBase.category`
- `backend/data/database.py` — `_ensure_sqlite_schema_migrations` (users + **chats.category**, kein früher Return mehr)

### Title-Job

- System-Prompt: nur **valides JSON** mit `title` und `category`
- `_parse_title_category_payload`, `run_chat_title_job` → DB-Update

### Frontend

- `frontend/index.html` — Toolbar, Labels (z. B. „Chronologisch (Neu oben)“)
- `frontend/js/chat-manager.js` — `groupChatsByCategory`, `renderChatList`, Snapshot + Suche
- `frontend/css/style.css` — `.chat-folder*`, Toolbar-Hinweis

### Trigger

- `response_finalizer` → `run_chat_title_job` (wie Task 021)

## A1–G17 (Foundation-Matrix)

Zuordnung dokumentiert in **`PROJECT_STATE.md` SECTION 1b** (B6, C7, C8, G17, D10).

## Betroffene Dateien (Auszug)

- `backend/data/database.py`, `models.py`, `schemas.py`
- `backend/services/orchestrator/title_generator.py`
- `alembic/versions/2026_04_12_chats_category_smart_grouping.py`
- `frontend/index.html`, `frontend/js/chat-manager.js`, `frontend/css/style.css`
- `backend/tests/test_title_generator_parse.py`, `backend/tests/test_crud.py`

## Kurztest / Rollout

- [x] Parser-Unit-Tests: `backend/tests/test_title_generator_parse.py`
- [x] Produktions-DB: fehlende Spalte → manuelles `ALTER` oder Auto-Migration beim Start
- [x] UI: Sortierung, Ordner, Suche, A/B-Actions in Ordnern
- [x] Post-Impl: PROJECT_STATE, WHAT_I_LEARNED, Registry

## Follow-up (optional)

- Manuelles PATCH `category`, Analytics, Ordner-Collapse-Persistenz

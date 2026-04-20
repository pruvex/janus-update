# Task: M-MEM-05 — Unified Memory Tools Phase 5

---

## 1. Ziel & Kontext

**Ziel:** Standardisierte Tool-Suite für LLM-gesteuerte Memory-Operationen (Write/Read/Update/History) mit Permission-Checks und Guard-Schutz.

**Kontext:** Phase 5 der Memory V2 Roadmap. Baut auf Phase 3 (Enricher + Guard) und Phase 4 (Cache + Cleanup) auf. Ermöglicht dem LLM gezielte Memory-Manipulation über Tools statt nur implizite Extraktion.

---

## 2. Impact-Analyse & Abhängigkeiten

### Basiert auf (REQUIRES):
- ✅ Phase 3: `enrich_fact()`, `apply_priority_guard()` in `memory_enricher.py`
- ✅ Phase 3: `memory_cache.invalidate()` für Update-Pfad  
- ✅ Phase 4: Feature-Flag Infrastruktur
- ✅ `update_memory_snippet()` in `memory_manager.py` (Zeile 763)

### Beeinflusst (BLOCKS):
- Phase 6: E2E Tool-Integration Tests
- Zukünftige Skills die Memory-Tools nutzen

### Risiko-Einschätzung:
- **Hoch**: `memory_update` MUSS `user_editable` prüfen — Fehlender Check = Security Bug
- **Mittel**: JSON-Feld `change_history` erfordert DB-Migration
- **Niedrig**: Tool-Schemas sind deklarativ

---

## 3. Betroffene Dateien

### Neu erstellen:
- `documentation/tasks/task_M-MEM-05_unified_memory_tools.md` (diese Datei)
- `backend/skills/system/memory_write.json`
- `backend/skills/system/memory_read.json`
- `backend/skills/system/memory_update.json`
- `backend/skills/system/memory_history.json`
- `backend/tools/memory_tools.py`
- `backend/tests/test_memory_tools.py`
- `alembic/versions/xxxx_add_change_history_to_memories.py`

### Modifizieren:
- `backend/data/models.py` — `change_history` JSON-Feld hinzufügen
- `backend/services/memory_manager.py` — Update-Pfad muss History befüllen

---

## 4. Umsetzungsschritte

### Schritt 4.1: DB-Migration
```bash
alembic revision -m "add_change_history_to_memories"
```
Spalte `change_history = Column(JSON, default=list)` zu `Memory` Model.

### Schritt 4.2: Tool-JSON-Schemas (4 Dateien)
Vollständige Schemas in `documentation/features/memory_v2.md` Section 5.1–5.4:

| Tool | Required Params | Sicherheitskritisch |
|------|-----------------|---------------------|
| `memory_write` | `fact` | `priority_override` max=0.95 |
| `memory_read` | `query` | `include_expired` default=false |
| `memory_update` | `memory_id`, `new_fact` | `user_editable` MUSS true sein |
| `memory_history` | `memory_id` | Nur Lesen, risk_level=low |

### Schritt 4.3: Handler-Implementation
```python
# backend/tools/memory_tools.py

async def handle_memory_write(params, db, chat_id) -> dict:
    # 1. fact_object bauen
    # 2. enrich_fact() + apply_priority_guard()
    # 3. save_memory_snippet()
    # 4. Return {status, memory_id, priority}

async def handle_memory_read(params, db) -> dict:
    # 1. Vektor-Suche
    # 2. Filter (min_priority, tags, include_expired)
    # 3. Limit max 50
    # 4. Return {memories, total_found}

async def handle_memory_update(params, db) -> dict:
    # 1. Lade Memory
    # 2. CHECK user_editable == True
    # 3. update_memory_snippet()
    # 4. Cache invalidate
    # 5. change_history append
    # 6. Return {status, memory_id}

async def handle_memory_history(params, db) -> dict:
    # 1. Lade Memory
    # 2. Return change_history + current_state
```

### Schritt 4.4: Permission-Matrix (NICHT VERHANDELBAR)

| Operation | `user_editable=true` | `user_editable=false` | source_skill Cap |
|-----------|---------------------|----------------------|-----------------|
| write | ✅ Erlaubt | N/A (neu) | 0.95 |
| read | ✅ Immer | ✅ Immer | N/A |
| update | ✅ Erlaubt | ❌ 403 Error | 0.95 |
| history | ✅ Immer | ✅ Immer | N/A |

---

## 5. Test-Vorgaben

```bash
pytest backend/tests/test_memory_tools.py -v
```

| # | Test | Expected |
|---|------|----------|
| 1 | Write Roundtrip | Memory found with correct priority |
| 2 | Write Guard (0.99 → cap 0.95) | priority == 0.95 |
| 3 | Read Filter Tags | Only tagged memories |
| 4 | Read Min Priority | Only high-priority |
| 5 | Update Happy Path | snippet changed, cache invalidated |
| 6 | Update Blocked | Error: "not_editable" |
| 7 | History After Update | change_history has 1 entry |

---

## 6. Ergebnis & Audit-Trail

**Status:** ✅ COMPLETED

**Impl-Loop:** ✅ IMPL → ✅ TEST → ✅ LINTER → ✅ IMPORTS → ✅ DIAMOND-REPORT

**Dateien erstellt:**
- ✅ `backend/skills/system/memory_write.json`
- ✅ `backend/skills/system/memory_read.json`
- ✅ `backend/skills/system/memory_update.json`
- ✅ `backend/skills/system/memory_history.json`
- ✅ `backend/tools/memory_tools.py`
- ✅ `backend/tests/test_memory_tools.py`
- ✅ `alembic/versions/2026_04_06_add_change_history.py`

**Dateien modifiziert:**
- ✅ `backend/data/models.py` — `change_history` JSON-Feld hinzugefügt

**Logging-Prefixe implementiert:**
- `[TOOL WRITE]` — Skill=X, Key=Y, Priority=Z
- `[TOOL READ]` — Query=X, Found=Y, Filtered=Z
- `[TOOL UPDATE]` — ID=X, user_editable=Y, source=Z
- `[TOOL HISTORY]` — ID=X, Entries=Y

**Test-Resultate:**
```
pytest backend/tests/test_memory_tools.py -v
16 passed in 0.89s

Test 1: Write Roundtrip ✅
Test 2: Write Guard (0.99 → cap 0.95) ✅
Test 3: Read Filter Tags ✅
Test 4: Read Min Priority ✅
Test 5: Update Happy Path ✅
Test 6: Update Blocked (user_editable=false) ✅
Test 7: History After Update ✅
```

**Security-Checks implementiert:**
- ✅ `memory_update` prüft `user_editable` VOR Änderung (403 wenn false)
- ✅ `memory_write` apply_priority_guard() enforced (Cap=0.95)
- ✅ `memory_update` priority_guard enforced (Cap=0.95)
- ✅ `memory_read` DSGVO: `include_expired` default=false

**Audit-Trail-Feld:**
- ✅ JSON-Array `change_history` auf Memory-Model
- ✅ Automatisches Befüllen bei `memory_update`
- ✅ Schema: `{timestamp, action, old_snippet, new_snippet, source}`

---

## 7. Debugging-Log

### 2026-04-06 — Implementation Complete
- **20:00** Task aus work order generiert
- **20:05** Tool-JSON-Schemas erstellt (4 Dateien)
- **20:10** models.py + Alembic Migration für change_history
- **20:15** memory_tools.py mit 4 Handlern implementiert
- **20:20** Tests erstellt (16 Tests)
- **20:25** SkillResponse.status Fix: 'success' → 'ok'
- **20:30** Pydantic-Validierung Fix: 0.99 wird akzeptiert, intern gekappt
- **20:35** Linter-Fehler behoben (imports, bare except, == None)
- **20:40** Migration ausgeführt: `alembic upgrade head`
- **20:45** Alle 16 Tests passed

### Herausforderungen & Lösungen
1. **SkillResponse.status** — Erwartet 'ok', nicht 'success' → Alle Handler korrigiert
2. **Pydantic Validation** — `priority_override` max=0.95 blockte 0.99 → Auf max=1.0 geändert, intern gekappt
3. **Test Assertions** — Vergessene 'success' → 'ok' Updates → Grep-Suche + Multi-Edit
4. **Linter** — Bare except, == None, Import-Ordnung → Ruff --fix + manuelle Fixes

### Verification Commands
```bash
# Tests
pytest backend/tests/test_memory_tools.py -v

# Linter
python -m ruff check backend/tools/memory_tools.py backend/tests/test_memory_tools.py

# Migration Status
alembic current

# DB Schema Check
sqlite3 janus.db ".schema memories" | grep change_history
```

---

**Task-Log:** `documentation/tasks/task_M-MEM-05_unified_memory_tools.md` aktualisiert (Sektion 6 & 7 ausgefüllt)


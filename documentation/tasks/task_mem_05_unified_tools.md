---
**Task-ID:** M-MEM-05
**Modell:** Kimi K2.5 (Windsurf)
**Audit:** Opus 4.6 (Lead Architect Review 2026-04-06)
**Ref:** `documentation/features/memory_v2.md` Section 5

**IST (Codebase-Zustand):**
- Memory-Schreibzugriff läuft ausschließlich über `memory_extractor.py` → `save_memory_snippet()`. Kein LLM-Tool kann Memories direkt erstellen, lesen oder aktualisieren.
- `update_memory_snippet()` existiert bereits (Zeile 763 in `memory_manager.py`) — kann als Basis für `memory_update` Tool genutzt werden.
- Kein Audit-Trail für Memory-Änderungen vorhanden (weder Tabelle noch JSON-Feld).
- Bestehende Tool-Datei `backend/tools/finance_tools.py` zeigt das Tool-Pattern für dieses Projekt.

**SOLL (nach Phase 5):**
- 4 Tool-JSON-Schemas in `backend/skills/system/` mit vollständigen Parameter-Definitionen.
- `backend/tools/memory_tools.py` implementiert alle 4 Handler.
- Jeder Write durchläuft `enrich_fact()` + `apply_priority_guard()` (Phase 3).
- `memory_update` prüft `user_editable` Flag VOR der Änderung.
- `memory_history` nutzt ein JSON-Array-Feld auf dem Memory-Model (kein extra Table).

**IMPL-LOOP:**
```
[IMPL → TEST → LINTER → IMPORTS → DIAMOND-REPORT]
```

---

# 1. Ziel

Standardisierte Tool-Suite, damit der LLM Memories gezielt schreiben, lesen, aktualisieren und historisieren kann — mit Permission-Checks und Guard-Schutz.

---

# 2. Abhängigkeiten

**REQUIRES (muss existieren):**
- Phase 3: `enrich_fact()`, `apply_priority_guard()` in `memory_enricher.py` ✅
- Phase 3: `memory_cache.invalidate()` für Update-Pfad ✅
- Phase 4: Feature-Flag Infrastruktur ✅

**BLOCKS (wartet auf uns):**
- Phase 6: E2E Tool-Integration Tests

---

# 3. Exakte Integrationspunkte (KRITISCH)

### 3.1 Tool-JSON-Schemas (4 Dateien)

Erstelle 4 JSON-Dateien. **Vollständige Schemas stehen in `memory_v2.md` Section 5.1–5.4.** Hier die KRITISCHEN Punkte:

| Tool | Datei | Required Params | Sicherheitskritisch |
|------|-------|-----------------|---------------------|
| `memory_write` | `backend/skills/system/memory_write.json` | `fact` | `priority_override` max=0.95, Guard cappt zusätzlich per `source_skill` |
| `memory_read` | `backend/skills/system/memory_read.json` | `query` | `include_expired` default=false (DSGVO: abgelaufene Daten nicht aktiv anbieten) |
| `memory_update` | `backend/skills/system/memory_update.json` | `memory_id`, `new_fact` | `user_editable` MUSS true sein, sonst 403 |
| `memory_history` | `backend/skills/system/memory_history.json` | `memory_id` | Nur Lese-Zugriff, risk_level=low |

### 3.2 Handler-Implementation: `backend/tools/memory_tools.py`

```python
# backend/tools/memory_tools.py

async def handle_memory_write(params: dict, db: Session, chat_id: int) -> dict:
    """
    FLOW:
    1. Baue fact_object aus params (fact, category, subject_name, etc.)
    2. enrich_fact(fact_object, source_skill="skill.memory_write")
    3. Falls priority_override: MIN(priority_override, 0.95)
    4. apply_priority_guard(priority, "skill.memory_write") → Cap=0.95
    5. save_memory_snippet(db, chat_id, fact_object, source_type="tool")
    6. Return: {status: "saved", memory_id, priority}
    """

async def handle_memory_read(params: dict, db: Session) -> dict:
    """
    FLOW:
    1. Vektor-Suche mit params["query"]
    2. Filter: min_priority, filter_tags, include_expired
    3. Limit: params.get("limit", 10), max 50
    4. Return: {memories: [...], total_found}
    """

async def handle_memory_update(params: dict, db: Session) -> dict:
    """
    FLOW:
    1. Lade Memory by ID
    2. CHECK: memory.user_editable == True, sonst → {"error": "not_editable"}
    3. Nutze bestehende update_memory_snippet() (Zeile 763 memory_manager.py)
    4. Cache invalidate nach Update
    5. Return: {status: "updated", memory_id}
    """

async def handle_memory_history(params: dict, db: Session) -> dict:
    """
    FLOW:
    1. Lade Memory by ID
    2. Lese memory.change_history (JSON-Array oder leere Liste)
    3. Return: {memory_id, history: [...], current_state}
    
    NOTE: change_history Feld muss bei Update befüllt werden:
    memory.change_history.append({
        "timestamp": now.isoformat(),
        "action": "update",
        "old_snippet": old_snippet,
        "source": source_skill
    })
    """
```

### 3.3 Permission-Matrix (NICHT VERHANDELBAR)

| Operation | `user_editable=true` | `user_editable=false` | source_skill Cap |
|-----------|---------------------|----------------------|-----------------|
| write | ✅ Erlaubt | N/A (neues Memory) | 0.95 |
| read | ✅ Immer | ✅ Immer | N/A |
| update | ✅ Erlaubt | ❌ 403 Error | 0.95 |
| history | ✅ Immer | ✅ Immer | N/A |

### 3.4 Audit-Trail-Feld (DB)

**ENTSCHEIDUNG:** Kein neuer Table. Stattdessen JSON-Array-Feld auf `Memory`-Model.

Prüfe ob `change_history` Spalte in `models.py` existiert. Falls nicht:
```python
# In models.py Memory-Klasse:
change_history = Column(JSON, default=list)  # [{timestamp, action, old_snippet, source}]
```

Falls eine Alembic-Migration nötig ist, erstelle sie.

---

# 4. Test-Vorgaben

```bash
pytest backend/tests/test_memory_tools.py -v
```

| # | Test | Action | Expected |
|---|------|--------|----------|
| 1 | Write Roundtrip | write(fact="Test") → read(query="Test") | Memory found with correct priority |
| 2 | Write Guard | write(priority_override=0.99, source=skill) | priority capped to 0.95 |
| 3 | Read Filter Tags | write(tags=["pet"]) → read(filter_tags=["pet"]) | Only tagged memories |
| 4 | Read Min Priority | read(min_priority=0.8) | Only high-priority memories |
| 5 | Update Happy Path | update(id=X, new_fact="Updated") | snippet changed, cache invalidated |
| 6 | Update Blocked | update(id=X) where user_editable=false | Error: "not_editable" |
| 7 | History After Update | update(id=X) → history(id=X) | change_history has 1 entry |

---

# 5. Audit-Trail

**Status:** ⏳ PENDING (Phase 5/6)
**Opus-Audit:** 2026-04-06 — Permission-Matrix definiert, Audit-Trail als JSON-Feld statt extra Table.

**WARNUNG:** `memory_update` MUSS `user_editable` prüfen. Ein fehlender Check ist ein Security-Bug.

**Logging-Prefixe:**
- `[TOOL WRITE]` — Skill=X, Key=Y, Priority=Z (guarded)
- `[TOOL READ]` — Query=X, Found=Y, Filtered=Z
- `[TOOL UPDATE]` — ID=X, user_editable=Y, source=Z
- `[TOOL HISTORY]` — ID=X, Entries=Y

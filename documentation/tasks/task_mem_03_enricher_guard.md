---
**Task-ID:** M-MEM-03
**Modell:** Kimi K2.5 (Windsurf)
**Audit:** Opus 4.6 (Lead Architect Review 2026-04-06)
**Ref:** `documentation/features/memory_v2.md` Section 4.2, 4.4

**IST (Codebase-Zustand):**
- `memory_extractor.py` Zeile 620-627: LLM extrahiert Fakten, Kategorie wird normalisiert, aber priority/ttl/tags werden NICHT gesetzt — die V2-Spalten (priority, memory_type, ttl, tags, source_skill) bleiben auf DB-Defaults.
- `memory_manager.py` Zeile 266-275: Bei Duplikat-Hash wird der Fakt komplett ignoriert (`return None`) — kein Merge, keine Priority-Aktualisierung.
- `memory_manager.py` Zeile 290-292: Priority wird aus `memory_type`-String abgeleitet (CORE_IDENTITY→2, CORE_DETAIL→1). Diese Logik ist hart-codiert statt regelbasiert.
- `memory_extractor.py` Zeile 584: Keine Absicherung gegen Provider-Ausfälle — jeder Chat-Turn triggert einen LLM-Extraction-Call, auch bei Dauerausfall.

**SOLL (nach Phase 3):**
- `enrich_fact()` setzt priority/ttl/tags/memory_type deterministisch NACH Kategorie-Normalisierung.
- Duplikate werden per `_merge_existing_memory()` aktualisiert statt ignoriert.
- `apply_priority_guard()` cappt Priority basierend auf `source_skill`.
- `ExtractionCircuitBreaker` sperrt nach 3 Failures für 120s.
- `parse_embedding()` eliminiert redundante `json.loads()` in Retrieval.

**IMPL-LOOP:**
```
[IMPL → TEST → LINTER → IMPORTS → DIAMOND-REPORT]
```

---

# 1. Ziel

6 neue/modifizierte Dateien liefern die Intelligenzschicht zwischen LLM-Extraktion und DB-Persistenz. Kein LLM-Output gelangt mehr ungefiltert in die Datenbank.

---

# 2. Abhängigkeiten

**REQUIRES (muss existieren):**
- Phase 1: V2-Spalten in `models.py` (priority, memory_type, ttl, tags, source_skill, user_editable, canonical_key) ✅
- Phase 2: `memory_cache.py` mit `put()`, `invalidate()` ✅

**BLOCKS (wartet auf uns):**
- Phase 4: `retrieve_diamond_slots()` braucht `parse_embedding()` aus diesem Task
- Phase 5: `memory_write` Tool braucht `apply_priority_guard()` aus diesem Task

---

# 3. Exakte Integrationspunkte (KRITISCH)

### 3.1 Enricher-Integration in `memory_extractor.py`

**WO:** Nach Zeile 627 (`item["category"] = normalized_cat`) und VOR Zeile 629 (canonical_key Regenerierung).

```python
# memory_extractor.py, nach Zeile 627:
from backend.services.memory_enricher import enrich_fact

# NACH Kategorie-Normalisierung, VOR canonical_key:
item = enrich_fact(item, source_skill="system.extractor")
# enrich_fact() setzt: priority, ttl, tags, memory_type, source_skill, user_editable
```

**WARUM HIER:** Die Enricher-Regeln basieren auf `category` und `predicate`. Beide sind erst nach Zeile 627 normalisiert. Die `canonical_key`-Regenerierung ab Zeile 629 kann danach unverändert bleiben.

### 3.2 Dedup-Merge in `memory_manager.py`

**WO:** Zeile 271-275 — ersetze `return None` durch `_merge_existing_memory()`.

**VORHER (aktuell):**
```python
# Zeile 271-275 in memory_manager.py:
if existing:
    logger.info(f"[DUPLICATE HASH] Ignoriere bekannten Fakt (Key: {key})")
    existing.last_accessed_at = datetime.datetime.now()
    db.commit()
    return None  # <-- BUG: Neue Metadaten gehen verloren
```

**NACHHER:**
```python
if existing:
    _merge_existing_memory(db, existing, fact_object, source_type)
    return existing  # <-- Merged statt ignoriert
```

### 3.3 Priority-Guard in `memory_manager.py`

**WO:** Zeile 286-294 — VOR dem `models.Memory(...)` Konstruktor.

**VORHER (aktuell):**
```python
# Zeile 290-292: Harte core_priority-Ableitung
core_priority = 0
if memory_type == "CORE_IDENTITY": core_priority = 2
elif memory_type == "CORE_DETAIL": core_priority = 1
```

**NACHHER (zusätzlich):**
```python
from backend.services.memory_enricher import apply_priority_guard

# Guard anwenden auf enriched priority
enriched_priority = fact_object.get("priority", 0.50)
source_skill = fact_object.get("source_skill", "system.extractor")
guarded_priority = apply_priority_guard(enriched_priority, source_skill)
```

Dann im `models.Memory()` Konstruktor die V2-Felder setzen:
```python
priority=guarded_priority,
memory_type=fact_object.get("memory_type", "GENERAL"),
ttl=fact_object.get("ttl"),
tags=fact_object.get("tags", []),
source_skill=source_skill,
user_editable=fact_object.get("user_editable", True),
canonical_key=key,
```

### 3.4 Circuit-Breaker in `memory_extractor.py`

**WO:** Zeile 509 (Beginn des `try`-Blocks in `extract_and_save_fact_from_interaction`).

```python
# Am Anfang von memory_extractor.py (Modul-Level):
_extraction_breaker = ExtractionCircuitBreaker(failure_threshold=3, recovery_timeout=120)

# Zeile 509, direkt nach `try:`:
if not _extraction_breaker.can_execute():
    logger.info("[EXTRACTION] Circuit breaker OPEN — skipping extraction")
    return []
```

**SUCCESS/FAILURE Recording:**
- Nach Zeile 590 (nach `_generate_fact_extraction_items_with_self_healing`): `_extraction_breaker.record_success()`
- Im `except Exception` Block (Zeile 759-761): `_extraction_breaker.record_failure()`

### 3.5 Embedding-Cache in `memory_manager.py`

**WO:** 5 Hotspots in `retrieve_diamond_context()`:
- Zeile 654: `json.loads(m.embedding_json)` → `parse_embedding(m.embedding_json)`
- Zeile 687: `json.loads(m.embedding_json)` → `parse_embedding(m.embedding_json)`
- Zeile 699: `json.loads(m.embedding_json)` → `parse_embedding(m.embedding_json)`
- Zeile 717: `json.loads(m.embedding_json)` → `parse_embedding(m.embedding_json)`
- Zeile 1085: `json.loads(mem.embedding_json)` → `parse_embedding(mem.embedding_json)`

```python
# Import am Anfang von memory_manager.py:
from backend.services.embedding_cache import parse_embedding
```

---

# 4. Neue Dateien (Vollständiger Code in `memory_v2.md`)

| Datei | Spec-Section | Kerninhalt |
|-------|-------------|------------|
| `backend/services/memory_enricher.py` | §4.2 | 9 `PRIORITY_RULES`, `TTL_RULES`, `TAG_RULES`, `PRIORITY_CAPS`, `enrich_fact()`, `apply_priority_guard()` |
| `backend/services/embedding_cache.py` | §4.4.2 | `@lru_cache(maxsize=2048)` für `parse_embedding(raw: bytes)` |
| `backend/services/memory_observability.py` | §4.4.4 | `MemorySystemMetrics` Singleton, thread-safe `increment()`, `snapshot()` |
| `backend/tests/test_memory_enricher.py` | — | 12 Unit Tests (siehe §5) |

---

# 5. `_merge_existing_memory()` — Exakte Regeln

```python
def _merge_existing_memory(db, existing, new_fact, new_source_skill):
    """
    REGELN (Opus V2.1 — NICHT VERHANDELBAR):
    1. Priority: MAX(existing.priority, new_fact["priority"])
    2. Tags: UNION(existing.tags, new_fact["tags"])
    3. source_skill: Behalte existing.source_skill, logge Collision
    4. snippet: Überschreibe NUR wenn new > existing priority
    5. last_accessed_at: NOW()
    6. Cache: invalidate(existing.id) nach Merge
    """
```

---

# 6. Test-Vorgaben

```bash
pytest backend/tests/test_memory_enricher.py -v
```

| # | Test | Input | Expected |
|---|------|-------|----------|
| 1 | Core Identity Priority | `{category: "Physis", predicate: "name_is"}` | priority=0.95 |
| 2 | Core Physical Priority | `{category: "Physis", predicate: "hat_frisur"}` | priority=0.90 |
| 3 | Pet Identity Priority | `{category: "Haustier-Details", predicate: "name_is"}` | priority=0.88 |
| 4 | Temporal TTL | `{category: "Termine"}` | ttl=2592000 (30d) |
| 5 | Permanent TTL | `{category: "Physis"}` | ttl=None |
| 6 | Tag Auto-Assign | `{category: "Stil", predicate: "traegt_brille"}` | tags⊇["fashion","wearing"] |
| 7 | Guard Clamp | priority=0.99, source=`skill.save_fact` | clamped→0.85 |
| 8 | Guard Passthrough | priority=0.80, source=`system` | unchanged=0.80 |
| 9 | Merge MAX-Priority | existing=0.75, new=0.90 | result=0.90 |
| 10 | Merge UNION-Tags | existing=["a"], new=["b"] | result=["a","b"] |
| 11 | Merge Source-Keep | existing=`system`, new=`skill.x` | result=`system` |
| 12 | CircuitBreaker States | 3× `record_failure()` | state=OPEN |

---

# 7. Audit-Trail

**Status:** ⏳ PENDING (Phase 3/6)
**Opus-Audit:** 2026-04-06 — 7 kritische Integrationspunkte identifiziert und dokumentiert.

**Logging-Prefixe:**
- `[ENRICHER]` — Rule-Matches
- `[PRIORITY GUARD]` — Clamping-Events
- `[DEDUP MERGE]` — Priority-Upgrades, Tag-Unions, Source-Collisions
- `[CIRCUIT BREAKER]` — State-Transitions (CLOSED → OPEN → HALF_OPEN)
- `[EMBEDDING CACHE]` — Hit/Miss Stats

# Pruki Memory System V2 (Diamond-OS V4.5)

## Feature Specification

**Version:** 2.1.0 (Gold Standard)  
**Status:** Final Specification — Opus Architect Reviewed  
**Date:** 2026-04-06  
**Reviewed By:** Opus 4.6 (Lead Architect), Flash-Guard V4.5, Kimi K2.5 (Initial Draft)  
**Change-Log 2.1:** LRU-bounded RAM cache, TTL zombie cleanup, knapsack budget selector, dedup merge strategy, embedding parse cache, extraction circuit-breaker, observability counters  

---

## 1. Executive Summary & Ziele

### 1.1 Vision

Das Pruki Memory System V2 ersetzt das bisherige, nahezu hardcodierte "Core-Priority" System (Integers 0/1/2) durch ein **fließendes, skalierbares Float-Priority System (0.0-1.0)**. Damit wird ermöglicht, dass Skills autonom entscheiden können, wie wichtig eine Information ist, ohne das System zu "überfluten".

### 1.2 Primärziele

| Ziel | Beschreibung | Erfolgskriterium |
|------|--------------|------------------|
| **Z1: Provider-Agnostik** | Extraktion muss mit GPT-5 (Codex), Gemini, Claude und Ollama funktionieren. Keine Modell-spezifischen Prompt-Hacks. | Alle Unit-Tests laufen mit `provider="openai"`, `provider="gemini"` und `provider="ollama"` durch. |
| **Z2: Skill-Autonomie** | Externe Skills dürfen in den Speicher schreiben, aber nicht mit `priority=1.0` den Kontext überfluten. | Priority-Guard enforced: Externe Skills max 0.7. |
| **Z3: Context Efficiency** | Keine String-Truncation mehr. Kontext wird Token-budget-aware aus priorisierten Slots zusammengesetzt. | Context-Build-Time < 50ms für 10.000 Memories. |
| **Z4: RAM Performance** | High-Priority Memories (>=0.8) müssen aus RAM kommen, nicht aus SQLite. | Abfragezeit für `priority >= 0.8` < 5ms (P95). |
| **Z5: Zero-Downtime Migration** | Bestehende Datenbank mit `core_priority` (Int) wird nahtlos auf `priority` (Float) migriert. | Alembic Migration läuft ohne Datenverlust. |
| **Z6: Resilience** | System muss OOM-sicher, zombie-frei und selbstheilend sein. Cache hat Limits, abgelaufene Memories werden automatisch bereinigt, LLM-Extraction-Fehler werden per Circuit-Breaker abgefangen. | RAM-Cache ≤ 500 Einträge, 0 Zombies nach 24h, kein Extraction-Loop bei Provider-Ausfall. |

### 1.3 Provider-Agnostik Erklärung

Das bisherige System forderte das LLM auf, `type` (CORE_IDENTITY, CORE_DETAIL, etc.) im JSON zu setzen. Das funktioniert bei GPT-4/5 zuverlässig, aber Ollama (llama3.1) und Gemini Nano liefern inkonsistente Werte oder halluzinieren Typen.

**Lösung:** Das LLM extrahiert **NUR** noch `fact`, `subject_name`, `predicate`, `object_value`, `category`, `canonical_key`, `evidence`. Alle Metadaten (`priority`, `ttl`, `tags`, `memory_type`) werden **nach** der LLM-Antwort von einem **deterministischen Python-Post-Processor** (`memory_enricher.py`) vergeben. Das macht das System unempfindlich gegen Modell-Qualitätsschwankungen.

---

## 2. Architektur-Design & Datenfluss

### 2.1 High-Level Komponenten

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DIAMOND-OS V4.5                                │
│                         Pruki Memory System V2                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │   LLM Extractor  │───>│  Memory Enricher │───>│  Priority Guard  │      │
│  │  (Provider-Agn.) │    │ (Deterministisch)│   │   (Hard-Cap)     │      │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘      │
│           │                      │                      │                     │
│           ▼                      ▼                      ▼                     │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │  Memory RAM      │    │    SQLite DB     │    │  Unified Tools   │      │
│  │  Cache (>=0.8)   │◄──►│  (Full Storage)  │◄──►│  (Write/Read/Upd)│      │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘      │
│           │                      │                      │                     │
│           ▼                      ▼                      ▼                     │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │  MemorySlot      │    │  Memory Manager  │    │  Context Manager │      │
│  │  (Dataclass)     │    │  (DB Ops)        │    │  (Budget Build)  │      │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Datenfluss: Speicher-Vorgang (Write Path)

```
1. User Input + Assistant Response
         │
         ▼
2. LLM Extraction (memory_extractor.py)
   - Prompt: Extrahiere Fakten, NICHT Metadaten
   - Output: List[ExtractedFact] (nur core Felder)
         │
         ▼
3. Memory Enricher (memory_enricher.py)
   - Eingabe: ExtractedFact + source_skill
   - Regeln: PRIORITY_RULES, TTL_RULES, TAG_RULES
   - Ausgabe: EnrichedFact (mit priority, ttl, tags, memory_type)
         │
         ▼
4. Priority Guard (memory_manager.py)
   - Prüfe: source_skill gegen PRIORITY_CAPS
   - Clamp: priority = min(raw_priority, CAP[source_skill])
   - Log: Wenn Clamping stattfand
         │
         ▼
5. Deduplizierung (memory_manager.py)
   - Hash: SHA256(canonical_key)
   - Existiert? → MERGE-STRATEGIE:
     a. Priority: MAX(existing.priority, new.priority) — höchste gewinnt
     b. Tags: UNION(existing.tags, new.tags) — additiv
     c. source_skill: Behalte Original, logge Collision
     d. last_accessed_at: NOW()
     e. snippet: Überschreibe NUR wenn new.priority > existing.priority
   - Neu? → Weiter zu Schritt 6
         │
         ▼
6. Persistenz (memory_manager.py)
   - INSERT INTO memories (alle Felder)
   - Wenn priority >= 0.8: → Cache Refresh Trigger
         │
         ▼
7. RAM Cache Update (memory_cache.py)
   - Invalidiere Entry oder Full Refresh
   - Neue Einträge mit priority >= 0.8 werden geladen
```

### 2.3 Datenfluss: Abruf-Vorgang (Read Path)

```
1. Chat Request mit Query
         │
         ▼
2. retrieve_diamond_slots() (memory_manager.py)
   a. Core Always (priority >= 0.95, global)
   b. Core Queryable (0.7 <= priority < 0.95, Vektor-Suche)
   c. Ephemeral (0.5 <= priority < 0.7, Zeit-basiert)
   d. STM (priority < 0.5 oder unklassiert, chat-spezifisch)
         │
         ▼
3. MemorySlot Erzeugung
   - Jeder Eintrag wird zu MemorySlot(text, tokens, tier, priority, memory_id)
   - Token-Count via tiktoken (cached)
         │
         ▼
4. Priority Sortierung
   - Slots nach priority (desc) sortiert
         │
         ▼
5. build_final_context() (context_manager.py)
   - Budget: max_tokens * memory_ratio (z.B. 30%)
   - Schleife: Füge Slots hinzu bis Budget ausgeschöpft
   - Output: Finales Message-Array für LLM Gateway
```

### 2.4 TTL Cleanup Lifecycle (Zombie-Prävention)

**Problem:** Memories mit `expires_at` in der Vergangenheit und `retain_until` abgelaufen werden nie gelöscht. Sie akkumulieren als "Zombies" in der DB und im Vektor-Scan.

**Lösung: Zwei-Schichten-Cleanup**

```
┌──────────────────────────────────────────────────────────────┐
│                   CLEANUP LIFECYCLE                            │
│                                                                │
│  LAYER 1: LAZY-ON-READ (Inline, bei jedem Retrieval)          │
│  ─────────────────────────────────────────────────────         │
│  retrieve_diamond_slots() filtert IMMER:                      │
│    WHERE expires_at IS NULL                                    │
│       OR expires_at > NOW()                                    │
│       OR (retain_until IS NOT NULL AND retain_until > NOW())  │
│  → Zombies erscheinen NIE im Context, auch ohne Cleanup-Job  │
│                                                                │
│  LAYER 2: BACKGROUND PURGE (Periodisch, alle 15 Min)          │
│  ─────────────────────────────────────────────────────         │
│  FastAPI BackgroundTasks / repeating_task:                     │
│    1. DELETE FROM memories                                     │
│       WHERE retain_until IS NOT NULL                           │
│       AND retain_until < NOW()                                 │
│    2. Cache invalidate für gelöschte IDs                       │
│    3. Log: "Purged {n} zombie memories"                        │
│                                                                │
│  LAYER 2b: PROMOTION CHECK (Selten, 1x pro Stunde)           │
│  ─────────────────────────────────────────────────────         │
│    Memories mit priority < 0.3 UND last_accessed_at > 30d     │
│    → Kandidaten für Soft-Delete (Archivierung)                │
│    → Nur nicht-core, nicht-user_editable                      │
└──────────────────────────────────────────────────────────────┘
```

**FastAPI Integration:**

```python
# backend/main.py — Startup-Hook
from contextlib import asynccontextmanager
from backend.services.memory_cleanup import schedule_memory_cleanup

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Schedule cleanup
    cleanup_task = asyncio.create_task(schedule_memory_cleanup(interval_seconds=900))
    yield
    # Shutdown: Cancel
    cleanup_task.cancel()

app = FastAPI(lifespan=lifespan)
```

```python
# backend/services/memory_cleanup.py
import asyncio
import logging
from datetime import datetime
from backend.data.database import SessionLocal
from backend.data import models
from backend.services.memory_cache import memory_cache

logger = logging.getLogger("janus_backend")

async def schedule_memory_cleanup(interval_seconds: int = 900):
    """Periodischer Zombie-Cleanup (alle 15 Min)."""
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            purged = purge_expired_memories()
            if purged > 0:
                logger.info(f"[MEMORY CLEANUP] Purged {purged} zombie memories")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[MEMORY CLEANUP] Error: {e}", exc_info=True)

def purge_expired_memories() -> int:
    """Löscht alle Memories deren retain_until abgelaufen ist."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        zombies = db.query(models.Memory).filter(
            models.Memory.retain_until.isnot(None),
            models.Memory.retain_until < now
        ).all()
        
        zombie_ids = [z.id for z in zombies]
        for z in zombies:
            db.delete(z)
        db.commit()
        
        # Cache-Invalidation für gelöschte IDs
        for zid in zombie_ids:
            memory_cache.invalidate(zid)
        
        return len(zombie_ids)
    except Exception as e:
        db.rollback()
        logger.error(f"purge_expired_memories failed: {e}")
        return 0
    finally:
        db.close()
```

---

## 3. Datenbankschema & Migration

### 3.1 Neues Schema (Target)

**Tabelle:** `memories`

| Spalte | Typ | Nullable | Default | Beschreibung |
|--------|-----|----------|---------|--------------|
| `id` | `INTEGER` | Nein | Auto-Inc | Primärschlüssel |
| `chat_id` | `INTEGER` | Ja | NULL | FK → chats.id (nullable für globale Memories) |
| `snippet` | `TEXT` | Ja | NULL | JSON-String des Fakts |
| `embedding_json` | `BLOB` | Ja | NULL | Vektor-Embedding (JSON-serialisiert) |
| `text_hash` | `VARCHAR(64)` | Ja | NULL | SHA256 von canonical_key (Index) |
| `canonical_key` | `VARCHAR(255)` | Ja | NULL | Menschenlesbarer Key (z.B. "max:Physis:hat:braune_haare") |
| `priority` | `FLOAT` | Nein | `0.5` | **NEU:** Float 0.0-1.0 (höher = wichtiger) |
| `memory_type` | `VARCHAR(20)` | Nein | `"GENERAL"` | **NEU:** Enum: CORE, TEMPORAL, GENERAL |
| `ttl` | `INTEGER` | Ja | NULL | **NEU:** TTL in Sekunden (NULL = permanent) |
| `expires_at` | `DATETIME` | Ja | NULL | Berechnet aus created_at + ttl |
| `retain_until` | `DATETIME` | Ja | NULL | Grace Period (expires_at + 7 Tage) |
| `tags` | `JSON` | Ja | `[]` | **NEU:** Array von Strings (z.B. ["pet", "identity"]) |
| `source_skill` | `VARCHAR(100)` | Ja | NULL | **NEU:** Skill-ID, die den Fakt geschrieben hat |
| `user_editable` | `BOOLEAN` | Nein | `TRUE` | **NEU:** Darf User diesen Fakt editieren/löschen? |
| `is_core_fact` | `BOOLEAN` | Nein | `FALSE` | **DEPRECATED:** Nur für Migration |
| `core_priority` | `INTEGER` | Nein | `0` | **DEPRECATED:** Nur für Migration |
| `category` | `VARCHAR(50)` | Ja | `"Allgemein"` | Legacy Kategorie |
| `source_type` | `VARCHAR(20)` | Ja | `"text"` | "text", "vision", "document" |
| `source_metadata` | `JSON` | Ja | NULL | Freiform-Dict |
| `created_at` | `DATETIME` | Nein | `utcnow` | Erstellungszeit |
| `last_accessed_at` | `DATETIME` | Nein | `utcnow` | Letzter Zugriff |

### 3.2 Indices (Performance)

```sql
-- Für Priority-Guard Lookups
CREATE INDEX idx_priority_high ON memories(priority) WHERE priority >= 0.8;

-- Für Deduplizierung
CREATE UNIQUE INDEX idx_text_hash ON memories(text_hash);

-- Für Chat-spezifische Queries
CREATE INDEX idx_chat_priority ON memories(chat_id, priority DESC);

-- Für TTL/Expiration Cleanup-Jobs
CREATE INDEX idx_expires_at ON memories(expires_at) WHERE expires_at IS NOT NULL;

-- Für Source-Skill Filtering
CREATE INDEX idx_source_skill ON memories(source_skill) WHERE source_skill IS NOT NULL;
```

### 3.3 Alembic Migration (Full Script)

```python
# alembic/versions/2026_04_06_memory_v2_priority_system.py
"""
Memory System V2: Float Priority Migration

- Fügt priority, memory_type, ttl, tags, source_skill, user_editable hinzu
- Migriert legacy core_priority/is_core_fact Werte
- Erstellt neue Indices
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# Revision identifiers
revision = 'memory_v2_priority_system'
down_revision = '<previous_revision_id>'
branch_labels = None
depends_on = None


def upgrade():
    # ─────────────────────────────────────────────
    # 1. Neue Spalten hinzufügen
    # ─────────────────────────────────────────────
    
    op.add_column('memories', sa.Column('priority', sa.Float, nullable=False, server_default='0.5'))
    op.add_column('memories', sa.Column('memory_type', sa.String(20), nullable=False, server_default='GENERAL'))
    op.add_column('memories', sa.Column('ttl', sa.Integer, nullable=True))
    op.add_column('memories', sa.Column('tags', sa.JSON, nullable=True, server_default='[]'))
    op.add_column('memories', sa.Column('source_skill', sa.String(100), nullable=True))
    op.add_column('memories', sa.Column('user_editable', sa.Boolean, nullable=False, server_default='1'))
    op.add_column('memories', sa.Column('canonical_key', sa.String(255), nullable=True))
    
    # ─────────────────────────────────────────────
    # 2. Backfill: Priority aus core_priority ableiten
    # ─────────────────────────────────────────────
    
    op.execute(text("""
        UPDATE memories 
        SET priority = CASE 
            WHEN core_priority = 2 THEN 0.95   -- CORE_IDENTITY (Always)
            WHEN core_priority = 1 THEN 0.75   -- CORE_DETAIL (Queryable)
            WHEN is_core_fact = 1 THEN 0.70    -- Legacy Core (unspecified level)
            WHEN expires_at IS NOT NULL THEN 0.60  -- Ephemeral/Temporal
            ELSE 0.50                          -- Standard General
        END
    """))
    
    # ─────────────────────────────────────────────
    # 3. Backfill: memory_type ableiten
    # ─────────────────────────────────────────────
    
    op.execute(text("""
        UPDATE memories 
        SET memory_type = CASE 
            WHEN core_priority >= 1 THEN 'CORE'
            WHEN expires_at IS NOT NULL THEN 'TEMPORAL'
            ELSE 'GENERAL'
        END
    """))
    
    # ─────────────────────────────────────────────
    # 4. Backfill: canonical_key aus snippet JSON extrahieren (best effort)
    # ─────────────────────────────────────────────
    
    # SQLite-spezifisch: JSON extraction
    op.execute(text("""
        UPDATE memories 
        SET canonical_key = COALESCE(
            json_extract(snippet, '$.canonical_key'),
            json_extract(snippet, '$.key'),
            text_hash  -- Fallback auf bestehenden Hash
        )
        WHERE snippet IS NOT NULL AND snippet LIKE '%{%}%'
    """))
    
    # ─────────────────────────────────────────────
    # 5. Backfill: tags aus category ableiten
    # ─────────────────────────────────────────────
    
    # Mapping-Tabelle für Tag-Backfill
    category_tags = {
        'Physis': '["appearance", "identity"]',
        'Stil': '["fashion", "identity"]',
        'Haustier-Details': '["pet", "identity"]',
        'Beziehungen': '["contact", "social"]',
        'Termine': '["calendar", "temporal"]',
        'Gesundheit': '["health", "medical"]',
        'Beruf': '["professional", "career"]',
        'Vorlieben': '["preferences", "personal"]',
    }
    
    for cat, tags_json in category_tags.items():
        op.execute(text(f"""
            UPDATE memories 
            SET tags = '{tags_json}'
            WHERE category = '{cat}' AND (tags IS NULL OR tags = '[]')
        """))
    
    # ─────────────────────────────────────────────
    # 6. Indices erstellen
    # ─────────────────────────────────────────────
    
    op.create_index('idx_priority_high', 'memories', ['priority'], 
                    sqlite_where=text('priority >= 0.8'))
    op.create_index('idx_chat_priority', 'memories', ['chat_id', sa.text('priority DESC')])
    op.create_index('idx_expires_at', 'memories', ['expires_at'], 
                    sqlite_where=text('expires_at IS NOT NULL'))
    op.create_index('idx_source_skill', 'memories', ['source_skill'],
                    sqlite_where=text('source_skill IS NOT NULL'))
    
    # ─────────────────────────────────────────────
    # 7. Default source_skill setzen (Mark as migrated)
    # ─────────────────────────────────────────────
    
    op.execute(text("""
        UPDATE memories 
        SET source_skill = 'system.legacy_migration'
        WHERE source_skill IS NULL
    """))


def downgrade():
    # Reverse Migration (Notenswert: Nur für Emergency Rollback)
    op.drop_index('idx_source_skill')
    op.drop_index('idx_expires_at')
    op.drop_index('idx_chat_priority')
    op.drop_index('idx_priority_high')
    
    op.drop_column('memories', 'canonical_key')
    op.drop_column('memories', 'user_editable')
    op.drop_column('memories', 'source_skill')
    op.drop_column('memories', 'tags')
    op.drop_column('memories', 'ttl')
    op.drop_column('memories', 'memory_type')
    op.drop_column('memories', 'priority')
```

### 3.4 Migration Safety Checklist

- [ ] Backup der SQLite-DB vor Migration (`cp janus.db janus.db.pre_v2`)
- [ ] Migration im Staging mit echten Daten testen
- [ ] Verify: `SELECT COUNT(*) FROM memories` vor und nach Migration identisch
- [ ] Verify: `SELECT MIN(priority), MAX(priority) FROM memories` ergibt 0.5 bis 0.95
- [ ] Spot-Check: 10 zufällige Einträge manuell auf Korrektheit prüfen

---

## 4. Code-Schnittstellen (Interfaces)

### 4.1 MemoryRAMCache (Singleton, LRU-Bounded)

**File:** `backend/services/memory_cache.py`

> **Opus 2.1 Fix:** Unbounded Dict → LRU mit `MAX_ITEMS=500`. Bei Überlauf werden die Einträge mit der niedrigsten Priority evicted. OOM-Risiko eliminiert. Observability-Counters für Debugging integriert.

```python
"""
In-Process RAM Cache für High-Priority Memories.
Singleton-Pattern, LRU-bounded, thread-safe via GIL.
MAX_ITEMS = 500 → ~1MB worst-case RAM footprint.
"""

from typing import Dict, List, Optional
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
import threading
import time
import logging
from sqlalchemy.orm import Session

from backend.data import models

logger = logging.getLogger("janus_backend")


@dataclass(frozen=True)
class CachedMemory:
    """Immutable Cache-Eintrag."""
    id: int
    canonical_key: str
    priority: float
    memory_type: str
    tags: tuple  # Frozen set as tuple
    snippet: str
    text_hash: str


@dataclass
class CacheMetrics:
    """Observability Counters (Opus V2.1)."""
    hits: int = 0
    misses: int = 0
    refreshes: int = 0
    evictions: int = 0
    invalidations: int = 0
    
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class MemoryRAMCache:
    """
    Singleton RAM Cache für Memories mit priority >= PRIORITY_THRESHOLD.
    
    GOLD STANDARD (Opus V2.1):
    - MAX_ITEMS: Hard-Limit auf 500 Einträge (OOM-Schutz)
    - LRU-Eviction: Bei Überlauf werden niedrig-priorisierte Einträge entfernt
    - Observability: hits/misses/evictions/refreshes zählen
    
    Nutzung:
        cache = MemoryRAMCache()
        cache.refresh_if_stale(db)
        high_prio = cache.get_all()  # Aus RAM, keine DB-Query
    """
    
    _instance: Optional['MemoryRAMCache'] = None
    _lock: threading.Lock = threading.Lock()
    
    # Konfiguration
    PRIORITY_THRESHOLD: float = 0.8
    REFRESH_INTERVAL_SECONDS: int = 300  # 5 Minuten
    MAX_ITEMS: int = 500  # OOM-Guard: Max Einträge im Cache
    
    def __new__(cls) -> 'MemoryRAMCache':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._cache: OrderedDict[int, CachedMemory] = OrderedDict()
        self._last_refresh: float = 0.0
        self._metrics: CacheMetrics = CacheMetrics()
        self._initialized = True
    
    def refresh(self, db: Session) -> None:
        """
        Lädt Memories mit priority >= threshold aus DB in RAM.
        Sortiert nach Priority desc, capped auf MAX_ITEMS.
        Thread-safe, atomarer Swap.
        """
        rows = (
            db.query(models.Memory)
            .filter(models.Memory.priority >= self.PRIORITY_THRESHOLD)
            .order_by(models.Memory.priority.desc())
            .limit(self.MAX_ITEMS)
            .all()
        )
        
        new_cache: OrderedDict[int, CachedMemory] = OrderedDict()
        for mem in rows:
            cached = CachedMemory(
                id=mem.id,
                canonical_key=mem.canonical_key or mem.text_hash or "",
                priority=mem.priority,
                memory_type=mem.memory_type or "GENERAL",
                tags=tuple(mem.tags or []),
                snippet=mem.snippet or "",
                text_hash=mem.text_hash or ""
            )
            new_cache[mem.id] = cached
        
        evicted = max(0, len(self._cache) - len(new_cache))
        
        # Atomarer Swap (GIL-geschützt)
        self._cache = new_cache
        self._last_refresh = time.time()
        self._metrics.refreshes += 1
        self._metrics.evictions += evicted
        
        logger.info(
            f"[CACHE REFRESH] {len(new_cache)} items loaded "
            f"(threshold={self.PRIORITY_THRESHOLD}, max={self.MAX_ITEMS})"
        )
    
    def refresh_if_stale(self, db: Session) -> None:
        """Refresh nur wenn REFRESH_INTERVAL überschritten."""
        if time.time() - self._last_refresh > self.REFRESH_INTERVAL_SECONDS:
            self.refresh(db)
    
    def get(self, memory_id: int) -> Optional[CachedMemory]:
        """Einzelnen Cache-Eintrag abrufen. Zählt hit/miss."""
        entry = self._cache.get(memory_id)
        if entry is not None:
            self._metrics.hits += 1
            # LRU: Move to end (most recently used)
            self._cache.move_to_end(memory_id)
        else:
            self._metrics.misses += 1
        return entry
    
    def get_all(self) -> List[CachedMemory]:
        """Alle gecachten High-Priority Memories."""
        return list(self._cache.values())
    
    def get_by_tag(self, tag: str) -> List[CachedMemory]:
        """Filtere Cache nach Tag."""
        return [m for m in self._cache.values() if tag in m.tags]
    
    def put(self, mem: CachedMemory) -> None:
        """
        Fügt einen Eintrag hinzu. Bei Überlauf wird der 
        niedrigst-priorisierte Eintrag evicted.
        """
        if mem.id in self._cache:
            # Update: Entferne alten, füge neuen hinzu
            del self._cache[mem.id]
        
        self._cache[mem.id] = mem
        
        # LRU-Eviction bei Überlauf
        while len(self._cache) > self.MAX_ITEMS:
            # Evict: Finde Eintrag mit niedrigster Priority
            min_id = min(self._cache, key=lambda k: self._cache[k].priority)
            evicted = self._cache.pop(min_id)
            self._metrics.evictions += 1
            logger.debug(f"[CACHE EVICT] ID={min_id}, priority={evicted.priority}")
    
    def invalidate(self, memory_id: int) -> None:
        """Einzelnen Eintrag invalidieren (z.B. nach Update/Delete)."""
        if memory_id in self._cache:
            del self._cache[memory_id]
            self._metrics.invalidations += 1
    
    def invalidate_all(self) -> None:
        """Cache komplett leeren."""
        count = len(self._cache)
        self._cache.clear()
        self._last_refresh = 0
        self._metrics.invalidations += count
    
    def get_stats(self) -> dict:
        """Diagnose-Info für /api/debug/memory-cache Endpoint."""
        return {
            "cached_count": len(self._cache),
            "max_items": self.MAX_ITEMS,
            "utilization": f"{len(self._cache) / self.MAX_ITEMS * 100:.1f}%",
            "last_refresh": (
                datetime.fromtimestamp(self._last_refresh).isoformat() 
                if self._last_refresh else None
            ),
            "threshold": self.PRIORITY_THRESHOLD,
            "avg_priority": (
                sum(m.priority for m in self._cache.values()) / len(self._cache) 
                if self._cache else 0
            ),
            "metrics": {
                "hits": self._metrics.hits,
                "misses": self._metrics.misses,
                "hit_rate": f"{self._metrics.hit_rate() * 100:.1f}%",
                "refreshes": self._metrics.refreshes,
                "evictions": self._metrics.evictions,
                "invalidations": self._metrics.invalidations,
            }
        }


# Convenience-Export
memory_cache = MemoryRAMCache()
```

### 4.2 Memory Enricher (Post-Processor)

**File:** `backend/services/memory_enricher.py`

```python
"""
Deterministischer Post-Processor für Memory Metadaten.
Wendet Regeln an, um priority, ttl, tags, memory_type zu setzen.
"""

from typing import Dict, List, Callable, Optional, Any
from datetime import timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger("janus_backend")


# ═══════════════════════════════════════════════════════════════════════════
# REGEL-DEFINITIONEN (Diese Regeln sind das Herzstück des Systems)
# ═══════════════════════════════════════════════════════════════════════════

PriorityRule = Callable[[Dict[str, Any]], bool]

@dataclass
class PriorityRuleEntry:
    condition: PriorityRule
    priority: float
    description: str

# Höchste Priorität zuerst (erste Match gewinnt)
PRIORITY_RULES: List[PriorityRuleEntry] = [
    # CORE_IDENTITY: Physische Identitätsmerkmale (Name, Aussehen)
    PriorityRuleEntry(
        lambda f: f.get("category") == "Physis" and 
                  f.get("predicate") in ["name_is", "heisst", "ist"],
        0.95,
        "Core Identity: Name oder fundamentale Identität"
    ),
    # CORE_PHYSICAL: Physische Merkmale (Haare, Augen, Teint)
    PriorityRuleEntry(
        lambda f: f.get("category") == "Physis" and 
                  f.get("predicate") in ["hat_frisur", "hat_augenfarbe", "hat_teint", "hat"],
        0.90,
        "Core Physical: Wiedererkennbare physische Merkmale"
    ),
    # CORE_RELATIONSHIP: Nahe Bezugspersonen
    PriorityRuleEntry(
        lambda f: f.get("category") == "Beziehungen" and 
                  f.get("predicate") in ["name_is", "heisst", "ist", "hat_beziehung"],
        0.85,
        "Core Relationship: Nahestehende Personen"
    ),
    # PET_IDENTITY: Haustier-Identität (für viele User sehr wichtig)
    PriorityRuleEntry(
        lambda f: f.get("category") == "Haustier-Details" and 
                  f.get("predicate") in ["name_is", "heisst", "ist"],
        0.88,
        "Pet Identity: Haustier-Namen und Rassen"
    ),
    # STYLE_IDENTITY: Wiederkehrende Style-Elemente
    PriorityRuleEntry(
        lambda f: f.get("category") == "Stil" and 
                  "traegt" in f.get("predicate", ""),
        0.75,
        "Style Identity: Accessoires/Schmuck (wiedererkennbar)"
    ),
    # HEALTH_FACTS: Gesundheitsinfos (hoch sensitiv, aber nicht immer relevant)
    PriorityRuleEntry(
        lambda f: f.get("category") == "Gesundheit",
        0.70,
        "Health: Medizinische Informationen"
    ),
    # TEMPORAL: Termine und Zeitpunkte
    PriorityRuleEntry(
        lambda f: f.get("category") == "Termine",
        0.60,
        "Temporal: Termine mit Ablaufdatum"
    ),
    # PREFERENCES: Vorlieben (Abneigungen)
    PriorityRuleEntry(
        lambda f: f.get("category") == "Vorlieben",
        0.55,
        "Preferences: Mag/Mag nicht"
    ),
    # DEFAULT
    PriorityRuleEntry(
        lambda f: True,
        0.50,
        "Default: Standard-Priorität"
    ),
]

# TTL-Regeln (in Sekunden)
TTL_RULES = {
    "Termine": timedelta(days=30).total_seconds(),
    "Allgemein": None,  # Permanent
    "Physis": None,     # Permanent
    "Beziehungen": None,
    "Stil": None,
    "Haustier-Details": None,
    "Gesundheit": None,
    "Beruf": None,
    "Vorlieben": timedelta(days=365).total_seconds(),  # 1 Jahr
}

# Tag-Mappings
TAG_RULES = {
    "Physis": ["appearance", "identity"],
    "Stil": ["fashion", "identity"],
    "Haustier-Details": ["pet", "identity"],
    "Beziehungen": ["contact", "social"],
    "Termine": ["calendar", "temporal"],
    "Gesundheit": ["health", "medical"],
    "Beruf": ["career", "professional"],
    "Vorlieben": ["preference", "personal"],
    "Allgemein": ["general"],
}

# Priority Caps pro Quelle (GUARD)
PRIORITY_CAPS: Dict[str, float] = {
    "system": 1.0,              # Internes System (unbeschränkt)
    "system.legacy_migration": 0.95,
    "system.extractor": 0.95,
    "system.memory_write": 0.95,
    "skill.save_core_memory": 0.90,
    "skill.save_fact": 0.85,
    "skill.external": 0.70,     # Generisches externes Skill-Cap
    "skill.websearch": 0.60,    # Websuche-Ergebnisse: weniger wichtig
    "user.explicit": 0.95,      # User sagt "Das ist wichtig"
    "user.implicit": 0.75,      # User erwähnt nebenbei
}


# ═══════════════════════════════════════════════════════════════════════════
# HAUPT-FUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════

def calculate_priority(fact: Dict[str, Any]) -> float:
    """
    Berechnet Priority basierend auf Regeln.
    Erste passende Regel gewinnt.
    """
    for rule in PRIORITY_RULES:
        if rule.condition(fact):
            logger.debug(f"Priority Rule matched: {rule.description} -> {rule.priority}")
            return rule.priority
    return 0.50  # Fallback (sollte nie erreicht werden wegen Default-Rule)


def calculate_ttl(category: str) -> Optional[float]:
    """TTL in Sekunden oder None für permanent."""
    return TTL_RULES.get(category)


def calculate_tags(fact: Dict[str, Any]) -> List[str]:
    """Tags aus Kategorie + dynamischen Regeln."""
    category = fact.get("category", "Allgemein")
    tags = list(TAG_RULES.get(category, ["general"]))
    
    # Dynamische Tag-Erweiterung
    if fact.get("source_type") == "vision":
        tags.append("visual")
    
    if fact.get("predicate", "").startswith("traegt"):
        tags.append("wearing")
    
    if "name" in fact.get("predicate", ""):
        tags.append("naming")
    
    # Deduplizieren
    return list(set(tags))


def determine_memory_type(priority: float, ttl: Optional[float]) -> str:
    """
    Bestimmt memory_type aus Priority und TTL.
    """
    if priority >= 0.85:
        return "CORE"
    elif ttl is not None:
        return "TEMPORAL"
    else:
        return "GENERAL"


def apply_priority_guard(raw_priority: float, source_skill: str) -> float:
    """
    Hard-Cap auf Priority basierend auf Quelle.
    Loggt Warnung wenn Clamping stattfand.
    """
    cap = PRIORITY_CAPS.get(source_skill, 0.60)  # Default 0.6 für unbekannte Quellen
    clamped = min(raw_priority, cap)
    
    if clamped < raw_priority:
        logger.warning(
            f"Priority Guard activated: {source_skill} requested {raw_priority}, "
            f"clamped to {clamped} (cap: {cap})"
        )
    
    return clamped


def enrich_fact(
    fact: Dict[str, Any],
    source_skill: str = "system.extractor",
    user_requested: bool = False
) -> Dict[str, Any]:
    """
    Haupt-Funktion: Reichert einen rohen Fakt mit Metadaten an.
    
    Args:
        fact: Roher Fakt von LLM (mit fact, category, canonical_key, etc.)
        source_skill: ID des Skills, der den Fakt erzeugt hat
        user_requested: True wenn User explizit "Merke dir das" gesagt hat
    
    Returns:
        Angereicherter Fakt mit priority, ttl, tags, memory_type
    """
    # 1. Priority berechnen
    calculated_priority = calculate_priority(fact)
    
    # 2. User-Override (wenn User explizit sagt es ist wichtig)
    if user_requested:
        calculated_priority = max(calculated_priority, 0.90)
        source_skill = "user.explicit"
    
    # 3. Priority Guard anwenden
    final_priority = apply_priority_guard(calculated_priority, source_skill)
    
    # 4. TTL berechnen
    category = fact.get("category", "Allgemein")
    ttl_seconds = calculate_ttl(category)
    
    # Override: Core Memories haben kein TTL
    if final_priority >= 0.85:
        ttl_seconds = None
    
    # 5. Tags berechnen
    tags = calculate_tags(fact)
    
    # 6. Memory Type bestimmen
    memory_type = determine_memory_type(final_priority, ttl_seconds)
    
    # 7. An Fakt anhängen
    fact["priority"] = final_priority
    fact["ttl"] = ttl_seconds
    fact["tags"] = tags
    fact["memory_type"] = memory_type
    fact["source_skill"] = source_skill
    fact["user_editable"] = True  # Default, kann später geändert werden
    
    return fact
```

### 4.3 MemorySlot & build_final_context (Budget Logic)

**File:** `backend/services/context_manager.py` (Erweiterung)

```python
"""
Erweiterte Context Manager Logik mit MemorySlot-basiertem Budget-Management.
Ersetzt die alte String-Truncation Methode.
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
import tiktoken
import logging

logger = logging.getLogger("janus_backend")


@dataclass
class MemorySlot:
    """
    Repräsentiert einen einzelnen Memory-Eintrag im Kontext.
    
    Attributes:
        text: Der formatierte Text des Fakts
        tokens: Pre-calculated Token-Count
        tier: Hierarchische Ebene (für Debug/Logging)
        priority: Float 0.0-1.0 (Sortierkriterium)
        memory_id: DB-ID (für Touch-Tracking)
        tags: Tags für Filterung
    """
    text: str
    tokens: int
    tier: Literal["core_always", "core_query", "ephemeral", "stm"]
    priority: float
    memory_id: int
    tags: List[str]
    
    def __post_init__(self):
        # Validation
        if self.tokens <= 0:
            self.tokens = 1  # Mindestens 1 Token


class TokenBudget:
    """
    Verwaltet das Token-Budget für den Context.
    """
    
    def __init__(
        self,
        max_tokens: int,
        system_ratio: float = 0.10,
        memory_ratio: float = 0.30,
        history_ratio: float = 0.50,
        response_buffer: int = 1000
    ):
        self.available = max_tokens - response_buffer
        self.system_budget = int(self.available * system_ratio)
        self.memory_budget = int(self.available * memory_ratio)
        self.history_budget = int(self.available * history_ratio)
        
        # Tracking
        self.used_system = 0
        self.used_memory = 0
        self.used_history = 0
    
    @property
    def remaining_memory(self) -> int:
        return self.memory_budget - self.used_memory
    
    def can_fit(self, tokens: int) -> bool:
        return self.remaining_memory >= tokens
    
    def allocate(self, tokens: int) -> bool:
        """Versucht Tokens zu allocieren. Returns True wenn erfolgreich."""
        if self.can_fit(tokens):
            self.used_memory += tokens
            return True
        return False


def count_tokens(text: str, model: str = "gpt-5.4-nano") -> int:
    """
    Tiktoken-basierte Token-Zählung mit Caching.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")  # Fallback
    
    return len(encoding.encode(text))


def create_memory_slots(
    memories: List[Dict],
    tier: Literal["core_always", "core_query", "ephemeral", "stm"]
) -> List[MemorySlot]:
    """
    Wandelt Memory-Dicts in MemorySlots um.
    """
    slots = []
    
    for mem in memories:
        # Text aus Snippet extrahieren
        snippet = mem.get("snippet", "")
        if snippet.startswith("{"):
            # JSON-Parsing für strukturierte Fakten
            try:
                import json
                data = json.loads(snippet)
                text = data.get("fact", snippet)
            except:
                text = snippet
        else:
            text = snippet
        
        # Formatierung für Context
        formatted = f"- {text}"
        tokens = count_tokens(formatted)
        
        slot = MemorySlot(
            text=formatted,
            tokens=tokens,
            tier=tier,
            priority=mem.get("priority", 0.5),
            memory_id=mem.get("id", 0),
            tags=mem.get("tags", [])
        )
        slots.append(slot)
    
    return slots


def select_slots_by_budget(
    slots: List[MemorySlot],
    budget: TokenBudget
) -> List[MemorySlot]:
    """
    Wählt Slots nach Priority aus bis Budget ausgeschöpft.
    
    GOLD STANDARD (Opus V2.1):
    Knapsack-Algorithmus statt Greedy-Break.
    Wenn ein großer Slot nicht passt, wird geprüft ob der nächste
    (kleinere) Slot noch reinpasst → continue statt break.
    Nur wenn remaining_budget < 1 Token → break.
    
    Algorithmus:
    1. Sortiere nach Priority (desc), dann Tier
    2. Iteriere: Passt Slot? → allocate. Passt nicht? → skip, try next.
    3. Break nur wenn kein Budget mehr für irgendeinen Slot übrig ist.
    """
    # Sortierung: Priority desc, dann tier (core_always zuerst)
    tier_order = {"core_always": 0, "core_query": 1, "ephemeral": 2, "stm": 3}
    
    sorted_slots = sorted(
        slots,
        key=lambda s: (-s.priority, tier_order.get(s.tier, 99))
    )
    
    selected: List[MemorySlot] = []
    skipped: List[MemorySlot] = []
    
    # Minimum Slot-Größe für Early-Termination
    min_slot_tokens = min((s.tokens for s in sorted_slots), default=1)
    
    for slot in sorted_slots:
        if budget.remaining_memory < min_slot_tokens:
            # Kein Platz mehr für irgendeinen Slot → echtes Break
            skipped.extend(sorted_slots[sorted_slots.index(slot):])
            break
        
        if budget.allocate(slot.tokens):
            selected.append(slot)
        else:
            # Dieser Slot passt nicht, aber ein kleinerer vielleicht schon → continue
            skipped.append(slot)
            logger.debug(
                f"[KNAPSACK] Skipping {slot.tier} slot (p={slot.priority}, "
                f"tk={slot.tokens}), remaining={budget.remaining_memory}tk"
            )
            continue
    
    if skipped:
        logger.info(
            f"[BUDGET] Selected {len(selected)}/{len(sorted_slots)} slots, "
            f"skipped {len(skipped)} (budget: {budget.used_memory}/{budget.memory_budget}tk)"
        )
    
    return selected


def format_memory_context(slots: List[MemorySlot]) -> str:
    """
    Formatiert Slots zu einem String mit Sektionen.
    """
    if not slots:
        return ""
    
    # Gruppieren nach Tier für bessere Lesbarkeit
    tiers = {}
    for slot in slots:
        tiers.setdefault(slot.tier, []).append(slot)
    
    sections = []
    
    tier_labels = {
        "core_always": "### CORE IDENTITY (ALWAYS ACTIVE)",
        "core_query": "### RELEVANT USER TRAITS",
        "ephemeral": "### ACTIVE FACTS & PLANS",
        "stm": "### CONVERSATION MEMORY"
    }
    
    for tier in ["core_always", "core_query", "ephemeral", "stm"]:
        if tier in tiers:
            label = tier_labels.get(tier, f"### {tier.upper()}")
            lines = [slot.text for slot in tiers[tier]]
            sections.append(f"{label}\n" + "\n".join(lines))
    
    return "INFORMATIONEN AUS DEM LANGZEITGEDÄCHTNIS:\n\n" + "\n\n".join(sections)


# ═══════════════════════════════════════════════════════════════════════════
# ERWEITERTER build_final_context (Ersatz für alte Methode)
# ═══════════════════════════════════════════════════════════════════════════

async def build_final_context_v2(
    self,
    user_prompt: str,
    chat_history: List[Dict],
    memory_slots: List[MemorySlot],  # NEU: Statt memory_context string
    model_id: str,
    api_key: str,
    budget_config: Dict,
    provider: str,
) -> List[Dict]:
    """
    Budget-aware Context Building mit MemorySlots.
    
    Ersetzt die alte String-Truncation Methode.
    """
    max_tokens = self.model_limits.get(model_id, 8000)
    
    # Budget initialisieren
    budget = TokenBudget(
        max_tokens=max_tokens,
        system_ratio=budget_config.get("system_prompt_ratio", 0.10),
        memory_ratio=budget_config.get("memory_ratio", 0.30),
        history_ratio=budget_config.get("history_ratio", 0.50),
        response_buffer=RESPONSE_BUFFER
    )
    
    final_history = []
    
    # 1. System Prompt (immer dabei, aber prüfen ob Budget passt)
    system_tokens = count_tokens(self.system_prompt_text, model_id)
    if system_tokens > budget.system_budget:
        logger.warning(f"System prompt ({system_tokens}tk) exceeds budget ({budget.system_budget}tk)")
        # Notfall: System prompt wird gekürzt (selten)
        system_text = self.system_prompt_text[:budget.system_budget * 4]
    else:
        system_text = self.system_prompt_text
    
    final_history.append({"role": "system", "content": system_text})
    budget.used_system = count_tokens(system_text, model_id)
    
    # 2. Memory Context mit Budget-Aware Selection
    selected_slots = select_slots_by_budget(memory_slots, budget)
    
    if selected_slots:
        memory_context = format_memory_context(selected_slots)
        final_history.append({
            "role": "system",
            "content": f"--- RELEVANTE ERINNERUNGEN ---\n{memory_context}\n"
        })
        budget.used_memory = sum(s.tokens for s in selected_slots)
        
        # Touch: Update last_accessed_at für ausgewählte Memories
        # (Async Fire-and-Forget)
        for slot in selected_slots:
            # Trigger touch in background
            pass
    
    # 3. Chat History mit verbleibendem Budget
    remaining_for_history = budget.history_budget - budget.used_history
    
    # Alte Nachrichten zuerst (für Rolling Window)
    truncated_history = []
    user_prompt_tokens = count_tokens(user_prompt, model_id)
    
    for message in reversed(chat_history):
        msg_tokens = count_tokens(message.get("content", ""), model_id)
        
        # Prüfe ob wir noch Platz haben
        current_total = (
            budget.used_system + 
            budget.used_memory + 
            sum(count_tokens(m.get("content", ""), model_id) for m in truncated_history) +
            msg_tokens +
            user_prompt_tokens
        )
        
        if current_total > max_tokens - RESPONSE_BUFFER:
            break
        
        truncated_history.insert(0, message)
    
    if truncated_history:
        final_history.extend(truncated_history)
    
    # 4. User Prompt (immer dabei)
    final_history.append({"role": "user", "content": user_prompt})
    
    # Log Summary
    total_tokens = sum(count_tokens(m.get("content", ""), model_id) for m in final_history)
    logger.info(
        f"Context built: {len(selected_slots)}/{len(memory_slots)} slots selected, "
        f"{len(truncated_history)}/{len(chat_history)} history messages, "
        f"total tokens: {total_tokens}/{max_tokens}"
    )
    
    return final_history
```

### 4.4 Opus-Optimierungen (Gold Standard Additions)

Die folgenden Komponenten wurden vom Lead Architect (Opus 4.6) als notwendig für Production-Grade identifiziert. Sie waren im Kimi-Entwurf nicht enthalten.

#### 4.4.1 Dedup Merge Strategy (Implementierung)

**File:** `backend/services/memory_manager.py` (Erweiterung von `save_memory_snippet`)

> **Problem:** Kimi-Entwurf sagt "Merge Tags, Update last_accessed_at" — aber was passiert mit Priority, Snippet, Source? Undefiniert → Race Condition bei concurrent Skills.

```python
def _merge_existing_memory(
    db: Session,
    existing: models.Memory,
    new_fact: Dict[str, Any],
    new_source_skill: str
) -> None:
    """
    Deterministische Merge-Strategie bei Dedup-Hit (gleicher canonical_key).
    
    REGELN (Opus V2.1):
    1. Priority: MAX(existing, new) — höchste gewinnt
    2. Tags: UNION — additiv, keine Löschung
    3. source_skill: Behalte Original, logge Collision
    4. snippet: Überschreibe NUR wenn new.priority > existing.priority
    5. last_accessed_at: NOW()
    """
    old_priority = existing.priority or 0.5
    new_priority = new_fact.get("priority", 0.5)
    
    # 1. Priority: Higher wins
    if new_priority > old_priority:
        existing.priority = new_priority
        # 4. Snippet: Nur bei Priority-Upgrade überschreiben
        if new_fact.get("fact"):
            import json
            existing.snippet = json.dumps(new_fact, ensure_ascii=False)
        logger.info(
            f"[DEDUP MERGE] Priority upgraded: {old_priority} -> {new_priority} "
            f"(key={existing.canonical_key})"
        )
    
    # 2. Tags: Union
    existing_tags = set(existing.tags or [])
    new_tags = set(new_fact.get("tags", []))
    merged_tags = list(existing_tags | new_tags)
    if merged_tags != list(existing_tags):
        existing.tags = merged_tags
    
    # 3. Source Skill: Log collision, keep original
    if new_source_skill and new_source_skill != existing.source_skill:
        logger.info(
            f"[DEDUP COLLISION] Key={existing.canonical_key}: "
            f"original_skill={existing.source_skill}, "
            f"competing_skill={new_source_skill} (kept original)"
        )
    
    # 5. Touch
    existing.last_accessed_at = datetime.utcnow()
    
    db.commit()
```

#### 4.4.2 Embedding Parse Cache

**File:** `backend/services/memory_manager.py` (Performance-Fix)

> **Problem:** `retrieve_diamond_context()` (aktuell Zeile 610) ruft für JEDEN Memory-Kandidaten `json.loads(m.embedding_json)` auf. Bei 300 STM-Kandidaten sind das 300 JSON-Parses pro Request.

```python
# backend/services/embedding_cache.py
"""
LRU-Cache für deserialisierte Embeddings.
Eliminiert redundante json.loads() Aufrufe im Retrieval-Path.
"""

from functools import lru_cache
from typing import Optional, List
import json


@lru_cache(maxsize=2048)
def parse_embedding(raw: bytes) -> Optional[List[float]]:
    """
    Cached JSON-Parse von Embedding-Bytes.
    
    Da embedding_json als LargeBinary gespeichert wird,
    ist der Input bytes. lru_cache benötigt hashbare Inputs,
    bytes ist hashbar.
    
    Benchmark: Reduziert 300 json.loads() auf ~30 Cache-Misses
    beim Erst-Aufruf, danach 0 Parses.
    """
    if raw is None:
        return None
    try:
        if isinstance(raw, bytes):
            return json.loads(raw.decode("utf-8"))
        return json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def clear_embedding_cache() -> None:
    """Cache leeren (z.B. nach Bulk-Update von Embeddings)."""
    parse_embedding.cache_clear()


def embedding_cache_stats() -> dict:
    """Diagnose."""
    info = parse_embedding.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "maxsize": info.maxsize,
        "currsize": info.currsize,
        "hit_rate": f"{info.hits / (info.hits + info.misses) * 100:.1f}%" if (info.hits + info.misses) > 0 else "0%"
    }
```

**Integration:** In `retrieve_diamond_slots()` ersetze alle `json.loads(m.embedding_json)` durch `parse_embedding(m.embedding_json)`.

#### 4.4.3 Extraction Circuit-Breaker

**File:** `backend/services/memory_extractor.py` (Erweiterung)

> **Problem:** Wenn der LLM-Provider down ist, versucht `extract_and_save_fact_from_interaction` bei JEDER Nachricht einen API-Call + Self-Healing Retry = 2 verbrannte Calls pro User-Nachricht. Bei 10 Nachrichten in 1 Minute = 20 fehlgeschlagene API-Calls (Kosten + Latenz).

```python
# Am Anfang von memory_extractor.py hinzufügen:

import time

class ExtractionCircuitBreaker:
    """
    Circuit-Breaker Pattern für LLM Extraction Calls.
    
    States:
    - CLOSED: Normal, alle Calls gehen durch
    - OPEN: Gesperrt, alle Calls werden sofort geskippt
    - HALF_OPEN: Ein Probe-Call wird durchgelassen
    
    Trigger: 3 aufeinanderfolgende Fehler → OPEN für 120 Sekunden
    Reset: Nach 120s → HALF_OPEN, nächster Call entscheidet
    """
    
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 120  # Sekunden
    ):
        self._failure_count: int = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time: float = 0
        self._state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Prüfe ob ein Call erlaubt ist."""
        if self._state == "CLOSED":
            return True
        
        if self._state == "OPEN":
            # Prüfe ob Recovery-Timeout abgelaufen
            if time.time() - self._last_failure_time > self._recovery_timeout:
                self._state = "HALF_OPEN"
                logger.info("[CIRCUIT BREAKER] State: OPEN → HALF_OPEN (probe allowed)")
                return True
            return False
        
        if self._state == "HALF_OPEN":
            return True  # Ein Probe-Call erlaubt
        
        return False
    
    def record_success(self) -> None:
        """Call war erfolgreich → Reset."""
        if self._state == "HALF_OPEN":
            logger.info("[CIRCUIT BREAKER] State: HALF_OPEN → CLOSED (recovered)")
        self._failure_count = 0
        self._state = "CLOSED"
    
    def record_failure(self) -> None:
        """Call ist fehlgeschlagen."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self._failure_threshold:
            self._state = "OPEN"
            logger.warning(
                f"[CIRCUIT BREAKER] State: → OPEN "
                f"({self._failure_count} consecutive failures, "
                f"locked for {self._recovery_timeout}s)"
            )
    
    def get_state(self) -> dict:
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "threshold": self._failure_threshold,
            "recovery_timeout": self._recovery_timeout,
        }


# Singleton
_extraction_breaker = ExtractionCircuitBreaker()
```

**Integration in `extract_and_save_fact_from_interaction()`:**

```python
async def extract_and_save_fact_from_interaction(...):
    # CIRCUIT BREAKER CHECK (Opus V2.1)
    if not _extraction_breaker.can_execute():
        logger.info("[EXTRACTION] Circuit breaker OPEN — skipping extraction")
        return []
    
    try:
        # ... bestehende Logik ...
        extracted_items = await _generate_fact_extraction_items_with_self_healing(...)
        
        _extraction_breaker.record_success()  # ← NEU
        # ... rest of processing ...
        
    except Exception as e:
        _extraction_breaker.record_failure()  # ← NEU
        logger.error(f"Extraction failed: {e}", exc_info=True)
        return []
```

#### 4.4.4 Memory System Observability

**File:** `backend/services/memory_observability.py`

> **Rationale:** Ohne Counters ist Debugging in Production ein Blindflug. Jede Komponente zählt ihre Operationen. Ein `/api/debug/memory` Endpoint gibt alles auf einen Blick.

```python
"""
Zentrale Observability für das Memory System.
Sammelt Counters von Cache, Enricher, Guard, Dedup, Cleanup.
"""

from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class MemorySystemMetrics:
    """Aggregierte Metriken für das gesamte Memory System."""
    
    # Write Path
    writes_total: int = 0
    writes_enriched: int = 0
    writes_guarded: int = 0       # Priority Guard hat geclampt
    writes_deduplicated: int = 0  # Dedup-Hit (Merge statt Insert)
    writes_rejected: int = 0     # Vom Guard oder Sanitizer abgelehnt
    
    # Read Path
    reads_total: int = 0
    reads_cache_hit: int = 0
    reads_cache_miss: int = 0
    reads_vector_scan: int = 0
    
    # Extraction
    extractions_total: int = 0
    extractions_success: int = 0
    extractions_failed: int = 0
    extractions_circuit_broken: int = 0
    
    # Cleanup
    zombies_purged: int = 0
    memories_archived: int = 0
    
    # Context Build
    context_builds: int = 0
    slots_selected_total: int = 0
    slots_dropped_total: int = 0
    
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def increment(self, counter_name: str, amount: int = 1) -> None:
        """Thread-safe Counter Increment."""
        with self._lock:
            current = getattr(self, counter_name, 0)
            setattr(self, counter_name, current + amount)
    
    def snapshot(self) -> dict:
        """Snapshot aller Metriken für API-Response."""
        return {
            "write_path": {
                "total": self.writes_total,
                "enriched": self.writes_enriched,
                "guarded": self.writes_guarded,
                "deduplicated": self.writes_deduplicated,
                "rejected": self.writes_rejected,
            },
            "read_path": {
                "total": self.reads_total,
                "cache_hit": self.reads_cache_hit,
                "cache_miss": self.reads_cache_miss,
                "vector_scans": self.reads_vector_scan,
            },
            "extraction": {
                "total": self.extractions_total,
                "success": self.extractions_success,
                "failed": self.extractions_failed,
                "circuit_broken": self.extractions_circuit_broken,
            },
            "cleanup": {
                "zombies_purged": self.zombies_purged,
                "archived": self.memories_archived,
            },
            "context": {
                "builds": self.context_builds,
                "slots_selected": self.slots_selected_total,
                "slots_dropped": self.slots_dropped_total,
            },
            "uptime_since": self._started_at,
        }


# Singleton
memory_metrics = MemorySystemMetrics()
```

**FastAPI Debug-Endpoint:**

```python
# backend/main.py — Debug-Router
@app.get("/api/debug/memory")
async def debug_memory_system():
    """Dashboard für Memory System Gesundheit."""
    from backend.services.memory_cache import memory_cache
    from backend.services.memory_observability import memory_metrics
    from backend.services.embedding_cache import embedding_cache_stats
    from backend.services.memory_extractor import _extraction_breaker
    
    return {
        "cache": memory_cache.get_stats(),
        "metrics": memory_metrics.snapshot(),
        "embedding_cache": embedding_cache_stats(),
        "circuit_breaker": _extraction_breaker.get_state(),
    }
```

---

## 5. Tool-Definitionen (Unified Memory Tools)

### 5.1 Tool: `memory_write`

**File:** `backend/skills/system/memory_write.json`

```json
{
  "id": "memory_write",
  "name": "Speichere Erinnerung",
  "description": "Speichert einen Fakt oder eine Information im Langzeitgedächtnis. Wird automatisch aufgerufen wenn der User etwas Wichtiges erwähnt.",
  "version": "2.0.0",
  "category": "memory",
  "risk_level": "low",
  "parameters": {
    "type": "object",
    "required": ["fact"],
    "properties": {
      "fact": {
        "type": "string",
        "description": "Der zu speichernde Fakt in natürlicher Sprache (Deutsch). Beispiel: 'Max hat braune Haare'"
      },
      "subject_name": {
        "type": "string",
        "description": "Name des Subjekts (Person, Tier, Objekt). Kleinbuchstaben."
      },
      "category": {
        "type": "string",
        "enum": ["Gesundheit", "Beziehungen", "Haustier-Details", "Vorlieben", "Beruf", "Termine", "Allgemein", "Physis", "Stil"],
        "description": "Kategorie des Fakts"
      },
      "priority_override": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 0.95,
        "description": "OPTIONAL: Manuelle Priority (0.0-0.95). Ohne Angabe wird automatisch berechnet. Max 0.95 auch für explizite Anfragen."
      },
      "ttl_days": {
        "type": "integer",
        "minimum": 1,
        "maximum": 365,
        "description": "OPTIONAL: Anzahl Tage bis zum Ablauf. Ohne Angabe wird aus Kategorie abgeleitet."
      },
      "tags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "OPTIONAL: Zusätzliche Tags für Filterung."
      },
      "evidence": {
        "type": "string",
        "description": "OPTIONAL: Zitat aus der User-Nachricht als Beleg."
      }
    }
  },
  "synthesis_directives": "SPEICHER-BESTÄTIGUNG: Wenn dieser Skill erfolgreich war, erwähne die Speicherung NICHT explizit außer der User fragt danach. Integriere das Wissen natürlich in zukünftige Antworten."
}
```

### 5.2 Tool: `memory_read`

**File:** `backend/skills/system/memory_read.json`

```json
{
  "id": "memory_read",
  "name": "Lese Erinnerung",
  "description": "Durchsucht das Gedächtnis nach relevanten Informationen zu einem Thema oder Namen.",
  "version": "2.0.0",
  "category": "memory",
  "risk_level": "low",
  "parameters": {
    "type": "object",
    "required": ["query"],
    "properties": {
      "query": {
        "type": "string",
        "description": "Suchbegriff oder Frage. Beispiele: 'Wie heißt der Hund?', 'Was weiß ich über Max?', 'Termine nächste Woche'"
      },
      "filter_tags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "OPTIONAL: Nur Memories mit diesen Tags berücksichtigen."
      },
      "min_priority": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "default": 0.0,
        "description": "OPTIONAL: Minimale Priority (0.0 = alle, 0.8 = nur wichtige)"
      },
      "include_expired": {
        "type": "boolean",
        "default": false,
        "description": "OPTIONAL: Auch abgelaufene Memories anzeigen (Grace Period)?"
      },
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 50,
        "default": 10,
        "description": "OPTIONAL: Maximale Anzahl Ergebnisse."
      }
    }
  },
  "response_schema": {
    "type": "object",
    "properties": {
      "memories": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "fact": {"type": "string"},
            "priority": {"type": "number"},
            "category": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "created_at": {"type": "string"},
            "expires_at": {"type": "string", "nullable": true}
          }
        }
      },
      "total_found": {"type": "integer"},
      "query": {"type": "string"}
    }
  }
}
```

### 5.3 Tool: `memory_update`

**File:** `backend/skills/system/memory_update.json`

```json
{
  "id": "memory_update",
  "name": "Aktualisiere Erinnerung",
  "description": "Aktualisiert oder korrigiert eine bestehende Erinnerung. Nur für user_editable=true Memories erlaubt.",
  "version": "2.0.0",
  "category": "memory",
  "risk_level": "medium",
  "parameters": {
    "type": "object",
    "required": ["memory_id", "new_fact"],
    "properties": {
      "memory_id": {
        "type": "integer",
        "description": "ID der zu aktualisierenden Memory (von memory_read)"
      },
      "new_fact": {
        "type": "string",
        "description": "Neuer/korrigierter Fakt-Text"
      },
      "new_priority": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "description": "OPTIONAL: Neue Priority. Wird ggf. durch Guard gekappt."
      }
    }
  },
  "error_cases": [
    "Memory nicht gefunden",
    "Memory ist nicht editierbar (user_editable=false)",
    "Permission denied (externe Skills dürfen nur eigene Memories editieren)"
  ]
}
```

### 5.4 Tool: `memory_history`

**File:** `backend/skills/system/memory_history.json`

```json
{
  "id": "memory_history",
  "name": "Zeige Memory-Verlauf",
  "description": "Zeigt alle Änderungen und Zugriffe auf eine bestimmte Erinnerung (Audit-Trail).",
  "version": "2.0.0",
  "category": "memory",
  "risk_level": "low",
  "parameters": {
    "type": "object",
    "required": ["memory_id"],
    "properties": {
      "memory_id": {
        "type": "integer",
        "description": "ID der Memory"
      }
    }
  }
}
```

---

## 6. Exakter Umsetzungsplan (Phasen)

### Phase 1: Foundation (DB & Models) — ETA 2-3h

**Ziel:** Schema-Änderungen und Migration laufen, bestehende Tests sind grün.

| # | Task | Datei(en) | Akzeptanzkriterium |
|---|------|-----------|-------------------|
| 1.1 | Alembic Migration erstellen | `alembic/versions/xxx_memory_v2.py` | `alembic upgrade head` läuft ohne Fehler |
| 1.2 | Pydantic Schema erweitern | `backend/data/schemas.py` | `ExtractedFact` hat neue optionale Felder (priority, ttl, tags, memory_type, source_skill, user_editable) |
| 1.3 | SQLAlchemy Model erweitern | `backend/data/models.py` | `Memory` Model hat alle neuen Spalten |
| 1.4 | Migration Test | SQLite Test-DB | 100 Test-Memories migriert, Werte korrekt (0.5-0.95 Range) |

**Blocking:** Keine andere Phase darf vor 1.4 beginnen.

---

### Phase 2: RAM Cache + TTL Cleanup — ETA 3h

**Ziel:** `MemoryRAMCache` Singleton mit LRU-Bound funktioniert, TTL-Zombies werden automatisch bereinigt.

| # | Task | Datei(en) | Akzeptanzkriterium |
|---|------|-----------|-------------------|
| 2.1 | `memory_cache.py` erstellen (LRU-bounded) | `backend/services/memory_cache.py` | Code aus Section 4.1, MAX_ITEMS=500, OrderedDict, CacheMetrics |
| 2.2 | Integration in `retrieve_diamond_context` | `backend/services/memory_manager.py` | Bei `priority >= 0.8` Query wird Cache bevorzugt |
| 2.3 | Cache Invalidation + `put()` | `backend/services/memory_manager.py` | `save_memory_snippet` triggert `cache.put()` für neue High-Priority, Eviction bei Überlauf funktioniert |
| 2.4 | `memory_cleanup.py` erstellen | `backend/services/memory_cleanup.py` | Code aus Section 2.4, `purge_expired_memories()` löscht Zombies |
| 2.5 | Lifespan-Hook in `main.py` | `backend/main.py` | Cleanup-Task startet bei App-Start, cancelled bei Shutdown |
| 2.6 | Lazy-Filter in `retrieve_diamond_slots` | `backend/services/memory_manager.py` | `WHERE expires_at IS NULL OR expires_at > NOW() OR retain_until > NOW()` |
| 2.7 | Unit Tests | `backend/tests/test_memory_cache.py` | 8 Tests: refresh, get, put, eviction, invalidate, stats, LRU-order, zombie-purge |

---

### Phase 3: Enricher, Guard & Resilience — ETA 4h

**Ziel:** LLM extrahiert nur Fakten, Enricher setzt Metadaten, Guard enforced Caps. Circuit-Breaker schützt vor Provider-Ausfällen. Dedup-Merge ist deterministisch.

| # | Task | Datei(en) | Akzeptanzkriterium |
|---|------|-----------|-------------------|
| 3.1 | `memory_enricher.py` erstellen | `backend/services/memory_enricher.py` | Code aus Section 4.2 implementiert |
| 3.2 | Integration in Extraction-Flow | `backend/services/memory_extractor.py` | Nach Zeile 637 (nach Kategorie-Normalisierung) wird `enrich_fact()` aufgerufen |
| 3.3 | Priority Guard in `save_memory_snippet` | `backend/services/memory_manager.py` | Clamp-Logik implementiert, Logging bei Clamping |
| 3.4 | Guard in `save_core_memory_fact` | `backend/services/memory_manager.py` | Explizite Quelle setzen, Guard prüft |
| 3.5 | `_merge_existing_memory()` implementieren | `backend/services/memory_manager.py` | Code aus Section 4.4.1: MAX-Priority, UNION-Tags, Snippet-only-on-upgrade |
| 3.6 | `ExtractionCircuitBreaker` implementieren | `backend/services/memory_extractor.py` | Code aus Section 4.4.3: 3 Failures → OPEN für 120s, HALF_OPEN Probe |
| 3.7 | `embedding_cache.py` erstellen | `backend/services/embedding_cache.py` | Code aus Section 4.4.2: `@lru_cache(maxsize=2048)` für Embedding-Parsing |
| 3.8 | `memory_observability.py` erstellen | `backend/services/memory_observability.py` | Code aus Section 4.4.4: `MemorySystemMetrics` Singleton |
| 3.9 | Unit Tests Enricher + Guard + Breaker | `backend/tests/test_memory_enricher.py` | 12 Tests: Priority-Regeln, TTL, Tags, Guard, Merge, CircuitBreaker states |

---

### Phase 4: Smart Context (Slots) — ETA 4h

**Ziel:** `build_final_context_v2` mit MemorySlots und Knapsack-Budget ersetzt alte String-Truncation.

| # | Task | Datei(en) | Akzeptanzkriterium |
|---|------|-----------|-------------------|
| 4.1 | `MemorySlot` Dataclass | `backend/services/context_manager.py` | Code aus Section 4.3 implementiert |
| 4.2 | `retrieve_diamond_slots()` | `backend/services/memory_manager.py` | Neue Funktion, liefert `List[MemorySlot]` statt String. Nutzt `parse_embedding()` Cache |
| 4.3 | Knapsack `select_slots_by_budget` | `backend/services/context_manager.py` | `continue` statt `break` bei Übergröße, `min_slot_tokens` Early-Termination |
| 4.4 | `build_final_context_v2` | `backend/services/context_manager.py` | Budget-Aware Selection implementiert |
| 4.5 | Orchestrator-Integration | `backend/services/chat_orchestrator.py` | Aufruf von `build_final_context_v2` statt altem Code |
| 4.6 | Feature-Flag `MEMORY_V2_ENABLED` | `backend/config.py` | Alter Code per Flag abschaltbar (Rollback-Plan) |
| 4.7 | Debug-Endpoint `/api/debug/memory` | `backend/main.py` | Gibt Cache-Stats, Metrics, CircuitBreaker, Embedding-Cache auf einen Blick |
| 4.8 | Unit Tests | `backend/tests/test_context_manager.py` | 8 Tests: Budget-Calc, Knapsack-Selection, Tier-Formatting, Edge-Cases (0 slots, 1 huge slot) |

---

### Phase 5: Unified Tools — ETA 4h

**Ziel:** Neue Tool-Suite funktioniert, Skills können Memories lesen/schreiben.

| # | Task | Datei(en) | Akzeptanzkriterium |
|---|------|-----------|-------------------|
| 5.1 | Tool JSONs erstellen | `backend/skills/system/memory_*.json` | Alle 4 JSON-Dateien aus Section 5 |
| 5.2 | `memory_write` Implementation | `backend/tools/memory_tools.py` | Funktion schreibt über `save_memory_snippet` |
| 5.3 | `memory_read` Implementation | `backend/tools/memory_tools.py` | Vektor-Suche + Filter nach Tags/Priority |
| 5.4 | `memory_update` Implementation | `backend/tools/memory_tools.py` | Check `user_editable`, Prüfung auf Eigentümer |
| 5.5 | `memory_history` Implementation | `backend/tools/memory_tools.py` | Audit-Trail (neue Tabelle oder JSON-Array) |
| 5.6 | Skill Mapping | `backend/skills/memory/skill_mapping.json` | Tools sind aufrufbar |
| 5.7 | Integration Tests | `backend/tests/test_memory_tools.py` | End-to-End Tests für alle 4 Tools |

---

### Phase 6: Integration & Regression — ETA 4h

**Ziel:** Gesamtsystem läuft, bestehende Tests grün, Performance-Metriken erreicht.

| # | Task | Akzeptanzkriterium |
|---|------|-------------------|
| 6.1 | Full Test Suite | `pytest backend/tests -q` > 95% Passing |
| 6.2 | Performance Benchmark | `retrieve_diamond_slots()` < 50ms für 10k Memories |
| 6.3 | RAM Cache Benchmark | Cache-Hit < 5ms |
| 6.4 | Staging Deployment | Migration auf Staging-DB erfolgreich |
| 6.5 | Documentation Update | `WHAT_I_LEARNED.md` + `PROJECT_STATE.md` aktualisiert |

---

## 7. Risiken & Mitigations

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|---------------------|--------|------------|
| Migration korruptiert Daten | Niedrig | Kritisch | Backup-Policy: 3-stufig (DB-Backup, Test auf Kopie, dry-run Mode) |
| Cache-Invalidation verpasst | Mittel | Hoch | "Cache-First-Read" Strategie: Bei Cache-Miss → DB-Read → Cache-Update |
| Performance-Regression | Mittel | Hoch | Benchmarks in CI, P95 < 50ms Gate |
| Priority Guard zu restriktiv | Niedrig | Mittel | Logging + Metrics, Dashboard für Clamping-Events |
| LLM gibt weiterhin Metadaten | Niedrig | Niedrig | Sanitizer: Ignoriere LLM-Metadaten, überschreibe mit Enricher-Werten |
| **RAM-Cache OOM** (Opus V2.1) | Niedrig | Kritisch | MAX_ITEMS=500 Hard-Limit, LRU-Eviction, `get_stats()` Monitoring |
| **Zombie-Memories akkumulieren** (Opus V2.1) | Mittel | Mittel | Lazy-Filter auf Read + Background-Purge alle 15 Min |
| **LLM-Extraction-Loop bei Provider-Ausfall** (Opus V2.1) | Mittel | Hoch | Circuit-Breaker: 3 Failures → 120s Lockout, HALF_OPEN Probe |
| **Dedup Race Condition** (Opus V2.1) | Niedrig | Mittel | Deterministische Merge-Strategie: MAX-Priority, UNION-Tags, Snippet-only-on-upgrade |
| **Embedding-Parse Hotspot** (Opus V2.1) | Hoch | Mittel | `@lru_cache(maxsize=2048)` für `parse_embedding()`, 90%+ Hit-Rate erwartet |

---

## 8. Success Metrics (Messbare Ziele)

**Performance:**
- P95 Latenz für Memory-Abfrage: < 50ms (10k Memories)
- P95 Latenz für High-Priority (RAM): < 5ms
- Memory Context Build: < 20ms
- Embedding Parse Cache Hit-Rate: > 90%

**Qualität:**
- Priority Guard Triggers: < 5% aller Writes
- Cache Hit Rate (priority >= 0.8): > 95%
- Migration Success Rate: 100% (0 Datenverlust)
- Zombie-Memories nach 24h: 0
- Circuit-Breaker OPEN-Events pro Woche: < 3

**Resilience (Opus V2.1):**
- RAM-Cache Utilization: < 80% von MAX_ITEMS (400/500)
- Cache Evictions pro Stunde: < 10 (sonst MAX_ITEMS erhöhen)
- Dedup-Merge Collisions pro Tag: < 5% aller Writes
- Knapsack-Budget Utilization: > 85% (wenig verschwendeter Platz)

**Adoption:**
- Unified Tools Usage: > 50% aller Memory-Interaktionen nach 2 Wochen
- Externe Skill Writes: > 10 Skills nutzen `memory_write`
- Debug-Endpoint `/api/debug/memory` wird von Ops genutzt |

---

**END OF SPECIFICATION**

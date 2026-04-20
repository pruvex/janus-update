"""
In-Process RAM Cache für High-Priority Memories.
Singleton-Pattern, LRU-bounded, thread-safe via GIL.
MAX_ITEMS = 500 → ~1MB worst-case RAM footprint.

V2.1.0 Gold Standard:
- LRU-Eviction bei Überlauf (niedrigste Priority first)
- Observability: hits/misses/evictions/refreshes/invalidations
- Refresh-Intervall: 5 Minuten
"""

from typing import Dict, List, Optional, Any
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
import threading
import time
import logging
from sqlalchemy.orm import Session

from backend.data import models
from backend.services.memory_observability import memory_metrics

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
    created_at: Optional[datetime] = None
    chat_id: Optional[int] = None


@dataclass
class CacheMetrics:
    """Observability Counters (V2.1 Gold Standard)."""
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
    
    GOLD STANDARD (V2.1):
    - MAX_ITEMS: Hard-Limit auf 500 Einträge (OOM-Schutz)
    - LRU-Eviction: Bei Überlauf werden niedrig-priorisierte Einträge entfernt
    - Observability: hits/misses/evictions/refreshes/invalidations zählen
    
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
        self._lock: threading.Lock = threading.Lock()  # Instance lock for thread safety
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
                tags=tuple(mem.tags if isinstance(mem.tags, list) else []),
                snippet=mem.snippet or "",
                text_hash=mem.text_hash or "",
                created_at=getattr(mem, "created_at", None),
                chat_id=getattr(mem, "chat_id", None),
            )
            new_cache[mem.id] = cached
        
        # Atomarer Swap mit Lock-Schutz
        with self._lock:
            evicted = max(0, len(self._cache) - len(new_cache))
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
        with self._lock:
            should_refresh = time.time() - self._last_refresh > self.REFRESH_INTERVAL_SECONDS
        if should_refresh:
            self.refresh(db)
    
    def get(self, memory_id: int) -> Optional[CachedMemory]:
        """Einzelnen Cache-Eintrag abrufen. Zählt hit/miss. Thread-safe."""
        with self._lock:
            entry = self._cache.get(memory_id)
            if entry is not None:
                self._metrics.hits += 1
                # LRU: Move to end (most recently used)
                self._cache.move_to_end(memory_id)
                logger.debug(f"[CACHE HIT] ID={memory_id}, priority={entry.priority}")
            else:
                self._metrics.misses += 1
                logger.debug(f"[CACHE MISS] ID={memory_id}")
        # Increment global metrics OUTSIDE the local lock (avoids nested-lock risk)
        if entry is not None:
            memory_metrics.increment("reads_cache_hit")
        else:
            memory_metrics.increment("reads_cache_miss")
        return entry
    
    def get_all(self) -> List[CachedMemory]:
        """Alle gecachten High-Priority Memories. Thread-safe."""
        with self._lock:
            return list(self._cache.values())
    
    def get_by_tag(self, tag: str) -> List[CachedMemory]:
        """Filtere Cache nach Tag. Thread-safe."""
        with self._lock:
            return [m for m in self._cache.values() if tag in m.tags]
    
    def put(self, mem: CachedMemory) -> None:
        """
        Fügt einen Eintrag hinzu. Bei Überlauf wird der 
        niedrigst-priorisierte Eintrag evicted. Thread-safe.
        """
        with self._lock:
            if mem.id in self._cache:
                # Update: Entferne alten, füge neuen hinzu (LRU-Preservation)
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
        """Einzelnen Eintrag invalidieren (z.B. nach Update/Delete). Thread-safe."""
        with self._lock:
            if memory_id in self._cache:
                del self._cache[memory_id]
                self._metrics.invalidations += 1
                logger.debug(f"[CACHE INVALIDATE] ID={memory_id}")
    
    def invalidate_all(self) -> None:
        """Cache komplett leeren. Thread-safe."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._last_refresh = 0
            self._metrics.invalidations += count
            logger.info(f"[CACHE INVALIDATE_ALL] {count} entries cleared")
    
    def touch(self, memory_id: int) -> None:
        """
        Markiert einen Eintrag als frisch verwendet (LRU-Update).
        Wird aufgerufen wenn ein Memory im Kontext verwendet wird. Thread-safe.
        """
        with self._lock:
            if memory_id in self._cache:
                self._cache.move_to_end(memory_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Diagnose-Info für /api/debug/memory-cache Endpoint. Thread-safe."""
        with self._lock:
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


# Convenience-Export (Singleton-Instance)
memory_cache = MemoryRAMCache()

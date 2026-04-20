"""
Zentrale Observability für das Memory System.
Sammelt Counters von Cache, Enricher, Guard, Dedup, Cleanup.

Memory System V2.1.0 - Diamond Standard
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

"""
LRU-Cache für deserialisierte Embeddings.
Eliminiert redundante json.loads() Aufrufe im Retrieval-Path.

Memory System V2.1.0 - Diamond Standard
"""

from functools import lru_cache
from typing import Optional, List
import json
import logging

logger = logging.getLogger("janus_backend")


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
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.debug(f"[EMBEDDING CACHE] Failed to parse embedding: {e}")
        return None


def clear_embedding_cache() -> None:
    """Cache leeren (z.B. nach Bulk-Update von Embeddings)."""
    parse_embedding.cache_clear()
    logger.info("[EMBEDDING CACHE] Cache cleared")


def embedding_cache_stats() -> dict:
    """Diagnose."""
    info = parse_embedding.cache_info()
    total = info.hits + info.misses
    return {
        "hits": info.hits,
        "misses": info.misses,
        "maxsize": info.maxsize,
        "currsize": info.currsize,
        "hit_rate": f"{info.hits / total * 100:.1f}%" if total > 0 else "0%"
    }

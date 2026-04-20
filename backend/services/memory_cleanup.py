"""
TTL Cleanup Service für Zombie-Memory Prävention.

Zweischichten-Architektur:
- Layer 1: Lazy-on-Read (immer aktiv, filtert abgelaufene Memories)
- Layer 2: Background Purge (alle 15 Min, löscht echte Zombies)

V2.1.0 Gold Standard: Periodischer Cleanup-Task mit Cache-Invalidation.
"""

import asyncio
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from backend.data.database import SessionLocal
from backend.data import models
from backend.services.memory_cache import memory_cache

logger = logging.getLogger("janus_backend")

# Default: 15 Minuten (900 Sekunden)
DEFAULT_CLEANUP_INTERVAL_SECONDS: int = 900


async def schedule_memory_cleanup(interval_seconds: int = DEFAULT_CLEANUP_INTERVAL_SECONDS) -> None:
    """
    Periodischer Zombie-Cleanup (alle 15 Min).
    
    Wird als Background-Task in FastAPI lifespan gestartet.
    
    Usage (in main.py):
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            cleanup_task = asyncio.create_task(
                schedule_memory_cleanup(interval_seconds=900)
            )
            yield
            cleanup_task.cancel()
    """
    logger.info(f"[MEMORY CLEANUP] Background task started (interval={interval_seconds}s)")
    
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            purged = purge_expired_memories()
            if purged > 0:
                logger.info(f"[MEMORY CLEANUP] Purged {purged} zombie memories")
        except asyncio.CancelledError:
            logger.info("[MEMORY CLEANUP] Background task cancelled")
            break
        except Exception as e:
            logger.error(f"[MEMORY CLEANUP] Error: {e}", exc_info=True)


def purge_expired_memories() -> int:
    """
    Löscht alle Memories deren retain_until abgelaufen ist.
    
    Returns:
        Anzahl der gelöschten Memories (Zombies)
    """
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Finde Zombies: retain_until ist gesetzt UND abgelaufen
        zombies = db.query(models.Memory).filter(
            models.Memory.retain_until.isnot(None),
            models.Memory.retain_until < now
        ).all()
        
        zombie_ids: List[int] = [z.id for z in zombies]
        
        for z in zombies:
            logger.debug(
                f"[ZOMBIE PURGE] ID={z.id}, key={z.canonical_key}, "
                f"retain_until={z.retain_until} < now={now}"
            )
            db.delete(z)
        
        db.commit()
        
        # Cache-Invalidation für gelöschte IDs
        for zid in zombie_ids:
            memory_cache.invalidate(zid)
        
        if zombie_ids:
            logger.info(
                f"[ZOMBIE PURGE COMPLETE] Deleted {len(zombie_ids)} memories, "
                f"invalidated {len(zombie_ids)} cache entries"
            )
        
        return len(zombie_ids)
        
    except Exception as e:
        db.rollback()
        logger.error(f"[ZOMBIE PURGE FAILED] {e}", exc_info=True)
        return 0
    finally:
        db.close()


def purge_by_expires_at() -> int:
    """
    Zusätzlicher Purge für Memories deren expires_at abgelaufen ist
    UND die kein retain_until haben (oder retain_until ebenfalls abgelaufen).
    
    Dies ist eine ergänzende Methode für den Fall dass ein Memory
    expire aber noch nicht die Grace-Period (retain_until) erreicht hat.
    """
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Finde Memories: expires_at ist abgelaufen UND (retain_until ist NULL ODER abgelaufen)
        zombies = db.query(models.Memory).filter(
            models.Memory.expires_at.isnot(None),
            models.Memory.expires_at < now,
            (
                (models.Memory.retain_until.is_(None)) |
                (models.Memory.retain_until < now)
            )
        ).all()
        
        zombie_ids: List[int] = [z.id for z in zombies]
        
        for z in zombies:
            logger.debug(
                f"[EXPIRED PURGE] ID={z.id}, key={z.canonical_key}, "
                f"expires_at={z.expires_at}"
            )
            db.delete(z)
        
        db.commit()
        
        # Cache-Invalidation
        for zid in zombie_ids:
            memory_cache.invalidate(zid)
        
        if zombie_ids:
            logger.info(f"[EXPIRED PURGE COMPLETE] Deleted {len(zombie_ids)} expired memories")
        
        return len(zombie_ids)
        
    except Exception as e:
        db.rollback()
        logger.error(f"[EXPIRED PURGE FAILED] {e}", exc_info=True)
        return 0
    finally:
        db.close()


def get_zombie_stats() -> dict:
    """
    Diagnose: Zählt potentielle Zombies (noch nicht gelöscht, aber abgelaufen).
    """
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Zombies: retain_until abgelaufen
        retain_zombies = db.query(models.Memory).filter(
            models.Memory.retain_until.isnot(None),
            models.Memory.retain_until < now
        ).count()
        
        # Expired: expires_at abgelaufen, aber retain_until noch nicht
        expired_but_retained = db.query(models.Memory).filter(
            models.Memory.expires_at.isnot(None),
            models.Memory.expires_at < now,
            models.Memory.retain_until.isnot(None),
            models.Memory.retain_until >= now
        ).count()
        
        # Expired ohne retain_until
        expired_no_retain = db.query(models.Memory).filter(
            models.Memory.expires_at.isnot(None),
            models.Memory.expires_at < now,
            models.Memory.retain_until.is_(None)
        ).count()
        
        return {
            "retain_until_expired": retain_zombies,
            "expired_but_grace_period": expired_but_retained,
            "expired_no_retain": expired_no_retain,
            "total_potential_zombies": retain_zombies + expired_no_retain,
            "checked_at": now.isoformat()
        }
        
    finally:
        db.close()


# Convenience für manuellen Aufruf (z.B. Admin-Endpoint)
def run_full_cleanup() -> dict:
    """
    Führt beide Purge-Methoden aus und gibt Statistik zurück.
    """
    logger.info("[FULL CLEANUP] Manual cleanup triggered")
    
    stats_before = get_zombie_stats()
    purged_retain = purge_expired_memories()
    purged_expired = purge_by_expires_at()
    stats_after = get_zombie_stats()
    
    result = {
        "purged_by_retain_until": purged_retain,
        "purged_by_expires_at": purged_expired,
        "total_purged": purged_retain + purged_expired,
        "stats_before": stats_before,
        "stats_after": stats_after,
        "cache_stats": memory_cache.get_stats()
    }
    
    logger.info(f"[FULL CLEANUP COMPLETE] {result['total_purged']} memories purged")
    return result

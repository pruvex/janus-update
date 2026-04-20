"""CRUD und schreibende/löschende Memory-Operationen (extrahiert aus memory_manager, Task 020)."""
import datetime
import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

import backend.data.models as models
from backend.logger_config import setup_logging
from backend.services.memory_cache import CachedMemory, memory_cache
from backend.services.memory_enricher import apply_priority_guard
from backend.services.memory_observability import memory_metrics
from backend.services import vector_service

setup_logging()
logger = logging.getLogger("janus_backend")


GRACE_PERIOD_DAYS = 7


def compute_hash(text: str) -> str:
    """Erstellt einen SHA256-Hash von einem Text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _serialize_embedding_json(embedding_json: str) -> bytes:
    """Serialisiert Embedding-JSON als UTF-8-Bytes für LargeBinary-Spalten."""
    if embedding_json is None:
        return None
    if isinstance(embedding_json, bytes):
        return embedding_json
    return embedding_json.encode("utf-8")


def _is_storage_path_artifact_fact(*, final_fact_text: str, canonical_key: str, object_value: str) -> bool:
    text = " ".join(
        [
            str(final_fact_text or ""),
            str(canonical_key or ""),
            str(object_value or ""),
        ]
    ).lower()
    if ".pdf" not in text:
        return False

    has_path_signal = bool(re.search(r"[a-z]:\\|\\\\|/users/|/home/|/documents/", text))
    has_storage_keyword = any(
        token in text
        for token in (
            "gespeichert unter",
            "dokument wurde unter",
            "dokumentenpfad",
            "dateipfad",
            "speicherpfad",
            "pdf-datei",
        )
    )
    return has_path_signal and has_storage_keyword


def save_memory_snippet(
    db: Session,
    chat_id: int,
    fact_object: Any = None,
    source_type: str = "text",
    source_metadata: dict = None,
    snippet_text: Optional[str] = None,
    category: str = "General Fact",
    expires_at: Optional[datetime.datetime] = None,
    is_core: bool = False,
    core_priority: Optional[int] = None,
) -> Optional[models.Memory]:
    """
    Speichert ein strukturiertes Fakten-Objekt, reinigt die Daten VOR dem Speichern
    und nutzt den canonical_key für die Deduplizierung.
    """
    def sanitize_data(value: Any) -> Any:
        """Rekursive Konvertierung in JSON-/DB-sichere Python-Standardtypen."""
        if isinstance(value, dict):
            return {str(sanitize_data(k)): sanitize_data(v) for k, v in value.items()}
        if isinstance(value, list):
            return [sanitize_data(v) for v in value]
        if isinstance(value, tuple):
            return [sanitize_data(v) for v in value]
        if isinstance(value, set):
            return [sanitize_data(v) for v in value]
        if isinstance(value, np.ndarray):
            return sanitize_data(value.tolist())
        if isinstance(value, np.floating):
            return float(value)
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.bool_):
            return bool(value)
        if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
            return value.isoformat()
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value

    # --- Legacy-Kompatibilität: alter String-basierten Call-Style unterstützen ---
    if not isinstance(fact_object, dict):
        raw_snippet = snippet_text if isinstance(snippet_text, str) else str(fact_object or "")
        raw_snippet = raw_snippet.strip()
        if not raw_snippet:
            logger.warning("Ignoriere leeren Memory-Snippet-Text.")
            return None

        embedding = vector_service.generate_embedding(raw_snippet)
        if embedding is None:
            logger.error("Konnte kein Embedding für Legacy-Snippet erstellen. Speichern abgebrochen.")
            return None

        resolved_core_priority = core_priority if core_priority is not None else (1 if is_core else 0)
        retain_until = (
            expires_at + datetime.timedelta(days=GRACE_PERIOD_DAYS)
            if expires_at is not None
            else None
        )

        try:
            db_memory = models.Memory(
                chat_id=chat_id,
                snippet=raw_snippet,
                embedding_json=_serialize_embedding_json(embedding),
                category=category,
                expires_at=expires_at,
                retain_until=retain_until,
                is_core_fact=bool(is_core),
                core_priority=resolved_core_priority,
                source_type=source_type,
                source_metadata=sanitize_data(source_metadata or {}),
            )
            db.add(db_memory)
            db.commit()
            db.refresh(db_memory)
            
            # CACHE INTEGRATION: Legacy-Put - Convert core_priority to priority for cache
            # core_priority=2 → priority=0.95, core_priority=1 → priority=0.75, else 0.50
            legacy_priority = 0.95 if resolved_core_priority == 2 else (0.75 if resolved_core_priority == 1 else 0.50)
            if legacy_priority >= memory_cache.PRIORITY_THRESHOLD:
                cached = CachedMemory(
                    id=db_memory.id,
                    canonical_key=db_memory.canonical_key or db_memory.text_hash or raw_snippet[:50],
                    priority=legacy_priority,
                    memory_type="GENERAL",
                    tags=(),
                    snippet=raw_snippet,
                    text_hash=compute_hash(raw_snippet)
                )
                memory_cache.put(cached)
                logger.debug(f"[CACHE PUT LEGACY] ID={db_memory.id}, priority={legacy_priority}")
            
            return db_memory
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Legacy-Memory-Snippets: {e}", exc_info=True)
            db.rollback()
            return None

    fact_object = sanitize_data(fact_object)
    source_metadata = sanitize_data(source_metadata or {})

    # ═══════════════════════════════════════════════════════════════════════════
    # HARD-KEY LOCK (Task 016) – Immutable identity address
    # ═══════════════════════════════════════════════════════════════════════════
    # ANY fact with category "Physis" and a name-predicate MUST use the fixed
    # canonical_key.  This is enforced here — not in the extractor — so it
    # catches both the pre-pass path AND any LLM-extracted Physis name facts.
    _PHYSIS_NAME_PREDICATES: frozenset = frozenset({
        "heißt", "heisst", "name_is", "ist_name", "hat_name",
    })
    if (
        str(fact_object.get("category", "")).strip() == "Physis"
        and str(fact_object.get("predicate", "")).strip() in _PHYSIS_NAME_PREDICATES
    ):
        fact_object["canonical_key"] = "user:physis:heisst:name"
        fact_object["_fixed_canonical_key"] = "user:physis:heisst:name"
        logger.info(
            "[HARD-KEY LOCK] Identity key enforced — predicate=%r object_value=%r",
            fact_object.get("predicate"),
            fact_object.get("object_value"),
        )
    # ═══════════════════════════════════════════════════════════════════════════

    # --- ULTRA-SANITIZER V3: Daten VOR dem Speichern in saubere Sprache umwandeln ---
    evidence = fact_object.get("evidence", "")
    raw_fact = fact_object.get("fact", "")
    key = fact_object.get("canonical_key", "")
    
    final_fact_text = ""

    # Priorität 1: Evidence ist immer der beste Text
    if evidence and len(evidence) > 5:
        final_fact_text = evidence
    
    # Priorität 2: Wenn das "fact"-Feld wie ein Satz aussieht
    elif raw_fact and "|" not in raw_fact and "(" not in raw_fact:
        final_fact_text = raw_fact

    # Priorität 2.5 (NEU): Wenn es ein visueller Fakt ist, behalte Details
    elif source_type == "vision":
        # Versuche, den Fakt so direkt wie möglich zu übernehmen
        if evidence and len(evidence) > 5:
            final_fact_text = evidence
        else:
            # Kombiniere Prädikat und Objekt, um Details zu bewahren
            pred = fact_object.get("predicate", "").replace("_", " ")
            obj = fact_object.get("object_value", "")
            if pred and obj:
                final_fact_text = f"{pred} {obj}"
            elif obj: # Fallback, falls nur ein Objekt da ist
                final_fact_text = obj
            
    # Priorität 3: Wenn alles andere Müll ist, übersetzen wir den canonical_key
    elif key and "|" in key:
        try:
            parts = key.split('|')
            if len(parts) >= 3:
                pred = parts[0].replace('_', ' ').replace('hat name', 'heißt').replace('name_is', 'heißt')
                subj_raw = parts[1]
                obj = parts[2]
                
                subj_name = subj_raw.split(':')[-1]
                subj_text = subj_name
                if "pet:dog" in subj_raw: subj_text = f"Der Hund {subj_name}"
                elif "pet:cat" in subj_raw: subj_text = f"Die Katze {subj_name}"
                elif "contact:person" in subj_raw: subj_text = f"Die Person {subj_name}"

                constructed_sentence = f"{subj_text} {pred} {obj}."
                final_fact_text = constructed_sentence
        except Exception:
            final_fact_text = raw_fact or key 
    else:
        final_fact_text = raw_fact or key

    # Letzte Bereinigung und Update des Objekts
    final_fact_text = final_fact_text.replace("dass dein", "Dein").strip().capitalize()
    if not final_fact_text:
        logger.warning("Ignoriere leeren Fakt nach Sanitize-Vorgang.")
        return None

    if _is_storage_path_artifact_fact(
        final_fact_text=final_fact_text,
        canonical_key=str(key or ""),
        object_value=str(fact_object.get("object_value") or ""),
    ):
        logger.info("Filtere technischen Speicherpfad-Fakt aus Memory-Persistenz: %s", final_fact_text)
        return None
        
    logger.info(f"SANITIZER: Finaler Fakt-Text für Speicherung: '{final_fact_text}'")
    fact_object["fact"] = final_fact_text
    # -----------------------------------------------------------------------------------

    # 1. Extrahiere den canonical_key (Original für Deduplizierung)
    if not key:
        logger.error("Fakt ohne canonical_key kann nicht gespeichert werden.")
        return None
    
    text_hash = compute_hash(key)

    # ═══════════════════════════════════════════════════════════════════════════
    # DEDUP-MERGE STRATEGY (Opus V2.1) - Merge statt Ignorieren
    # ═══════════════════════════════════════════════════════════════════════════
    existing = db.query(models.Memory).filter(
        models.Memory.text_hash == text_hash
    ).first()

    if existing:
        _merge_existing_memory(db, existing, fact_object, source_type)
        memory_metrics.increment("writes_deduplicated")
        return existing  # Merged statt ignoriert

    # ═══════════════════════════════════════════════════════════════════════════
    # PRIORITY GUARD (Opus V2.1) - Cappt Priority basierend auf Quelle
    # ═══════════════════════════════════════════════════════════════════════════
    enriched_priority = fact_object.get("priority", 0.50)
    source_skill = fact_object.get("source_skill", "system.extractor")
    guarded_priority = apply_priority_guard(enriched_priority, source_skill)
    
    if guarded_priority < enriched_priority:
        memory_metrics.increment("writes_guarded")
    
    fact_object["priority"] = guarded_priority
    # ═══════════════════════════════════════════════════════════════════════════

    # 3. Wenn neu, fortfahren
    embedding = vector_service.generate_embedding(final_fact_text)
    if embedding is None:
        logger.error(f"Konnte kein Embedding für '{final_fact_text}' erstellen. Speichern abgebrochen.")
        return None

    snippet_json = json.dumps(fact_object, ensure_ascii=False)
    source_metadata = json.loads(json.dumps(source_metadata, ensure_ascii=False))

    try:
        # V2-Felder aus dem angereicherten Fakt-Objekt extrahieren
        category = fact_object.get("category")
        memory_type = fact_object.get("memory_type", "GENERAL")
        ttl = fact_object.get("ttl")
        tags = fact_object.get("tags", [])
        user_editable = fact_object.get("user_editable", True)
        
        # TTL zu expires_at konvertieren
        expires_at = None
        if ttl is not None:
            expires_at = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
        
        retain_until = None
        if expires_at is not None:
            retain_until = expires_at + datetime.timedelta(days=GRACE_PERIOD_DAYS)

        db_memory = models.Memory(
            chat_id=chat_id,
            snippet=snippet_json,
            embedding_json=_serialize_embedding_json(embedding),
            normalized_text=key,
            text_hash=text_hash,
            category=category,
            # Legacy Felder
            is_core_fact=(guarded_priority >= 0.85),
            core_priority=(2 if guarded_priority >= 0.95 else (1 if guarded_priority >= 0.85 else 0)),
            # V2 Felder
            priority=guarded_priority,
            memory_type=memory_type,
            ttl=ttl,
            tags=tags,
            source_skill=source_skill,
            user_editable=user_editable,
            canonical_key=key,
            expires_at=expires_at,
            retain_until=retain_until,
            source_type=source_type,
            source_metadata=source_metadata,
        )
        db.add(db_memory)
        db.commit()
        db.refresh(db_memory)
        
        logger.info(
            "[SAVED] id=%d, key=%s, priority=%s, memory_type=%s, source_skill=%s",
            db_memory.id, key, guarded_priority, memory_type, source_skill
        )
        memory_metrics.increment("writes_total")
        
        # CACHE INTEGRATION: Aggressive Cache-Warming (V2.1.0 Diamond)
        # Jede Memory mit priority >= 0.8 MUSS sofort in den RAM-Cache,
        # ohne auf den nächsten Refresh-Zyklus zu warten.
        if db_memory.priority >= memory_cache.PRIORITY_THRESHOLD:
            cached = CachedMemory(
                id=db_memory.id,
                canonical_key=db_memory.canonical_key or db_memory.text_hash or "",
                priority=db_memory.priority,
                memory_type=db_memory.memory_type or "GENERAL",
                tags=tuple(db_memory.tags if isinstance(db_memory.tags, list) else []),
                snippet=db_memory.snippet or "",
                text_hash=db_memory.text_hash or ""
            )
            memory_cache.put(cached)
            logger.info(
                "[CACHE WARM] New high-priority memory cached immediately: "
                "ID=%d, priority=%.2f, key=%s",
                db_memory.id, db_memory.priority, key,
            )
        
        _consolidate_memory_after_save(db, fact_object)
        return db_memory
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Memory-Snippets: {e}", exc_info=True)
        db.rollback()
        return None


def _merge_existing_memory(
    db: Session,
    existing: models.Memory,
    new_fact: Dict[str, Any],
    new_source_type: str
) -> None:
    """
    Deterministische Merge-Strategie bei Dedup-Hit (gleicher canonical_key).
    
    REGELN (Opus V2.1):
    1. Priority: MAX(existing, new) — höchste gewinnt
    2. Tags: UNION — additiv, keine Löschung
    3. source_skill/source_type: Behalte Original, logge Collision
    4. snippet: Überschreibe NUR wenn new.priority > existing.priority
    5. last_accessed_at: NOW()
    6. Cache: invalidate nach Merge
    """
    # SECURITY GUARD: Prevent modification of non-editable memories
    if not existing.user_editable:
        logger.warning(
            "[SECURITY] BLOCKED Attempt to merge non-editable memory ID=%d",
            existing.id
        )
        return None
    
    try:
        old_priority = existing.priority or 0.5
        new_raw_priority = new_fact.get("priority", 0.5)
        new_source_skill = new_fact.get("source_skill", "system.extractor")
        
        # GUARD: Apply Priority Guard to new priority before comparison
        new_priority = apply_priority_guard(new_raw_priority, new_source_skill)
        
        # ── Identity slot: always overwrite snippet (Task 015) ──────────────
        # The clean name from the pre-pass (after stop-word truncation) must
        # always win, even when old and new priority are equal (both 0.95).
        _is_identity_slot = (existing.canonical_key == "user:physis:heisst:name")
        if _is_identity_slot and new_fact.get("fact"):
            existing.snippet = json.dumps(new_fact, ensure_ascii=False)
            existing.priority = max(old_priority, new_priority)
            existing.memory_type = "CORE"
            existing.is_core_fact = True
            existing.core_priority = 2
            logger.info(
                "[DEDUP MERGE] Identity slot overwritten: fact=%r priority=%.2f",
                new_fact.get("fact"), existing.priority,
            )
        # ────────────────────────────────────────────────────────────────────

        # 1. Priority: Higher wins
        elif new_priority > old_priority:
            existing.priority = new_priority
            existing.memory_type = new_fact.get("memory_type", existing.memory_type)
            existing.is_core_fact = (new_priority >= 0.85)
            existing.core_priority = (2 if new_priority >= 0.95 else (1 if new_priority >= 0.85 else 0))
            
            # 4. Snippet: Nur bei Priority-Upgrade überschreiben
            if new_fact.get("fact"):
                existing.snippet = json.dumps(new_fact, ensure_ascii=False)
            logger.info(
                f"[DEDUP MERGE] Priority upgraded: {old_priority} -> {new_priority} "
                f"(key={existing.canonical_key})"
            )
        
        # 2. Tags: Union (set comparison for deterministic check)
        existing_tags = set(existing.tags or [])
        new_tags = set(new_fact.get("tags", []))
        merged_tags = list(existing_tags | new_tags)
        if set(merged_tags) != existing_tags:  # Set comparison (order-agnostic)
            existing.tags = merged_tags
            logger.debug(f"[DEDUP MERGE] Tags merged: {existing_tags} + {new_tags} = {merged_tags}")
        
        # 3. Source Skill: Log collision, keep original
        if new_source_skill and new_source_skill != existing.source_skill:
            logger.info(
                f"[DEDUP COLLISION] Key={existing.canonical_key}: "
                f"original_skill={existing.source_skill}, "
                f"competing_skill={new_source_skill} (kept original)"
            )
        
        # 5. Touch
        existing.last_accessed_at = datetime.datetime.now()
        
        db.commit()
        
        # 6. Cache-Warming: Nach Merge sofort zurück in den RAM-Cache statt nur invalidieren.
        #    Garantiert Cache-Hit beim ersten Recall nach Merge.
        merged_priority = existing.priority or 0.5
        if merged_priority >= memory_cache.PRIORITY_THRESHOLD:
            refreshed_cached = CachedMemory(
                id=existing.id,
                canonical_key=existing.canonical_key or existing.text_hash or "",
                priority=merged_priority,
                memory_type=existing.memory_type or "GENERAL",
                tags=tuple(existing.tags if isinstance(existing.tags, list) else []),
                snippet=existing.snippet or "",
                text_hash=existing.text_hash or ""
            )
            memory_cache.put(refreshed_cached)
            logger.info(
                "[CACHE WARM] Merged memory re-cached: ID=%d, priority=%.2f",
                existing.id, merged_priority,
            )
        else:
            memory_cache.invalidate(existing.id)
            logger.debug(f"[CACHE INVALIDATE] Merged ID={existing.id} (priority below threshold)")
        
    except Exception as e:
        logger.error(f"[DEDUP MERGE] Error during merge for key={existing.canonical_key}: {e}", exc_info=True)
        db.rollback()


def touch_memory_snippet(db: Session, memory_id: int):
    """Aktualisiert den last_accessed_at Zeitstempel eines STM-Eintrags und den Cache-LRU."""
    memory_item = db.query(models.Memory).filter(models.Memory.id == memory_id).first()
    if memory_item:
        memory_item.last_accessed_at = datetime.datetime.now()
        db.commit()
        # CACHE TOUCH: Update LRU position for this memory
        memory_cache.touch(memory_id)


def archive_old_memories(db: Session):
    """
    Prüft, ob das STM bereinigt werden muss und verschiebt die ältesten,
    am seltensten genutzten und nicht-essentiellen Erinnerungen ins LTM.
    """
    STM_LIMIT = 250
    STM_TARGET_SIZE = 200  # Reduzieren auf dieses Niveau, um nicht ständig zu archivieren

    try:
        stm_count = db.query(models.Memory).count()
        if stm_count <= STM_LIMIT:
            logger.info(
                f"STM size ({stm_count}) is within limit ({STM_LIMIT}). No archival needed."
            )
            return

        logger.info(
            f"STM size ({stm_count}) exceeds limit ({STM_LIMIT}). Starting archival process."
        )

        num_to_archive = stm_count - STM_TARGET_SIZE

        # Finde Kandidaten: Nicht "core", sortiert nach dem letzten Zugriff (älteste zuerst)
        # KORREKTUR: Die gesamte Abfrage wird in runde Klammern gesetzt, um IndentationErrors zu vermeiden.
        candidates = (
            db.query(models.Memory)
            .filter(not models.Memory.is_core_fact)
            .filter(
                models.Memory.expires_at is None
            )  # <-- GOLD STANDARD: Nur zeitlose Fakten archivieren!
            .order_by(models.Memory.last_accessed_at.asc())
            .limit(num_to_archive)
            .all()
        )

        if not candidates:
            logger.warning("STM is full but no non-core facts could be found to archive.")
            return

        for mem in candidates:
            # 1. In LTM kopieren
            new_ltm_entry = models.Memory(
                original_memory_id=mem.id,
                chat_id=mem.chat_id,
                snippet=mem.snippet,
                embedding_json=mem.embedding_json,
                created_at=mem.created_at,
            )
            db.add(new_ltm_entry)

            # 2. Aus STM löschen
            db.delete(mem)
            # CACHE INVALIDATE: Remove archived memory from cache
            memory_cache.invalidate(mem.id)

        db.commit()
        logger.info(f"Successfully archived {len(candidates)} memory snippets.")

    except Exception as e:
        logger.error(f"Error during memory archival: {e}")
        db.rollback()


def prune_expired_memories(db: Session):
    """
    Prunes expired memories according to the Diamond Memory Architecture rules.
    
    This function will:
    1. Delete memories that have expired and passed their retain_until date
    2. Archive old, rarely used memories to LTM (Long-Term Memory)
    3. Enforce token limits for different memory types
    """
    from datetime import datetime, timedelta

    from sqlalchemy import func, or_
    
    try:
        now = datetime.utcnow()
        
        # --- 1. Prune fully expired memories ---
        # Only delete memories that have both expired AND passed their retain_until date
        expired = db.query(models.Memory).filter(
            models.Memory.expires_at.isnot(None),
            models.Memory.retain_until.isnot(None),
            models.Memory.retain_until < now
        ).all()
        
        if expired:
            logger.info(f"Pruning {len(expired)} fully expired memories")
            for memory in expired:
                db.delete(memory)
                # CACHE INVALIDATE: Remove pruned memory from cache
                memory_cache.invalidate(memory.id)
            db.commit()
            logger.info(f"Successfully pruned {len(expired)} expired memories")
        
        # --- 2. Archive old, rarely used memories to LTM ---
        # Only archive non-core memories that are older than 30 days
        # and haven't been accessed in the last 7 days
        archive_cutoff = now - timedelta(days=30)
        last_access_cutoff = now - timedelta(days=7)
        
        # Get count of current LTM items to limit archiving if needed
        ltm_count = db.query(func.count(models.Memory.id)).scalar() or 0
        max_ltm_items = 5000  # Maximum number of items to keep in LTM
        
        if ltm_count < max_ltm_items:
            # Find memories to archive
            memories_to_archive = db.query(models.Memory).filter(
                models.Memory.is_core_fact == False,  # Don't archive core memories
                models.Memory.created_at < archive_cutoff,
                models.Memory.last_accessed_at < last_access_cutoff,
                or_(
                    models.Memory.expires_at.is_(None),  # Non-ephemeral
                    and_(
                        models.Memory.expires_at > now,  # Not yet expired
                        models.Memory.retain_until > now  # Not in grace period
                    )
                )
            ).order_by(
                models.Memory.last_accessed_at.asc()  # Oldest accessed first
            ).limit(max_ltm_items - ltm_count).all()
            
            # Archive the memories
            archived_count = 0
            archived_ids = []  # Track IDs for cache invalidation
            for memory in memories_to_archive:
                try:
                    # Create LTM entry
                    ltm_entry = models.Memory(
                        original_memory_id=memory.id,
                        chat_id=memory.chat_id,
                        snippet=memory.snippet,
                        embedding_json=memory.embedding_json,
                        created_at=memory.created_at,
                        archived_at=now
                    )
                    db.add(ltm_entry)
                    
                    # Delete from main memory
                    db.delete(memory)
                    archived_count += 1
                    archived_ids.append(memory.id)
                    
                except Exception as e:
                    logger.error(f"Error archiving memory {memory.id}: {e}")
                    db.rollback()
                    continue
            
            if archived_count > 0:
                db.commit()
                # CACHE INVALIDATE: Remove all archived memories from cache
                for mem_id in archived_ids:
                    memory_cache.invalidate(mem_id)
                logger.info(f"Archived {archived_count} memories to LTM")
        
        # --- 3. Enforce token limits for different memory types ---
        # This is a simplified version - in a real implementation, you'd want to
        # calculate actual token counts and enforce limits more precisely
        
        # Limit core always memories
        core_always_count = db.query(models.Memory).filter(
            models.Memory.is_core_fact == True,
            models.Memory.core_priority == 2  # Always include core
        ).count()
        
        max_core_always = 100  # Adjust based on your needs
        if core_always_count > max_core_always:
            # Find excess core always memories by least recently accessed
            excess_cores = db.query(models.Memory).filter(
                models.Memory.is_core_fact == True,
                models.Memory.core_priority == 2
            ).order_by(
                models.Memory.last_accessed_at.asc()
            ).limit(core_always_count - max_core_always).all()
            
            for memory in excess_cores:
                # Demote to queryable core instead of deleting
                memory.core_priority = 1
            
            if excess_cores:
                db.commit()
                logger.info(f"Demoted {len(excess_cores)} core always memories to queryable")
        
        return {
            "pruned": len(expired),
            "archived": archived_count if 'archived_count' in locals() else 0,
            "core_memories_demoted": len(excess_cores) if 'excess_cores' in locals() else 0
        }
        
    except Exception as e:
        logger.error(f"Error during memory pruning and maintenance: {e}", exc_info=True)
        db.rollback()
        return {"error": str(e)}


def update_memory_snippet(
    db: Session, 
    memory_id: int, 
    new_snippet: str, 
    is_core: bool = None,
    core_priority: int = None,
    expires_at: Optional[datetime] = None
):
    """
    Updates a memory snippet with new content and properties.
    
    Args:
        db: Database session
        memory_id: ID of the memory to update
        new_snippet: New content for the memory
        is_core: Whether this is a core memory (optional, keeps current if None)
        core_priority: New core priority (0=None, 1=Queryable, 2=Always, keeps current if None)
        expires_at: New expiration datetime (None for no expiration, keeps current if None)
        
    Returns:
        The updated Memory object or None if not found
        
    Raises:
        ValueError: If the memory is not editable (user_editable=False)
    """
    memory_item = db.query(models.Memory).filter(models.Memory.id == memory_id).first()
    if not memory_item:
        return None
    
    # GAP-5 FIX: Security check - user_editable protection
    if not memory_item.user_editable:
        logger.warning(
            f"[SECURITY] BLOCKED: Attempt to update non-editable memory ID={memory_id}, "
            f"user_editable={memory_item.user_editable}"
        )
        raise ValueError(
            f"Memory {memory_id} is not editable (user_editable=false). "
            "Use memory_update tool with appropriate permissions or contact system admin."
        )
    
    try:
        # Update basic fields
        memory_item.snippet = new_snippet
        memory_item.embedding_json = _serialize_embedding_json(
            vector_service.generate_embedding(new_snippet)
        )
        
        # Update core status if provided
        if is_core is not None:
            memory_item.is_core_fact = is_core
            
            # If setting as core but no priority specified, default to Queryable
            if is_core and core_priority is None and memory_item.core_priority == 0:
                memory_item.core_priority = 1
        
        # Update core priority if provided
        if core_priority is not None:
            memory_item.core_priority = core_priority
            
            # If setting priority > 0, ensure is_core is True
            if core_priority > 0:
                memory_item.is_core_fact = True
        
        # Update expiration if provided
        if expires_at is not None:
            memory_item.expires_at = expires_at
            
            # Update retain_until based on the new expires_at
            if expires_at is not None:
                memory_item.retain_until = expires_at + datetime.timedelta(days=GRACE_PERIOD_DAYS)
            else:
                memory_item.retain_until = None
        
        # Update last_accessed timestamp
        memory_item.last_accessed_at = datetime.datetime.utcnow()
        
        db.commit()
        db.refresh(memory_item)
        
        # CACHE INVALIDATE: Remove updated memory from cache (will be re-added on next read if high priority)
        memory_cache.invalidate(memory_id)
        logger.debug(f"[CACHE INVALIDATE] ID={memory_id}")
        
        logger.info(f"Updated memory {memory_id} (Core: {memory_item.is_core_fact}, "
                  f"Priority: {memory_item.core_priority}, Expires: {memory_item.expires_at})")
        
        return memory_item
    
    except Exception as e:
        logger.error(f"Error updating memory {memory_id}: {e}", exc_info=True)
        db.rollback()
        return None


def _consolidate_memory_after_save(db: Session, saved_fact_object: Dict[str, Any]) -> None:
    """
    Überprüft nach dem Speichern, ob der neue Fakt einen alten, allgemeineren Fakt redundant macht.
    Wird intern von save_memory_snippet aufgerufen.
    """
    predicate = saved_fact_object.get("predicate")
    subject_pet_type = saved_fact_object.get("subject_pet_type")
    subject_role = saved_fact_object.get("subject_role")
    subject_name = saved_fact_object.get("subject_name")
    chat_id = saved_fact_object.get("chat_id")

    # REGEL 1: Wenn ein Haustier einen Namen bekommt, ist der generische "owns|user|..."-Fakt redundant.
    if predicate == "name_is" and subject_pet_type in ["cat", "dog"] and subject_role == "pet":
        # Suche nach dem alten, generischen Fakt
        generic_key_to_delete = f"owns|user|{subject_pet_type}"
        generic_hash_to_delete = compute_hash(generic_key_to_delete)
        
        # Finde alle Chats des Users (für den Fall, dass der Fakt in einem anderen Chat erstellt wurde)
        fact_to_delete = db.query(models.Memory).filter(
            models.Memory.text_hash == generic_hash_to_delete
        ).first()

        if fact_to_delete:
            logger.info(
                f"KONSOLIDIERE (Regel 1): Neuer spezifischer Fakt '{saved_fact_object.get('canonical_key')}' "
                f"macht alten Fakt '{generic_key_to_delete}' (ID: {fact_to_delete.id}) redundant. Lösche alten Fakt."
            )
            db.delete(fact_to_delete)
            db.commit()
            # CACHE INVALIDATE: Remove consolidated memory from cache
            memory_cache.invalidate(fact_to_delete.id)
            logger.debug(f"[CACHE INVALIDATE] Consolidated ID={fact_to_delete.id}")
    
    # [FIX] REGEL 2: Wir entfernen die Prüfung auf 'predicate == "name_is"'.
    # Wenn wir IRGENDEINEN Fakt speichern, der einen konkreten Typ (cat/dog) UND einen Namen hat,
    # wissen wir genug, um den alten "unknown"-Eintrag zu löschen.
    if subject_pet_type in ["cat", "dog"] and subject_name:
        # Baue den Key für die "schlechtere" Version (unknown type)
        # Wir suchen nach dem spezifischen "name_is" Fakt mit "unknown" type
        redundant_unknown_key = f"name_is|pet:unknown:{subject_name.lower()}|{subject_name}"
        redundant_hash = compute_hash(redundant_unknown_key)

        fact_to_delete = db.query(models.Memory).filter(
            models.Memory.text_hash == redundant_hash
        ).first()

        if fact_to_delete:
            logger.info(
                f"KONSOLIDIERE (Regel 2): Neuer präziser Fakt '{saved_fact_object.get('canonical_key')}' "
                f"ersetzt ungenauen Fakt '{redundant_unknown_key}' (ID: {fact_to_delete.id}). Lösche alten Fakt."
            )
            db.delete(fact_to_delete)
            db.commit()
            # CACHE INVALIDATE: Remove consolidated memory from cache
            memory_cache.invalidate(fact_to_delete.id)
            logger.debug(f"[CACHE INVALIDATE] Consolidated ID={fact_to_delete.id}")


def save_raw_memory(db: Session, chat_id: int, user_input: str):
    """Speichert die rohe Benutzereingabe als Gedächtnis."""
    current_logger = logging.getLogger("janus_backend")  # Get logger inside function
    current_logger.info(f"Attempting to save raw memory for chat {chat_id}: '{user_input}'")
    saved_memory = save_memory_snippet(db, chat_id, user_input)
    if saved_memory:
        current_logger.info(f"Raw memory saved successfully: '{user_input}'")
    else:
        current_logger.warning(f"Failed to save raw memory for chat {chat_id}: '{user_input}'")
    return saved_memory


def transfer_facts_to_new_subject(db: Session, chat_id: int, old_name: str, new_name: str):
    """
    Schreibt Fakten auf den echten Namen um UND löscht dabei Widersprüche.
    """
    import json

    from backend.data.models import Memory
    
    mems = db.query(Memory).filter(Memory.chat_id == chat_id).all()
    updated = 0
    deleted = 0
    
    for m in mems:
        try:
            data = json.loads(m.snippet)
            # Nur Fakten vom alten Alias (unbekannt) anfassen
            if data.get("subject_name") == old_name.lower():
                
                # FILTER: Wenn der Fakt sagt "unbekannt" oder "nicht identifiziert", weg damit!
                fact_text = data.get("fact", "").lower() + data.get("object_value", "").lower()
                if "unbekannt" in fact_text or "nicht identifiziert" in fact_text or "unknown" in fact_text:
                    db.delete(m)
                    deleted += 1
                    continue

                # Sonst: Umschreiben auf Maggy
                data["subject_name"] = new_name.lower()
                data["canonical_key"] = data["canonical_key"].replace(old_name.lower(), new_name.lower())
                m.snippet = json.dumps(data)
                m.normalized_text = data["canonical_key"]
                updated += 1
        except Exception:
            continue
        
    db.commit()
    logger.info(f"📦 TRANSFER: {updated} Fakten migriert, {deleted} 'Unbekannt'-Fakten gelöscht.")

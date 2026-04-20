"""
Memory Tools — Unified Memory Tool Suite (Phase 5)

Standardisierte Tool-Suite für LLM-gesteuerte Memory-Operationen:
- memory_write: Speichert neue Erinnerungen
- memory_read: Liest Erinnerungen via Vektor-Suche
- memory_update: Aktualisiert bestehende Erinnerungen (mit user_editable Check)
- memory_history: Zeigt Audit-Trail einer Erinnerung

Logging Prefixe:
- [TOOL WRITE] — Skill=X, Key=Y, Priority=Z
- [TOOL READ] — Query=X, Found=Y, Filtered=Z  
- [TOOL UPDATE] — ID=X, user_editable=Y, source=Z
- [TOOL HISTORY] — ID=X, Entries=Y
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from backend.data import models
from backend.data.schemas_tools import ToolResultV1
from backend.services import vector_service
from backend.services.memory_cache import memory_cache
from backend.services.memory_enricher import apply_priority_guard, enrich_fact
from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1

logger = logging.getLogger("janus_backend")

_MEMORY_TAGS = ["memory", "recall"]


# ═══════════════════════════════════════════════════════════════════════════
# INPUT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class MemoryWriteArgs(BaseModel):
    fact: str = Field(..., min_length=1, description="Der zu speichernde Fakt")
    subject_name: Optional[str] = Field(None, description="Name des Subjekts")
    category: Optional[str] = Field(
        None,
        description="Kategorie des Fakts",
        enum=["Gesundheit", "Beziehungen", "Haustier-Details", "Vorlieben", "Beruf", "Termine", "Allgemein", "Physis", "Stil"]
    )
    priority_override: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Manuelle Priority (0.0-1.0), wird intern auf 0.95 gekappt"
    )
    ttl_days: Optional[int] = Field(None, ge=1, le=365, description="TTL in Tagen")
    tags: Optional[List[str]] = Field(None, description="Zusätzliche Tags")
    evidence: Optional[str] = Field(None, description="Zitat aus User-Nachricht als Beleg")

    @validator('priority_override')
    def validate_priority_override(cls, v):
        if v is not None and v > 0.95:
            return 0.95  # Clamp to max
        return v


class MemoryReadArgs(BaseModel):
    query: str = Field(..., min_length=1, description="Suchbegriff oder Frage")
    filter_tags: Optional[List[str]] = Field(None, description="Nur Memories mit diesen Tags")
    min_priority: float = Field(0.0, ge=0.0, le=1.0, description="Minimale Priority")
    include_expired: bool = Field(False, description="Auch abgelaufene Memories anzeigen")
    # BUG-MEM-020: Erhöht von 10 auf 25 für besseren Recall (Allergie nicht vergessen!)
    limit: int = Field(25, ge=1, le=50, description="Maximale Anzahl Ergebnisse")


class MemoryUpdateArgs(BaseModel):
    memory_id: int = Field(..., description="ID der zu aktualisierenden Memory")
    new_fact: str = Field(..., min_length=1, description="Neuer/korrigierter Fakt-Text")
    new_priority: Optional[float] = Field(None, ge=0.0, le=1.0, description="Neue Priority")


class MemoryHistoryArgs(BaseModel):
    memory_id: int = Field(..., description="ID der Memory")


# ═══════════════════════════════════════════════════════════════════════════
# HANDLER: memory_write
# ═══════════════════════════════════════════════════════════════════════════

async def handle_memory_write(
    params: Dict[str, Any],
    db: Session,
    chat_id: int,
    source_skill: str = "system.memory_write"
) -> ToolResultV1:
    """
    FLOW:
    1. Baue fact_object aus params
    2. enrich_fact(fact_object, source_skill)
    3. Falls priority_override: MIN(priority_override, 0.95)
    4. apply_priority_guard(priority, source_skill) → Cap=0.95
    5. save_memory_snippet(db, chat_id, fact_object, source_type="tool")
    6. Return: {status: "saved", memory_id, priority}
    """
    t0 = time.perf_counter()
    try:
        args = MemoryWriteArgs(**params)
        
        # 1. Build fact_object
        fact_object = {
            "fact": args.fact,
            "subject_name": args.subject_name,
            "category": args.category or "Allgemein",
            "canonical_key": _build_canonical_key(args.subject_name, args.fact),
            "evidence": args.evidence,
            "source_type": "tool",
        }
        
        # Add optional fields
        if args.tags:
            fact_object["tags"] = args.tags
            
        # 2. Enrich fact
        enriched = enrich_fact(fact_object, source_skill=source_skill)
        
        # 3. Apply priority_override if provided (internally capped at 0.95)
        if args.priority_override is not None:
            enriched["priority"] = min(args.priority_override, 0.95)
            enriched["source_skill"] = source_skill  # Override source for explicit requests
        
        # 4. Apply priority guard
        final_priority = apply_priority_guard(enriched["priority"], enriched["source_skill"])
        enriched["priority"] = final_priority
        
        # Apply TTL if provided
        if args.ttl_days is not None:
            enriched["ttl"] = args.ttl_days * 86400  # Convert days to seconds
        
        # 5. Save via Task-020 Memory-Paket (öffentliche API)
        from backend.services.memory import save_memory_snippet

        saved = save_memory_snippet(
            db=db,
            chat_id=chat_id,
            fact_object=enriched,
            source_type="tool"
        )
        
        if not saved:
            return tool_err_v1(
                "SAVE_FAILED",
                "Failed to save memory",
                tags=_MEMORY_TAGS,
                started_at=t0,
            )
        
        logger.info(
            f"[TOOL WRITE] Skill={source_skill}, Key={enriched.get('canonical_key')}, "
            f"Priority={final_priority}, ID={saved.id}"
        )
        
        return tool_ok_v1(
            {
                "operation": "saved",
                "memory_id": saved.id,
                "priority": final_priority,
                "canonical_key": enriched.get("canonical_key"),
            },
            tags=_MEMORY_TAGS,
            started_at=t0,
            primary_entity_id=str(saved.id),
        )
        
    except Exception as e:
        logger.error(f"[TOOL WRITE] Error: {e}", exc_info=True)
        return tool_err_v1("WRITE_ERROR", str(e), tags=_MEMORY_TAGS, started_at=t0)


# ═══════════════════════════════════════════════════════════════════════════
# HANDLER: memory_read
# ═══════════════════════════════════════════════════════════════════════════

async def handle_memory_read(
    params: Dict[str, Any],
    db: Session,
    chat_id: Optional[int] = None
) -> ToolResultV1:
    """
    FLOW:
    1. Vektor-Suche mit params["query"]
    2. Filter: min_priority, filter_tags, include_expired
    3. Limit: default 25 (via MemoryReadArgs schema), max 50
    4. Return: {memories: [...], total_found}
    """
    t0 = time.perf_counter()
    try:
        args = MemoryReadArgs(**params)
        
        # Build base query (no need to generate embedding here - find_most_similar_indices does it)
        now = datetime.utcnow()
        query = db.query(models.Memory)
        
        # Apply priority filter
        if args.min_priority > 0:
            query = query.filter(models.Memory.priority >= args.min_priority)
        
        # Apply expiration filter (DSGVO: default exclude expired)
        if not args.include_expired:
            query = query.filter(
                (models.Memory.expires_at.is_(None)) | (models.Memory.expires_at > now)
            )
        
        # Get candidates
        candidates = query.all()
        
        # Filter by tags if specified
        if args.filter_tags:
            filtered = []
            for mem in candidates:
                mem_tags = mem.tags or []
                if any(tag in mem_tags for tag in args.filter_tags):
                    filtered.append(mem)
            candidates = filtered
        
        # Vector similarity search
        candidate_embeddings = []
        valid_memories = []
        for mem in candidates:
            if mem.embedding_json:
                try:
                    emb = json.loads(mem.embedding_json.decode('utf-8') if isinstance(mem.embedding_json, bytes) else mem.embedding_json)
                    candidate_embeddings.append(emb)
                    valid_memories.append(mem)
                except Exception:
                    continue
        
        if valid_memories and candidate_embeddings:
            from backend.services.vector_service import find_most_similar_indices
            indices = find_most_similar_indices(
                args.query,
                candidate_embeddings,
                top_k=min(args.limit, 50),
                threshold=0.25
            )
            results = [valid_memories[i] for i in indices]
        else:
            results = []
        
        # Format output
        memories_out = []
        for mem in results:
            snippet_data = _parse_snippet(mem.snippet)
            memories_out.append({
                "memory_id": mem.id,
                "fact": snippet_data.get("fact", mem.snippet),
                "priority": mem.priority,
                "category": mem.category,
                "tags": mem.tags or [],
                "user_editable": mem.user_editable,
                "created_at": mem.created_at.isoformat() if mem.created_at else None,
                "expires_at": mem.expires_at.isoformat() if mem.expires_at else None,
            })
        
        logger.info(
            f"[TOOL READ] Query='{args.query}', Found={len(results)}, "
            f"Filtered={len(candidates) - len(results)}, Limit={args.limit}"
        )
        
        return tool_ok_v1(
            {
                "memories": memories_out,
                "total_found": len(results),
                "query": args.query,
            },
            tags=_MEMORY_TAGS,
            started_at=t0,
        )
        
    except Exception as e:
        logger.error(f"[TOOL READ] Error: {e}", exc_info=True)
        return tool_err_v1("READ_ERROR", str(e), tags=_MEMORY_TAGS, started_at=t0)


# ═══════════════════════════════════════════════════════════════════════════
# HANDLER: memory_update
# ═══════════════════════════════════════════════════════════════════════════

async def handle_memory_update(
    params: Dict[str, Any],
    db: Session,
    source_skill: str = "system.memory_update"
) -> ToolResultV1:
    """
    FLOW:
    1. Lade Memory by ID
    2. CHECK: memory.user_editable == True, sonst → {"error": "not_editable"}
    3. Nutze bestehende update_memory_snippet() oder implementiere Update-Logik
    4. Cache invalidate nach Update
    5. change_history append
    6. Return: {status: "updated", memory_id}
    """
    t0 = time.perf_counter()
    try:
        args = MemoryUpdateArgs(**params)
        
        # 1. Load memory
        memory = db.query(models.Memory).filter(models.Memory.id == args.memory_id).first()
        if not memory:
            return tool_err_v1(
                "NOT_FOUND",
                f"Memory {args.memory_id} not found",
                tags=_MEMORY_TAGS,
                started_at=t0,
            )
        
        # 2. CHECK user_editable (SECURITY CRITICAL)
        if not memory.user_editable:
            logger.warning(
                f"[TOOL UPDATE] BLOCKED: ID={args.memory_id}, user_editable=False, "
                f"source={source_skill}"
            )
            return tool_err_v1(
                "NOT_EDITABLE",
                "This memory is not editable (user_editable=false)",
                tags=_MEMORY_TAGS,
                started_at=t0,
            )
        
        # Get old snippet for history
        old_snippet = memory.snippet
        old_snippet_data = _parse_snippet(old_snippet)
        
        # 3. Update logic
        # Parse existing snippet or create new
        try:
            if old_snippet and old_snippet.startswith('{'):
                existing_data = json.loads(old_snippet)
            else:
                existing_data = {"fact": old_snippet or ""}
        except Exception:
            existing_data = {"fact": old_snippet or ""}
        
        # Update fact
        existing_data["fact"] = args.new_fact
        existing_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update priority if provided
        if args.new_priority is not None:
            guarded_priority = apply_priority_guard(args.new_priority, source_skill)
            existing_data["priority"] = guarded_priority
            memory.priority = guarded_priority
            # Update legacy fields
            memory.is_core_fact = (guarded_priority >= 0.85)
            memory.core_priority = 2 if guarded_priority >= 0.95 else (1 if guarded_priority >= 0.85 else 0)
        
        # Update snippet
        new_snippet = json.dumps(existing_data, ensure_ascii=False)
        memory.snippet = new_snippet
        
        # Update embedding
        try:
            new_embedding = vector_service.generate_embedding(args.new_fact)
            if new_embedding:
                memory.embedding_json = json.dumps(new_embedding).encode('utf-8')
        except Exception as e:
            logger.warning(f"[TOOL UPDATE] Failed to update embedding: {e}")
        
        # Update last_accessed
        memory.last_accessed_at = datetime.utcnow()
        
        # 4. Update change_history (Audit Trail)
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "update",
            "old_snippet": old_snippet_data.get("fact", old_snippet) if isinstance(old_snippet_data, dict) else old_snippet,
            "new_snippet": args.new_fact,
            "source": source_skill
        }
        
        # Initialize or append to change_history (use list() copy for SQLAlchemy to detect change)
        current_history = list(memory.change_history or [])
        if isinstance(current_history, str):
            try:
                current_history = json.loads(current_history)
            except Exception:
                current_history = []
        current_history.append(history_entry)
        memory.change_history = current_history
        
        db.commit()
        db.refresh(memory)
        
        # 5. Cache invalidate
        memory_cache.invalidate(args.memory_id)
        
        logger.info(
            f"[TOOL UPDATE] ID={args.memory_id}, user_editable=True, "
            f"source={source_skill}, history_entries={len(current_history)}"
        )
        
        return tool_ok_v1(
            {
                "operation": "updated",
                "memory_id": args.memory_id,
                "history_entries": len(current_history),
            },
            tags=_MEMORY_TAGS,
            started_at=t0,
            primary_entity_id=str(args.memory_id),
        )
        
    except Exception as e:
        logger.error(f"[TOOL UPDATE] Error: {e}", exc_info=True)
        return tool_err_v1("UPDATE_ERROR", str(e), tags=_MEMORY_TAGS, started_at=t0)


# ═══════════════════════════════════════════════════════════════════════════
# HANDLER: memory_history
# ═══════════════════════════════════════════════════════════════════════════

async def handle_memory_history(
    params: Dict[str, Any],
    db: Session
) -> ToolResultV1:
    """
    FLOW:
    1. Lade Memory by ID
    2. Lese memory.change_history (JSON-Array oder leere Liste)
    3. Return: {memory_id, history: [...], current_state}
    """
    t0 = time.perf_counter()
    try:
        args = MemoryHistoryArgs(**params)
        
        # 1. Load memory
        memory = db.query(models.Memory).filter(models.Memory.id == args.memory_id).first()
        if not memory:
            return tool_err_v1(
                "NOT_FOUND",
                f"Memory {args.memory_id} not found",
                tags=_MEMORY_TAGS,
                started_at=t0,
            )
        
        # 2. Get change_history
        history = memory.change_history or []
        if isinstance(history, str):
            try:
                history = json.loads(history)
            except Exception:
                history = []
        
        # Parse current state
        snippet_data = _parse_snippet(memory.snippet)
        
        logger.info(
            f"[TOOL HISTORY] ID={args.memory_id}, Entries={len(history)}"
        )
        
        return tool_ok_v1(
            {
                "memory_id": args.memory_id,
                "history": history,
                "current_state": {
                    "fact": snippet_data.get("fact", memory.snippet),
                    "priority": memory.priority,
                    "category": memory.category,
                    "tags": memory.tags or [],
                    "user_editable": memory.user_editable,
                    "created_at": memory.created_at.isoformat() if memory.created_at else None,
                    "updated_at": memory.last_accessed_at.isoformat() if memory.last_accessed_at else None,
                },
            },
            tags=_MEMORY_TAGS,
            started_at=t0,
            primary_entity_id=str(args.memory_id),
        )
        
    except Exception as e:
        logger.error(f"[TOOL HISTORY] Error: {e}", exc_info=True)
        return tool_err_v1("HISTORY_ERROR", str(e), tags=_MEMORY_TAGS, started_at=t0)


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _build_canonical_key(subject_name: Optional[str], fact: str) -> str:
    """Build a canonical key from subject and fact."""
    if subject_name:
        # Normalize: lowercase, replace spaces
        norm_subject = subject_name.lower().strip().replace(" ", "_")
        # Take first 5 words of fact
        fact_words = fact.lower().split()[:5]
        fact_part = "_".join(fact_words)
        return f"{norm_subject}|{fact_part}"
    else:
        # Hash the fact itself
        import hashlib
        return hashlib.sha256(fact.encode()).hexdigest()[:16]


def _parse_snippet(snippet: Optional[str]) -> Dict[str, Any]:
    """Parse a JSON snippet or return raw text as 'fact'."""
    if not snippet:
        return {"fact": ""}
    if snippet.startswith('{'):
        try:
            return json.loads(snippet)
        except Exception:
            return {"fact": snippet}
    return {"fact": snippet}


# ═══════════════════════════════════════════════════════════════════════════
# SYNC WRAPPERS (for ToolExecutor compatibility)
# ═══════════════════════════════════════════════════════════════════════════

def memory_write_tool(db: Session, **kwargs) -> ToolResultV1:
    """Sync wrapper for handle_memory_write with proper asyncio handling.
    
    Args:
        db: Database session (injected by ToolExecutor)
        **kwargs: Tool arguments (fact, subject_name, category, priority_override, ttl_days, tags, evidence, chat_id)
    """
    import asyncio
    
    # Extract chat_id from kwargs or use default
    chat_id = kwargs.pop("chat_id", 9999)
    
    # Build params dict from remaining kwargs
    params = {k: v for k, v in kwargs.items() if v is not None}
    
    try:
        loop = asyncio.get_running_loop()
        # If we're in an async context, schedule the coroutine
        future = asyncio.run_coroutine_threadsafe(handle_memory_write(params, db, chat_id), loop)
        return future.result(timeout=30)
    except RuntimeError:
        # No running loop - use our own
        return asyncio.run(handle_memory_write(params, db, chat_id))


async def memory_read_tool_async(params: Dict[str, Any], db: Session) -> ToolResultV1:
    """Async wrapper for handle_memory_read."""
    return await handle_memory_read(params, db)


def memory_read_tool(db: Session, **kwargs) -> ToolResultV1:
    """Sync wrapper for handle_memory_read.
    
    Args:
        db: Database session (injected by ToolExecutor)
        **kwargs: Tool arguments (query, filter_tags, min_priority, include_expired, limit)
    """
    import asyncio
    
    # Build params dict from kwargs, filtering None values
    params = {k: v for k, v in kwargs.items() if v is not None}
    
    try:
        loop = asyncio.get_running_loop()
        # If we're in an async context, schedule the coroutine
        future = asyncio.run_coroutine_threadsafe(handle_memory_read(params, db), loop)
        return future.result(timeout=30)
    except RuntimeError:
        # No running loop - use our own
        return asyncio.run(handle_memory_read(params, db))


async def memory_update_tool_async(params: Dict[str, Any], db: Session) -> ToolResultV1:
    """Async wrapper for handle_memory_update."""
    return await handle_memory_update(params, db)


def memory_update_tool(db: Session, **kwargs) -> ToolResultV1:
    """Sync wrapper for handle_memory_update.
    
    Args:
        db: Database session (injected by ToolExecutor)
        **kwargs: Tool arguments (memory_id, new_fact, new_priority)
    """
    import asyncio
    
    # Build params dict from kwargs, filtering None values
    params = {k: v for k, v in kwargs.items() if v is not None}
    
    try:
        loop = asyncio.get_running_loop()
        future = asyncio.run_coroutine_threadsafe(handle_memory_update(params, db), loop)
        return future.result(timeout=30)
    except RuntimeError:
        return asyncio.run(handle_memory_update(params, db))


async def memory_history_tool_async(params: Dict[str, Any], db: Session) -> ToolResultV1:
    """Async wrapper for handle_memory_history."""
    return await handle_memory_history(params, db)


def memory_history_tool(db: Session, **kwargs) -> ToolResultV1:
    """Sync wrapper for handle_memory_history.
    
    Args:
        db: Database session (injected by ToolExecutor)
        **kwargs: Tool arguments (memory_id)
    """
    import asyncio
    
    # Build params dict from kwargs, filtering None values
    params = {k: v for k, v in kwargs.items() if v is not None}
    
    try:
        loop = asyncio.get_running_loop()
        future = asyncio.run_coroutine_threadsafe(handle_memory_history(params, db), loop)
        return future.result(timeout=30)
    except RuntimeError:
        return asyncio.run(handle_memory_history(params, db))

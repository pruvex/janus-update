"""Retrieval, Diamond-Context/Slots und Token-Schätzung (extrahiert aus memory_manager, Task 020)."""
import datetime
import json
import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

import backend.data.models as models
from backend.data import database
from backend.logger_config import setup_logging
from backend.services.embedding_cache import parse_embedding
from backend.services.memory_budget import (
    MemorySlot,
    _calculate_text_similarity,
    _extract_readable_text,
    cached_memory_to_slot,
    memory_to_slot,
)
from backend.services.memory_cache import memory_cache
from backend.services.memory_observability import memory_metrics
from backend.services import vector_service
from .utils import _is_meta_noise

from .crud_service import touch_memory_snippet

setup_logging()
logger = logging.getLogger("janus_backend")


# --- Constants for Diamond Memory Architecture ---
MAX_CORE_ALWAYS_TOKENS = 400
MAX_CORE_QUERY_TOKENS = 600
MAX_STM_TOKENS = 1500
# BACKLOG-074 FIX: Increased similarity threshold from 0.35 to 0.50 to prevent context bleed
# (SEC-003-GEMINI: "Simple factual prompt" was returning unrelated Tesla content)
SIMILARITY_THRESHOLD = 0.50
VECTOR_KNAPSACK_SIMILARITY_THRESHOLD = 0.70
# Health-Injector: gleiche Schwelle wie Knapsack-Dubletten (memory_budget)
_HEALTH_JACCARD_DEDUP_THRESHOLD = 0.70


_EXTERNAL_CONTEXT_QUERY_RE = re.compile(
    r"\b(?:wetter|weather|websearch|websuche|web\s*search|internet|online|"
    r"recherchier(?:e|en)?|recherche|suche|search|aktuell(?:e|er|es|en)?|"
    r"news|nachrichten|preis(?:e)?|preise|kurs(?:e)?|schedule|fahrplan|"
    r"entfernung|distanz|route|routing|wie\s+weit|how\s+far)\b",
    re.IGNORECASE,
)
_PERSONAL_SCOPE_HINT_RE = re.compile(
    r"\b(?:meine?|mein|mir|mich|my|me|"
    r"vorlieben|praeferenzen|präferenzen|preferences|"
    r"interessen|interests|allerg(?:ie|ien)|unvertraeglichkeit(?:en)?|unverträglichkeit(?:en)?|"
    r"gesundheit|health|familie|family|wohnort|adresse|budget|kalender|termine)\b",
    re.IGNORECASE,
)


def _is_context_privacy_memory_suppressed_query(query: str) -> bool:
    """Return True when memory would be irrelevant or unsafe for current/external queries."""
    normalized = " ".join(str(query or "").strip().lower().split())
    if not normalized:
        return True
    exact_suppressed = {
        "simple factual prompt",
        "factual prompt",
        "erklaer kurz",
        "erklär kurz",
        "erkläre kurz",
    }
    if normalized in exact_suppressed:
        return True
    if _EXTERNAL_CONTEXT_QUERY_RE.search(normalized) and not _PERSONAL_SCOPE_HINT_RE.search(normalized):
        return True
    return False


def _is_generic_memory_suppressed_query(query: str) -> bool:
    """Return True for synthetic or underspecified prompts that must not receive memory context."""
    normalized = " ".join(str(query or "").strip().lower().split())
    if not normalized:
        return True
    exact_suppressed = {
        "simple factual prompt",
        "factual prompt",
        "erklaer kurz",
        "erklär kurz",
        "erkläre kurz",
    }
    return _is_context_privacy_memory_suppressed_query(query)


def _dedupe_health_memories_jaccard(memories: List[Any]) -> List[Any]:
    """Behält bevorzugt höher-priorisierte Zeilen; überspringt Fakten mit >70 % Jaccard-Ähnlichkeit zu einer behaltenen."""
    if len(memories) < 2:
        return memories
    sorted_m = sorted(
        memories,
        key=lambda m: (-(getattr(m, "priority", None) or 0.0), -(getattr(m, "id", 0) or 0)),
    )
    kept: List[Any] = []
    texts_kept: List[str] = []
    for mem in sorted_m:
        raw = getattr(mem, "snippet", None) or ""
        t = _extract_readable_text(str(raw))
        if not (t or "").strip():
            ck = getattr(mem, "canonical_key", None)
            t = str(ck).strip() if ck else ""
        if not t:
            kept.append(mem)
            continue
        if any(
            _calculate_text_similarity(t, prev) > _HEALTH_JACCARD_DEDUP_THRESHOLD
            for prev in texts_kept
        ):
            logger.info(
                "[HEALTH-INJECTOR] SKIP id=%s (Jaccard > %.0f%% vs kept fact)",
                getattr(mem, "id", "?"),
                _HEALTH_JACCARD_DEDUP_THRESHOLD * 100,
            )
            continue
        kept.append(mem)
        texts_kept.append(t)
    return kept


def estimate_tokens(text: str) -> int:
    """Grobe Schätzung der Tokenanzahl (3-4 Zeichen pro Token)."""
    return len(text) // 3


def get_last_subject_from_chat(db: Session, chat_id: int) -> Optional[Dict[str, str]]:
    """
    Ruft den subject_name und die subject_role des jüngsten Fakts für eine chat_id ab.
    Nützlich, um den Kontext aufrechtzuerhalten, wenn der aktuelle User-Prompt keinen Namen enthält.
    """
    latest_memory = db.query(models.Memory).filter(
        models.Memory.chat_id == chat_id
    ).order_by(models.Memory.created_at.desc()).first()

    if latest_memory and latest_memory.snippet:
        try:
            fact_data = json.loads(latest_memory.snippet)
            subject_name = fact_data.get('subject_name')
            subject_role = fact_data.get('subject_role')
            if subject_name and subject_role:
                return {"subject_name": subject_name, "subject_role": subject_role}
        except json.JSONDecodeError:
            logger.warning(f"Konnte Snippet {latest_memory.id} nicht als JSON parsen.")
    return None


class RetrievalContext:
    def __init__(self):
        self.core_always: List[str] = []
        self.core_queryable: List[str] = []
        self.ephemeral_active: List[str] = [] # Gültige Fakten (Termine in Zukunft)
        self.ephemeral_echo: List[str] = []   # Grace Period Fakten (Rückschau)
        self.stm_context: List[str] = []      # Normaler Kontext

    def format_for_prompt(self) -> str:
        """Baut den Kontext-String mit klaren Sektionen."""
        sections = []
        
        if self.core_always:
            sections.append("### CORE IDENTITY (ALWAYS ACTIVE)\n" + "\n".join(f"- {s}" for s in self.core_always))
            
        if self.core_queryable:
            sections.append("### RELEVANT USER TRAITS\n" + "\n".join(f"- {s}" for s in self.core_queryable))
            
        # Ephemeral mischen wir intelligent
        active_facts = self.ephemeral_active
        if active_facts:
            sections.append("### ACTIVE FACTS & PLANS\n" + "\n".join(f"- {s}" for s in active_facts))
            
        if self.ephemeral_echo:
            sections.append("### RECENTLY EXPIRED (CONTEXT ONLY)\n" + "\n".join(f"- [PAST] {s}" for s in self.ephemeral_echo))
            
        if self.stm_context:
            sections.append("### CONVERSATION MEMORY\n" + "\n".join(f"- {s}" for s in self.stm_context))
            
        if not sections:
            return ""
            
        return "INFORMATIONEN AUS DEM LANGZEITGEDÄCHTNIS:\n" + "\n\n".join(sections)


def retrieve_diamond_context(
    db: Session,
    chat_id: int,
    query: str,
    max_core_always_tokens: int = MAX_CORE_ALWAYS_TOKENS,
    max_core_query_tokens: int = MAX_CORE_QUERY_TOKENS,
    max_stm_tokens: int = MAX_STM_TOKENS,
    similarity_threshold: float = SIMILARITY_THRESHOLD
) -> str:
    """
    Diamond Standard Retrieval (CROSS-CHAT ENABLED).

    OPTIMIERT (Issue 002 + 011):
    - Single Batch-Query statt 5 separaten Queries
    - Precomputed Query-Embedding (nur 1x encode() pro Aufruf)

    Logik:
    - Core Memories & Termine (Ephemeral) werden GLOBAL (chat-übergreifend) gesucht.
    - STM & Echo (Verlauf) bleiben LOKAL (chat-spezifisch).
    """
    ctx = RetrievalContext()
    now = datetime.datetime.now()

    # ═══════════════════════════════════════════════════════════════════════════
    # ISSUE 011: Query-Embedding EINMAL berechnen (wiederverwendbar)
    # ═══════════════════════════════════════════════════════════════════════════
    query_embedding = vector_service.get_query_embedding(query)
    if query_embedding is None:
        logger.error("[RETRIEVE] Konnte Query-Embedding nicht generieren - verwende Fallback")
        # Fallback: Return empty context (graceful degrade)
        return ctx.format_for_prompt()

    # ═══════════════════════════════════════════════════════════════════════════
    # ISSUE 002: SINGLE BATCH QUERY statt 5 separaten Queries
    # Lade ALLE relevanten Memories in einem Query, partitioniere in-memory
    # ═══════════════════════════════════════════════════════════════════════════
    is_past_query = any(w in query.lower() for w in ["gestern", "war", "letzte", "damals", "vorhin"])

    # Ein Query für alle Memory-Typen (außer Echo - das ist conditional)
    all_relevant_memories = db.query(models.Memory).filter(
        or_(
            # Core-Always (Prio 2) - GLOBAL
            models.Memory.core_priority == 2,
            # Core-Queryable (Prio 1) - GLOBAL
            models.Memory.core_priority == 1,
            # Active Ephemeral (expires_at > now) - GLOBAL
            models.Memory.expires_at > now,
            # STM (chat-spezifisch, non-core, nicht expired)
            and_(
                models.Memory.chat_id == chat_id,
                models.Memory.is_core_fact == False,
                or_(
                    models.Memory.expires_at == None,
                    models.Memory.expires_at > now
                )
            )
        )
    ).all()

    # In-Memory Partitionierung (O(n) mit n = Gesamtanzahl Memories)
    core_always_objs = [m for m in all_relevant_memories if m.core_priority == 2]
    core_candidates = [m for m in all_relevant_memories if m.core_priority == 1]
    active_candidates = [m for m in all_relevant_memories if m.expires_at and m.expires_at > now]
    stm_candidates = [
        m for m in all_relevant_memories
        if m.chat_id == chat_id
        and not m.is_core_fact
        and (m.expires_at is None or m.expires_at > now)
        and m.core_priority == 0  # Nicht bereits als Core geladen
    ]

    logger.info(
        "[BATCH QUERY] Loaded %d memories total (core_always=%d, core_query=%d, ephemeral=%d, stm=%d)",
        len(all_relevant_memories), len(core_always_objs), len(core_candidates),
        len(active_candidates), len(stm_candidates)
    )

    # 1. CORE MEMORY (GLOBAL - Gilt für den User in ALLEN Chats)
    # ------------------------

    # A. Core-Always (Prio 2): Laden wir IMMER
    ctx.core_always = [m.snippet for m in core_always_objs[:15]]  # Limit 15

    # B. Core-Queryable (Prio 1): Vektorsuche mit Precomputed Embedding
    if core_candidates:
        candidate_embeddings = [parse_embedding(m.embedding_json) for m in core_candidates]
        indices = vector_service.find_most_similar_indices_precomputed(
            query_embedding, candidate_embeddings, top_k=5, threshold=0.25
        )

        used_tokens = 0
        for idx in indices:
            snippet = core_candidates[idx].snippet
            if used_tokens + estimate_tokens(snippet) < max_core_query_tokens:
                ctx.core_queryable.append(snippet)
                used_tokens += estimate_tokens(snippet)
                touch_memory_snippet(db, core_candidates[idx].id)

    # 2. EPHEMERAL MEMORY STRATEGY
    # ----------------------------

    # A. Active Ephemeral (Gültig > JETZT): Vektorsuche mit Precomputed Embedding
    if active_candidates:
        emb_active = [parse_embedding(m.embedding_json) for m in active_candidates]
        idx_active = vector_service.find_most_similar_indices_precomputed(
            query_embedding, emb_active, top_k=5, threshold=0.2
        )

        for idx in idx_active:
            ctx.ephemeral_active.append(active_candidates[idx].snippet)
            touch_memory_snippet(db, active_candidates[idx].id)

    # B. Echo Ephemeral (Abgelaufen < JETZT): LOKAL, nur bei Past-Query
    if is_past_query:
        # Echo ist conditional, daher separater Query (selten genug)
        echo_candidates = db.query(models.Memory).filter(
            models.Memory.chat_id == chat_id,
            models.Memory.expires_at < now,
            models.Memory.retain_until > now
        ).all()

        if echo_candidates:
            emb_echo = [parse_embedding(m.embedding_json) for m in echo_candidates]
            idx_echo = vector_service.find_most_similar_indices_precomputed(
                query_embedding, emb_echo, top_k=3, threshold=similarity_threshold
            )
            for idx in idx_echo:
                ctx.ephemeral_echo.append(echo_candidates[idx].snippet)

    # 3. STM RETRIEVAL (Der Rest)
    # ---------------------------
    if stm_candidates:
        emb_stm = [parse_embedding(m.embedding_json) for m in stm_candidates]
        idx_stm = vector_service.find_most_similar_indices_precomputed(
            query_embedding, emb_stm, top_k=10, threshold=similarity_threshold
        )

        stm_token_count = 0
        for idx in idx_stm:
            snippet = stm_candidates[idx].snippet
            if stm_token_count + estimate_tokens(snippet) < max_stm_tokens:
                ctx.stm_context.append(snippet)
                stm_token_count += estimate_tokens(snippet)
                touch_memory_snippet(db, stm_candidates[idx].id)

    return ctx.format_for_prompt()


def retrieve_diamond_slots(
    db: Session,
    chat_id: int,
    query: str,
    max_tokens: int = 8000,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
    identity: "Optional[Any]" = None,  # IdentitySlot (Task 013) — injected after knapsack
) -> List[MemorySlot]:
    """
    V3 (GLOBAL-UNLOCK): Liefert MemorySlots für Budget-Aware Selection.

    OPTIMIERT (Issue 002 + 011):
    - Single Batch-Query statt 5 separaten Queries
    - Precomputed Query-Embedding (nur 1x encode() pro Aufruf)

    LOGIK:
    - priority >= 0.8: GLOBAL (alle Chats) - Core Identity
    - priority 0.5-0.8: GLOBAL per Vektor-Suche
    - priority < 0.5: LOKAL (nur aktueller Chat) - STM
    - Deduplizierung: Ein Memory ID nur einmal im Ergebnis
    """
    slots: List[MemorySlot] = []
    seen_ids: set = set()  # Deduplizierung
    now = datetime.datetime.now()

    if _is_generic_memory_suppressed_query(query):
        logger.info(
            "[MEMORY SUPPRESS] Generic/underspecified query skips memory injection: %r",
            str(query or "")[:80],
        )
        return slots

    # ═══════════════════════════════════════════════════════════════════════════
    # ISSUE 011: Query-Embedding EINMAL berechnen (wiederverwendbar)
    # ═══════════════════════════════════════════════════════════════════════════
    query_embedding = vector_service.get_query_embedding(query)
    if query_embedding is None:
        logger.error("[RETRIEVE SLOTS] Konnte Query-Embedding nicht generieren - verwende Fallback")
        # Fallback: Return RAM-Cache-only results (graceful degrade)
        return slots

    # ═══════════════════════════════════════════════════════════════════════════
    # 0. EPISODIC MEMORY: Batch-Load aller Chat-Titel (ein Query, O(n) chats)
    # ═══════════════════════════════════════════════════════════════════════════
    _GHOST_CHAT_THRESHOLD = 9999
    _chat_title_map: Dict[int, str] = {}
    try:
        _chats = db.query(models.Chat.id, models.Chat.title).all()
        _chat_title_map = {
            c.id: (c.title or f"Chat #{c.id}")
            for c in _chats
            if c.id < _GHOST_CHAT_THRESHOLD
        }
    except Exception:
        logger.warning("[TEMPORAL] Failed to batch-load chat titles — falling back to defaults")

    _active_chat_title = _chat_title_map.get(chat_id, "")

    def _title_for(cid: Optional[int]) -> str:
        if cid is None:
            return _active_chat_title or "Globales Gedächtnis"
        if cid >= _GHOST_CHAT_THRESHOLD:
            return _active_chat_title or "Hintergrund-Extraktion"
        return _chat_title_map.get(cid, f"Chat #{cid}")

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. CACHE-FIRST: High-Prio Memories aus dem RAM-Cache laden (O(1), kein DB-Hit)
    # ═══════════════════════════════════════════════════════════════════════════
    cached_entries = memory_cache.get_all()
    cache_hit_count = 0
    for cached in cached_entries:
        if cached.id not in seen_ids:
            # ═══════════════════════════════════════════════════════════════════════════
            # META-NOISE FILTER: Verhindere, dass Meta-Instruktionen den LLM-Kontext erreichen
            # ═══════════════════════════════════════════════════════════════════════════
            snippet_text = str(getattr(cached, "snippet", ""))
            if _is_meta_noise(snippet_text):
                logger.info(f"[META-NOISE-REJECT] Slot id={cached.id} verworfen (Meta-Noise im Cache): {snippet_text[:80]}...")
                memory_metrics.increment("reads_meta_noise_rejected")
                continue
            # ═══════════════════════════════════════════════════════════════════════════
            slot = cached_memory_to_slot(
                cached, "core_identity",
                chat_title=_title_for(getattr(cached, "chat_id", None)),
            )
            slots.append(slot)
            seen_ids.add(cached.id)
            touch_memory_snippet(db, cached.id)
            cache_hit_count += 1
            memory_metrics.increment("reads_cache_hit")

    logger.info(
        "[CACHE-FIRST] %d high-priority slots served from RAM cache", cache_hit_count
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # ISSUE 002: SINGLE BATCH QUERY für alle verbleibenden Kategorien
    # ═══════════════════════════════════════════════════════════════════════════

    # Ein Query für High-Prio (DB-Fallback), Health, Global Vector, Ephemeral, STM
    # Ausschließen: bereits im Cache geladen (seen_ids)
    batch_exclusion_filter = ~models.Memory.id.in_(seen_ids) if seen_ids else True

    batch_memories = db.query(models.Memory).filter(
        batch_exclusion_filter,
        or_(
            # High-Prio DB-Fallback (priority >= 0.8)
            models.Memory.priority >= 0.8,
            # Health-Kategorie (Gesundheit/Health via category oder snippet)
            models.Memory.category.in_(["Gesundheit", "Health"]),
            # Globaler Keyword-Scan (Snippet): Gesundheitswarnungen ohne chat_id-Filter
            and_(
                models.Memory.snippet.isnot(None),
                or_(
                    models.Memory.snippet.ilike("%allergie%"),
                    models.Memory.snippet.ilike("%nuss%"),
                    models.Memory.snippet.ilike("%krankheit%"),
                    models.Memory.snippet.ilike("%medizin%"),
                    models.Memory.snippet.ilike("%reaktion%"),
                ),
            ),
            # Global Vector Search Range (priority 0.5-0.8)
            and_(
                models.Memory.priority >= 0.5,
                models.Memory.priority < 0.8
            ),
            # Active Ephemeral
            models.Memory.expires_at > now,
            # STM (chat-spezifisch, low priority)
            and_(
                models.Memory.chat_id == chat_id,
                models.Memory.priority < 0.5,
                models.Memory.is_core_fact == False,
                or_(
                    models.Memory.expires_at == None,
                    models.Memory.expires_at > now
                )
            )
        )
    ).all()

    # In-Memory Partitionierung nach Typ
    high_prio_fallback = [m for m in batch_memories if m.priority >= 0.8]
    health_candidates = [
        m for m in batch_memories
        if m.category in ["Gesundheit", "Health"]
        or (m.snippet and any(kw in m.snippet.lower() for kw in ["allergie", "nuss", "krankheit", "medizin", "reaktion"]))
    ]
    global_candidates = [m for m in batch_memories if 0.5 <= m.priority < 0.8]
    active_candidates = [m for m in batch_memories if m.expires_at and m.expires_at > now]
    stm_candidates = [
        m for m in batch_memories
        if m.chat_id == chat_id
        and (m.priority < 0.5 or m.priority is None)
        and not m.is_core_fact
        and (m.expires_at is None or m.expires_at > now)
    ]

    logger.info(
        "[BATCH QUERY SLOTS] Loaded %d memories (high_prio=%d, health=%d, global=%d, ephemeral=%d, stm=%d)",
        len(batch_memories), len(high_prio_fallback), len(health_candidates),
        len(global_candidates), len(active_candidates), len(stm_candidates)
    )

    # 1a. High-Prio DB-Fallback (wenn nicht im Cache)
    for mem in high_prio_fallback[:20]:  # Limit 20
        if mem.id not in seen_ids:
            # META-NOISE FILTER
            snippet_text = str(getattr(mem, "snippet", ""))
            if _is_meta_noise(snippet_text):
                logger.info(f"[META-NOISE-REJECT] Slot id={mem.id} verworfen (Meta-Noise High-Prio): {snippet_text[:80]}...")
                memory_metrics.increment("reads_meta_noise_rejected")
                continue
            slot = memory_to_slot(mem, "core_identity", chat_title=_title_for(mem.chat_id))
            slots.append(slot)
            seen_ids.add(mem.id)
            touch_memory_snippet(db, mem.id)
            memory_metrics.increment("reads_cache_miss")

    logger.info(
        "[GLOBAL-UNLOCK] Loaded %d HIGH PRIO total (%d cache, %d DB fallback)",
        cache_hit_count + len(high_prio_fallback), cache_hit_count, len(high_prio_fallback),
    )

    # 1b. HARD-FACT-INJECTOR (Gesundheit/Allergien)
    logger.info("[HEALTH-INJECTOR] === INJECTOR CALLED === chat_id=%d, query='%s...'", chat_id, query[:50])

    # Dedup Health-Fakten mit Jaccard
    _pre_dedupe = len(health_candidates)
    health_facts = _dedupe_health_memories_jaccard(health_candidates)
    if len(health_facts) < _pre_dedupe:
        logger.info(
            "[HEALTH-INJECTOR] Jaccard dedup: %d -> %d rows",
            _pre_dedupe, len(health_facts),
        )

    injected_count = 0
    for mem in health_facts:
        if mem.id not in seen_ids:
            # META-NOISE FILTER
            snippet_text = str(getattr(mem, "snippet", ""))
            if _is_meta_noise(snippet_text):
                logger.info(f"[META-NOISE-REJECT] Slot id={mem.id} verworfen (Meta-Noise Health): {snippet_text[:80]}...")
                memory_metrics.increment("reads_meta_noise_rejected")
                continue
            slot = memory_to_slot(mem, "health_mandatory", chat_title=_title_for(mem.chat_id))
            slots.append(slot)
            seen_ids.add(mem.id)
            touch_memory_snippet(db, mem.id)
            injected_count += 1

    logger.info("[HEALTH-INJECTOR] Injected %d/%d health facts", injected_count, len(health_facts))

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. GLOBAL VECTOR SEARCH (priority 0.5-0.8) - Cross-Chat
    # ═══════════════════════════════════════════════════════════════════════════
    if global_candidates:
        candidate_embeddings = [parse_embedding(m.embedding_json) for m in global_candidates]
        indices = vector_service.find_most_similar_indices_precomputed(
            query_embedding, candidate_embeddings, top_k=10, threshold=VECTOR_KNAPSACK_SIMILARITY_THRESHOLD
        )

        for idx in indices:
            mem = global_candidates[idx]
            if mem.id not in seen_ids:
                # META-NOISE FILTER
                snippet_text = str(getattr(mem, "snippet", ""))
                if _is_meta_noise(snippet_text):
                    logger.info(f"[META-NOISE-REJECT] Slot id={mem.id} verworfen (Meta-Noise Global): {snippet_text[:80]}...")
                    memory_metrics.increment("reads_meta_noise_rejected")
                    continue
                slot = memory_to_slot(mem, "global_query", chat_title=_title_for(mem.chat_id))
                slots.append(slot)
                seen_ids.add(mem.id)
                touch_memory_snippet(db, mem.id)

        logger.info(f"[GLOBAL-UNLOCK] Vector search found {len(indices)} matches globally")

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. ACTIVE EPHEMERAL (expires_at > now) - GLOBAL
    # ═══════════════════════════════════════════════════════════════════════════
    if active_candidates:
        emb_active = [parse_embedding(m.embedding_json) for m in active_candidates]
        idx_active = vector_service.find_most_similar_indices_precomputed(
            query_embedding, emb_active, top_k=5, threshold=VECTOR_KNAPSACK_SIMILARITY_THRESHOLD
        )

        for idx in idx_active:
            mem = active_candidates[idx]
            if mem.id not in seen_ids:
                # META-NOISE FILTER
                snippet_text = str(getattr(mem, "snippet", ""))
                if _is_meta_noise(snippet_text):
                    logger.info(f"[META-NOISE-REJECT] Slot id={mem.id} verworfen (Meta-Noise Ephemeral): {snippet_text[:80]}...")
                    memory_metrics.increment("reads_meta_noise_rejected")
                    continue
                slot = memory_to_slot(mem, "ephemeral", chat_title=_title_for(mem.chat_id))
                slots.append(slot)
                seen_ids.add(mem.id)
                touch_memory_snippet(db, mem.id)

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. STM (Short-Term Memory) - LOKAL nur für low priority (< 0.5)
    # ═══════════════════════════════════════════════════════════════════════════
    if stm_candidates:
        emb_stm = [parse_embedding(m.embedding_json) for m in stm_candidates]
        idx_stm = vector_service.find_most_similar_indices_precomputed(
            query_embedding, emb_stm, top_k=10, threshold=max(similarity_threshold, VECTOR_KNAPSACK_SIMILARITY_THRESHOLD)
        )

        for idx in idx_stm:
            mem = stm_candidates[idx]
            if mem.id not in seen_ids:
                # META-NOISE FILTER
                snippet_text = str(getattr(mem, "snippet", ""))
                if _is_meta_noise(snippet_text):
                    logger.info(f"[META-NOISE-REJECT] Slot id={mem.id} verworfen (Meta-Noise STM): {snippet_text[:80]}...")
                    memory_metrics.increment("reads_meta_noise_rejected")
                    continue
                slot = memory_to_slot(mem, "stm", chat_title=_title_for(mem.chat_id))
                slots.append(slot)
                seen_ids.add(mem.id)
                touch_memory_snippet(db, mem.id)

    logger.info(
        "[MEMORY RETRIEVE] chat_id=%d, query_len=%d, slots=%d (global unlock active)",
        chat_id, len(query), len(slots)
    )

    # ── Identity Preload (Task 013) ───────────────────────────────────────────
    # Note: this injection point is PRE-budget (slots returned here go through
    # select_slots_by_budget in the orchestrator). The orchestrator also calls
    # ensure_identity_in_slots AFTER select_slots_by_budget to make the slot
    # budget-exempt.  Injecting here as well ensures the identity fact is also
    # visible in any code path that uses retrieve_diamond_slots directly.
    if identity is not None:
        try:
            from backend.services.memory_identity import ensure_identity_in_slots
            slots = ensure_identity_in_slots(slots, identity)
        except Exception as _id_err:
            logger.warning("[IDENTITY PRELOAD] inject failed in retrieve_diamond_slots: %s", _id_err)
    # ─────────────────────────────────────────────────────────────────────────

    return slots


def get_memories_for_management(db: Session) -> List[models.Memory]:
    """
    Holt alle Memories für das Frontend, sortiert nach Wichtigkeit (Diamond Standard).
    Sortierung: Core Identity (2) -> Core Detail (1) -> General (0) -> Erstellungsdatum
    
    Args:
        db: Database session
        
    Returns:
        List[Memory]: List of Memory objects sorted by priority and creation date
    """
    return db.query(models.Memory).order_by(
        models.Memory.core_priority.desc().nulls_last(),
        models.Memory.is_core_fact.desc(),
        models.Memory.created_at.desc()
    ).all()


def get_all_memories(db: Session):
    """DEPRECATED: Use retrieve_diamond_context or get_memories_for_management instead"""
    return db.query(database.Memory).all()


def find_similar_memory_snippet(db: Session, query_text: str) -> Optional[str]:
    """Legacy wrapper: returns the most similar memory snippet text or None."""
    memories = get_all_memories(db)
    similar_memories = vector_service.find_similar_snippets(query_text, memories)
    if not similar_memories:
        return None
    return getattr(similar_memories[0], "snippet", None) if not isinstance(similar_memories[0], str) else similar_memories[0]


def get_all_facts(db: Session) -> List[models.Memory]:  # Verwende models.Memory
    """Gibt alle Erinnerungen zurück, die als Fakten und nicht als Fragen oder rohe Eingaben gelten."""
    return (
        db.query(database.Memory)
        .filter(  # Verwende models.Memory
            ~database.Memory.snippet.startswith("wie "),
            ~database.Memory.snippet.startswith("was "),
            ~database.Memory.snippet.startswith("wer "),
            ~database.Memory.snippet.startswith("wo "),
            ~database.Memory.snippet.startswith("wann "),
            ~database.Memory.snippet.startswith("warum "),
        )
        .all()
    )

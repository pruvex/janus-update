"""
Memory V2 Budget-Aware Context Selection
Diamond Standard - Phase 4 Implementation

Ersetzt String-basierte Context-Injection durch Budget-Aware MemorySlot-Selection.
"""

import datetime as _dt
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from backend.data import models

logger = logging.getLogger("janus_backend")

# Feature-Flag für sofortigen Rollback auf alten Code
MEMORY_V2_ENABLED = os.getenv("MEMORY_V2_ENABLED", "true").lower() == "true"


@dataclass
class MemorySlot:
    """Repräsentiert einen einzelnen Memory-Slot mit Budget-relevanten Metadaten."""
    text: str
    tokens: int
    tier: Literal["core_always", "core_query", "ephemeral", "stm"]
    priority: float
    memory_id: int
    tags: List[str]
    timestamp: str = ""
    chat_title: str = ""


class TokenBudget:
    """Token-Budget-Verwaltung mit Ratio-Allokation."""
    
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
        self.response_buffer = response_buffer
        self.used_memory = 0
        self.selected_count = 0
        self.skipped_count = 0

    @property
    def remaining_memory(self) -> int:
        return self.memory_budget - self.used_memory

    def allocate(self, tokens: int) -> bool:
        """Allokiert Tokens wenn möglich, sonst False."""
        if self.remaining_memory >= tokens:
            self.used_memory += tokens
            self.selected_count += 1
            return True
        self.skipped_count += 1
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Gibt Budget-Statistiken zurück."""
        return {
            "max_tokens": self.available + self.response_buffer,
            "available": self.available,
            "system_budget": self.system_budget,
            "memory_budget": self.memory_budget,
            "history_budget": self.history_budget,
            "used_memory": self.used_memory,
            "remaining_memory": self.remaining_memory,
            "selected_count": self.selected_count,
            "skipped_count": self.skipped_count,
        }


# --- Tiktoken Singleton (lazy init, graceful fallback) ---
_tiktoken_encoder: Optional[object] = None
_tiktoken_init_done: bool = False


def _get_tiktoken_encoder():
    """Lazy-Init tiktoken cl100k_base. Fallback auf None bei ImportError."""
    global _tiktoken_encoder, _tiktoken_init_done
    if _tiktoken_init_done:
        return _tiktoken_encoder
    _tiktoken_init_done = True
    try:
        import tiktoken
        _tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
        logger.info("[BUDGET] tiktoken cl100k_base encoder geladen")
    except Exception as e:
        logger.warning(f"[BUDGET] tiktoken nicht verfügbar, Fallback auf Heuristik: {e}")
        _tiktoken_encoder = None
    return _tiktoken_encoder


def estimate_tokens(text: str) -> int:
    """Präzise Token-Zählung via tiktoken, Fallback auf len//4."""
    enc = _get_tiktoken_encoder()
    if enc is not None:
        return max(1, len(enc.encode(text)))
    return max(1, len(text) // 4)


_GERMAN_MONTHS = [
    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


def _utc_to_local(dt_utc: _dt.datetime) -> _dt.datetime:
    """Bulletproof UTC→local conversion via C-level localtime().

    Works reliably on Windows, Linux, macOS, Docker, and WSL — even when
    Python's datetime.astimezone() fails to detect the system timezone.
    Handles DST transitions correctly.
    """
    import time as _time
    import calendar as _cal
    epoch = _cal.timegm(dt_utc.timetuple())
    local_struct = _time.localtime(epoch)
    return _dt.datetime(*local_struct[:6])


def format_temporal_stamp(dt: Optional[_dt.datetime]) -> str:
    """Human-readable German timestamp in LOCAL time.

    DB stores UTC (naive, via datetime.utcnow). We convert via the
    C-level localtime() for bulletproof timezone handling on all platforms.
    """
    if dt is None:
        return ""
    # Strip tzinfo — we always treat the raw value as UTC
    naive_utc = dt.replace(tzinfo=None) if dt.tzinfo else dt
    local_dt = _utc_to_local(naive_utc)
    now = _dt.datetime.now()

    time_str = local_dt.strftime("%H:%M")
    if local_dt.date() == now.date():
        return f"Heute um {time_str}"
    if local_dt.date() == (now - _dt.timedelta(days=1)).date():
        return f"Gestern um {time_str}"
    month = _GERMAN_MONTHS[local_dt.month] if local_dt.month <= 12 else str(local_dt.month)
    return f"{local_dt.day}. {month} {local_dt.year} um {time_str}"


def cached_memory_to_slot(cached: Any, tier: str, chat_title: str = "") -> MemorySlot:
    """Konvertiert CachedMemory (RAM-Cache) zu MemorySlot ohne DB-Zugriff."""
    text = _extract_readable_text(cached.snippet or "")
    tokens = estimate_tokens(text)
    tags = list(cached.tags) if cached.tags else []
    ts = format_temporal_stamp(getattr(cached, "created_at", None))
    return MemorySlot(
        text=text,
        tokens=tokens,
        tier=tier,
        priority=cached.priority,
        memory_id=cached.id,
        tags=[t.strip() for t in tags if t],
        timestamp=ts,
        chat_title=chat_title or "Globales Gedächtnis",
    )


def memory_to_slot(memory: models.Memory, tier: str, chat_title: str = "") -> MemorySlot:
    """Konvertiert DB Memory zu MemorySlot."""
    # Priorität aus V2-Feldern oder Legacy core_priority mappen
    if hasattr(memory, 'priority') and memory.priority is not None:
        priority = memory.priority
    elif hasattr(memory, 'core_priority') and memory.core_priority:
        # Legacy mapping
        priority_map = {2: 0.95, 1: 0.75, 0: 0.50}
        priority = priority_map.get(memory.core_priority, 0.50)
    else:
        priority = 0.50

    # Tags aus V2-Feldern oder leer
    tags = []
    if hasattr(memory, 'tags') and memory.tags:
        tags = memory.tags.split(',') if isinstance(memory.tags, str) else memory.tags

    # GAP-5 FIX: Extrahiere lesbaren Text aus JSON-Snippets
    raw_snippet = memory.snippet or ""
    text = _extract_readable_text(raw_snippet)
    tokens = estimate_tokens(text)

    ts = format_temporal_stamp(getattr(memory, "created_at", None))

    return MemorySlot(
        text=text,
        tokens=tokens,
        tier=tier,  # type: ignore
        priority=priority,
        memory_id=memory.id,
        tags=[t.strip() for t in tags if t],
        timestamp=ts,
        chat_title=chat_title or "Globales Gedächtnis",
    )


def _extract_readable_text(snippet: str) -> str:
    """Extrahiert lesbaren Text aus JSON-Snippet oder gibt Plain-Text zurück."""
    if not snippet:
        return ""
    stripped = snippet.strip()
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            # Priorität: evidence > fact > canonical_key
            for key in ("evidence", "fact", "canonical_key"):
                val = data.get(key, "")
                if val and len(str(val)) > 3:
                    return str(val)
            return stripped
        except (json.JSONDecodeError, TypeError):
            return stripped
    return stripped


_GHOST_CHAT_TITLES = frozenset({
    "", "Hintergrund-Extraktion", "Globales Gedächtnis",
})

_RELATION_TAGS = frozenset({
    "social", "contact", "beziehungen", "familie", "freund",
    "relationship", "partner", "kollege",
})


def _has_real_chat_title(slot: MemorySlot) -> bool:
    return bool(slot.chat_title and slot.chat_title not in _GHOST_CHAT_TITLES)


def _is_relation_slot(slot: MemorySlot) -> bool:
    """True if the slot describes a person/relationship fact."""
    if any(t.lower() in _RELATION_TAGS for t in (slot.tags or [])):
        return True
    _text = slot.text.lower()
    return "freund" in _text or "bruder" in _text or "schwester" in _text or "des nutzers" in _text


def _extract_proper_names(text: str) -> set:
    """Extract capitalized words that look like proper names."""
    import re
    return {
        w.lower() for w in re.findall(r'\b[A-ZÄÖÜ][a-zäöüß]{2,}\b', text)
        if w.lower() not in {"user", "nutzer", "freund", "bruder", "schwester",
                             "ehefrau", "ehemann", "partner", "mutter", "vater",
                             "heute", "gestern", "fakt", "chat", "globales"}
    }


def _calculate_text_similarity(text1: str, text2: str) -> float:
    """
    BUG-MEM-020: Einfache Token-basierte Ähnlichkeit für Dubletten-Erkennung.
    Gibt Ähnlichkeit zwischen 0.0 und 1.0 zurück.
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalisiere: lowercase, nur Buchstaben/Zahlen
    def normalize(t: str) -> set:
        return set(
            ''.join(c for c in word.lower() if c.isalnum())
            for word in t.split()
            if len(word) > 2  # Ignoriere sehr kurze Wörter
        )
    
    tokens1 = normalize(text1)
    tokens2 = normalize(text2)
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def _is_placeholder_memory_slot(slot: MemorySlot) -> bool:
    text = str(getattr(slot, "text", "") or "").casefold()
    if not text:
        return False
    placeholder_markers = (
        "name des testprojekts",
        "projektname",
        "chat titel platzhalter",
        "chat-titel platzhalter",
    )
    if not any(marker in text for marker in placeholder_markers):
        return False
    concrete_markers = ("phoenix",)
    return not any(marker in text for marker in concrete_markers)


def select_slots_by_budget(
    slots: List[MemorySlot],
    budget: TokenBudget,
    min_slot_tokens: int = 50
) -> List[MemorySlot]:
    """
    Knapsack-Algorithmus für Memory-Selection.
    
    Kritischer Unterschied zu Greedy:
    - continue statt break bei Übergröße
    - Kleinere Slots können noch reinpassen
    
    BUG-MEM-020: Dubletten-Prüfung (>80% Ähnlichkeit = überspringen)
    """
    logger.info(
        "[KNAPSACK] Starting selection: %d candidates, budget=%d tk",
        len(slots), budget.memory_budget
    )

    # Sortiere nach Priorität (absteigend), dann nach Größe (aufsteigend)
    sorted_slots = sorted(
        slots,
        key=lambda s: (-s.priority, s.tokens)
    )

    selected: List[MemorySlot] = []
    skipped: List[MemorySlot] = []

    # BUG-MEM-020: Dubletten-Tracking (Origin-Focus)
    _DUPLICATE_SIMILARITY_THRESHOLD = 0.70

    for slot in sorted_slots:
        if _is_placeholder_memory_slot(slot):
            skipped.append(slot)
            logger.info(
                "[KNAPSACK] Skipping placeholder memory slot ID=%s: %s",
                slot.memory_id,
                slot.text[:80],
            )
            continue

        if budget.remaining_memory < min_slot_tokens:
            logger.debug(f"[KNAPSACK] Budget zu klein für weitere Slots ({budget.remaining_memory} < {min_slot_tokens})")
            break

        # Dubletten-Prüfung: Origin-aware + Ghost-Chat-aware.
        # When a near-duplicate is found, the slot with the higher priority
        # stays (sort order guarantees it's `existing`), but we always adopt:
        #   a) the OLDEST timestamp (lowest memory_id = first mention)
        #   b) the REAL chat title over a ghost title
        is_duplicate = False
        _slot_is_relation = _is_relation_slot(slot)
        _slot_names = _extract_proper_names(slot.text) if _slot_is_relation else set()

        for existing in selected:
            similarity = _calculate_text_similarity(slot.text, existing.text)

            # Relation slots about the SAME person get a much lower threshold:
            # "Chris ist Freund des Nutzers" vs "Chris heißt Christoph"
            # share the name "Chris" but have low Jaccard.
            _is_same_person_dup = False
            if (
                similarity <= _DUPLICATE_SIMILARITY_THRESHOLD
                and _slot_is_relation
                and _is_relation_slot(existing)
            ):
                _existing_names = _extract_proper_names(existing.text)
                if _slot_names & _existing_names:
                    _is_same_person_dup = True

            if similarity > _DUPLICATE_SIMILARITY_THRESHOLD or _is_same_person_dup:
                # (a) Origin timestamp: lower ID = older = origin fact
                if slot.memory_id < existing.memory_id and slot.timestamp:
                    existing.timestamp = slot.timestamp
                    logger.debug(
                        "[KNAPSACK] Origin-swap: ID=%d adopted older timestamp from ID=%d",
                        existing.memory_id, slot.memory_id,
                    )
                # (b) Real chat title beats ghost title
                if not _has_real_chat_title(existing) and _has_real_chat_title(slot):
                    existing.chat_title = slot.chat_title
                    if not existing.timestamp and slot.timestamp:
                        existing.timestamp = slot.timestamp
                    logger.info(
                        "[KNAPSACK] Ghost-swap: ID=%d inherited title '%s' from ID=%d",
                        existing.memory_id, slot.chat_title, slot.memory_id,
                    )
                is_duplicate = True
                _reason = "same-person" if _is_same_person_dup else f"jaccard={similarity:.2f}"
                logger.debug(
                    f"[KNAPSACK] Skipping duplicate slot ID={slot.memory_id} "
                    f"({_reason} with ID={existing.memory_id})"
                )
                skipped.append(slot)
                break
        if is_duplicate:
            continue

        if budget.allocate(slot.tokens):
            selected.append(slot)
            logger.debug(f"[KNAPSACK] Selected slot ID={slot.memory_id}, p={slot.priority:.2f}, tk={slot.tokens}")
        else:
            # Überspringe großen Slot, probiere nächsten (Knapsack-Prinzip)
            skipped.append(slot)
            logger.debug(f"[KNAPSACK] Skipping oversized slot ID={slot.memory_id}, p={slot.priority:.2f}, tk={slot.tokens}, remaining={budget.remaining_memory}")
            continue

    # Logging-Summary
    total_tokens = sum(s.tokens for s in selected)
    logger.info(
        f"[BUDGET] Selected {len(selected)}/{len(slots)} slots, "
        f"skipped {len(skipped)} (budget: {total_tokens}/{budget.memory_budget} tk)"
    )

    return selected


def _format_slot_line(s: MemorySlot) -> str:
    """Episodic format: includes timestamp and chat origin when available."""
    if s.timestamp and s.chat_title:
        return f"| GESPEICHERT AM: {s.timestamp} | IM CHAT: '{s.chat_title}' | FAKT: {s.text}"
    if s.timestamp:
        return f"| GESPEICHERT AM: {s.timestamp} | FAKT: {s.text}"
    return f"- {s.text}"


def format_memory_context(slots: List[MemorySlot]) -> str:
    """Formatiert selected Slots zu kontextuellen String-Block mit episodischen Metadaten."""
    if not slots:
        return ""

    # Gruppiere nach Tier (robust mit setdefault für unbekannte Tiers)
    tiers: Dict[str, List[MemorySlot]] = {
        "core_always": [],
        "core_identity": [],
        "core_query": [],
        "global_query": [],
        "ephemeral": [],
        "stm": []
    }

    tier_labels = {
        "core_always": "### CORE IDENTITY (ALWAYS ACTIVE)",
        "core_identity": "### CORE IDENTITY",
        "core_query": "### RELEVANT USER TRAITS",
        "global_query": "### GLOBALE ERINNERUNGEN",
        "ephemeral": "### ACTIVE FACTS & PLANS",
        "stm": "### CONVERSATION MEMORY"
    }

    for slot in slots:
        tiers.setdefault(slot.tier, []).append(slot)

    sections = []
    _tier_order = ["core_always", "core_identity", "global_query", "core_query", "ephemeral", "stm"]

    for tier_key in _tier_order:
        tier_slots = tiers.get(tier_key)
        if tier_slots:
            lines = [_format_slot_line(s) for s in tier_slots]
            label = tier_labels.get(tier_key, f"### {tier_key.upper()}")
            sections.append(f"{label}\n" + "\n".join(lines))

    total_tokens = sum(s.tokens for s in slots)
    logger.info(f"[CONTEXT V2] Built context: {len(slots)} slots, ~{total_tokens} tokens")

    return "\n\n".join(sections) if sections else ""


# =============================================================================
# DETERMINISTIC FACT COUPONS — Diamond Gold Final Layer
# =============================================================================

def extract_fact_coupons(slots: List[MemorySlot], user_query: str) -> List[str]:
    """
    Generiert deterministische Fact-Coupons für kritische Fakten.
    
    Coupons werden generiert für:
    1. Gesundheits-Informationen (immer)
    2. Abneigungen bei Vorlieben-Fragen (Query-Intent-Erkennung)
    3. High-Priority Slots (priority >= 0.70) mit Query-Overlap
    
    Args:
        slots: Selektierte MemorySlots nach Knapsack
        user_query: Roh-User-Query für Intent-Erkennung
        
    Returns:
        Liste von Coupon-Strings (jeder ist ein enforcebarer Fakt)
    """
    coupons: List[str] = []
    query_lower = user_query.lower()

    # Intent-Erkennung für Vorlieben/Trinken/Essen
    _preference_intents = {
        "trink": ["getränk", "trinken", "tee", "kaffee", "wasser", "trinke"],
        "esse": ["essen", "food", "gericht", "isst", "mahl"],
        "vorliebe": ["magst", "vorliebe", "liebling", "mögen", "geschmack"],
        "allergie": ["allergie", "unverträglich", "verträgst"],
    }

    _is_preference_query = any(
        keyword in query_lower for keywords in _preference_intents.values() for keyword in keywords
    )

    # Health-Risiko-Keywords: Nur wenn die Query potenziell gefährlich
    # für jemanden mit einer Allergie/Erkrankung sein könnte.
    _health_risk_triggers = (
        "essen", "esse", "isst", "trinken", "trinke", "trink",
        "kochen", "koch", "backen", "back", "rezept", "zubereite",
        "restaurant", "bestell", "snack", "naschen", "probier",
        "kaufen", "kauf", "einkauf", "geschenk", "mitbring",
        "hunger", "durst", "appetit", "mahl", "gericht",
        "zutat", "inhalt", "enthält", "verträg",
        "allergi", "unverträg", "gesundheit", "medikament",
        "nuss", "milch", "gluten", "laktose", "soja",
    )
    _is_health_relevant = any(t in query_lower for t in _health_risk_triggers)

    # Negative-Preference Keywords für Coupon-Generierung
    _negative_markers = ["hasst", "mag nicht", "verabscheut", "nicht leiden",
                         "ekelt", "trinkt kein", "isst kein", "verträgt kein",
                         "abneigung", "hass", "nicht ausstehen"]

    for slot in slots:
        slot_lower = slot.text.lower()
        tags_lower = [t.lower() for t in slot.tags]

        # COUPON-TYP 1: Gesundheit — nur bei risiko-relevanter Query.
        # Bei sicheren Queries (Teddybär, Uhrzeit) bleibt der Fakt im
        # normalen Kontext, wird aber KEIN erzwungener Coupon.
        if "gesundheit" in tags_lower or any(g in slot_lower for g in ["allergie", "unverträglich", "krankheit", "medikament"]):
            if _is_health_relevant:
                coupons.append(f"[HEALTH] {slot.text}")
            else:
                logger.debug(
                    "[COUPON SKIP] Health fact stays in context (no risk trigger): %s",
                    slot.text[:60],
                )
            continue
        
        # COUPON-TYP 2: Abneigungen bei Vorlieben-Fragen
        if _is_preference_query:
            # Prüfe ob Slot eine Abneigung enthält
            if any(marker in slot_lower for marker in _negative_markers):
                # Coupon mit expliziter Wahrheitspflicht
                coupons.append(f"[MUST-MENTION-NEGATIVE] {slot.text}")
                continue
            # Auch bei High-Prio Vorlieben bei Preference-Queries
            if slot.priority >= 0.70 and "vorlieben" in tags_lower:
                coupons.append(f"[PREFERENCE] {slot.text}")
                continue
        
        # COUPON-TYP 3: High-Priority (>=0.70) mit Query-Overlap
        if slot.priority >= 0.70:
            # Extrahiere Keywords aus dem Query (min 4 Buchstaben)
            query_keywords = set(
                w for w in query_lower.split() 
                if len(w) >= 4 and w.isalpha()
            )
            # Prüfe auf Überlappung mit Slot-Text
            slot_words = set(
                w for w in slot_lower.split() 
                if len(w) >= 4 and w.isalpha()
            )
            overlap = query_keywords & slot_words
            
            if overlap:
                # Coupon nur bei semantischem Overlap
                coupons.append(f"[HIGH-PRIORITY-OVERLAP] {slot.text}")
    
    return coupons


def format_fact_coupons(coupons: List[str]) -> str:
    """
    Formatiert Coupons zu einem deterministischen System-Block.
    
    Dieser Block wird als separate System-Message eingefügt,
    direkt vor der User-Message (höchste Aufmerksamkeit).
    """
    if not coupons:
        return ""
    
    lines = [
        "!!! FACT COUPONS — RELEVANZ-PFLICHT !!!",
        "Die folgenden Fakten sind gesicherte Wahrheiten über den Nutzer.",
        "Erwähne sie NUR, wenn sie einen DIREKTEN Bezug zur aktuellen Frage haben.",
        ""
    ]

    for i, coupon in enumerate(coupons, 1):
        lines.append(f"{i}. {coupon}")

    lines.extend([
        "",
        "REGELN:",
        "1. NICHT LEUGNEN: Behaupte NIEMALS, diese Informationen nicht zu haben.",
        "2. RELEVANZ-FILTER: Erwähne einen Coupon nur, wenn er zur Frage passt.",
        "   Eine Allergie gehört in Antworten über Essen/Kochen/Geschenke,",
        "   aber NICHT in Antworten über Spielzeug, Uhrzeit oder Wetter.",
        "3. Bei Zweifel: Lieber erwähnen als verschweigen (Sicherheit > Kürze).",
    ])
    
    return "\n".join(lines)

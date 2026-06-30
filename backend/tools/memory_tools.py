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
import re
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
MEMORY_READ_SIMILARITY_THRESHOLD = 0.65


_SENSITIVE_MEMORY_WRITE_RE = re.compile(
    r"\b(?:passwort|password|secret|token|api[-_\s]?key|credential|zugangsdaten)\b"
    r".{0,80}\b[A-Za-z0-9._~+/=-]*(?:SECRET|TOKEN|KEY|PASS)[A-Za-z0-9._~+/=-]*\b|"
    r"\b(?:abc123SECRET|SECRET-[A-Za-z0-9._~+/=-]+)\b",
    re.IGNORECASE,
)
_NO_DURABLE_MEMORY_RE = re.compile(
    r"\b(?:speichere|speicher|merk(?:e)?|remember|save)\b"
    r".{0,80}\b(?:nicht|not|no)\b.{0,80}\b(?:dauerhaft|permanent|langfristig|long[-\s]?term|memory|gedaechtnis|gedächtnis)\b|"
    r"\b(?:nicht|not|no)\b.{0,80}\b(?:dauerhaft|permanent|langfristig|long[-\s]?term)\b",
    re.IGNORECASE,
)
_CONTACT_QUERY_SCOPE_PATTERNS = [
    re.compile(r"\bwas\s+mag(?:en)?\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bwas\s+wei(?:ß|ss)t\s+du\s+über\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bich\s+will\s+mit\s+(.+)$", re.IGNORECASE),
    re.compile(r"\b(?:vorlieben|praeferenzen|prÃ¤ferenzen|interessen|hobbys)\s+von\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bmein(?:e|en)?\s+(?:freund|freundin)\s+(.+)$", re.IGNORECASE),
    re.compile(r"\bkorr(?:e|i)ktur:?\s+(.+)$", re.IGNORECASE),
    re.compile(
        r"^\s*([a-zäöüß][\wäöüß-]*(?:\s+[a-zäöüß][\wäöüß-]*){0,2})\s+"
        r"(?:liebt|mag|ist|wohnt|hasst|verbringt|baut)\b",
        re.IGNORECASE,
    ),
]
_CONTACT_QUERY_STOPWORDS = {
    "als",
    "am",
    "an",
    "bei",
    "bin",
    "das",
    "dem",
    "den",
    "der",
    "die",
    "du",
    "ein",
    "eine",
    "er",
    "essen",
    "fuer",
    "für",
    "geht",
    "gehen",
    "heute",
    "ich",
    "im",
    "in",
    "ist",
    "mag",
    "mit",
    "nicht",
    "oder",
    "sie",
    "und",
    "was",
    "weiss",
    "weißt",
    "wohnt",
    "zu",
    "zum",
}
_CONTACT_QUERY_CONTEXT_TERMS = {
    "haustier",
    "haustiere",
    "hund",
    "hunde",
    "katze",
    "katzen",
}
_EXPLICIT_CONTACT_SUBJECT_RE = re.compile(
    r"^\s*([a-zäöüß][\wäöüß-]*(?:\s+[a-zäöüß][\wäöüß-]*){0,2})\s+"
    r"(?:liebt|mag|ist|wohnt|hasst|verbringt|baut)\b",
    re.IGNORECASE,
)
_EXPLICIT_CONTACT_SUBJECT_STOPWORDS = {
    "ja",
    "genau",
    "richtig",
    "korrekt",
    "stimmt",
    "yes",
    "und",
    "oder",
    "er",
    "sie",
    "es",
    "ich",
    "du",
}


def _is_sensitive_memory_write_request(text: Any) -> bool:
    return bool(_SENSITIVE_MEMORY_WRITE_RE.search(str(text or "")))


def _is_no_durable_memory_request(text: Any) -> bool:
    return bool(_NO_DURABLE_MEMORY_RE.search(str(text or "")))


def _normalize_memory_search_text(text: Any) -> str:
    normalized = str(text or "").casefold()
    normalized = normalized.replace("ü", "ue").replace("ä", "ae").replace("ö", "oe").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def _memory_lexical_match_score(mem: models.Memory, query: str) -> int:
    query_norm = _normalize_memory_search_text(query)
    if not query_norm:
        return 0
    haystack = " ".join(
        _normalize_memory_search_text(part)
        for part in (
            mem.snippet,
            mem.category,
            mem.canonical_key,
            " ".join(mem.tags or []),
        )
    )
    query_terms = [term for term in query_norm.split() if len(term) >= 3]
    if not query_terms:
        return 0
    return sum(1 for term in query_terms if term in haystack)


def _normalize_memory_search_text(text: Any) -> str:
    normalized = str(text or "").casefold()
    normalized = (
        normalized
        .replace("ü", "ue")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ß", "ss")
        .replace("Ã¼", "ue")
        .replace("Ã¤", "ae")
        .replace("Ã¶", "oe")
        .replace("ÃŸ", "ss")
    )
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def _extract_explicit_lead_contact_subject(text: Any) -> Optional[str]:
    match = _EXPLICIT_CONTACT_SUBJECT_RE.search(str(text or "").strip())
    if not match:
        return None
    subject = str(match.group(1) or "").strip()
    tokens = [token.casefold() for token in subject.split() if token]
    if not tokens or any(token in _EXPLICIT_CONTACT_SUBJECT_STOPWORDS for token in tokens):
        return None
    return subject.strip() or None


def _rebind_explicit_contact_subject(
    *,
    fact: str,
    subject_name: Optional[str],
    original_user_text: Optional[str],
) -> tuple[str, Optional[str]]:
    def _tokenize_subject(value: Optional[str]) -> list[str]:
        return [token for token in _normalize_memory_search_text(value).split() if token]

    def _is_more_specific_subject(candidate: Optional[str], explicit: str) -> bool:
        candidate_tokens = _tokenize_subject(candidate)
        explicit_tokens = _tokenize_subject(explicit)
        if not candidate_tokens or not explicit_tokens:
            return False
        if len(candidate_tokens) <= len(explicit_tokens):
            return False
        return candidate_tokens[: len(explicit_tokens)] == explicit_tokens

    explicit_subject = _extract_explicit_lead_contact_subject(original_user_text)
    if not explicit_subject:
        return fact, subject_name

    rebound_subject = subject_name or explicit_subject
    if not _is_more_specific_subject(subject_name, explicit_subject):
        rebound_subject = explicit_subject

    rebound_fact = str(fact or "").strip()
    if rebound_fact:
        fact_match = _EXPLICIT_CONTACT_SUBJECT_RE.search(rebound_fact)
        if fact_match:
            original_prefix = str(fact_match.group(1) or "").strip()
            if (
                original_prefix
                and _normalize_memory_search_text(original_prefix) != _normalize_memory_search_text(explicit_subject)
                and not _is_more_specific_subject(original_prefix, explicit_subject)
            ):
                rebound_fact = rebound_fact.replace(original_prefix, explicit_subject, 1)
    return rebound_fact, rebound_subject


def _extract_contact_query_subject_aliases(db: Session, query: str) -> set[str]:
    query_norm = _normalize_memory_search_text(query)
    if not query_norm:
        return set()

    query_tokens = {token for token in query_norm.split() if len(token) >= 3}
    aliases: set[str] = set()

    scoped_fragments: List[str] = []
    normalized_scope_patterns = [
        re.compile(r"\bwas\s+mag(?:en)?\s+(.+)$"),
        re.compile(r"\bwas\s+weisst\s+du\s+ueber\s+(.+)$"),
        re.compile(r"\bich\s+will\s+mit\s+(.+)$"),
        re.compile(r"\b(?:vorlieben|praeferenzen|interessen|hobbys)\s+von\s+(.+)$"),
        re.compile(r"\bmein(?:e|en)?\s+(?:freund|freundin)\s+(.+)$"),
        re.compile(r"\bkorr(?:e|i)ktur\s+(.+)$"),
        re.compile(
            r"^\s*([a-z][a-z0-9-]*(?:\s+[a-z][a-z0-9-]*){0,2})\s+"
            r"(?:liebt|mag|ist|wohnt|hasst|verbringt|baut)\b"
        ),
    ]
    for pattern in normalized_scope_patterns:
        match = pattern.search(query_norm)
        if not match:
            continue
        for part in re.split(r"\bund\b|,|/|;", match.group(1)):
            tokens: List[str] = []
            for token in part.split():
                if token in _CONTACT_QUERY_STOPWORDS or token in _CONTACT_QUERY_CONTEXT_TERMS:
                    break
                if len(token) < 3:
                    continue
                tokens.append(_normalize_contact_query_fragment_alias(token))
                if len(tokens) >= 2:
                    break
            if tokens:
                scoped_fragments.append(" ".join(tokens))
        if scoped_fragments:
            break

    if not scoped_fragments:
        for pattern in _CONTACT_QUERY_SCOPE_PATTERNS:
            match = pattern.search(str(query or ""))
            if not match:
                continue
            fragment_norm = _normalize_memory_search_text(match.group(1))
            if not fragment_norm:
                continue
            for part in re.split(r"\bund\b|,|/|;", fragment_norm):
                tokens: List[str] = []
                for token in part.split():
                    token_norm = _normalize_memory_search_text(token)
                    if token_norm in _CONTACT_QUERY_STOPWORDS or token_norm in _CONTACT_QUERY_CONTEXT_TERMS:
                        break
                    if len(token_norm) < 3:
                        continue
                    tokens.append(_normalize_contact_query_fragment_alias(token_norm))
                    if len(tokens) >= 2:
                        break
                if tokens:
                    scoped_fragments.append(" ".join(tokens))
            if scoped_fragments:
                break

    if scoped_fragments:
        contacts = db.query(models.Contact).all()
        matched_exact_fragment = False
        for fragment in scoped_fragments:
            fragment_tokens = {token for token in fragment.split() if len(token) >= 3}
            fragment_aliases = {fragment}
            for token in fragment_tokens:
                fragment_aliases.add(_normalize_contact_query_fragment_alias(token))
            exact_contact_aliases: List[str] = []
            for contact in contacts:
                contact_aliases = [
                    str(value or "").strip()
                    for value in (getattr(contact, "name", None), getattr(contact, "nickname", None))
                    if str(value or "").strip()
                ]
                normalized_aliases = [
                    _normalize_memory_search_text(alias)
                    for alias in contact_aliases
                    if _normalize_memory_search_text(alias)
                ]
                if any(candidate in normalized_aliases for candidate in fragment_aliases):
                    exact_contact_aliases.extend(normalized_aliases)
                    break
            if exact_contact_aliases:
                matched_exact_fragment = True
                for alias_norm in exact_contact_aliases:
                    aliases.add(alias_norm)
                    aliases.update(token for token in alias_norm.split() if len(token) >= 3)
                continue

            if not matched_exact_fragment:
                aliases.add(fragment)
                aliases.update(fragment_tokens)
        return aliases

    for contact in db.query(models.Contact).all():
        contact_aliases = [
            str(value or "").strip()
            for value in (getattr(contact, "name", None), getattr(contact, "nickname", None))
            if str(value or "").strip()
        ]
        matched = False
        normalized_aliases: List[str] = []
        for alias in contact_aliases:
            alias_norm = _normalize_memory_search_text(alias)
            if not alias_norm:
                continue
            normalized_aliases.append(alias_norm)
            alias_tokens = {token for token in alias_norm.split() if len(token) >= 3}
            query_alias_tokens = {
                _normalize_contact_query_fragment_alias(token)
                for token in query_tokens
                if token
            }
            if (
                re.search(rf"(?<!\w){re.escape(alias_norm)}s?(?!\w)", query_norm)
                or query_tokens.intersection(alias_tokens)
                or query_alias_tokens.intersection(alias_tokens)
            ):
                matched = True
        if not matched:
            continue
        for alias_norm in normalized_aliases:
            aliases.add(alias_norm)
            aliases.update(token for token in alias_norm.split() if len(token) >= 3)

    if aliases:
        return aliases

    return aliases


def _normalize_contact_query_fragment_alias(value: str) -> str:
    fragment = _normalize_memory_search_text(value)
    if fragment.endswith("s") and len(fragment) > 3:
        singular = fragment[:-1]
        if singular:
            fragment = singular
    return fragment


def _memory_matches_subject_aliases(mem: models.Memory, subject_aliases: set[str]) -> bool:
    if not subject_aliases:
        return True
    snippet_data = _parse_snippet(mem.snippet)
    fact_text = str(snippet_data.get("fact") or mem.snippet or "")
    subject_name = str(snippet_data.get("subject_name") or "")
    haystack_parts = [
        _normalize_memory_search_text(subject_name),
        _normalize_memory_search_text(getattr(mem, "canonical_key", None)),
        _normalize_memory_search_text(fact_text),
    ]
    haystack = " ".join(part for part in haystack_parts if part).strip()
    if not haystack:
        return False
    return any(alias and alias in haystack for alias in subject_aliases)


def _is_pet_overview_query(query: str) -> bool:
    query_norm = _normalize_memory_search_text(query)
    if not query_norm:
        return False
    return any(term in query_norm.split() for term in ("haustier", "haustiere", "hund", "katze"))


def _build_contact_pet_detail_memories(
    db: Session,
    query: str,
    subject_aliases: set[str],
) -> List[Dict[str, Any]]:
    if not subject_aliases or not _is_pet_overview_query(query):
        return []

    supplemental: List[Dict[str, Any]] = []
    query_norm = _normalize_memory_search_text(query)
    for contact in db.query(models.Contact).all():
        aliases = {
            _normalize_memory_search_text(getattr(contact, "name", None)),
            _normalize_memory_search_text(getattr(contact, "nickname", None)),
        }
        aliases.discard("")
        alias_match = bool(aliases & subject_aliases)
        if not alias_match and query_norm:
            alias_match = any(
                alias and (
                    re.search(rf"(?<!\w){re.escape(alias)}s?(?!\w)", query_norm)
                    or re.search(rf"(?<!\w){re.escape(alias.rstrip('s'))}(?!\w)", query_norm)
                )
                for alias in aliases
            )
        if not aliases or not alias_match:
            continue

        for index, detail in enumerate(list(getattr(contact, "personal_details", None) or []), start=1):
            detail_text = str(detail or "").strip()
            if not detail_text:
                continue
            detail_norm = _normalize_memory_search_text(detail_text)
            if not any(term in detail_norm.split() for term in ("haustier", "hund", "katze", "tasso", "garfield")):
                continue
            if detail_text.casefold().startswith("hat "):
                fact_text = f"{contact.name} {detail_text}"
            else:
                fact_text = detail_text
            supplemental.append(
                {
                    "memory_id": f"contact-{contact.id}-pet-{index}",
                    "fact": fact_text,
                    "priority": 1.0,
                    "category": "Haustier-Details",
                    "tags": ["contact", "personal_detail", "pet_overview"],
                    "user_editable": False,
                    "created_at": None,
                    "expires_at": None,
                }
            )
    return supplemental


def _is_contact_authoritative_pet_overview(
    query: str,
    subject_aliases: set[str],
    supplemental_memories: List[Dict[str, Any]],
) -> bool:
    if not subject_aliases or not supplemental_memories:
        return False
    if not _is_pet_overview_query(query):
        return False
    return any(
        isinstance(mem, dict)
        and "contact" in (mem.get("tags") or [])
        and "pet_overview" in (mem.get("tags") or [])
        for mem in supplemental_memories
    )


def _is_placeholder_memory_fact_text(text: Any) -> bool:
    normalized = _normalize_memory_search_text(text)
    if not normalized:
        return False
    placeholder_markers = (
        "name des testprojekts",
        "projektname",
        "chat titel platzhalter",
        "chat titel",
    )
    if not any(marker in normalized for marker in placeholder_markers):
        return False
    concrete_markers = ("phoenix", "orion")
    return not any(marker in normalized for marker in concrete_markers)


def _build_memory_write_source_metadata(
    *,
    source_skill: str,
    original_user_text: Optional[str],
) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {
        "source_skill": str(source_skill or "").strip() or "system.memory_write",
    }
    user_msg = str(original_user_text or "").strip()
    if user_msg:
        metadata["user_msg"] = user_msg[:500]
        metadata["contact_sync_trusted"] = True
        metadata["contact_sync_origin"] = "direct_user_utterance"
    return metadata


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


class MemoryDeleteArgs(BaseModel):
    memory_id: int = Field(..., description="ID der zu löschenden Memory")


class MemoryHistoryArgs(BaseModel):
    memory_id: int = Field(..., description="ID der Memory")


# ═══════════════════════════════════════════════════════════════════════════
# HANDLER: memory_write
# ═══════════════════════════════════════════════════════════════════════════

async def handle_memory_write(
    params: Dict[str, Any],
    db: Session,
    chat_id: int,
    source_skill: str = "system.memory_write",
    original_user_text: Optional[str] = None,
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

        if _is_sensitive_memory_write_request(args.fact):
            logger.warning("[TOOL WRITE] BLOCKED sensitive memory write request")
            return tool_err_v1(
                "SENSITIVE_MEMORY_BLOCKED",
                "Sensitive secret-like facts are not stored in memory.",
                tags=_MEMORY_TAGS,
                started_at=t0,
            )

        if _is_no_durable_memory_request(args.fact):
            logger.info("[TOOL WRITE] Skipping non-durable memory request")
            return tool_ok_v1(
                {
                    "operation": "not_saved",
                    "reason": "no_durable_memory_requested",
                    "memory_id": None,
                },
                tags=_MEMORY_TAGS,
                started_at=t0,
            )

        rebound_fact, rebound_subject_name = _rebind_explicit_contact_subject(
            fact=args.fact,
            subject_name=args.subject_name,
            original_user_text=original_user_text,
        )
        if rebound_fact != args.fact or rebound_subject_name != args.subject_name:
            logger.info(
                "[TOOL WRITE] Rebinding explicit contact subject from fact=%r subject=%r to fact=%r subject=%r",
                args.fact,
                args.subject_name,
                rebound_fact,
                rebound_subject_name,
            )
            args.fact = rebound_fact
            args.subject_name = rebound_subject_name
        
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

        source_metadata = _build_memory_write_source_metadata(
            source_skill=source_skill,
            original_user_text=original_user_text,
        )
        saved = save_memory_snippet(
            db=db,
            chat_id=chat_id,
            fact_object=enriched,
            source_type="tool",
            source_metadata=source_metadata,
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

        contact_proposal_result = None
        if str(source_skill or "") != "system.contact_memory_sync":
            from backend.services import contact_manager

            contact_proposal_result = contact_manager.stage_contact_update_from_memory(
                db,
                memory=saved,
                chat_id=chat_id,
            )
        
        return tool_ok_v1(
            {
                "operation": "saved",
                "memory_id": saved.id,
                "priority": final_priority,
                "canonical_key": enriched.get("canonical_key"),
                "contact_proposal": contact_proposal_result,
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

        subject_aliases = _extract_contact_query_subject_aliases(db, args.query)
        if subject_aliases:
            subject_filtered = [
                mem for mem in candidates if _memory_matches_subject_aliases(mem, subject_aliases)
            ]
            if subject_filtered:
                candidates = subject_filtered
        
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
                threshold=MEMORY_READ_SIMILARITY_THRESHOLD
            )
            results = [valid_memories[i] for i in indices]
        else:
            results = []

        if len(results) < args.limit:
            existing_ids = {mem.id for mem in results}
            lexical_matches = sorted(
                (
                    (_memory_lexical_match_score(mem, args.query), mem)
                    for mem in candidates
                    if mem.id not in existing_ids
                ),
                key=lambda item: (-item[0], -(item[1].priority or 0.0), -(item[1].id or 0)),
            )
            results.extend(
                mem
                for score, mem in lexical_matches
                if score > 0
            )
            results = results[:args.limit]
        
        # Format output
        memories_out = []
        for mem in results:
            snippet_data = _parse_snippet(mem.snippet)
            fact_text = snippet_data.get("fact", mem.snippet)
            if _is_placeholder_memory_fact_text(fact_text):
                logger.info(
                    "[TOOL READ] Skipping placeholder memory fact ID=%s: %s",
                    mem.id,
                    str(fact_text)[:80],
                )
                continue
            memories_out.append({
                "memory_id": mem.id,
                "fact": fact_text,
                "priority": mem.priority,
                "category": mem.category,
                "tags": mem.tags or [],
                "user_editable": mem.user_editable,
                "created_at": mem.created_at.isoformat() if mem.created_at else None,
                "expires_at": mem.expires_at.isoformat() if mem.expires_at else None,
            })

        if subject_aliases:
            supplemental_pet_memories = _build_contact_pet_detail_memories(db, args.query, subject_aliases)
            if _is_contact_authoritative_pet_overview(args.query, subject_aliases, supplemental_pet_memories):
                memories_out = supplemental_pet_memories
            else:
                existing_fact_keys = {
                    _normalize_memory_search_text(mem.get("fact"))
                    for mem in memories_out
                    if isinstance(mem, dict)
                }
                for supplemental in supplemental_pet_memories:
                    fact_key = _normalize_memory_search_text(supplemental.get("fact"))
                    if fact_key in existing_fact_keys:
                        continue
                    memories_out.append(supplemental)
                    existing_fact_keys.add(fact_key)

        logger.info(
            f"[TOOL READ] Query='{args.query}', Found={len(results)}, "
            f"Filtered={len(candidates) - len(results)}, Limit={args.limit}"
        )
        
        return tool_ok_v1(
            {
                "memories": memories_out,
                "total_found": len(memories_out),
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
        new_canonical_key = _build_canonical_key(None, args.new_fact)
        memory.canonical_key = new_canonical_key
        memory.text_hash = _hash_canonical_key(new_canonical_key)
        memory.normalized_text = new_canonical_key
        
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
# HANDLER: memory_delete
# ═══════════════════════════════════════════════════════════════════════════

async def handle_memory_delete(
    params: Dict[str, Any],
    db: Session,
    source_skill: str = "system.memory_delete"
) -> ToolResultV1:
    """
    FLOW:
    1. Lade Memory by ID
    2. CHECK user_editable (SECURITY CRITICAL)
    3. Delete from DB
    4. Invalidate cache
    5. Return: {status: "deleted", memory_id}
    """
    t0 = time.perf_counter()
    try:
        args = MemoryDeleteArgs(**params)

        memory = db.query(models.Memory).filter(models.Memory.id == args.memory_id).first()
        if not memory:
            return tool_err_v1(
                "NOT_FOUND",
                f"Memory {args.memory_id} not found",
                tags=_MEMORY_TAGS,
                started_at=t0,
            )

        if not memory.user_editable:
            logger.warning(
                f"[TOOL DELETE] BLOCKED: ID={args.memory_id}, user_editable=False, "
                f"source={source_skill}"
            )
            return tool_err_v1(
                "NOT_EDITABLE",
                "This memory is not deletable (user_editable=false)",
                tags=_MEMORY_TAGS,
                started_at=t0,
            )

        snippet_preview = str(memory.snippet or "")[:80]
        db.delete(memory)
        db.commit()

        memory_cache.invalidate(args.memory_id)

        logger.info(
            f"[TOOL DELETE] ID={args.memory_id}, source={source_skill}, "
            f"preview='{snippet_preview}'"
        )

        return tool_ok_v1(
            {
                "operation": "deleted",
                "memory_id": args.memory_id,
            },
            tags=_MEMORY_TAGS,
            started_at=t0,
            primary_entity_id=str(args.memory_id),
        )

    except Exception as e:
        logger.error(f"[TOOL DELETE] Error: {e}", exc_info=True)
        return tool_err_v1("DELETE_ERROR", str(e), tags=_MEMORY_TAGS, started_at=t0)


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


def _hash_canonical_key(key: str) -> str:
    import hashlib
    return hashlib.sha256(str(key or "").encode()).hexdigest()


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

def memory_write_tool(
    db: Session,
    original_user_text: Optional[str] = None,
    source_skill: str = "system.memory_write",
    **kwargs,
) -> ToolResultV1:
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
        future = asyncio.run_coroutine_threadsafe(
            handle_memory_write(
                params,
                db,
                chat_id,
                source_skill=source_skill,
                original_user_text=original_user_text,
            ),
            loop,
        )
        return future.result(timeout=30)
    except RuntimeError:
        # No running loop - use our own
        return asyncio.run(
            handle_memory_write(
                params,
                db,
                chat_id,
                source_skill=source_skill,
                original_user_text=original_user_text,
            )
        )


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


def memory_delete_tool(db: Session, **kwargs) -> ToolResultV1:
    """Sync wrapper for handle_memory_delete.

    Args:
        db: Database session (injected by ToolExecutor)
        **kwargs: Tool arguments (memory_id)
    """
    import asyncio

    params = {k: v for k, v in kwargs.items() if v is not None}

    try:
        loop = asyncio.get_running_loop()
        future = asyncio.run_coroutine_threadsafe(handle_memory_delete(params, db), loop)
        return future.result(timeout=30)
    except RuntimeError:
        return asyncio.run(handle_memory_delete(params, db))


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

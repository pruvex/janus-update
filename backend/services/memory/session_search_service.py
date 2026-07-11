import os
import re
from typing import Any, Dict, List, Optional

from backend.services.memory.session_fts_store import SessionFTSStore
from backend.tools.memory_tools import _SENSITIVE_MEMORY_WRITE_RE

MEMORY_SESSION_SEARCH_ENABLED = os.getenv("MEMORY_SESSION_SEARCH_ENABLED", "false").lower() == "true"
SESSION_SEARCH_SNIPPET_MAX_CHARS = 500
SESSION_SEARCH_FETCH_MULTIPLIER = 5
SESSION_SEARCH_FETCH_CAP = 50
_SESSION_SEARCH_SENSITIVE_RE = re.compile(
    r"\b(?:passwort|password|secret|token|api[-_\s]?key|credential|zugangsdaten)\b",
    re.IGNORECASE,
)
_SESSION_SEARCH_TEXT_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def session_search_enabled() -> bool:
    return MEMORY_SESSION_SEARCH_ENABLED


def sanitize_session_search_text(text: Any) -> Optional[str]:
    value = " ".join(str(text or "").split())
    if not value:
        return None
    if _SENSITIVE_MEMORY_WRITE_RE.search(value) or _SESSION_SEARCH_SENSITIVE_RE.search(value):
        return None
    if len(value) > SESSION_SEARCH_SNIPPET_MAX_CHARS:
        value = value[:SESSION_SEARCH_SNIPPET_MAX_CHARS].rstrip() + " ..."
    return value


def index_session_message(
    *,
    message_id: int,
    chat_id: int,
    role: str,
    content: str,
    created_at: Any,
    db_path: Optional[str] = None,
) -> bool:
    if not session_search_enabled():
        return False
    if not sanitize_session_search_text(content):
        return False
    with SessionFTSStore(db_path=db_path) as store:
        store.index_message(
            message_id=message_id,
            chat_id=chat_id,
            role=role,
            content=str(content or ""),
            created_at=created_at,
        )
    return True


def search_session_messages(
    *,
    query: str,
    limit: int = 5,
    chat_id: Optional[int] = None,
    since_days: Optional[int] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    fetch_limit = min(max(int(limit), 1) * SESSION_SEARCH_FETCH_MULTIPLIER, SESSION_SEARCH_FETCH_CAP)
    with SessionFTSStore(db_path=db_path) as store:
        rows = store.search(query=query, limit=fetch_limit, chat_id=chat_id, since_days=since_days)
    results: List[Dict[str, Any]] = []
    query_is_question = _looks_like_question_query(query)
    for row in rows:
        safe_snippet = sanitize_session_search_text(row.snippet)
        safe_content = sanitize_session_search_text(row.content)
        if not safe_snippet or not safe_content:
            continue
        if query_is_question and _is_query_echo_row(query, safe_content):
            continue
        results.append(
            {
                "message_id": row.message_id,
                "chat_id": row.chat_id,
                "role": row.role,
                "created_at": row.created_at,
                "snippet": _strip_fts_markup(safe_snippet),
                "content_preview": safe_content,
            }
        )
        if len(results) >= max(int(limit), 1):
            break
    return results


def _strip_fts_markup(text: str) -> str:
    return re.sub(r"<[^>]+>", "", str(text or "")).strip()


def _normalize_search_text(text: Any) -> str:
    lowered = str(text or "").casefold()
    return " ".join(_SESSION_SEARCH_TEXT_TOKEN_RE.findall(lowered))


def _looks_like_question_query(text: Any) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    normalized = _normalize_search_text(value)
    if len(normalized.split()) >= 3:
        return True
    return "?" in value


def _is_query_echo_row(query: Any, content: Any) -> bool:
    return _normalize_search_text(query) == _normalize_search_text(content)

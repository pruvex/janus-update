import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.data.schemas_tools import ToolResultV1
from backend.services.memory.session_search_service import (
    search_session_messages,
    session_search_enabled,
)
from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1


async def handle_session_search(
    params: Dict[str, Any],
    db: Session,
    db_path: Optional[str] = None,
) -> ToolResultV1:
    started = time.perf_counter()
    tags = ["memory", "session_search"]
    query = str(params.get("query") or "").strip()
    if not query:
        return tool_err_v1("INVALID_QUERY", "session_search requires a non-empty query.", tags=tags, started_at=started)
    if not session_search_enabled():
        return tool_err_v1(
            "FEATURE_DISABLED",
            "Session-Search is currently disabled via MEMORY_SESSION_SEARCH_ENABLED=false.",
            tags=tags,
            started_at=started,
        )

    limit = int(params.get("limit") or 5)
    chat_id = params.get("chat_id")
    since_days = params.get("since_days")
    matches = search_session_messages(
        query=query,
        limit=limit,
        chat_id=int(chat_id) if chat_id is not None else None,
        since_days=int(since_days) if since_days is not None else None,
        db_path=db_path,
    )
    return tool_ok_v1(
        {
            "query": query,
            "matches": matches,
            "total_found": len(matches),
        },
        message=f"Session-Search returned {len(matches)} Treffer.",
        tags=tags,
        started_at=started,
    )


def session_search_tool(db: Session, **kwargs) -> ToolResultV1:
    import asyncio

    params = {k: v for k, v in kwargs.items() if v is not None}
    try:
        loop = asyncio.get_running_loop()
        future = asyncio.run_coroutine_threadsafe(handle_session_search(params, db), loop)
        return future.result(timeout=30)
    except RuntimeError:
        return asyncio.run(handle_session_search(params, db))

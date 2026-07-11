import logging
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")
_QUERY_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)

SESSION_FTS_DB_PATH = os.path.join(get_app_data_dir(), "session_fts.db")
SESSION_SEARCH_ROLES = tuple(
    role.strip().lower()
    for role in os.getenv("SESSION_SEARCH_ROLES", "user").split(",")
    if role.strip()
)


@dataclass
class SessionSearchRow:
    message_id: int
    chat_id: int
    role: str
    created_at: str
    content: str
    snippet: str
    rank: float


class SessionFTSStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or SESSION_FTS_DB_PATH
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.executescript(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS session_messages USING fts5(
                message_id UNINDEXED,
                chat_id UNINDEXED,
                role UNINDEXED,
                created_at UNINDEXED,
                content,
                tokenize='unicode61 remove_diacritics 2'
            );
            """
        )
        conn.commit()

    def index_message(
        self,
        *,
        message_id: int,
        chat_id: int,
        role: str,
        content: str,
        created_at: Optional[Any],
    ) -> None:
        normalized_role = str(role or "").strip().lower()
        if SESSION_SEARCH_ROLES and normalized_role not in SESSION_SEARCH_ROLES:
            return
        text = str(content or "").strip()
        if not text:
            return
        created = self._coerce_timestamp(created_at)
        conn = self._get_conn()
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO session_messages
                (rowid, message_id, chat_id, role, created_at, content)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(message_id),
                    int(message_id),
                    int(chat_id),
                    normalized_role,
                    created,
                    text,
                ),
            )

    def delete_message(self, message_id: int) -> None:
        conn = self._get_conn()
        with conn:
            conn.execute("DELETE FROM session_messages WHERE rowid = ?", (int(message_id),))

    def search(
        self,
        *,
        query: str,
        limit: int = 5,
        chat_id: Optional[int] = None,
        since_days: Optional[int] = None,
    ) -> List[SessionSearchRow]:
        text = str(query or "").strip()
        if not text:
            return []

        filters = []
        params: List[Any] = []
        if chat_id is not None:
            filters.append("chat_id = ?")
            params.append(int(chat_id))
        if since_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=max(int(since_days), 0))
            filters.append("created_at >= ?")
            params.append(cutoff.isoformat())
        max_rows = max(1, min(int(limit), 20))
        conn = self._get_conn()
        collected: List[SessionSearchRow] = []
        seen_message_ids: set[int] = set()
        for candidate in self._build_query_candidates(text):
            where_parts = ["session_messages MATCH ?"]
            where_parts.extend(filters)
            query_params = [candidate, *params, max_rows]
            sql = f"""
                SELECT
                    message_id,
                    chat_id,
                    role,
                    created_at,
                    content,
                    snippet(session_messages, 4, '', '', ' ... ', 18) AS snippet,
                    rank
                FROM session_messages
                WHERE {" AND ".join(where_parts)}
                ORDER BY rank
                LIMIT ?
            """
            rows = conn.execute(sql, query_params).fetchall()
            for row in rows:
                message_id = int(row["message_id"])
                if message_id in seen_message_ids:
                    continue
                seen_message_ids.add(message_id)
                collected.append(
                    SessionSearchRow(
                        message_id=message_id,
                        chat_id=int(row["chat_id"]),
                        role=str(row["role"] or ""),
                        created_at=str(row["created_at"] or ""),
                        content=str(row["content"] or ""),
                        snippet=str(row["snippet"] or row["content"] or ""),
                        rank=float(row["rank"] or 0.0),
                    )
                )
                if len(collected) >= max_rows:
                    return collected
        return collected

    def _build_query_candidates(self, text: str) -> List[str]:
        tokens = [token.lower() for token in _QUERY_TOKEN_RE.findall(text) if token.strip()]
        if not tokens:
            return []

        candidates: List[str] = []
        exact = " ".join(tokens)
        if exact:
            candidates.append(exact)

        prefix_tokens = [f"{token}*" for token in tokens if len(token) >= 3]
        if prefix_tokens:
            candidates.append(" OR ".join(prefix_tokens))

        keyword_tokens = [token for token in tokens if len(token) >= 4]
        if keyword_tokens:
            keyword_prefix = " OR ".join(f"{token}*" for token in keyword_tokens)
            if keyword_prefix not in candidates:
                candidates.append(keyword_prefix)

        deduped: List[str] = []
        for candidate in candidates:
            if candidate and candidate not in deduped:
                deduped.append(candidate)
        return deduped

    def get_stats(self) -> Dict[str, int]:
        row = self._get_conn().execute(
            "SELECT COUNT(*) AS total FROM session_messages"
        ).fetchone()
        return {"messages": int(row["total"] or 0)}

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _coerce_timestamp(self, value: Optional[Any]) -> str:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
            return value.isoformat()
        text = str(value or "").strip()
        if text:
            return text
        return datetime.now(timezone.utc).isoformat()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

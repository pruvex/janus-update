"""
RAG V2 FTS5 Keyword-Index

SQLite FTS5 Virtual Table for fast full-text keyword search over all indexed chunks.
Provides BM25 ranking via the built-in RANK function.

Configuration:
- Tokenizer: unicode61 remove_diacritics 2
- WAL mode for concurrent read/write
- synchronous=NORMAL for balanced durability/performance
- UNINDEXED columns for metadata (chunk_id, source_path, format)
"""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

FTS_DB_PATH = os.path.join(get_app_data_dir(), "knowledge_fts_v2.db")


class FTSStore:
    """
    SQLite FTS5-backed keyword search index.

    Each chunk gets one row with:
    - chunk_id (UNINDEXED): stable ID matching ChromaDB
    - source_path (UNINDEXED): original file path
    - format (UNINDEXED): code | markdown | unknown
    - text: the actual chunk content (tokenized by unicode61)
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or FTS_DB_PATH
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
        # WAL mode + NORMAL sync for concurrent read/write performance
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA mmap_size = 30000000000")

        # Create FTS5 virtual table if not exists
        # tokenize='unicode61 remove_diacritics 2' for clean search over German/umlauts
        conn.executescript(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS kb_chunks USING fts5(
                chunk_id UNINDEXED,
                source_path UNINDEXED,
                format UNINDEXED,
                text,
                tokenize='unicode61 remove_diacritics 2'
            );

            -- Auxiliary table for efficient chunk lookups by ID
            CREATE TABLE IF NOT EXISTS chunk_lookup (
                chunk_id TEXT PRIMARY KEY,
                source_path TEXT NOT NULL,
                format TEXT,
                text_preview TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_chunk_lookup_path ON chunk_lookup(source_path);
            """
        )
        conn.commit()
        logger.info(f"FTSStore initialized at {self.db_path}")

    def add_chunks(
        self,
        chunk_ids: List[str],
        source_paths: List[str],
        formats: List[str],
        texts: List[str],
    ) -> None:
        """
        Insert or replace multiple chunks in the FTS index.

        Args:
            chunk_ids: Stable IDs matching ChromaDB
            source_paths: Original file path for each chunk
            formats: Format tag (code, markdown, etc.)
            texts: Chunk text content
        """
        conn = self._get_conn()
        # Use INSERT OR REPLACE to handle re-indexing of existing chunks
        fts_data = list(zip(chunk_ids, source_paths, formats, texts))
        lookup_data = [
            (cid, sp, fmt, txt[:500])  # text_preview truncated
            for cid, sp, fmt, txt in zip(chunk_ids, source_paths, formats, texts)
        ]

        with conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO kb_chunks (chunk_id, source_path, format, text)
                VALUES (?, ?, ?, ?)
                """,
                fts_data,
            )
            conn.executemany(
                """
                INSERT OR REPLACE INTO chunk_lookup (chunk_id, source_path, format, text_preview)
                VALUES (?, ?, ?, ?)
                """,
                lookup_data,
            )

        logger.info(f"FTSStore indexed {len(chunk_ids)} chunks")

    def delete_chunks(self, chunk_ids: List[str]) -> None:
        """Delete chunks from the FTS index by chunk_id."""
        if not chunk_ids:
            return
        conn = self._get_conn()
        placeholders = ",".join("?" * len(chunk_ids))
        with conn:
            conn.execute(
                f"DELETE FROM kb_chunks WHERE chunk_id IN ({placeholders})",
                chunk_ids,
            )
            conn.execute(
                f"DELETE FROM chunk_lookup WHERE chunk_id IN ({placeholders})",
                chunk_ids,
            )
        logger.info(f"FTSStore deleted {len(chunk_ids)} chunks")

    def delete_by_source_path(self, source_path: str) -> None:
        """Delete all chunks belonging to a given source file."""
        conn = self._get_conn()
        with conn:
            conn.execute(
                "DELETE FROM kb_chunks WHERE source_path = ?", (source_path,)
            )
            conn.execute(
                "DELETE FROM chunk_lookup WHERE source_path = ?", (source_path,)
            )
        logger.info(f"FTSStore deleted all chunks for {source_path}")

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, any]]:
        """
        Full-text search with BM25 ranking.

        Returns a list of dicts ordered by BM25 relevance (best first):
        {
            "chunk_id": str,
            "source_path": str,
            "format": str,
            "text": str,
            "bm25_rank": float,
            "rank": int,  # 1-based position in FTS result
        }
        """
        if not query or not query.strip():
            return []

        conn = self._get_conn()
        # Use the built-in rank column for BM25 scoring
        # rank is a hidden column in FTS5 that returns the BM25 score
        # We ORDER BY rank to get most relevant first
        rows = conn.execute(
            """
            SELECT chunk_id, source_path, format, text, rank AS bm25_rank
            FROM kb_chunks
            WHERE kb_chunks MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, top_k),
        ).fetchall()

        results = []
        for rank_pos, row in enumerate(rows, start=1):
            results.append(
                {
                    "chunk_id": row["chunk_id"],
                    "source_path": row["source_path"],
                    "format": row["format"],
                    "text": row["text"],
                    "bm25_rank": row["bm25_rank"],
                    "rank": rank_pos,
                }
            )

        logger.debug(f"FTS search for '{query[:50]}...' returned {len(results)} results")
        return results

    def get_stats(self) -> dict:
        """Return statistics about the FTS index."""
        conn = self._get_conn()
        total = conn.execute(
            "SELECT COUNT(*) FROM kb_chunks"
        ).fetchone()[0]
        total_lookup = conn.execute(
            "SELECT COUNT(*) FROM chunk_lookup"
        ).fetchone()[0]
        return {
            "fts_chunks": total,
            "lookup_entries": total_lookup,
        }

    def optimize(self) -> None:
        """Run FTS5 optimize to merge index segments."""
        conn = self._get_conn()
        conn.execute("INSERT INTO kb_chunks(kb_chunks) VALUES('optimize')")
        conn.commit()
        logger.info("FTSStore optimized")

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("FTSStore connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

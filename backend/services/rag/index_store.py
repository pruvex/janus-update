"""
RAG V2 Index Store — SQLite-backed incremental file tracking.

Manages SHA-256 hashes, file metadata, and chunk_id mapping for all indexed files.
Supports orphan detection and cleanup.
"""

import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

DB_PATH = os.path.join(get_app_data_dir(), "knowledge_index_v2.db")


@dataclass(frozen=True)
class IndexedFile:
    """Represents a tracked file in the index."""
    path: str
    sha256: str
    mtime: float
    size_bytes: int
    last_run_id: int
    chunk_ids: List[str]
    format: str
    indexed_at: float

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "mtime": self.mtime,
            "size_bytes": self.size_bytes,
            "last_run_id": self.last_run_id,
            "chunk_ids": json.dumps(self.chunk_ids),
            "format": self.format,
            "indexed_at": self.indexed_at,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "IndexedFile":
        return cls(
            path=row["path"],
            sha256=row["sha256"],
            mtime=row["mtime"],
            size_bytes=row["size_bytes"],
            last_run_id=row["last_run_id"],
            chunk_ids=json.loads(row["chunk_ids"]),
            format=row["format"],
            indexed_at=row["indexed_at"],
        )


class IndexStore:
    """
    SQLite-backed store for tracking indexed files.

    Guarantees:
    - Physical isolation: DB is at knowledge_index_v2.db (never touches legacy paths)
    - Atomicity: All writes within sqlite3 transactions
    - Orphan detection: Files not seen in the latest run can be identified and removed
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema (idempotent)."""
        conn = self._get_conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS indexed_files (
                path          TEXT PRIMARY KEY,
                sha256        TEXT NOT NULL,
                mtime         REAL NOT NULL,
                size_bytes    INTEGER NOT NULL,
                last_run_id   INTEGER NOT NULL,
                chunk_ids     TEXT NOT NULL,
                format        TEXT NOT NULL,
                indexed_at    REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_indexed_files_run ON indexed_files(last_run_id);
            CREATE INDEX IF NOT EXISTS idx_indexed_files_sha  ON indexed_files(sha256);
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                run_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at    REAL NOT NULL,
                ended_at      REAL,
                root_path     TEXT NOT NULL,
                files_scanned INTEGER DEFAULT 0,
                files_indexed INTEGER DEFAULT 0,
                files_skipped INTEGER DEFAULT 0,
                files_deleted INTEGER DEFAULT 0,
                status        TEXT DEFAULT 'running'
            );
            """
        )
        conn.commit()
        logger.info(f"IndexStore initialized at {self.db_path}")

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def start_run(self, root_path: str) -> int:
        """Start a new ingestion run, returning the run_id."""
        conn = self._get_conn()
        cursor = conn.execute(
            "INSERT INTO ingestion_runs (started_at, root_path) VALUES (?, ?)",
            (time.time(), root_path),
        )
        conn.commit()
        run_id = cursor.lastrowid
        logger.info(f"Ingestion run started: run_id={run_id}, root={root_path}")
        return run_id

    def end_run(
        self,
        run_id: int,
        files_scanned: int = 0,
        files_indexed: int = 0,
        files_skipped: int = 0,
        files_deleted: int = 0,
        status: str = "completed",
    ) -> None:
        """Mark a run as completed with statistics."""
        conn = self._get_conn()
        conn.execute(
            """
            UPDATE ingestion_runs
            SET ended_at = ?, files_scanned = ?, files_indexed = ?,
                files_skipped = ?, files_deleted = ?, status = ?
            WHERE run_id = ?
            """,
            (
                time.time(),
                files_scanned,
                files_indexed,
                files_skipped,
                files_deleted,
                status,
                run_id,
            ),
        )
        conn.commit()
        logger.info(
            f"Ingestion run {run_id} {status}: "
            f"scanned={files_scanned}, indexed={files_indexed}, "
            f"skipped={files_skipped}, deleted={files_deleted}"
        )

    def get(self, path: str) -> Optional[IndexedFile]:
        """Retrieve a single indexed file by path."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM indexed_files WHERE path = ?", (path,)
        ).fetchone()
        return IndexedFile.from_row(row) if row else None

    def find_by_filename(self, filename: str) -> List[IndexedFile]:
        """
        Fuzzy filename resolution: find files where source_path contains the
        given needle. Callers should post-filter by basename / stem for
        strict matching - this SQL step is intentionally permissive so that
        stems like "aegypten" still match paths like ".../aegypten.pdf".

        Args:
            filename: The needle (full basename, stem, or any substring).

        Returns:
            List of IndexedFile objects whose path contains the needle.
        """
        if not filename:
            return []
        conn = self._get_conn()
        # Normalize slashes for Windows compatibility
        pattern = f"%{filename}%"
        rows = conn.execute(
            "SELECT * FROM indexed_files WHERE path LIKE ?", (pattern,)
        ).fetchall()
        return [IndexedFile.from_row(row) for row in rows]

    def get_all_paths_for_filename(self, filename: str) -> List[str]:
        """
        Get all absolute paths for a given filename (stem or full name).
        Used for duplicate detection - if multiple files with the same name
        exist at different locations, the system should warn the user.

        Args:
            filename: The filename to search for (stem or full name, case-insensitive).

        Returns:
            List of absolute paths matching the filename.
        """
        if not filename:
            return []
        conn = self._get_conn()
        # Normalize filename: remove extension, lowercase
        from pathlib import PurePath
        stem = PurePath(filename).stem.lower()
        # Search for paths containing the stem (case-insensitive)
        pattern = f"%{stem}%"
        rows = conn.execute(
            "SELECT path FROM indexed_files WHERE LOWER(path) LIKE ?",
            (pattern.lower(),)
        ).fetchall()
        # Post-filter by basename stem for exact match
        matched_paths = []
        for row in rows:
            path = row["path"]
            path_stem = PurePath(path).stem.lower()
            if path_stem == stem:
                matched_paths.append(path)
        return matched_paths

    def get_chunk(self, chunk_id: str) -> Optional[Dict]:
        """
        Get chunk metadata from ChromaDB by chunk_id.

        This is a convenience method for ContextExpander.
        Note: IndexStore itself only stores file-level metadata; chunks are in ChromaDB.
        """
        try:
            import chromadb
            from backend.utils.paths import get_app_data_dir

            chroma_path = Path(get_app_data_dir()) / "rag_chroma_db_v2"
            client = chromadb.PersistentClient(path=str(chroma_path))

            # Try both collections
            for collection_name in ["kb_code_v2", "kb_prose_v2"]:
                try:
                    collection = client.get_collection(collection_name)
                    results = collection.get(ids=[chunk_id], include=["metadatas", "documents"])
                    if results["ids"]:
                        return {
                            "chunk_id": chunk_id,
                            "metadata": results["metadatas"][0] if results.get("metadatas") else {},
                            "text": results["documents"][0] if results.get("documents") else "",
                            "collection": collection_name,
                        }
                except Exception:
                    continue
            return None
        except Exception as e:
            logger.warning(f"IndexStore.get_chunk failed for {chunk_id}: {e}")
            return None

    def get_chunks_by_file(self, source_path: str, limit: int = None) -> List[Dict]:
        """
        Get chunks for a given file path from ChromaDB.

        Args:
            source_path: The file path to search for.
            limit: Maximum number of chunks to return (default None = no limit).

        This is a convenience method for ContextExpander and duplicate preview.
        """
        try:
            import chromadb
            from backend.utils.paths import get_app_data_dir

            # Normalize path to match ingestion normalization (pathlib.Path(p).resolve().as_posix().lower())
            query_path = Path(source_path).resolve().as_posix().lower()

            chroma_path = Path(get_app_data_dir()) / "rag_chroma_db_v2"
            client = chromadb.PersistentClient(path=str(chroma_path))

            chunks = []
            # Try both collections
            for collection_name in ["kb_code_v2", "kb_prose_v2"]:
                try:
                    collection = client.get_collection(collection_name)
                    # Use limit if provided, otherwise get all chunks (high limit)
                    query_limit = limit if limit is not None else 10000
                    results = collection.get(
                        where={"source_path": query_path},
                        include=["metadatas", "documents", "ids"],
                        limit=query_limit,
                    )
                    for idx, chunk_id in enumerate(results.get("ids", [])):
                        chunks.append({
                            "chunk_id": chunk_id,
                            "text": results.get("documents", [])[idx] if idx < len(results.get("documents", [])) else "",
                            "metadata": results.get("metadatas", [])[idx] if idx < len(results.get("metadatas", [])) else {},
                            "collection": collection_name,
                        })
                except Exception:
                    continue
            return chunks
        except Exception as e:
            logger.warning(f"IndexStore.get_chunks_by_file failed for {source_path}: {e}")
            return []

    def get_all(self) -> Dict[str, IndexedFile]:
        """Retrieve all indexed files as a dict keyed by path."""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM indexed_files").fetchall()
        return {row["path"]: IndexedFile.from_row(row) for row in rows}

    def upsert(self, file: IndexedFile) -> None:
        """Insert or update an indexed file record."""
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO indexed_files (path, sha256, mtime, size_bytes, last_run_id, chunk_ids, format, indexed_at)
            VALUES (:path, :sha256, :mtime, :size_bytes, :last_run_id, :chunk_ids, :format, :indexed_at)
            ON CONFLICT(path) DO UPDATE SET
                sha256 = excluded.sha256,
                mtime = excluded.mtime,
                size_bytes = excluded.size_bytes,
                last_run_id = excluded.last_run_id,
                chunk_ids = excluded.chunk_ids,
                format = excluded.format,
                indexed_at = excluded.indexed_at
            """,
            file.to_dict(),
        )
        conn.commit()

    def delete(self, path: str) -> bool:
        """Delete a single indexed file record. Returns True if a row was deleted."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM indexed_files WHERE path = ?", (path,))
        conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted index record for {path}")
        return deleted

    def find_orphans(self, run_id: int) -> List[str]:
        """
        Return paths of files whose last_run_id is older than the given run_id.
        These files were not seen in the current run and are candidates for deletion.
        """
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT path FROM indexed_files WHERE last_run_id < ?", (run_id,)
        ).fetchall()
        return [row["path"] for row in rows]

    def delete_orphans(self, run_id: int) -> List[str]:
        """
        Delete all index records whose last_run_id is older than the given run_id.
        Returns the list of deleted paths.
        """
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT path FROM indexed_files WHERE last_run_id < ?", (run_id,)
        ).fetchall()
        paths = [row["path"] for row in rows]
        if paths:
            placeholders = ",".join("?" * len(paths))
            conn.execute(
                f"DELETE FROM indexed_files WHERE path IN ({placeholders})",
                paths,
            )
            conn.commit()
            logger.info(f"Deleted {len(paths)} orphan index records")
        return paths

    def get_stats(self) -> dict:
        """Return aggregate statistics about the index."""
        conn = self._get_conn()
        total_files = conn.execute(
            "SELECT COUNT(*) FROM indexed_files"
        ).fetchone()[0]
        total_chunks = conn.execute(
            "SELECT SUM(CAST(json_array_length(chunk_ids) AS INTEGER)) FROM indexed_files"
        ).fetchone()[0] or 0
        last_run = conn.execute(
            "SELECT * FROM ingestion_runs ORDER BY run_id DESC LIMIT 1"
        ).fetchone()
        return {
            "total_files": total_files,
            "total_chunks": total_chunks,
            "last_run": dict(last_run) if last_run else None,
        }

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("IndexStore connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

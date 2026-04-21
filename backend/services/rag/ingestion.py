"""
RAG V2 Ingestion Engine

Format-aware document ingestion with:
- Incremental indexing (SHA-256 + mtime/size prefilter)
- Physical isolation from legacy rag_chroma_db/
- Orphan detection and cleanup
- Multi-format adapter routing

Guardrails:
- All ChromaDB access uses rag_chroma_db_v2/ path ONLY
- Assertion aborts if legacy path rag_chroma_db/ is detected
- No modification of rag_manager.py or vector_service.py
"""

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import chromadb
from chromadb.utils import embedding_functions

from backend.utils.paths import get_app_data_dir

from .adapters.base import BaseAdapter, RawChunk
from .adapters.code import CodeAdapter
from .adapters.markdown import MarkdownAdapter
from .index_store import IndexStore, IndexedFile

logger = logging.getLogger("janus_backend")

# --- PHYSICAL ISOLATION GUARD ---
V2_CHROMA_PATH = os.path.join(get_app_data_dir(), "rag_chroma_db_v2")
LEGACY_CHROMA_PATH = os.path.join(get_app_data_dir(), "rag_chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # P1: shared embedding; P3 adds jina-code


def _assert_isolation(chroma_path: str) -> None:
    """
    CRITICAL GUARD: Abort if the Chroma path contains the legacy directory.

    This is the last line of defense against accidental legacy index corruption.
    """
    normalized = os.path.normpath(chroma_path)
    legacy_marker = os.path.normpath(LEGACY_CHROMA_PATH)
    if normalized == legacy_marker or normalized.startswith(legacy_marker + os.sep):
        raise RuntimeError(
            f"FATAL: ChromaDB path '{chroma_path}' points to legacy directory. "
            f"V2 code must NEVER use '{LEGACY_CHROMA_PATH}'. Aborting."
        )
    logger.debug(f"Isolation check passed: {normalized} != {legacy_marker}")


# --- LAZY EMBEDDING ---
_embedding_function = None


def get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        logger.info(f"[RAG V2] Loading embedding model '{EMBEDDING_MODEL}'...")
        start = time.time()
        _embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        logger.info(f"[RAG V2] Embedding model loaded in {time.time() - start:.2f}s")
    return _embedding_function


# --- FORMAT ROUTER ---
class FormatRouter:
    """
    Routes file paths to the appropriate adapter based on extension.

    Adapters are tried in order; the first one whose .supports() returns True wins.
    """

    ADAPTERS: List[BaseAdapter] = [
        MarkdownAdapter(),
        CodeAdapter(),
    ]

    @classmethod
    def get_adapter(cls, path: Path) -> Optional[BaseAdapter]:
        for adapter in cls.ADAPTERS:
            if adapter.supports(path):
                return adapter
        return None

    @classmethod
    def is_supported(cls, path: Path) -> bool:
        return cls.get_adapter(path) is not None

    @classmethod
    def get_format(cls, path: Path) -> str:
        adapter = cls.get_adapter(path)
        if adapter is None:
            return "unknown"
        if isinstance(adapter, CodeAdapter):
            return "code"
        if isinstance(adapter, MarkdownAdapter):
            return "markdown"
        return "other"


# --- INGESTION RUN ---
class IngestionRun:
    """
    Single ingestion pass over a directory tree.

    Responsibilities:
    1. Scan directory for supported files
    2. Compare against index (mtime+size prefilter → SHA-256)
    3. Parse changed files into chunks
    4. Upsert chunks into V2 ChromaDB collection
    5. Detect and delete orphan records
    """

    def __init__(
        self,
        root_dir: str,
        collection_name: str = "kb_code_v2",
        chroma_path: Optional[str] = None,
        db_path: Optional[str] = None,
    ):
        self.root_dir = Path(root_dir).resolve()
        self.collection_name = collection_name
        self.chroma_path = chroma_path or V2_CHROMA_PATH
        self.store = IndexStore(db_path=db_path)

        # ISOLATION GUARD
        _assert_isolation(self.chroma_path)

        self._client = None
        self._collection = None
        self._run_id: Optional[int] = None
        self.stats = {
            "scanned": 0,
            "indexed": 0,
            "skipped": 0,
            "deleted": 0,
            "errors": 0,
        }

    @property
    def client(self):
        if self._client is None:
            _assert_isolation(self.chroma_path)
            os.makedirs(self.chroma_path, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.chroma_path)
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=get_embedding_function(),
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _scan_files(self) -> List[Path]:
        """Recursively find all supported files under root_dir."""
        files: List[Path] = []
        if not self.root_dir.exists():
            logger.warning(f"Root directory does not exist: {self.root_dir}")
            return files

        for p in self.root_dir.rglob("*"):
            if p.is_file() and FormatRouter.is_supported(p):
                files.append(p)

        logger.info(f"Scan found {len(files)} supported files in {self.root_dir}")
        return files

    def _needs_indexing(self, path: Path, stored: Optional[IndexedFile]) -> Tuple[bool, str]:
        """
        Determine if a file needs re-indexing.

        Returns (needs_index, reason).
        Prefilter: mtime+size comparison (fast).
        Confirm: SHA-256 (slow but deterministic).
        """
        mtime, size = BaseAdapter.get_file_stats(path)

        if stored is None:
            return True, "not_in_index"

        if stored.mtime != mtime or stored.size_bytes != size:
            return True, "mtime_or_size_changed"

        # Fast path: mtime+size unchanged → skip SHA
        # (but we still compute SHA for correctness)
        current_sha = BaseAdapter.compute_sha256(path)
        if stored.sha256 != current_sha:
            return True, "sha256_changed"

        return False, "unchanged"

    def _index_file(self, path: Path, run_id: int) -> List[str]:
        """
        Parse a file and upsert its chunks into ChromaDB.

        Returns list of chunk IDs.
        """
        adapter = FormatRouter.get_adapter(path)
        if adapter is None:
            raise ValueError(f"No adapter for {path}")

        chunks = adapter.parse(path)
        if not chunks:
            logger.warning(f"No chunks extracted from {path}")
            return []

        # Prepare ChromaDB payload
        texts = [c.text for c in chunks]
        metadatas = [
            {
                **c.metadata,
                "source_path": str(path),
                "format": FormatRouter.get_format(path),
                "start_line": c.start_line,
                "end_line": c.end_line,
                "indexed_at": time.time(),
            }
            for c in chunks
        ]
        ids = [
            hashlib.sha256(
                f"{path}:{i}:{chunk.text[:100]}".encode()
            ).hexdigest()
            for i, chunk in enumerate(chunks)
        ]

        # Upsert into ChromaDB
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )

        # Store in index
        mtime, size = BaseAdapter.get_file_stats(path)
        sha = BaseAdapter.compute_sha256(path)
        indexed = IndexedFile(
            path=str(path),
            sha256=sha,
            mtime=mtime,
            size_bytes=size,
            last_run_id=run_id,
            chunk_ids=ids,
            format=FormatRouter.get_format(path),
            indexed_at=time.time(),
        )
        self.store.upsert(indexed)

        logger.info(f"Indexed {path}: {len(chunks)} chunks")
        return ids

    def _delete_file_index(self, path: str, chunk_ids: List[str]) -> None:
        """Remove a file from both ChromaDB and the SQLite index."""
        try:
            self.collection.delete(ids=chunk_ids)
            logger.info(f"Deleted {len(chunk_ids)} ChromaDB chunks for {path}")
        except Exception as e:
            logger.error(f"Failed to delete ChromaDB chunks for {path}: {e}")

        self.store.delete(path)

    def run(self) -> dict:
        """
        Execute the full ingestion pipeline.

        Returns statistics dict.
        """
        self._run_id = self.store.start_run(str(self.root_dir))
        run_id = self._run_id
        logger.info(f"=== Ingestion run {run_id} started ===")

        try:
            files = self._scan_files()
            self.stats["scanned"] = len(files)

            # Get current index state
            index = self.store.get_all()

            # Process each file
            for path in files:
                stored = index.get(str(path))
                needs_index, reason = self._needs_indexing(path, stored)

                if not needs_index:
                    # Update last_run_id even for skipped files (so they're not orphans)
                    if stored:
                        updated = IndexedFile(
                            path=stored.path,
                            sha256=stored.sha256,
                            mtime=stored.mtime,
                            size_bytes=stored.size_bytes,
                            last_run_id=run_id,
                            chunk_ids=stored.chunk_ids,
                            format=stored.format,
                            indexed_at=stored.indexed_at,
                        )
                        self.store.upsert(updated)
                    self.stats["skipped"] += 1
                    continue

                try:
                    # If re-indexing, first delete old chunks
                    if stored and stored.chunk_ids:
                        self._delete_file_index(stored.path, stored.chunk_ids)

                    self._index_file(path, run_id)
                    self.stats["indexed"] += 1
                except Exception as e:
                    logger.error(f"Failed to index {path}: {e}", exc_info=True)
                    self.stats["errors"] += 1

            # Orphan cleanup: files not touched in this run
            orphans = self.store.find_orphans(run_id)
            for orphan_path in orphans:
                orphan = index.get(orphan_path)
                if orphan and orphan.chunk_ids:
                    self._delete_file_index(orphan_path, orphan.chunk_ids)
                self.stats["deleted"] += 1

            self.store.end_run(
                run_id=run_id,
                files_scanned=self.stats["scanned"],
                files_indexed=self.stats["indexed"],
                files_skipped=self.stats["skipped"],
                files_deleted=self.stats["deleted"],
                status="completed" if self.stats["errors"] == 0 else "completed_with_errors",
            )

        except Exception as e:
            logger.error(f"Ingestion run {run_id} failed: {e}", exc_info=True)
            self.store.end_run(run_id=run_id, status="failed")
            raise

        logger.info(
            f"=== Ingestion run {run_id} completed ===\n"
            f"  Scanned:  {self.stats['scanned']}\n"
            f"  Indexed:  {self.stats['indexed']}\n"
            f"  Skipped:  {self.stats['skipped']}\n"
            f"  Deleted:  {self.stats['deleted']}\n"
            f"  Errors:   {self.stats['errors']}"
        )
        return self.stats

    def close(self) -> None:
        self.store.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

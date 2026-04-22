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
from typing import Dict, List, Optional, Tuple, Any

import chromadb
from chromadb.utils import embedding_functions

from backend.utils.paths import get_app_data_dir

from .adapters.base import BaseAdapter, RawChunk
from .adapters.code import CodeAdapter
from .adapters.markdown import MarkdownAdapter
from .fts_store import FTSStore
from .index_store import IndexStore, IndexedFile
from .path_policy import PathPolicy, SecurityError, set_global_policy
from .retrieval_logger import get_retrieval_logger

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


def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata to ensure ChromaDB compatibility.

    ChromaDB only accepts str, int, float, bool types.
    Convert list and dict values to JSON strings.

    HOTFIX: Prevents crashes when metadata contains list/dict values.
    """
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, (list, dict)):
            sanitized[key] = json.dumps(value)
        else:
            sanitized[key] = value
    return sanitized


# --- COLLECTION NAMES ---
COLLECTION_CODE = "kb_code_v2"
COLLECTION_PROSE = "kb_prose_v2"


# --- LAZY EMBEDDING ---
# P3: Shared MiniLM for both code and prose.
# P4: Will split into kb_code_v2 (Jina-Code) + kb_prose_v2 (MiniLM).
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

    FINAL: Format-Gatekeeper ensures only Gold-Formates are processed.
    """

    ADAPTERS: List[BaseAdapter] = [
        MarkdownAdapter(),
        CodeAdapter(),
    ]

    # FINAL: Gold-Formates for global discovery
    GOLD_FORMATS = {".pdf", ".md", ".txt", ".py", ".js", ".ts", ".docx"}

    @classmethod
    def is_gold_format(cls, path: Path) -> bool:
        """Check if file extension is in the Gold-Formats list."""
        return path.suffix.lower() in cls.GOLD_FORMATS

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
        chroma_path: Optional[str] = None,
        db_path: Optional[str] = None,
        enable_path_policy: bool = True,  # P6: Enable path security checks
    ):
        self.root_dir = Path(root_dir).resolve()
        self.chroma_path = chroma_path or V2_CHROMA_PATH
        self.store = IndexStore(db_path=db_path)

        # ISOLATION GUARD
        _assert_isolation(self.chroma_path)

        # P6: Path Policy (Security)
        self.path_policy = None
        if enable_path_policy:
            self.path_policy = PathPolicy(self.root_dir)
            set_global_policy(self.root_dir)  # Set global policy for other modules
            logger.info(f"[P6] PathPolicy enabled for root: {self.root_dir}")

        self.fts = FTSStore()
        self.retrieval_logger = get_retrieval_logger()  # P6: Retrieval logger

        self._client = None
        self._collections: Dict[str, any] = {}  # collection_name -> Collection
        self._run_id: Optional[int] = None
        self.stats = {
            "scanned": 0,
            "indexed": 0,
            "skipped": 0,
            "deleted": 0,
            "errors": 0,
            "denied": 0,  # P6: Count of denied files
        }

    @property
    def client(self):
        if self._client is None:
            _assert_isolation(self.chroma_path)
            os.makedirs(self.chroma_path, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.chroma_path)
        return self._client

    def _get_collection(self, collection_name: str):
        """Get or create a ChromaDB collection by name (lazy)."""
        if collection_name not in self._collections:
            self._collections[collection_name] = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=get_embedding_function(),
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[collection_name]

    def _route_format_to_collection(self, fmt: str) -> str:
        """
        Route a file format to its target collection.

        P3: Both code and prose use MiniLM (shared embedding).
        P4: Code will switch to Jina-Code embeddings in kb_code_v2.
        """
        if fmt == "code":
            return COLLECTION_CODE
        return COLLECTION_PROSE

    def _scan_files(self) -> List[Path]:
        """
        Recursively find all supported files under root_dir.

        FINAL: Format-Gatekeeper ensures only Gold-Formates are processed.
        HOTFIX: Uses os.walk with onerror callback for robust error handling.
        """
        files: List[Path] = []
        if not self.root_dir.exists():
            logger.warning(f"Root directory does not exist: {self.root_dir}")
            return files

        def onerror(error: OSError) -> None:
            """Handle errors during os.walk without stopping the entire scan."""
            logger.warning(f"[RAG V2] Scan error at {error.filename}: {error.strerror}")

        try:
            for dirpath, dirnames, filenames in os.walk(self.root_dir, onerror=onerror):
                for filename in filenames:
                    file_path = Path(dirpath) / filename
                    # FINAL: Check if file is supported AND is a gold format
                    if FormatRouter.is_supported(file_path) and FormatRouter.is_gold_format(file_path):
                        files.append(file_path)
        except Exception as e:
            logger.error(f"[RAG V2] Unexpected error during file scan: {e}", exc_info=True)

        logger.info(f"Scan found {len(files)} gold-format files in {self.root_dir}")
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

        # HOTFIX: Sanitize metadata to ensure ChromaDB compatibility
        metadatas = [_sanitize_metadata(m) for m in metadatas]

        ids = [
            hashlib.sha256(
                f"{path}:{i}:{chunk.text[:100]}".encode()
            ).hexdigest()
            for i, chunk in enumerate(chunks)
        ]

        # P3 Dual-Collection: route chunks to code or prose collection
        fmt = FormatRouter.get_format(path)
        target_collection = self._route_format_to_collection(fmt)
        collection = self._get_collection(target_collection)

        # Upsert into ChromaDB
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )

        # Upsert into FTS5 keyword index (parallel sparse index)
        source_paths = [str(path)] * len(chunks)
        formats = [FormatRouter.get_format(path)] * len(chunks)
        self.fts.add_chunks(
            chunk_ids=ids,
            source_paths=source_paths,
            formats=formats,
            texts=texts,
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

        # P6: Log successful ingestion
        self.retrieval_logger.log_ingestion_success(
            file_path=str(path),
            num_chunks=len(chunks),
            collection=target_collection,
        )

        return ids

    def _delete_file_index(self, path: str, chunk_ids: List[str], fmt: str = "unknown") -> None:
        """Remove a file from ChromaDB, FTS5, and the SQLite index."""
        target_collection = self._route_format_to_collection(fmt)
        collection = self._get_collection(target_collection)
        try:
            collection.delete(ids=chunk_ids)
            logger.info(f"Deleted {len(chunk_ids)} ChromaDB chunks from {target_collection} for {path}")
        except Exception as e:
            logger.error(f"Failed to delete ChromaDB chunks for {path}: {e}")

        try:
            self.fts.delete_chunks(chunk_ids)
        except Exception as e:
            logger.error(f"Failed to delete FTS5 chunks for {path}: {e}")

        self.store.delete(path)

    def run_partial(self, file_paths: List[str]) -> dict:
        """
        Re-index only specific files (P8: for watcher).

        This is used by the background watchdog to re-index changed files
        without running a full ingestion scan.

        Args:
            file_paths: List of file paths to re-index.

        Returns:
            Statistics dict for the partial run.
        """
        self._run_id = self.store.start_run(str(self.root_dir))
        run_id = self._run_id
        logger.info(f"[P8] Partial ingestion run {run_id} started for {len(file_paths)} files")

        partial_stats = {
            "scanned": 0,
            "indexed": 0,
            "skipped": 0,
            "deleted": 0,
            "errors": 0,
            "denied": 0,
        }

        try:
            # Get current index state
            index = self.store.get_all()

            # Process only the specified files
            for file_path_str in file_paths:
                path = Path(file_path_str)

                # P6: Path Policy Check (Security)
                if self.path_policy:
                    denied_reason = self.path_policy.get_denied_reason(path)
                    if denied_reason:
                        self.retrieval_logger.log_ingestion_skip(str(path), denied_reason)
                        logger.warning(f"[P8] [SKIP] {path}: {denied_reason}")
                        partial_stats["denied"] += 1
                        continue

                # Check if file exists
                if not path.exists():
                    # File was deleted, remove from index
                    stored = index.get(str(path))
                    if stored and stored.chunk_ids:
                        self._delete_file_index(stored.path, stored.chunk_ids, stored.format)
                        partial_stats["deleted"] += 1
                    continue

                # Check if file is supported
                if not FormatRouter.is_supported(path):
                    partial_stats["skipped"] += 1
                    continue

                partial_stats["scanned"] += 1
                stored = index.get(str(path))
                needs_index, reason = self._needs_indexing(path, stored)

                if not needs_index:
                    partial_stats["skipped"] += 1
                    continue

                try:
                    # If re-indexing, first delete old chunks
                    if stored and stored.chunk_ids:
                        self._delete_file_index(stored.path, stored.chunk_ids, stored.format)

                    self._index_file(path, run_id)
                    partial_stats["indexed"] += 1
                except Exception as e:
                    logger.error(f"[P8] Failed to index {path}: {e}", exc_info=True)
                    partial_stats["errors"] += 1

            # Update last_run_id for all files in this partial run
            for file_path_str in file_paths:
                stored = index.get(file_path_str)
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

            self.store.end_run(
                run_id=run_id,
                files_scanned=partial_stats["scanned"],
                files_indexed=partial_stats["indexed"],
                files_skipped=partial_stats["skipped"],
                files_deleted=partial_stats["deleted"],
                status="completed" if partial_stats["errors"] == 0 else "completed_with_errors",
            )

        except Exception as e:
            logger.error(f"[P8] Partial ingestion run {run_id} failed: {e}", exc_info=True)
            self.store.end_run(run_id=run_id, status="failed")
            raise

        logger.info(
            f"[P8] Partial ingestion run {run_id} completed\n"
            f"  Scanned:  {partial_stats['scanned']}\n"
            f"  Indexed:  {partial_stats['indexed']}\n"
            f"  Skipped:  {partial_stats['skipped']}\n"
            f"  Deleted:  {partial_stats['deleted']}\n"
            f"  Errors:   {partial_stats['errors']}"
        )
        return partial_stats

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
                # P6: Path Policy Check (Security)
                if self.path_policy:
                    denied_reason = self.path_policy.get_denied_reason(path)
                    if denied_reason:
                        self.retrieval_logger.log_ingestion_skip(str(path), denied_reason)
                        logger.warning(f"[P6] [SKIP] {path}: {denied_reason}")
                        self.stats["denied"] += 1
                        continue

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
                        self._delete_file_index(stored.path, stored.chunk_ids, stored.format)

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
                    self._delete_file_index(orphan_path, orphan.chunk_ids, orphan.format)
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
        self.fts.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

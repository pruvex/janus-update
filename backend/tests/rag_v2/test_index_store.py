"""
Unit tests for RAG V2 IndexStore.
"""

import tempfile
from pathlib import Path

import pytest

from backend.services.rag.index_store import IndexStore, IndexedFile


class TestIndexStore:
    """Test the SQLite-backed index store."""

    def test_init_creates_db(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = IndexStore(db_path=db_path)
            stats = store.get_stats()
            assert stats["total_files"] == 0
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_upsert_and_get(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = IndexStore(db_path=db_path)
            file = IndexedFile(
                path="/test/file.py",
                sha256="abc123",
                mtime=1234567890.0,
                size_bytes=100,
                last_run_id=1,
                chunk_ids=["chunk1", "chunk2"],
                format="code",
                indexed_at=1234567890.0,
            )
            store.upsert(file)

            retrieved = store.get("/test/file.py")
            assert retrieved is not None
            assert retrieved.sha256 == "abc123"
            assert retrieved.chunk_ids == ["chunk1", "chunk2"]
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_delete(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = IndexStore(db_path=db_path)
            file = IndexedFile(
                path="/test/file.py",
                sha256="abc123",
                mtime=1234567890.0,
                size_bytes=100,
                last_run_id=1,
                chunk_ids=["chunk1"],
                format="code",
                indexed_at=1234567890.0,
            )
            store.upsert(file)
            assert store.get("/test/file.py") is not None

            deleted = store.delete("/test/file.py")
            assert deleted is True
            assert store.get("/test/file.py") is None
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_orphan_detection(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = IndexStore(db_path=db_path)

            # File from run 1
            file1 = IndexedFile(
                path="/test/file1.py",
                sha256="abc123",
                mtime=1234567890.0,
                size_bytes=100,
                last_run_id=1,
                chunk_ids=["chunk1"],
                format="code",
                indexed_at=1234567890.0,
            )
            store.upsert(file1)

            # File from run 2
            file2 = IndexedFile(
                path="/test/file2.py",
                sha256="def456",
                mtime=1234567890.0,
                size_bytes=200,
                last_run_id=2,
                chunk_ids=["chunk2"],
                format="code",
                indexed_at=1234567890.0,
            )
            store.upsert(file2)

            # Orphans: files with run_id < 2
            orphans = store.find_orphans(run_id=2)
            assert "/test/file1.py" in orphans
            assert "/test/file2.py" not in orphans

            # Delete orphans
            deleted = store.delete_orphans(run_id=2)
            assert "/test/file1.py" in deleted
            assert store.get("/test/file1.py") is None
            assert store.get("/test/file2.py") is not None
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_run_tracking(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = IndexStore(db_path=db_path)
            run_id = store.start_run("/test/root")
            assert isinstance(run_id, int)

            store.end_run(run_id, files_scanned=10, files_indexed=5, files_skipped=3, files_deleted=2)

            stats = store.get_stats()
            assert stats["last_run"] is not None
            assert stats["last_run"]["files_scanned"] == 10
            assert stats["last_run"]["status"] == "completed"
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

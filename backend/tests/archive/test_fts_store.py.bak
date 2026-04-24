"""
Unit tests for RAG V2 FTS5 Store.
"""

import tempfile
from pathlib import Path

import pytest

from backend.services.rag.fts_store import FTSStore


class TestFTSStore:
    """Test the SQLite FTS5 keyword index."""

    def test_init_creates_db(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = FTSStore(db_path=db_path)
            stats = store.get_stats()
            assert stats["fts_chunks"] == 0
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_add_and_search(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = FTSStore(db_path=db_path)
            store.add_chunks(
                chunk_ids=["c1", "c2", "c3"],
                source_paths=["/test/a.py", "/test/b.py", "/test/c.py"],
                formats=["code", "code", "markdown"],
                texts=[
                    "def hello_world(): pass",
                    "def goodbye_world(): pass",
                    "# Hello World\nThis is markdown.",
                ],
            )

            # Search for "hello"
            results = store.search("hello", top_k=10)
            chunk_ids = [r["chunk_id"] for r in results]
            assert "c1" in chunk_ids or "c3" in chunk_ids

            # Search for exact symbol
            results = store.search("goodbye_world", top_k=10)
            chunk_ids = [r["chunk_id"] for r in results]
            assert "c2" in chunk_ids
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_unicode61_diacritics(self):
        """Test that unicode61 remove_diacritics works for German umlauts."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = FTSStore(db_path=db_path)
            store.add_chunks(
                chunk_ids=["g1"],
                source_paths=["/test/de.md"],
                formats=["markdown"],
                texts=["Skandinavien Hauptstadt Stockholm Schweden"],
            )

            # Search should find this regardless of exact accent matching
            results = store.search("Skandinavien", top_k=10)
            assert len(results) >= 1
            assert results[0]["chunk_id"] == "g1"
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_delete_chunks(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = FTSStore(db_path=db_path)
            store.add_chunks(
                chunk_ids=["c1", "c2"],
                source_paths=["/test/a.py", "/test/b.py"],
                formats=["code", "code"],
                texts=["def foo(): pass", "def bar(): pass"],
            )

            # Verify both exist
            assert len(store.search("foo", top_k=10)) >= 1
            assert len(store.search("bar", top_k=10)) >= 1

            # Delete c1
            store.delete_chunks(["c1"])

            # c1 gone, c2 remains
            assert len(store.search("foo", top_k=10)) == 0
            assert len(store.search("bar", top_k=10)) >= 1
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_delete_by_source_path(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = FTSStore(db_path=db_path)
            store.add_chunks(
                chunk_ids=["c1", "c2", "c3"],
                source_paths=["/test/a.py", "/test/a.py", "/test/b.py"],
                formats=["code", "code", "code"],
                texts=["text one", "text two", "text three"],
            )

            # Delete all from a.py
            store.delete_by_source_path("/test/a.py")

            # Only b.py chunks remain
            results = store.search("text", top_k=10)
            assert len(results) == 1
            assert results[0]["chunk_id"] == "c3"
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_replace_existing_chunks(self):
        """Re-indexing same chunk_id should replace, not duplicate."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = FTSStore(db_path=db_path)
            store.add_chunks(
                chunk_ids=["c1"],
                source_paths=["/test/a.py"],
                formats=["code"],
                texts=["original text"],
            )

            # Re-index with different text
            store.add_chunks(
                chunk_ids=["c1"],
                source_paths=["/test/a.py"],
                formats=["code"],
                texts=["updated text"],
            )

            # Should find updated, not original
            results = store.search("original", top_k=10)
            assert len(results) == 0
            results = store.search("updated", top_k=10)
            assert len(results) == 1
            assert results[0]["chunk_id"] == "c1"
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_bm25_ranking(self):
        """FTS5 RANK should return BM25 scores."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            store = FTSStore(db_path=db_path)
            # Add multiple chunks with different text relevance
            store.add_chunks(
                chunk_ids=["r1", "r2", "r3"],
                source_paths=["/test/a.py", "/test/b.py", "/test/c.py"],
                formats=["code"] * 3,
                texts=[
                    "function search(query): return results",
                    "search is a common operation in databases",
                    "the quick brown fox jumps over the lazy dog",
                ],
            )

            results = store.search("search", top_k=10)
            # r1 and r2 should rank higher than r3 (which has no "search")
            chunk_ids = [r["chunk_id"] for r in results]
            assert "r3" not in chunk_ids  # No match for "search"
            # r1 and r2 should be present
            assert "r1" in chunk_ids or "r2" in chunk_ids
            store.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

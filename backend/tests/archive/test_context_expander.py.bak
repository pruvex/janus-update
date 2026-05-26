"""
Unit tests for RAG V2 Context Expander (context_expander.py).

Tests:
- Context Expansion (±1 chunks)
- Deduplication
- Expansion Stats
- Edge Cases (empty, single chunk)
"""

import tempfile
from pathlib import Path

import pytest

from backend.services.rag.context_expander import ContextExpander
from backend.services.rag.index_store import IndexStore


class TestContextExpanderExpansion:
    """Test context expansion logic."""

    def test_expand_surrounding_chunks(self):
        """Expander should load ±1 chunks around each result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "index.db"
            index_store = IndexStore(db_path=str(db_path))

            # Create a mock file with 5 chunks
            source_path = "/test/file.py"
            chunks = []
            for i in range(5):
                chunks.append(
                    {
                        "chunk_id": f"chunk_{i}",
                        "text": f"chunk text {i}",
                        "metadata": {"source_path": source_path},
                    }
                )

            # Add chunks to index store (via direct DB manipulation for testing)
            # Note: In real usage, chunks are added via ingestion
            # For this test, we'll mock the get_chunks_by_file method

            expander = ContextExpander(index_store)

            # Mock get_chunks_by_file to return our test chunks
            original_get = index_store.get_chunks_by_file
            index_store.get_chunks_by_file = lambda path: chunks

            # Expand around chunk_2 (should get chunk_1 and chunk_3)
            surrounding = expander._get_surrounding_chunks("chunk_2", window=1)

            assert len(surrounding) == 2
            surrounding_ids = [s["chunk_id"] for s in surrounding]
            assert "chunk_1" in surrounding_ids
            assert "chunk_3" in surrounding_ids

            # Restore original method
            index_store.get_chunks_by_file = original_get

            index_store.close()

    def test_expand_window_2(self):
        """Expander with window=2 should load ±2 chunks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "index.db"
            index_store = IndexStore(db_path=str(db_path))

            source_path = "/test/file.py"
            chunks = [
                {"chunk_id": f"chunk_{i}", "text": f"chunk {i}", "metadata": {}}
                for i in range(7)
            ]

            expander = ContextExpander(index_store)
            index_store.get_chunks_by_file = lambda path: chunks

            # Expand around chunk_3 with window=2
            surrounding = expander._get_surrounding_chunks("chunk_3", window=2)

            # Should get chunk_1, chunk_2, chunk_4, chunk_5 (skip chunk_3 itself)
            assert len(surrounding) == 4
            surrounding_ids = [s["chunk_id"] for s in surrounding]
            assert "chunk_1" in surrounding_ids
            assert "chunk_2" in surrounding_ids
            assert "chunk_4" in surrounding_ids
            assert "chunk_5" in surrounding_ids
            assert "chunk_3" not in surrounding_ids

            index_store.close()

    def test_expand_boundary_handling(self):
        """Expander should handle boundaries (first/last chunk) correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "index.db"
            index_store = IndexStore(db_path=str(db_path))

            chunks = [
                {"chunk_id": f"chunk_{i}", "text": f"chunk {i}", "metadata": {}}
                for i in range(3)
            ]

            expander = ContextExpander(index_store)
            index_store.get_chunks_by_file = lambda path: chunks

            # Expand around chunk_0 (first chunk)
            surrounding = expander._get_surrounding_chunks("chunk_0", window=1)
            surrounding_ids = [s["chunk_id"] for s in surrounding]

            # Should only get chunk_1 (no chunk_-1)
            assert len(surrounding) == 1
            assert "chunk_1" in surrounding_ids

            # Expand around chunk_2 (last chunk)
            surrounding = expander._get_surrounding_chunks("chunk_2", window=1)
            surrounding_ids = [s["chunk_id"] for s in surrounding]

            # Should only get chunk_1 (no chunk_3)
            assert len(surrounding) == 1
            assert "chunk_1" in surrounding_ids

            index_store.close()


class TestContextExpanderDedup:
    """Test deduplication logic."""

    def test_deduplicate_expanded_chunks(self):
        """Expander should not add duplicate chunks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "index.db"
            index_store = IndexStore(db_path=str(db_path))

            chunks = [
                {"chunk_id": f"chunk_{i}", "text": f"chunk {i}", "metadata": {}}
                for i in range(5)
            ]

            expander = ContextExpander(index_store)
            index_store.get_chunks_by_file = lambda path: chunks

            # Mock get_chunk to return chunk metadata
            index_store.get_chunk = lambda cid: {
                "chunk_id": cid,
                "source_path": "/test/file.py",
            }

            # Input: chunk_0 and chunk_1 (already neighbors)
            results = [
                {"chunk_id": "chunk_0", "text": "chunk 0", "metadata": {}},
                {"chunk_id": "chunk_1", "text": "chunk 1", "metadata": {}},
            ]

            expanded = expander.expand(results, expand_window=1, max_expanded=10)

            # Check for duplicates
            chunk_ids = [r["chunk_id"] for r in expanded]
            assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunks found"

            index_store.close()

    def test_deduplicate_across_files(self):
        """Expander should handle chunks from different files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "index.db"
            index_store = IndexStore(db_path=str(db_path))

            # Mock get_chunks_by_file to return file-specific chunks
            def mock_get_chunks(path):
                if path == "/test/file1.py":
                    return [
                        {"chunk_id": "f1_c0", "text": "f1 chunk 0", "metadata": {}},
                        {"chunk_id": "f1_c1", "text": "f1 chunk 1", "metadata": {}},
                    ]
                elif path == "/test/file2.py":
                    return [
                        {"chunk_id": "f2_c0", "text": "f2 chunk 0", "metadata": {}},
                        {"chunk_id": "f2_c1", "text": "f2 chunk 1", "metadata": {}},
                    ]
                return []

            expander = ContextExpander(index_store)
            index_store.get_chunks_by_file = mock_get_chunks
            index_store.get_chunk = lambda cid: {
                "chunk_id": cid,
                "source_path": "/test/file1.py" if "f1" in cid else "/test/file2.py",
            }

            results = [
                {"chunk_id": "f1_c0", "text": "f1 chunk 0", "metadata": {}},
                {"chunk_id": "f2_c0", "text": "f2 chunk 0", "metadata": {}},
            ]

            expanded = expander.expand(results, expand_window=1, max_expanded=10)

            # Should have chunks from both files, no duplicates
            chunk_ids = [r["chunk_id"] for r in expanded]
            assert len(chunk_ids) == len(set(chunk_ids))

            index_store.close()


class TestContextExpanderStats:
    """Test expansion statistics."""

    def test_expansion_stats(self):
        """Expander should calculate correct statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "index.db"
            index_store = IndexStore(db_path=str(db_path))

            expander = ContextExpander(index_store)

            results = [
                {"chunk_id": "1", "text": "test", "metadata": {"source_path": "/file1.py"}, "is_expanded": False},
                {"chunk_id": "2", "text": "test2", "metadata": {"source_path": "/file1.py"}, "is_expanded": True},
                {"chunk_id": "3", "text": "test3", "metadata": {"source_path": "/file2.py"}, "is_expanded": True},
            ]

            stats = expander.get_expansion_stats(results)

            assert stats["original_count"] == 1  # Only chunk 1 is not expanded
            assert stats["expanded_count"] == 2  # Chunks 2 and 3 are expanded
            assert stats["total_count"] == 3
            assert stats["unique_sources"] == 2  # file1.py and file2.py

            index_store.close()


class TestContextExpanderEdgeCases:
    """Test edge cases."""

    def test_expand_empty_results(self):
        """Expander should handle empty results gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "index.db"
            index_store = IndexStore(db_path=str(db_path))

            expander = ContextExpander(index_store)
            expanded = expander.expand([], expand_window=1, max_expanded=10)

            assert expanded == []

            index_store.close()

    def test_expand_single_chunk(self):
        """Expander should handle single chunk results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "index.db"
            index_store = IndexStore(db_path=str(db_path))

            chunks = [
                {"chunk_id": "chunk_0", "text": "chunk 0", "metadata": {}},
                {"chunk_id": "chunk_1", "text": "chunk 1", "metadata": {}},
            ]

            expander = ContextExpander(index_store)
            index_store.get_chunks_by_file = lambda path: chunks
            index_store.get_chunk = lambda cid: {"chunk_id": cid, "source_path": "/test/file.py"}

            results = [{"chunk_id": "chunk_0", "text": "chunk 0", "metadata": {}}]

            expanded = expander.expand(results, expand_window=1, max_expanded=10)

            # Should have chunk_0 + chunk_1 (expanded)
            assert len(expanded) == 2
            chunk_ids = [r["chunk_id"] for r in expanded]
            assert "chunk_0" in chunk_ids
            assert "chunk_1" in chunk_ids

            index_store.close()

    def test_expand_max_limit(self):
        """Expander should respect max_expanded limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "index.db"
            index_store = IndexStore(db_path=str(db_path))

            chunks = [
                {"chunk_id": f"chunk_{i}", "text": f"chunk {i}", "metadata": {}}
                for i in range(10)
            ]

            expander = ContextExpander(index_store)
            index_store.get_chunks_by_file = lambda path: chunks
            index_store.get_chunk = lambda cid: {"chunk_id": cid, "source_path": "/test/file.py"}

            # Input: 3 chunks, max_expanded=5
            results = [
                {"chunk_id": f"chunk_{i}", "text": f"chunk {i}", "metadata": {}}
                for i in range(3)
            ]

            expanded = expander.expand(results, expand_window=1, max_expanded=5)

            # Should not exceed max_expanded
            assert len(expanded) <= 5

            index_store.close()

    def test_expand_missing_chunk_metadata(self):
        """Expander should handle missing chunk metadata gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "index.db"
            index_store = IndexStore(db_path=str(db_path))

            expander = ContextExpander(index_store)

            # Mock get_chunk to return None (chunk not found)
            index_store.get_chunk = lambda cid: None

            results = [{"chunk_id": "unknown_chunk", "text": "test", "metadata": {}}]

            # Should not crash, just return original without expansion
            expanded = expander.expand(results, expand_window=1, max_expanded=10)

            assert len(expanded) == 1
            assert expanded[0]["chunk_id"] == "unknown_chunk"

            index_store.close()

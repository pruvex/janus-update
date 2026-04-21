"""
Integration tests for RAG V2 Hybrid Retriever.

These tests verify the full pipeline: index -> vector search + keyword search -> RRF fusion.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from backend.services.rag.hybrid_retriever import HybridRetriever
from backend.services.rag.ingestion import IngestionRun


class TestHybridRetriever:
    """Test the HybridRetriever end-to-end with a temporary index."""

    def test_empty_index_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "fts_v2.db"
            idx_tmp = Path(tmpdir) / "index_v2.db"

            retriever = HybridRetriever(
                chroma_path=str(chroma_tmp),
                fts_db_path=str(db_tmp),
                index_db_path=str(idx_tmp),
                use_reranker=False,  # P4: Disable reranker for basic test
                expand_context=False,  # P4: Disable expansion for basic test
            )
            results = retriever.query("hello", top_k=5)
            assert results == []
            retriever.close()

    def test_vector_search_finds_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python file
            test_file = Path(tmpdir) / "hello.py"
            test_file.write_text("def hello_world():\n    print('Hello World')\n")

            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "fts_v2.db"
            idx_tmp = Path(tmpdir) / "index_v2.db"

            # Index it
            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(idx_tmp),
            ) as ingest:
                stats = ingest.run()
                assert stats["indexed"] == 1

            # Query via hybrid retriever (P4: disable reranker/expansion for basic test)
            retriever = HybridRetriever(
                chroma_path=str(chroma_tmp),
                fts_db_path=str(db_tmp),
                index_db_path=str(idx_tmp),
                use_reranker=False,
                expand_context=False,
            )
            results = retriever.query("hello world function", top_k=5)
            assert len(results) > 0
            assert any("hello" in r["text"].lower() for r in results)
            retriever.close()

    def test_keyword_boosts_exact_symbol(self):
        """
        A variable name that may be missed by vector search should be
        found by FTS5 and boosted to the top via RRF.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "symbols.py"
            # Use single-quoted docstrings to avoid triple-quote nesting issues
            test_file.write_text(
                'def process_data():\n    "This function does general data processing."\n    pass\n\n'
                'def calculate_ferb_numerator():\n    "Computes the FERB numerator for analysis."\n    pass\n'
            )

            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "fts_v2.db"
            idx_tmp = Path(tmpdir) / "index_v2.db"

            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(idx_tmp),
            ) as ingest:
                ingest.run()

            retriever = HybridRetriever(
                chroma_path=str(chroma_tmp),
                fts_db_path=str(db_tmp),
                index_db_path=str(idx_tmp),
                use_reranker=False,
                expand_context=False,
            )
            # Search for exact symbol "ferb"
            results = retriever.query("ferb", top_k=5)

            # The exact symbol should appear in results due to FTS5
            found = any("ferb" in r["text"].lower() for r in results)
            assert found, f"Expected 'ferb' in results, got: {[r['text'][:60] for r in results]}"
            retriever.close()

    def test_hybrid_provenance(self):
        """Results should indicate whether they came from vector, keyword, or both."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def foo_bar():\n    return 42\n")

            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "fts_v2.db"
            idx_tmp = Path(tmpdir) / "index_v2.db"

            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(idx_tmp),
            ) as ingest:
                ingest.run()

            retriever = HybridRetriever(
                chroma_path=str(chroma_tmp),
                fts_db_path=str(db_tmp),
                index_db_path=str(idx_tmp),
                use_reranker=False,
                expand_context=False,
            )
            results = retriever.query("foo bar function", top_k=5)

            for r in results:
                assert "rrf_score" in r
                assert "vector_rank" in r
                assert "keyword_rank" in r
                # If present in both, both ranks should be set
                if r["vector_rank"] is not None and r["keyword_rank"] is not None:
                    # Document appeared in both rankings
                    assert r["rrf_score"] > 0
            retriever.close()

    def test_top_k_limit(self):
        """Should return exactly top_k results or fewer if index is small."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def func():\n    pass\n")

            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "fts_v2.db"
            idx_tmp = Path(tmpdir) / "index_v2.db"

            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(idx_tmp),
            ) as ingest:
                ingest.run()

            retriever = HybridRetriever(
                chroma_path=str(chroma_tmp),
                fts_db_path=str(db_tmp),
                index_db_path=str(idx_tmp),
                use_reranker=False,
                expand_context=False,
            )
            results = retriever.query("function", top_k=3)
            assert len(results) <= 3
            retriever.close()

    def test_p5_router_code_query(self):
        """P5: A code query should be routed to code collections with keyword bias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "hello.py"
            test_file.write_text("def hello_world():\n    print('Hello World')\n")

            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "fts_v2.db"
            idx_tmp = Path(tmpdir) / "index_v2.db"

            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(idx_tmp),
            ) as ingest:
                ingest.run()

            retriever = HybridRetriever(
                chroma_path=str(chroma_tmp),
                fts_db_path=str(db_tmp),
                index_db_path=str(idx_tmp),
                use_reranker=False,
                expand_context=False,
            )
            # P5: Code-like query
            results = retriever.query("hello_world() function", top_k=5, use_router=True)

            # Should include router metadata
            if results:
                assert "router_mode" in results[0]
                assert results[0]["router_mode"] in ("code_heavy", "hybrid")

            retriever.close()

    def test_p5_router_prose_query(self):
        """P5: A prose query should be routed to prose collections with vector bias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "hello.py"
            test_file.write_text("def hello_world():\n    print('Hello World')\n")

            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "fts_v2.db"
            idx_tmp = Path(tmpdir) / "index_v2.db"

            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(idx_tmp),
            ) as ingest:
                ingest.run()

            retriever = HybridRetriever(
                chroma_path=str(chroma_tmp),
                fts_db_path=str(db_tmp),
                index_db_path=str(idx_tmp),
                use_reranker=False,
                expand_context=False,
            )
            # P5: Prose-like query
            results = retriever.query(
                "How does the hello world function work", top_k=5, use_router=True
            )

            if results:
                assert "router_mode" in results[0]
                assert results[0]["router_mode"] in ("prose_heavy", "hybrid")

            retriever.close()

    def test_p5_retrieval_mode_override(self):
        """P5: Manual retrieval_mode override should bypass router."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "hello.py"
            test_file.write_text("def hello_world():\n    print('Hello World')\n")

            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "fts_v2.db"
            idx_tmp = Path(tmpdir) / "index_v2.db"

            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(idx_tmp),
            ) as ingest:
                ingest.run()

            retriever = HybridRetriever(
                chroma_path=str(chroma_tmp),
                fts_db_path=str(db_tmp),
                index_db_path=str(idx_tmp),
                use_reranker=False,
                expand_context=False,
            )
            # Override with code mode even for prose-looking query
            results = retriever.query(
                "How does it work",
                top_k=5,
                use_router=True,
                retrieval_mode="code",
            )

            if results:
                assert results[0]["router_mode"] == "code_heavy"

            retriever.close()

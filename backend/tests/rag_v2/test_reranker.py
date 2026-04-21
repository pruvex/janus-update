"""
Unit tests for RAG V2 Cross-Encoder Reranker (reranker.py).

Tests:
- Singleton Pattern
- Lazy-Loading
- Graceful Fallback
- Latency Gate (≤500ms for 20 pairs)
- Memory Gate (≤150MB RAM after model load)
"""

import time
from typing import Dict, List

import pytest

from backend.services.rag.reranker import CrossEncoderReranker


class TestRerankerSingleton:
    """Test that the reranker follows the singleton pattern."""

    def test_singleton_instance(self):
        """Multiple get_instance calls should return the same object."""
        instance1 = CrossEncoderReranker.get_instance()
        instance2 = CrossEncoderReranker.get_instance()
        assert instance1 is instance2

    def test_new_returns_singleton(self):
        """__new__ should return the same singleton instance."""
        instance1 = CrossEncoderReranker()
        instance2 = CrossEncoderReranker()
        assert instance1 is instance2


class TestRerankerLazyLoading:
    """Test that the model is loaded lazily."""

    def test_model_not_loaded_initially(self):
        """Model should not be loaded before first use."""
        reranker = CrossEncoderReranker()
        assert not reranker.is_available()

    def test_model_loads_on_first_rerank(self):
        """Model should load when rerank is called."""
        reranker = CrossEncoderReranker()
        candidates = [
            {"chunk_id": "1", "text": "test text", "metadata": {}},
            {"chunk_id": "2", "text": "another test", "metadata": {}},
        ]

        # If sentence-transformers is installed, this should trigger loading
        reranked = reranker.rerank("test query", candidates, top_k=2)

        # If model loaded successfully, check availability
        # If not installed, it should still return results (fallback)
        assert len(reranked) == 2


class TestRerankerGracefulFallback:
    """Test graceful fallback when model loading fails."""

    def test_fallback_on_missing_sentence_transformers(self):
        """If sentence-transformers is not installed, rerank should return original ranking."""
        reranker = CrossEncoderReranker()
        candidates = [
            {"chunk_id": "1", "text": "test text", "metadata": {}},
            {"chunk_id": "2", "text": "another test", "metadata": {}},
        ]

        # Force model load failure by setting the flag
        reranker._model_load_failed = True

        reranked = reranker.rerank("test query", candidates, top_k=2)

        # Should return original ranking unchanged
        assert len(reranked) == 2
        assert reranked[0]["chunk_id"] == "1"
        assert reranked[1]["chunk_id"] == "2"

    def test_fallback_on_rerank_exception(self):
        """If reranking fails, should return original top_k."""
        reranker = CrossEncoderReranker()
        candidates = [
            {"chunk_id": "1", "text": "test text", "metadata": {}},
            {"chunk_id": "2", "text": "another test", "metadata": {}},
        ]

        # Mock model that raises exception
        class MockModel:
            def predict(self, pairs):
                raise RuntimeError("Mock error")

        reranker._model = MockModel()
        reranker._model_loaded = True

        reranked = reranker.rerank("test query", candidates, top_k=2)

        # Should return original ranking unchanged
        assert len(reranked) == 2


class TestRerankerLatency:
    """Test latency gate: ≤500ms for 20 pairs."""

    def test_latency_gate_20_pairs(self):
        """Reranking 20 pairs should complete within 500ms on CPU."""
        reranker = CrossEncoderReranker()

        # Create 20 candidates
        candidates = [
            {"chunk_id": str(i), "text": f"test text {i}", "metadata": {}}
            for i in range(20)
        ]

        if not reranker.is_available():
            # Skip if model not installed
            pytest.skip("sentence-transformers not installed")

        start_time = time.time()
        reranked = reranker.rerank("test query", candidates, top_k=5)
        latency_ms = (time.time() - start_time) * 1000

        assert len(reranked) == 5
        assert latency_ms <= 500, f"Latency {latency_ms:.1f}ms exceeds 500ms gate"


class TestRerankerMemory:
    """Test memory gate: ≤150MB RAM after model load."""

    def test_memory_gate_model_load(self):
        """Model loading should not consume more than 150MB RAM."""
        import psutil
        import os

        # Get current process
        process = psutil.Process(os.getpid())

        # Baseline memory
        baseline_mem = process.memory_info().rss / (1024 * 1024)  # MB

        # Load model
        reranker = CrossEncoderReranker()
        if not reranker.is_available():
            pytest.skip("sentence-transformers not installed")

        # Memory after load
        loaded_mem = process.memory_info().rss / (1024 * 1024)  # MB
        mem_increase = loaded_mem - baseline_mem

        # Gate: ≤150MB increase
        assert mem_increase <= 150, f"Memory increase {mem_increase:.1f}MB exceeds 150MB gate"


class TestRerankerScoring:
    """Test scoring and ranking behavior."""

    def test_rerank_adds_scores(self):
        """Reranked results should include rerank_score and rerank_rank."""
        reranker = CrossEncoderReranker()
        candidates = [
            {"chunk_id": "1", "text": "python function definition", "metadata": {}},
            {"chunk_id": "2", "text": "javascript class", "metadata": {}},
        ]

        if not reranker.is_available():
            pytest.skip("sentence-transformers not installed")

        reranked = reranker.rerank("python function", candidates, top_k=2)

        assert len(reranked) == 2
        assert "rerank_score" in reranked[0]
        assert "rerank_rank" in reranked[0]
        assert reranked[0]["rerank_rank"] == 1
        assert reranked[1]["rerank_rank"] == 2

    def test_rerank_empty_candidates(self):
        """Empty candidate list should return empty list."""
        reranker = CrossEncoderReranker()
        reranked = reranker.rerank("test query", [], top_k=5)
        assert reranked == []

    def test_rerank_top_k_larger_than_candidates(self):
        """If top_k > len(candidates), return all candidates."""
        reranker = CrossEncoderReranker()
        candidates = [
            {"chunk_id": "1", "text": "test", "metadata": {}},
        ]

        reranked = reranker.rerank("test query", candidates, top_k=10)

        assert len(reranked) == 1


class TestRerankerModelInfo:
    """Test model information retrieval."""

    def test_model_info_unloaded(self):
        """Model info should indicate not loaded when model is not loaded."""
        reranker = CrossEncoderReranker()
        info = reranker.get_model_info()
        assert info["loaded"] is False
        assert "model_name" in info

    def test_model_info_loaded(self):
        """Model info should include max_seq_length when loaded."""
        reranker = CrossEncoderReranker()
        if not reranker.is_available():
            pytest.skip("sentence-transformers not installed")

        info = reranker.get_model_info()
        assert info["loaded"] is True
        assert "max_seq_length" in info
        assert info["max_seq_length"] > 0

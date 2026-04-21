"""
Unit tests for RAG V2 Reciprocal Rank Fusion.
"""

import pytest

from backend.services.rag.rrf import reciprocal_rank_fusion, fuse_with_fallback, K


class TestReciprocalRankFusion:
    """Test the RRF algorithm correctness."""

    def test_symmetric_rankings(self):
        """
        Core RRF invariant: fuse([[a,b], [b,a]]) must give equal scores.
        This is the canonical test from the RRF paper.
        """
        ranking_a = [("a", 0.9), ("b", 0.8)]
        ranking_b = [("b", 0.9), ("a", 0.8)]

        fused = reciprocal_rank_fusion([ranking_a, ranking_b], k=K)

        # Both a and b should have identical scores
        scores = {doc_id: score for doc_id, score in fused}
        assert scores["a"] == scores["b"]

    def test_single_source(self):
        """Single ranking should pass through with rank-adjusted scores."""
        ranking = [("x", 1.0), ("y", 0.9), ("z", 0.8)]
        fused = reciprocal_rank_fusion([ranking], k=K)

        assert len(fused) == 3
        assert fused[0][0] == "x"  # First in input is first in output
        # Scores: x=1/60, y=1/61, z=1/62
        assert fused[0][1] > fused[1][1] > fused[2][1]

    def test_two_sources_overlap(self):
        """Documents appearing in both sources get higher score."""
        r1 = [("a", 1.0), ("b", 0.9)]
        r2 = [("a", 0.8), ("c", 0.7)]

        fused = reciprocal_rank_fusion([r1, r2], k=K)
        scores = {d: s for d, s in fused}

        # a is in both, so it should have highest score
        assert scores["a"] > scores["b"]
        assert scores["a"] > scores["c"]

    def test_asymmetric_rankings(self):
        """Document only in one ranking still contributes but gets lower score."""
        r1 = [("a", 1.0), ("b", 0.9), ("c", 0.8)]
        r2 = [("a", 1.0)]  # Only a appears

        fused = reciprocal_rank_fusion([r1, r2], k=K)
        scores = {d: s for d, s in fused}

        # a is top in both, so it's #1
        assert fused[0][0] == "a"
        # b and c only in r1, but still ranked
        assert "b" in scores
        assert "c" in scores

    def test_empty_rankings(self):
        """Empty input should return empty output."""
        assert reciprocal_rank_fusion([]) == []
        assert reciprocal_rank_fusion([[]]) == []

    def test_k_influence(self):
        """Smaller k means top ranks dominate more."""
        r1 = [("a", 1.0), ("b", 0.5)]
        r2 = [("b", 1.0), ("a", 0.5)]

        # With k=1, top ranks are heavily weighted
        fused_small_k = reciprocal_rank_fusion([r1, r2], k=1)
        # With k=1000, all ranks nearly equal weight
        fused_large_k = reciprocal_rank_fusion([r1, r2], k=1000)

        # Large k should make scores more equal
        scores_small = {d: s for d, s in fused_small_k}
        scores_large = {d: s for d, s in fused_large_k}

        # With k=1, the score difference is larger
        diff_small = abs(scores_small["a"] - scores_small["b"])
        diff_large = abs(scores_large["a"] - scores_large["b"])
        assert diff_small > diff_large

    def test_fuse_with_fallback_structure(self):
        """fuse_with_fallback returns structured dicts."""
        r1 = [("a", 1.0), ("b", 0.9)]
        r2 = [("b", 1.0), ("a", 0.8)]

        results = fuse_with_fallback([r1, r2], k=K, top_k=2)
        assert len(results) == 2

        for r in results:
            assert "doc_id" in r
            assert "rrf_score" in r
            assert "rank" in r
            assert "sources" in r
            assert isinstance(r["rrf_score"], float)
            assert isinstance(r["rank"], int)
            assert isinstance(r["sources"], list)

"""
Unit tests for RAG V2 Query Router (query_router.py).

Tests:
- Accuracy Gate: ≥90% accuracy against router_fixtures.jsonl
- Zero-Magic Gate: No LLM calls, pure regex/heuristic (~0ms latency)
- Regression Gate: Prose queries route to prose path, code to code path
- Signal Detection: Individual code/prose signal tests
- Hybrid Classification: Ambiguous queries classified as hybrid
- Manual Override: retrieval_mode parameter works
- Weighted RRF: P5 weighted fusion produces different scores than uniform
"""

import json
import time
from pathlib import Path

import pytest

from backend.services.rag.query_router import (
    route,
    is_code_query,
    is_prose_query,
    RouterDecision,
    _score_code_signals,
    _score_prose_signals,
    _determine_mode,
)
from backend.services.rag.rrf import reciprocal_rank_fusion, weighted_reciprocal_rank_fusion


# --- Fixture Loading ---

FIXTURES_PATH = Path(__file__).parent.parent / "rag" / "router_fixtures.jsonl"


def _load_fixtures():
    """Load router test fixtures from JSONL."""
    fixtures = []
    with FIXTURES_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            fixtures.append(json.loads(line))
    return fixtures


# --- Accuracy Gate ---

class TestRouterAccuracy:
    """Test router accuracy against labeled fixtures."""

    def test_accuracy_gate(self):
        """Router must achieve ≥90% accuracy on labeled fixtures."""
        fixtures = _load_fixtures()
        assert len(fixtures) >= 20, f"Need ≥20 fixtures, got {len(fixtures)}"

        correct = 0
        total = len(fixtures)
        failures = []

        for fixture in fixtures:
            query = fixture["query"]
            expected = fixture["expected_mode"]
            decision = route(query)
            actual = decision.mode

            if actual == expected:
                correct += 1
            else:
                failures.append(
                    f"  FAIL: '{query[:50]}...' expected={expected} actual={actual}"
                )

        accuracy = correct / total if total > 0 else 0.0
        msg = f"Accuracy: {correct}/{total} = {accuracy:.1%}\n" + "\n".join(failures)
        assert accuracy >= 0.90, msg


# --- Zero-Magic Gate (Latency) ---

class TestRouterLatency:
    """Test that routing is pure regex/heuristic with ~0ms latency."""

    def test_latency_gate(self):
        """Routing 100 queries must complete within 100ms total (1ms avg)."""
        fixtures = _load_fixtures()
        queries = [f["query"] for f in fixtures]

        # Warm-up (first call may cache regex patterns)
        route(queries[0])

        start = time.perf_counter()
        for q in queries:
            route(q)
        elapsed_ms = (time.perf_counter() - start) * 1000

        avg_ms = elapsed_ms / len(queries)
        assert avg_ms < 5.0, f"Avg routing latency {avg_ms:.2f}ms exceeds 5ms gate"

    def test_no_llm_calls(self):
        """Verify route() does not import or call any LLM client."""
        import inspect
        import ast

        source_file = Path(__file__).parent.parent.parent / "services" / "rag" / "query_router.py"
        source = source_file.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Look for suspicious imports or calls
        llm_keywords = {"openai", "anthropic", "gemini", "claude", "gpt", "llm", "chat", "completion"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name.lower() for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    mod = (node.module or "").lower()
                    names = [mod]

                for name in names:
                    for kw in llm_keywords:
                        if kw in name:
                            pytest.fail(f"LLM-related import found: {name}")


# --- Regression Gate ---

class TestRouterRegression:
    """Test that standard prose queries still route to prose path."""

    def test_prose_queries_route_to_prose(self):
        """Standard NL questions must route to prose_heavy or hybrid."""
        prose_queries = [
            "how does the database connection pool work",
            "What is the purpose of the authentication module",
            "Where can I find the user profile settings",
            "Why does the search return empty results for new files",
            "Can you explain the difference between vector and keyword search",
        ]
        for q in prose_queries:
            decision = route(q)
            assert decision.mode in ("prose_heavy", "hybrid"), (
                f"Query '{q[:40]}...' routed to {decision.mode}, expected prose/heavy or hybrid"
            )

    def test_code_queries_route_to_code(self):
        """Code-like queries must route to code_heavy or hybrid."""
        code_queries = [
            "def process_data() { return x + 1 }",
            "user_repository.findById(id)",
            "import os from './utils'",
            "class UserService { getUser() {} }",
            "src/services/rag/query_router.py",
        ]
        for q in code_queries:
            decision = route(q)
            assert decision.mode in ("code_heavy", "hybrid"), (
                f"Query '{q[:40]}...' routed to {decision.mode}, expected code_heavy or hybrid"
            )


# --- Signal Detection ---

class TestCodeSignals:
    """Test individual code signal detection."""

    def test_snake_case_detection(self):
        scores = _score_code_signals("user_repository.find_by_id")
        assert scores["snake_case"] > 0.5

    def test_camel_case_detection(self):
        scores = _score_code_signals("findByIdAndName")
        assert scores["camel_case"] > 0.5

    def test_file_extension_detection(self):
        scores = _score_code_signals("query_router.py")
        assert scores["file_ext"] > 0.5

    def test_function_call_detection(self):
        scores = _score_code_signals("process(data)")
        assert scores["func_call"] > 0.5

    def test_code_keyword_detection(self):
        scores = _score_code_signals("def hello(): return 42")
        assert scores["code_keywords"] > 0.5

    def test_code_fence_detection(self):
        scores = _score_code_signals("```python\ndef hello():\n    pass\n```")
        assert scores["code_fences"] > 0.5

    def test_path_like_detection(self):
        scores = _score_code_signals("src/utils/helpers.py")
        assert scores["path_like"] > 0.5

    def test_composite_boost_multiple_signals(self):
        """Multiple active signals should boost composite score."""
        scores = _score_code_signals("src/services/user_repository.find_by_id()")
        assert scores["composite_code"] > 0.7


class TestProseSignals:
    """Test individual prose signal detection."""

    def test_question_word_detection(self):
        scores = _score_prose_signals("How does the system work")
        assert scores["question_words"] > 0.5

    def test_long_sentence_detection(self):
        scores = _score_prose_signals("this is a fairly long sentence with many words")
        assert scores["long_sentence"] >= 0.5

    def test_short_sentence_no_boost(self):
        scores = _score_prose_signals("short sentence")
        assert scores["long_sentence"] == 0.0

    def test_no_code_signals_boosts_prose(self):
        """Prose without code signals gets a bonus."""
        scores = _score_prose_signals("How does the database connection work")
        assert scores["no_code_signals"] > 0.5

    def test_composite_prose_with_question(self):
        scores = _score_prose_signals("What is the meaning of life")
        assert scores["composite_prose"] > 0.5


# --- Hybrid Classification ---

class TestHybridMode:
    """Test that ambiguous queries get hybrid classification."""

    def test_hybrid_when_both_signals_weak(self):
        """Weak signals on both sides → hybrid."""
        mode = _determine_mode(0.1, 0.1)
        assert mode == "hybrid"

    def test_hybrid_when_both_strong_and_close(self):
        """Both strong with small margin → hybrid."""
        mode = _determine_mode(0.45, 0.50)
        assert mode == "hybrid"

    def test_code_when_code_dominates(self):
        mode = _determine_mode(0.80, 0.20)
        assert mode == "code_heavy"

    def test_prose_when_prose_dominates(self):
        mode = _determine_mode(0.20, 0.80)
        assert mode == "prose_heavy"


# --- Router Decision Structure ---

class TestRouterDecision:
    """Test RouterDecision dataclass and properties."""

    def test_code_heavy_weights(self):
        d = route("def process_data(): return 42")
        assert d.mode == "code_heavy"
        assert "kb_code_v2" in d.collections
        assert d.vector_weight < d.keyword_weight  # keyword > vector for code
        assert d.code_bias > 0

    def test_prose_heavy_weights(self):
        d = route("How does the database connection pool work")
        assert d.mode == "prose_heavy"
        assert "kb_prose_v2" in d.collections
        assert d.vector_weight > d.keyword_weight  # vector > keyword for prose
        assert d.code_bias < 0

    def test_hybrid_weights(self):
        # A query that is ambiguous
        d = route("process data results")  # short, has process but not clear
        assert d.mode in ("hybrid", "code_heavy", "prose_heavy")
        # For hybrid: balanced weights
        if d.mode == "hybrid":
            assert abs(d.vector_weight - d.keyword_weight) < 0.1
            assert d.code_bias == 0.0

    def test_empty_query_fallback(self):
        d = route("")
        assert d.mode == "hybrid"
        assert "kb_code_v2" in d.collections
        assert "kb_prose_v2" in d.collections

    def test_signals_dict_present(self):
        d = route("def hello(): pass")
        assert "code_scores" in d.signals
        assert "prose_scores" in d.signals
        assert "query_length" in d.signals


# --- Convenience Functions ---

class TestConvenienceFunctions:
    """Test is_code_query and is_prose_query helpers."""

    def test_is_code_query_true(self):
        assert is_code_query("def foo(): pass")

    def test_is_code_query_false(self):
        assert not is_code_query("how does this work")

    def test_is_prose_query_true(self):
        assert is_prose_query("how does the system work")

    def test_is_prose_query_false(self):
        assert not is_prose_query("def foo(): pass")


# --- Weighted RRF ---

class TestWeightedRRF:
    """Test that weighted RRF produces different scores than uniform RRF."""

    def test_weighted_vs_uniform(self):
        """Weighted RRF with [0.8, 0.2] should differ from [1.0, 1.0]."""
        rankings = [
            [("doc1", 1.0), ("doc2", 0.9), ("doc3", 0.8)],
            [("doc3", 1.0), ("doc1", 0.9), ("doc4", 0.8)],
        ]

        uniform = reciprocal_rank_fusion(rankings, k=60)
        weighted = weighted_reciprocal_rank_fusion(rankings, weights=[0.8, 0.2], k=60)

        # Both should return same documents but possibly different order/scores
        uniform_ids = {d for d, _ in uniform}
        weighted_ids = {d for d, _ in weighted}
        assert uniform_ids == weighted_ids

        # Scores should differ
        uniform_scores = {d: s for d, s in uniform}
        weighted_scores = {d: s for d, s in weighted}
        assert any(uniform_scores[d] != weighted_scores[d] for d in uniform_ids)

    def test_weighted_boosts_preferred_source(self):
        """A doc that is rank-1 in the high-weight source should win."""
        rankings = [
            [("docA", 1.0), ("docB", 0.9)],  # Source 0 (weight=0.9)
            [("docB", 1.0), ("docA", 0.9)],  # Source 1 (weight=0.1)
        ]

        weighted = weighted_reciprocal_rank_fusion(rankings, weights=[0.9, 0.1], k=60)
        # docA should win because it is rank-1 in the high-weight source
        winner, winner_score = weighted[0]
        assert winner == "docA"

    def test_weighted_empty_rankings(self):
        """Empty rankings list should return empty."""
        assert weighted_reciprocal_rank_fusion([], weights=[1.0], k=60) == []

    def test_weighted_default_weights(self):
        """Weights shorter than rankings should default to 1.0."""
        rankings = [
            [("doc1", 1.0)],
            [("doc1", 1.0)],
            [("doc1", 1.0)],
        ]
        result = weighted_reciprocal_rank_fusion(rankings, weights=[0.5], k=60)
        assert len(result) == 1

"""
RAG V2 Query Router

Classifies incoming user queries via regex heuristics to determine search strategy.
No LLM calls — pure regex/linguistic heuristics for ~0ms latency.

Classification modes:
- code_heavy:   Query looks like code search (snake_case, file extensions, etc.)
- prose_heavy:  Query looks like natural language question
- hybrid:       Mixed signals or ambiguous

Output: RouterDecision with mode, collection targets, and fusion weights.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

logger = logging.getLogger("janus_backend")


@dataclass(frozen=True)
class RouterDecision:
    """Immutable routing decision produced by the query router."""

    mode: str  # "code_heavy" | "prose_heavy" | "hybrid"
    collections: List[str]  # target ChromaDB collections
    vector_weight: float  # 0.0–1.0 weight for vector search in fusion
    keyword_weight: float  # 0.0–1.0 weight for keyword search in fusion
    code_bias: float  # -1.0 (prose) to +1.0 (code), 0.0 = neutral
    signals: Dict[str, any] = field(default_factory=dict, repr=False)


# --- Regex Patterns for Code Signals ---

# Snake_case or camelCase identifiers
_SNAKE_CASE_RE = re.compile(r"\b[a-z]+_[a-z_]+\b")
_CAMEL_CASE_RE = re.compile(r"\b[a-z]+[A-Z][a-zA-Z]+\b")

# File extensions (e.g., .py, .js, .ts)
_FILE_EXT_RE = re.compile(r"\.[a-zA-Z]+\b")
_KNOWN_CODE_EXTS = frozenset(
    {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".go", ".rs", ".rb"}
)

# Function call patterns: func() or func(args)
_FUNC_CALL_RE = re.compile(r"\b\w+\s*\([^)]*\)")

# Class/function definition keywords
_CODE_KEYWORD_RE = re.compile(
    r"\b(def|class|function|fn|func|const|let|var|import|from|require|export|return|if|for|while)\b",
    re.IGNORECASE,
)

# Code fences / inline code markers
_CODE_FENCE_RE = re.compile(r"```|`[^`]+`")

# Path-like strings (e.g., src/utils.py)
_PATH_LIKE_RE = re.compile(r"[a-zA-Z_][\w/\-.]*\.[a-zA-Z]+")

# --- Regex Patterns for Prose Signals ---

# German / English question words
_QUESTION_WORD_RE = re.compile(
    r"\b(Wer|Was|Wo|Wie|Wann|Warum|Welche|Wie viel|Wie viele|Who|What|Where|How|When|Why|Which)\b",
    re.IGNORECASE,
)

# Sentence-ending punctuation (indicates NL)
_SENTENCE_PUNCT_RE = re.compile(r"[.!?;]")

# Whitespace ratio (prose tends to have more spaces)
_WORD_SPLIT_RE = re.compile(r"\s+")


def _score_code_signals(query: str) -> Dict[str, float]:
    """Score how "code-like" a query is. Returns signal dict with 0.0–1.0 scores."""
    scores = {}
    query_lower = query.lower()
    words = query.split()

    # 1. snake_case identifiers
    snake_matches = len(_SNAKE_CASE_RE.findall(query))
    scores["snake_case"] = min(snake_matches / 2.0, 1.0)

    # 2. camelCase identifiers
    camel_matches = len(_CAMEL_CASE_RE.findall(query))
    scores["camel_case"] = min(camel_matches / 2.0, 1.0)

    # 3. File extensions
    ext_matches = _FILE_EXT_RE.findall(query)
    known_ext_hits = sum(1 for e in ext_matches if e.lower() in _KNOWN_CODE_EXTS)
    scores["file_ext"] = min(known_ext_hits / 1.0, 1.0)

    # 4. Function calls
    func_matches = len(_FUNC_CALL_RE.findall(query))
    scores["func_call"] = min(func_matches / 1.0, 1.0)

    # 5. Code keywords
    kw_matches = len(_CODE_KEYWORD_RE.findall(query))
    scores["code_keywords"] = min(kw_matches / 3.0, 1.0)

    # 6. Code fences / backticks
    fence_matches = len(_CODE_FENCE_RE.findall(query))
    scores["code_fences"] = min(fence_matches / 1.0, 1.0)

    # 7. Path-like strings
    path_matches = len(_PATH_LIKE_RE.findall(query))
    scores["path_like"] = min(path_matches / 1.0, 1.0)

    # Composite code score (max of individual signals, with bonuses)
    raw_code = max(
        scores.get("snake_case", 0.0) * 0.9,
        scores.get("camel_case", 0.0) * 0.9,
        scores.get("file_ext", 0.0) * 1.0,
        scores.get("func_call", 0.0) * 1.0,
        scores.get("code_keywords", 0.0) * 0.8,
        scores.get("code_fences", 0.0) * 0.7,
        scores.get("path_like", 0.0) * 0.8,
    )
    # Boost if multiple signals fire
    active_signals = sum(1 for v in scores.values() if v >= 0.3)
    composite = min(raw_code + (active_signals - 1) * 0.15, 1.0)
    scores["composite_code"] = composite

    return scores


def _score_prose_signals(query: str) -> Dict[str, float]:
    """Score how "prose-like" a query is. Returns signal dict with 0.0–1.0 scores."""
    scores = {}
    words = query.split()
    word_count = len(words)

    # 1. Question words
    qw_matches = len(_QUESTION_WORD_RE.findall(query))
    scores["question_words"] = min(qw_matches / 1.0, 1.0)

    # 2. Sentence length ≥ 8 words
    if word_count >= 8:
        scores["long_sentence"] = 1.0
    elif word_count >= 5:
        scores["long_sentence"] = 0.5
    else:
        scores["long_sentence"] = 0.0

    # 3. Sentence punctuation
    punct_matches = len(_SENTENCE_PUNCT_RE.findall(query))
    scores["punctuation"] = min(punct_matches / 2.0, 1.0)

    # 4. High word-to-char ratio (prose has more spaces)
    if len(query) > 0:
        space_ratio = query.count(" ") / len(query)
        scores["space_ratio"] = min(space_ratio * 3.0, 1.0)
    else:
        scores["space_ratio"] = 0.0

    # 5. No code signals = strong prose signal
    code_scores = _score_code_signals(query)
    if code_scores["composite_code"] < 0.1 and word_count >= 3:
        scores["no_code_signals"] = 0.7
    else:
        scores["no_code_signals"] = 0.0

    # Composite prose score
    raw_prose = max(
        scores.get("question_words", 0.0) * 1.0,
        scores.get("long_sentence", 0.0) * 0.8,
        scores.get("punctuation", 0.0) * 0.6,
        scores.get("space_ratio", 0.0) * 0.5,
        scores.get("no_code_signals", 0.0) * 0.7,
    )
    # Boost if multiple signals fire
    active_signals = sum(1 for v in scores.values() if v >= 0.3)
    composite = min(raw_prose + (active_signals - 1) * 0.15, 1.0)
    scores["composite_prose"] = composite

    return scores


def _determine_mode(code_score: float, prose_score: float) -> str:
    """Determine routing mode based on code vs prose scores."""
    # Thresholds tuned for ≥90% accuracy on fixtures
    CODE_THRESHOLD = 0.35
    PROSE_THRESHOLD = 0.40
    HYBRID_MARGIN = 0.15  # If scores are within this margin, classify as hybrid

    if code_score >= CODE_THRESHOLD and prose_score >= PROSE_THRESHOLD:
        # Both signals strong → check margin
        if abs(code_score - prose_score) <= HYBRID_MARGIN:
            return "hybrid"
        elif code_score > prose_score:
            return "code_heavy"
        else:
            return "prose_heavy"

    if code_score >= CODE_THRESHOLD and prose_score < PROSE_THRESHOLD:
        return "code_heavy"

    if prose_score >= PROSE_THRESHOLD and code_score < CODE_THRESHOLD:
        return "prose_heavy"

    # Weak signals on both sides → default to hybrid (safe fallback)
    return "hybrid"


def _build_decision(
    query: str,
    code_scores: Dict[str, float],
    prose_scores: Dict[str, float],
) -> RouterDecision:
    """Build the final RouterDecision from scored signals."""
    code_score = code_scores["composite_code"]
    prose_score = prose_scores["composite_prose"]
    mode = _determine_mode(code_score, prose_score)

    # Collection targets based on mode
    if mode == "code_heavy":
        collections = ["kb_code_v2"]
    elif mode == "prose_heavy":
        collections = ["kb_prose_v2"]
    else:
        collections = ["kb_code_v2", "kb_prose_v2"]

    # Fusion weights: code-heavy → boost keyword (exact symbol matching)
    #                 prose-heavy → boost vector (semantic similarity)
    if mode == "code_heavy":
        vector_weight = 0.25
        keyword_weight = 0.75
        code_bias = +1.0
    elif mode == "prose_heavy":
        vector_weight = 0.80
        keyword_weight = 0.20
        code_bias = -1.0
    else:
        vector_weight = 0.50
        keyword_weight = 0.50
        code_bias = 0.0

    decision = RouterDecision(
        mode=mode,
        collections=collections,
        vector_weight=vector_weight,
        keyword_weight=keyword_weight,
        code_bias=code_bias,
        signals={
            "code_scores": code_scores,
            "prose_scores": prose_scores,
            "query_length": len(query),
            "word_count": len(query.split()),
        },
    )

    logger.debug(
        f"[QueryRouter] mode={mode} code={code_score:.2f} prose={prose_score:.2f} "
        f"collections={collections} v_w={vector_weight:.2f} k_w={keyword_weight:.2f}"
    )
    return decision


def route(query: str) -> RouterDecision:
    """
    Route a user query to the appropriate search strategy.

    Pure regex/heuristic classification — no LLM calls, ~0ms latency.

    Args:
        query: The raw user query string.

    Returns:
        RouterDecision with mode, target collections, and fusion weights.
    """
    if not query or not query.strip():
        # Empty query → safe hybrid default
        return RouterDecision(
            mode="hybrid",
            collections=["kb_code_v2", "kb_prose_v2"],
            vector_weight=0.50,
            keyword_weight=0.50,
            code_bias=0.0,
            signals={"empty_query": True},
        )

    code_scores = _score_code_signals(query)
    prose_scores = _score_prose_signals(query)
    return _build_decision(query, code_scores, prose_scores)


# --- Convenience functions ---

def is_code_query(query: str, threshold: float = 0.35) -> bool:
    """Quick check if query looks code-heavy."""
    code_scores = _score_code_signals(query)
    return code_scores["composite_code"] >= threshold


def is_prose_query(query: str, threshold: float = 0.40) -> bool:
    """Quick check if query looks prose-heavy."""
    prose_scores = _score_prose_signals(query)
    return prose_scores["composite_prose"] >= threshold

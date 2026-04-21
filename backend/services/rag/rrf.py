"""
RAG V2 Reciprocal Rank Fusion (RRF)

Pure function implementation of RRF combining multiple ranked lists into a single
fused ranking. Follows the original Cormack et al. formula with k=60.

Formula:
    score(d) = Σ (1 / (k + rank_i(d)))

where rank_i(d) is the 1-based position of document d in ranking i.
If d is not present in ranking i, it contributes 0 to the sum.

The constant k=60 provides strong bias toward top-ranked items while
still giving lower-ranked items a meaningful contribution.
"""

from typing import Dict, List, Tuple

# Gold-standard constant from original RRF paper
K = 60


def reciprocal_rank_fusion(
    rankings: List[List[Tuple[str, float]]],
    k: int = K,
) -> List[Tuple[str, float]]:
    """
    Fuse multiple ranked lists using Reciprocal Rank Fusion.

    Args:
        rankings: List of rankings, each ranking is a list of (doc_id, score) tuples.
                  Order within each ranking matters (best first, rank=1).
                  The score values are ignored for RRF computation; only rank position matters.
        k: RRF constant. Default 60 (gold standard).

    Returns:
        List of (doc_id, rrf_score) tuples, sorted by descending RRF score.
    """
    if not rankings:
        return []

    # Aggregate RRF scores per document
    scores: Dict[str, float] = {}

    for ranking in rankings:
        for rank_pos, (doc_id, _) in enumerate(ranking, start=1):
            rrf_score = 1.0 / (k + rank_pos)
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score

    # Sort by descending RRF score
    sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


def fuse_with_fallback(
    rankings: List[List[Tuple[str, float]]],
    k: int = K,
    top_k: int = 10,
) -> List[Dict[str, any]]:
    """
    Fuse rankings and return a structured result list with ranks.

    Args:
        rankings: List of rankings as (doc_id, score) tuples per source.
        k: RRF constant.
        top_k: Maximum number of results to return.

    Returns:
        List of dicts: {"doc_id": str, "rrf_score": float, "rank": int, "sources": List[str]}
    """
    fused = reciprocal_rank_fusion(rankings, k=k)

    # Determine which sources contained each doc (for provenance)
    source_map: Dict[str, List[str]] = {}
    for src_idx, ranking in enumerate(rankings):
        src_name = f"source_{src_idx}"
        for doc_id, _ in ranking:
            if doc_id not in source_map:
                source_map[doc_id] = []
            source_map[doc_id].append(src_name)

    results = []
    for rank_pos, (doc_id, score) in enumerate(fused[:top_k], start=1):
        results.append(
            {
                "doc_id": doc_id,
                "rrf_score": score,
                "rank": rank_pos,
                "sources": source_map.get(doc_id, []),
            }
        )

    return results


def weighted_reciprocal_rank_fusion(
    rankings: List[List[Tuple[str, float]]],
    weights: List[float],
    k: int = K,
) -> List[Tuple[str, float]]:
    """
    P5: Weighted Reciprocal Rank Fusion.

    Allows giving different sources different weights in the fusion.
    Useful when the query router determines one channel (vector vs keyword)
    should be trusted more for a specific query type.

    Formula:
        score(d) = Σ (weight_i / (k + rank_i(d)))

    Args:
        rankings: List of rankings, each ranking is a list of (doc_id, score) tuples.
                  Order within each ranking matters (best first, rank=1).
        weights: Weight for each ranking source. Must sum to approximately 1.0.
                 If shorter than rankings, remaining weights default to 1.0.
        k: RRF constant. Default 60.

    Returns:
        List of (doc_id, rrf_score) tuples, sorted by descending RRF score.
    """
    if not rankings:
        return []

    # Normalize weights
    norm_weights = list(weights) + [1.0] * (len(rankings) - len(weights))
    norm_weights = norm_weights[: len(rankings)]

    # Aggregate weighted RRF scores per document
    scores: Dict[str, float] = {}

    for weight, ranking in zip(norm_weights, rankings):
        for rank_pos, (doc_id, _) in enumerate(ranking, start=1):
            rrf_score = weight * (1.0 / (k + rank_pos))
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score

    # Sort by descending RRF score
    sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results

"""
Knowledge Service - Unified RAG Interface

Provides a unified interface for knowledge queries with support for both
legacy (V1) and V2 RAG implementations.

Zero-Regression Guard:
- Default retrieval_mode="legacy" uses V1 (rag_manager.py)
- V2 (hybrid_retriever) is only initialized when retrieval_mode="v2" or "hybrid"
- This ensures V2 components are not loaded unless explicitly requested
"""

import logging
from typing import Dict, List, Optional, Literal

logger = logging.getLogger("janus_backend")


def query(
    query_text: str,
    top_k: int = 10,
    retrieval_mode: Literal["legacy", "v2", "hybrid"] = "legacy",
    file_type_filter: Optional[List[str]] = None,
    **kwargs,
) -> Dict:
    """
    Execute a knowledge query.

    Args:
        query_text: The search query.
        top_k: Number of results to return.
        retrieval_mode: "legacy" (V1, default), "v2" (RAG V2 only), "hybrid" (both).
        file_type_filter: Optional list of file extensions to filter (V2 only).
        **kwargs: Additional parameters passed to underlying implementation.

    Returns:
        Dict with results and metadata.

    Zero-Regression Guard:
        - When retrieval_mode="legacy" (default), V2 is NOT initialized.
        - V2 is only loaded when retrieval_mode="v2" or "hybrid".
    """
    # Legacy mode (V1) - default behavior
    if retrieval_mode == "legacy":
        return _query_legacy(query_text, top_k=top_k, **kwargs)

    # V2 mode or hybrid mode
    if retrieval_mode in ("v2", "hybrid"):
        return _query_v2(
            query_text,
            top_k=top_k,
            file_type_filter=file_type_filter,
            retrieval_mode_override=None,  # Let router decide
            **kwargs,
        )

    # Fallback to legacy for unknown modes
    logger.warning(f"Unknown retrieval_mode '{retrieval_mode}', falling back to legacy")
    return _query_legacy(query_text, top_k=top_k, **kwargs)


def _query_legacy(query_text: str, top_k: int = 10, **kwargs) -> Dict:
    """
    Execute query using legacy V1 RAG (rag_manager.py).

    This function imports and uses the legacy implementation only when called.
    """
    try:
        from backend.services.rag_manager import query as rag_query

        results = rag_query(query_text, top_k=top_k, **kwargs)

        return {
            "results": results,
            "mode": "legacy",
            "num_results": len(results) if results else 0,
        }

    except ImportError as e:
        logger.error(f"Legacy RAG not available: {e}")
        return {
            "results": [],
            "mode": "legacy",
            "num_results": 0,
            "error": f"Legacy RAG not available: {e}",
        }
    except Exception as e:
        logger.error(f"Legacy query failed: {e}", exc_info=True)
        return {
            "results": [],
            "mode": "legacy",
            "num_results": 0,
            "error": str(e),
        }


def _query_v2(
    query_text: str,
    top_k: int = 10,
    file_type_filter: Optional[List[str]] = None,
    retrieval_mode_override: Optional[Literal["code", "prose", "hybrid"]] = None,
    **kwargs,
) -> Dict:
    """
    Execute query using V2 RAG (hybrid_retriever).

    This function imports and uses the V2 implementation only when called.
    """
    try:
        from backend.services.rag.api_adapter import query_v2

        results = query_v2(
            query_text=query_text,
            top_k=top_k,
            file_type_filter=file_type_filter,
            retrieval_mode_override=retrieval_mode_override,
            **kwargs,
        )

        return results

    except ImportError as e:
        logger.error(f"V2 RAG not available: {e}")
        return {
            "results": [],
            "mode": "v2",
            "num_results": 0,
            "error": f"V2 RAG not available: {e}",
        }
    except Exception as e:
        logger.error(f"V2 query failed: {e}", exc_info=True)
        return {
            "results": [],
            "mode": "v2",
            "num_results": 0,
            "error": str(e),
        }

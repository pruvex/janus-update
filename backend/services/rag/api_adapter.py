"""
RAG V2 API Adapter

Adapter layer between the API and RAG V2 system.
Provides a clean interface for knowledge_service.py to use V2 features
without directly importing RAG internals.

This adapter ensures:
- Zero-Regression: V2 is only initialized when explicitly requested
- Lazy loading: V2 components loaded on first use
- Graceful fallback: Returns legacy results if V2 fails
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Literal

from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

# Lazy-loaded V2 components
_hybrid_retriever = None
_v2_initialized = False


def _get_v2_retriever(
    workspace_root: Optional[str] = None,
    enable_reranker: bool = True,
    enable_context_expansion: bool = True,
    enable_router: bool = True,
):
    """
    Lazy-load the V2 HybridRetriever.

    Only initializes when first called (Zero-Regression Guard).
    """
    global _hybrid_retriever, _v2_initialized

    if _v2_initialized:
        return _hybrid_retriever

    # Import V2 components (lazy)
    try:
        from .hybrid_retriever import HybridRetriever
        from .ingestion import IngestionRun

        # Determine paths
        chroma_path = Path(get_app_data_dir()) / "rag_chroma_db_v2"
        fts_db_path = Path(get_app_data_dir()) / "knowledge_fts_v2.db"
        index_db_path = Path(get_app_data_dir()) / "knowledge_index_v2.db"

        # Initialize retriever
        _hybrid_retriever = HybridRetriever(
            chroma_path=str(chroma_path),
            fts_db_path=str(fts_db_path),
            index_db_path=str(index_db_path),
            use_reranker=enable_reranker,
            expand_context=enable_context_expansion,
        )

        # Initialize path policy with workspace root if provided
        if workspace_root:
            from .path_policy import set_global_policy
            set_global_policy(Path(workspace_root))

        _v2_initialized = True
        logger.info("[RAG V2 API Adapter] V2 HybridRetriever initialized")
        return _hybrid_retriever

    except ImportError as e:
        logger.warning(f"[RAG V2 API Adapter] V2 components not available: {e}")
        return None
    except Exception as e:
        logger.error(f"[RAG V2 API Adapter] Failed to initialize V2: {e}", exc_info=True)
        return None


def query_v2(
    query_text: str,
    workspace_root: Optional[str] = None,
    top_k: int = 10,
    file_type_filter: Optional[List[str]] = None,
    retrieval_mode_override: Optional[Literal["code", "prose", "hybrid"]] = None,
    enable_reranker: bool = True,
    enable_context_expansion: bool = True,
    enable_router: bool = True,
    filename: Optional[str] = None,
) -> Dict:
    """
    Execute a V2 hybrid retrieval query.

    Args:
        query_text: The search query.
        workspace_root: Workspace root path for path policy.
        top_k: Number of results to return.
        file_type_filter: Optional list of file extensions to filter.
        retrieval_mode_override: Override router decision ("code", "prose", "hybrid").
        enable_reranker: Enable cross-encoder reranking.
        enable_context_expansion: Enable context expansion.
        enable_router: Enable query router.
        filename: Optional filename to filter results (fuzzy match on source_path).

    Returns:
        Dict with results and metadata:
        {
            "results": [...],  # List of result dicts
            "mode": "v2",
            "num_results": int,
            "latency_ms": float,
            "router_mode": Optional[str],
        }
    """
    retriever = _get_v2_retriever(
        workspace_root=workspace_root,
        enable_reranker=enable_reranker,
        enable_context_expansion=enable_context_expansion,
    )

    if retriever is None:
        logger.warning("[RAG V2 API Adapter] V2 not available, returning empty results")
        return {
            "results": [],
            "mode": "v2",
            "num_results": 0,
            "latency_ms": 0,
            "error": "V2 not available",
        }

    try:
        results = retriever.query(
            query_text=query_text,
            top_k=top_k,
            use_router=enable_router,
            retrieval_mode=retrieval_mode_override,
            file_type_filter=file_type_filter,
            filename=filename,
        )

        return {
            "results": results,
            "mode": "v2",
            "num_results": len(results),
        }

    except Exception as e:
        logger.error(f"[RAG V2 API Adapter] Query failed: {e}", exc_info=True)
        return {
            "results": [],
            "mode": "v2",
            "num_results": 0,
            "error": str(e),
        }


def get_v2_status() -> Dict:
    """
    Get V2 system status for health checks.

    Returns:
        Dict with V2 status information:
        {
            "v2_available": bool,
            "v2_initialized": bool,
            "chroma_v2_path": str,
            "fts_v2_path": str,
            "index_v2_path": str,
            "indexed_files_count": int,
        }
    """
    from .index_store import IndexStore
    from .fts_store import FTSStore

    chroma_path = Path(get_app_data_dir()) / "rag_chroma_db_v2"
    fts_db_path = Path(get_app_data_dir()) / "knowledge_fts_v2.db"
    index_db_path = Path(get_app_data_dir()) / "knowledge_index_v2.db"

    indexed_count = 0
    fts_status = "unknown"

    try:
        # Try to get indexed file count
        if index_db_path.exists():
            store = IndexStore(db_path=str(index_db_path))
            all_files = store.get_all()
            indexed_count = len(all_files)
            store.close()
    except Exception:
        pass

    try:
        # Try to get FTS status
        if fts_db_path.exists():
            fts = FTSStore(db_path=str(fts_db_path))
            fts_status = "available"
            fts.close()
    except Exception:
        fts_status = "unavailable"

    return {
        "v2_available": _v2_initialized,
        "v2_initialized": _v2_initialized,
        "chroma_v2_path": str(chroma_path),
        "fts_v2_path": str(fts_db_path),
        "index_v2_path": str(index_db_path),
        "chroma_v2_exists": chroma_path.exists(),
        "fts_v2_exists": fts_db_path.exists(),
        "index_v2_exists": index_db_path.exists(),
        "indexed_files_count": indexed_count,
        "fts_status": fts_status,
    }

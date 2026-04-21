"""
RAG V2 Hybrid Retriever

Orchestrates dense (ChromaDB vector) + sparse (FTS5 keyword) search,
then fuses results via Reciprocal Rank Fusion (RRF).

Pipeline:
1. Embed query → query ChromaDB collection for top-k vector matches
2. Run FTS5 keyword search for top-k keyword matches
3. Fuse both rankings via RRF (k=60)
4. Return unified top-k results with provenance metadata
"""

import logging
import os
from typing import Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions

from backend.utils.paths import get_app_data_dir

from .fts_store import FTSStore
from .rrf import reciprocal_rank_fusion, K
from .ingestion import COLLECTION_CODE, COLLECTION_PROSE
from .reranker import CrossEncoderReranker
from .context_expander import ContextExpander
from .index_store import IndexStore

logger = logging.getLogger("janus_backend")

V2_CHROMA_PATH = os.path.join(get_app_data_dir(), "rag_chroma_db_v2")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class HybridRetriever:
    """
    Hybrid dense+sparse retriever with RRF fusion.

    Physical isolation guarantee: only uses rag_chroma_db_v2/.
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,  # P3: None = search both collections
        chroma_path: Optional[str] = None,
        fts_db_path: Optional[str] = None,
        index_db_path: Optional[str] = None,
        use_reranker: bool = True,  # P4: Enable cross-encoder reranking
        expand_context: bool = True,  # P4: Enable context expansion
    ):
        self.collection_name = collection_name  # P3: None = auto-detect both
        self.chroma_path = chroma_path or V2_CHROMA_PATH
        self.fts = FTSStore(db_path=fts_db_path)
        self.index_store = IndexStore(db_path=index_db_path)
        self.use_reranker = use_reranker
        self.expand_context = expand_context

        self._client = None
        self._collections: Dict[str, any] = {}  # P3: multi-collection support
        self._embedding_function = None
        self._reranker = None  # P4: lazy-loaded
        self._expander = None  # P4: lazy-loaded

    def _get_embedding_function(self):
        if self._embedding_function is None:
            logger.info(f"[HybridRetriever] Loading embedding model '{EMBEDDING_MODEL}'...")
            self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            )
        return self._embedding_function

    @property
    def client(self):
        if self._client is None:
            os.makedirs(self.chroma_path, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.chroma_path)
        return self._client

    def _get_collection(self, collection_name: str):
        """Get or create a ChromaDB collection by name (lazy)."""
        if collection_name not in self._collections:
            self._collections[collection_name] = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self._get_embedding_function(),
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[collection_name]

    def _get_collection_names(self) -> List[str]:
        """P3: Return list of collections to search."""
        if self.collection_name:
            return [self.collection_name]
        return [COLLECTION_CODE, COLLECTION_PROSE]

    def _vector_search_collection(self, query: str, collection_name: str, top_k: int = 10) -> List[Dict[str, any]]:
        """
        Query a single ChromaDB collection for top-k vector matches.

        Returns list of {chunk_id, distance, text, metadata, rank, collection}.
        """
        try:
            collection = self._get_collection(collection_name)
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Vector search failed for {collection_name}: {e}")
            return []

        if not results or not results["ids"] or not results["ids"][0]:
            return []

        vector_results = []
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        for rank_pos, (cid, text, meta, dist) in enumerate(
            zip(ids, docs, metas, dists), start=1
        ):
            vector_results.append(
                {
                    "chunk_id": cid,
                    "text": text,
                    "metadata": meta,
                    "distance": dist,
                    "rank": rank_pos,
                    "collection": collection_name,
                }
            )

        logger.debug(f"Vector search [{collection_name}] returned {len(vector_results)} results")
        return vector_results

    def _vector_search(self, query: str, top_k: int = 10) -> List[Dict[str, any]]:
        """
        P3: Query all relevant collections and merge results.

        When collection_name is set, search only that collection.
        Otherwise search both kb_code_v2 and kb_prose_v2.
        """
        all_results = []
        collections = self._get_collection_names()
        per_collection_k = max(top_k // len(collections), 5)

        for coll_name in collections:
            results = self._vector_search_collection(query, coll_name, per_collection_k)
            all_results.extend(results)

        # Re-rank merged results by distance (best first)
        all_results.sort(key=lambda r: r["distance"])

        # Assign new merged ranks
        for rank_pos, result in enumerate(all_results, start=1):
            result["rank"] = rank_pos

        logger.debug(f"Vector search merged {len(all_results)} results from {len(collections)} collections")
        return all_results[:top_k]

    def _keyword_search(self, query: str, top_k: int = 10) -> List[Dict[str, any]]:
        """
        Query FTS5 index for top-k keyword matches.

        Returns list of {chunk_id, text, bm25_rank, rank}.
        """
        results = self.fts.search(query, top_k=top_k)
        logger.debug(f"Keyword search returned {len(results)} results")
        return results

    def _get_reranker(self) -> CrossEncoderReranker:
        """Lazy-load the cross-encoder reranker."""
        if self._reranker is None:
            self._reranker = CrossEncoderReranker.get_instance()
        return self._reranker

    def _get_expander(self) -> ContextExpander:
        """Lazy-load the context expander."""
        if self._expander is None:
            self._expander = ContextExpander(self.index_store)
        return self._expander

    def query(
        self,
        query_text: str,
        top_k: int = 10,
        vector_k: int = 20,
        keyword_k: int = 20,
        k: int = K,
        rerank_k: int = 5,  # P4: Top-k after reranking
        expand_window: int = 1,  # P4: ±N chunks for context expansion
    ) -> List[Dict[str, any]]:
        """
        Execute P4 hybrid retrieval: vector + keyword → RRF → Rerank → Expand → Final.

        Args:
            query_text: The user query string.
            top_k: Number of final results to return.
            vector_k: Number of candidates from vector search.
            keyword_k: Number of candidates from keyword search.
            k: RRF constant (default 60).
            rerank_k: Number of results to keep after reranking (default 5).
            expand_window: Number of chunks to expand on each side (default 1).

        Returns:
            List of result dicts ordered by relevance (best first):
            {
                "chunk_id": str,
                "text": str,
                "source_path": str,
                "metadata": dict,
                "rrf_score": float,
                "rerank_score": Optional[float],
                "is_expanded": bool,
                "vector_rank": Optional[int],
                "keyword_rank": Optional[int],
                "distance": Optional[float],
                "bm25_rank": Optional[float],
            }
        """
        logger.info(
            f"Hybrid query: '{query_text[:60]}...' (vector_k={vector_k}, keyword_k={keyword_k}, k={k})"
        )

        # 1. Dense search (vector)
        vector_results = self._vector_search(query_text, top_k=vector_k)

        # 2. Sparse search (keyword)
        keyword_results = self._keyword_search(query_text, top_k=keyword_k)

        # Build RRF input: list of [(chunk_id, score), ...] per source
        vector_ranking = [(r["chunk_id"], 1.0 / r["rank"]) for r in vector_results]
        keyword_ranking = [(r["chunk_id"], 1.0 / r["rank"]) for r in keyword_results]

        # 3. Fuse via RRF (get top-20 for reranking)
        fused = reciprocal_rank_fusion([vector_ranking, keyword_ranking], k=k)
        rrf_candidates = fused[:20]  # P4: Keep top-20 for reranking

        # 4. Build lookup maps for enrichment
        vector_map: Dict[str, Dict] = {r["chunk_id"]: r for r in vector_results}
        keyword_map: Dict[str, Dict] = {r["chunk_id"]: r for r in keyword_results}

        # 5. Build candidate list for reranking
        candidates = []
        for chunk_id, rrf_score in rrf_candidates:
            v = vector_map.get(chunk_id)
            k = keyword_map.get(chunk_id)
            text = v["text"] if v else (k["text"] if k else "")
            metadata = v["metadata"] if v else {}
            source_path = metadata.get("source_path", k["source_path"] if k else "")
            candidates.append(
                {
                    "chunk_id": chunk_id,
                    "text": text,
                    "source_path": source_path,
                    "metadata": metadata,
                    "rrf_score": rrf_score,
                    "vector_rank": v["rank"] if v else None,
                    "keyword_rank": k["rank"] if k else None,
                    "distance": v["distance"] if v else None,
                    "bm25_rank": k["bm25_rank"] if k else None,
                }
            )

        # 6. P4: Rerank with cross-encoder (if enabled)
        if self.use_reranker:
            reranker = self._get_reranker()
            if reranker.is_available():
                candidates = reranker.rerank(query_text, candidates, top_k=rerank_k)
                logger.info(f"[P4] Reranked to {len(candidates)} results")
            else:
                logger.debug("[P4] Reranker not available, using RRF ranking")
                candidates = candidates[:rerank_k]
        else:
            candidates = candidates[:rerank_k]

        # 7. P4: Context expansion (if enabled)
        if self.expand_context:
            expander = self._get_expander()
            expanded = expander.expand(candidates, expand_window=expand_window, max_expanded=top_k)
            stats = expander.get_expansion_stats(expanded)
            logger.info(
                f"[P4] Context expansion: {stats['original_count']} → {stats['total_count']} chunks "
                f"(added {stats['expanded_count']}, {stats['unique_sources']} sources)"
            )
            final_results = expanded[:top_k]
        else:
            final_results = candidates[:top_k]

        # 8. Add collection provenance
        for r in final_results:
            v = vector_map.get(r["chunk_id"])
            if v:
                r["collection"] = v.get("collection", "unknown")

        logger.info(
            f"Hybrid query returned {len(final_results)} results "
            f"(from {len(vector_results)} vector + {len(keyword_results)} keyword)"
        )
        return final_results

    def close(self) -> None:
        self.fts.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

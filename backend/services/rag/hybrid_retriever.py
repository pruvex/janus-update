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
        collection_name: str = "kb_code_v2",
        chroma_path: Optional[str] = None,
        fts_db_path: Optional[str] = None,
    ):
        self.collection_name = collection_name
        self.chroma_path = chroma_path or V2_CHROMA_PATH
        self.fts = FTSStore(db_path=fts_db_path)

        self._client = None
        self._collection = None
        self._embedding_function = None

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

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._get_embedding_function(),
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _vector_search(self, query: str, top_k: int = 10) -> List[Dict[str, any]]:
        """
        Query ChromaDB collection for top-k vector matches.

        Returns list of {chunk_id, distance, text, metadata, rank}.
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
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
                }
            )

        logger.debug(f"Vector search returned {len(vector_results)} results")
        return vector_results

    def _keyword_search(self, query: str, top_k: int = 10) -> List[Dict[str, any]]:
        """
        Query FTS5 index for top-k keyword matches.

        Returns list of {chunk_id, text, bm25_rank, rank}.
        """
        results = self.fts.search(query, top_k=top_k)
        logger.debug(f"Keyword search returned {len(results)} results")
        return results

    def query(
        self,
        query_text: str,
        top_k: int = 10,
        vector_k: int = 20,
        keyword_k: int = 20,
        k: int = K,
    ) -> List[Dict[str, any]]:
        """
        Execute hybrid retrieval: vector + keyword → RRF fusion.

        Args:
            query_text: The user query string.
            top_k: Number of final fused results to return.
            vector_k: Number of candidates from vector search.
            keyword_k: Number of candidates from keyword search.
            k: RRF constant (default 60).

        Returns:
            List of result dicts ordered by fused relevance (best first):
            {
                "chunk_id": str,
                "text": str,
                "source_path": str,
                "metadata": dict,
                "rrf_score": float,
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

        # 3. Fuse via RRF
        fused = reciprocal_rank_fusion([vector_ranking, keyword_ranking], k=k)

        # 4. Build lookup maps for enrichment
        vector_map: Dict[str, Dict] = {r["chunk_id"]: r for r in vector_results}
        keyword_map: Dict[str, Dict] = {r["chunk_id"]: r for r in keyword_results}

        # 5. Enrich and return top-k
        final_results = []
        for rank_pos, (chunk_id, rrf_score) in enumerate(fused[:top_k], start=1):
            v = vector_map.get(chunk_id)
            k = keyword_map.get(chunk_id)

            # Prefer vector text/metadata if available, fallback to keyword
            text = v["text"] if v else (k["text"] if k else "")
            metadata = v["metadata"] if v else {}
            source_path = metadata.get("source_path", k["source_path"] if k else "")

            final_results.append(
                {
                    "chunk_id": chunk_id,
                    "text": text,
                    "source_path": source_path,
                    "metadata": metadata,
                    "rrf_score": rrf_score,
                    "rank": rank_pos,
                    "vector_rank": v["rank"] if v else None,
                    "keyword_rank": k["rank"] if k else None,
                    "distance": v["distance"] if v else None,
                    "bm25_rank": k["bm25_rank"] if k else None,
                }
            )

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

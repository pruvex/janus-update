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
import time
from pathlib import PurePath
from typing import Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions

from backend.utils.paths import get_app_data_dir

from .fts_store import FTSStore
from .rrf import reciprocal_rank_fusion, weighted_reciprocal_rank_fusion, K
from .ingestion import COLLECTION_CODE, COLLECTION_PROSE
from .reranker import CrossEncoderReranker
from .context_expander import ContextExpander
from .index_store import IndexStore
from .query_router import route as query_route, RouterDecision
from .retrieval_logger import get_retrieval_logger

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
        use_router: bool = True,
    ):
        self.collection_name = collection_name  # P3: None = auto-detect both
        self.chroma_path = chroma_path or V2_CHROMA_PATH
        self.fts = FTSStore(db_path=fts_db_path)
        self.index_store = IndexStore(db_path=index_db_path)
        self.use_reranker = use_reranker
        self.expand_context = expand_context
        self.use_router = use_router

        self._client = None
        self._collections: Dict[str, any] = {}  # P3: multi-collection support
        self._embedding_function = None
        self._reranker = None  # P4: lazy-loaded
        self._expander = None  # P4: lazy-loaded
        self.retrieval_logger = get_retrieval_logger()  # P6: Retrieval logger

    @staticmethod
    def _normalize_path(p: str) -> str:
        """Convert backslashes to forward slashes and lowercase for path comparison."""
        return p.replace("\\", "/").lower() if p else p

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
        use_router: bool = True,  # P5: Enable query router
        retrieval_mode: Optional[str] = None,  # P5: Override router: "code" | "prose" | "hybrid"
        file_type_filter: Optional[List[str]] = None,  # P5: Optional file extension filter
        filename: Optional[str] = None,  # Fuzzy filename resolution: filter by source_path endswith(filename)
    ) -> List[Dict[str, any]]:
        """
        Execute P5 hybrid retrieval: Router → vector + keyword → Weighted RRF → Rerank → Expand → Final.

        Args:
            query_text: The user query string.
            top_k: Number of final results to return.
            vector_k: Number of candidates from vector search.
            keyword_k: Number of candidates from keyword search.
            k: RRF constant (default 60).
            rerank_k: Number of results to keep after reranking (default 5).
            expand_window: Number of chunks to expand on each side (default 1).
            use_router: P5: Enable query-based routing (code/prose/hybrid detection).
            retrieval_mode: P5: Override router decision. "code" | "prose" | "hybrid".
            file_type_filter: P5: Optional list of file extensions to filter results.
            filename: Fuzzy filename resolution: filter results by source_path endswith(filename).

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
                "router_mode": Optional[str],
                "vector_rank": Optional[int],
                "keyword_rank": Optional[int],
                "distance": Optional[float],
                "bm25_rank": Optional[float],
            }
        """
        # P5: Route query to determine search strategy
        router_decision = None
        if use_router:
            if retrieval_mode:
                # Manual override
                from .query_router import RouterDecision
                if retrieval_mode == "code":
                    router_decision = RouterDecision(
                        mode="code_heavy",
                        collections=["kb_code_v2"],
                        vector_weight=0.25,
                        keyword_weight=0.75,
                        code_bias=+1.0,
                    )
                elif retrieval_mode == "prose":
                    router_decision = RouterDecision(
                        mode="prose_heavy",
                        collections=["kb_prose_v2"],
                        vector_weight=0.80,
                        keyword_weight=0.20,
                        code_bias=-1.0,
                    )
                else:
                    router_decision = RouterDecision(
                        mode="hybrid",
                        collections=["kb_code_v2", "kb_prose_v2"],
                        vector_weight=0.50,
                        keyword_weight=0.50,
                        code_bias=0.0,
                    )
            else:
                router_decision = query_route(query_text)

            logger.info(
                f"[P5] Router: mode={router_decision.mode} "
                f"collections={router_decision.collections} "
                f"v_w={router_decision.vector_weight:.2f} k_w={router_decision.keyword_weight:.2f}"
            )

            # Override collection targets for this query
            if router_decision.mode == "code_heavy":
                self.collection_name = COLLECTION_CODE
            elif router_decision.mode == "prose_heavy":
                self.collection_name = COLLECTION_PROSE
            else:
                self.collection_name = None  # Search both

        logger.info(
            f"Hybrid query: '{query_text[:60]}...' (vector_k={vector_k}, keyword_k={keyword_k}, k={k})"
        )

        # P6: Latency tracking
        latencies = {}
        overall_start = time.time()

        # LOCKDOWN: When filename is provided, skip global search entirely.
        # Only use index_store lookup + rescue path. This prevents the system
        # from falling back to global search when the filename filter fails.
        if filename:
            logger.info(f"[FILENAME-LOCKDOWN] Skipping global search, using index_store-only mode for '{filename}'")
            # Initialize empty results for the global search path
            vector_results = []
            keyword_results = []
            vector_map = {}
            keyword_map = {}
            candidates = []
            latencies["vector_ms"] = 0.0
            latencies["keyword_ms"] = 0.0
            latencies["rrf_ms"] = 0.0
        else:
            # 1. Dense search (vector)
            vec_start = time.time()
            vector_results = self._vector_search(query_text, top_k=vector_k)
            latencies["vector_ms"] = (time.time() - vec_start) * 1000

            # 2. Sparse search (keyword)
            fts_start = time.time()
            keyword_results = self._keyword_search(query_text, top_k=keyword_k)
            latencies["keyword_ms"] = (time.time() - fts_start) * 1000

            # Build RRF input: list of [(chunk_id, score), ...] per source
            vector_ranking = [(r["chunk_id"], 1.0 / r["rank"]) for r in vector_results]
            keyword_ranking = [(r["chunk_id"], 1.0 / r["rank"]) for r in keyword_results]

            # 3. Fuse via RRF (get top-20 for reranking)
            # P5: Use weighted RRF if router is active
            rrf_start = time.time()
            if router_decision and (router_decision.vector_weight != 0.5 or router_decision.keyword_weight != 0.5):
                fused = weighted_reciprocal_rank_fusion(
                    [vector_ranking, keyword_ranking],
                    weights=[router_decision.vector_weight, router_decision.keyword_weight],
                    k=k,
                )
            else:
                fused = reciprocal_rank_fusion([vector_ranking, keyword_ranking], k=k)
            latencies["rrf_ms"] = (time.time() - rrf_start) * 1000
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
        rerank_start = time.time()
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
        latencies["rerank_ms"] = (time.time() - rerank_start) * 1000

        # 7. P4: Context expansion (if enabled)
        expand_start = time.time()
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
        latencies["expand_ms"] = (time.time() - expand_start) * 1000
        latencies["total_ms"] = (time.time() - overall_start) * 1000

        # Add collection provenance
        for r in final_results:
            v = vector_map.get(r["chunk_id"])
            if v:
                r["collection"] = v.get("collection", "unknown")

        # P5: Add router metadata to results
        if router_decision:
            for r in final_results:
                r["router_mode"] = router_decision.mode
                r["router_code_bias"] = router_decision.code_bias

        # P5: Apply file_type_filter if specified
        if file_type_filter and final_results:
            filtered = []
            for r in final_results:
                source = r.get("source_path", "")
                ext = os.path.splitext(source)[1].lower()
                if any(f.lower() == ext or f.lower() == ext.lstrip(".") for f in file_type_filter):
                    filtered.append(r)
            if filtered:
                final_results = filtered
                logger.info(f"[P5] File type filter applied: {len(final_results)} results remain")

        # Fuzzy filename resolution: robust path-based matcher.
        # Normalizes both needle and haystack to stems (no extension, lowercase)
        # and converts all backslashes to forward slashes for Windows compatibility.
        # So "aegypten", "aegypten.pdf", "AEGYPTEN.PDF",
        # "C:\foo\aegypten.pdf" all collide with a DB path like
        # "C:\Users\...\JanusPDFs\aegypten.pdf".
        if filename:
            filter_start = time.time()

            needle = PurePath(filename).name.lower()
            needle_stem = PurePath(needle).stem  # strips extension
            logger.info(f"[FILENAME-FILTER] needle='{filename}' -> stem='{needle_stem}'")

            def _path_matches(source: str) -> bool:
                if not source:
                    return False
                # Normalize slashes and case before comparison
                source_norm = self._normalize_path(source)
                basename = PurePath(source_norm).name
                if basename == needle or basename == needle_stem:
                    return True
                source_stem = PurePath(basename).stem
                return source_stem == needle_stem

            # LOCKDOWN: When filename is provided, ONLY filtered search + rescue.
            # NEVER fall back to global search results.
            # Skip the global retrieval entirely and go straight to index_store.
            all_found_paths: set = set()
            try:
                # Query by stem; find_by_filename uses LIKE '%{needle}' → broader,
                # we then apply _path_matches to be strict on basename/stem.
                indexed_candidates = self.index_store.find_by_filename(needle_stem)
                for idx_file in indexed_candidates:
                    # Normalize path before comparison
                    if _path_matches(idx_file.path):
                        all_found_paths.add(idx_file.path)
            except Exception as exc:
                logger.warning(f"[FILENAME-FILTER] IndexStore lookup failed: {exc}")

            # DUPLICATE DETECTION: Check if multiple files with the same name exist
            all_paths_for_filename = self.index_store.get_all_paths_for_filename(filename)
            has_duplicates = len(all_paths_for_filename) > 1

            # Filter current retrieval results (may be empty if we skipped global search)
            filtered = [r for r in final_results if _path_matches(r.get("source_path", ""))]

            # RESCUE: If retrieval returned nothing for this file but the file
            # IS indexed, fetch its chunks directly so the LLM gets real content
            # instead of a global fallback.
            if not filtered and all_found_paths:
                logger.warning(
                    f"[FILENAME-FILTER] Retrieval miss for '{filename}', "
                    f"rescuing chunks for: {sorted(all_found_paths)}"
                )
                rescued: List[Dict[str, any]] = []
                try:
                    for path in sorted(all_found_paths):
                        for chunk in self.index_store.get_chunks_by_file(path):
                            rescued.append({
                                "chunk_id": chunk["chunk_id"],
                                "text": chunk.get("text", ""),
                                "source_path": path,
                                "metadata": chunk.get("metadata", {}),
                                "rrf_score": 0.0,
                                "rescued": True,
                            })
                except Exception as exc:
                    logger.warning(f"[FILENAME-FILTER] Rescue fetch failed: {exc}")
                filtered = rescued[:top_k]

            if filtered:
                final_results = filtered
                # Ensure every path that matched is reported, even if only one
                # chunk survived the filter (this is the ambiguity signal).
                for r in final_results:
                    all_found_paths.add(r.get("source_path", ""))
                all_found_paths.discard("")
                for r in final_results:
                    r["all_matched_paths"] = sorted(list(all_found_paths))
                logger.info(
                    f"[FILENAME-FILTER] Applied for '{filename}': "
                    f"{len(final_results)} chunks, {len(all_found_paths)} distinct file(s)"
                )
            else:
                logger.warning(f"[FILENAME-FILTER] No results found matching filename '{filename}' - LOCKDOWN: Returning empty instead of global search")
                final_results = []
                latencies["filename_filter_ms"] = (time.time() - filter_start) * 1000
                # Early return to prevent any fallback to global search
                return RetrievalResult(
                    results=[],
                    query_text=query_text,
                    latencies=latencies,
                    router_decision=router_decision,
                    metadata={"filename": filename, "lockdown": True}
                )
            latencies["filename_filter_ms"] = (time.time() - filter_start) * 1000

        # Inject source header directly into text to make it inseparable for LLMs
        for r in final_results:
            source_path = r.get("source_path", "")
            if source_path:
                source_header = f"[DOKUMENT-QUELLE: {source_path}]"
                r["text"] = f"{source_header}\n\n{r.get('text', '')}"
                # DUPLICATE WARNING: If multiple files with same name exist, add prominent warning
                if has_duplicates and len(all_paths_for_filename) > 1:
                    paths_info = "\n".join(f"  - {p}" for p in sorted(all_paths_for_filename))
                    warning_block = f"!!! SYSTEM-WARNHINWEIS: MEHRERE DATEIEN GEFUNDEN !!!\nDateiname: {filename}\nGefundene Pfade:\n{paths_info}\nAktuelle Auswahl: {source_path}"
                    r["text"] = f"{warning_block}\n\n{r['text']}"
                # Legacy: If all_matched_paths exists, add it as a prominent warning block
                all_matched = r.get("all_matched_paths")
                if all_matched and len(all_matched) > 1:
                    paths_info = "\n".join(f"  - {p}" for p in all_matched)
                    warning_block = f"!!! SYSTEM-WARNHINWEIS: MEHRERE DATEIEN GEFUNDEN !!!\nPfade:\n{paths_info}"
                    r["text"] = f"{warning_block}\n\n{r['text']}"

        logger.info(
            f"Hybrid query returned {len(final_results)} results "
            f"(from {len(vector_results)} vector + {len(keyword_results)} keyword)"
        )

        # P6: Log retrieval with latency breakdown
        router_dict = None
        if router_decision:
            router_dict = {
                "mode": router_decision.mode,
                "collections": router_decision.collections,
                "vector_weight": router_decision.vector_weight,
                "keyword_weight": router_decision.keyword_weight,
                "code_bias": router_decision.code_bias,
            }

        top_result = final_results[0] if final_results else None
        top_dict = None
        if top_result:
            top_dict = {
                "chunk_id": top_result.get("chunk_id"),
                "source_path": top_result.get("source_path"),
                "rrf_score": top_result.get("rrf_score"),
            }

        self.retrieval_logger.log_query(
            query=query_text,
            router_decision=router_dict,
            latency_breakdown=latencies,
            top_result=top_dict,
            num_results=len(final_results),
        )

        return final_results

    def close(self) -> None:
        self.fts.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

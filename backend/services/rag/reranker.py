"""
RAG V2 Cross-Encoder Reranker

Provides re-ranking of retrieved chunks using a cross-encoder model.
Singleton pattern with lazy-loading and thread-safe initialization.
Graceful fallback to original ranking if model loading fails.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("janus_backend")

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    """
    Singleton cross-encoder reranker with lazy loading and thread safety.

    Usage:
        reranker = CrossEncoderReranker.get_instance()
        reranked = reranker.rerank(query, candidates, top_k=5)
    """

    _instance = None
    _lock = threading.Lock()
    _model = None
    _model_loaded = False
    _model_load_failed = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "CrossEncoderReranker":
        """Get the singleton instance."""
        return cls()

    def _load_model(self) -> bool:
        """
        Load the cross-encoder model on first use (lazy loading).

        Returns True if successful, False on failure.
        """
        if self._model_loaded:
            return True

        if self._model_load_failed:
            # Don't retry if load already failed
            return False

        with self._lock:
            # Double-check after acquiring lock
            if self._model_loaded:
                return True
            if self._model_load_failed:
                return False

            try:
                logger.info(f"[CrossEncoderReranker] Loading model '{MODEL_NAME}'...")
                from sentence_transformers import CrossEncoder

                start_time = time.time()
                self._model = CrossEncoder(MODEL_NAME)
                load_time = time.time() - start_time

                self._model_loaded = True
                logger.info(
                    f"[CrossEncoderReranker] Model loaded in {load_time:.2f}s. "
                    f"Max sequence length: {self._model.max_seq_length}"
                )
                return True

            except ImportError:
                logger.error(
                    "[CrossEncoderReranker] sentence-transformers not installed. "
                    "Reranking disabled, falling back to original ranking."
                )
                self._model_load_failed = True
                return False

            except Exception as e:
                logger.error(
                    f"[CrossEncoderReranker] Failed to load model: {e}. "
                    "Reranking disabled, falling back to original ranking."
                )
                self._model_load_failed = True
                return False

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, any]],
        top_k: int = 5,
    ) -> List[Dict[str, any]]:
        """
        Re-rank candidate chunks using cross-encoder.

        Args:
            query: The search query.
            candidates: List of candidate dicts with 'chunk_id', 'text', 'metadata'.
            top_k: Number of top results to return.

        Returns:
            Re-ranked list of candidates with 'rerank_score' added.
            If model loading fails, returns original top_k candidates unchanged.
        """
        if not candidates:
            return []

        if not self._load_model():
            # Graceful fallback: return original ranking
            logger.debug("[CrossEncoderReranker] Model not loaded, returning original ranking")
            return candidates[:top_k]

        try:
            # Prepare query-document pairs
            pairs = [(query, cand["text"]) for cand in candidates]

            # Compute cross-encoder scores
            start_time = time.time()
            scores = self._model.predict(pairs)
            inference_time = time.time() - start_time

            logger.debug(
                f"[CrossEncoderReranker] Reranked {len(candidates)} candidates "
                f"in {inference_time*1000:.1f}ms"
            )

            # Add scores to candidates
            for cand, score in zip(candidates, scores):
                cand["rerank_score"] = float(score)

            # Sort by rerank score (descending)
            reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)

            # Update ranks
            for rank_pos, cand in enumerate(reranked, start=1):
                cand["rerank_rank"] = rank_pos

            return reranked[:top_k]

        except Exception as e:
            logger.error(f"[CrossEncoderReranker] Reranking failed: {e}, falling back to original ranking")
            return candidates[:top_k]

    def is_available(self) -> bool:
        """Check if the reranker model is available."""
        return self._model_loaded and self._model is not None

    def get_model_info(self) -> Dict[str, any]:
        """Get information about the loaded model."""
        if not self._model_loaded:
            return {"loaded": False, "model_name": MODEL_NAME}

        return {
            "loaded": True,
            "model_name": MODEL_NAME,
            "max_seq_length": self._model.max_seq_length,
        }

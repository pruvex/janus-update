"""
RAG V2 Context Expander

Expands retrieved chunks with surrounding context (±1 chunks) from the index_store.
Provides deduplication to avoid duplicate chunks in the final result.
"""

import logging
from typing import Dict, List, Optional, Set

from .index_store import IndexStore

logger = logging.getLogger("janus_backend")


class ContextExpander:
    """
    Expands top-k results with surrounding chunks for better context.

    Strategy:
    - For each top-k chunk, load ±1 neighboring chunks from the same file.
    - Deduplicate by chunk_id to avoid repeats.
    - Preserve original ranking order.
    """

    def __init__(self, index_store: IndexStore):
        self.index_store = index_store

    def expand(
        self,
        results: List[Dict[str, any]],
        expand_window: int = 1,
        max_expanded: int = 20,
    ) -> List[Dict[str, any]]:
        """
        Expand results with surrounding chunks.

        Args:
            results: List of result dicts with 'chunk_id', 'text', 'metadata'.
            expand_window: Number of chunks to expand on each side (default: 1).
            max_expanded: Maximum number of chunks after expansion (default: 20).

        Returns:
            Expanded list of results with 'is_expanded' flag added.
        """
        if not results:
            return []

        # Track seen chunk_ids for deduplication
        seen_ids: Set[str] = set()
        expanded_results: List[Dict[str, any]] = []

        # Add original results first (preserve ranking)
        for result in results:
            chunk_id = result["chunk_id"]
            if chunk_id not in seen_ids:
                result["is_expanded"] = False
                expanded_results.append(result)
                seen_ids.add(chunk_id)

            # Load surrounding chunks
            surrounding = self._get_surrounding_chunks(chunk_id, expand_window)
            for surr in surrounding:
                surr_id = surr["chunk_id"]
                if surr_id not in seen_ids:
                    surr["is_expanded"] = True
                    surr["expanded_from"] = chunk_id
                    expanded_results.append(surr)
                    seen_ids.add(surr_id)

                    # Stop if we hit max limit
                    if len(expanded_results) >= max_expanded:
                        break

            if len(expanded_results) >= max_expanded:
                break

        logger.debug(
            f"[ContextExpander] Expanded {len(results)} chunks to {len(expanded_results)} "
            f"(window=±{expand_window}, max={max_expanded})"
        )
        return expanded_results

    def _get_surrounding_chunks(
        self, chunk_id: str, window: int
    ) -> List[Dict[str, any]]:
        """
        Load surrounding chunks for a given chunk_id.

        Args:
            chunk_id: The chunk ID to expand around.
            window: Number of chunks to load on each side.

        Returns:
            List of surrounding chunk dicts.
        """
        try:
            # Get chunk metadata from index_store
            chunk_meta = self.index_store.get_chunk(chunk_id)
            if not chunk_meta:
                return []

            source_path = chunk_meta.get("source_path")
            if not source_path:
                return []

            # Get all chunks from the same file
            file_chunks = self.index_store.get_chunks_by_file(source_path)
            if not file_chunks:
                return []

            # Find the current chunk's position
            current_idx = -1
            for idx, fc in enumerate(file_chunks):
                if fc["chunk_id"] == chunk_id:
                    current_idx = idx
                    break

            if current_idx == -1:
                return []

            # Extract surrounding chunks
            start_idx = max(0, current_idx - window)
            end_idx = min(len(file_chunks), current_idx + window + 1)

            surrounding = []
            for idx in range(start_idx, end_idx):
                if idx != current_idx:  # Skip the current chunk itself
                    fc = file_chunks[idx]
                    surrounding.append(
                        {
                            "chunk_id": fc["chunk_id"],
                            "text": fc.get("text", ""),
                            "metadata": fc.get("metadata", {}),
                        }
                    )

            return surrounding

        except Exception as e:
            logger.error(f"[ContextExpander] Failed to get surrounding chunks for {chunk_id}: {e}")
            return []

    def get_expansion_stats(self, results: List[Dict[str, any]]) -> Dict[str, int]:
        """
        Calculate expansion statistics for a result set.

        Returns dict with:
        - original_count: number of original (non-expanded) chunks
        - expanded_count: number of expanded chunks
        - total_count: total number of chunks
        - unique_sources: number of unique source files
        """
        original = sum(1 for r in results if not r.get("is_expanded", False))
        expanded = sum(1 for r in results if r.get("is_expanded", False))
        unique_sources = len(set(r.get("metadata", {}).get("source_path", "") for r in results))

        return {
            "original_count": original,
            "expanded_count": expanded,
            "total_count": len(results),
            "unique_sources": unique_sources,
        }

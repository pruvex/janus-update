# backend/services/vector_service.py

import functools
import json
import logging
import os
import threading
import time
from typing import Any, List, Optional

import chromadb
import numpy as np
from backend.utils.paths import get_app_data_dir

# Configure environment variables for better control
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_OFFLINE"] = "0"

logger = logging.getLogger("janus_backend")
CHROMA_PATH = os.path.join(get_app_data_dir(), "rag_chroma_db")

# --- LAZY LOADING IMPLEMENTATION ---

_model: Optional[Any] = None
_model_name = "all-MiniLM-L6-v2"
_model_loading = False
_model_ready_event = threading.Event()

# --- ISSUE 011: QUERY EMBEDDING CACHE (Thread-Safe) ---
# FastAPI workers are process-isolated, so a simple dict + lock is sufficient.
# LRU behavior via functools.lru_cache on the internal function.

_query_embedding_cache: dict = {}
_cache_lock = threading.Lock()
_MAX_CACHE_SIZE = 128


def _get_cached_embedding(text: str) -> Optional[np.ndarray]:
    """Internal cache lookup (thread-safe)."""
    with _cache_lock:
        return _query_embedding_cache.get(text)


def _set_cached_embedding(text: str, embedding: np.ndarray) -> None:
    """Internal cache store with LRU eviction (thread-safe)."""
    with _cache_lock:
        if len(_query_embedding_cache) >= _MAX_CACHE_SIZE:
            # Simple LRU: remove oldest entry (first key)
            oldest_key = next(iter(_query_embedding_cache))
            del _query_embedding_cache[oldest_key]
        _query_embedding_cache[text] = embedding


def get_query_embedding(text: str) -> Optional[np.ndarray]:
    """
    Generiert ein Query-Embedding mit LRU-Cache.
    Wiederverwendbar für mehrere Vector-Suchen in einem Retrieval-Durchlauf.
    """
    # Normalize text for cache key
    cache_key = text.replace("\n", " ").strip()
    if not cache_key:
        return None
    
    # Cache hit?
    cached = _get_cached_embedding(cache_key)
    if cached is not None:
        logger.debug(f"[EMBEDDING CACHE] Hit for query: {cache_key[:50]}...")
        return cached
    
    # Cache miss: compute
    model = _get_model()
    if model is None:
        logger.error("Embedding-Modell ist nicht verfügbar.")
        return None
    
    try:
        embedding = model.encode(cache_key)
        _set_cached_embedding(cache_key, embedding)
        logger.debug(f"[EMBEDDING CACHE] Miss - computed & cached: {cache_key[:50]}...")
        return embedding
    except Exception as e:
        logger.error(f"Fehler bei der Embedding-Generierung: {e}")
        return None


def clear_embedding_cache() -> None:
    """Clears the query embedding cache (useful for testing)."""
    with _cache_lock:
        _query_embedding_cache.clear()
        logger.info("[EMBEDDING CACHE] Cleared.")


# --- END ISSUE 011 ---

def is_model_loading() -> bool:
    return bool(_model_loading and _model is None)


def warmup_status_text() -> str:
    return "System wird noch warm..."


def _load_model_sync() -> Optional[Any]:
    global _model, _model_loading
    if _model is not None:
        _model_ready_event.set()
        return _model
    _model_loading = True
    try:
        # Pfad-Konfiguration (nur beim Laden relevant)
        app_data = get_app_data_dir()
        model_cache_path = os.path.join(app_data, "model_cache")
        os.makedirs(model_cache_path, exist_ok=True)
        os.environ["SENTENCE_TRANSFORMERS_HOME"] = model_cache_path

        logger.info(f"LAZY LOAD: Lade Vektor-Modell '{_model_name}' jetzt...")
        start_time = time.time()
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(
            _model_name,
            cache_folder=model_cache_path,
            device="cpu"
        )
        end_time = time.time()
        logger.info(f"LAZY LOAD: Vektor-Modell in {end_time - start_time:.2f} Sekunden geladen.")
        _model_ready_event.set()
        return _model
    except Exception as e:
        logger.error(f"LAZY LOAD: Fehler beim Laden des Vektor-Modells: {str(e)}", exc_info=True)
        logger.warning("Vektor-Suche wird deaktiviert sein.")
        _model = None
        _model_ready_event.clear()
        return None
    finally:
        _model_loading = False


def start_background_model_load() -> None:
    """Start model loading in background thread (non-blocking startup)."""
    global _model_loading
    if _model is not None or _model_loading:
        return
    logger.info("💎 [STARTUP] Vektor-Modell wird im Hintergrund geladen...")

    def _runner() -> None:
        _load_model_sync()

    _model_loading = True
    threading.Thread(target=_runner, name="janus-vector-warmup", daemon=True).start()


def _get_model(wait_for_model: bool = True) -> Optional[Any]:
    """
    Lädt das SentenceTransformer-Modell beim ersten Aufruf ("lazy").
    Gibt das geladene Modell aus einem globalen Cache zurück.
    """
    global _model
    # Wenn das Modell schon geladen ist, gib es sofort zurück
    if _model is not None:
        return _model

    if not wait_for_model:
        start_background_model_load()
        return None

    if _model_loading:
        _model_ready_event.wait(timeout=30)
        if _model is not None:
            return _model
    return _load_model_sync()

# --- ENDE LAZY LOADING ---

def generate_embedding(text: str, wait_for_model: bool = True) -> Optional[str]:
    """Generiert einen Vektor-Embedding für einen gegebenen Text."""
    model = _get_model(wait_for_model=wait_for_model) # Modell "lazy" anfordern
    if model is None:
        if wait_for_model:
            logger.error("Embedding-Modell ist nicht verfügbar.")
        else:
            logger.debug("Embedding-Modell lädt noch im Hintergrund (non-blocking Pfad).")
        return None
    try:
        text = text.replace("\n", " ").strip()
        embedding = model.encode(text)
        return json.dumps(embedding.tolist())
    except Exception as e:
        logger.error(f"Fehler bei der Embedding-Generierung für Text '{text}': {e}")
        return None


def _safe_stack_embeddings(
    candidate_embeddings: List[Any],
    expected_dim: Optional[int] = None,
) -> tuple[List[int], Optional[np.ndarray], int]:
    """Filtert invalide Embeddings (None, falsche Shape, falsche Dimension) aus einer heterogenen
    Kandidatenliste und stackt den Rest in ein kompaktes np.ndarray (float32).

    Gibt zurück:
        valid_indices: Die Original-Indizes der validen Embeddings (für Score-Alignment).
        stacked:       (n_valid, dim)-Array oder None, wenn nichts valide war.
        dropped:       Anzahl gefilterter Einträge (für Log-Diagnose).

    Hintergrund: np.array(list_of_lists, dtype=float32) bricht mit
    "inhomogeneous shape" ab, sobald auch nur ein Eintrag None ist oder eine
    abweichende Länge hat. Das passiert im Memory-Retrieval, wenn Slots ohne
    gecachtes Embedding oder mit legacy-Embeddings unterschiedlicher Modell-Versionen
    gemischt werden.
    """
    if not candidate_embeddings:
        return [], None, 0

    valid_pairs: list[tuple[int, np.ndarray]] = []
    dropped = 0
    for i, emb in enumerate(candidate_embeddings):
        if emb is None:
            dropped += 1
            continue
        if not isinstance(emb, (list, tuple, np.ndarray)):
            dropped += 1
            continue
        try:
            arr = np.asarray(emb, dtype=np.float32)
        except (ValueError, TypeError):
            dropped += 1
            continue
        if arr.ndim != 1 or arr.size == 0:
            dropped += 1
            continue
        if not np.all(np.isfinite(arr)):
            dropped += 1
            continue
        valid_pairs.append((i, arr))

    if not valid_pairs:
        return [], None, dropped

    # Referenz-Dimension: explizit vorgegeben, sonst die des ersten validen Eintrags
    ref_dim = expected_dim if expected_dim is not None else valid_pairs[0][1].size
    consistent = [(i, a) for i, a in valid_pairs if a.size == ref_dim]
    dropped += len(valid_pairs) - len(consistent)

    if not consistent:
        return [], None, dropped

    indices = [i for i, _ in consistent]
    stacked = np.stack([a for _, a in consistent], axis=0)
    return indices, stacked, dropped


def calculate_similarity_batch(query_text: str, candidate_embeddings: List[List[float]]) -> List[float]:
    """
    Berechnet die Ähnlichkeit zwischen Query-Text und einer Liste von Vektoren.

    Robust gegen inhomogene Embedding-Listen (None, falsche Dimension, NaN) —
    invalide Einträge werden übersprungen und mit Score 0.0 aligned.
    """
    model = _get_model()  # Modell "lazy" anfordern
    if model is None or not candidate_embeddings:
        return [0.0] * len(candidate_embeddings) if candidate_embeddings else []

    try:
        from sentence_transformers import util
        query_embedding = model.encode(query_text)
        query_dim = int(np.asarray(query_embedding).size)
        indices, corpus, dropped = _safe_stack_embeddings(candidate_embeddings, expected_dim=query_dim)
        if dropped:
            logger.warning(
                "calculate_similarity_batch: %d/%d Embeddings gefiltert (None/Shape/Dim-Mismatch zu query_dim=%d)",
                dropped, len(candidate_embeddings), query_dim,
            )
        if corpus is None:
            return [0.0] * len(candidate_embeddings)
        cos_scores = util.cos_sim(query_embedding, corpus)[0].tolist()
        # Alignment: Original-Länge beibehalten, invalide Positionen = 0.0
        scores = [0.0] * len(candidate_embeddings)
        for local_idx, orig_idx in enumerate(indices):
            scores[orig_idx] = float(cos_scores[local_idx])
        return scores
    except Exception as e:
        logger.error(f"Error in batch similarity calculation: {e}")
        return [0.0] * len(candidate_embeddings)


def calculate_similarity_with_precomputed(
    query_embedding: np.ndarray, candidate_embeddings: List[List[float]]
) -> List[float]:
    """
    ISSUE 011: Berechnet Ähnlichkeit mit bereits berechnetem Query-Embedding.
    Vermeidet redundant encode() Aufrufe bei mehreren Suchen pro Query.

    Robust gegen inhomogene Embedding-Listen (None, falsche Dimension, NaN) —
    invalide Einträge werden übersprungen und mit Score 0.0 aligned.
    """
    if not candidate_embeddings:
        return []

    try:
        from sentence_transformers import util
        query_dim = int(np.asarray(query_embedding).size)
        indices, corpus, dropped = _safe_stack_embeddings(candidate_embeddings, expected_dim=query_dim)
        if dropped:
            logger.warning(
                "calculate_similarity_with_precomputed: %d/%d Embeddings gefiltert (None/Shape/Dim-Mismatch zu query_dim=%d)",
                dropped, len(candidate_embeddings), query_dim,
            )
        if corpus is None:
            return [0.0] * len(candidate_embeddings)
        cos_scores = util.cos_sim(query_embedding, corpus)[0].tolist()
        scores = [0.0] * len(candidate_embeddings)
        for local_idx, orig_idx in enumerate(indices):
            scores[orig_idx] = float(cos_scores[local_idx])
        return scores
    except Exception as e:
        logger.error(f"Error in precomputed similarity calculation: {e}")
        return [0.0] * len(candidate_embeddings)


def find_most_similar_indices(query_text: str, embeddings_list: List[List[float]], top_k: int, threshold: float) -> List[int]:
    """
    Gibt die INDIZES der Top-K ähnlichsten Embeddings zurück.
    """
    scores = calculate_similarity_batch(query_text, embeddings_list)
    if not scores:
        return []

    qualified_indices = [i for i, s in enumerate(scores) if s >= threshold]
    if not qualified_indices:
        return []

    qualified_indices.sort(key=lambda i: scores[i], reverse=True)
    return qualified_indices[:top_k]


def find_most_similar_indices_precomputed(
    query_embedding: np.ndarray, embeddings_list: List[List[float]], top_k: int, threshold: float
) -> List[int]:
    """
    ISSUE 011: Top-K Suche mit bereits berechnetem Query-Embedding.
    """
    scores = calculate_similarity_with_precomputed(query_embedding, embeddings_list)
    if not scores:
        return []

    qualified_indices = [i for i, s in enumerate(scores) if s >= threshold]
    if not qualified_indices:
        return []

    qualified_indices.sort(key=lambda i: scores[i], reverse=True)
    return qualified_indices[:top_k]


# Veraltete Funktionen für Kompatibilität (optional, falls noch irgendwo aufgerufen)
def find_similar_snippets(query_text: str, memories: list, top_k: int = 3, threshold: float = 0.1):
    # Dies ist ein Wrapper für alten Code, der DB-Objekte erwartet
    if not memories:
        return []
    
    embeddings = []
    valid_memories = []
    
    for mem in memories:
        try:
            emb = json.loads(mem.embedding_json)
            embeddings.append(emb)
            valid_memories.append(mem)
        except:
            continue
            
    indices = find_most_similar_indices(query_text, embeddings, top_k, threshold)
    return [valid_memories[i] for i in indices]


def delete_embeddings(chunk_ids: List[str], collection_name: str = "janus_global_documents"):
    """Remove the provided chunk IDs from the shared Chroma collection."""
    if not chunk_ids:
        return

    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(name=collection_name)
        collection.delete(ids=chunk_ids)
        logger.info(f"Vektor-Service: {len(chunk_ids)} Embeddings aus '{collection_name}' gelöscht.")
    except Exception as exc:
        logger.error(f"Vektor-Service: Fehler beim Löschen von Embeddings: {exc}", exc_info=True)


def delete_by_document_id(document_id: int):
    """Entfernt alle Vektoren eines Dokuments direkt aus der Collection."""
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(name="janus_global_documents")
        collection.delete(where={"document_id": document_id})
        return True
    except Exception as e:
        print(f"Fehler bei nativer Chroma-Löschung: {e}")
        return False


class VectorService:
    def __init__(self, persist_directory: str = CHROMA_PATH):
        self.persist_directory = persist_directory
        self.embedding_fn = self._build_embedding_function()
        self._client = None
        self.collection = None
        try:
            self._client = chromadb.PersistentClient(path=self.persist_directory)
            collection_kwargs = {
                "name": "janus_global_documents",
                "metadata": {"hnsw:space": "cosine"},
            }
            if self.embedding_fn is not None:
                collection_kwargs["embedding_function"] = self.embedding_fn
            else:
                logger.warning("Vektor-Service: Starte ohne Embedding-Funktion. Semantische Suche/Indexierung ist eingeschränkt, Backend bleibt aber verfügbar.")
            self.collection = self._client.get_or_create_collection(**collection_kwargs)
            logger.info("Vektor-Service: Diamond-Initialisierung erfolgreich.")
        except Exception as exc:
            logger.error(f"Vektor-Service: Kritischer Fehler beim Start: {exc}")
            self.collection = None

    def _build_embedding_function(self):
        try:
            from chromadb.utils import embedding_functions
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=_model_name
            )
        except Exception as exc:
            logger.warning(
                "Vektor-Service: Embedding-Funktion konnte nicht initialisiert werden. Nutze Offline-Degrade ohne Embeddings. error=%s",
                exc,
            )
            return None

    def delete_by_document_id(self, document_id: int):
        """Löscht alle Vektoren eines Dokuments (Wichtig für Tabletop-Updates)."""
        if not self.collection:
            return False
        try:
            # Wir löschen beide Typen (Int und String), um sicher zu gehen
            self.collection.delete(where={"document_id": document_id})
            self.collection.delete(where={"document_id": str(document_id)})
            return True
        except Exception as e:
            logger.error(f"Fehler bei Vektor-Löschung ID {document_id}: {e}")
            return False

# Singleton-Instanz sicher am Ende exportieren
vector_service = VectorService()
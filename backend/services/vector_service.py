# backend/services/vector_service.py

import json
import logging
import os
import time
from typing import List, Optional

import numpy as np
from backend.utils.paths import get_app_data_dir
from sentence_transformers import SentenceTransformer, util

# Configure environment variables for better control
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Prevent tokenizer warnings
os.environ["HF_HUB_OFFLINE"] = "0"  # Enable hub access for model downloads

logger = logging.getLogger("janus_backend")

# Configure model cache in AppData directory
app_data = get_app_data_dir()
model_cache_path = os.path.join(app_data, "model_cache")
os.makedirs(model_cache_path, exist_ok=True)

# Set the cache directory for sentence-transformers
os.environ["SENTENCE_TRANSFORMERS_HOME"] = model_cache_path
model_name = "all-MiniLM-L6-v2"

logger.info(f"Loading Vector Model from/to: {model_cache_path}")

# Initialize the model with proper error handling
try:
    # Device map 'cpu' to ensure stability on standard backends
    model = SentenceTransformer(
        model_name,
        cache_folder=model_cache_path,
        device="cpu"
    )
    logger.info(f"Successfully loaded model: {model_name}")
except Exception as e:
    logger.error(f"Failed to load SentenceTransformer: {str(e)}", exc_info=True)
    logger.warning("Vector search functionality will be disabled.")
    model = None


def generate_embedding(text: str) -> Optional[str]:
    """Generiert einen Vektor-Embedding für einen gegebenen Text."""
    if model is None:
        logger.error("Embedding-Modell ist nicht verfügbar.")
        return None
    try:
        # Normalize text slightly
        text = text.replace("\n", " ").strip()
        embedding = model.encode(text)
        return json.dumps(embedding.tolist())
    except Exception as e:
        logger.error(f"Fehler bei der Embedding-Generierung für Text '{text}': {e}")
        return None


def calculate_similarity_batch(query_text: str, candidate_embeddings: List[List[float]]) -> List[float]:
    """
    Berechnet die Ähnlichkeit zwischen Query-Text und einer Liste von Vektoren.
    """
    if model is None or not candidate_embeddings:
        return []

    try:
        # 1. Query Text -> Vektor
        query_embedding = model.encode(query_text)
        
        # 2. Kandidaten -> Matrix
        corpus_embeddings = np.array(candidate_embeddings, dtype=np.float32)

        # 3. Cosine Similarity berechnen
        # util.cos_sim gibt einen Tensor zurück
        cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
        
        return cos_scores.tolist()
    except Exception as e:
        logger.error(f"Error in batch similarity calculation: {e}")
        return [0.0] * len(candidate_embeddings)


def find_most_similar_indices(query_text: str, embeddings_list: List[List[float]], top_k: int, threshold: float) -> List[int]:
    """
    Gibt die INDIZES der Top-K ähnlichsten Embeddings zurück.
    Erwartet 'query_text' als String und 'embeddings_list' als Liste von Vektoren.
    """
    # Berechnung der Scores
    scores = calculate_similarity_batch(query_text, embeddings_list)
    
    if not scores:
        return []

    # Filtern nach Threshold und Index merken
    qualified_indices = [i for i, s in enumerate(scores) if s >= threshold]
    
    if not qualified_indices:
        return []

    # Sortieren nach Score (höchster zuerst)
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
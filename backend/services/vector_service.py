import json
import logging
import os

import numpy as np
from backend.utils.paths import resource_path
from sentence_transformers import SentenceTransformer, util

# Strictly enforce offline mode for all Hugging Face components
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["HF_EVALUATE_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"  # Explicitly disable hub access
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Prevent tokenizer warnings

logger = logging.getLogger("janus_backend")

# Das Modell wird nur einmal beim Start geladen und im Speicher gehalten.
# 'all-MiniLM-L6-v2' ist ein gutes Allround-Modell, das schnell und lokal läuft.
try:
    # Der Pfad zum Modell innerhalb des PyInstaller-Bundles
    model_path = resource_path("backend/model_cache/all-MiniLM-L6-v2")

    # Verify the model files exist locally
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model directory not found at {model_path}")

    logger.info(f"Loading SentenceTransformer model in OFFLINE mode from: {model_path}")

    # Load model with minimal configuration for offline use
    model = SentenceTransformer(
        model_path,
        device="cpu",  # Force CPU usage to avoid CUDA initialization delays
    )

    logger.info(
        f"Successfully loaded SentenceTransformer model from local cache. Model device: {model.device}"
    )
    logger.info(f"Model max sequence length: {model.max_seq_length}")

except Exception as e:
    logger.error(
        f"Critical error loading SentenceTransformer model from {model_path}: {str(e)}",
        exc_info=True,
    )
    logger.error("Application will continue but vector search functionality will be disabled.")

    # Log environment for debugging
    logger.info("Environment variables for debugging:")
    for key, value in os.environ.items():
        if key.startswith(("HF_", "TRANSFORMERS_", "TOKENIZERS_")):
            logger.info(f"{key}={value}")

    model = None


def generate_embedding(text: str):
    """Generiert einen Vektor-Embedding für einen gegebenen Text."""
    if model is None:
        logger.error("Embedding-Modell ist nicht verfügbar.")
        return None
    try:
        logger.info(f"Generating embedding for text: '{text}'")
        embedding = model.encode(text)
        logger.info(f"Embedding generated successfully for text: '{text}'")
        return json.dumps(embedding.tolist())  # Speichere als JSON-String
    except Exception as e:
        logger.error(f"Fehler bei der Embedding-Generierung für Text '{text}': {e}")
        return None


def _find_similar_items(
    query_text: str, items: list, embedding_attribute: str, top_k: int, threshold: float
):
    if model is None or not items:
        return []
    try:
        query_embedding = model.encode(query_text)

        items_with_embeddings = [item for item in items if getattr(item, embedding_attribute)]
        if not items_with_embeddings:
            return []

        corpus_embeddings = [
            json.loads(getattr(item, embedding_attribute)) for item in items_with_embeddings
        ]

        cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]

        top_results_indices = np.argpartition(-cos_scores, range(min(top_k, len(cos_scores))))[
            :top_k
        ]

        similar_items = []
        for i, idx in enumerate(top_results_indices):
            score = float(cos_scores[idx])  # Convert to float
            if score > threshold:
                similar_items.append(items_with_embeddings[idx])
        return similar_items
    except Exception as e:
        logger.error(f"Fehler bei der Vektor-Suche für {embedding_attribute}: {e}")
        return []


def find_similar_snippets(query_text: str, memories: list, top_k: int = 3, threshold: float = 0.1):
    """Findet die semantisch ähnlichsten Erinnerungen an einen Suchtext."""
    similar_memories = _find_similar_items(query_text, memories, "embedding_json", top_k, threshold)
    for mem in similar_memories:
        # Access the score from the original cos_scores calculation if needed for logging
        # For now, we'll just log the snippet and assume the score is handled by _find_similar_items
        logger.info(f"Snippet: '{mem.snippet}')")
    logger.info(f"find_similar_snippets: Returning {len(similar_memories)} similar memories.")
    return similar_memories


def find_similar_chat_summaries(
    query_text: str, chats: list, top_k: int = 3, threshold: float = 0.5
):
    """Findet die semantisch ähnlichsten Chat-Zusammenfassungen an einen Suchtext."""
    return _find_similar_items(query_text, chats, "summary_embedding_json", top_k, threshold)

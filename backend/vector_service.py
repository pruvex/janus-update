import logging
import json
import numpy as np
from sentence_transformers import SentenceTransformer, util
from backend.utils.paths import resource_path

logger = logging.getLogger('janus_backend')

# Das Modell wird nur einmal beim Start geladen und im Speicher gehalten.
# 'all-MiniLM-L6-v2' ist ein gutes Allround-Modell, das schnell und lokal läuft.
try:
    # Der Pfad zum Modell innerhalb des PyInstaller-Bundles
    model_path = resource_path('backend/model_cache/all-MiniLM-L6-v2')
    model = SentenceTransformer(model_path)
except Exception as e:
    logger.error(f"Konnte das SentenceTransformer-Modell nicht laden von Pfad {model_path}: {e}")
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
        return json.dumps(embedding.tolist()) # Speichere als JSON-String
    except Exception as e:
        logger.error(f"Fehler bei der Embedding-Generierung für Text '{text}': {e}")
        return None

def find_similar_snippets(query_text: str, memories: list, top_k: int = 3, threshold: float = 0.1):
    """
    Findet die semantisch ähnlichsten Erinnerungen an einen Suchtext.
    """
    if model is None or not memories:
        return []
    try:
        query_embedding = model.encode(query_text)

        # Filtere zuerst die Memories, die ein Embedding haben
        memories_with_embeddings = [mem for mem in memories if mem.embedding_json]
        if not memories_with_embeddings:
            return []

        # Lade die Embeddings aus den gefilterten Datenbank-Objekten
        corpus_embeddings = [json.loads(mem.embedding_json) for mem in memories_with_embeddings]

        # Berechne die Kosinus-Ähnlichkeit
        cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]

        # Finde die Indizes der Top K Treffer
        top_results_indices = np.argpartition(-cos_scores, range(min(top_k, len(cos_scores))))[:top_k]

        # Filtere die Ergebnisse nach dem Schwellenwert und gib die Original-Memory-Objekte zurück
        similar_memories = []
        for i, idx in enumerate(top_results_indices):
            score = cos_scores[idx]
            logger.info(f"Snippet: '{memories_with_embeddings[idx].snippet}', Score: {score:.4f}")
            if score > threshold:
                # Greife auf die gefilterte Liste zu, um den korrekten Index zu verwenden
                similar_memories.append(memories_with_embeddings[idx])
        logger.info(f"find_similar_snippets: Returning {len(similar_memories)} similar memories.")
        return similar_memories
    except Exception as e:
        logger.error(f"Fehler bei der Vektor-Suche: {e}")
        return []

def find_similar_chat_summaries(query_text: str, chats: list, top_k: int = 3, threshold: float = 0.5):
    """
    Findet die semantisch ähnlichsten Chat-Zusammenfassungen an einen Suchtext.
    """
    if model is None or not chats:
        return []
    try:
        query_embedding = model.encode(query_text)

        chats_with_embeddings = [chat for chat in chats if chat.summary_embedding_json]
        if not chats_with_embeddings:
            return []

        corpus_embeddings = [json.loads(chat.summary_embedding_json) for chat in chats_with_embeddings]

        cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]

        top_results_indices = np.argpartition(-cos_scores, range(min(top_k, len(cos_scores))))[:top_k]

        similar_chats = []
        for i, idx in enumerate(top_results_indices):
            score = cos_scores[idx]
            if score > threshold:
                similar_chats.append(chats_with_embeddings[idx])
        return similar_chats
    except Exception as e:
        logger.error(f"Fehler bei der Vektor-Suche für Chat-Zusammenfassungen: {e}")
        return []
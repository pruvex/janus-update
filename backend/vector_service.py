import logging
import json
import numpy as np
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger('janus_backend')

# Das Modell wird nur einmal beim Start geladen und im Speicher gehalten.
# 'all-MiniLM-L6-v2' ist ein gutes Allround-Modell, das schnell und lokal läuft.
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.error(f"Konnte das SentenceTransformer-Modell nicht laden: {e}")
    model = None

def generate_embedding(text: str):
    """Generiert einen Vektor-Embedding für einen gegebenen Text."""
    if model is None:
        logger.error("Embedding-Modell ist nicht verfügbar.")
        return None
    try:
        embedding = model.encode(text)
        return json.dumps(embedding.tolist()) # Speichere als JSON-String
    except Exception as e:
        logger.error(f"Fehler bei der Embedding-Generierung für Text '{text[:50]}...': {e}")
        return None

def find_similar_snippets(query_text: str, memories: list, top_k: int = 3, threshold: float = 0.1):
    """
    Findet die semantisch ähnlichsten Erinnerungen an einen Suchtext.
    """
    if model is None or not memories:
        return []
    try:
        query_embedding = model.encode(query_text)

        # Lade die Embeddings aus den Datenbank-Objekten
        corpus_embeddings = [json.loads(mem.embedding_json) for mem in memories if mem.embedding_json]

        if not corpus_embeddings:
            return []
        # Berechne die Kosinus-Ähnlichkeit
        cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]

        # Finde die Indizes der Top K Treffer
        top_results_indices = np.argpartition(-cos_scores, range(min(top_k, len(cos_scores))))[:top_k]

        # Filtere die Ergebnisse nach dem Schwellenwert und gib die Original-Memory-Objekte zurück
        similar_memories = []
        for idx in top_results_indices:
            if cos_scores[idx] > threshold:
                similar_memories.append(memories[idx])
        return similar_memories
    except Exception as e:
        logger.error(f"Fehler bei der Vektor-Suche: {e}")
        return []
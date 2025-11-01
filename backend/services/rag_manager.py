# backend/rag_manager.py

import os
import logging
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
import requests
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
from typing import List

logger = logging.getLogger("janus_backend")

from backend.utils.paths import get_app_data_dir

CHROMA_PATH = os.path.join(get_app_data_dir(), "rag_chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)


def _get_or_create_collection(collection_name: str):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=sentence_transformer_ef,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def _split_text(text, chunk_size=1000, chunk_overlap=200):
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks


def _extract_text_from_epub(file_path: str) -> str:
    try:
        book = epub.read_epub(file_path)
        chapters = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_body_content(), "html.parser")
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            chapters.append(soup.get_text(separator="\n", strip=True))
        return "\n\n".join(chapters)
    except Exception as e:
        logger.error(
            f"Fehler beim Extrahieren von EPUB {os.path.basename(file_path)}: {e}"
        )
        return ""


def process_and_index_folder(folder_path: str, status_dict: dict, collection_name: str):
    logger.info(
        f"Starte Indexierung für Ordner: '{folder_path}' in Sammlung: '{collection_name}'"
    )
    if not os.path.isdir(folder_path):
        status_dict.update(
            {"in_progress": False, "message": "Fehler: Ordner nicht gefunden."}
        )
        return

    try:
        collection = _get_or_create_collection(collection_name)
        supported_extensions = (".pdf", ".epub")
        supported_files = [
            f
            for f in os.listdir(folder_path)
            if f.lower().endswith(supported_extensions)
        ]
        status_dict["total_files"] = len(supported_files)

        for i, filename in enumerate(supported_files):
            status_dict.update(
                {
                    "processed_files": i,
                    "current_file": filename,
                    "message": f"Verarbeite Datei {i + 1} von {len(supported_files)}...",
                }
            )
            logger.info(f"Verarbeite: {filename} ({i + 1}/{len(supported_files)})")

            full_text = ""
            full_path = os.path.join(folder_path, filename)
            try:
                if filename.lower().endswith(".pdf"):
                    reader = PdfReader(full_path)
                    full_text = "\n".join(
                        [
                            page.extract_text()
                            for page in reader.pages
                            if page.extract_text()
                        ]
                    )
                elif filename.lower().endswith(".epub"):
                    full_text = _extract_text_from_epub(full_path)

                if full_text:
                    chunks = _split_text(full_text)
                    ids = [
                        f"{collection_name}_{filename}_chunk_{j}"
                        for j in range(len(chunks))
                    ]
                    if chunks:
                        collection.add(documents=chunks, ids=ids)
                else:
                    logger.warning(
                        f"Kein Text aus {filename} extrahiert. Datei wird übersprungen."
                    )
            except Exception as e:
                logger.error(
                    f"Fehler bei der Verarbeitung von {filename}: {e}", exc_info=True
                )

        final_msg = f"Indexierung von {len(supported_files)} Dateien für Sammlung '{collection_name}' erfolgreich abgeschlossen."
        status_dict.update(
            {
                "in_progress": False,
                "processed_files": len(supported_files),
                "current_file": "",
                "message": final_msg,
            }
        )
        logger.info(final_msg)
    except Exception as e:
        error_msg = f"Kritischer Fehler bei Indexierung: {e}"
        status_dict.update({"in_progress": False, "message": error_msg})
        logger.error(error_msg, exc_info=True)


def query_knowledge_base(
    query_text: str, collection_name: str, n_results: int = 7
) -> list[str]:
    try:
        collection = _get_or_create_collection(collection_name)
        results = collection.query(query_texts=[query_text], n_results=n_results)
        return results["documents"][0] if results["documents"] else []
    except Exception as e:
        logger.error(
            f"Fehler bei Abfrage der Sammlung '{collection_name}': {e}", exc_info=True
        )
        return []


def list_collections() -> list[str]:
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        return [c.name for c in client.list_collections()]
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Sammlungen: {e}", exc_info=True)
        return []

def get_all_documents_from_collection(collection_name: str, limit: int = 15) -> List[str]:
    """Holt eine Liste von Dokumenteninhalten aus einer spezifischen Collection."""
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(name=collection_name)
        # get() holt Dokumente; wir beschränken die Anzahl mit 'limit'
        results = collection.get(limit=limit, include=["documents"])
        
        documents = results.get("documents")
        if not documents:
            logger.warning(f"Keine Dokumente in der Collection '{collection_name}' gefunden.")
            return []
            
        logger.info(f"{len(documents)} Dokumente aus '{collection_name}' für die Stilanalyse abgerufen.")
        return documents
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von Dokumenten aus Collection '{collection_name}': {e}", exc_info=True)
        return []

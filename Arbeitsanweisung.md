Phase 1: Die Backend-Grundlage (Das RAG-Modul)
Zuerst schaffen wir das "Gehirn" des Systems in Python.
1. Benötigte Bibliotheken installieren
Stellen Sie sicher, dass Ihr Janus-Server gestoppt ist. Aktivieren Sie dann Ihre virtuelle Umgebung und installieren Sie alle benötigten Pakete mit einem einzigen Befehl:
code
Powershell
# Im Terminal, im Hauptverzeichnis Ihres Projekts
.\backend\venv\Scripts\Activate.ps1
pip install sentence-transformers chromadb pypdf beautifulsoup4 ebooklib
2. Neue Datei backend/rag_manager.py erstellen
Erstellen Sie im backend-Ordner diese neue Datei. Sie enthält die gesamte Logik für das Laden, Verarbeiten und Abfragen Ihrer Wissensbanken. Fügen Sie den folgenden, vollständigen Code ein:
code
Python
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

logger = logging.getLogger('janus_backend')

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
        metadata={"hnsw:space": "cosine"}
    )
    return collection

def _split_text(text, chunk_size=1000, chunk_overlap=200):
    if not text: return []
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
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            chapters.append(soup.get_text(separator='\n', strip=True))
        return "\n\n".join(chapters)
    except Exception as e:
        logger.error(f"Fehler beim Extrahieren von EPUB {os.path.basename(file_path)}: {e}")
        return ""

def process_and_index_folder(folder_path: str, status_dict: dict, collection_name: str):
    logger.info(f"Starte Indexierung für Ordner: '{folder_path}' in Sammlung: '{collection_name}'")
    if not os.path.isdir(folder_path):
        status_dict.update({"in_progress": False, "message": "Fehler: Ordner nicht gefunden."})
        return

    try:
        collection = _get_or_create_collection(collection_name)
        supported_extensions = ('.pdf', '.epub')
        supported_files = [f for f in os.listdir(folder_path) if f.lower().endswith(supported_extensions)]
        status_dict["total_files"] = len(supported_files)

        for i, filename in enumerate(supported_files):
            status_dict.update({
                "processed_files": i,
                "current_file": filename,
                "message": f"Verarbeite Datei {i+1} von {len(supported_files)}..."
            })
            logger.info(f"Verarbeite: {filename} ({i+1}/{len(supported_files)})")

            full_text = ""
            full_path = os.path.join(folder_path, filename)
            try:
                if filename.lower().endswith(".pdf"):
                    reader = PdfReader(full_path)
                    full_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                elif filename.lower().endswith(".epub"):
                    full_text = _extract_text_from_epub(full_path)

                if full_text:
                    chunks = _split_text(full_text)
                    ids = [f"{collection_name}_{filename}_chunk_{j}" for j in range(len(chunks))]
                    if chunks:
                        collection.add(documents=chunks, ids=ids)
                else:
                    logger.warning(f"Kein Text aus {filename} extrahiert. Datei wird übersprungen.")
            except Exception as e:
                logger.error(f"Fehler bei der Verarbeitung von {filename}: {e}", exc_info=True)

        final_msg = f"Indexierung von {len(supported_files)} Dateien für Sammlung '{collection_name}' erfolgreich abgeschlossen."
        status_dict.update({"in_progress": False, "processed_files": len(supported_files), "current_file": "", "message": final_msg})
        logger.info(final_msg)
    except Exception as e:
        error_msg = f"Kritischer Fehler bei Indexierung: {e}"
        status_dict.update({"in_progress": False, "message": error_msg})
        logger.error(error_msg, exc_info=True)

def query_knowledge_base(query_text: str, collection_name: str, n_results: int = 7) -> list[str]:
    try:
        collection = _get_or_create_collection(collection_name)
        results = collection.query(query_texts=[query_text], n_results=n_results)
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        logger.error(f"Fehler bei Abfrage der Sammlung '{collection_name}': {e}", exc_info=True)
        return []

def list_collections() -> list[str]:
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        return [c.name for c in client.list_collections()]
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Sammlungen: {e}", exc_info=True)
        return []
Phase 2: API-Endpunkte in main.py hinzufügen
Wir machen die neuen Funktionen über die API erreichbar. Fügen Sie die folgenden Code-Blöcke an den entsprechenden Stellen in main.py ein oder ersetzen Sie sie.
1. Imports und globale "Status-Tafel" (ganz oben in main.py):
code
Python
# Nahe am Anfang der Datei, bei den anderen Imports
from backend import rag_manager
from typing import Dict, Any

# Fügen Sie diese globale Variable nach den Imports hinzu
RAG_INDEXING_STATUS: Dict[str, Any] = {
    "in_progress": False, "total_files": 0, "processed_files": 0,
    "current_file": "", "message": "Keine Indexierung aktiv."
}
2. Neue Pydantic-Modelle (bei den anderen Modellen):
code
Python
class RagFolderRequest(BaseModel):
    path: str
    collection_name: str

class RagUrlRequest(BaseModel):
    url: str
    collection_name: str
3. Neue API-Endpunkte (fügen Sie diesen Block z.B. vor der /api/chat Route ein):
code
Python
@app.get("/api/rag/collections")
async def get_rag_collections():
    return {"collections": rag_manager.list_collections()}

@app.get("/api/rag/indexing-status")
async def get_indexing_status():
    return RAG_INDEXING_STATUS

@app.post("/api/rag/index-folder")
async def index_folder(request: RagFolderRequest):
    if RAG_INDEXING_STATUS["in_progress"]:
        raise HTTPException(status_code=409, detail="Eine Indexierung läuft bereits.")
    
    try:
        RAG_INDEXING_STATUS.update({
            "in_progress": True, "total_files": 0, "processed_files": 0,
            "message": "Indexierung wird gestartet..."
        })
        asyncio.create_task(
            asyncio.to_thread(
                rag_manager.process_and_index_folder, 
                request.path, RAG_INDEXING_STATUS, request.collection_name
            )
        )
        return {"message": "Indexierung gestartet."}
    except Exception as e:
        RAG_INDEXING_STATUS["in_progress"] = False
        logger.error(f"Fehler beim Start der Ordner-Indexierung: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fehler beim Start der Indexierung.")
Phase 3: Die Benutzeroberfläche (HTML & JS)
1. index.html anpassen:
Fügen Sie den Navigationslink und die komplette Sektion für die Wissensbasis hinzu.
Navigationslink (in <div id="settings-nav">):
code
Html
<a href="#" class="settings-nav-link" data-target="rag-management-section">Wissensbasis</a>
Sektion (in <div id="settings-content-area">):
code
Html
<div id="rag-management-section" class="settings-section" style="display: none;">
    <h3>Wissensbasis-Verwaltung (RAG)</h3>
    <p>Füge Inhalte zu spezifischen Wissens-Bibliotheken hinzu.</p>
    
    <div class="rag-control-group" style="margin-bottom: 20px;">
        <label for="rag-collection-select" style="display: block; margin-bottom: 5px;">Wissens-Bibliothek:</label>
        <select id="rag-collection-select"></select>
        <input type="text" id="rag-new-collection-name-input" placeholder="Name für neue Bibliothek..." style="display: none; margin-top: 8px;">
    </div>
    
    <div class="rag-control-group">
        <h4>Dateien aus Ordner indexieren (PDF, EPUB)</h4>
        <input type="text" id="rag-folder-path-input" placeholder="Vollständiger Pfad zum Ordner...">
        <button id="rag-index-folder-btn">Indexierung starten</button>
    </div>
    
    <p id="rag-status-message" style="margin-top: 15px; color: #aaa;"></p>
    <div id="rag-progress-container" style="display: none; margin-top: 15px;">
        <p id="rag-progress-text"></p>
        <progress id="rag-progress-bar" value="0" max="100" style="width: 100%;"></progress>
    </div>
</div>
2. js/settings.js anpassen:
Fügen Sie den kompletten Codeblock für die RAG-Verwaltung in Ihre DOMContentLoaded-Funktion ein.
code
JavaScript
// Innerhalb von document.addEventListener('DOMContentLoaded', () => { ... in js/settings.js });

    // --- RAG WISSENSBASIS-VERWALTUNG ---
    const ragFolderPathInput = document.getElementById('rag-folder-path-input');
    const ragIndexFolderBtn = document.getElementById('rag-index-folder-btn');
    const ragStatusMessage = document.getElementById('rag-status-message');
    const collectionSelect = document.getElementById('rag-collection-select');
    const newCollectionNameInput = document.getElementById('rag-new-collection-name-input');
    const progressContainer = document.getElementById('rag-progress-container');
    const progressText = document.getElementById('rag-progress-text');
    const progressBar = document.getElementById('rag-progress-bar');
    let pollingInterval = null;

    async function loadCollections() {
        try {
            const response = await fetch('/api/rag/collections');
            const data = await response.json();
            const currentSelection = collectionSelect.value;
            collectionSelect.innerHTML = '';
            
            const newOption = document.createElement('option');
            newOption.value = '__new__';
            newOption.textContent = 'Neue Bibliothek erstellen...';
            collectionSelect.appendChild(newOption);

            if (data.collections) {
                data.collections.forEach(name => {
                    const option = document.createElement('option');
                    option.value = name;
                    option.textContent = name;
                    collectionSelect.appendChild(option);
                });
            }
            // Stelle die vorherige Auswahl wieder her, falls möglich
            if (currentSelection && collectionSelect.querySelector(`option[value="${currentSelection}"]`)) {
                collectionSelect.value = currentSelection;
            }
            handleCollectionChange();
        } catch (error) { console.error('Fehler beim Laden der Wissens-Bibliotheken:', error); }
    }

    function handleCollectionChange() {
        newCollectionNameInput.style.display = collectionSelect.value === '__new__' ? 'block' : 'none';
    }

    collectionSelect.addEventListener('change', handleCollectionChange);

    function getSelectedCollectionName() {
        return collectionSelect.value === '__new__' ? newCollectionNameInput.value.trim() : collectionSelect.value;
    }

    async function updateProgress() {
        try {
            const response = await fetch('/api/rag/indexing-status');
            if (!response.ok) throw new Error(`Server-Fehler: ${response.status}`);
            const status = await response.json();

            if (status.in_progress) {
                progressContainer.style.display = 'block';
                if (status.total_files > 0) {
                    progressBar.max = status.total_files;
                    progressBar.value = status.processed_files;
                    progressText.textContent = `[${status.processed_files}/${status.total_files}] Verarbeite: ${status.current_file || '...'}`;
                } else {
                    progressText.textContent = 'Berechne Dateien...';
                }
            } else {
                if (pollingInterval) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                }
                progressContainer.style.display = 'none';
                ragStatusMessage.textContent = status.message || 'Prozess beendet.';
                ragStatusMessage.style.color = '#10b981';
                ragIndexFolderBtn.disabled = false;
                loadCollections();
            }
        } catch (error) {
            console.error("Fehler beim Abrufen des Indexierungsstatus:", error);
            ragStatusMessage.textContent = `Fehler beim Abruf des Status: ${error.message}`;
            ragStatusMessage.style.color = '#b91c1c';
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
            ragIndexFolderBtn.disabled = false;
        }
    }
    
    ragIndexFolderBtn.addEventListener('click', async () => {
        const path = ragFolderPathInput.value.trim();
        const collectionName = getSelectedCollectionName();
        if (!path || !collectionName) {
            alert('Bitte geben Sie einen Ordnerpfad UND einen gültigen Bibliotheksnamen an.');
            return;
        }
        if (pollingInterval) clearInterval(pollingInterval);

        ragIndexFolderBtn.disabled = true;
        ragStatusMessage.textContent = 'Indexierung wird gestartet...';
        ragStatusMessage.style.color = '#3b82f6';
        progressContainer.style.display = 'block';
        progressText.textContent = 'Initialisiere...';
        progressBar.value = 0;

        try {
            const response = await fetch('/api/rag/index-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path, collection_name: collectionName })
            });
            const result = await response.json();
            if (response.ok) {
                ragStatusMessage.textContent = result.message;
                setTimeout(() => {
                    updateProgress();
                    pollingInterval = setInterval(updateProgress, 2000);
                }, 1000);
            } else {
                throw new Error(result.detail || 'Fehler beim Starten.');
            }
        } catch (error) {
            ragStatusMessage.textContent = `Fehler: ${error.message}`;
            ragStatusMessage.style.color = '#b91c1c';
            ragIndexFolderBtn.disabled = false;
            progressContainer.style.display = 'none';
        }
    });

    // Sorge dafür, dass die Sammlungen geladen werden, wenn der Tab geklickt wird
    const ragNavLink = document.querySelector('.settings-nav-link[data-target="rag-management-section"]');
    if(ragNavLink) {
        ragNavLink.addEventListener('click', loadCollections);
    }
Phase 4: Die Intelligenz im creative_writer
Ersetzen Sie die creative_writer-Funktion (z.B. in backend/creative_writer.py) mit dieser finalen Version:
code
Python
from . import rag_manager
from .llm_gateway import call_llm
import logging

logger = logging.getLogger('janus_backend')

async def creative_writer(prompt: str, provider: str, model: str, api_key: str, style: str):
    available_collections = rag_manager.list_collections()
    logger.info(f"Verfügbare Wissens-Bibliotheken: {available_collections}")
    
    selected_collection = None
    if available_collections:
        selection_model = "gpt-4o-mini" if provider == "openai" else model
        selection_prompt = f"""Basierend auf der folgenden Benutzeranfrage, welche der verfügbaren Wissens-Bibliotheken ist am relevantesten? Antworte NUR mit dem exakten Namen der am besten passenden Bibliothek aus der Liste. Wenn keine passt, antworte mit "None".

Verfügbare Bibliotheken: {', '.join(available_collections)}
Benutzeranfrage: "{prompt}"
Beste Bibliothek:"""
        
        try:
            llm_response = await call_llm(provider, selection_model, api_key, messages=[{"role": "user", "content": selection_prompt}], temperature=0.0)
            best_choice = llm_response.get("text", "").strip().replace("'", "").replace('"', '')
            if best_choice in available_collections:
                selected_collection = best_choice
                logger.info(f"LLM hat die Wissensbasis '{selected_collection}' ausgewählt.")
            else:
                logger.info(f"LLM hat keine passende Bibliothek gefunden (Antwort: '{best_choice}').")
        except Exception as e:
            logger.error(f"Fehler bei der Auswahl der Bibliothek: {e}")

    retrieved_context = []
    if selected_collection:
        retrieved_context = rag_manager.query_knowledge_base(prompt, collection_name=selected_collection, n_results=7)
    
    final_prompt = prompt
    if retrieved_context:
        logger.info(f"{len(retrieved_context)} Kontext-Abschnitte aus '{selected_collection}' gefunden.")
        context_string = "\n\n".join([f"- {item}" for item in retrieved_context])
        final_prompt = f"""Du bist ein meisterhafter kreativer Autor im Stil von {style}. Deine Aufgabe ist es, eine originelle, kreative Arbeit basierend auf der Anfrage des Benutzers zu verfassen.
**WICHTIG:** Nutze die folgenden Textausschnitte aus der Wissensbasis '{selected_collection}' als Inspiration für deinen Stil, Ton und Vokabular. Baue diese Elemente in deine Antwort ein, um sie authentischer zu machen, aber kopiere sie nicht einfach.
---
**INSPIRATIONS-KONTEXT:**
{context_string}
---
**ANFRAGE DES BENUTZERS:**
{prompt}"""
    else:
        logger.info("Kein relevanter Kontext gefunden. Verwende Standard-Prompt.")
    
    try:
        final_llm_response = await call_llm(provider, model, api_key, messages=[{"role": "user", "content": final_prompt}])
        return final_llm_response.get("text", "Ich konnte keine kreative Antwort erstellen.")
    except Exception as e:
        logger.error(f"Fehler im Creative Writer beim finalen LLM-Aufruf: {e}", exc_info=True)
        return f"Ein Fehler ist aufgetreten: {e}"
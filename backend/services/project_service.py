import logging
import asyncio
import json
import re
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.services.websearch.openai_provider import OpenAIWebSearchProvider

from backend.data import crud
from backend.services.rag_manager import add_text_to_collection
from backend.services.scraper_service import scrape_website
from backend.services import llm_gateway  # Importiere das Gateway
import keyring  # Importiere keyring

logger = logging.getLogger("janus_backend")

async def initialize_project_knowledge(
    db: Session, 
    project_id: int, 
    project_name: str,
    active_provider: str,
    active_model: str
):
    """
    Der autonome Agent: Analysiert den Projektnamen, recherchiert und indexiert Wissen.
    Nutzt den aktiven Provider und das aktuelle Modell des Benutzers.
    """
    logger.info(f"Starte autonome Wissensbeschaffung für Projekt: '{project_name}' mit Provider: {active_provider}")
    
    # API-Key für den aktiven Provider holen
    api_key = keyring.get_password("Janus-Projekt", active_provider)
    
    if not api_key:
        logger.warning(f"Kein API-Key für Provider '{active_provider}' gefunden. Überspringe Recherche.")
        return

    # Logik, um ein gutes, günstiges Modell für die Recherche auszuwählen
    research_model = active_model
    if active_provider == "openai":
        research_model = "gpt-4o-mini"  # Wir überschreiben, um Kosten zu sparen

    try:
        # 1. LLM fragen, was zu tun ist
        prompt = (
            f"Du bist ein Recherche-Agent. Deine Aufgabe ist es, für ein neues Projekt namens '{project_name}' "
            "die 3-5 wichtigsten Suchbegriffe zu identifizieren, um eine solide Wissensbasis aufzubauen. "
            "Antworte NUR mit einer JSON-formatierten Liste von Strings. Beispiel: [\"Suchbegriff 1\", \"Suchbegriff 2\"]"
        )
        
        # Wir nutzen einen einfachen Call, um die Suchbegriffe zu bekommen
        response = await llm_gateway.simple_llm_generate_content(
            provider=active_provider,
            model=research_model,
            api_key=api_key,
            prompt=prompt
        )
        
        search_queries = json.loads(response['text'])
        
        # 2. Websuche durchführen & URLs scrapen/indexieren
        urls_to_scrape = set()
        
        # Websuche direkt über den Provider ausführen
        search_provider = OpenAIWebSearchProvider()
        
        for query in search_queries:
            # Websuche durchführen
            search_result = await search_provider.search(api_key=api_key, query=query, model="gpt-4o-mini")
            search_result_text = search_result.get("text", "")
            
            # Extrahiere URLs aus dem Ergebnis
            found_urls = re.findall(r'https?://[^\s)]+', search_result_text)
            for url in found_urls:
                urls_to_scrape.add(url)

        # 3. Scrapen und in RAG speichern
        collection_name = f"project_{project_id}"
        
        for url in list(urls_to_scrape)[:5]:  # Limitiere auf die ersten 5 URLs, um Kosten zu sparen
            try:
                content = await scrape_website(url)
                await asyncio.to_thread(add_text_to_collection, content, url, collection_name)
                crud.add_file_to_project(db, project_id, filename=url, local_path=url, file_type="url_dump")
            except Exception as e:
                logger.error(f"Fehler beim Scrapen/Indexieren von {url}: {e}")

    except json.JSONDecodeError as e:
        logger.error(f"Ungültiges JSON in der Antwort des LLM: {e}")
    except Exception as e:
        logger.error(f"Fehler bei der autonomen Recherche: {e}", exc_info=True)

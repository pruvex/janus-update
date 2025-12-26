import logging
import asyncio
import urllib.request
import urllib.error
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger("janus_backend")

def _fetch_and_parse(url: str) -> str:
    """Synchrone Funktion zum Laden und Parsen einer Webseite."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Unnötige Elemente entfernen
        for script_or_style in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            script_or_style.decompose()
            
        # Text extrahieren
        text = soup.get_text(separator='\n')
        
        # Leerzeilen bereinigen
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Metadaten holen (Titel)
        title = soup.title.string if soup.title else url
        
        return f"Titel: {title}\nURL: {url}\n\n--- INHALT ---\n{text}"
        
    except Exception as e:
        logger.error(f"Scraping error for {url}: {e}")
        return f"Fehler beim Lesen der Webseite: {str(e)}"

async def scrape_website(url: str) -> str:
    """
    Asynchrone Wrapper-Funktion für den Scraper.
    Lädt den Textinhalt einer Webseite herunter.
    """
    logger.info(f"Scraping URL: {url}")
    return await asyncio.to_thread(_fetch_and_parse, url)

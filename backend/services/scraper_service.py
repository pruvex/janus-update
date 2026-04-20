import logging
import asyncio
import time
import urllib.request
from bs4 import BeautifulSoup

from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1

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

async def scrape_website(url: str, provider: str = "", **kwargs) -> ToolResultV1:
    """
    Asynchrone Wrapper-Funktion für den Scraper.
    Lädt den Textinhalt einer Webseite herunter.
    Gibt ToolResultV1 (Diamond Skill Contract) zurück.
    Provider-Weiche: Ollama erhält max. 1000 Zeichen.
    """
    started_at = time.perf_counter()
    skill_name = "system.scrape_website"

    def _elapsed_ms() -> int:
        return int((time.perf_counter() - started_at) * 1000)

    try:
        normalized_url = str(url or "").strip()
        if not normalized_url:
            logger.warning("skill=%s status=error code=INVALID_INPUT", skill_name)
            return ToolResultV1(
                status="error",
                data={},
                error=ToolErrorDetails(
                    code="INVALID_INPUT",
                    message="Keine URL angegeben.",
                ),
                metadata={"execution_time_ms": _elapsed_ms()},
            )

        logger.info("Scraping URL: %s", normalized_url)
        content = await asyncio.to_thread(_fetch_and_parse, normalized_url)

        if content.startswith("Fehler beim Lesen"):
            logger.warning("skill=%s status=error code=SCRAPE_FAILED url=%s ms=%s", skill_name, normalized_url, _elapsed_ms())
            return ToolResultV1(
                status="error",
                data={},
                error=ToolErrorDetails(
                    code="SCRAPE_FAILED",
                    message=content,
                ),
                metadata={"execution_time_ms": _elapsed_ms()},
            )

        # Provider-Weiche: Ollama bekommt gekürzten Content
        is_ollama = str(provider or kwargs.get("provider", "")).strip().lower() == "ollama"
        if is_ollama and len(content) > 1000:
            content = content[:1000] + "\n... [Inhalt für lokales Modell auf 1000 Zeichen gekürzt.]"

        logger.info("skill=%s status=ok url=%s chars=%s ollama_truncated=%s ms=%s", skill_name, normalized_url, len(content), is_ollama, _elapsed_ms())
        return ToolResultV1(
            status="ok",
            data={"content": content, "url": normalized_url, "char_count": len(content)},
            metadata={"execution_time_ms": _elapsed_ms()},
        )

    except Exception as e:
        logger.error("skill=%s status=error code=SCRAPE_FAILED url=%s error=%s ms=%s", skill_name, url, e, _elapsed_ms(), exc_info=True)
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(
                code="SCRAPE_FAILED",
                message=str(e),
            ),
            metadata={"execution_time_ms": _elapsed_ms()},
        )

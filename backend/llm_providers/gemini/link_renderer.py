"""
Gemini Link Renderer – Janus Brute-Force Implementation

AUTARK: Funktioniert vollständig ohne LLM-Tags oder API-Metadaten.
1. Brute-Force Keyword Matching: Durchsucht Text nach Produktnamen/Aliassen aus Map
2. Automatischer Wiki-Linker: Erkennt großgeschriebene Eigennamen
3. Notfall-Überschrift: Immer "**Gefundene Quellen & Angebote:**" anhängen
"""

import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote_plus

logger = logging.getLogger("janus_backend")

# 💎 IN-PLACE FIX: Item-Anfänger für intelligente Term-Extraction
ITEM_STARTERS = {
    "serie", "modell", "sorte", "typ", "variante", "ausführung",
    "größe", "format", "edition", "version", "line", "reihe",
    "produkt", "artikel", "gerät", "maschine", "anlage"
}

# 💎 IN-PLACE FIX: Preis-Indikatoren
PRICE_INDICATORS = {
    "€", "euro", "eur", "preis", "kosten", "kostet", "uvp", 
    "ab", "ab ", "statt", "statt ", "sparen", "sparen sie",
    "günstig", "billig", "teuer", "angebot", "deal"
}

# 💎 CLEAN-DATA FIX: Füllwörter für Text-Säuberung (Case-Insensitive)
FILLER_WORDS = {
    "z. b.", "ca.", "ab", "kostet", "liegen bei", "etwa", 
    "straßenpreis", "uvp", "ca", "z.b.", "z.b", "ca ",
    "ungefähr", "circa", "etwa", "rund", "ca.:"
}

# 💎 IMPORT-REPAIR FIX: Wikipedia Stop-Wörter als globale Konstante
WIKI_STOP_WORDS = {
    "der", "die", "das", "den", "dem", "ein", "eine", "einen", "einer", "eines", "einem",
    "und", "oder", "aber", "sondern", "denn", "weil", "wenn", "als", "wie", "bis", "seit",
    "ob", "damit", "sodass", "dass", "obwohl", "trotz", "während", "indem", "wobei",
    "er", "sie", "es", "wir", "ihr", "sie", "ich", "du", "mein", "dein", "sein",
    "dieser", "diese", "dieses", "jener", "jene", "jenes", "welcher", "welche", "welches",
    "mancher", "manche", "manches", "solcher", "solche", "solches", "aller", "alle", "alles",
    "jeder", "jede", "jedes", "beide", "beides", "einer", "eines", "kein", "keine",
    "auf", "in", "an", "bei", "mit", "von", "zu", "für", "durch", "gegen", "ohne",
    "um", "unter", "über", "vor", "nach", "zwischen", "neben", "hinter", "neben",
    "auch", "nur", "schon", "noch", "immer", "nie", "oft", "sehr", "mehr", "weniger",
    "hier", "dort", "da", "wo", "wohin", "her", "hin", "überall", "nirgends",
    "jetzt", "dann", "bald", "später", "früher", "nie", "immer", "oft", "selten",
    "ja", "nein", "vielleicht", "wohl", "gewiss", "sicher", "wahrscheinlich",
    "etwas", "nichts", "alles", "viel", "wenig", "mehr", "genug", "zu", "sehr"
}


class GeminiLinkRenderer:
    """
    JANUS BRUTE-FORCE RENDERER – Vollständig autark.
    
    Kernaufgaben:
    1. Brute-Force Keyword Matching: Durchsucht Text nach Produktnamen/Aliassen
    2. Automatischer Wiki-Linker: Erkennt großgeschriebene Eigennamen
    3. Notfall-Überschrift: Immer "**Gefundene Quellen & Angebote:**" anhängen
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize renderer with product map and alias index.
        """
        self._product_map: Dict[str, Dict[str, Any]] = {}
        self._url_to_product: Dict[str, str] = {}
        # Brute-Force Index: keyword -> (product_id, url, product_name)
        self._keyword_index: Dict[str, Tuple[str, str, str]] = {}
        self._links_injected_this_turn = 0
        
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "idealo_product_map.json"
        else:
            config_path = Path(config_path)
        
        self._load_product_map(config_path)
    
    def _load_product_map(self, config_path: Path) -> None:
        """Load product map and build Brute-Force keyword index."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._product_map = json.load(f)
            
            # Build Brute-Force keyword index
            for product_id, product_data in self._product_map.items():
                url = product_data.get("url", "")
                product_name = product_data.get("name", product_id)
                aliases = product_data.get("aliases", [])
                
                if url:
                    # Index main product name
                    self._keyword_index[product_name.lower()] = (product_id, url, product_name)
                    # Index all aliases
                    for alias in aliases:
                        alias_lower = alias.lower().strip()
                        if alias_lower and alias_lower not in self._keyword_index:
                            self._keyword_index[alias_lower] = (product_id, url, product_name)
                    # Also store URL mapping
                    self._url_to_product[url] = product_name
            
            logger.info(
                "Brute-Force Renderer: Loaded %s products with %s keyword mappings",
                len(self._product_map),
                len(self._keyword_index)
            )
        except Exception as e:
            logger.error("Brute-Force Renderer: Failed to load product map from %s: %s", config_path, e)
            self._product_map = {}
            self._url_to_product = {}
            self._keyword_index = {}
    
    def reset_turn_counter(self) -> None:
        """Reset the per-turn link counter. Call at start of each response."""
        self._links_injected_this_turn = 0
    
    def render_with_sources(
        self,
        text: str,
        search_results: List[Dict[str, Any]],
        wiki_results: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        SOURCE-MAPPER: Deterministische Link-Erzeugung aus Tool-Ergebnissen.
        
        Statt im Text nach Begriffen zu suchen, nutzen wir die echten, strukturierten
        Daten von Google Search (Idealo) und Wikipedia.
        
        Zwei klar getrennte Sektionen:
        1. "### Angebote bei Idealo" - aus search_results
        2. "### Hintergrundwissen (Wikipedia)" - aus wiki_results
        
        Das LLM liefert den Text, wir setzen die exakten Quellen darunter.
        """
        if not text or not text.strip():
            return {"text": text or ""}
        
        self.reset_turn_counter()
        
        # Sammle alle Links
        idealo_links: List[Dict[str, str]] = []
        wiki_links: List[Dict[str, str]] = []
        seen_urls: Set[str] = set()
        
        # SCHRITT 1: Idealo-Links aus search_results extrahieren
        for result in search_results or []:
            # Extrahiere Payload aus Tool-Ergebnis
            payload = self._extract_payload_from_result(result)
            if not payload:
                continue
            
            data = payload.get("data", {}) if isinstance(payload.get("data"), dict) else {}
            sources = data.get("sources", []) if isinstance(data.get("sources"), list) else []
            
            for source in sources:
                if not isinstance(source, dict):
                    continue
                
                title = str(source.get("title") or source.get("name") or "Produkt").strip()
                url = str(source.get("url") or source.get("uri") or "").strip()
                
                # Nur Idealo-URLs
                if url and "idealo.de" in url.lower() and url not in seen_urls:
                    idealo_links.append({
                        "type": "idealo",
                        "title": title,
                        "url": url
                    })
                    seen_urls.add(url)
        
        # SCHRITT 2: Wikipedia-Links aus wiki_results extrahieren
        for result in wiki_results or []:
            payload = self._extract_payload_from_result(result)
            if not payload:
                continue
            
            data = payload.get("data", {}) if isinstance(payload.get("data"), dict) else {}
            
            # Versuche verschiedene Datenstrukturen
            wiki_title = data.get("title") or data.get("topic") or data.get("query")
            wiki_url = data.get("url") or data.get("uri") or data.get("link")
            
            # Fallback: Konstruiere URL aus Titel
            if wiki_title and not wiki_url:
                wiki_topic = str(wiki_title).replace(' ', '_')
                wiki_url = f"https://de.wikipedia.org/wiki/{quote_plus(wiki_topic)}"
            
            if wiki_url and wiki_title and wiki_url not in seen_urls:
                wiki_links.append({
                    "type": "wikipedia",
                    "title": str(wiki_title),
                    "url": wiki_url
                })
                seen_urls.add(wiki_url)
        
        # SCHRITT 3: Zwei Sektionen am Ende anhängen
        final_text = text.strip()
        
        # Idealo-Sektion
        if idealo_links:
            final_text += "\n\n### Angebote bei Idealo\n"
            for link in idealo_links[:10]:  # Max 10 Links
                final_text += f"- 🌐 [{link['title']}]({link['url']})\n"
                self._links_injected_this_turn += 1
        
        # Wikipedia-Sektion
        if wiki_links:
            final_text += "\n### Hintergrundwissen (Wikipedia)\n"
            for link in wiki_links[:5]:  # Max 5 Links
                final_text += f"- 📖 [{link['title']}]({link['url']})\n"
                self._links_injected_this_turn += 1
        
        logger.info(
            "Source-Mapper: %s Idealo-Links, %s Wikipedia-Links angehängt",
            len(idealo_links), len(wiki_links)
        )
        
        return {"text": final_text}

    def _extract_payload_from_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extrahiert das Payload aus verschiedenen Tool-Result-Formaten.
        """
        if not isinstance(result, dict):
            return None
        
        # Direktes Payload
        if "payload" in result:
            payload = result.get("payload")
            if isinstance(payload, dict):
                return payload
        
        # Content-Block Format
        if "content" in result:
            content = result.get("content")
            if isinstance(content, dict):
                return content
        
        # Direkte Daten
        if "data" in result or "status" in result:
            return result
        
        return None

    def render_aggregated_sources(
        self,
        full_response: str,
        all_tool_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        💎 AGGREGATOR FIX: Structured Source Aggregator – Post-Aggregation Rendering.
        
        Statt "In-Place"-Rendering während der Tool-Loops, sammeln wir alle Tool-Ergebnisse
        und erstellen am Ende eine saubere Quellen-Sektion.
        
        Architektur:
        1. Iteriere über all_tool_results
        2. Extrahiere URLs aus Websearch (Idealo) und Wikipedia
        3. Erstelle Sektion ## Quellen & Angebote am Ende
        4. Jeder Skill bekommt seinen eigenen Unter-Header:
           - ### Angebote (Websearch)
           - ### Wissens-Quellen (Wikipedia)
        
        Garantie: Die Liste steht AM ENDE der Nachricht und niemals mitten im Text.
        """
        if not full_response or not full_response.strip():
            return {"text": full_response or ""}
        
        if not all_tool_results:
            return {"text": full_response}
        
        # Sammle URLs nach Skill-Typ
        websearch_links: List[Dict[str, str]] = []
        wiki_links: List[Dict[str, str]] = []
        seen_urls: Set[str] = set()
        
        for result in all_tool_results:
            if not isinstance(result, dict):
                continue
            
            skill_name = str(result.get("name") or "").lower()
            payload = self._extract_payload_from_result(result)
            if not payload:
                # Versuche direkt aus content zu extrahieren
                content = result.get("content")
                if isinstance(content, dict):
                    payload = content
                elif isinstance(content, str):
                    try:
                        payload = json.loads(content)
                    except Exception:
                        continue
            
            if not payload:
                continue
            
            data = payload.get("data", {}) if isinstance(payload.get("data"), dict) else {}
            
            # 💎 WEBSEARCH: Extrahiere Idealo-Links
            if "websearch" in skill_name or "search" in skill_name:
                sources = data.get("sources", []) if isinstance(data.get("sources"), list) else []
                for source in sources:
                    if not isinstance(source, dict):
                        continue
                    url = str(source.get("url") or source.get("uri") or "").strip()
                    title = str(source.get("title") or source.get("name") or "Produkt").strip()
                    if url and url not in seen_urls:
                        websearch_links.append({"title": title, "url": url})
                        seen_urls.add(url)
            
            # 💎 WIKIPEDIA: Extrahiere Wiki-Links
            if "wikipedia" in skill_name or "wiki" in skill_name:
                wiki_title = data.get("title") or data.get("topic") or data.get("query")
                wiki_url = data.get("url") or data.get("uri") or data.get("link")
                if wiki_title and not wiki_url:
                    wiki_topic = str(wiki_title).replace(' ', '_')
                    wiki_url = f"https://de.wikipedia.org/wiki/{quote_plus(wiki_topic)}"
                if wiki_url and wiki_title and wiki_url not in seen_urls:
                    wiki_links.append({"title": str(wiki_title), "url": wiki_url})
                    seen_urls.add(wiki_url)
        
        # 💎 ERSTELLE FINALE SEKTION am Ende
        if not websearch_links and not wiki_links:
            return {"text": full_response}
        
        final_text = full_response.rstrip()
        
        # Haupt-Header
        final_text += "\n\n## Quellen & Angebote\n"
        
        # Websearch-Sektion
        if websearch_links:
            final_text += "\n### Angebote (Websearch)\n"
            for link in websearch_links[:10]:  # Max 10 Links
                final_text += f"- 🌐 [{link['title']}]({link['url']})\n"
        
        # Wikipedia-Sektion
        if wiki_links:
            final_text += "\n### Wissens-Quellen (Wikipedia)\n"
            for link in wiki_links[:5]:  # Max 5 Links
                final_text += f"- 📖 [{link['title']}]({link['url']})\n"
        
        logger.info(
            "AGGREGATOR FIX: %s Websearch-Links, %s Wikipedia-Links aggregiert",
            len(websearch_links), len(wiki_links)
        )
        
        return {"text": final_text}

    def render_final_response(
        self,
        response: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        💎 CLEAN-ARCHITECTURE FIX: Nur Shopping-Links (Idealo).
        
        Der LinkRenderer ist ausschließlich für Preis/Shopping-Informationen zuständig.
        Wikipedia-Links werden vom system.wikipedia_summary Skill erzeugt, NICHT hier!
        
        Verarbeitet nur Absätze mit Preis-Indikatoren (€, Euro, kosten, etc.).
        """
        if response.get("type") != "text" and not response.get("text"):
            return response
        
        final_text = str(response.get("text") or "").strip()
        if not final_text:
            return response
        
        self.reset_turn_counter()
        
        # Robuster Split in Absätze
        paragraphs = self._split_text_into_paragraphs(final_text)
        
        processed_paragraphs: List[str] = []
        seen_urls: Set[str] = set()
        
        # 💎 NUR SHOPPING-ABSÄTZE VERARBEITEN
        for paragraph in paragraphs:
            if not paragraph.strip():
                processed_paragraphs.append(paragraph)
                continue
            
            # Nur Absätze mit Preis-Indikatoren verarbeiten
            para_lower = paragraph.lower()
            has_price = any(indicator in para_lower for indicator in PRICE_INDICATORS)
            
            if has_price:
                # 💎 SHOPPING PIPELINE (nur für Idealo)
                processed_para, new_links = self._process_shopping_paragraph(paragraph, seen_urls)
                # URLs tracken
                for link in new_links:
                    seen_urls.add(link["url"])
                processed_paragraphs.append(processed_para)
            else:
                # Kein Preis-Kontext: Absatz unverändert lassen
                # Wikipedia-Links werden vom Skill-System erzeugt!
                processed_paragraphs.append(paragraph)
        
        rendered_text = '\n\n'.join(processed_paragraphs)
        response["text"] = rendered_text
        
        logger.info("Clean-Architecture: %s Absätze verarbeitet (nur Shopping)", len(paragraphs))
        
        return response
    
    def _split_text_into_paragraphs(self, text: str) -> List[str]:
        """
        💎 DIAMOND-STANDARD: Robuster Split in Absätze (double newlines).
        """
        # Split bei doppelten Zeilenumbrüchen
        paragraphs = text.split('\n\n')
        
        # Bereinige: entferne leere Absätze
        cleaned = []
        for para in paragraphs:
            stripped = para.strip()
            if stripped:
                cleaned.append(stripped)
        
        return cleaned
    
    def _process_shopping_paragraph(
        self,
        paragraph: str,
        seen_urls: Set[str]
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        💎 CLEAN-ARCHITECTURE SHOPPING PIPELINE: Nur für Idealo-Links.
        
        Zwei-Phasen-Extraktion:
        Phase 1: Exakte Produktnamen aus idealo_product_map.json
        Phase 2: Fettgedruckter Text (kein Label, also nicht mit : enden)
        
        NO-GARBAGE POLICY:
        - Keine Links für Begriffe < 3 Zeichen
        - Keine Labels (enden mit Doppelpunkt)
        
        Returns: (processed_paragraph, list_of_new_links)
        """
        links: List[Dict[str, str]] = []
        search_term: Optional[str] = None
        
        # ============================================================================
        # 💎 PHASE 1: Exakter Treffer aus JSON Map (höchste Priorität)
        # ============================================================================
        product_match = self._find_product_in_paragraph(paragraph)
        if product_match:
            product_name, url = product_match
            clean_url = self._clean_url_for_insertion(url)
            if clean_url and clean_url not in seen_urls:
                links.append({
                    "type": "idealo",
                    "title": product_name,
                    "url": clean_url
                })
                seen_urls.add(clean_url)
                link_lines = [f"\n- 🌐 [Idealo Suche nach: '{product_name}']({clean_url})"]
                paragraph = paragraph + "".join(link_lines)
                return paragraph, links
        
        # ============================================================================
        # 💎 PHASE 2: Fettgedruckter Text (kein Label)
        # ============================================================================
        bold_matches = re.findall(r'\*\*(.+?)\*\*', paragraph)
        for bold_text in bold_matches:
            clean_bold = self._sanitize_search_term(bold_text)
            # NO-GARBAGE: Keine Labels mit Doppelpunkt, min 3 Zeichen
            if clean_bold and not clean_bold.endswith(':') and len(clean_bold) >= 3:
                search_term = clean_bold
                break
        
        # ============================================================================
        # 💎 LINK-ERZEUGUNG
        # ============================================================================
        if search_term:
            search_url = f"https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={quote_plus(search_term)}"
            clean_url = self._validate_url_strict(search_url)
            
            if clean_url and clean_url not in seen_urls:
                links.append({
                    "type": "idealo",
                    "title": search_term,
                    "url": clean_url
                })
                seen_urls.add(clean_url)
                link_lines = [f"\n- 🌐 [Idealo Suche nach: '{search_term}']({clean_url})"]
                paragraph = paragraph + "".join(link_lines)
        
        return paragraph, links
    
    def _process_block_omni_matcher(
        self,
        block: str,
        tier1_query: Optional[str],
        seen_urls: Set[str],
        has_tier1_data: bool
    ) -> Tuple[str, List[Dict[str, str]], Optional[str]]:
        """
        💎 OMNI-MATCHER: Dreistufige Kaskade für jeden Block.
        
        ZERO-HALLUCINATION FIX:
        - Bold-Text ONLY: **Produktname** ist der EXKLUSIVE Suchbegriff
        - Kein Context-Memory, keine Zusätze, keine Historie!
        - Radikale Sanitization: **, *, :, Anführungszeichen, Klammern entfernt
        
        Returns: (processed_block, links, tier_used)
        """
        links: List[Dict[str, str]] = []
        tier_used: Optional[str] = None
        
        # Prüfe auf Preis-Kontext
        has_price = any(indicator in block.lower() for indicator in PRICE_INDICATORS)
        
        # 💎 TIER 1: Metadata-Query (nur wenn Daten vorhanden und Preis-Kontext)
        if tier1_query and has_price:
            search_url = f"https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={quote_plus(tier1_query)}"
            clean_url = self._validate_url_strict(search_url)
            if clean_url and clean_url not in seen_urls:
                links.append({
                    "type": "idealo",
                    "title": tier1_query,
                    "url": clean_url
                })
                tier_used = "tier1"
                logger.info(f"Omni-Matcher TIER 1: [{tier1_query}] für Block")
        
        # 💎 TIER 2: JSON-Keyword Fallback (wenn Tier 1 fehlt oder kein Treffer)
        if not links:
            product_match = self._find_product_in_paragraph(block)
            if product_match:
                product_name, url = product_match
                clean_url = self._clean_url_for_insertion(url)
                if clean_url and clean_url not in seen_urls:
                    links.append({
                        "type": "idealo",
                        "title": product_name,
                        "url": clean_url
                    })
                    tier_used = "tier2"
                    logger.info(f"Omni-Matcher TIER 2: JSON-Keyword [{product_name}] für Block")
        
        # 💎 TIER 3: Context-Extraction Notfall (wenn Tier 1+2 fehlen, aber Preis da)
        # 💎 ZERO-HALLUCINATION: NUR Bold-Text, kein Context-Memory!
        if not links and has_price:
            search_term = self._extract_clean_term_from_bold(block)
            if search_term and len(search_term) >= 3:
                search_url = f"https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={quote_plus(search_term)}"
                clean_search_url = self._validate_url_strict(search_url)
                if clean_search_url and clean_search_url not in seen_urls:
                    links.append({
                        "type": "idealo",
                        "title": search_term,
                        "url": clean_search_url
                    })
                    tier_used = "tier3"
                    logger.info(f"Omni-Matcher TIER 3: Bold-Extraction [{search_term}] für Block")
        
        # 💎 LISTEN-LAYOUT: Eingerückte Links je nach Block-Typ
        if links:
            link_lines = self._format_links_for_block(block, links)
            block = block + "".join(link_lines)
        
        return block, links, tier_used
    
    def _format_links_for_block(
        self,
        block: str,
        links: List[Dict[str, str]]
    ) -> List[str]:
        """
        💎 LISTEN-LAYOUT: Formatierung angepasst an Block-Typ.
        
        Bei Listenpunkten: Eingerückte Links (2 Leerzeichen)
        Bei Absätzen: Normale Listen-Links
        """
        link_lines: List[str] = []
        
        # Prüfe ob Block ein Listenpunkt ist
        is_list_item = bool(re.match(r'^[\s]*[-*•]', block.strip()))
        
        for link in links:
            if link["type"] == "idealo":
                if is_list_item:
                    # 💎 ZERO-HALLUCINATION: Transparenz - zeige was gesucht wurde
                    link_lines.append(f"\n  - 🌐 [Idealo Suche nach: '{link['title']}']({link['url']})")
                else:
                    # Normale Formatierung für Absätze
                    link_lines.append(f"\n- 🌐 [Idealo Suche nach: '{link['title']}']({link['url']})")
        
        return link_lines
    
    def _extract_search_queries_from_metadata(
        self, 
        metadata: Optional[Dict[str, Any]]
    ) -> List[str]:
        """
        💎 QUERY-ALIGNMENT: Extrahiere webSearchQueries aus Gemini-Metadaten.
        """
        if not metadata:
            return []
        
        queries: List[str] = []
        
        # Suche in groundingMetadata
        grounding = metadata.get("groundingMetadata", {})
        if not grounding:
            grounding = metadata.get("grounding_metadata", {})
        
        if grounding:
            web_queries = grounding.get("webSearchQueries", [])
            if not web_queries:
                web_queries = grounding.get("web_search_queries", [])
            if web_queries:
                queries.extend([q for q in web_queries if isinstance(q, str) and q.strip()])
        
        # Fallback: Suche direkt in metadata
        if not queries:
            web_queries = metadata.get("webSearchQueries", [])
            if not web_queries:
                web_queries = metadata.get("web_search_queries", [])
            if web_queries:
                queries.extend([q for q in web_queries if isinstance(q, str) and q.strip()])
        
        # Bereinige Queries
        cleaned_queries = []
        for q in queries:
            # Entferne Preis-Suffixe für besseres Matching
            q_clean = q.strip()
            if len(q_clean) >= 3:
                cleaned_queries.append(q_clean)
        
        return cleaned_queries
    
    def _split_text_into_blocks(self, text: str) -> List[str]:
        """
        💎 ROBUSTES SPLITTING: Absätze UND Listenpunkte als eigene Blöcke.
        
        Nutzt re.split() um bei \n\n (Absätze) UND bei \n- / \n* (Listen) zu trennen.
        """
        # Split bei Absätzen ODER bei Listenpunkten
        pattern = r'\n(?=[-*•\d+\.])|\n\n'
        blocks = re.split(pattern, text)
        
        # Bereinige: entferne leere Blöcke, behalte Whitespace inhaltlicher Blöcke
        cleaned_blocks = []
        for block in blocks:
            if block.strip():
                cleaned_blocks.append(block.strip())
        
        return cleaned_blocks
    
    def _find_best_matching_query(
        self, 
        block: str, 
        queries: List[str],
        used_queries: Set[str]
    ) -> Optional[str]:
        """
        � QUERY-ALIGNMENT SCORING: Wort-Überschneidungen zwischen Block und Query.
        
        Score = Anzahl gemeinsamer Wörter / max(Wörter in Block, Wörter in Query)
        """
        if not queries:
            return None
        
        block_lower = block.lower()
        block_words = set(re.findall(r'\b\w+\b', block_lower))
        
        best_query: Optional[str] = None
        best_score = 0.0
        
        for query in queries:
            if query in used_queries:
                continue  # Bereits verwendet
            
            query_lower = query.lower()
            query_words = set(re.findall(r'\b\w+\b', query_lower))
            
            if not query_words:
                continue
            
            # Berechne Überschneidung
            common_words = block_words & query_words
            
            if not common_words:
                continue
            
            # Score: Jaccard-ähnlich mit Gewichtung für wichtige Wörter
            score = len(common_words) / max(len(block_words), len(query_words))
            
            # Bonus für wichtige Wörter (Substantive, großgeschrieben)
            for word in common_words:
                if word[0].isupper() if word else False:
                    score += 0.1  # Bonus für Eigennamen
            
            logger.debug(f"Query-Alignment: Block vs [{query}] = {score:.2f} ({len(common_words)} Wörter)")
            
            if score > best_score and score >= 0.3:  # Mindest-Threshold 30%
                best_score = score
                best_query = query
        
        if best_query:
            logger.info(f"Query-Alignment: Absatz [{block[:40]}...] gematcht mit Query [{best_query}] (Score: {best_score:.2f})")
        
        return best_query
    
    def _process_block_with_query(
        self,
        block: str,
        query: Optional[str],
        seen_urls: Set[str]
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        💎 QUERY-ALIGNMENT: Verarbeite Block mit bestem Matching-Query.
        """
        links: List[Dict[str, str]] = []
        
        # Prüfe auf Preis-Kontext im Block
        has_price = any(indicator in block.lower() for indicator in PRICE_INDICATORS)
        
        if query and has_price:
            # 💎 EXAKTER LINK: Nutze den gematchten Query für Idealo-Suche
            search_url = f"https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={quote_plus(query)}"
            clean_url = self._validate_url_strict(search_url)
            
            if clean_url and clean_url not in seen_urls:
                links.append({
                    "type": "idealo",
                    "title": query,
                    "url": clean_url
                })
                logger.info(f"Query-Alignment: Idealo-Link für [{query}] erzeugt")
        
        # Injiziere Links direkt unter Block
        if links:
            link_lines = [f"\n- 🌐 [Idealo Suche nach: '{link['title']}']({link['url']})" for link in links]
            block = block + "".join(link_lines)
        
        return block, links

    def _validate_url_strict(self, url: str) -> Optional[str]:
        """
        💎 QUERY-ALIGNMENT: Strikte URL-Validierung ohne Leerzeichen.
        """
        if not url:
            return None
        
        url = url.strip()
        
        # Entferne doppelte Slashes (außer nach https://)
        url = re.sub(r'(?<!:)//+', '/', url)
        
        # Entferne doppelte Klammern
        url = re.sub(r'\)\)+', ')', url)
        url = re.sub(r'\(\(+', '(', url)
        
        # 💎 KEINE Leerzeichen in URLs erlauben - quote_plus bereits angewendet
        # Aber sicherheitshalber nochmal prüfen
        if ' ' in url:
            url = url.replace(' ', '%20')
        
        # Prüfe Schema
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url.lstrip('/')
        
        return url if url.startswith('http') and ' ' not in url else None
    
    def _find_product_in_paragraph(self, paragraph: str) -> Optional[Tuple[str, str]]:
        """
        💎 IN-PLACE FIX: Finde exaktes Produkt-Match im Absatz.
        
        Returns: (product_name, url) oder None
        """
        # Sortiere Keywords nach Länge (längste zuerst)
        sorted_keywords = sorted(
            self._keyword_index.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for keyword, (product_id, url, product_name) in sorted_keywords:
            pattern = rf"(?i)\b{re.escape(keyword)}\b"
            if re.search(pattern, paragraph):
                return (product_name, url)
        
        return None
    
    def _extract_term_with_item_starters(self, paragraph: str) -> Optional[str]:
        """
        💎 IN-PLACE FIX: Extrahiere Suchbegriff via Item-Anfänger.
        
        Pattern: "Item-Anfänger + Begriff + Preis"
        """
        # Finde Item-Anfänger im Text
        para_lower = paragraph.lower()
        for starter in ITEM_STARTERS:
            if starter in para_lower:
                # Extrahiere Text nach dem Item-Anfänger bis zum Preis/Ende
                starter_pos = para_lower.find(starter)
                if starter_pos == -1:
                    continue
                
                # Text nach Item-Anfänger
                after_starter = paragraph[starter_pos + len(starter):]
                after_lower = after_starter.lower()
                
                # Finde Preis-Position
                price_pos = len(after_starter)
                for indicator in PRICE_INDICATORS:
                    pos = after_lower.find(indicator)
                    if pos != -1 and pos < price_pos:
                        price_pos = pos
                
                # Extrahiere Begriff dazwischen (max 5 Wörter)
                term_candidate = after_starter[:price_pos].strip()
                # Entferne führende Satzzeichen/Leerzeichen
                term_candidate = re.sub(r'^[\s\-:]+', '', term_candidate)
                
                words = term_candidate.split()
                if len(words) > 5:
                    words = words[:5]
                
                if words:
                    term = ' '.join(words)
                    # Bereinige
                    term = re.sub(r'[,.;:!?]$', '', term).strip()
                    if len(term) >= 3:
                        return term
        
        return None
    
    def _extract_term_before_price(self, paragraph: str) -> Optional[str]:
        """
        💎 IN-PLACE FIX: Extrahiere erste 3-5 Wörter vor Preis-Indikator.
        """
        para_lower = paragraph.lower()
        
        # Finde erste Preis-Position
        first_price_pos = len(paragraph)
        for indicator in PRICE_INDICATORS:
            pos = para_lower.find(indicator)
            if pos != -1 and pos < first_price_pos:
                first_price_pos = pos
        
        if first_price_pos >= len(paragraph):
            return None
        
        # Extrahiere 3-5 Wörter davor
        before_price = paragraph[:first_price_pos].strip()
        words = before_price.split()
        
        # Nimm letzte 3-5 Wörter (wahrscheinlich das Produkt)
        if len(words) > 5:
            words = words[-5:]
        elif len(words) < 3:
            # Zu kurz, nimm mehr Kontext vom Anfang
            return None
        
        term = ' '.join(words)
        # Bereinige: entferne führende Kleinbuchstaben-Artikel
        term = re.sub(r'^(der |die |das |den |dem |ein |eine |einen )', '', term, flags=re.IGNORECASE)
        term = re.sub(r'[,.;:!?]$', '', term).strip()
        
        return term if len(term) >= 3 else None
    
    # ============================================================================
    # 💎 ZERO-HALLUCINATION FIX: Radikal vereinfachte Text-Extraktion
    # ============================================================================
    
    def _extract_clean_term_from_bold(self, block: str) -> Optional[str]:
        """
        💎 ZERO-HALLUCINATION: EXKLUSIV Bold-Text Extraktion.
        
        Regel: Der Suchbegriff ist AUSSCHLIESSLICH das, was das LLM fett markiert hat.
        Wenn das LLM schreibt **WMF Stelio**, dann ist der Suchbegriff nur "WMF Stelio".
        Keine Zusätze, keine Historie, kein Context-Memory!
        
        Returns: Bereinigter Suchbegriff oder None
        """
        # EXKLUSIV: Bold-Text mit Regex \*\*(.*?)\*\*
        bold_pattern = r'\*\*(.+?)\*\*'
        matches = re.findall(bold_pattern, block)
        
        for match in matches:
            bold_text = match.strip()
            
            # Radikale Sanitization
            clean_term = self._sanitize_search_term(bold_text)
            
            # Prüfe: Nicht zu kurz, nicht nur Zahlen, keine Preis-Indikatoren
            if len(clean_term) >= 3 and not clean_term.isdigit():
                if not any(ind in clean_term.lower() for ind in PRICE_INDICATORS):
                    return clean_term
        
        return None
    
    def _sanitize_search_term(self, term: str) -> str:
        """
        💎 ZERO-HALLUCINATION: Rücksichtslose Text-Säuberung.
        
        Entfernt ALLES was nicht zum Produktnamen gehört:
        - Markdown: **, *, __, _, ` (restlos entfernen)
        - Satzzeichen: :, ;, !, ?, ., , am Ende
        - Anführungszeichen: ", '
        - Klammern und deren Inhalt: (Inhalt), [Inhalt], {Inhalt}
        - Füllwörter: z. B., ca., ab, kostet, etc.
        - Preis-Muster: Zahlen + €/$/EUR
        
        Beispiel: "[B. Medium Adult):** ca. 44€" -> "Medium Adult"
        """
        if not term:
            return ""
        
        term = term.strip()
        
        # 1. Entferne Markdown-Sonderzeichen RESTLOS
        term = re.sub(r'\*+', '', term)  # ** und * entfernen
        term = re.sub(r'_+', '', term)    # __ und _ entfernen  
        term = re.sub(r'`+', '', term)   # ` und `` entfernen
        
        # 2. Entferne Anführungszeichen
        term = re.sub(r'["\']+', '', term)  # " und ' entfernen
        
        # 3. Entferne Klammern und deren Inhalt
        term = re.sub(r'\([^)]*\)', '', term)  # (Inhalt) entfernen
        term = re.sub(r'\[([^\]]*)\]', r'\1', term)  # [Inhalt] -> Inhalt
        term = re.sub(r'\{[^}]*\}', '', term)  # {Inhalt} entfernen
        
        # 4. Entferne Satzzeichen am Anfang und Ende
        term = re.sub(r'^[;:!?.,:\-]+', '', term).strip()
        term = re.sub(r'[;:!?.,:]+$', '', term).strip()
        
        # 5. Entferne Füllwörter (case-insensitive, ganze Wörter)
        for filler in FILLER_WORDS:
            pattern = rf'(?i)\b{re.escape(filler)}\b'
            term = re.sub(pattern, '', term)
        
        # 6. Entferne führende Artikel und Präpositionen
        term = re.sub(r'^(der |die |das |den |dem |ein |eine |einen |einer |eines |einem )', '', term, flags=re.IGNORECASE)
        term = re.sub(r'^(mit |für |von |zu |bei |an |auf |in |ab )', '', term, flags=re.IGNORECASE)
        
        # 7. Entferne Preis-Muster am Ende (Zahlen + Währung)
        term = re.sub(r'\s+\d+[,.]?\d*\s*[€$£]?(?:\s|$)', '', term).strip()
        
        # 8. Kollabiere mehrfache Leerzeichen
        term = re.sub(r'\s+', ' ', term).strip()
        
        return term
    
    # ============================================================================
    # ENDE ZERO-HALLUCINATION FIX
    # ============================================================================
    
    def _extract_main_themes(self, text: str) -> List[str]:
        """
        💎 IN-PLACE FIX: Extrahiere Hauptthemen für Wikipedia-Links.
        """
        # Suche nach Eigennamen (mindestens 2 Wörter, beide großgeschrieben)
        theme_pattern = r'\b([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)\b'
        matches = re.findall(theme_pattern, text)
        
        # Filtere Duplikate und kurze Begriffe, behalte nur echte Eigennamen
        themes = []
        seen = set()
        for match in matches:
            match_lower = match.lower()
            if match_lower not in seen and len(match) >= 5:
                # Prüfe ob beide Wörter sinnvoll sind
                words = match.split()
                if len(words) == 2:
                    # Beispiel: "WMF Bueno" - beide großgeschrieben
                    themes.append(match)
                    seen.add(match_lower)
        
        return themes[:3]  # Max 3 Themen
    
    def _clean_url_for_insertion(self, url: str) -> Optional[str]:
        """
        💎 IN-PLACE FIX: URL-Veredelung für saubere Links.
        """
        if not url:
            return None
        
        # Basis-Cleaning
        url = url.strip()
        
        # Entferne doppelte Slashes (außer nach https://)
        url = re.sub(r'(?<!:)//+', '/', url)
        
        # Entferne doppelte Klammern
        url = re.sub(r'\)\)+', ')', url)
        url = re.sub(r'\(\(+', '(', url)
        url = re.sub(r'\[\[+', '[', url)
        url = re.sub(r'\]\]+', ']', url)
        
        # Leerzeichen -> %20
        url = url.replace(' ', '%20')
        
        # Prüfe Schema
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url.lstrip('/')
        
        return url if url.startswith('http') else None
    
    def render_links(
        self,
        text: str,
        grounding_metadata: Optional[Dict[str, Any]] = None,
        enable_idealo: bool = True,
        enable_wikipedia: bool = True
    ) -> str:
        """
        JANUS BRUTE-FORCE RENDERER: Vollständig autark.
        
        1. Brute-Force Keyword Matching: Durchsucht Text nach Produktnamen/Aliassen
        2. Automatischer Wiki-Linker: Erkennt großgeschriebene Eigennamen  
        3. Immer "**Gefundene Quellen & Angebote:**" anhängen
        """
        if not text or not text.strip():
            return text
        
        logger.info("Brute-Force Renderer: Verarbeite Text der Laenge %s", len(text))
        
        self.reset_turn_counter()
        result = text
        
        # --- BRUTE-FORCE LAYER 1: Produkt-Keyword Matching ---
        product_links: List[Dict[str, str]] = []
        if enable_idealo and self._keyword_index:
            product_links = self._brute_force_product_matching(text)
            logger.info("Brute-Force: %s Produkt-Links gefunden", len(product_links))
        
        # --- BRUTE-FORCE LAYER 2: Automatischer Wiki-Linker ---
        wiki_links: List[Dict[str, str]] = []
        if enable_wikipedia:
            wiki_links = self._extract_proper_nouns_for_wiki(text)
            logger.info("Brute-Force: %s Wiki-Links gefunden", len(wiki_links))
        
        # --- DEDUPLIKATION ---
        seen_urls: Set[str] = set()
        all_links: List[Dict[str, str]] = []
        
        for link in product_links + wiki_links:
            url = link.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_links.append(link)
        
        # --- IMMER DIE NOTFALL-ÜBERSCHRIFT ANHÄNGEN ---
        result = self._append_brute_force_section(result, all_links)
        
        # Brute-Force Log
        logger.info(
            "Brute-Force Renderer: %s Produkt-Links, %s Wiki-Links, Gesamt: %s",
            len(product_links), len(wiki_links), len(all_links)
        )
        
        return result
    
    def _extract_links_from_metadata(
        self,
        grounding_metadata: Dict[str, Any],
        enable_idealo: bool,
        enable_wikipedia: bool
    ) -> List[Dict[str, str]]:
        """
        Extract URLs from groundingMetadata.
        
        Returns list of dicts with: {type: 'idealo'|'wikipedia', title: str, url: str}
        """
        links: List[Dict[str, str]] = []
        
        # Get grounding chunks (the actual web sources)
        chunks = grounding_metadata.get("groundingChunks", [])
        if not isinstance(chunks, list):
            chunks = []
        
        # Get grounding supports (links between response text and chunks)
        supports = grounding_metadata.get("groundingSupports", [])
        if not isinstance(supports, list):
            supports = []
        
        logger.debug("LinkRenderer: Processing %s chunks and %s supports", len(chunks), len(supports))
        
        # Collect all chunk indices referenced in supports
        referenced_chunk_indices: Set[int] = set()
        for support in supports:
            chunk_indices = support.get("groundingChunkIndices", [])
            if isinstance(chunk_indices, list):
                for idx in chunk_indices:
                    if isinstance(idx, int):
                        referenced_chunk_indices.add(idx)
        
        # Extract URLs from referenced chunks
        for idx in referenced_chunk_indices:
            if idx < 0 or idx >= len(chunks):
                continue
            
            chunk = chunks[idx]
            if not isinstance(chunk, dict):
                continue
            
            # Extract web URL from chunk
            web = chunk.get("web", {})
            if not isinstance(web, dict):
                continue
            
            uri = web.get("uri", "").strip()
            title = web.get("title", "").strip() or "Quelle"
            
            if not uri:
                continue
            
            # Categorize and filter - also collect general web links
            if self._is_idealo_url(uri):
                if enable_idealo:
                    # Diamond mapping: Find product name
                    product_name = self._resolve_product_name(uri, title)
                    links.append({
                        "type": "idealo",
                        "title": product_name or title,
                        "url": uri
                    })
            elif self._is_wikipedia_url(uri):
                if enable_wikipedia:
                    links.append({
                        "type": "wikipedia",
                        "title": self._extract_wikipedia_topic(title),
                        "url": uri
                    })
            else:
                # 💎 NO-FILTER FALLBACK: Collect general web links too
                links.append({
                    "type": "general",
                    "title": title,
                    "url": uri
                })
        
        return links
    
    def _extract_links_from_tags(
        self,
        text: str,
        enable_idealo: bool,
        enable_wikipedia: bool
    ) -> List[Dict[str, str]]:
        """
        💎 LAYER 2: Extract links from [[PRODUCT:id]] and [[WIKI:topic]] tags in text.
        
        This is the fallback layer when metadata is empty or incomplete.
        """
        import re
        links: List[Dict[str, str]] = []
        
        # Pattern for [[PRODUCT:name_or_id]] tags - case insensitive
        if enable_idealo:
            product_pattern = r'\[\[PRODUCT:([^\]]+)\]\]'
            for match in re.finditer(product_pattern, text, re.IGNORECASE):
                product_ref = match.group(1).strip()
                # Try to resolve to a real URL via product map
                product_url = None
                product_name = product_ref
                
                # Search product map for matching product
                for pid, pdata in self._product_map.items():
                    if pid.lower() == product_ref.lower() or pdata.get("name", "").lower() == product_ref.lower():
                        product_url = pdata.get("url")
                        product_name = pdata.get("name", product_ref)
                        break
                
                if product_url:
                    links.append({
                        "type": "idealo",
                        "title": product_name,
                        "url": product_url
                    })
                    logger.debug(f"LinkRenderer: Resolved tag [[PRODUCT:{product_ref}]] -> {product_url}")
        
        # Pattern for [[WIKI:topic]] tags - case insensitive
        if enable_wikipedia:
            wiki_pattern = r'\[\[WIKI:([^\]]+)\]\]'
            for match in re.finditer(wiki_pattern, text, re.IGNORECASE):
                topic = match.group(1).strip()
                # Build Wikipedia URL
                wiki_url = f"https://de.wikipedia.org/wiki/{quote_plus(topic.replace(' ', '_'))}"
                links.append({
                    "type": "wikipedia",
                    "title": topic,
                    "url": wiki_url
                })
                logger.debug(f"LinkRenderer: Resolved tag [[WIKI:{topic}]] -> {wiki_url}")
        
        return links
    
    def _is_idealo_url(self, url: str) -> bool:
        """Check if URL is from Idealo."""
        return "idealo.de" in url.lower()
    
    def _is_wikipedia_url(self, url: str) -> bool:
        """Check if URL is from Wikipedia."""
        return ".wikipedia.org" in url.lower() or url.startswith("https://de.wikipedia.org")
    
    def _resolve_product_name(self, url: str, fallback_title: str) -> Optional[str]:
        """
        Diamond mapping: Try to find a human-readable product name for an Idealo URL.
        
        Returns product name from idealo_product_map.json if URL matches, else None.
        """
        # Direct URL match
        if url in self._url_to_product:
            return self._url_to_product[url]
        
        # Base URL match (without query params)
        base_url = url.split("?")[0]
        if base_url in self._url_to_product:
            return self._url_to_product[base_url]
        
        # Fuzzy match: Check if any product URL is a substring
        for product_url, product_name in self._url_to_product.items():
            if product_url in url or url in product_url:
                return product_name
        
        return None
    
    def _append_general_sources(self, text: str, general_links: List[Dict[str, str]]) -> str:
        """
        💎 NO-FILTER FALLBACK: Append general web sources when no Idealo/Wikipedia found.
        
        Format:
        **Gefundene Quellen:**
        🔗 [Titel](URL)
        """
        if not general_links:
            return text
        
        # Check if there's already a sources section
        if "**Gefundene Quellen**" in text or "**Gefundene Quellen:**" in text:
            logger.debug("LinkRenderer: Text already contains general sources section, skipping")
            return text
        
        # Build general sources section
        lines: List[str] = ["\n\n**Gefundene Quellen:**"]
        
        for link in general_links:
            if self._links_injected_this_turn >= 10:  # MAX_LINKS_PER_TURN
                break
            title = link.get("title", "Quelle")
            url = link.get("url", "")
            if url:
                lines.append(f"\n🔗 [{title}]({url})")
                self._links_injected_this_turn += 1
        
        return text + "".join(lines)
    
    def _extract_wikipedia_topic(self, title: str) -> str:
        """Extract the topic from a Wikipedia page title."""
        # Remove common suffixes
        topic = title.replace(" – Wikipedia", "").replace(" - Wikipedia", "").replace(" | Wikipedia", "")
        return topic.strip() or "Thema"
    
    def _brute_force_product_matching(self, text: str) -> List[Dict[str, str]]:
        """
        💎 FINALE SCHLIFF: Durchsucht Text nach Produktnamen + dynamische Idealo-Suche.
        """
        links: List[Dict[str, str]] = []
        found_products: Set[str] = set()
        
        # Sortiere Keywords nach Länge (längste zuerst) für präziseres Matching
        sorted_keywords = sorted(
            self._keyword_index.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        # --- LAYER 1: Exaktes Keyword Matching aus der Map ---
        for keyword, (product_id, url, product_name) in sorted_keywords:
            if product_id in found_products:
                continue
            
            # 💎 Regex mit (?i) Flag für case-insensitive Matching
            pattern = rf"(?i)\b{re.escape(keyword)}\b"
            if re.search(pattern, text):
                # 💎 FINALE SCHLIFF: URL-Validierung
                clean_url = self._validate_url(url)
                if clean_url:
                    links.append({
                        "type": "idealo",
                        "title": product_name,
                        "url": clean_url
                    })
                    found_products.add(product_id)
                    logger.debug(f"Brute-Force: Produkt '{keyword}' -> '{product_name}' gefunden")
        
        # --- LAYER 2: Dynamische Idealo-Suche für nicht-exakte Treffer ---
        # 💎 FINALE SCHLIFF: Wenn Preis/Shopping-Kontext erkannt, aber kein exaktes Produkt
        text_lower = text.lower()
        has_shopping_context = any(kw in text_lower for kw in IDEALO_SEARCH_KEYWORDS)
        
        if has_shopping_context and len(links) == 0:
            # Extrahiere potenzielles Produkt aus dem Satz-Kontext
            search_term = self._extract_search_term(text)
            if search_term:
                search_url = f"https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={quote_plus(search_term)}"
                # 💎 FINALE SCHLIFF: URL-Validierung
                clean_search_url = self._validate_url(search_url)
                if clean_search_url:
                    links.append({
                        "type": "idealo",
                        "title": f"{search_term} auf Idealo suchen",
                        "url": clean_search_url
                    })
                    logger.info(f"Dynamische Idealo-Suche: '{search_term}'")
        
        return links
    
    def _extract_search_term(self, text: str) -> Optional[str]:
        """
        💎 FINALE SCHLIFF: Extrahiert potenzielles Produkt aus Shopping-Kontext.
        """
        # Muster: "Wie viel kostet [Produkt]?", "[Produkt] Preise", etc.
        patterns = [
            # "Produkt kosten/preis"
            rf"(?i)([A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ0-9\s]{{2,30}}?)\s+(?:kostet|kosten|preis|preise)",
            # "Preis für Produkt"
            rf"(?i)(?:preis|preise|kosten)\s+(?:für|von)\s+([A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ0-9\s]{{2,30}}?)",
            # "wie viel kostet Produkt"
            rf"(?i)(?:wie\s+viel\s+)?(?:kostet|kosten)\s+([A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ0-9\s]{{2,30}}?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                term = match.group(1).strip()
                # Bereinige: max 3 Wörter, keine Stop-Words am Ende
                words = term.split()
                if len(words) > 3:
                    term = ' '.join(words[:3])
                # Filtere kurze/unwahrscheinliche Begriffe
                if len(term) >= 3 and term.lower() not in WIKI_STOP_WORDS:
                    return term
        
        return None
    
    def _validate_url(self, url: str) -> Optional[str]:
        """
        💎 FINALE SCHLIFF: URL-Validierung für saubere Markdown-Links.
        """
        if not url:
            return None
        
        # Entferne doppelte Klammern und Leerzeichen
        url = url.strip()
        url = re.sub(r'\)\)+', ')', url)
        url = re.sub(r'\[\[+', '[', url)
        url = re.sub(r'\]\]+', ']', url)
        url = re.sub(r'\(\(+', '(', url)
        
        # Entferne Leerzeichen in URLs
        url = url.replace(' ', '%20')
        
        # Prüfe auf gültiges Schema
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url.lstrip('/')
        
        return url if url.startswith('http') else None
    
    def _get_all_links(self, text: str) -> List[Dict[str, str]]:
        """
        Hilfsmethode für Debug-Output: Sammelt alle gefundenen Links.
        """
        product_links = self._brute_force_product_matching(text)
        wiki_links = self._extract_proper_nouns_for_wiki(text)
        return product_links + wiki_links
    
    def _extract_proper_nouns_for_wiki(self, text: str) -> List[Dict[str, str]]:
        """
        💎 FINALE SCHLIFF: Intelligente Eigennamen-Erkennung für Wiki-Links.
        
        Filtert Stop-Words und prüft Kontext (mitten im Satz großgeschrieben).
        """
        links: List[Dict[str, str]] = []
        
        # Extrahiere alle großgeschriebenen Wörter/Phrasen (potenzielle Eigennamen)
        proper_noun_pattern = r'\b[A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ0-9\s]+(?:\s+[A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ0-9\s]+){0,2}\b'
        
        candidates = []
        for match in re.finditer(proper_noun_pattern, text):
            candidate = match.group().strip()
            
            # 💎 FINALE SCHLIFF: Stop-Words Filter
            if candidate.lower() in WIKI_STOP_WORDS:
                continue
            
            # 💎 FINALE SCHLIFF: Kontext-Prüfung (echte Eigennamen)
            # Muss mind. 3 Zeichen haben, nicht nur Ziffern, kein Markdown
            if (len(candidate) >= 3 and 
                not candidate.startswith('#') and 
                not candidate.startswith('[') and
                not candidate.startswith('*') and
                not candidate.isdigit()):
                candidates.append(candidate)
        
        # Zähle Häufigkeit
        noun_counts = Counter(candidates)
        
        # Top 3, die mindestens 1-mal vorkommen
        top_nouns = [
            (noun, count) for noun, count in noun_counts.most_common(10)
            if count >= 1 and len(noun) >= 3
        ][:3]
        
        # Erstelle Wiki-Links
        for noun, count in top_nouns:
            wiki_topic = noun.replace(' ', '_')
            wiki_url = f"https://de.wikipedia.org/wiki/{quote_plus(wiki_topic)}"
            links.append({
                "type": "wikipedia",
                "title": noun,
                "url": wiki_url
            })
            logger.debug(f"Brute-Force Wiki: '{noun}' (vorkommen: {count})")
        
        return links
    
    def _append_brute_force_section(
        self,
        text: str,
        links: List[Dict[str, str]]
    ) -> str:
        """
        💎 FINALE SCHLIFF: Absolute End-Sektion mit Trennlinie.
        """
        # Bereits vorhanden? Dann überspringen
        if "**Gefundene Quellen & Angebote**" in text or "**Gefundene Quellen & Angebote:**" in text:
            return text
        
        # 💎 FINALE SCHLIFF: Entferne existierende Sektionen am Ende für Neuanordnung
        text = text.strip()
        
        # Gruppiere Links
        idealo_links = [l for l in links if l["type"] == "idealo"]
        wiki_links = [l for l in links if l["type"] == "wikipedia"]
        
        # 💎 FINALE SCHLIFF: Absolute End Layout mit Trennlinie
        lines: List[str] = ["\n\n---\n**Gefundene Quellen & Angebote:**"]
        
        # Idealo-Links (Produktangebote)
        for link in idealo_links[:3]:  # Max 3
            if self._links_injected_this_turn >= 10:
                break
            title = link.get("title", "Produkt")
            url = link.get("url", "")
            # 💎 FINALE SCHLIFF: URL-Validierung
            clean_url = self._validate_url(url)
            if clean_url:
                lines.append(f"\n🌐 [Zum Angebot bei Idealo: {title}]({clean_url})")
                self._links_injected_this_turn += 1
        
        # Wikipedia-Links (Hintergrundinfo)
        for link in wiki_links[:3]:  # Max 3
            if self._links_injected_this_turn >= 10:
                break
            title = link.get("title", "Thema")
            url = link.get("url", "")
            # 💎 FINALE SCHLIFF: URL-Validierung
            clean_url = self._validate_url(url)
            if clean_url:
                lines.append(f"\n📖 [Mehr auf Wikipedia: {title}]({clean_url})")
                self._links_injected_this_turn += 1
        
        # Fallback: Wenn gar keine Links gefunden, zeige generischen Hinweis
        if not idealo_links and not wiki_links:
            lines.append("\n🔍 Weitere Informationen finden Sie auf Idealo.de oder Wikipedia.")
        
        return text + "".join(lines)
    
    def _append_links_section(self, text: str, links: List[Dict[str, str]]) -> str:
        """
        Append a clean links section at the end of the text.
        
        Format:
        **Quellen:**
        🌐 [Zum Angebot bei Idealo: Produktname](URL)
        📖 [Mehr auf Wikipedia: Thema](URL)
        """
        if not links:
            return text
        
        # Check if there's already a sources section
        if "**Quellen**" in text or "**Quellen:**" in text or "🌐" in text or "📖" in text:
            logger.debug("LinkRenderer: Text already contains links section, skipping")
            return text
        
        # Build links section
        lines: List[str] = ["\n\n**Quellen:**"]
        
        # Group by type for better organization
        idealo_links = [l for l in links if l["type"] == "idealo"]
        wiki_links = [l for l in links if l["type"] == "wikipedia"]
        
        # Add Idealo links
        for link in idealo_links:
            if self._links_injected_this_turn >= 10:  # MAX_LINKS_PER_TURN
                break
            title = link.get("title", "Produkt")
            url = link.get("url", "")
            if url:
                lines.append(f"\n🌐 [Zum Angebot bei Idealo: {title}]({url})")
                self._links_injected_this_turn += 1
        
        # Add Wikipedia links
        for link in wiki_links:
            if self._links_injected_this_turn >= 10:  # MAX_LINKS_PER_TURN
                break
            title = link.get("title", "Thema")
            url = link.get("url", "")
            if url:
                lines.append(f"\n📖 [Mehr auf Wikipedia: {title}]({url})")
                self._links_injected_this_turn += 1
        
        return text + "".join(lines)


# Global singleton instance (lazy-loaded)
_link_renderer_instance: Optional[GeminiLinkRenderer] = None


def get_link_renderer() -> GeminiLinkRenderer:
    """Get or create the global renderer instance."""
    global _link_renderer_instance
    if _link_renderer_instance is None:
        _link_renderer_instance = GeminiLinkRenderer()
    return _link_renderer_instance


def render_links(
    text: str,
    grounding_metadata: Optional[Dict[str, Any]] = None,
    enable_idealo: bool = True,
    enable_wikipedia: bool = True
) -> str:
    """
    Convenience function: Render links using the global renderer instance.
    """
    renderer = get_link_renderer()
    return renderer.render_links(text, grounding_metadata, enable_idealo, enable_wikipedia)

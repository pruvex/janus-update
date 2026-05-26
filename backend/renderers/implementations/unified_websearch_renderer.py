import re
import json
import os
import logging
from typing import Dict, Any, List, Optional
from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer
from backend.renderers.websearch_templates import WebSearchTemplateEngine

logger = logging.getLogger("janus_backend")

# Identifiers that make a <=2-word product term specific enough for a link.
# Rule: inject only when matched term has >= 3 words  OR  contains one of these.
_LINK_IDENTIFIER_PATTERN = re.compile(
    r"\b(M[1-9]|Pro|Max|Ultra|Plus|Air|Lite|Mini|Slim|OLED|SE|RTX|GTX|RX|Ti|Deck|"
    r"Series|Switch|PS\d|\d+)\b",
    re.IGNORECASE,
)

_ACCESSORY_BLACKLIST = [
    "hülle", "tasche", "case", "sleeve", "kabel", "adapter", 
    "folie", "mäppchen", "schutz", "cover", "zubehör", "ständer", "dock"
]


class UnifiedWebSearchRenderer(BaseRenderer):
    skill_id = "system.websearch"

    def __init__(self):
        self.product_map = self._load_product_map()
        logger.info(f"UnifiedWebSearchRenderer: Loaded {len(self.product_map)} products for source-aware matching.")

    def _load_product_map(self) -> Dict[str, Any]:
        map_path = os.path.join(os.getcwd(), "config", "idealo_product_map.json")
        try:
            with open(map_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load product map: {e}")
            return {}

    def _clean_text(self, text: str) -> str:
        import re
        if not text:
            return ""
        # 1. Entferne alle Janus-Anker wie [[PRODUCT:Name]] oder [[WIKI:Thema]]
        # Wir nutzen einen aggressiven Regex, der alles zwischen [[ und ]] löscht
        cleaned = re.sub(r"\[\[.*?\]\]", "", text)
        cleaned = re.sub(r"\n{2,}\[Global Research\][\s\S]*$", "", cleaned, flags=re.IGNORECASE)
        
        # 2. Entferne mehrfache Zeilenumbrüche und Leerzeichen
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r" {2,}", " ", cleaned)
        
        return cleaned.strip()

    def _render_price_enrichment(self, price_enrichment: Dict[str, Any]) -> str:
        """Rendert den Preis-Enrichment-Block aus der Seamless Integration."""
        results = price_enrichment.get("results") or []
        if not results:
            return ""
        lines = ["\n---\n**💰 Preis-Verifizierung (Janus Price-Check):**"]
        for r in results[:3]:
            p_name = str(r.get("product_name") or "")
            p_price = r.get("price")
            p_currency = str(r.get("currency") or "EUR")
            p_source = str(r.get("source") or "")
            if p_price is not None:
                lines.append(f"- {p_name}: ab {float(p_price):.2f} {p_currency} ({p_source})")
        ref_tip = price_enrichment.get("refurbished_tip")
        if ref_tip and isinstance(ref_tip, dict):
            rt_price = ref_tip.get("price")
            rt_currency = str(ref_tip.get("currency") or "EUR")
            rt_source = str(ref_tip.get("source") or "")
            if rt_price is not None:
                lines.append(f"- **[SPAR-TIPP: Refurbished]** ab {float(rt_price):.2f} {rt_currency} ({rt_source})")
        return "\n".join(lines)

    def _find_idealo_links(self, text: str) -> list:
        """Scan *text* for known product aliases; return [(product_name, idealo_url), ...].""" 
        if not text or not self.product_map:
            return []
        lowered = text.lower()
        found: list = []
        seen_urls: set = set()
        for product_data in self.product_map.values():
            idealo_url = (product_data.get("links") or {}).get("idealo.de", "").strip()
            if not idealo_url or idealo_url in seen_urls:
                continue
            product_name = str(product_data.get("name") or "").strip()
            aliases = [a.lower() for a in (product_data.get("aliases") or [])]
            all_terms = ([product_name.lower()] if product_name else []) + aliases
            if any(term and term in lowered for term in all_terms):
                found.append((product_name, idealo_url))
                seen_urls.add(idealo_url)
        return found

    def _inject_inline_product_links(self, text: str) -> tuple:
        """Insert [Idealo \U0001f517](url) after the first mention of each known product.

        Strategy: collect ALL first-occurrence matches across every product/alias,
        then resolve conflicts by keeping the longest match at each position
        (so 'iPhone 15 Pro' always beats 'iPhone 15').  Injections are applied
        right-to-left so earlier offsets are unaffected.

        Returns (modified_text, set_of_injected_idealo_urls).
        """
        if not text or not self.product_map:
            return text, set()

        # Step 1: collect (start, end, product_name, idealo_url, matched_term)
        candidates_found: list = []
        for product_data in self.product_map.values():
            idealo_url = (product_data.get("links") or {}).get("idealo.de", "").strip()
            if not idealo_url:
                continue
            product_name = str(product_data.get("name") or "").strip()
            aliases = list(product_data.get("aliases") or [])
            terms = sorted(
                ([product_name] if product_name else []) + aliases,
                key=len,
                reverse=True,
            )
            for term in terms:
                if not term:
                    continue
                
                # C8: Accessory Filter (Zero-Inference)
                term_lower = term.lower()
                if any(bad_word in term_lower for bad_word in _ACCESSORY_BLACKLIST):
                    continue

                m = re.search(re.escape(term), text, re.IGNORECASE)
                if m:
                    candidates_found.append((m.start(), m.end(), product_name, idealo_url, term))
                    break  # one match per product is enough

        # Step 2: sort by span length descending, then position ascending
        candidates_found.sort(key=lambda x: (-(x[1] - x[0]), x[0]))

        # Step 3: greedily select non-overlapping matches (longest wins)
        # Specificity gate: reject generic single-word or 2-word-without-identifier terms
        accepted: list = []
        seen_urls: set = set()
        for start, end, pname, url, matched_term in candidates_found:
            if url in seen_urls:
                continue
            if not self._is_link_worthy(matched_term):
                logger.debug("INLINE-INJECT: rejected generic term '%s'", matched_term)
                continue
            if any(s < end and e > start for s, e, *_ in accepted):
                continue  # overlaps with an already-accepted longer match
            accepted.append((start, end, pname, url, matched_term))
            seen_urls.add(url)

        # Step 4: apply insertions right-to-left to preserve earlier offsets
        result = text
        injected_urls: set = set()
        for start, end, pname, url, *_ in sorted(accepted, key=lambda x: x[0], reverse=True):
            link_tag = f" [Idealo \U0001f517]({url})"
            result = result[:end] + link_tag + result[end:]
            injected_urls.add(url)
            logger.debug("INLINE-INJECT: '%s' -> %s", pname, url)

        return result, injected_urls

    @staticmethod
    def _is_link_worthy(term: str) -> bool:
        """Returns True if the matched term is specific enough to warrant an Idealo link.

        Rule:
          - >= 3 words (e.g. 'MacBook Air M3', 'Nintendo Switch 2') -> always OK
          - >= 2 words AND contains a specific product identifier              -> OK
          - 1 word OR (2 words without identifier)                             -> rejected
        """
        words = term.strip().split()
        if len(words) >= 3:
            return True
        if len(words) >= 2 and _LINK_IDENTIFIER_PATTERN.search(term):
            return True
        return False

    @staticmethod
    def _is_release_lookup_text(text: str) -> bool:
        lowered = str(text or "").lower()
        product_marker = any(
            token in lowered
            for token in ("switch", "nintendo", "playstation", "xbox", "steam", "spiele", "games", "buch", "bücher", "film", "serie")
        )
        release_marker = any(
            token in lowered
            for token in ("release", "releases", "erscheinen", "erscheint", "neuerschein", "kommende", "naechsten monat", "nächsten monat", "next month", "upcoming")
        )
        return product_marker and release_marker

    @staticmethod
    def _asks_for_price(text: str) -> bool:
        lowered = str(text or "").lower()
        return any(token in lowered for token in ("preis", "preise", "kostet", "kosten", "uvp", "price", "cost", "kauf", "buy"))

    @staticmethod
    def _strip_unasked_price_fragments(text: str) -> str:
        value = str(text or "")
        patterns = (
            r"\s+und\s+kostet\s+laut\s+Suchergebnis\s+[^.()]+",
            r",?\s+wobei\s+der\s+Preis\s+laut\s+Suchergebnis\s+bei\s+[^.()]+\s+liegt",
            r"\s+zum\s+Preis\s+von\s+[^.()]+\s+\(laut\s+Suchergebnis\)",
            r"\s+mit\s+einem\s+Preis\s+von\s+[^.()]+\s+\(laut\s+Suchergebnis\)",
            r",?\s+das\s+laut\s+Suchergebnis\s+[^.()]+\s+kostet",
        )
        for pattern in patterns:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)
        return value

    @staticmethod
    def _format_numbered_list_for_chat(text: str) -> str:
        value = str(text or "").strip()
        if not value:
            return value

        value = re.sub(
            r"(?m)^(\d+\.\s*)\*\*(.+?)\*\*:\s*",
            lambda m: f"{m.group(1)}**{m.group(2).strip()}**\n",
            value,
        )
        value = re.sub(
            r"\s*\(Quelle:\s*([^)]+)\)\.?",
            lambda m: f"\nQuelle: {m.group(1).strip()}.",
            value,
        )
        value = re.sub(r"\n(?=\d+\.\s*\*\*)", "\n\n", value)
        return re.sub(r"\n{3,}", "\n\n", value).strip()

    @staticmethod
    def _ensure_sentence(text: str) -> str:
        value = str(text or "").strip()
        if not value:
            return value
        return value if value[-1] in ".!?" else value + "."

    @staticmethod
    def _normalize_broken_gemini_release_markup(text: str) -> str:
        value = str(text or "")
        if not value:
            return value

        # Gemini sometimes bolds the whole sentence and splits "(Quelle: IGN)"
        # as "(Quelle**\nIGN)."; restore a parseable source marker first.
        value = re.sub(
            r"\(Quelle\*\*\s*\n\s*([^)]+)\)\.?",
            lambda m: f"(Quelle: {m.group(1).strip()}).",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"\(Quelle\*\*\s*([^)]+)\)\.?",
            lambda m: f"(Quelle: {m.group(1).strip()}).",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"(?m)^(\d+\.\s*)\*\*([^\n]*\(Quelle:\s*[^)]+\)\.?)\s*$",
            lambda m: f"{m.group(1)}{m.group(2).strip()}",
            value,
        )
        return value

    @staticmethod
    def _derive_title_and_description(title: str, body: str) -> tuple[str, str]:
        clean_title = re.sub(r"\s+", " ", str(title or "")).strip(" :")
        clean_body = re.sub(r"\s+", " ", str(body or "")).strip()

        subtitle_match = re.match(
            r"^([A-ZÄÖÜ][\wÄÖÜäöüß!'-]+(?:\s+[A-ZÄÖÜ][\wÄÖÜäöüß!'-]+){0,4})\s+"
            r"(?:startet|erscheint|kommt|wird)\s+am\s+"
            r"(\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+\s+\d{4})\s+(?:als|für|mit|und|,)?\s*(.*)$",
            clean_body,
            flags=re.IGNORECASE,
        )
        if subtitle_match and "(" not in clean_title:
            subtitle = subtitle_match.group(1).strip(" :")
            date = subtitle_match.group(2).strip()
            rest = subtitle_match.group(3).strip(" ,")
            return f"{clean_title}: {subtitle} ({date})", rest

        # Handle sentence-style release entries:
        # "Final Fantasy VII Rebirth erscheint am 3. Juni 2026 als ..."
        patterns = (
            r"^(.+?)\s+(?:erscheint|erscheinen|wird|werden)\s+am\s+(\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+\s+\d{4})\s+(?:als|für|mit|und|,)?\s*(.*)$",
            r"^(.+?)\s+(?:startet|kommt)\s+am\s+(\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+\s+\d{4})\s+(?:als|für|mit|und|,)?\s*(.*)$",
        )
        for pattern in patterns:
            match = re.match(pattern, clean_title, flags=re.IGNORECASE)
            if not match:
                continue
            name = match.group(1).strip(" :")
            date = match.group(2).strip()
            tail = match.group(3).strip(" ,")
            sentence = tail or clean_body
            if tail and re.match(r"^(Fortsetzung|Fußball|Fussball|Simulation|RPG|Rollenspiel|Action|Adventure)\b", tail, flags=re.IGNORECASE):
                sentence = f"Eine {tail}"
            return f"{name} ({date})", sentence

        return clean_title, clean_body

    @classmethod
    def _extract_price_line(cls, text: str) -> tuple[str, str]:
        value = str(text or "")
        patterns = (
            r"\s+und\s+kostet\s+laut\s+Suchergebnis\s+([^.()]+)",
            r",?\s+wobei\s+der\s+Preis\s+laut\s+Suchergebnis\s+bei\s+([^.()]+)\s+liegt",
            r"\s+zum\s+Preis\s+von\s+([^.()]+)\s+\(laut\s+Suchergebnis\)",
            r"\s+mit\s+einem\s+Preis\s+von\s+([^.()]+)\s+\(laut\s+Suchergebnis\)",
            r",?\s+das\s+laut\s+Suchergebnis\s+([^.()]+)\s+kostet",
        )
        for pattern in patterns:
            match = re.search(pattern, value, flags=re.IGNORECASE)
            if not match:
                continue
            price = re.sub(r"\s+", " ", match.group(1)).strip(" ,.;")
            cleaned = re.sub(pattern, "", value, flags=re.IGNORECASE).strip()
            if price:
                return f"Preis: voraussichtlich {price} laut Suchergebnis.", cleaned
        return "Preis: online leider nicht verfügbar.", value

    @classmethod
    def _format_release_list_for_chat(cls, text: str) -> str:
        value = str(text or "").strip()
        if not value:
            return value
        value = cls._normalize_broken_gemini_release_markup(value)

        entry_re = re.compile(
            r"(?ms)^(\d+)\.\s*(?:\*\*(.+?)(?::)?\*\*:?\s*|\*\*(.+?)(?=\s+\(Quelle:|\s+Quelle:|\n|$)|(.+?\([^)]*\)):\s*|([^:\n]+(?:\([^)]*\))?)(?=\s+\(Quelle:|\s+Quelle:|\n|$)|([^:\n]+):\s*)(.*?)(?=^\d+\.|\Z)"
        )
        matches = list(entry_re.finditer(value))
        if not matches:
            return cls._format_numbered_list_for_chat(value)

        prefix = value[: matches[0].start()].strip()
        blocks: List[str] = [prefix] if prefix else []
        for match in matches:
            number = match.group(1).strip()
            title = re.sub(r"\s+", " ", match.group(2) or match.group(3) or match.group(4) or match.group(5) or match.group(6) or "").strip(" :*")
            body = re.sub(r"\s+", " ", match.group(7)).strip()
            body = re.sub(r"^\*+\s*", "", body).strip()
            leading_date = re.match(r"^\(([^)]+)\):?\s*(.*)$", body)
            if leading_date and "(" not in title:
                title = f"{title} ({leading_date.group(1).strip()})"
                body = leading_date.group(2).strip()
            title, body = cls._derive_title_and_description(title, body)

            source = ""
            source_match = re.search(r"\(Quelle:\s*([^)]+)\)\.?", body, flags=re.IGNORECASE)
            if source_match:
                source = source_match.group(1).strip()
                body = re.sub(r"\s*\(Quelle:\s*([^)]+)\)\.?", "", body, flags=re.IGNORECASE).strip()
            else:
                source_match = re.search(r"\bQuelle:\s*([^.\n]+)\.?", body, flags=re.IGNORECASE)
                if source_match:
                    source = source_match.group(1).strip()
                    body = re.sub(r"\s*\bQuelle:\s*([^.\n]+)\.?", "", body, flags=re.IGNORECASE).strip()

            price_line, body = cls._extract_price_line(body)
            description = cls._ensure_sentence(body)
            source_line = f"Quelle: {source}." if source else "Quelle: nicht eindeutig verfügbar."
            blocks.append(f"{number}. **{title}**\n{description}\n{price_line}\n{source_line}")

        return "\n\n".join(block for block in blocks if block).strip()

    @staticmethod
    def _is_internal_redirect_url(url: str) -> bool:
        try:
            from urllib.parse import urlparse

            domain = urlparse(str(url or "").strip()).netloc.lower()
        except Exception:
            return False
        return domain.endswith("vertexaisearch.cloud.google.com") or domain.endswith("google.com")

    def _render_item_list(self, items: List[Dict[str, Any]], price_enrichment: Optional[Dict]) -> str:
        """Rendert strukturierte WebSearchItem-Liste mit Item-Level-Links, Thumbnail-Placeholder und Auto-Source-Footer."""
        lines = []
        first_source_url = None
        first_domain = None
        
        for item in items:
            title = str(item.get("title") or "").strip()
            description = str(item.get("description") or "").strip()
            source_url = str(item.get("source_url") or "").strip()
            thumbnail_url = item.get("thumbnail_url")

            if not title and not source_url:
                continue
            
            # Speichere erste Quelle für Auto-Footer
            if source_url and not first_source_url:
                first_source_url = source_url
                # Extrahiere Domain
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(source_url)
                    first_domain = parsed.netloc.replace('www.', '')
                except:
                    first_domain = "Quelle"

            # [ROADMAP] Thumbnail: render img tag when available, placeholder otherwise
            if thumbnail_url:
                thumb = f"![Vorschau]({thumbnail_url}) "
            else:
                thumb = ""

            # Item-Level-Link
            if source_url and not self._is_internal_redirect_url(source_url):
                entry = f"- {thumb}[**{title or source_url}**]({source_url})"
            else:
                entry = f"- {thumb}**{title}**"

            if description:
                entry += f"\n  {description}"

            lines.append(entry)

        output = "\n".join(lines)

        if price_enrichment and isinstance(price_enrichment, dict):
            enrichment_block = self._render_price_enrichment(price_enrichment)
            if enrichment_block:
                output += enrichment_block

        # Auto-Source-Footer: Immer anzeigen wenn Websuche-Quelle vorhanden
        if first_source_url and first_domain and not self._is_internal_redirect_url(first_source_url):
            output += f"\n\n**Quelle:** [{first_domain}]({first_source_url})"

        return output

    def render(self, data: dict, llm_text: str = "") -> str:
        """Rendert WebSearch-Ergebnisse - unterstützt sowohl altes Text-Format als auch neues Structured Output."""
        # 1. Quellen aus data
        sources = data.get("sources", []) if isinstance(data, dict) else []
        items = data.get("items", []) if isinstance(data, dict) else []
        price_enrichment = data.get("price_enrichment") if isinstance(data, dict) else None

        # 2. Bereinige LLM-Text; falls leer, nutze data["text"] als Fallback
        raw_text = str((data.get("text") or "") if isinstance(data, dict) else "")
        cleaned = self._clean_text(llm_text or raw_text)
        if not cleaned and isinstance(items, list) and items:
            return self._render_item_list(items, price_enrichment if isinstance(price_enrichment, dict) else None)

        query_text = str(data.get("query") or "") if isinstance(data, dict) else ""
        scan_text = raw_text + " " + (llm_text or "")
        intent_text = query_text or scan_text
        templated = WebSearchTemplateEngine.render(data if isinstance(data, dict) else {}, cleaned, intent_text)
        if templated:
            return templated

        # 3. Inline-Produkt-Links in den Text einweben (DEAKTIVIERT - C8 Architektur-Pivot)
        # final_text, already_injected = self._inject_inline_product_links(cleaned)
        final_text = cleaned
        if self._is_release_lookup_text(intent_text):
            final_text = self._format_release_list_for_chat(final_text)
        else:
            final_text = self._format_numbered_list_for_chat(final_text)
        already_injected = set()
        # if already_injected:
        #     logger.info("INLINE-INJECT: %d product link(s) woven into text", len(already_injected))

        # 4. Footer: erste Quellen-URL
        footer = ""
        if sources and not re.search(r"\[[^\]]+\]\(https?://[^)]+\)", final_text):
            first_source = sources[0]
            url = None
            if isinstance(first_source, dict):
                url = first_source.get("url") or first_source.get("source_url")
            else:
                url = getattr(first_source, "url", None) or getattr(first_source, "source_url", None)
            if url and not self._is_internal_redirect_url(str(url)):
                from urllib.parse import urlparse
                domain = urlparse(str(url)).netloc.replace("www.", "")
                if domain:
                    footer = f"\n\n**Quelle:** [{domain}]({url})"

        # 5. Text + Footer zusammenführen
        result = f"{final_text}{footer}" if final_text else footer.lstrip()

        # 6. Preisvergleich-Block am Ende: nur für Produkte, die NICHT inline verlinkt wurden
        remaining_links = [
            (name, link_url)
            for name, link_url in self._find_idealo_links(scan_text)
            if link_url not in already_injected
        ]
        if remaining_links and not self._is_release_lookup_text(scan_text):
            link_lines = [
                f"- [{name} auf Idealo \U0001f517]({link_url})"
                for name, link_url in remaining_links[:3]
            ]
            idealo_block = "\n\n**\U0001f4b0 Preisvergleich:**\n" + "\n".join(link_lines)
            logger.info("IDEALO-BLOCK: %d non-inline link(s) appended", len(remaining_links))
            result = result + idealo_block

        return result


register_renderer(UnifiedWebSearchRenderer())

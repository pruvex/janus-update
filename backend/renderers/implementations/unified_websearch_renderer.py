import re
import json
import os
import logging
from typing import Dict, Any, List, Optional
from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer

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
            if source_url:
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
        if first_source_url and first_domain:
            output += f"\n\n**Quelle:** [{first_domain}]({first_source_url})"

        return output

    def render(self, data: dict, llm_text: str = "") -> str:
        """Rendert WebSearch-Ergebnisse - unterstützt sowohl altes Text-Format als auch neues Structured Output."""
        # 1. Quellen aus data
        sources = data.get("sources", []) if isinstance(data, dict) else []

        # 2. Bereinige LLM-Text; falls leer, nutze data["text"] als Fallback
        raw_text = str((data.get("text") or "") if isinstance(data, dict) else "")
        cleaned = self._clean_text(llm_text or raw_text)

        # 3. Inline-Produkt-Links in den Text einweben (DEAKTIVIERT - C8 Architektur-Pivot)
        # final_text, already_injected = self._inject_inline_product_links(cleaned)
        final_text = cleaned
        already_injected = set()
        # if already_injected:
        #     logger.info("INLINE-INJECT: %d product link(s) woven into text", len(already_injected))

        # 4. Footer: erste Quellen-URL
        footer = ""
        if sources:
            first_source = sources[0]
            url = None
            if isinstance(first_source, dict):
                url = first_source.get("url") or first_source.get("source_url")
            else:
                url = getattr(first_source, "url", None) or getattr(first_source, "source_url", None)
            if url:
                from urllib.parse import urlparse
                domain = urlparse(str(url)).netloc.replace("www.", "")
                if domain:
                    footer = f"\n\n**Quelle:** [{domain}]({url})"

        # 5. Text + Footer zusammenführen
        result = f"{final_text}{footer}" if final_text else footer.lstrip()

        # 6. Preisvergleich-Block am Ende: nur für Produkte, die NICHT inline verlinkt wurden
        scan_text = raw_text + " " + (llm_text or "")
        remaining_links = [
            (name, link_url)
            for name, link_url in self._find_idealo_links(scan_text)
            if link_url not in already_injected
        ]
        if remaining_links:
            link_lines = [
                f"- [{name} auf Idealo \U0001f517]({link_url})"
                for name, link_url in remaining_links[:3]
            ]
            idealo_block = "\n\n**\U0001f4b0 Preisvergleich:**\n" + "\n".join(link_lines)
            logger.info("IDEALO-BLOCK: %d non-inline link(s) appended", len(remaining_links))
            result = result + idealo_block

        return result


register_renderer(UnifiedWebSearchRenderer())

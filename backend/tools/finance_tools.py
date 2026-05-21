# backend/tools/finance_tools.py
import asyncio
import logging
import re
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import List, Optional

import aiohttp
import keyring
from pydantic import BaseModel, Field

import random

from backend.data.schemas import PriceComparisonOutput, PriceEntry
from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1
from backend.services.websearch.websearch import execute_websearch_service
from backend.services import llm_gateway

logger = logging.getLogger("janus_backend")

# ---------------------------------------------------------------------------
# Multi-Kategorie-Explosion: Vage Anfragen erkennen und expandieren
# ---------------------------------------------------------------------------
_VAGUE_QUERY_INDICATORS = frozenset([
    "modelle", "modell", "geschenk", "varianten", "sachen",
    "arten", "typen", "sorten", "produkte", "items",
    "welches", "welche", "was für", "empfehlung",
])

# ---------------------------------------------------------------------------
# In-Memory TTL-Cache (max 100 Einträge, 30 Min TTL)
# Finanzdaten (Gold, BTC etc.) werden mit TTL=0 gezielt ausgeschlossen.
# ---------------------------------------------------------------------------

_FINANCIAL_KEYWORDS = frozenset(
    ["gold", "btc", "bitcoin", "ethereum", "eth", "kurs", "aktie", "dax", "krypto", "crypto"]
)

# ---------------------------------------------------------------------------
# Hard-Source-Policy: Nur echte Preisvergleichs-Portale als Quelle
# ---------------------------------------------------------------------------
_TRUSTED_PRICE_DOMAINS = ("idealo.de", "geizhals.de")
_SITE_RESTRICTION_DE = " site:idealo.de OR site:geizhals.de"
_SITE_RESTRICTION_EN = ""  # Kein Site-Lock für internationale Suchen


def _apply_site_restriction(query: str, locale: str) -> str:
    """Hängt den site:-Operator an die Query, falls noch nicht vorhanden."""
    if locale.startswith("de") and "site:" not in query.lower():
        return query + _SITE_RESTRICTION_DE
    return query


def _is_trusted_source_url(url: Optional[str]) -> bool:
    """Prüft, ob eine URL von einem vertrauenswürdigen Preisvergleichs-Portal stammt."""
    if not url:
        return False
    url_lower = url.lower()
    return any(domain in url_lower for domain in _TRUSTED_PRICE_DOMAINS)


def _pick_trusted_url(sources: list) -> Optional[str]:
    """Wählt die erste vertrauenswürdige URL aus den Suchquellen.
    Fallback auf die erste URL, falls keine trusted gefunden wird."""
    first_url = None
    for src in (sources or []):
        u = src.get("url") if isinstance(src, dict) else None
        if not u:
            continue
        if first_url is None:
            first_url = u
        if _is_trusted_source_url(u):
            return u
    return first_url


class _TTLCache:
    def __init__(self, maxsize: int = 100, ttl_seconds: float = 1800.0):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl_seconds

    def get(self, key: str):
        if key in self._cache:
            value, ts = self._cache[key]
            if time.monotonic() - ts < self._ttl:
                self._cache.move_to_end(key)
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time.monotonic())
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)


_price_cache = _TTLCache(maxsize=100, ttl_seconds=1800.0)


# Browser-Emulation: Rotierende User-Agents + Referer für Bot-Evasion
_USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]


def _get_browser_headers() -> dict:
    """Generiert realistische Browser-Headers mit Random-UA und Referer."""
    return {
        "User-Agent": random.choice(_USER_AGENT_POOL),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Cache-Control": "max-age=0",
    }


# ---------------------------------------------------------------------------
# Input-Schema
# ---------------------------------------------------------------------------

class PriceComparisonArgs(BaseModel):
    product_name: str = Field(
        ...,
        min_length=1,
        description=(
            "Konkreter Produktname oder Modell für den Preisvergleich "
            "(z.B. 'Nintendo Switch 2 OLED', 'RTX 4090', 'Gold Feinunze'). "
            "Budget-Hinweise wie 'bis 50€' dürfen im String stehen — das Tool extrahiert sie automatisch."
        ),
    )
    condition_filter: Optional[str] = Field(
        default="both",
        description=(
            "Zustand: 'new' = nur Neuware, 'refurbished' = nur generalüberholt/refurbished, "
            "'both' = beides vergleichen (Standard)."
        ),
    )
    locale: str = Field(
        default="de_DE",
        description="Markt/Locale für Quellen und Site-Filter, z.B. 'de_DE' (idealo/geizhals), 'en_US' (Amazon/Best Buy).",
    )
    currency: str = Field(
        default="EUR",
        description="Ausgabe-Währung als ISO-Code: 'EUR', 'USD', 'GBP', …",
    )


# ---------------------------------------------------------------------------
# Preis-Extraktion aus LLM-Suchtext
# ---------------------------------------------------------------------------

_PRICE_PATTERN = re.compile(
    r"(\d{1,4}(?:[.,]\d{3})*[.,]\d{2})\s*(?:€|\$|£|EUR|USD|GBP)"
    r"|(?:€|\$|£)\s*(\d{1,4}(?:[.,]\d{3})*[.,]\d{2})"
)
_SOURCE_PATTERNS = {
    "idealo.de": re.compile(r"idealo", re.IGNORECASE),
    "geizhals.de": re.compile(r"geizhals", re.IGNORECASE),
    "amazon.com": re.compile(r"amazon\.(?:com|de)", re.IGNORECASE),
    "bestbuy.com": re.compile(r"best\s?buy", re.IGNORECASE),
}


def _extract_best_price(text: str, currency: str = "EUR") -> Optional[float]:
    """Extrahiert den niedrigsten Preis aus einem Suchtext (Best-Effort)."""
    matches = _PRICE_PATTERN.findall(text)
    prices: List[float] = []
    for m in matches:
        raw = (m[0] or m[1]).replace(".", "").replace(",", ".")
        try:
            val = float(raw)
            if 0.01 < val < 100_000:
                prices.append(val)
        except ValueError:
            continue
    return min(prices) if prices else None


def _detect_source(text: str, locale: str) -> str:
    """Ermittelt die primäre Preisquelle aus dem Suchtext."""
    for source_name, pattern in _SOURCE_PATTERNS.items():
        if pattern.search(text):
            return source_name
    return "idealo.de" if locale.startswith("de") else "amazon.com"


def _is_financial_instrument(product_name: str) -> bool:
    """Prüft ob das Produkt ein Finanzinstrument ist (kein Caching)."""
    lower = product_name.lower()
    return any(kw in lower for kw in _FINANCIAL_KEYWORDS)


async def _verify_price_from_url(url: str, expected_price: float, currency: str = "EUR", timeout: int = 10) -> dict:
    """
    Verification-Phase: Crawle die URL und extrahiere den aktuellen Preis.
    Gibt ein Dict mit live_verified, live_price, verification_status zurück.
    """
    verification_result = {
        "live_verified": False,
        "live_price": None,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "verification_status": "skipped"
    }
    
    # Nur HTTP(S) URLs verifizieren
    if not url or not url.startswith(("http://", "https://")):
        verification_result["verification_status"] = "unavailable"
        return verification_result
    
    # Skip für bestimmte problematische Domains (z.B. Amazon mit Bot-Schutz)
    skip_domains = ["amazon.", "ebay."]
    if any(domain in url.lower() for domain in skip_domains):
        verification_result["verification_status"] = "skipped"
        return verification_result
    
    try:
        logger.info("PRICE-VERIFICATION: Crawle %s", url)
        headers = _get_browser_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout), ssl=False) as response:
                if response.status != 200:
                    verification_result["verification_status"] = f"unavailable (HTTP {response.status})"
                    return verification_result
                
                html = await response.text()
                
                # Versuche Preis aus HTML zu extrahieren
                # Pattern 1: Meta-Tags (OpenGraph, Twitter)
                meta_patterns = [
                    r'<meta[^>]+property=["\']og:price:amount["\'][^>]+content=["\']([\d.,]+)["\']',
                    r'<meta[^>]+name=["\']twitter:data1["\'][^>]+content=["\']([\d.,]+)["\']',
                    r'<meta[^>]+property=["\']product:price:amount["\'][^>]+content=["\']([\d.,]+)["\']',
                ]
                
                for pattern in meta_patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        raw_price = match.group(1).replace(".", "").replace(",", ".")
                        try:
                            live_price = float(raw_price)
                            verification_result["live_price"] = live_price
                            verification_result["live_verified"] = True
                            # Vergleiche mit erwartetem Preis (10% Toleranz)
                            tolerance = expected_price * 0.10
                            if abs(live_price - expected_price) <= tolerance:
                                verification_result["verification_status"] = "verified"
                            else:
                                verification_result["verification_status"] = "mismatch"
                            logger.info("PRICE-VERIFICATION: Meta-Tag Preis gefunden: %.2f %s (status: %s)", 
                                       live_price, currency, verification_result["verification_status"])
                            return verification_result
                        except ValueError:
                            continue
                
                # Pattern 2: JSON-LD Schema.org
                jsonld_pattern = r'<script type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
                for match in re.finditer(jsonld_pattern, html, re.DOTALL | re.IGNORECASE):
                    try:
                        json_content = match.group(1)
                        # Suche nach price oder lowPrice Feldern
                        price_matches = re.findall(r'["\'](?:price|lowPrice|highPrice)["\']\s*:\s*["\']?([\d.,]+)["\']?', json_content)
                        for price_str in price_matches:
                            clean_price = price_str.replace(".", "").replace(",", ".")
                            try:
                                live_price = float(clean_price)
                                if 0.01 < live_price < 100_000:  # Plausibilitätscheck
                                    verification_result["live_price"] = live_price
                                    verification_result["live_verified"] = True
                                    tolerance = expected_price * 0.10
                                    if abs(live_price - expected_price) <= tolerance:
                                        verification_result["verification_status"] = "verified"
                                    else:
                                        verification_result["verification_status"] = "mismatch"
                                    logger.info("PRICE-VERIFICATION: JSON-LD Preis gefunden: %.2f %s", 
                                               live_price, currency)
                                    return verification_result
                            except ValueError:
                                continue
                    except Exception:
                        continue
                
                # Pattern 3: Generische Preis-Elemente im HTML
                price_elements = re.findall(r'class=["\'][^"\']*(?:price|preis|cost)["\'][^>]*>(?:[^<]*[€$£])?\s*([\d.,]+)', 
                                           html, re.IGNORECASE)
                for price_str in price_elements[:8]:  # TOP 8 für bessere Coverage
                    try:
                        clean_price = price_str.replace(".", "").replace(",", ".")
                        live_price = float(clean_price)
                        if 0.01 < live_price < 100_000:
                            verification_result["live_price"] = live_price
                            verification_result["live_verified"] = True
                            tolerance = expected_price * 0.10
                            if abs(live_price - expected_price) <= tolerance:
                                verification_result["verification_status"] = "verified"
                            else:
                                verification_result["verification_status"] = "mismatch"
                            logger.info("PRICE-VERIFICATION: HTML-Element Preis gefunden: %.2f %s", 
                                       live_price, currency)
                            return verification_result
                    except ValueError:
                        continue
                
                # Kein Preis gefunden
                verification_result["verification_status"] = "unavailable"
                logger.info("PRICE-VERIFICATION: Kein Preis auf %s gefunden", url)
                
    except asyncio.TimeoutError:
        verification_result["verification_status"] = "unavailable (timeout)"
        logger.warning("PRICE-VERIFICATION: Timeout für %s", url)
    except Exception as exc:
        verification_result["verification_status"] = f"unavailable ({str(exc)[:50]})"
        logger.warning("PRICE-VERIFICATION: Fehler für %s: %s", url, exc)
    
    return verification_result


async def _verify_single_variant(url: str, expected_price: float, currency: str, variant_index: int) -> dict:
    """
    Wrapper für _verify_price_from_url mit internem Try-Except.
    WICHTIG: Ein 503-Fehler bei einer Variante bricht NICHT die anderen ab.
    """
    try:
        result = await _verify_price_from_url(
            url=url,
            expected_price=expected_price,
            currency=currency,
            timeout=10
        )
        # Füge Varianten-Index hinzu für Zuordnung
        result["_variant_index"] = variant_index
        return result
    except Exception as exc:
        # Einzelne Variante failed - return error dict statt Exception werfen
        logger.warning("PRICE-VERIFICATION: Variante %d failed: %s", variant_index, str(exc)[:50])
        return {
            "live_verified": False,
            "live_price": None,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "verification_status": f"error: {str(exc)[:30]}",
            "_variant_index": variant_index
        }


_BUDGET_RE = re.compile(
    r"(?:bis|unter|max(?:imal)?|budget|höchstens|maximal)\s*"
    r"(\d{1,6}(?:[.,]\d{1,2})?)\s*(?:€|euro|eur)",
    re.IGNORECASE,
)
_BUDGET_RE_SUFFIX = re.compile(
    r"(\d{1,6}(?:[.,]\d{1,2})?)\s*(?:€|euro|eur)\s*"
    r"(?:budget|limit|max(?:imal)?|höchstens|obergrenze)",
    re.IGNORECASE,
)
_BUDGET_RE_BARE = re.compile(
    r"(?:bis|unter|max(?:imal)?|budget|höchstens)\s+"
    r"(\d{1,6}(?:[.,]\d{1,2})?)\b",
    re.IGNORECASE,
)


def _extract_budget_limit(product_name: str) -> Optional[float]:
    """Extracts a budget ceiling from the query string.

    Recognises patterns like:
      - "bis 25€", "unter 50 Euro", "max 100€"
      - "25€ Budget", "30 EUR Limit"
      - "bis 25" (bare number after budget keyword)

    Returns None if no budget is found.
    """
    for pattern in (_BUDGET_RE, _BUDGET_RE_SUFFIX, _BUDGET_RE_BARE):
        m = pattern.search(product_name)
        if m:
            raw = m.group(1).replace(",", ".")
            try:
                value = float(raw)
                if 0.5 <= value <= 99999:
                    return value
            except ValueError:
                continue
    return None


def _strip_budget_from_query(product_name: str) -> str:
    """Removes budget expressions from the search query so web searches
    focus on the product, not the price constraint."""
    cleaned = product_name
    for pattern in (_BUDGET_RE, _BUDGET_RE_SUFFIX, _BUDGET_RE_BARE):
        cleaned = pattern.sub("", cleaned)
    return re.sub(r"\s{2,}", " ", cleaned).strip() or product_name


def _build_new_query(product_name: str, locale: str) -> str:
    """Baut die Suchanfrage für Neuware mit Hard-Source-Policy."""
    if locale.startswith("de"):
        return _apply_site_restriction(f"{product_name} Preis neu günstig", locale)
    return f"{product_name} price new cheapest amazon.com OR bestbuy.com"


async def _expand_vague_query(
    product_name: str,
    api_key: str,
    provider: str,
    model: Optional[str],
    budget_limit: Optional[float] = None,
) -> List[str]:
    """
    Multi-Kategorie-Explosion: Wandelt eine vage Anfrage in EXAKT 3 konkrete Suchbegriffe um.
    Nutzt einen schnellen internen LLM-Call (max 100 Tokens) für die Expansion.

    Wenn ein ``budget_limit`` gesetzt ist, wird die Expansion auf Produkte in
    dieser Preisklasse eingeschränkt und das Limit an jeden Suchbegriff gehängt.
    """
    budget_rule = ""
    if budget_limit is not None:
        budget_rule = (
            f"\n5. BUDGET-LIMIT: Der User hat maximal {budget_limit:.0f}€. "
            f"Schlage NUR Produkte vor, die realistisch unter {budget_limit:.0f}€ erhältlich sind. "
            f"KEINE Sammlerstücke, Premium- oder Luxus-Produkte!"
        )

    expansion_prompt = f"""Du bist ein Produkt-Kategorisierer. 
Aus der vagen Anfrage "{product_name}" generiere EXAKT 3 konkrete, spezifische Suchbegriffe für verschiedene Produktkategorien.

REGELN:
1. EXAKT 3 Begriffe, komma-getrennt
2. Jeder Begriff muss ein spezifisches Produkt beschreiben (keine Kategorien)
3. Verwende Marken und Produkttypen (z.B. "LEGO", "Revell", "Actionfiguren")
4. KEINE Einleitung, KEINE Nummerierung, NUR die 3 Begriffe{budget_rule}

BEISPIEL Eingabe: "Star Wars Modelle"
BEISPIEL Ausgabe: LEGO Star Wars Sets, Star Wars Revell Bausatz, Star Wars Actionfiguren

Eingabe: "{product_name}"
Ausgabe:"""

    try:
        logger.info(
            "MULTI-CAT-EXPLOSION: Expanding vague query '%s' via LLM (budget=%s)",
            product_name, f"{budget_limit:.0f}€" if budget_limit else "none",
        )
        
        response = await llm_gateway.simple_llm_generate_content(
            provider=provider,
            model=model or "gpt-5.4-nano",
            api_key=api_key,
            prompt=expansion_prompt,
        )
        
        if isinstance(response, dict):
            text = response.get("text", "") or response.get("content", "")
        else:
            text = str(response)
        
        expanded_terms = []
        
        if "," in text:
            expanded_terms = [t.strip().strip('"\'').strip() for t in text.split(",") if t.strip()]
        else:
            expanded_terms = [t.strip().strip('"\'').strip() for t in text.split("\n") if t.strip()]
        
        expanded_terms = [t for t in expanded_terms if len(t) >= 3]

        # Budget-Suffix an jeden Term hängen, damit _extract_budget_limit
        # und die Websuche das Limit respektieren.
        if budget_limit is not None and expanded_terms:
            budget_suffix = f" bis {budget_limit:.0f}€"
            expanded_terms = [
                t if budget_suffix.lower() in t.lower() else f"{t}{budget_suffix}"
                for t in expanded_terms
            ]
            logger.info(
                "MULTI-CAT-EXPLOSION: Budget suffix '%s' appended to all terms",
                budget_suffix.strip(),
            )

        if len(expanded_terms) >= 3:
            expanded_terms = expanded_terms[:3]
            logger.info("MULTI-CAT-EXPLOSION: Generated 3 search terms: %s", expanded_terms)
            return expanded_terms
        elif expanded_terms:
            logger.info("MULTI-CAT-EXPLOSION: Generated %d search terms (fewer than 3): %s", len(expanded_terms), expanded_terms)
            return expanded_terms
        else:
            logger.warning("MULTI-CAT-EXPLOSION: No valid terms generated, falling back to original query")
            return [product_name]
            
    except Exception as exc:
        logger.warning("MULTI-CAT-EXPLOSION: Expansion failed: %s. Using original query.", exc)
        return [product_name]


async def _execute_single_search(
    query: str,
    api_key: str,
    provider: str,
    model: Optional[str],
    locale: str,
    currency: str,
    search_query_count_ref: List[int],  # Mutable reference für Zählung
) -> List[PriceEntry]:
    """
    Führt eine einzelne Websuche aus und extrahiert PriceEntry(s).
    Wird von asyncio.gather für parallele Ausführung genutzt.
    """
    results: List[PriceEntry] = []
    
    try:
        base_query = f"{query} Preis neu günstig" if locale.startswith("de") else f"{query} price new cheapest"
        search_query = _apply_site_restriction(base_query, locale)
        
        logger.info("MULTI-CAT-SEARCH: Executing search for '%s'", search_query)
        raw_result = await execute_websearch_service(
            query=search_query,
            api_key=api_key,
            provider=provider,
            model=model,
        )
        
        search_query_count_ref[0] += 1
        
        text = raw_result.get("text", "")
        sources = raw_result.get("sources", [])
        url = _pick_trusted_url(sources)
        price = _extract_best_price(text, currency)
        source = _detect_source(text, locale)
        
        if price is not None:
            # Erstelle Varianten-Label aus dem Query
            variant_label = query.replace("Preis neu günstig", "").strip()
            if len(variant_label) > 50:
                variant_label = variant_label[:47] + "..."
            
            entry = PriceEntry(
                product_name=query,
                variant=variant_label or "Variante",
                price=price,
                currency=currency,
                source=source,
                condition="new",
                includes_shipping=False,
                url=url
            )
            results.append(entry)
            logger.info("MULTI-CAT-SEARCH: Found price %.2f %s for '%s'", price, currency, query)
        else:
            logger.info("MULTI-CAT-SEARCH: No price found for '%s'", query)
            
    except Exception as exc:
        logger.warning("MULTI-CAT-SEARCH: Search failed for '%s': %s", query, exc)
    
    return results

def _merge_and_dedupe_results(all_results: List[List[PriceEntry]]) -> List[PriceEntry]:
    """
    Mergt Ergebnisse aus mehreren parallelen Suchen und entfernt Duplikate.
    Bevorzugt günstigere Preise bei gleichem Produkt.
    """
    merged: List[PriceEntry] = []
    seen_products: dict = {}  # product_name -> (price, index)
    
    for result_list in all_results:
        for entry in result_list:
            # Normalisierter Key für Deduplizierung
            key = f"{entry.product_name.lower()}:{entry.variant or ''}"
            
            if key in seen_products:
                # Vergleiche Preise, behalte den günstigeren
                existing_price, existing_idx = seen_products[key]
                if entry.price < existing_price:
                    # Ersetze mit günstigerem Eintrag
                    merged[existing_idx] = entry
                    seen_products[key] = (entry.price, existing_idx)
                    logger.info("MULTI-CAT-MERGE: Replaced duplicate with cheaper price: %.2f < %.2f", 
                               entry.price, existing_price)
            else:
                seen_products[key] = (entry.price, len(merged))
                merged.append(entry)
    
    # Sortiere nach Preis (günstigste zuerst)
    merged.sort(key=lambda x: x.price)
    
    logger.info("MULTI-CAT-MERGE: Merged %d result lists into %d unique entries", 
               len(all_results), len(merged))
    
    return merged

def _is_vague_query(product_name: str) -> bool:
    """Prüft ob eine Anfrage als 'vage' gilt und Expansion benötigt."""
    lower_name = product_name.lower()
    return any(indicator in lower_name for indicator in _VAGUE_QUERY_INDICATORS)

def _build_refurbished_query(product_name: str, locale: str) -> str:
    """Baut die Suchanfrage für Refurbished-Ware mit Hard-Source-Policy."""
    if locale.startswith("de"):
        return _apply_site_restriction(f"{product_name} generalüberholt refurbished Preis", locale)
    return f"{product_name} refurbished renewed price amazon.com OR bestbuy.com"


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

async def price_comparison_tool(
    args: PriceComparisonArgs,
    api_key: str = "",
    provider: str = "",
    model: Optional[str] = None,
) -> ToolResultV1:
    """Preisvergleich via 2-Runden-Websuche: Neuware + optionaler Refurbished-Check."""
    _shield_t0 = time.perf_counter()
    try:
        return await _price_comparison_tool_impl(args, api_key, provider, model)
    except Exception as e:
        logger.exception("system.price_comparison: unhandled failure")
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(code="PRICE_COMPARISON_FAILED", message=str(e)),
            metadata={"execution_time_ms": int((time.perf_counter() - _shield_t0) * 1000)},
        )


async def _price_comparison_tool_impl(
    args: PriceComparisonArgs,
    api_key: str = "",
    provider: str = "",
    model: Optional[str] = None,
) -> ToolResultV1:
    """Interne Implementierung (von price_comparison_tool mit Shield umschlossen)."""
    product_name = str(args.product_name or "").strip()
    condition_filter = str(args.condition_filter or "both").lower()
    locale = str(args.locale or "de_DE")
    currency = str(args.currency or "EUR")
    retrieved_at = datetime.now(timezone.utc).isoformat()

    if not product_name:
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(
                code="INVALID_ARGUMENTS",
                message="product_name darf nicht leer sein.",
            ),
        )

    # --- BUDGET-ENFORCEMENT: Limit aus Query extrahieren ---
    budget_limit = _extract_budget_limit(product_name)
    if budget_limit is not None:
        product_name = _strip_budget_from_query(product_name)
        logger.info(
            "BUDGET-ENFORCEMENT: Limit %.2f %s erkannt. Bereinigter Query: '%s'",
            budget_limit, currency, product_name,
        )

    # Cache-Key (mit Budget, da unterschiedliche Limits unterschiedliche Ergebnisse liefern)
    is_financial = _is_financial_instrument(product_name)
    budget_tag = f":budget={budget_limit}" if budget_limit is not None else ""
    cache_key = f"{product_name.lower()}:{condition_filter}:{locale}:{currency}{budget_tag}"
    if not is_financial:
        cached = _price_cache.get(cache_key)
        if cached is not None:
            logger.info("PRICE-COMPARISON: Cache-Hit für '%s'.", product_name)
            return ToolResultV1(status="ok", data=cached)

    # API-Key aus Keyring holen falls nicht injiziert
    effective_provider = str(provider or "openai").strip().lower()
    effective_api_key = api_key or keyring.get_password("Janus-Projekt", effective_provider) or ""

    results: List[PriceEntry] = []
    refurbished_tip: Optional[PriceEntry] = None
    
    # 💎 SEARCH-COSTS FIX: Zähle Websuchen für Kostenberechnung (0.01€ pro Suche)
    search_query_count = 0
    search_failure_count = 0
    SEARCH_COST_PER_QUERY_EUR = 0.01

    # --- MULTI-KATEGORIE-EXPLOSION: Vage Anfragen expandieren ---
    expanded_queries: List[str] = [product_name]  # Default: Original-Query
    is_vague = _is_vague_query(product_name)
    
    if is_vague:
        logger.info("PRICE-COMPARISON: Vage Anfrage erkannt '%s' - Starte Multi-Kategorie-Expansion", product_name)
        expanded_queries = await _expand_vague_query(
            product_name=product_name,
            api_key=effective_api_key,
            provider=effective_provider,
            model=model,
            budget_limit=budget_limit,
        )
        logger.info("PRICE-COMPARISON: Query expanded to %d specific searches: %s", len(expanded_queries), expanded_queries)
    
    # --- PARALLELE SUCHE für alle expanded queries ---
    # Nutze mutable List-Reference für Search-Cost-Counting
    search_counter = [0]  # [count] - mutable für _execute_single_search
    
    if is_vague and len(expanded_queries) > 1:
        logger.info("PRICE-COMPARISON: Starte PARALLELE SUCHE für %d Queries", len(expanded_queries))
        
        # Erstelle Tasks für parallele Ausführung
        search_tasks = [
            _execute_single_search(
                query=q,
                api_key=effective_api_key,
                provider=effective_provider,
                model=model,
                locale=locale,
                currency=currency,
                search_query_count_ref=search_counter,
            )
            for q in expanded_queries
        ]
        
        # Führe alle Suchen parallel aus
        parallel_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Filtere Exceptions und sammle Ergebnisse
        all_result_lists: List[List[PriceEntry]] = []
        for i, result in enumerate(parallel_results):
            if isinstance(result, Exception):
                search_failure_count += 1
                logger.warning("PRICE-COMPARISON: Parallel search %d failed: %s", i, result)
            else:
                all_result_lists.append(result)
        
        # Merge und Dedupliziere
        if all_result_lists:
            merged_results = _merge_and_dedupe_results(all_result_lists)
            results.extend(merged_results)
            search_query_count += search_counter[0]
            
            # Bestpreis-Einstieg markieren (günstigstes über alle Kategorien)
            if results:
                cheapest = min(results, key=lambda x: x.price)
                cheapest.variant = f"Bestpreis-Einstieg ({cheapest.variant or 'Kategorie'})"
                logger.info("PRICE-COMPARISON: Bestpreis-Einstieg identifiziert: %.2f %s (%s)", 
                           cheapest.price, cheapest.currency, cheapest.product_name)
            
            logger.info("PRICE-COMPARISON: Parallel search complete - %d total results, %d queries used", 
                       len(results), search_counter[0])
    
    # --- ANCHOR-SUCHE: Initial-Suche IMMER zuerst ausführen (für non-vague oder Fallback) ---
    # Dieser "Anchor"-Preis (günstigstes Ergebnis) bleibt IMMER erhalten
    anchor_result: Optional[PriceEntry] = None
    if not is_vague and condition_filter in ("new", "both"):
        try:
            query_new = _build_new_query(product_name, locale)
            logger.info("PRICE-COMPARISON: ANCHOR-SUCHE – Query: '%s'", query_new)
            raw_new = await execute_websearch_service(
                query=query_new,
                api_key=effective_api_key,
                provider=effective_provider,
                model=model,
            )
            search_query_count += 1  # 💎 SEARCH-COSTS: Anchor-Suche zählen
            text_new = raw_new.get("text", "")
            sources_new = raw_new.get("sources", [])
            url_new = _pick_trusted_url(sources_new)
            price_new = _extract_best_price(text_new, currency)
            source_new = _detect_source(text_new, locale)

            if price_new is not None:
                anchor_result = PriceEntry(
                    product_name=product_name,
                    variant="Bestpreis-Einstieg",
                    price=price_new,
                    currency=currency,
                    source=source_new,
                    condition="new",
                    includes_shipping=False,
                    url=url_new
                )
                logger.info(
                    "PRICE-COMPARISON: ANCHOR gefunden %s %.2f %s (%s)",
                    product_name, price_new, currency, source_new,
                )
        except Exception as exc:
            search_failure_count += 1
            logger.warning("PRICE-COMPARISON: ANCHOR-SUCHE fehlgeschlagen für '%s': %s", product_name, exc)

    # --- MacBook VARIANTEN-DIVERSIFIZIERUNG ---
    # Bei MacBook-Anfragen: Zusätzliche Varianten suchen und zur Liste hinzufügen
    if "macbook" in product_name.lower() and "m3" in product_name.lower():
        logger.info("PRICE-COMPARISON: MacBook M3 erkannt - Starte Varianten-Diversifizierung")
        
        # Definiere die 3 Hauptvarianten
        variants = [
            {"name": "MacBook Air M3 13", "query_suffix": "13 Zoll", "variant_label": "Air 13 Zoll"},
            {"name": "MacBook Air M3 15", "query_suffix": "15 Zoll", "variant_label": "Air 15 Zoll"},
            {"name": "MacBook Pro M3 14", "query_suffix": "14 Zoll Pro", "variant_label": "Pro 14 Zoll"},
        ]
        
        for variant in variants:
            try:
                variant_query = _apply_site_restriction(
                    f"{variant['name']} {variant['query_suffix']} Preis neu", locale
                )
                logger.info("PRICE-COMPARISON: Variante-Suche: '%s'", variant_query)
                
                raw_variant = await execute_websearch_service(
                    query=variant_query,
                    api_key=effective_api_key,
                    provider=effective_provider,
                    model=model,
                )
                search_query_count += 1  # 💎 SEARCH-COSTS: Varianten-Suche zählen
                
                text_variant = raw_variant.get("text", "")
                sources_variant = raw_variant.get("sources", [])
                url_variant = _pick_trusted_url(sources_variant)
                price_variant = _extract_best_price(text_variant, currency)
                source_variant = _detect_source(text_variant, locale)
                
                if price_variant is not None:
                    # Prüfe ob diese Variante bereits existiert (vermeide Duplikate)
                    existing = [r for r in results if variant['variant_label'] in (r.variant or "")]
                    if not existing:
                        results.append(PriceEntry(
                            product_name=variant['name'],
                            variant=variant['variant_label'],
                            price=price_variant,
                            currency=currency,
                            source=source_variant,
                            condition="new",
                            includes_shipping=False,
                            url=url_variant
                        ))
                        logger.info(
                            "PRICE-COMPARISON: Variante '%s' hinzugefügt: %.2f %s",
                            variant['variant_label'], price_variant, currency
                        )
            except Exception as exc:
                search_failure_count += 1
                logger.warning("PRICE-COMPARISON: Variante-Suche fehlgeschlagen für '%s': %s", variant['name'], exc)
    
    # --- ANCHOR zu results hinzufügen (wenn gefunden) ---
    if anchor_result:
        # Prüfe ob der Anchor bereits in der Liste ist (vermeide Duplikate)
        anchor_exists = any(
            abs(r.price - anchor_result.price) < 0.01 and r.variant == anchor_result.variant
            for r in results
        )
        if not anchor_exists:
            results.insert(0, anchor_result)  # Anchor immer an erster Stelle
            logger.info("PRICE-COMPARISON: ANCHOR '%s' zu results hinzugefügt (%.2f %s)",
                       anchor_result.product_name, anchor_result.price, anchor_result.currency)

    # --- FALLBACK: Wenn keine Ergebnisse (weder Anchor noch Varianten) ---
    if not results:
        try:
            query_new = _build_new_query(product_name, locale)
            logger.info("PRICE-COMPARISON: Runde 1 – Neuware-Query: '%s'", query_new)
            raw_new = await execute_websearch_service(
                query=query_new,
                api_key=effective_api_key,
                provider=effective_provider,
                model=model,
            )
            search_query_count += 1  # 💎 SEARCH-COSTS: Runde 1 zählen
            text_new = raw_new.get("text", "")
            sources_new = raw_new.get("sources", [])
            url_new = _pick_trusted_url(sources_new)
            price_new = _extract_best_price(text_new, currency)
            source_new = _detect_source(text_new, locale)

            if price_new is not None:
                results.append(PriceEntry(
                    product_name=product_name,
                    price=price_new,
                    currency=currency,
                    source=source_new,
                    condition="new",
                    includes_shipping=False,
                    url=url_new
                ))
                logger.info(
                    "PRICE-COMPARISON: Neuware %s %.2f %s (%s)",
                    product_name, price_new, currency, source_new,
                )
        except Exception as exc:
            search_failure_count += 1
            logger.warning("PRICE-COMPARISON: Runde 1 fehlgeschlagen für '%s': %s", product_name, exc)

    # --- Runde 2: Refurbished (nur bei condition_filter != 'new') ---
    if condition_filter in ("refurbished", "both") and not is_financial:
        try:
            query_refurb = _build_refurbished_query(product_name, locale)
            logger.info("PRICE-COMPARISON: Runde 2 – Refurbished-Query: '%s'", query_refurb)
            raw_refurb = await execute_websearch_service(
                query=query_refurb,
                api_key=effective_api_key,
                provider=effective_provider,
                model=model,
            )
            search_query_count += 1  # 💎 SEARCH-COSTS: Refurbished-Suche zählen
            text_refurb = raw_refurb.get("text", "")
            sources_refurb = raw_refurb.get("sources", [])
            url_refurb = _pick_trusted_url(sources_refurb)
            price_refurb = _extract_best_price(text_refurb, currency)
            source_refurb = _detect_source(text_refurb, locale)

            if price_refurb is not None:
                # 20%-Regel: Refurbished nur anzeigen wenn >= 20% Ersparnis vs. Neuware
                new_price_ref = results[0].price if results else None
                savings_pct = (
                    (new_price_ref - price_refurb) / new_price_ref
                    if new_price_ref and new_price_ref > 0
                    else 0.0
                )

                if condition_filter == "refurbished" or savings_pct >= 0.20:
                    refurbished_tip = PriceEntry(
                        product_name=product_name,
                        price=price_refurb,
                        currency=currency,
                        source=source_refurb,
                        condition="refurbished",
                        includes_shipping=False,
                        url=url_refurb
                    )
                    logger.info(
                        "PRICE-COMPARISON: Refurbished-Tipp %.1f%% Ersparnis (%.2f %s)",
                        savings_pct * 100, price_refurb, currency,
                    )
                else:
                    logger.info(
                        "PRICE-COMPARISON: Refurbished (%.2f) unter 20%%-Schwelle – nicht angezeigt.", price_refurb
                    )
        except Exception as exc:
            search_failure_count += 1
            logger.warning("PRICE-COMPARISON: Runde 2 fehlgeschlagen für '%s': %s", product_name, exc)

    # --- HARD-SOURCE-POLICY: Post-Search Validierung (DE only) ---
    if locale.startswith("de") and results:
        _pre_source_count = len(results)
        results = [r for r in results if _is_trusted_source_url(r.url) or r.url is None]
        _removed = _pre_source_count - len(results)
        if _removed:
            logger.info(
                "HARD-SOURCE-POLICY: %d/%d Ergebnisse mit Fremd-URLs entfernt.",
                _removed, _pre_source_count,
            )
    if locale.startswith("de") and refurbished_tip and refurbished_tip.url:
        if not _is_trusted_source_url(refurbished_tip.url):
            logger.info(
                "HARD-SOURCE-POLICY: Refurbished-Tipp mit Fremd-URL '%s' entfernt.",
                refurbished_tip.url[:60],
            )
            refurbished_tip = None

    # --- SORTIERUNG: Nach price aufsteigend sortieren ---
    results.sort(key=lambda x: x.price)
    logger.info("PRICE-COMPARISON: Ergebnisse nach Preis sortiert (%d Einträge)", len(results))

    # --- BUDGET-ENFORCEMENT: Harter Filter ---
    budget_exceeded = False
    _pre_filter_count = len(results)
    if budget_limit is not None and results:
        results = [r for r in results if r.price <= budget_limit]
        if refurbished_tip and refurbished_tip.price > budget_limit:
            logger.info(
                "BUDGET-ENFORCEMENT: Refurbished-Tipp %.2f %s übersteigt Budget %.2f — entfernt.",
                refurbished_tip.price, currency, budget_limit,
            )
            refurbished_tip = None
        if not results:
            budget_exceeded = True
            logger.warning(
                "BUDGET-ENFORCEMENT: ALLE %d Ergebnisse übersteigen Budget von %.2f %s.",
                _pre_filter_count, budget_limit, currency,
            )
        else:
            logger.info(
                "BUDGET-ENFORCEMENT: %d/%d Ergebnisse innerhalb Budget %.2f %s.",
                len(results), _pre_filter_count, budget_limit, currency,
            )

    if not results and refurbished_tip is None:
        if budget_exceeded:
            return ToolResultV1(
                status="ok",
                data={
                    "query": product_name,
                    "locale": locale,
                    "currency": currency,
                    "results": [],
                    "refurbished_tip": None,
                    "budget_limit": budget_limit,
                    "budget_exceeded": True,
                    "_budget_notice": (
                        f"KEIN Produkt unter {budget_limit:.0f} {currency} gefunden. "
                        f"Der günstigste gefundene Preis lag über dem Budget."
                    ),
                },
            )
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(
                code="PRICE_SOURCE_UNAVAILABLE" if search_failure_count and search_query_count == 0 else "NO_RESULTS_FOUND",
                message=(
                    f"Die Preis-/Websuche fuer '{product_name}' konnte keine verlaesslichen Quellen abrufen. "
                    "Ohne aktuelle Quellenbelege gebe ich keine Preise aus."
                    if search_failure_count and search_query_count == 0
                    else f"Kein belegbarer Preis fuer '{product_name}' gefunden. Bitte praezisiere den Produktnamen."
                ),
                details={
                    "search_query_count": search_query_count,
                    "search_failure_count": search_failure_count,
                },
            ),
        )

    # --- Bulk Verification Phase: ALLE Varianten parallel verifizieren ---
    # Sammle alle URLs mit Varianten-Index für parallel crawling
    verification_tasks = []
    variant_indices = []
    
    for i, result in enumerate(results):
        if result.url:
            verification_tasks.append(
                _verify_single_variant(
                    url=result.url,
                    expected_price=result.price,
                    currency=result.currency,
                    variant_index=i
                )
            )
            variant_indices.append(i)
    
    if verification_tasks:
        logger.info("PRICE-COMPARISON: Starte BULK-Verification für %d Varianten (Timeout: 6s)", len(verification_tasks))
        
        # 6s Latency-Guard: Lieber veralteter Preis als Timeout-Fehler
        try:
            bulk_results = await asyncio.wait_for(
                asyncio.gather(*verification_tasks, return_exceptions=True),
                timeout=6.0
            )
            
            # Verarbeite Ergebnisse pro Variante
            for idx, verify_result in enumerate(bulk_results):
                result_idx = variant_indices[idx]
                target_result = results[result_idx]
                
                if isinstance(verify_result, Exception):
                    # Einzelner Task failed - markiere als fehlgeschlagen, nicht alles abbrechen
                    target_result.live_verified = False
                    target_result.verification_status = f"error: {str(verify_result)[:30]}"
                    logger.warning("PRICE-COMPARISON: Variante %d Verifikation fehlgeschlagen: %s", 
                                   result_idx, str(verify_result)[:50])
                else:
                    # Erfolgreiche Verifikation
                    target_result.live_verified = verify_result["live_verified"]
                    target_result.live_price = verify_result["live_price"]
                    target_result.verified_at = verify_result["verified_at"]
                    target_result.verification_status = verify_result["verification_status"]
                    
                    logger.info("PRICE-COMPARISON: Variante %d Status: %s (live_price: %s)", 
                               result_idx, verify_result["verification_status"], verify_result["live_price"])
                    
                    # Überschreibe Preis wenn live verifiziert
                    if verify_result["live_verified"] and verify_result["live_price"] is not None:
                        old_price = target_result.price
                        target_result.price = verify_result["live_price"]
                        target_result.source = f"{target_result.source} (live-verifiziert)"
                        logger.info("PRICE-COMPARISON: Variante %d Preis überschrieben: %.2f -> %.2f %s", 
                                   result_idx, old_price, verify_result["live_price"], target_result.currency)
                    
                    # Markiere 503-Fehler für UI
                    elif "503" in str(verify_result.get("verification_status", "")):
                        target_result.verification_status = "503_failed"
                        logger.warning("PRICE-COMPARISON: Variante %d 503-Fehler - Daten könnten veraltet sein", result_idx)
                        
        except asyncio.TimeoutError:
            logger.warning("PRICE-COMPARISON: BULK-Verification Timeout nach 6s - einige Preise möglicherweise nicht live-verifiziert")
            # Markiere alle als nicht verifiziert bei Timeout
            for i, result in enumerate(results):
                if not result.live_verified:
                    result.verification_status = "timeout_skip"

    # --- POST-VERIFICATION BUDGET-RECHECK ---
    # Live-Verification kann Preise erhöhen; entferne nachträglich über Budget.
    if budget_limit is not None and results:
        _pre_recheck = len(results)
        results = [r for r in results if r.price <= budget_limit]
        if len(results) < _pre_recheck:
            logger.info(
                "BUDGET-RECHECK: %d Ergebnisse nach Verification über Budget entfernt.",
                _pre_recheck - len(results),
            )
        if not results:
            budget_exceeded = True

    output = PriceComparisonOutput(
        query=product_name,
        locale=locale,
        currency=currency,
        results=results,
        refurbished_tip=refurbished_tip,
        retrieved_at=retrieved_at,
    )

    # Enrich output with EXTREME verification markers - LLM MUST see these
    output_dict = output.model_dump()
    
    # Add variant labels for easy LLM grouping
    for i, entry in enumerate(output_dict.get("results", [])):
        if entry.get("variant"):
            entry["variant_label"] = entry["variant"]
        elif "macbook" in product_name.lower():
            # Auto-detect variant from product_name
            if "air" in entry.get("product_name", "").lower():
                if "15" in entry.get("product_name", ""):
                    entry["variant_label"] = "Air 15 Zoll"
                else:
                    entry["variant_label"] = "Air 13 Zoll"
            elif "pro" in entry.get("product_name", "").lower():
                entry["variant_label"] = "Pro 14 Zoll"
    
    # Add visible markers for live_verified status in the output text for LLM synthesis
    if results and results[0].live_verified:
        verified_price = results[0].live_price or results[0].price
        output_dict["_live_verified_marker"] = "✅ LIVE-VERIFIED"
        output_dict["_verification_note"] = f"Der Preis wurde live auf der Shop-Seite verifiziert: {results[0].price} {results[0].currency}"
        # EXTREME HIGHLIGHTING: Make the verified price impossible to miss
        output_dict["!!! VERIFIED_BEST_PRICE !!!"] = verified_price
        output_dict["!!! VERIFIED_PRICE_ATTENTION !!!"] = f"USE THIS EXACT PRICE: {verified_price} {results[0].currency}"
        output_dict["_priority_instruction"] = f"PRIORITIZE THIS VERIFIED PRICE: {verified_price} {results[0].currency}"
    elif results and results[0].verification_status and "503" in str(results[0].verification_status):
        output_dict["_live_verified_marker"] = "⚠️ VERIFIZIERUNG FEHLGESCHLAGEN (503)"
        output_dict["_verification_note"] = "Der Preis konnte nicht live verifiziert werden - Daten könnten veraltet sein."
        output_dict["!!! VERIFICATION_FAILED_503 !!!"] = True
    
    # --- BUDGET-META: Informiere das LLM über aktives Budget ---
    if budget_limit is not None:
        output_dict["budget_limit"] = budget_limit
        output_dict["budget_exceeded"] = budget_exceeded
        output_dict["_budget_directive"] = (
            f"!!! BUDGET-PFLICHT: Der Nutzer hat ein Maximum von {budget_limit:.0f} {currency} angegeben. "
            f"Erwähne NUR Produkte bis {budget_limit:.0f} {currency}. "
            f"Nenne NIEMALS teurere Alternativen. !!!"
        )

    # Always add structure hint for the LLM
    output_dict["_output_format_hint"] = "Format: - [Variante]: ab [Preis] [Währung] (Quelle: [Name](URL))"
    output_dict["_link_requirement"] = "JEDER PUNKT MUSS EINEN FUNKTIONIERENDEN LINK AM ENDE HABEN"
    
    result_dict = output_dict

    # 💎 SEARCH-COSTS FIX: Berechne und logge Gesamtkosten für Websuchen
    total_search_cost_eur = search_query_count * SEARCH_COST_PER_QUERY_EUR
    logger.info("PRICE-COMPARISON: SEARCH-COSTS - %d Queries × %.2f€ = %.2f€", 
                search_query_count, SEARCH_COST_PER_QUERY_EUR, total_search_cost_eur)
    
    # Füge Search-Costs zum Output hinzu für Sidebar-Anzeige
    output_dict["_search_costs"] = {
        "query_count": search_query_count,
        "cost_per_query_eur": SEARCH_COST_PER_QUERY_EUR,
        "total_search_cost_eur": total_search_cost_eur
    }

    # Cache-Eintrag schreiben (nicht für Finanzdaten)
    if not is_financial:
        _price_cache.set(cache_key, result_dict)

    return ToolResultV1(status="ok", data=result_dict)

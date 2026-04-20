"""
Gemini Provider Constants – Diamond Standard Directives

Zentrale Quelle für alle Link-Direktiven und Rendering-Regeln.
Single Source of Truth für Gemini Websearch Optimization.
"""

# ID-Anchor Protocol Directive
# PRIORITY 1 – MANDATORY. Wird an oberste Stelle des System-Prompts injiziert.
ID_INJECTION_DIRECTIVE = """[PRIORITY 1 – MANDATORY ID-ANCHOR PROTOCOL]

You MUST wrap EVERY product name in [[PRODUCT:name]] format.
You MUST wrap EVERY background topic in [[WIKI:topic]] format.

This is REQUIRED for our link-processing pipeline. Failure to do so will break the UI.

Examples:
- "Der [[PRODUCT:nintendo_switch_2]] kostet 449 Euro."
- "Mehr zur Geschichte: [[WIKI:Nintendo Switch]]"
- "Die [[PRODUCT:rtx_5090]] bietet 32GB VRAM."
- "Infos zum Hersteller: [[WIKI:NVIDIA]]"

Known product IDs: nintendo_switch_2, nintendo_switch_2_mario_kart, playstation_5_slim, playstation_5_digital, playstation_5_pro, xbox_series_x, xbox_series_s, steam_deck, steam_deck_oled, iphone_15, iphone_15_pro, iphone_15_pro_max, samsung_galaxy_s24, samsung_galaxy_s24_ultra, ipad_pro_11, ipad_pro_13, macbook_air_m3, macbook_pro_m3, nintendo_switch_oled, meta_quest_3, rtx_5090, rtx_5080, rtx_5070.

UNKNOWN PRODUCTS: If a product is NOT in the list above, STILL use [[PRODUCT:product_name]] (e.g., [[PRODUCT:rtx_5060]]). The renderer will generate a search link.

NEVER write raw URLs yourself. The system will render all links.
"""

# Universal Deep-Link Directive (für nicht-Listen Queries)
UNIVERSAL_LINK_DIRECTIVE = """CRITICAL UNIVERSAL LINKING DIRECTIVE:
1. You MUST find a dedicated, highly specific source URL from the <context> for EACH fact, item, or entity in your answer.
2. It is STRICTLY FORBIDDEN to use a generic root domain link. The URL must point directly to the specific article, product page, or subpage.
3. If an entity is mentioned in the context, but you cannot find a specific deep-link URL, write "(Keine spezifische Quelle gefunden)" instead.
4. SOURCE-LANGUAGE-FILTER: Prioritize German domains (.de, .at, .ch) over any other domain.
5. ACCURACY OVER COMPLETENESS: A missing link is better than a wrong link.
"""

# Hybrid Linking Directive (für Listen-Queries mit Links erlaubt)
HYBRID_LINK_DIRECTIVE = """CRITICAL HYBRID-LINKING DIRECTIVE:
1. For each item in the list, you MUST try to generate a specific deep-link URL.
2. First, try to find an exact URL in the provided <context>.
3. If no specific URL is found in the context, you are ALLOWED to CONSTRUCT a plausible-looking URL to a major German-language source.
4. If you construct a link, label it as [Kandidat] in the link text.
5. MARKING-REGEL: When creating lists of products, wrap entity names with <b> and </b> tags (e.g., <b>The Rogue Prince of Persia</b>). This is REQUIRED for automatic linking.
"""

# Price Precision Rules (Preisabfragen)
PRICE_PRECISION_DIRECTIVE = """PRICE PRECISION RULE:
1. ONLY state prices that you find EXPLICITLY written with a currency symbol (e.g., '427,90 €') in the <context>.
2. NEVER state a price range (e.g., '414 bis 449 Euro'). Always pick ONLY the LOWEST price and use prefix 'ab'. Example: 'ab 414 Euro'.
3. If no explicit price is found, write 'Aktueller Straßenpreis ist derzeit nicht eindeutig belegbar' instead.
4. STREET PRICE FORMAT: When both standard and bundle editions exist, state cheapest street prices in ONE compact sentence using 'ab'.
5. UVP SEPARATION: Keep UVP in its OWN paragraph. Insert BLANK LINE between UVP and street price paragraphs.
6. NEVER mention refurbished prices or models.
"""

# List Query Detection Tokens
LIST_QUERY_TOKENS = (
    "liste", "list", "top", "ranking", "beste", "alle",
    "neuerscheinungen", "highlights", "mehrere", "welche spiele",
    "welche autos", "spiele", "games", "kostet", "preis"
)

# Product Pattern Regex (für Backward-Compatibility in Renderer)
PRODUCT_PATTERNS = [
    r'Nintendo\s+Switch\s+2',
    r'Nintendo\s+Switch(?![^\w]|$)(?!\s+2)',
    r'PlayStation\s+5\s*(?:Pro|Slim|Digital)?',
    r'PS\s*5\s*(?:Pro|Slim|Digital)?',
    r'Xbox\s+Series\s+[XS]',
    r'Steam\s+Deck(?:\s+OLED)?',
    r'iPhone\s+15\s*(?:Pro\s*Max|Pro|Plus)?',
    r'Galaxy\s+S24\s*(?:Ultra|Plus|\+)?',
    r'iPad\s+Pro\s+(?:11|13)\s*(?:2024)?',
    r'MacBook\s+(?:Pro|Air)\s+(?:M3|2024)?',
    r'Meta\s+Quest\s+3',
    r'RTX\s*50\d0',
    r'GeForce\s+RTX\s*50\d0',
    r'NVIDIA\s+RTX\s*50\d0',
]

# Renderer Security Limits
MAX_LINKS_PER_TURN = 8

# Wikipedia Headers for API Calls
WIKI_HEADERS = {
    "User-Agent": "JanusBot/0.4.2 (https://janus-projekt.dev; contact@janus-projekt.dev) python-httpx/0.27"
}

# Non-Entity Patterns (für Entity-Extraktion)
NON_ENTITY_PATTERNS = (
    r"^(?i)(unverbindlich|günstigste?|straßenpreis|uvp|preis|release|erscheinung|"
    r"fazit|zusammenfassung|übersicht|hinweis|quelle|anmerkung)"
)

# Invalid Entities for Diamond Filter
INVALID_ENTITIES = {
    "uvp", "preis", "straßenpreis", "basis-konsole", "konsole",
    "bundle-edition", "standard-edition", "release-datum", "vorteil",
    "basis-modell", "bundle", "edition", "version", "pack"
}

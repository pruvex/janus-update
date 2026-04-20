import re

_MAX_REPEATED_INVALID_SIGNATURE = 3
_DEFAULT_COMPLETION_TOKENS = 4000

_GERMAN_LOCALIZATION_DIRECTIVE = (
    "LOKALISIERUNG: Du operierst in Deutschland. Antworte standardmäßig auf Deutsch. "
    "Verwende Euro (€) als Standardwährung und metrische Einheiten (Kilometer, Grad Celsius). "
    "Frage den Nutzer NICHT nach Land oder Währung, außer er bittet explizit darum. "
    "Triff stattdessen Annahmen basierend auf dem Standort Deutschland, inklusive lokaler Feiertage, Öffnungszeiten und Steuerlogiken."
)
_SMART_ASSUMPTION_DIRECTIVE = (
    "SMART ASSUMPTIONS: Stelle bei Preis- oder Informationsfragen KEINE Rückfragen zu Land oder Währung, "
    "wenn der Nutzer nichts spezifiziert. Nutze standardmäßig Deutschland und Euro und formuliere deine Antwort als "
    "'Basierend auf dem deutschen Markt kostet [Produkt] derzeit [Preis].' Sei proaktiv statt nachzufragen."
)
_GERMAN_PRICE_RULE = (
    "LOKALISIERUNGS-REGEL: Du operierst für einen Nutzer in Deutschland. Wenn nach Preisen, Kosten oder Währungen gefragt "
    "wird, nutze IMMER Euro (€) und deutsche Marktpreise als Standard. Nenne dem Nutzer den Preis basierend auf diesen "
    "Annahmen und frage NICHT nach Land oder Währung, es sei denn, der Nutzer fragt explizit nach einem anderen Land."
)
_LOCALIZATION_DIRECTIVES = (
    _GERMAN_LOCALIZATION_DIRECTIVE,
    _SMART_ASSUMPTION_DIRECTIVE,
    _GERMAN_PRICE_RULE,
)

_GOOGLE_MAPS_DIR_RE = re.compile(r"https://www\.google\.com/maps/dir/\?api=1[^\s\"'<>)]*", re.IGNORECASE)
_WINDOWS_PDF_PATH_RE = re.compile(r"[A-Za-z]:\\[^\n\r]*?\.pdf", re.IGNORECASE)
_FACT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

_RESEARCH_TOOL_SKILLS = {
    "system.websearch",
    "system.scrape_website",
    "system.wikipedia_summary",
    "system.rss_news",
}

_RESEARCH_SYNTHESIS_RULE = (
    "💎 DIAMOND-STANDARD RECHERCHE-REGEL: Wenn du Daten aus einer Websuche oder anderen Quellen erhältst, "
    "ist VOLLSTÄNDIGKEIT dein oberstes Gebot. Prüfe Snippets kritisch auf Aktualität (Jahreszahlen!) und "
    "entferne SEO-Spam. Beantworte die Nutzerfrage extrem präzise und nenne JEDES gefundene Detail (z. B. jeden Preis, "
    "jedes Release-Datum). Füge IMMER die relevanteste Quelle als Markdown-Link an das Ende deiner Antwort."
)

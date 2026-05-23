import re
from datetime import datetime

from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer
from backend.services.websearch.link_quality import (
    LinkIntent,
    is_low_value_source,
    select_best_source_for_item,
    score_source_for_intent,
)


_SOURCE_LABELS = {
    "spiegel": "SPIEGEL",
    "gamestar": "GameStar",
    "tagesschau": "Tagesschau",
    "zeit": "ZEIT",
    "heise": "Heise",
    "golem": "Golem",
    "dlf": "Deutschlandfunk",
    "sz": "Sueddeutsche Zeitung",
    "handelsblatt": "Handelsblatt",
    "ntv": "n-tv",
    "reuters": "Reuters",
    "bbc": "BBC",
}

_GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "maerz": 3,
    "marz": 3,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}

class RssNewsRenderer(BaseRenderer):
    skill_id = "system.rss_news"

    def render(self, data: dict) -> str:
        source = str(data.get("source") or "unbekannt").strip()
        items = data.get("items") if isinstance(data.get("items"), list) else []

        if items:
            return self._render_news_items(data, items)

        websearch_sources = data.get("websearch_sources")
        if data.get("fallback") == "websearch" and isinstance(websearch_sources, list):
            fallback_items = self._items_from_websearch_text_and_sources(
                str(data.get("websearch_text") or ""),
                websearch_sources,
                str(data.get("original_query") or data.get("query") or ""),
            )
            patched = dict(data)
            patched["items"] = fallback_items
            return self._render_news_items(patched, fallback_items)

        if data.get("fallback") == "websearch":
            text = str(data.get("websearch_text") or "").strip()
            if text:
                return "Kurzlage: RSS lieferte keine passenden Treffer, daher wurde eine Websuche genutzt.\n\n" + text

        headlines = data.get("headlines") if isinstance(data.get("headlines"), list) else []
        count = data.get("count")
        if not headlines:
            return f"Ich konnte aktuell keine Schlagzeilen von {source} aufbereiten."

        lines = [f"**Aktuelle Schlagzeilen von {source}**", ""]
        for idx, headline in enumerate(headlines, start=1):
            text = str(headline or "Ohne Titel").strip() or "Ohne Titel"
            lines.append(f"{idx}. {text}")
        if isinstance(count, int):
            lines.append("")
            lines.append(f"- **Anzahl:** {count}")
        return "\n".join(lines)

    def _render_news_items(self, data: dict, items: list) -> str:
        query = str(data.get("query") or "").strip()
        used_websearch = data.get("fallback") == "websearch"
        if query:
            descriptor = "belegte Meldungen" if used_websearch else "kuratierte Meldungen"
            lines = [f"Kurzlage: Zu {query} liegen aktuell {descriptor} vor.", ""]
        else:
            lines = ["Kurzlage: Aktuelle Meldungen aus kuratierten RSS-Feeds.", ""]

        render_items = self._filter_current_news_items(data, items)
        if used_websearch and not render_items:
            return (
                f"Kurzlage: Zu {query or 'der Anfrage'} konnte ich aktuell keine sauber belegten Meldungen "
                "mit konkreter Detailquelle aufbereiten.\n\n"
                "Einordnung:\n"
                "RSS lieferte keine passenden Treffer; die Websuche lieferte keine ausreichend belastbaren Detailquellen."
            )

        for idx, item in enumerate(render_items[:5], start=1):
            title = str(item.get("title") or "Ohne Titel").strip() or "Ohne Titel"
            date = str(item.get("date") or "").strip()
            summary = str(item.get("summary") or "").strip() or "Kurzmeldung ohne Zusammenfassung."
            title, summary = self._normalize_title_summary(title, summary)
            source_key = str(item.get("source") or "").strip().lower()
            source_label = str(item.get("source_label") or _SOURCE_LABELS.get(source_key) or source_key or "Quelle")
            url = str(item.get("url") or "").strip()

            heading = f"{idx}. {title}"
            if date:
                heading += f" ({date})"
            lines.append(heading)
            lines.append(summary)
            if url and not self._is_low_value_source(url):
                lines.append(f"Quelle: {source_label}. [Link]({url})")
            else:
                lines.append(f"Quelle: {source_label}. Link online leider nicht verfuegbar.")
            lines.append("")

        lines.append("Einordnung:")
        if used_websearch:
            lines.append("RSS lieferte keine passenden Treffer; diese Kurzlage nutzt belegte Webquellen als Fallback.")
        else:
            lines.append("RSS-basierte Kurzlage aus kuratierten Quellen; bei fehlender Abdeckung nutzt Janus die Websuche als Fallback.")
        return "\n".join(lines).rstrip()

    def _websearch_news_item_has_evidence(self, item: dict) -> bool:
        url = str((item or {}).get("url") or "").strip()
        return bool(url and not self._is_low_value_source(url))

    def _items_from_websearch_text_and_sources(self, text: str, sources: list, query_context: str = "") -> list:
        source_rows = [source for source in sources if isinstance(source, dict)]
        items = []
        primary_text = re.split(r"(?im)^\s*\[Global Research\]\s*$", str(text or ""), maxsplit=1)[0]
        segments = self._numbered_news_segments(primary_text)
        for idx, raw_body in enumerate(segments, start=1):
            body, label = self._extract_source_label(raw_body)
            title, summary = self._split_websearch_news_body(body)
            if self._is_current_news_context(f"{query_context} {text}") and self._news_item_is_stale(f"{title} {summary}"):
                continue
            url = self._url_for_item(label, title, summary, idx, source_rows)
            items.append(
                {
                    "title": title,
                    "summary": summary or "Kurzmeldung aus der Websuche; Details stehen in der verlinkten Quelle.",
                    "url": url,
                    "source": "websearch",
                    "source_label": label or self._label_from_url(url),
                    "date": "",
                }
            )
            if len(items) >= 5:
                break
        if items:
            return items
        return self._items_from_websearch_sources(source_rows)

    def _numbered_news_segments(self, text: str) -> list:
        starts = list(re.finditer(r"(?m)^\s*\d+[.)]\s*", str(text or "")))
        segments = []
        for pos, match in enumerate(starts):
            start = match.end()
            end = starts[pos + 1].start() if pos + 1 < len(starts) else len(text)
            segment = re.sub(r"\s+", " ", text[start:end]).strip(" .")
            if segment:
                segments.append(segment)
        return segments

    def _extract_source_label(self, body: str) -> tuple[str, str]:
        clean = re.sub(r"\s+", " ", str(body or "")).strip(" .")
        label = ""
        source_match = re.search(r"\(Quelle:\s*([^)]+)\)", clean, flags=re.IGNORECASE)
        if not source_match:
            source_match = re.search(
                r"\bQuelle:\s*([^.\n]+(?:\.(?:com|de|net|org|co\.uk|tv))?)\.?",
                clean,
                flags=re.IGNORECASE,
            )
        if source_match:
            label = re.sub(r"\s+", " ", source_match.group(1)).strip(" .)")
            clean = re.sub(r"\s*\(Quelle:\s*[^)]+\)\.?", "", clean, flags=re.IGNORECASE).strip(" .")
            clean = re.sub(r"\s*\bQuelle:\s*[^.\n]+\.?", "", clean, flags=re.IGNORECASE).strip(" .")
        return clean, label

    def _filter_current_news_items(self, data: dict, items: list) -> list:
        query = str(data.get("query") or "")
        query_context = f"{query} {data.get('original_query') or ''}"
        if not data.get("is_current_news") and not self._is_current_news_context(query_context):
            return items
        filtered = []
        for item in items:
            if not isinstance(item, dict):
                continue
            text = " ".join(str(item.get(key) or "") for key in ("title", "summary", "date"))
            if self._news_item_is_stale(text):
                continue
            filtered.append(item)
        return filtered or items

    def _is_current_news_context(self, value: str) -> bool:
        lowered = str(value or "").casefold()
        return any(
            marker in lowered
            for marker in (
                "aktuell",
                "aktuelle",
                "neuigkeiten",
                "news",
                "latest",
                "neues",
                "heute",
                "meldungen",
            )
        )

    def _news_item_is_stale(self, value: str, max_age_days: int = 45) -> bool:
        parsed = self._extract_news_date(value)
        if not parsed:
            return False
        now = datetime.now()
        age_days = (now.date() - parsed.date()).days
        return age_days > max_age_days

    def _extract_news_date(self, value: str) -> datetime | None:
        text = str(value or "")
        numeric = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(20\d{2})\b", text)
        if numeric:
            try:
                return datetime(int(numeric.group(3)), int(numeric.group(2)), int(numeric.group(1)))
            except ValueError:
                return None
        month_match = re.search(
            r"\b(\d{1,2})\.\s*([A-Za-zÄÖÜäöüß]+)\s+(20\d{2})\b",
            text,
            flags=re.IGNORECASE,
        )
        if month_match:
            month_key = (
                month_match.group(2)
                .casefold()
                .replace("ä", "ae")
                .replace("ö", "oe")
                .replace("ü", "ue")
                .replace("ß", "ss")
            )
            month = _GERMAN_MONTHS.get(month_key) or _GERMAN_MONTHS.get(month_match.group(2).casefold())
            if not month:
                return None
            try:
                return datetime(int(month_match.group(3)), month, int(month_match.group(1)))
            except ValueError:
                return None
        return None

    def _split_websearch_news_body(self, body: str) -> tuple[str, str]:
        clean = re.sub(r"\s+", " ", str(body or "")).strip(" .")
        if not clean:
            return "Meldung", ""
        colon_match = re.match(r"^(.{3,90}?):\s+(.+)$", clean)
        if colon_match:
            return self._normalize_title_summary(colon_match.group(1).strip(), colon_match.group(2).strip())

        clause_match = re.match(
            r"^(.{12,95}?)(?:,\s+|,\s*wobei\b|\s+und\s+|\.?\s*$)",
            clean,
        )
        title = clause_match.group(1).strip(" ,.;") if clause_match else clean[:90].strip(" ,.;")
        if len(title) > 90:
            title = title[:87].rstrip(" ,.;") + "..."
        return self._normalize_title_summary(title or "Meldung", clean)

    def _normalize_title_summary(self, title: str, summary: str) -> tuple[str, str]:
        clean_title = re.sub(r"\s+", " ", str(title or "").replace("**", "")).strip(" .")
        clean_summary = re.sub(r"\s+", " ", str(summary or "").replace("**", "")).strip(" .")
        clean_summary = re.sub(r"\s*\(Quelle:\s*[^)]+\)\.?", "", clean_summary, flags=re.IGNORECASE).strip(" .")
        clean_summary = re.sub(r"\s*\bQuelle:\s*[^.\n]+\.?", "", clean_summary, flags=re.IGNORECASE).strip(" .")

        colon_match = re.match(r"^(.{3,90}?):\s+(.+)$", clean_title)
        if colon_match:
            prefix = colon_match.group(1).strip(" .")
            title_tail = colon_match.group(2).strip(" .")
            clean_title = prefix
            if not clean_summary:
                clean_summary = title_tail

        if clean_title and clean_summary:
            duplicate_patterns = [
                rf"^{re.escape(clean_title)}\s*:\s*",
                rf"^{re.escape(clean_title)}\s+",
            ]
            for pattern in duplicate_patterns:
                stripped = re.sub(pattern, "", clean_summary, count=1, flags=re.IGNORECASE).strip(" .")
                if stripped != clean_summary:
                    clean_summary = stripped
                    break
            embedded_duplicate = re.search(
                rf"\b{re.escape(clean_title)}\s*:\s*",
                clean_summary,
                flags=re.IGNORECASE,
            )
            if embedded_duplicate:
                clean_summary = clean_summary[embedded_duplicate.end():].strip(" .")

        if clean_title and clean_summary.casefold().startswith(clean_title.casefold()):
            clean_summary = clean_summary[len(clean_title):].lstrip(" :.-")

        return clean_title or "Meldung", clean_summary or "Kurzmeldung ohne Zusammenfassung."

    def _items_from_websearch_sources(self, sources: list) -> list:
        items = []
        for source in sources[:5]:
            if not isinstance(source, dict):
                continue
            url = str(source.get("url") or source.get("source_url") or "").strip()
            if not url:
                continue
            title = str(source.get("title") or source.get("name") or "Meldung").strip()
            summary = str(
                source.get("snippet") or source.get("description") or source.get("text") or ""
            ).strip()
            label = str(source.get("source") or source.get("domain") or "").strip() or self._label_from_url(url)
            items.append(
                {
                    "title": title,
                    "summary": summary or "Kurzmeldung aus der Websuche; Details stehen in der verlinkten Quelle.",
                    "url": url,
                    "source": "websearch",
                    "source_label": label,
                    "date": str(source.get("date") or "").strip(),
                }
            )
        return items

    def _url_for_item(self, label: str, title: str, summary: str, index: int, sources: list) -> str:
        best_url, _quality = select_best_source_for_item(
            [source for source in sources if isinstance(source, dict)],
            intent=LinkIntent.NEWS,
            title=title,
            summary=summary,
            label=label,
            target_index=index,
        )
        return best_url

    def _score_source_for_item(self, source: dict, label: str, title: str, summary: str, index: int) -> int:
        quality = score_source_for_intent(
            source,
            intent=LinkIntent.NEWS,
            title=title,
            summary=summary,
            label=label,
            target_index=index,
        )
        return quality.score

    def _is_low_value_source(self, value: str) -> bool:
        return is_low_value_source(value, LinkIntent.NEWS)

    def _label_from_url(self, url: str) -> str:
        host = str(url or "").replace("https://", "").replace("http://", "").split("/")[0]
        host = host.removeprefix("www.")
        label = host.split(".")[0] if host else "Web"
        return label[:1].upper() + label[1:]


register_renderer(RssNewsRenderer())

"""Deterministic templates for provider-agnostic websearch answers."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlparse


@dataclass(frozen=True)
class ReleaseListItem:
    index: str
    title: str
    description: str
    price_line: str
    source_line: str


class WebSearchTemplateEngine:
    """Route websearch payloads into deterministic chat templates.

    The provider may be OpenAI, Gemini or a fallback search provider. This
    engine owns the chat-facing shape, so provider quirks never leak into UI.
    """

    RELEASE_PRODUCT_MARKERS = (
        "switch",
        "nintendo",
        "playstation",
        "xbox",
        "steam",
        "spiele",
        "games",
        "buch",
        "bücher",
        "film",
        "serie",
    )
    RELEASE_MARKERS = (
        "release",
        "releases",
        "erscheinen",
        "erscheint",
        "neuerschein",
        "kommende",
        "naechsten monat",
        "nächsten monat",
        "next month",
        "upcoming",
    )

    @classmethod
    def render(cls, data: Dict[str, Any], text: str, intent_text: str) -> Optional[str]:
        if cls.is_release_lookup(intent_text):
            return cls.render_release_list(text, data=data)
        return None

    @classmethod
    def is_release_lookup(cls, text: str) -> bool:
        lowered = str(text or "").lower()
        has_product = any(token in lowered for token in cls.RELEASE_PRODUCT_MARKERS)
        has_release = any(token in lowered for token in cls.RELEASE_MARKERS)
        return has_product and has_release

    @staticmethod
    def _ensure_sentence(text: str) -> str:
        value = str(text or "").strip()
        if not value:
            return value
        return value if value[-1] in ".!?" else value + "."

    @staticmethod
    def _repair_release_sentence_fragment(text: str) -> str:
        value = str(text or "").strip()
        if not value:
            return value
        if re.match(r"^(?:die\s+)?Nintendo\s+Switch\s+2\b", value, flags=re.IGNORECASE):
            return f"Erscheint für {value[0].lower()}{value[1:]}"
        if re.match(r"^ver(?:Ã¶|oe|ö)?ffentlicht\s+und\b", value, flags=re.IGNORECASE):
            return f"Wird {value[0].lower()}{value[1:]}"
        if re.match(r"^(atmosphärisches|atmosphÃ¤risches)\s+Horror\b", value, flags=re.IGNORECASE):
            return f"Ein {value[0].lower()}{value[1:]}"
        return value

    @staticmethod
    def _date_pattern() -> str:
        return r"\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+\s+\d{4}"

    @staticmethod
    def _normalize_broken_release_markup(text: str) -> str:
        value = str(text or "")
        if not value:
            return value
        value = re.sub(r"\[\[.*?\]\]", "", value)
        value = re.sub(r"\n{2,}\[Global Research\][\s\S]*$", "", value, flags=re.IGNORECASE)
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
            r"\(Quelle(?!:)\s*\n\s*([^)]+)\)\.?",
            lambda m: f"(Quelle: {m.group(1).strip()}).",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"\(Quelle(?!:)\s+([^)]+)\)\.?",
            lambda m: f"(Quelle: {m.group(1).strip()}).",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"\s*\(Quelle:\s*([^)]+)\)\.?",
            lambda m: f"\nQuelle: {m.group(1).strip()}.",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"(?m)^(\d+\.\s*)\*\*([^\n]*?)\s*$",
            lambda m: m.group(0) if "**" in m.group(2) else f"{m.group(1)}{m.group(2).strip()}",
            value,
        )
        value = re.sub(
            r"(?m)^(\d+\.\s*)\*\*([^\n]*\(Quelle:\s*[^)]+\)\.?)\s*$",
            lambda m: f"{m.group(1)}{m.group(2).strip()}",
            value,
        )
        value = re.sub(r"(?m)^(\d+)\)\s+", r"\1. ", value)
        return re.sub(r"\n{3,}", "\n\n", value).strip()

    @classmethod
    def _extract_price_line(cls, text: str) -> tuple[str, str]:
        value = str(text or "")
        value = re.sub(
            r"\s*Preis:\s*online\s+leider\s+nicht\s+verf(?:ü|ue|Ã¼)gbar\.?",
            "",
            value,
            flags=re.IGNORECASE,
        ).strip()
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
    def _derive_title_and_description(cls, title: str, body: str) -> tuple[str, str]:
        clean_title = re.sub(r"\s+", " ", str(title or "")).strip(" :*")
        clean_body = re.sub(r"\s+", " ", str(body or "")).strip()
        clean_body = re.sub(r"^[\u2013\u2014-]\s*", "", clean_body).strip()
        clean_body = re.sub(r"^Release\s+am\s+", "Erscheint am ", clean_body, flags=re.IGNORECASE)
        clean_body = re.sub(r"\(Kontext\s+", "(", clean_body, flags=re.IGNORECASE)
        date_rx = cls._date_pattern()

        inline_dash = re.match(rf"^(.+?\([^)]*{date_rx}[^)]*\))\s+(?:[\u2013\u2014-]|\?)\s+(.+)$", clean_title)
        if inline_dash:
            clean_title = inline_dash.group(1).strip()
            clean_body = " ".join(part for part in (inline_dash.group(2).strip(), clean_body) if part).strip()

        inline_dash_date = re.match(rf"^(.+?)\s+(?:[\u2013\u2014-]|\?)\s+({date_rx})\s*:\s*(.+)$", clean_title)
        if inline_dash_date and not clean_body:
            clean_title = f"{inline_dash_date.group(1).strip()} ({inline_dash_date.group(2).strip()})"
            clean_body = inline_dash_date.group(3).strip()

        title_dash_date = re.match(rf"^(.+?)\s+(?:[\u2013\u2014-]|\?)\s+({date_rx})$", clean_title)
        if title_dash_date and clean_body:
            clean_title = f"{title_dash_date.group(1).strip()} ({title_dash_date.group(2).strip()})"

        title_date = re.search(rf"\(({date_rx})\)", clean_title)
        duplicate_body_date = re.match(rf"^(.+?)\s+\(({date_rx})\)\s+(?:[\u2013\u2014-]|\?)\s+(.+)$", clean_body)
        if title_date and duplicate_body_date:
            subtitle = duplicate_body_date.group(1).strip(" :")
            body_date = duplicate_body_date.group(2).strip()
            rest = duplicate_body_date.group(3).strip()
            base_title = re.sub(rf"\s*\({date_rx}\)\s*$", "", clean_title).strip()
            if body_date == title_date.group(1) and subtitle.lower() not in base_title.lower():
                return f"{base_title}: {subtitle} ({body_date})", rest

        body_subtitle_date = re.match(rf"^(.+?)\s+\(({date_rx})\)\s+(?:[\u2013\u2014-]|\?)\s+(.+)$", clean_body)
        if body_subtitle_date and "(" not in clean_title:
            subtitle = body_subtitle_date.group(1).strip(" :")
            date = body_subtitle_date.group(2).strip()
            rest = body_subtitle_date.group(3).strip()
            if subtitle.lower() not in clean_title.lower():
                return f"{clean_title}: {subtitle} ({date})", rest

        subtitle_colon = re.match(r"^([^:]{2,80}):\s*(.+)$", clean_body)
        if subtitle_colon and "(" not in clean_title:
            subtitle = subtitle_colon.group(1).strip(" :")
            clean_title = f"{clean_title}: {subtitle}"
            clean_body = subtitle_colon.group(2).strip()

        subtitle_match = re.match(
            r"^([A-ZÄÖÜ][\wÄÖÜäöüß!'-]+(?:\s+[A-ZÄÖÜ][\wÄÖÜäöüß!'-]+){0,4})\s+"
            r"(?:startet|erscheint|kommt|wird)\s+am\s+"
            rf"({date_rx})\s+(?:als|für|mit|und|,)?\s*(.*)$",
            clean_body,
            flags=re.IGNORECASE,
        )
        if subtitle_match and "(" not in clean_title:
            subtitle = subtitle_match.group(1).strip(" :")
            date = subtitle_match.group(2).strip()
            rest = subtitle_match.group(3).strip(" ,")
            return f"{clean_title}: {subtitle} ({date})", rest

        patterns = (
            rf"^(.+?)\s+(?:erscheint|erscheinen|wird|werden)\s+am\s+({date_rx})\s+(?:als|für|mit|und|,)?\s*(.*)$",
            rf"^(.+?)\s+(?:startet|kommt)\s+am\s+({date_rx})\s+(?:als|für|mit|und|,)?\s*(.*)$",
        )
        for pattern in patterns:
            match = re.match(pattern, clean_title, flags=re.IGNORECASE)
            if not match:
                continue
            name = match.group(1).strip(" :")
            date = match.group(2).strip()
            tail = match.group(3).strip(" ,")
            sentence = tail or clean_body
            if tail and re.match(r"^Horror\b", tail, flags=re.IGNORECASE):
                sentence = f"Ein {tail}"
                return f"{name} ({date})", sentence
            if tail and re.match(
                r"^(Fortsetzung|Fußball|Fussball|Simulation|RPG|Rollenspiel|Action|Adventure)\b",
                tail,
                flags=re.IGNORECASE,
            ):
                sentence = f"Eine {tail}"
            return f"{name} ({date})", sentence

        embedded_patterns = (
            (rf"\s+erscheint\s+am\s+({date_rx})\s+", " erscheint "),
            (rf"^Erscheint\s+am\s+({date_rx}),?\s*", ""),
            (rf"\s+wird\s+am\s+({date_rx})\s+ver(?:ö|oe|Ã¶)?ffentlicht", " wird veröffentlicht"),
            (rf"\s+erscheint\s+am\s+({date_rx})\.", " erscheint."),
            (rf",?\s+f(?:ür|Ã¼r|ue|ÃƒÂ¼r|ÃƒÆ’Ã‚Â¼r)\s+den\s+({date_rx})\s+in\s+der\s+[^.]*Release-Liste\s+gef(?:ührt|Ã¼hrt|uehrt|ÃƒÂ¼hrt|ÃƒÆ’Ã‚Â¼hrt)\.?", "."),
            (rf"\s+f(?:ü|ue|Ã¼)r\s+den\s+({date_rx})\s+", " "),
            (rf",?\s+geplant\s+am\s+({date_rx})\.?", "."),
            (rf",?\s+f(?:ür|Ã¼|ue|ÃƒÂ¼)r\s+den\s+({date_rx})\s+in\s+der\s+[^.]*Release-Liste\s+gef(?:ühr|Ã¼hr|uehr|ÃƒÂ¼hr)t\.?", "."),
            (rf"\s+am\s+({date_rx})\s+erscheinende\s+", " "),
            (rf"\s+am\s+({date_rx})\.?", "."),
        )
        for pattern, replacement in embedded_patterns:
            match = re.search(pattern, clean_body, flags=re.IGNORECASE)
            if not match:
                continue
            date = match.group(1).strip()
            cleaned_body = re.sub(pattern, replacement, clean_body, count=1, flags=re.IGNORECASE)
            cleaned_body = re.sub(r"\s{2,}", " ", cleaned_body).strip(" ,")
            return f"{clean_title} ({date})", cleaned_body

        return clean_title, clean_body

    @classmethod
    def _strip_redundant_release_calendar_phrases(cls, text: str) -> str:
        value = str(text or "").strip()
        if not value:
            return value
        patterns = (
            r";?\s*als\s+Terminspiel\s+im\s+Juni-Kalender\s+von\s+[^.]+\.?",
            r";?\s*ebenfalls\s+mit\s+Datumseintrag\s+im\s+Juni\s+\d{4}-Release-Überblick\.?",
            r";?\s*[^.;]*führt\s+ihn\s+als\s+Juni-Release\s+mit\s+Datum\s+\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+\.?",
            r";?\s*[^.;]*nennt\s+den\s+\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+\s+als\s+konkretes\s+Erscheinungsdatum\.?",
            r";?\s*[^.;]*nennt\s+den\s+Release\s+konkret\s+für\s+den\s+\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+\.?",
            r";?\s*steht\s+bei\s+[^.;]+ebenfalls\s+für\s+den\s+\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+\s+im\s+Juni-Kalender\.?",
            r",?\s+das\s+laut\s+[^.;]+\s+ebenfalls\s+am\s+\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+\s+für\s+[^.;]+(?:ankommt|erscheint)\.?",
            r";?\s*erscheint\s+am\s+\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+\.?",
            r";?\s*[^.;]*ebenfalls\s+am\s+\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+\s+für\s+[^.;]+(?:ankommt|erscheint)\.?",
            r";?\s*[^.;]*laut\s+[^.;]+\s+ebenfalls\s+am\s+\d{1,2}\.\s+[A-Za-zÄÖÜäöüß]+[^.]*\.?",
        )
        for pattern in patterns:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE).strip()
        value = re.sub(
            r"\s*Zusätzlich\s+\([^)]*\):[\s\S]*$",
            "",
            value,
            flags=re.IGNORECASE,
        ).strip()
        return value.strip(" ;,")

    @staticmethod
    def _extract_source(body: str) -> tuple[str, str]:
        value = str(body or "")
        source_match = re.search(r"\(Quelle:\s*([^)]+)\)\.?", value, flags=re.IGNORECASE)
        if source_match:
            source = source_match.group(1).strip()
            cleaned = re.sub(r"\s*\(Quelle:\s*([^)]+)\)\.?", "", value, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r"\s*\(([a-z0-9-]+\.(?:com|de|net|org|co\.uk|tv))\)\.?", "", cleaned, flags=re.IGNORECASE).strip()
            return source, cleaned
        source_match = re.search(r"\bQuelle:\s*([^.\n]+(?:\.(?:com|de|net|org|co\.uk|tv))?)\.?", value, flags=re.IGNORECASE)
        if source_match:
            source = source_match.group(1).strip()
            cleaned = re.sub(r"\s*\bQuelle:\s*([^.\n]+(?:\.(?:com|de|net|org|co\.uk|tv))?)\.?", "", value, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r"\s*\(([a-z0-9-]+\.(?:com|de|net|org|co\.uk|tv))\)\.?", "", cleaned, flags=re.IGNORECASE).strip()
            return source, cleaned
        return "", value

    @staticmethod
    def _normalize_source_label(label: str) -> str:
        value = re.sub(r"\s+", " ", str(label or "")).strip().lower()
        value = re.sub(r"^www\.", "", value)
        value = re.sub(r"\.(com|de|net|org|co\.uk|tv)$", "", value)
        return value

    @staticmethod
    def _detail_tokenize(value: str) -> List[str]:
        normalized = unquote(str(value or "")).lower()
        normalized = re.sub(r"\([^)]*\)", " ", normalized)
        tokens = re.findall(r"[a-z0-9äöüß]+", normalized)
        stopwords = {
            "the",
            "and",
            "for",
            "with",
            "switch",
            "nintendo",
            "playstation",
            "xbox",
            "juni",
            "june",
            "2026",
            "game",
            "games",
            "spiel",
            "spiele",
        }
        return [token for token in tokens if len(token) > 2 and token not in stopwords]

    @classmethod
    def _source_candidate_text(cls, item: Dict[str, Any], url: str) -> str:
        parts = [
            item.get("title"),
            item.get("name"),
            item.get("source"),
            item.get("domain"),
            item.get("snippet"),
            item.get("description"),
            item.get("text"),
            url,
        ]
        try:
            parsed = urlparse(url)
            parts.extend([parsed.netloc, parsed.path])
        except Exception:
            pass
        return unquote(" ".join(str(part or "") for part in parts)).lower()

    @classmethod
    def _source_candidate_label(cls, item: Dict[str, Any], url: str) -> str:
        for key in ("source", "domain", "title", "name"):
            label = str(item.get(key) or "").strip()
            if label:
                return label
        try:
            return urlparse(url).netloc.replace("www.", "") or "Quelle"
        except Exception:
            return "Quelle"

    @staticmethod
    def _looks_like_overview_source(text: str) -> bool:
        return bool(
            re.search(
                r"\b(upcoming|release(?:s)?|erschein(?:t|en|ungen)?|calendar|kalender|list|liste|"
                r"june|juni|next-month|naechsten-monat|nächsten-monat|all-games|new-games)\b",
                text,
                flags=re.IGNORECASE,
            )
        )

    @classmethod
    def _best_detail_source_url(cls, item_title: str, candidates: List[Dict[str, str]]) -> str:
        title_without_date = re.sub(r"\([^)]*\)", " ", str(item_title or ""))
        title_tokens = cls._detail_tokenize(title_without_date)
        if not title_tokens:
            return ""
        title_phrase = " ".join(title_tokens)
        best_url = ""
        best_score = 0

        for candidate in candidates:
            url = str(candidate.get("url") or "").strip()
            search_text = str(candidate.get("search_text") or "").lower()
            if not url or not search_text:
                continue
            matched_tokens = [token for token in title_tokens if token in search_text]
            if len(title_tokens) >= 3 and len(matched_tokens) < 2:
                continue
            if len(title_tokens) <= 2 and len(matched_tokens) < len(title_tokens):
                continue

            score = len(matched_tokens) * 10
            compact_text = re.sub(r"[^a-z0-9äöüß]+", " ", search_text)
            if title_phrase and title_phrase in compact_text:
                score += 35
            try:
                path = unquote(urlparse(url).path).lower()
            except Exception:
                path = url.lower()
            if all(token in path for token in matched_tokens[: max(2, min(3, len(matched_tokens)))]):
                score += 20
            if cls._looks_like_overview_source(search_text):
                score -= 18
            if re.search(r"\b(nintendo|playstation|xbox|steam|square-enix|ubisoft|ea\.com|konami)\b", search_text):
                score += 8

            if score > best_score:
                best_score = score
                best_url = url

        return best_url if best_score >= 20 else ""

    @classmethod
    def _build_source_links(cls, data: Dict[str, Any]) -> tuple[Dict[str, str], List[str], List[Dict[str, str]]]:
        mapping: Dict[str, str] = {}
        ordered_urls: List[str] = []
        detail_candidates: List[Dict[str, str]] = []
        candidates: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            sources = data.get("sources")
            if isinstance(sources, list):
                candidates.extend([item for item in sources if isinstance(item, dict)])
            items = data.get("items")
            if isinstance(items, list):
                candidates.extend([item for item in items if isinstance(item, dict)])

        for item in candidates:
            url = str(item.get("url") or item.get("source_url") or "").strip()
            if not url:
                continue
            if url not in ordered_urls:
                ordered_urls.append(url)
            detail_candidates.append(
                {
                    "url": url,
                    "label": cls._source_candidate_label(item, url),
                    "search_text": cls._source_candidate_text(item, url),
                }
            )
            labels = [
                item.get("title"),
                item.get("name"),
                item.get("source"),
                item.get("domain"),
            ]
            for raw_label in labels:
                label = str(raw_label or "").strip()
                if not label:
                    continue
                normalized = cls._normalize_source_label(label)
                if normalized and normalized not in mapping:
                    mapping[normalized] = url
                domain_match = re.search(r"\b([a-z0-9-]+\.(?:com|de|net|org|co\.uk|tv))\b", label, flags=re.IGNORECASE)
                if domain_match:
                    domain_label = cls._normalize_source_label(domain_match.group(1))
                    if domain_label and domain_label not in mapping:
                        mapping[domain_label] = url
        return mapping, ordered_urls, detail_candidates

    @classmethod
    def _build_source_url_map(cls, data: Dict[str, Any]) -> Dict[str, str]:
        mapping, _, _ = cls._build_source_links(data)
        return mapping

    @classmethod
    def _source_line(
        cls,
        source: str,
        source_url_map: Dict[str, str],
        fallback_url: str = "",
        detail_url: str = "",
    ) -> str:
        label = str(source or "").strip()
        if not label:
            url = detail_url or fallback_url
            if url:
                return f"Quelle: nicht eindeutig verfügbar. [Link]({url})"
            return "Quelle: nicht eindeutig verfügbar."
        normalized = cls._normalize_source_label(label)
        url = detail_url or source_url_map.get(normalized, "")
        if not url:
            for known_label, known_url in source_url_map.items():
                if normalized and (normalized in known_label or known_label in normalized):
                    url = known_url
                    break
        if not url:
            url = fallback_url
        if url:
            return f"Quelle: {label}. [Link]({url})"
        return f"Quelle: {label}."

    @classmethod
    def _parse_release_items(cls, text: str, data: Optional[Dict[str, Any]] = None) -> List[ReleaseListItem]:
        value = cls._normalize_broken_release_markup(text)
        source_url_map, ordered_source_urls, detail_candidates = cls._build_source_links(data or {})
        entry_re = re.compile(
            r"(?ms)^(\d+)\.\s*"
            r"(?:"
            r"\*\*(.+?)(?::)?\*\*:?\s*|"
            r"\*\*(.+?)(?=\s+\(Quelle:|\s+Quelle:|\n|$)|"
            r"([^:\n]+):\s*|"
            r"([^:\n]+(?:\([^)]*\))?)(?=\s+\(Quelle:|\s+Quelle:|\n|$)|"
            r"(.+?\([^)]*\)):\s*"
            r")"
            r"(.*?)(?=^\d+\.|\Z)"
        )
        items: List[ReleaseListItem] = []
        for match in entry_re.finditer(value):
            number = match.group(1).strip()
            title = re.sub(
                r"\s+",
                " ",
                match.group(2) or match.group(3) or match.group(4) or match.group(5) or match.group(6) or "",
            ).strip(" :*")
            body = re.sub(r"\s+", " ", match.group(7)).strip()
            body = re.sub(r"^\*+\s*", "", body).strip()
            source, title = cls._extract_source(title)
            body_source, body = cls._extract_source(body)
            if not source:
                source = body_source
            if not body:
                split_match = re.match(r"^(.+?)\s+(?:[\u2013\u2014-]|\?)\s+(Release\s+am\s+.+)$", title, flags=re.IGNORECASE)
                if split_match:
                    title = split_match.group(1).strip()
                    body = split_match.group(2).strip()

            leading_date = re.match(r"^\(([^)]+)\):?\s*(.*)$", body)
            if leading_date and "(" not in title:
                title = f"{title} ({leading_date.group(1).strip()})"
                body = leading_date.group(2).strip()

            title, body = cls._derive_title_and_description(title, body)
            price_line, body = cls._extract_price_line(body)
            body = cls._strip_redundant_release_calendar_phrases(body)
            description = cls._ensure_sentence(cls._repair_release_sentence_fragment(body))
            fallback_url = ""
            try:
                source_position = int(number) - 1
            except ValueError:
                source_position = -1
            if 0 <= source_position < len(ordered_source_urls):
                fallback_url = ordered_source_urls[source_position]
            elif len(ordered_source_urls) == 1:
                fallback_url = ordered_source_urls[0]
            detail_url = cls._best_detail_source_url(title, detail_candidates)
            source_line = cls._source_line(source, source_url_map, fallback_url, detail_url)
            items.append(
                ReleaseListItem(
                    index=number,
                    title=title,
                    description=description,
                    price_line=price_line,
                    source_line=source_line,
                )
            )
        return items

    @classmethod
    def render_release_list(cls, text: str, data: Optional[Dict[str, Any]] = None) -> str:
        value = cls._normalize_broken_release_markup(text)
        items = cls._parse_release_items(value, data=data)
        if not items:
            return value
        first_match = re.search(r"(?m)^\d+\.", value)
        prefix = value[: first_match.start()].strip() if first_match else ""
        blocks: List[str] = [prefix] if prefix else []
        for item in items:
            blocks.append(
                "\n".join(
                    [
                        f"{item.index}. **{item.title}**",
                        item.description,
                        item.price_line,
                        item.source_line,
                    ]
                )
            )
        return "\n\n".join(block for block in blocks if block).strip()

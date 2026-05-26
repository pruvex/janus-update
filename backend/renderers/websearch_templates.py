"""Deterministic templates for provider-agnostic websearch answers."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlparse

from backend.services.websearch.query_bias import normalize_source_url


@dataclass(frozen=True)
class ReleaseListItem:
    index: str
    title: str
    description: str
    price_line: str
    source_line: str


@dataclass(frozen=True)
class RankingListItem:
    index: str
    title: str
    description: str
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
        "album",
        "alben",
        "rockalbum",
        "rockalben",
        "musik",
        "ep",
        "single",
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
    RANKING_MARKERS = (
        "top",
        "topliste",
        "ranking",
        "rangliste",
        "beste",
        "besten",
        "beruehmteste",
        "berühmteste",
        "bekannteste",
        "beliebteste",
        "beliebtesten",
        "wichtigste",
        "groesste",
        "größte",
        "fuehrende",
        "führende",
    )
    RANKING_INTRO_SOURCE_PREFIX = "Quelle der Liste"

    @classmethod
    def render(cls, data: Dict[str, Any], text: str, intent_text: str) -> Optional[str]:
        if cls.is_release_lookup(intent_text):
            return cls.render_release_list(text, data=data)
        if cls.is_ranking_lookup(intent_text):
            return cls.render_ranking_list(text, data=data, intent_text=intent_text)
        return None

    @classmethod
    def is_release_lookup(cls, text: str) -> bool:
        lowered = str(text or "").lower()
        has_product = any(token in lowered for token in cls.RELEASE_PRODUCT_MARKERS)
        has_release = any(token in lowered for token in cls.RELEASE_MARKERS)
        return has_product and has_release

    @classmethod
    def is_ranking_lookup(cls, text: str) -> bool:
        lowered = str(text or "").lower()
        if not lowered:
            return False
        if cls.is_release_lookup(lowered):
            return False
        if re.search(r"\btop\s*\d+\b", lowered):
            return True
        return any(re.search(rf"\b{re.escape(marker)}\b", lowered) for marker in cls.RANKING_MARKERS)

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
    def _month_year_pattern() -> str:
        return r"(?:Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}"

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

    @staticmethod
    def _normalize_broken_ranking_markup(text: str) -> str:
        value = WebSearchTemplateEngine._normalize_broken_release_markup(text)
        value = re.sub(r"(?im)^\s*Details:\s*.*$", "", value)
        value = re.sub(
            r"(?im)^\s*(?:#{1,6}\s*)?(?:\d+\.?\s*)?Quellen\s*$[\s\S]*$",
            "",
            value,
        )
        value = re.sub(
            r"\s*\(Quelle:\s*([^)]+)\)\.?",
            lambda m: f"\nQuelle: {m.group(1).strip()}.",
            value,
            flags=re.IGNORECASE,
        )
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
        month_year_rx = cls._month_year_pattern()

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
            (rf"\s+ver(?:ö|oe|Ã¶|ÃƒÂ¶)?ffentlicht\s+[^.]*?\s+am\s+({date_rx})\s+", " veröffentlicht "),
            (rf"\s+bringt\s+[^.]*?\s+am\s+({date_rx})\s+(?:heraus|raus)", " bringt ein neues Werk heraus"),
            (rf"\s+kehrt\s+[^.]*?\s+am\s+({date_rx})\s+mit\s+", " kehrt mit "),
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

        month_year_patterns = (
            (rf"\s+f(?:ür|ue|Ã¼|ÃƒÂ¼)r\s+eine\s+Ver(?:ö|oe|Ã¶|ÃƒÂ¶)?ffentlichung\s+im\s+Laufe\s+des\s+({month_year_rx})\s+angek(?:ü|ue|Ã¼|ÃƒÂ¼)ndigt", " ist angekündigt"),
            (rf"\s+im\s+Laufe\s+des\s+({month_year_rx})\s+angek(?:ü|ue|Ã¼|ÃƒÂ¼)ndigt", " angekündigt"),
        )
        for pattern, replacement in month_year_patterns:
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
                r"ranking|rangliste|topliste|beste|besten|aller-zeiten|aller zeiten|galerie|"
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
            url = normalize_source_url(str(item.get("url") or item.get("source_url") or "").strip())
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
            url = fallback_url
        if url:
            return f"Quelle: {label}. [Link]({url})"
        return f"Quelle: {label}."

    @staticmethod
    def _is_person_or_sports_ranking(intent_text: str) -> bool:
        lowered = str(intent_text or "").lower()
        return any(
            marker in lowered
            for marker in (
                "spieler",
                "sportler",
                "basketball",
                "fussball",
                "fußball",
                "person",
                "personen",
                "athlet",
                "athleten",
            )
        )

    @staticmethod
    def _wikipedia_detail_url(title: str) -> str:
        value = re.sub(r"\([^)]*\)", " ", str(title or ""))
        value = re.sub(r"\s+", " ", value).strip(" :")
        if not value or len(value) > 80:
            return ""
        if not re.search(r"[A-Za-zÃ„Ã–ÃœÃ¤Ã¶Ã¼ÃŸ]", value):
            return ""
        slug = "_".join(value.split())
        return f"https://de.wikipedia.org/wiki/{slug}"

    @classmethod
    def _ranking_source_lines(
        cls,
        source: str,
        source_url_map: Dict[str, str],
        fallback_url: str = "",
        detail_url: str = "",
        title: str = "",
        intent_text: str = "",
    ) -> str:
        label = str(source or "").strip() or "nicht eindeutig verfÃ¼gbar"
        normalized = cls._normalize_source_label(label)
        source_url = source_url_map.get(normalized, "")
        if not source_url:
            for known_label, known_url in source_url_map.items():
                if normalized and (normalized in known_label or known_label in normalized):
                    source_url = known_url
                    break
        if not source_url:
            source_url = fallback_url
        if not detail_url and cls._is_person_or_sports_ranking(intent_text):
            detail_url = cls._wikipedia_detail_url(title)

        source_line = f"Quelle: {label}."
        if source_url:
            source_line += f" [Liste]({source_url})"
        if detail_url and detail_url != source_url:
            return source_line + f"\nDetails: [Link]({detail_url})"
        if source_url:
            return source_line.replace("[Liste]", "[Link]")
        return source_line

    @classmethod
    def _ranking_detail_line(
        cls,
        title: str,
        detail_url: str = "",
        intent_text: str = "",
    ) -> str:
        url = detail_url
        if not url and cls._is_person_or_sports_ranking(intent_text):
            url = cls._wikipedia_detail_url(title)
        if url:
            return f"Details: [Link]({url})"
        return "Details: online leider nicht eindeutig verfÃ¼gbar."

    @classmethod
    def _ranking_list_source_line(
        cls,
        data: Optional[Dict[str, Any]],
        items: List[RankingListItem],
        preferred_label_override: str = "",
        intent_text: str = "",
    ) -> str:
        source_url_map, ordered_source_urls, detail_candidates = cls._build_source_links(data or {})
        preferred_label = str(preferred_label_override or "").strip()
        for item in items:
            if preferred_label:
                break
            match = re.search(r"^Quelle:\s*([^.\n]+)\.", item.source_line, flags=re.IGNORECASE)
            if match:
                preferred_label = match.group(1).strip()
                break
        url = ""
        if preferred_label:
            normalized = cls._normalize_source_label(preferred_label)
            url = source_url_map.get(normalized, "")
            if not url:
                for known_label, known_url in source_url_map.items():
                    if normalized and (normalized in known_label or known_label in normalized):
                        url = known_url
                        break
            if url:
                matching_text = ""
                for candidate in detail_candidates:
                    if str(candidate.get("url") or "") == url:
                        matching_text = str(candidate.get("search_text") or "")
                        break
                if not cls._looks_like_overview_source(matching_text or url):
                    url = ""
        if not url:
            for candidate in detail_candidates:
                candidate_url = str(candidate.get("url") or "")
                candidate_text = str(candidate.get("search_text") or "")
                if candidate_url and cls._looks_like_overview_source(candidate_text):
                    url = candidate_url
                    break
        if preferred_label and url:
            return f"{cls.RANKING_INTRO_SOURCE_PREFIX}: {preferred_label}. [Link]({url})"
        if preferred_label:
            return f"{cls.RANKING_INTRO_SOURCE_PREFIX}: {preferred_label}."
        if url:
            return f"{cls.RANKING_INTRO_SOURCE_PREFIX}: [Link]({url})"
        return ""

    @classmethod
    def _split_ranking_prefix(cls, prefix: str) -> tuple[str, str]:
        value = str(prefix or "").strip()
        if not value:
            return "", ""
        source_label = ""

        def _capture(match: re.Match[str]) -> str:
            nonlocal source_label
            source_label = match.group(1).strip()
            return ""

        value = re.sub(
            rf"(?im)^\s*{re.escape(cls.RANKING_INTRO_SOURCE_PREFIX)}:\s*([^.\n]+)\.?.*$",
            _capture,
            value,
        )
        value = re.sub(r"\n{3,}", "\n\n", value).strip()
        return value, source_label

    @classmethod
    def _ranking_intro_line(cls, intent_text: str, items: List[RankingListItem]) -> str:
        if not items:
            return ""
        lowered = str(intent_text or "").lower()
        count = len(items)
        if "basketball" in lowered and ("spieler" in lowered or "sportler" in lowered):
            return f"Die {count} erfolgreichsten Basketballer aller Zeiten sind:"
        if "buch" in lowered or "bÃ¼cher" in lowered or "buecher" in lowered:
            return f"Die {count} relevantesten BÃ¼cher aus der Suche sind:"
        if "serie" in lowered or "serien" in lowered:
            return f"Die {count} relevantesten Serien aus der Suche sind:"
        if "kopfhÃ¶rer" in lowered or "kopfhoerer" in lowered:
            return f"Die {count} relevantesten KopfhÃ¶rer aus der Suche sind:"
        if "tool" in lowered or "ki" in lowered or "ai" in lowered:
            return f"Die {count} relevantesten Tools aus der Suche sind:"
        return f"Die {count} relevantesten EintrÃ¤ge aus der Suche sind:"

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

    @staticmethod
    def _strip_ranking_noise(text: str) -> str:
        value = str(text or "").strip()
        if not value:
            return value
        patterns = (
            r"\s*\(([a-z0-9-]+\.(?:com|de|net|org|co\.uk|tv))\)\.?",
            r"\s*\bl(?:aut|auter)\s+(?:der\s+)?(?:Quelle|Suchergebnis|Liste|Ranking)\b[:,]?\s*",
            r"\s*\b(?:im|in\s+der)\s+(?:Ranking|Topliste|Rangliste)\s+(?:gef(?:ue|ü)hrt|gelistet)\b\.?",
        )
        for pattern in patterns:
            value = re.sub(pattern, " ", value, flags=re.IGNORECASE).strip()
        value = re.sub(r"\s{2,}", " ", value)
        return value.strip(" -;:,")

    @classmethod
    def _derive_ranking_title_and_description(cls, title: str, body: str) -> tuple[str, str]:
        clean_title = re.sub(r"\s+", " ", str(title or "")).strip(" :*")
        clean_body = re.sub(r"\s+", " ", str(body or "")).strip()
        clean_body = re.sub(r"^[\u2013\u2014-]\s*", "", clean_body).strip()

        inline_dash = re.match(r"^(.+?)\s+(?:[\u2013\u2014-]|\?)\s+(.+)$", clean_title)
        if inline_dash and not clean_body:
            clean_title = inline_dash.group(1).strip(" :")
            clean_body = inline_dash.group(2).strip()

        if not clean_body:
            colon = re.match(r"^([^:]{2,100}):\s*(.+)$", clean_title)
            if colon:
                clean_title = colon.group(1).strip(" :")
                clean_body = colon.group(2).strip()

        return clean_title, cls._strip_ranking_noise(clean_body)

    @classmethod
    def _split_person_ranking_sentence(
        cls,
        title: str,
        body: str,
        intent_text: str,
    ) -> tuple[str, str]:
        clean_title = str(title or "").strip()
        clean_body = str(body or "").strip()
        if clean_body or not cls._is_person_or_sports_ranking(intent_text):
            return clean_title, clean_body
        words = clean_title.split()
        if len(words) < 3:
            return clean_title, clean_body

        name_parts: List[str] = []
        rest_parts: List[str] = []
        for word in words:
            core = word.strip(".,;:!?\"'()[]")
            if not rest_parts and len(name_parts) < 4 and re.match(r"^[A-ZÃ„Ã–Ãœ][A-Za-zÃ„Ã–ÃœÃ¤Ã¶Ã¼ÃŸ.'-]*$", core):
                name_parts.append(core)
                continue
            rest_parts.append(word)
        if len(name_parts) < 2 or not rest_parts:
            return clean_title, clean_body
        name = " ".join(name_parts).strip()
        description = " ".join(rest_parts).strip()
        if description:
            description = description[0].upper() + description[1:]
        return name, description

    @classmethod
    def _parse_ranking_items(
        cls,
        text: str,
        data: Optional[Dict[str, Any]] = None,
        intent_text: str = "",
    ) -> List[RankingListItem]:
        value = cls._normalize_broken_ranking_markup(text)
        source_url_map, ordered_source_urls, detail_candidates = cls._build_source_links(data or {})
        entry_re = re.compile(
            r"(?ms)^(\d+)\.\s*"
            r"(?:"
            r"\*\*(.+?)(?::)?\*\*:?\s*|"
            r"\*\*(.+?)(?=\s+\(Quelle:|\s+Quelle:|\n|$)|"
            r"([^:\n]+):\s*|"
            r"([^:\n]+)(?=\s+\(Quelle:|\s+Quelle:|\n|$)"
            r")"
            r"(.*?)(?=^\d+\.|\Z)"
        )
        items: List[RankingListItem] = []
        for match in entry_re.finditer(value):
            number = match.group(1).strip()
            title = re.sub(
                r"\s+",
                " ",
                match.group(2) or match.group(3) or match.group(4) or match.group(5) or "",
            ).strip(" :*")
            body = re.sub(r"\s+", " ", match.group(6)).strip()
            body = re.sub(r"^\*+\s*", "", body).strip()
            source, title = cls._extract_source(title)
            body_source, body = cls._extract_source(body)
            if not source:
                source = body_source
            title, body = cls._derive_ranking_title_and_description(title, body)
            title, body = cls._split_person_ranking_sentence(title, body, intent_text)
            description = cls._ensure_sentence(body)
            fallback_url = ""
            try:
                source_position = int(number) - 1
            except ValueError:
                source_position = -1
            if 0 <= source_position < len(ordered_source_urls):
                fallback_url = ordered_source_urls[source_position]
            elif len(ordered_source_urls) == 1:
                fallback_url = ordered_source_urls[0]
            if cls._is_person_or_sports_ranking(intent_text):
                detail_url = cls._wikipedia_detail_url(title) or cls._best_detail_source_url(title, detail_candidates)
            else:
                detail_url = cls._best_detail_source_url(title, detail_candidates)
            source_line = cls._ranking_source_lines(
                source,
                source_url_map,
                fallback_url,
                detail_url,
                title=title,
                intent_text=intent_text,
            )
            detail_line = cls._ranking_detail_line(title, detail_url, intent_text)
            items.append(
                RankingListItem(
                    index=number,
                    title=title,
                    description=description,
                    source_line=f"{source_line}\n{detail_line}",
                )
            )
        return items

    @classmethod
    def render_ranking_list(
        cls,
        text: str,
        data: Optional[Dict[str, Any]] = None,
        intent_text: str = "",
    ) -> str:
        value = cls._normalize_broken_ranking_markup(text)
        intent_text = str(intent_text or (data or {}).get("query") or "")
        items = cls._parse_ranking_items(value, data=data, intent_text=intent_text)
        if not items:
            return value
        first_match = re.search(r"(?m)^\d+\.", value)
        prefix = value[: first_match.start()].strip() if first_match else ""
        clean_prefix, prefix_source_label = cls._split_ranking_prefix(prefix)
        blocks: List[str] = [clean_prefix] if clean_prefix else [cls._ranking_intro_line(intent_text, items)]
        list_source_line = cls._ranking_list_source_line(data, items, prefix_source_label, intent_text)
        if list_source_line:
            blocks.append(list_source_line)
        for item in items:
            detail_line = ""
            for line in item.source_line.splitlines():
                if line.strip().startswith("Details:"):
                    detail_line = line.strip()
                    break
            blocks.append(
                "\n".join(
                    [
                        f"{item.index}. **{item.title}**",
                        item.description,
                        detail_line or "Details: online leider nicht eindeutig verfÃ¼gbar.",
                    ]
                )
            )
        return "\n\n".join(block for block in blocks if block).strip()

from __future__ import annotations

import re

from .models import SupportedFact, VerifiedSource
from .query_planner import extract_subject, query_domain


def _sentence_split(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    if not clean:
        return []
    return [part.strip(" .") for part in re.split(r"(?<!\d)[.!?]\s+", clean) if part.strip(" .")]


def _clean_title(title: str, source_label: str) -> str:
    value = re.sub(r"\s+", " ", str(title or "Aktuelle Meldung")).strip(" .")
    label_parts = [source_label, source_label.split(".")[0] if source_label else ""]
    for label in label_parts:
        if not label:
            continue
        value = re.sub(rf"\s*[-|]\s*{re.escape(label)}\s*$", "", value, flags=re.IGNORECASE).strip(" .")
    return value or "Aktuelle Meldung"


def _first_list_item(text: str) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return ""
    value = re.sub(r"^\s*(?:[-*]\s*)?(?:1[.)]\s*)", "", value)
    parts = re.split(r"\s(?:2[.)]|II[.)])\s+", value, maxsplit=1)
    return parts[0].strip()


def _clean_markup(text: str) -> str:
    value = str(text or "")
    value = re.sub(r"\bQuelle:\s*\[[^\]]+\]\([^)]*(?:\)|$)", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bQuelle:\s*https?://\S+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\bQuelle:\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[[^\]]{0,120}(?:https?://|\.de|\.com)[^\]]{0,160}$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -*.")


def _domain_subject_tokens(query: str) -> set[str]:
    domain = query_domain(query)
    if domain == "film":
        return {
            "film",
            "filme",
            "kino",
            "kinostart",
            "kinostarts",
            "trailer",
            "festival",
            "streaming",
            "startet",
            "erscheint",
        }
    if domain == "gaming":
        return {
            "gaming",
            "game",
            "games",
            "spiel",
            "spiele",
            "playstation",
            "xbox",
            "nintendo",
            "switch",
            "pc",
            "release",
            "erscheint",
            "angekuendigt",
            "ankündigt",
        }
    return _tokens(extract_subject(query))


def _quoted_or_bold_names(text: str) -> list[str]:
    raw = str(text or "")
    names: list[str] = []
    patterns = (
        r"\*\*([^*]{3,90})\*\*",
        r"„([^“]{3,90})“",
        r'"([^"]{3,90})"',
    )
    for pattern in patterns:
        for match in re.finditer(pattern, raw):
            candidate = _clean_markup(match.group(1))
            if _is_interesting_name(candidate):
                names.append(candidate)
    return _dedupe_names(names)


def _is_interesting_name(value: str) -> bool:
    lowered = str(value or "").casefold().strip()
    if len(lowered) < 4 or len(lowered) > 90:
        return False
    boring = {
        "umsatz",
        "gewinn",
        "treiber",
        "ausblick",
        "quelle",
        "detailartikel",
        "besucherstaerkster film",
        "besucherstärkster film",
        "verfuegbarkeit",
        "verfügbarkeit",
        "rekordumsatz",
        "quartalsdividende",
        "state of play juni 2026",
        "erfolgreich in den deutschen kinos gestartet",
    }
    if lowered in boring:
        return False
    if lowered.startswith("diese neuen ") or lowered.startswith("diese neue "):
        return False
    if re.fullmatch(r"\d{1,2}\.?\s*(mai|juni|juli|august|september|oktober|november|dezember)?", lowered):
        return False
    return True


def _dedupe_names(names: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for name in names:
        key = re.sub(r"\W+", "", name.casefold())
        if not key or key in seen:
            continue
        deduped.append(name)
        seen.add(key)
    return deduped


def _join_names(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} und {names[1]}"
    return f"{', '.join(names[:-1])} und {names[-1]}"


def _domain_release_summary(source: VerifiedSource, query: str, title: str) -> str:
    domain = query_domain(query)
    if domain not in {"film", "gaming"}:
        return ""
    text = f"{source.snippet} {source.page_excerpt[:900]}"
    names = _quoted_or_bold_names(text)
    title_without_site = re.split(r"\s[-|]\s", title, maxsplit=1)[0].strip()
    if domain == "gaming" and _is_interesting_name(title_without_site):
        if any(
            marker in title_without_site.casefold()
            for marker in ("gaming", "game", "games", "spiele", "release", "highlights", "playstation", "state of play", "xbox", "nintendo", "gta")
        ):
            names.insert(0, title_without_site)
    if domain == "film" and _is_interesting_name(title_without_site):
        if any(marker in title_without_site.casefold() for marker in ("film", "kino", "trailer", "start", "neu")) or any(
            marker in str(source.source_label or "").casefold()
            for marker in ("filmstarts", "moviejones", "kino.de", "kino-zeit", "filmportal")
        ):
            names.insert(0, title_without_site)
    names = _dedupe_names(names)[:4]
    if not names:
        if str(source.source_type or "") == "curated_briefing":
            title_summary = _title_as_summary(title)
            if title_summary and title_summary.casefold() != title.casefold():
                return title_summary
            return ""
        return ""
    if domain == "film":
        return f"Die Quelle nennt als konkrete Film-/Kino-Neuigkeiten unter anderem {_join_names(names)}"
    return f"Die Quelle nennt als konkrete Gaming-Neuigkeiten unter anderem {_join_names(names)}"


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9äöüß][a-z0-9äöüß._-]{2,}", str(value or "").casefold())
        if token not in {"news", "aktuell", "neues", "meldung", "nachrichten"}
    }


NAVIGATION_FRAGMENTS = (
    "zum inhalt springen",
    "zu hauptinhalt springen",
    "navigation",
    "shop login",
    "newsletter",
    "login | registrieren",
    "wo finde ich was",
    "toplisten",
    "reviews spiele",
    "filme & serien",
    "spiele & commun",
    "toggle search",
    "no result",
    "view all result",
    "home news",
    "startseite",
    "suche nach",
    "heise+ entdecken",
    "alle magazine im browser lesen",
    "newsticker hintergruende",
    "newsticker hintergr",
    "testberichte meinungen",
    "online-magazine",
    "apple store mac ipad iphone",
    "zubehoer support",
    "zubehör support",
    "newsroom open newsroom navigation",
    "close newsroom navigation",
    "verwandte themen",
    "updateverlauf",
    "wetter dax jobsuche partnersuche",
    "telefonverz",
)


def _strip_repeated_title(text: str, title: str) -> str:
    value = str(text or "").strip(" .")
    title_value = str(title or "").strip(" .")
    if not value or not title_value:
        return value
    value_folded = value.casefold()
    title_folded = title_value.casefold()
    if value_folded.startswith(title_folded):
        return value[len(title_value) :].lstrip(" -|:.").strip()
    title_without_site = re.split(r"\s[-|]\s", title_value, maxsplit=1)[0].strip()
    if title_without_site and value_folded.startswith(title_without_site.casefold()):
        return value[len(title_without_site) :].lstrip(" -|:.").strip()
    return value


def _looks_like_navigation_noise(text: str) -> bool:
    lowered = re.sub(r"\s+", " ", str(text or "")).casefold()
    if any(fragment in lowered for fragment in NAVIGATION_FRAGMENTS):
        return True
    if "[link]" in lowered or "](" in lowered or "quelle:" in lowered:
        return True
    short_words = lowered.split()
    uppercaseish = sum(1 for word in short_words if len(word) <= 3)
    return len(short_words) >= 18 and uppercaseish / max(len(short_words), 1) > 0.45


def _clean_summary_text(text: str, title: str, query: str) -> str:
    text = _first_list_item(text)
    subject_tokens = _domain_subject_tokens(query)
    title_norm = re.sub(r"\s+", " ", title).casefold()
    selected: list[str] = []
    for sentence in _sentence_split(text):
        normalized = _clean_markup(_strip_repeated_title(re.sub(r"\s+", " ", sentence).strip(" ."), title))
        lowered = normalized.casefold()
        if not normalized or lowered == title_norm:
            continue
        if _looks_like_navigation_noise(normalized):
            continue
        if len(normalized) < 35:
            continue
        if subject_tokens and not any(token in lowered for token in subject_tokens):
            continue
        selected.append(normalized)
        if len(selected) >= 2:
            break
    return ". ".join(selected).strip(" .")


def extract_supported_fact(source: VerifiedSource, query: str = "") -> SupportedFact:
    title = _clean_title(source.title, source.source_label)
    summary = _domain_release_summary(source, query, title)
    if not summary:
        summary = _clean_summary_text(source.snippet, title, query)
    if not summary or _looks_like_navigation_noise(summary):
        summary = _clean_summary_text(source.page_excerpt, title, query)
    sentences = _sentence_split(summary)
    summary = ". ".join(sentences[:2]).strip(" .")
    if not summary:
        summary = _title_as_summary(title)
    if len(summary) > 340:
        summary = summary[:340].rsplit(" ", 1)[0].strip(" .")
    return SupportedFact(title=title, summary=summary + ".", source=source)


def _title_as_summary(title: str) -> str:
    cleaned = re.split(r"\s[-|]\s", str(title or "Aktuelle Meldung"), maxsplit=1)[0].strip(" .")
    if not cleaned:
        cleaned = "Aktuelle Meldung"
    return cleaned

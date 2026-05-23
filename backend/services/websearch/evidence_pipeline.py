from __future__ import annotations

from dataclasses import dataclass, field
import logging
import re
from typing import Any, Mapping, Sequence

from backend.services.websearch.link_quality import (
    LinkIntent,
    SourceQualityScore,
    broad_label_for_match,
    is_low_value_source,
    normalize_label_for_match,
    score_source_for_intent,
    select_best_source_for_item,
)
from backend.services.websearch.query_bias import normalize_source_url

logger = logging.getLogger("janus_backend")


NEWS_QUERY_MARKERS = (
    "news",
    "nachrichten",
    "neuigkeiten",
    "schlagzeilen",
    "aktuell",
    "aktuelle",
    "neues",
    "latest",
)


_OFFICIAL_NEWS_SITES = {
    "openai": "openai.com",
    "google": "blog.google",
    "microsoft": "microsoft.com",
    "meta": "about.fb.com",
    "apple": "apple.com",
    "nvidia": "nvidia.com",
    "tesla": "tesla.com",
}


@dataclass(frozen=True)
class EvidenceClaim:
    index: str
    title: str
    summary: str
    label: str
    intent: LinkIntent = LinkIntent.NEWS


@dataclass(frozen=True)
class EvidenceDecision:
    claim: EvidenceClaim
    url: str = ""
    quality: SourceQualityScore = field(default_factory=lambda: SourceQualityScore(-999, False, ("no_candidates",)))

    @property
    def accepted(self) -> bool:
        return bool(self.url and self.quality.acceptable)

    @property
    def no_link_reason(self) -> str:
        if self.accepted:
            return ""
        return ",".join(self.quality.reasons or ("no_acceptable_source",))


class EvidencePipeline:
    """Provider-agnostic evidence extraction and source binding.

    This layer keeps retrieval, evidence quality and chat rendering separated:
    providers may return sparse or redirected sources, but every display link
    must be accepted against one concrete claim before it reaches the renderer.
    """

    @classmethod
    def is_news_query(cls, query: str) -> bool:
        lowered = str(query or "").casefold()
        return any(marker in lowered for marker in NEWS_QUERY_MARKERS)

    @staticmethod
    def split_news_body(body: str) -> tuple[str, str]:
        clean = re.sub(r"\s+", " ", str(body or "").replace("**", "")).strip(" .")
        if not clean:
            return "Meldung", ""
        colon_match = re.match(r"^(.{3,90}?):\s+(.+)$", clean)
        if colon_match:
            return colon_match.group(1).strip(" ."), colon_match.group(2).strip(" .")
        title = re.split(r"[.;]", clean, maxsplit=1)[0].strip()
        return title[:90].strip(" ."), clean

    @staticmethod
    def extract_source_label(body: str) -> tuple[str, str]:
        clean = re.sub(r"\s+", " ", str(body or "")).strip(" .")
        label = ""
        source_match = re.search(r"\(Quelle:\s*([^)]+)\)", clean, flags=re.IGNORECASE)
        if not source_match:
            source_match = re.search(
                r"\bQuelle:\s*([^\n]+?)(?:\.\s*(?:Link)?\s*$|$)",
                clean,
                flags=re.IGNORECASE,
            )
        if source_match:
            label = re.sub(r"\s+", " ", source_match.group(1)).strip(" .)")
            clean = re.sub(r"\s*\(Quelle:\s*[^)]+\)\.?", "", clean, flags=re.IGNORECASE).strip(" .")
            clean = re.sub(
                r"\s*\bQuelle:\s*[^\n]+?(?:\.\s*(?:Link)?\s*$|$)",
                "",
                clean,
                flags=re.IGNORECASE,
            ).strip(" .")
        return clean, label

    @classmethod
    def numbered_news_segments(cls, text: str) -> list[str]:
        primary_text = re.split(r"(?im)^\s*\[Global Research\]\s*$", str(text or ""), maxsplit=1)[0]
        starts = list(re.finditer(r"(?m)^\s*\d+[.)]\s*", primary_text))
        segments: list[str] = []
        for pos, match in enumerate(starts):
            start = match.end()
            end = starts[pos + 1].start() if pos + 1 < len(starts) else len(primary_text)
            segment = re.sub(r"\s+", " ", primary_text[start:end]).strip(" .")
            if segment:
                segments.append(segment)
        return segments

    @classmethod
    def extract_news_claims(cls, query: str, text: str, limit: int = 5) -> list[EvidenceClaim]:
        if not cls.is_news_query(query):
            return []
        claims: list[EvidenceClaim] = []
        for idx, segment in enumerate(cls.numbered_news_segments(text), start=1):
            body, label = cls.extract_source_label(segment)
            title, summary = cls.split_news_body(body)
            if not title or not label:
                continue
            claims.append(EvidenceClaim(index=str(idx), title=title, summary=summary, label=label))
            if len(claims) >= limit:
                break
        return claims

    @staticmethod
    def match_source_for_claim(sources: Sequence[Mapping[str, Any]], claim: EvidenceClaim) -> EvidenceDecision:
        url, quality = select_best_source_for_item(
            [source for source in sources if isinstance(source, Mapping)],
            intent=claim.intent,
            title=claim.title,
            summary=claim.summary,
            label=claim.label,
            target_index=claim.index,
        )
        decision = EvidenceDecision(claim=claim, url=url, quality=quality)
        logger.debug(
            "WEBSEARCH-EVIDENCE: claim=%s label=%s accepted=%s score=%s reasons=%s url=%s",
            claim.title,
            claim.label,
            decision.accepted,
            quality.score,
            ",".join(quality.reasons),
            url,
        )
        return decision

    @classmethod
    def match_sources_for_claims(
        cls,
        sources: Sequence[Mapping[str, Any]],
        claims: Sequence[EvidenceClaim],
    ) -> list[EvidenceDecision]:
        return [cls.match_source_for_claim(sources, claim) for claim in claims]

    @classmethod
    def claims_needing_resolution(
        cls,
        sources: Sequence[Mapping[str, Any]],
        claims: Sequence[EvidenceClaim],
    ) -> list[EvidenceClaim]:
        return [decision.claim for decision in cls.match_sources_for_claims(sources, claims) if not decision.accepted]

    @staticmethod
    def official_news_site_for_label(label: str) -> str:
        return _OFFICIAL_NEWS_SITES.get(broad_label_for_match(label), "")

    @classmethod
    def repair_query_for_claims(cls, base_query: str, claims: Sequence[EvidenceClaim], limit: int = 4) -> str:
        terms: list[str] = []
        for claim in claims[:limit]:
            official_site = cls.official_news_site_for_label(claim.label)
            if official_site:
                terms.append(f'"{claim.title}" site:{official_site}')
            else:
                terms.append(cls.repair_query_term_for_claim(claim))
        resolve_terms = " OR ".join(terms)
        return (
            f"{resolve_terms} {base_query} konkrete Detailquelle Artikel deutschsprachige Quelle "
            "letzte 30 Tage aktuell offizielle Quelle wenn genannt keine Startseite keine News-Uebersicht keine Aggregatoren "
            "keine Paywall keine Dokumentation keine API-Docs kein Help-Center kein dentro.de kein YouTube kein Reddit"
        )

    @classmethod
    def repair_query_term_for_claim(cls, claim: EvidenceClaim) -> str:
        official_site = cls.official_news_site_for_label(claim.label)
        if official_site:
            return f'"{claim.title}" site:{official_site}'

        label_norm = normalize_label_for_match(claim.label)
        label_domain = str(claim.label or "").strip().casefold().removeprefix("www.")
        if re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+", label_domain):
            return f'"{claim.title}" site:{label_domain}'
        if label_norm:
            return f'"{claim.title}" "{claim.label}" site:de'
        return f'"{claim.title}" site:de'

    @classmethod
    def focused_repair_query_for_claim(cls, base_query: str, claim: EvidenceClaim) -> str:
        term = cls.repair_query_term_for_claim(claim)
        summary_terms = " ".join(token for token in re.findall(r"[A-Za-z0-9ÄÖÜäöüß-]{4,}", claim.summary)[:6])
        return (
            f"{term} {summary_terms} {base_query} konkrete Detailseite Artikel deutschsprachig "
            "kein Startseite keine News-Uebersicht keine Paywall kein YouTube kein Reddit"
        )

    @classmethod
    def merge_resolved_sources(
        cls,
        sources: Sequence[Mapping[str, Any]],
        resolved_sources: Sequence[Mapping[str, Any]],
        claims: Sequence[EvidenceClaim],
    ) -> list[dict[str, Any]]:
        seen = {
            normalize_source_url(str(source.get("url") or source.get("source_url") or ""))
            for source in sources
            if isinstance(source, Mapping)
        }
        additions: list[dict[str, Any]] = []
        for claim in claims:
            for candidate in resolved_sources:
                if not isinstance(candidate, Mapping):
                    continue
                decision = cls.match_source_for_claim([candidate], claim)
                if not decision.accepted:
                    continue
                url = normalize_source_url(str(candidate.get("url") or candidate.get("source_url") or ""))
                if not url or url in seen:
                    continue
                item = dict(candidate)
                item["url"] = url
                item["news_target_index"] = claim.index
                item["news_target_title"] = claim.title
                item["news_target_label"] = claim.label
                additions.append(item)
                seen.add(url)
                break
        return additions + [dict(source) for source in sources if isinstance(source, Mapping)]

    @staticmethod
    def source_label_from_url(url: str) -> str:
        host = str(url or "").replace("https://", "").replace("http://", "").split("/")[0]
        host = host.removeprefix("www.")
        label = host.split(".")[0] if host else "Web"
        return label[:1].upper() + label[1:]

    @classmethod
    def news_items_from_text_and_sources(
        cls,
        *,
        query: str,
        text: str,
        sources: Sequence[Mapping[str, Any]],
        is_stale,
    ) -> list[dict[str, Any]]:
        source_rows = [source for source in sources if isinstance(source, Mapping)]
        items: list[dict[str, Any]] = []
        for claim in cls.extract_news_claims(query, text):
            if is_stale(f"{claim.title} {claim.summary}"):
                continue
            decision = cls.match_source_for_claim(source_rows, claim)
            url = decision.url if decision.accepted and not is_low_value_source(decision.url, LinkIntent.NEWS) else ""
            items.append(
                {
                    "title": claim.title,
                    "summary": claim.summary or "Kurzmeldung aus der Websuche; Details stehen in der verlinkten Quelle.",
                    "url": url,
                    "source": "websearch",
                    "source_label": claim.label or cls.source_label_from_url(url),
                    "date": "",
                    "evidence_score": decision.quality.score,
                    "evidence_reasons": list(decision.quality.reasons),
                    "no_link_reason": decision.no_link_reason,
                }
            )
            if len(items) >= 5:
                break
        return items

from __future__ import annotations

from .query_planner import query_domain
from .source_classifier import SourceClassification


HARD_REJECT_SOURCE_TYPES = {
    "asset",
    "search_page",
    "community",
    "topic_listing",
}


def evidence_rejection_reason(query: str, classification: SourceClassification) -> str:
    source_type = classification.source_type
    if source_type in HARD_REJECT_SOURCE_TYPES:
        return f"source_type_{source_type}"

    domain = query_domain(query)
    if domain in {"film", "gaming"}:
        if source_type == "curated_briefing":
            return ""
        if source_type == "calendar_or_listing" and classification.evidence_score < 0.72:
            return "insufficient_briefing_evidence"
        if source_type == "unknown" and classification.evidence_score < 0.65:
            return "insufficient_briefing_evidence"
    elif source_type == "calendar_or_listing":
        return "insufficient_news_evidence"

    if classification.evidence_score < 0.35:
        return "insufficient_evidence"
    return ""

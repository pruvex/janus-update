from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SearchCandidate:
    provider: str
    url: str
    title: str
    snippet: str
    rank: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PageFetchResult:
    url: str
    final_url: str
    status_code: int | None
    title: str
    text: str
    language_hint: str = ""
    published_at: str | None = None
    error: str = ""


@dataclass(frozen=True)
class VerifiedSource:
    url: str
    canonical_url: str
    title: str
    source_label: str
    snippet: str
    page_excerpt: str
    language: str
    published_at: str | None
    is_reachable: bool
    is_detail_page: bool
    topic_match_score: float
    source_quality_score: float
    provider: str = ""
    rank: int = 999
    source_type: str = "unknown"
    evidence_score: float = 0.0
    rejection_reasons: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SupportedFact:
    title: str
    summary: str
    source: VerifiedSource
    topic_label: str = "Aktuelles"


@dataclass(frozen=True)
class SingleVerifiedNewsResult:
    query: str
    fact: SupportedFact | None
    status: str
    reason: str = ""
    facts: tuple[SupportedFact, ...] = field(default_factory=tuple)

    @property
    def has_fact(self) -> bool:
        return self.fact is not None

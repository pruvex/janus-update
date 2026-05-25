from __future__ import annotations

import pytest

from backend.services.websearch_v3.models import PageFetchResult, SearchCandidate, VerifiedSource
from backend.services.websearch_v3.fact_extractor import extract_supported_fact
from backend.services.websearch_v3.page_fetcher import fetch_candidate_page
from backend.services.websearch_v3.page_fetcher import _repair_mojibake
from backend.services.websearch_v3.pipeline import WebSearchV3Pipeline, source_policy_for_query
from backend.services.websearch_v3.gemini_native import _build_phase1_prompt
from backend.services.websearch_v3.query_planner import (
    build_briefing_search_queries,
    build_company_search_queries,
    extract_subject,
    is_broad_briefing_query,
    is_simple_news_query,
)
from backend.services.websearch_v3.providers import (
    candidates_from_websearch_result,
    normalize_gemini_grounding_response,
    normalize_openai_response_output,
)
from backend.services.websearch_v3.renderer_adapter import NO_SOURCE_TEXT, render_single_verified_news
from backend.services.websearch_v3.source_classifier import classify_source
from backend.services.websearch_v3.topic_labeler import label_source_topic
from backend.services.websearch.query_bias import build_query_suffix


def _page(url: str, *, title: str = "Microsoft und EY bauen KI-Kooperation aus", text: str | None = None) -> PageFetchResult:
    return PageFetchResult(
        url=url,
        final_url=url,
        status_code=200,
        title=title,
        text=text
        or (
            "Microsoft und EY bauen ihre KI-Kooperation aus. Die Partner wollen Unternehmen "
            "bei der Einfuehrung von KI-Loesungen unterstuetzen und neue Dienste bereitstellen."
        ),
        language_hint="de",
    )


def test_query_bias_does_not_treat_filmpreis_as_price_query():
    suffix = build_query_suffix("2026 aktuelle Filmnews Deutschland Kino Festival Deutscher Filmpreis Filmportal")

    assert '"in Euro"' not in suffix


def test_source_policy_is_adaptive_by_query_shape():
    assert source_policy_for_query("hat Nvidia Quartalszahlen veröffentlicht?", 4).target_sources == 1
    assert source_policy_for_query("was gibt es neues zu Microsoft?", 4).target_sources == 2
    assert source_policy_for_query("was gibt es neues im Gaming?", 4).target_sources == 3
    assert source_policy_for_query("Neues im Kino aktuelle Kinostarts Deutschland Mai 2026", 4).target_sources == 3


def test_source_policy_respects_configured_upper_cap():
    assert source_policy_for_query("was gibt es neues im Kino?", 2).target_sources == 2
    assert source_policy_for_query("was gibt es neues zu OpenAI?", 1).target_sources == 1


def test_source_classifier_distinguishes_detail_article_from_listing():
    detail_candidate = SearchCandidate(
        provider="openai",
        url="https://www.game.de/game-branchenbarometer-2026-stimmung-in-der-deutschen-games-branche-hellt-sich-langsam-auf",
        title="Games-Branchenbarometer 2026: Stimmung hellt sich langsam auf",
        snippet="Aktuelle Trends fuer Studios und Publisher.",
        rank=1,
    )
    listing_candidate = SearchCandidate(
        provider="openai",
        url="https://www.filmportal.de/news/cinema/month/202601",
        title="Kinostarts | filmportal.de",
        snippet="Monatsuebersicht der Kinostarts.",
        rank=1,
    )

    detail = classify_source(
        detail_candidate,
        _page(detail_candidate.url, title=detail_candidate.title, text="Aktuelle Games-Branche Trends 2026."),
    )
    listing = classify_source(
        listing_candidate,
        _page(listing_candidate.url, title=listing_candidate.title, text="Kinostarts Monatsuebersicht Kalender."),
    )

    assert detail.source_type == "news_article"
    assert detail.evidence_score > listing.evidence_score
    assert listing.source_type == "calendar_or_listing"


def test_page_fetcher_repairs_common_utf8_mojibake():
    assert _repair_mojibake("fÃ¼r dein KMU") == "für dein KMU"


@pytest.mark.asyncio
async def test_vertex_redirect_fetch_error_preserves_resolved_target(monkeypatch):
    class Response:
        def __init__(self, *, url: str, status_code: int, headers: dict[str, str], text: str = ""):
            self.url = url
            self.status_code = status_code
            self.headers = headers
            self.text = text

    calls: list[str] = []

    def fake_get(url, **kwargs):
        calls.append(url)
        if "vertexaisearch.cloud.google.com" in url:
            return Response(
                url=url,
                status_code=302,
                headers={"Location": "https://borncity.com/news/microsoft-und-ey-ki-agenten"},
            )
        raise TimeoutError("read timed out")

    monkeypatch.setattr("backend.services.websearch_v3.page_fetcher.requests.get", fake_get)

    page = await fetch_candidate_page(
        SearchCandidate(
            provider="gemini",
            url="https://vertexaisearch.cloud.google.com/grounding-api-redirect/microsoft",
            title="borncity.com",
            snippet="Microsoft und EY erweitern ihre KI-Kooperation.",
            rank=0,
        )
    )

    assert calls == [
        "https://vertexaisearch.cloud.google.com/grounding-api-redirect/microsoft",
        "https://borncity.com/news/microsoft-und-ey-ki-agenten",
    ]
    assert page.final_url == "https://borncity.com/news/microsoft-und-ey-ki-agenten"
    assert page.error == "read timed out"


@pytest.mark.asyncio
async def test_microsoft_news_accepts_good_german_detail_source():
    source_url = "https://www.computerwoche.de/a/microsoft-und-ey-bauen-ki-kooperation-aus,123456"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": source_url,
                    "title": "Microsoft und EY bauen KI-Kooperation aus",
                    "snippet": "Microsoft und EY erweitern ihre Zusammenarbeit rund um KI.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url)

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Microsoft?")

    assert result.status == "ok"
    assert result.fact is not None
    assert result.fact.source.canonical_url == source_url.rstrip("/")
    rendered = render_single_verified_news(result)
    assert "Quelle:" in rendered
    assert f"[Link]({source_url})" in rendered


@pytest.mark.asyncio
async def test_two_verified_sources_are_rendered_when_requested():
    first_url = "https://www.computerwoche.de/a/microsoft-und-ey-bauen-ki-kooperation-aus,123456"
    second_url = "https://www.heise.de/news/microsoft-stellt-neue-cloud-funktion-vor-987654.html"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": first_url,
                    "title": "Microsoft und EY bauen KI-Kooperation aus",
                    "snippet": "Microsoft und EY erweitern ihre Zusammenarbeit rund um KI.",
                },
                {
                    "url": second_url,
                    "title": "Microsoft stellt neue Cloud-Funktion vor",
                    "snippet": "Microsoft stellt eine neue Cloud-Funktion fuer Unternehmenskunden vor.",
                },
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        if candidate.url == second_url:
            return _page(
                candidate.url,
                title="Microsoft stellt neue Cloud-Funktion vor",
                text=(
                    "Microsoft stellt eine neue Cloud-Funktion fuer Unternehmenskunden vor. "
                    "Die Funktion soll Teams beim Betrieb von KI-Anwendungen unterstuetzen und "
                    "wird in mehreren deutschen Rechenzentren bereitgestellt."
                ),
            )
        return _page(candidate.url)

    result = await WebSearchV3Pipeline(search, fetch).verified_news("was gibt es neues zu Microsoft?", max_sources=2)
    rendered = render_single_verified_news(result)

    assert result.status == "ok"
    assert len(result.facts) == 2
    assert "zwei belegte Meldungen" in rendered
    assert "Partnerschaft & Kunden:" in rendered
    assert "Produkt & Technik:" in rendered
    assert f"[Link]({first_url})" in rendered
    assert f"[Link]({second_url})" in rendered


@pytest.mark.asyncio
async def test_two_source_mode_prefers_distinct_hosts():
    first_url = "https://www.computerwoche.de/a/microsoft-und-ey-bauen-ki-kooperation-aus,123456"
    same_host_url = "https://www.computerwoche.de/a/microsoft-stellt-cloud-funktion-vor,987654"
    second_host_url = "https://www.heise.de/news/microsoft-stellt-neue-cloud-funktion-vor-987654.html"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": first_url,
                    "title": "Microsoft und EY bauen KI-Kooperation aus",
                    "snippet": "Microsoft und EY erweitern ihre Zusammenarbeit rund um KI.",
                },
                {
                    "url": same_host_url,
                    "title": "Microsoft stellt Copilot-Funktion vor",
                    "snippet": "Microsoft stellt eine neue Copilot-Funktion fuer Unternehmenskunden vor.",
                },
                {
                    "url": second_host_url,
                    "title": "Microsoft stellt neue Cloud-Funktion vor",
                    "snippet": "Microsoft stellt eine neue Cloud-Funktion fuer Unternehmenskunden vor.",
                },
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                f"{candidate.title}. Microsoft stellt neue Funktionen fuer Unternehmenskunden vor. "
                "Die Meldung beschreibt KI, Cloud und neue Dienste fuer deutsche Kunden."
            ),
        )

    result = await WebSearchV3Pipeline(search, fetch).verified_news("was gibt es neues zu Microsoft?", max_sources=2)

    assert result.status == "ok"
    assert len(result.facts) == 2
    assert [fact.source.canonical_url for fact in result.facts] == [first_url, second_host_url]


@pytest.mark.asyncio
async def test_german_query_does_not_add_english_second_source_when_german_source_exists():
    german_url = "https://www.computerwoche.de/article/4176377/microsoft-und-ey-bundeln-ihre-ki-krafte.html"
    english_url = "https://learn.microsoft.com/en-us/partner-center/announcements/2026-may"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": german_url,
                    "title": "Microsoft und EY buendeln ihre KI-Kraefte",
                    "snippet": "Microsoft und EY bauen eine KI-Partnerschaft fuer Unternehmenskunden aus.",
                },
                {
                    "url": english_url,
                    "title": "Partner Center announcements - Microsoft Learn",
                    "snippet": "Microsoft publishes Partner Center announcements for May 2026.",
                },
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        if candidate.url == english_url:
            return PageFetchResult(
                url=candidate.url,
                final_url=candidate.url,
                status_code=200,
                title="Partner Center announcements - Microsoft Learn",
                text=(
                    "Partner Center announcements for May 2026. Microsoft publishes updates for partners, "
                    "commercial marketplace offers, cloud services, and account management."
                ),
                language_hint="en",
            )
        return _page(
            candidate.url,
            title="Microsoft und EY buendeln ihre KI-Kraefte",
            text=(
                "Microsoft und EY buendeln ihre KI-Kraefte. Die Partner bauen eine KI-Kooperation fuer "
                "Unternehmenskunden aus und wollen Copilot in grossen Organisationen skalieren."
            ),
        )

    result = await WebSearchV3Pipeline(search, fetch).verified_news("was gibt es neues zu Microsoft?", max_sources=2)

    assert result.status == "ok"
    assert len(result.facts) == 1
    assert result.facts[0].source.canonical_url == german_url


@pytest.mark.asyncio
async def test_generic_microsoft_news_page_is_rejected():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://news.microsoft.com/de-de/news",
                    "title": "Microsoft News",
                    "snippet": "Microsoft News und aktuelle Meldungen.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title="Microsoft News")

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Microsoft?")

    assert result.status == "no_source"
    assert render_single_verified_news(result) == NO_SOURCE_TEXT


@pytest.mark.asyncio
async def test_generic_microsoft_recent_news_page_is_rejected():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://news.microsoft.com/de-de/recent-news",
                    "title": "Recent News | News Center Microsoft",
                    "snippet": "Microsoft News und aktuelle Meldungen.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title="Recent News | News Center Microsoft")

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Microsoft?")

    assert result.status == "no_source"
    assert render_single_verified_news(result) == NO_SOURCE_TEXT


@pytest.mark.asyncio
async def test_generic_microsoft_recent_news_paged_url_is_rejected():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://news.microsoft.com/de-de/recent-news/page/5",
                    "title": "Recent News | Seite 5 von 638 | News Center Microsoft",
                    "snippet": "Microsoft News Archivseite.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title)

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Microsoft?")

    assert result.status == "no_source"
    assert render_single_verified_news(result) == NO_SOURCE_TEXT


@pytest.mark.asyncio
async def test_generic_microsoft_source_show_all_page_is_rejected():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://news.microsoft.com/source/emea/alle-anzeigen?lang=de",
                    "title": "Alle anzeigen - Source EMEA",
                    "snippet": "Microsoft Source EMEA Übersicht.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title)

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Microsoft?")

    assert result.status == "no_source"
    assert render_single_verified_news(result) == NO_SOURCE_TEXT


@pytest.mark.asyncio
async def test_generic_stock_news_listing_is_rejected():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.onvista.de/news/aktien/Microsoft-News-US5949181045",
                    "title": "Microsoft News - Aktuelle Nachrichten zur Microsoft Aktie",
                    "snippet": "Microsoft und EY bauen ihre KI-Kooperation aus.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title="Microsoft News - Aktuelle Nachrichten zur Microsoft Aktie - onvista",
            text="Microsoft Aktie News Kurse Analysen. Microsoft und EY bauen ihre KI-Kooperation aus.",
        )

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Microsoft?")

    assert result.status == "no_source"
    assert render_single_verified_news(result) == NO_SOURCE_TEXT


@pytest.mark.asyncio
async def test_financial_news_source_is_rejected_for_general_company_news():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.ad-hoc-news.de/boerse/news/ueberblick/nvidia-corporation-aktie-us67066g1040-analysten-sehen-weiter-fantasie/69410400",
                    "title": "NVIDIA Corporation-Aktie: Analysten sehen weiter Fantasie nach Zahlen",
                    "snippet": "Analysten sehen nach den Zahlen weiter Fantasie in der Nvidia-Aktie.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title="NVIDIA Corporation-Aktie: Analysten sehen weiter Fantasie nach Zahlen",
            text=(
                "NVIDIA Corporation-Aktie: Analysten sehen weiter Fantasie nach Zahlen. "
                "Boerse, Kurse, Aktienkurse, Analysten und Marktdaten zur Nvidia Corporation. "
                "Die Aktie reagiert nach den Quartalszahlen auf neue Einschaetzungen."
            ),
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.single_verified_news("aktuelle Nachrichten zu Nvidia?")

    assert result.status == "no_source"
    assert any("financial_news_source" in item["reasons"] for item in pipeline.last_search_metadata["rejected_sources"])


@pytest.mark.asyncio
async def test_stock_site_company_results_article_is_rejected_for_general_news():
    source_url = "https://www.boersennews.de/nachrichten/artikel/boersennews/nvidia-nach-zahlen-im-minus-warum-anleger-trotzdem-optimistisch-bleiben/5154112"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": source_url,
                    "title": "Nvidia nach Zahlen: Rekordumsatz im ersten Quartal",
                    "snippet": (
                        "Nvidia meldet Quartalszahlen mit starkem Umsatzwachstum. "
                        "Haupttreiber bleibt das Geschaeft mit Rechenzentren und KI-Chips."
                    ),
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                "Nvidia meldet im ersten Quartal des Geschaeftsjahres Rekordumsatz. "
                "Das Geschaeft mit Rechenzentren und KI-Chips bleibt der wichtigste Wachstumstreiber. "
                "Der Detailartikel ordnet ein, warum die Nachfrage nach KI-Beschleunigern trotz hoher Erwartungen "
                "weiter stark ist und welche Rolle neue Blackwell-Systeme fuer den Ausblick spielen."
            ),
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.single_verified_news("aktuelle Nachrichten zu Nvidia?")

    assert result.status == "no_source"
    assert any("financial_news_source" in item["reasons"] for item in pipeline.last_search_metadata["rejected_sources"])


@pytest.mark.asyncio
async def test_official_company_financial_results_are_valid_company_news():
    source_url = "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2027"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": source_url,
                    "title": "NVIDIA Announces Financial Results for First Quarter Fiscal 2027 | NVIDIA Newsroom",
                    "snippet": (
                        "NVIDIA erzielte einen Rekordumsatz von 81,6 Milliarden US-Dollar. "
                        "Die Nachfrage nach Blackwell-Systemen bleibt hoch."
                    ),
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return PageFetchResult(
            url=candidate.url,
            final_url=candidate.url,
            status_code=200,
            title="NVIDIA Announces Financial Results for First Quarter Fiscal 2027 | NVIDIA Newsroom",
            text=(
                "NVIDIA announced financial results for the first quarter of fiscal 2027. "
                "NVIDIA reported record revenue of 81.6 billion dollars, up 85 percent from a year ago. "
                "Demand for Blackwell systems and data center AI infrastructure remained high."
            ),
            language_hint="en",
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.single_verified_news("aktuelle Nachrichten zu Nvidia?")

    assert result.status == "ok"
    assert result.fact is not None
    assert result.fact.source.canonical_url == source_url
    assert "financial_news_source" not in result.fact.source.rejection_reasons


@pytest.mark.asyncio
async def test_unknown_stock_analysis_page_is_rejected_for_general_company_news():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.avronline.de/nachrichten/news-views-markets/nvidia-aktie-2026-ki-boom-analyse-prognose/20539",
                    "title": "Nvidia Aktie 2026: Warum der KI-Champion weiter boomt - Aktuelle Analyse und Prognose",
                    "snippet": "Im Mai 2026 notiert die Aktie bei rund 191 bis 194 Euro und hat in den vergangenen Monaten zugelegt.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title="Nvidia Aktie 2026: Warum der KI-Champion weiter boomt - Aktuelle Analyse und Prognose",
            text=(
                "Nvidia Aktie 2026: Warum der KI-Champion weiter boomt. "
                "News, Views & Markets berichtet ueber Kurs, Aktie, Analyse und Prognose. "
                "Im Mai 2026 notiert die Aktie bei rund 191 bis 194 Euro."
            ),
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.single_verified_news("aktuelle Nachrichten zu Nvidia?")

    assert result.status == "no_source"
    assert any("financial_news_source" in item["reasons"] for item in pipeline.last_search_metadata["rejected_sources"])


@pytest.mark.asyncio
async def test_low_value_translated_market_aggregator_is_rejected_for_general_news():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://eu.36kr.com/de/p/3818435292857480",
                    "title": "NVIDIA: Unter Konkurrenzdruck und AI-Aenderungen",
                    "snippet": "Nvidia veroeffentlichte Ergebnisse fuer das erste Quartal des Geschaeftsjahres 2027.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title="NVIDIA: Unter Konkurrenzdruck und AI-Aenderungen",
            text=(
                "海豚投研 2026-05-21 Die Herrscher der Rechenleistung werden von der Kost-Nutzen-Ratio umzingelt. "
                "Nvidia hat nach dem Boersenschluss an der amerikanischen Boerse die Ergebnisse veroeffentlicht."
            ),
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.single_verified_news("aktuelle Nachrichten zu Nvidia?")

    assert result.status == "no_source"
    assert any("low_value_host" in item["reasons"] for item in pipeline.last_search_metadata["rejected_sources"])


@pytest.mark.asyncio
async def test_comdirect_finance_source_is_rejected_for_general_company_news():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.comdirect.de/inf/news/detail.html?CIF_Check=true&ID_NEWS=1162575593",
                    "title": "Nvidia beschleunigt Wachstum mit 85 Prozent Umsatzplus | comdirect Informer",
                    "snippet": "Quelle: comdirect Informer / dpa-AFX. Beispielhafter Link basierend auf den Suchdaten.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title="Nvidia beschleunigt Wachstum mit 85 Prozent Umsatzplus | comdirect Informer",
            text=(
                "Nvidia beschleunigt Wachstum mit 85 Prozent Umsatzplus. "
                "Quelle: comdirect Informer / dpa-AFX. Beispielhafter Link basierend auf den Suchdaten."
            ),
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.single_verified_news("aktuelle Nachrichten Nvidia")

    assert result.status == "no_source"
    rejected = pipeline.last_search_metadata["rejected_sources"]
    assert any("financial_news_source" in item["reasons"] for item in rejected)
    assert any("low_signal_page" in item["reasons"] for item in rejected)


@pytest.mark.asyncio
async def test_general_news_query_topic_score_ignores_news_words():
    source_url = "https://www.computerbase.de/news/internet/nvidia-telekom-sap-deutsche-ki-cloud-mit-10-000-gpus-geht-anfang-2026-online.94903/"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": source_url,
                    "title": "Nvidia, Telekom und SAP: Deutsche KI-Cloud geht Anfang 2026 online",
                    "snippet": "Nvidia liefert GPUs fuer eine deutsche KI-Cloud von Telekom und SAP.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title="Nvidia, Telekom und SAP: Deutsche KI-Cloud geht Anfang 2026 online",
            text=(
                "Nvidia, Telekom und SAP bauen eine deutsche KI-Cloud mit 10.000 GPUs. "
                "Die Plattform soll Anfang 2026 online gehen und Unternehmen Rechenleistung fuer KI-Anwendungen bieten."
            ),
        )

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("aktuelle Nachrichten Nvidia")

    assert result.status == "ok"
    assert result.fact is not None
    assert result.fact.source.topic_match_score == 1.0


@pytest.mark.asyncio
async def test_english_non_official_source_is_rejected_for_german_news_query():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.fool.com/investing/2026/05/24/nvidia-dividend-raise-buy-ai-growth-stock",
                    "title": "Nvidia raises dividend after AI growth",
                    "snippet": "Nvidia raises its dividend after another quarter of AI growth.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return PageFetchResult(
            url=candidate.url,
            final_url=candidate.url,
            status_code=200,
            title="Nvidia raises dividend after AI growth",
            text=(
                "Nvidia raises its dividend after another quarter of AI growth. "
                "The company reported strong demand for AI accelerators and data center products."
            ),
            language_hint="en",
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.single_verified_news("aktuelle Nachrichten zu Nvidia?")

    assert result.status == "no_source"
    assert any(
        "non_german_non_official_source" in item["reasons"]
        for item in pipeline.last_search_metadata["rejected_sources"]
    )


@pytest.mark.asyncio
async def test_unofficial_brand_host_is_rejected_for_general_company_news():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://chatopenai.de/news/gpt-55-agentenarbeit-alltag",
                    "title": "GPT 5.5 bringt Agentenarbeit in den Alltag - ChatGPT Deutsch",
                    "snippet": "Laut OpenAI wird GPT-5.5 in ChatGPT und Codex ausgerollt.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title="GPT 5.5 bringt Agentenarbeit in den Alltag - ChatGPT Deutsch",
            text=(
                "GPT 5.5 bringt Agentenarbeit in den Alltag. Laut OpenAI wird GPT-5.5 in ChatGPT "
                "und Codex fuer Plus, Pro, Business und Enterprise ausgerollt. Diese Newsseite "
                "erklaert ChatGPT Prompts, Apps und Accounts."
            ),
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.single_verified_news("was gibt es neues zu OpenAI?")

    assert result.status == "no_source"
    assert any("unofficial_brand_host" in item["reasons"] for item in pipeline.last_search_metadata["rejected_sources"])


@pytest.mark.asyncio
async def test_english_official_source_can_pass_when_no_german_source_exists():
    source_url = "https://www.nvidia.com/en-us/about-nvidia/blog/nvidia-launches-new-ai-platform/"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": source_url,
                    "title": "NVIDIA launches new AI platform",
                    "snippet": "NVIDIA launches a new AI platform for enterprise developers.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return PageFetchResult(
            url=candidate.url,
            final_url=candidate.url,
            status_code=200,
            title="NVIDIA launches new AI platform",
            text=(
                "NVIDIA launches a new AI platform for enterprise developers. "
                "The platform supports data center acceleration, AI software, and developer tools for companies. "
                "NVIDIA says the release is designed to help teams build, deploy, and operate AI applications "
                "across enterprise infrastructure with updated software, hardware support, and cloud integrations."
            ),
            language_hint="en",
        )

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("aktuelle Nachrichten zu Nvidia?")

    assert result.status == "ok"
    assert result.fact is not None
    assert result.fact.source.canonical_url == source_url.rstrip("/")


@pytest.mark.asyncio
async def test_topic_and_financial_report_pages_are_rejected():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.zdfheute.de/thema/apple-112.html",
                    "title": "Apple - Aktuelle Nachrichten und Hintergründe",
                    "snippet": "Apple News und Hintergruende.",
                },
                {
                    "url": "https://www.businessinsider.de/themen/apple",
                    "title": "Apple - News & Infos von Business Insider Deutschland",
                    "snippet": "Apple News und Infos.",
                },
                {
                    "url": "https://investor.nvidia.com/financial-info/financial-reports/default.aspx",
                    "title": "NVIDIA Corporation - Financial Reports",
                    "snippet": "NVIDIA financial reports.",
                },
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text=f"{candidate.title}. Microsoft Apple NVIDIA News.")

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Apple?")

    assert result.status == "no_source"
    assert render_single_verified_news(result) == NO_SOURCE_TEXT


@pytest.mark.asyncio
async def test_nested_news_listing_path_is_rejected():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.macwelt.de/apple/news",
                    "title": "Apple News",
                    "snippet": "Apple hat ein Update veroeffentlicht.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title="Apple News",
            text="Apple News, Tests, Ratgeber und aktuelle Meldungen. Apple hat ein Update veroeffentlicht.",
        )

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Apple?")

    assert result.status == "no_source"
    assert render_single_verified_news(result) == NO_SOURCE_TEXT


@pytest.mark.asyncio
async def test_paywall_marker_does_not_match_unrelated_host_suffix_text():
    source_url = "https://www.macwelt.de/news/apple-veroeffentlicht-ios-update-123.html"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": source_url,
                    "title": "Apple veroeffentlicht iOS-Update",
                    "snippet": "Apple veroeffentlicht ein neues iOS-Update fuer iPhones.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title="Apple veroeffentlicht iOS-Update",
            text=(
                "Apple veroeffentlicht ein neues iOS-Update fuer iPhones. Das Update schliesst mehrere "
                "Sicherheitsluecken und bringt Verbesserungen fuer die Installation auf aktuellen Geraeten. "
                "Nutzerinnen und Nutzer koennen das Update ueber die Systemeinstellungen laden."
            ),
        )

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Apple?")

    assert result.fact is not None
    assert "paywall_host" not in result.fact.source.rejection_reasons


@pytest.mark.asyncio
async def test_thin_or_fetch_error_pages_are_rejected_with_reasons():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.computerwoche.de/a/microsoft-ki,123456",
                    "title": "Microsoft und EY bauen KI-Kooperation aus",
                    "snippet": "Microsoft und EY bauen ihre KI-Kooperation aus.",
                },
                {
                    "url": "https://www.computerwoche.de/a/microsoft-copilot,789",
                    "title": "Microsoft Copilot News",
                    "snippet": "Microsoft Copilot News.",
                },
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        if "123456" in candidate.url:
            return PageFetchResult(
                url=candidate.url,
                final_url=candidate.url,
                status_code=200,
                title=candidate.title,
                text="Microsoft EY.",
                language_hint="de",
            )
        return PageFetchResult(
            url=candidate.url,
            final_url=candidate.url,
            status_code=None,
            title=candidate.title,
            text="",
            language_hint="de",
            error="timeout",
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.single_verified_news("was gibt es neues zu Microsoft?")
    rejected = pipeline.last_search_metadata["rejected_sources"]

    assert result.status == "no_source"
    assert any("thin_page" in item["reasons"] for item in rejected)
    assert any("fetch_error" in item["reasons"] for item in rejected)


@pytest.mark.asyncio
async def test_verified_source_preserves_published_at_metadata():
    source_url = "https://www.computerwoche.de/a/microsoft-und-ey-bauen-ki-kooperation-aus,123456"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": source_url,
                    "title": "Microsoft und EY bauen KI-Kooperation aus",
                    "snippet": "Microsoft und EY erweitern ihre Zusammenarbeit rund um KI.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return PageFetchResult(
            url=candidate.url,
            final_url=candidate.url,
            status_code=200,
            title="Microsoft und EY bauen KI-Kooperation aus",
            text=(
                "Microsoft und EY bauen ihre KI-Kooperation aus. Die Partner wollen Unternehmen "
                "bei der Einfuehrung von KI-Loesungen unterstuetzen und neue Dienste bereitstellen."
            ),
            language_hint="de",
            published_at="2026-05-24T08:00:00+02:00",
        )

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Microsoft?")

    assert result.fact is not None
    assert result.fact.source.published_at == "2026-05-24T08:00:00+02:00"


@pytest.mark.asyncio
async def test_google_search_page_is_rejected_before_fetch():
    fetched = False

    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.google.com/search?q=Microsoft+News",
                    "title": "Google Search",
                    "snippet": "Microsoft News",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        nonlocal fetched
        fetched = True
        return _page(candidate.url)

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Microsoft?")

    assert result.status == "no_source"
    assert fetched is False


@pytest.mark.asyncio
async def test_vertex_redirect_is_not_rendered():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/microsoft",
                    "title": "computerwoche.de",
                    "snippet": "Microsoft und EY bauen KI-Kooperation aus.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url)

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Microsoft?")
    rendered = render_single_verified_news(result)

    assert result.status == "no_source"
    assert "vertexaisearch.cloud.google.com" not in rendered


@pytest.mark.asyncio
async def test_german_source_is_preferred_over_equivalent_english_source():
    german_url = "https://www.computerwoche.de/a/microsoft-und-ey-bauen-ki-kooperation-aus,123456"
    english_url = "https://www.microsoft.com/en-us/industry/blog/microsoft-ey-ai-partnership"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": english_url,
                    "title": "Microsoft and EY expand AI partnership",
                    "snippet": "Microsoft and EY expand their AI partnership.",
                },
                {
                    "url": german_url,
                    "title": "Microsoft und EY bauen KI-Kooperation aus",
                    "snippet": "Microsoft und EY erweitern ihre KI-Kooperation.",
                },
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        if candidate.url == english_url:
            return PageFetchResult(
                url=candidate.url,
                final_url=candidate.url,
                status_code=200,
                title="Microsoft and EY expand AI partnership",
                text="Microsoft and EY expand their AI partnership for enterprise customers.",
                language_hint="en",
            )
        return _page(candidate.url)

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Microsoft?")

    assert result.fact is not None
    assert result.fact.source.canonical_url == german_url


@pytest.mark.asyncio
async def test_no_validated_hit_returns_honest_no_source_answer():
    async def search(_query):
        return {"sources": [], "metadata": {"provider": "openai"}}

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url)

    result = await WebSearchV3Pipeline(search, fetch).single_verified_news("was gibt es neues zu Microsoft?")

    assert result.status == "no_source"
    assert render_single_verified_news(result) == "Ich habe aktuell keine ausreichend belastbare Quelle gefunden."


def test_gemini_and_openai_normalization_return_same_candidate_shape():
    gemini = normalize_gemini_grounding_response(
        {
            "candidates": [
                {
                    "groundingMetadata": {
                        "groundingChunks": [
                            {"web": {"uri": "https://www.computerwoche.de/a/microsoft-ki,123", "title": "Computerwoche"}}
                        ],
                        "groundingSupports": [
                            {
                                "segment": {"text": "Microsoft und EY erweitern ihre KI-Kooperation."},
                                "groundingChunkIndices": [0],
                            }
                        ],
                    }
                }
            ]
        }
    )
    openai = normalize_openai_response_output(
        [
            {
                "type": "message",
                "content": [
                    {
                        "text": "Microsoft und EY erweitern ihre KI-Kooperation.",
                        "annotations": [
                            {
                                "type": "url_citation",
                                "url": "https://www.computerwoche.de/a/microsoft-ki,123",
                                "title": "Computerwoche",
                            }
                        ],
                    }
                ],
            }
        ]
    )

    for candidate in [gemini[0], openai[0]]:
        assert isinstance(candidate, SearchCandidate)
        assert candidate.url == "https://www.computerwoche.de/a/microsoft-ki,123"
        assert candidate.title == "Computerwoche"
        assert candidate.provider in {"gemini", "openai"}


def test_candidates_from_websearch_result_prefers_gemini_grounding_metadata():
    result = {
        "sources": [
            {
                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/ignored",
                "title": "Ignored redirect",
            }
        ],
        "metadata": {
            "provider": "gemini",
            "grounding_metadata": {
                "groundingChunks": [
                    {"web": {"uri": "https://www.computerwoche.de/a/microsoft-ki,123", "title": "Computerwoche"}}
                ],
                "groundingSupports": [
                    {
                        "segment": {"text": "Microsoft und EY erweitern ihre KI-Kooperation."},
                        "groundingChunkIndices": [0],
                    }
                ],
            },
        },
    }

    candidates = candidates_from_websearch_result(result)

    assert len(candidates) == 1
    assert candidates[0].provider == "gemini"
    assert candidates[0].url == "https://www.computerwoche.de/a/microsoft-ki,123"
    assert "KI-Kooperation" in candidates[0].snippet


def test_candidates_from_websearch_result_prefers_openai_url_citations():
    result = {
        "sources": [
            {
                "url": "https://example.com/generic-news",
                "title": "Generic fallback",
            }
        ],
        "metadata": {
            "provider": "openai",
            "url_citations": [
                {
                    "url": "https://www.computerwoche.de/a/microsoft-ki,123",
                    "title": "Computerwoche",
                    "text": "Microsoft und EY erweitern ihre KI-Kooperation.",
                }
            ],
        },
    }

    candidates = candidates_from_websearch_result(result)

    assert len(candidates) == 1
    assert candidates[0].provider == "openai"
    assert candidates[0].url == "https://www.computerwoche.de/a/microsoft-ki,123"
    assert candidates[0].title == "Computerwoche"


def test_fact_extractor_filters_repeated_title_and_navigation_noise():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://blogs.nvidia.de/global-nemotron-coalition",
        canonical_url="https://blogs.nvidia.de/global-nemotron-coalition",
        title="NVIDIA gruendet Nemotron-Koalition fuehrender KI-Labore aus aller Welt | NVIDIA",
        source_label="blogs.nvidia.de",
        snippet=(
            "NVIDIA gruendet Nemotron-Koalition fuehrender KI-Labore aus aller Welt | NVIDIA "
            "Zum Inhalt springen Suche nach: Toggle Search Startseite KI Rechenzentrum. "
            "NVIDIA will mit der Koalition offene Frontier-Modelle fuer Unternehmen vorantreiben."
        ),
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "aktuelle Nachrichten zu Nvidia?")

    assert "Zum Inhalt springen" not in fact.summary
    assert "Toggle Search" not in fact.summary
    assert "offene Frontier-Modelle" in fact.summary


def test_fact_extractor_falls_back_when_snippet_is_navigation_noise():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://www.heise.de/news/iOS-26-4-ist-da-Diese-Neuerungen-bringen-die-Apple-Updates-11223122.html",
        canonical_url="https://www.heise.de/news/iOS-26-4-ist-da-Diese-Neuerungen-bringen-die-Apple-Updates-11223122.html",
        title="iOS 26.4 ist da: Diese Neuerungen bringen die Apple-Updates | heise online",
        source_label="heise.de",
        snippet=(
            "iOS 26.4 ist da: Diese Neuerungen bringen die Apple-Updates | heise online "
            "heise+ entdecken Suchen Abo Suchen Alle Magazine im Browser lesen IT News Newsticker "
            "Hintergruende Ratgeber Testberichte Meinungen Online-Magazine."
        ),
        page_excerpt=(
            "Apple hat iOS 26.4 und weitere Updates freigegeben. "
            "Die Aktualisierungen bringen neue Funktionen fuer iPhone und iPad sowie mehrere Fehlerkorrekturen."
        ),
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "was gibt es neues zu Apple?")

    assert "heise+ entdecken" not in fact.summary
    assert "Alle Magazine" not in fact.summary
    assert "Apple hat iOS 26.4" in fact.summary


def test_fact_extractor_falls_back_from_support_navigation_noise():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://support.microsoft.com/de-de/topic/kb5087544",
        canonical_url="https://support.microsoft.com/de-de/topic/kb5087544",
        title="Mai 2026 - KB5087544: Windows-Update",
        source_label="support.microsoft.com",
        snippet=(
            "Mai 2026 - KB5087544: Windows-Update Verwandte Themen Updateverlauf Windows 11 "
            "Support Microsoft Konto Datenschutz."
        ),
        page_excerpt=(
            "Microsoft veroeffentlicht mit KB5087544 ein Windows-Update fuer Mai 2026. "
            "Das Update behebt Fehler und bringt Sicherheitsverbesserungen fuer unterstuetzte Systeme."
        ),
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "was gibt es neues zu Microsoft?")

    assert "Verwandte Themen" not in fact.summary
    assert "Updateverlauf" not in fact.summary
    assert "Microsoft veroeffentlicht" in fact.summary


def test_fact_extractor_does_not_split_dates_as_sentence_boundaries():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://news.microsoft.com/source/emea/2026/05/surface-business",
        canonical_url="https://news.microsoft.com/source/emea/2026/05/surface-business",
        title="Microsoft kuendigt neue Surface-Geraete an",
        source_label="news.microsoft.com",
        snippet=(
            "Hardware: Neue Surface-Geraete fuer Unternehmen. "
            "Microsoft hat am 19. Mai 2026 neue Modelle seiner Surface-Reihe vorgestellt, "
            "die speziell auf Geschaeftskunden und KI-Anwendungen zugeschnitten sind."
        ),
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "was gibt es neues zu Microsoft?")

    assert "19. Mai 2026" in fact.summary
    assert "Surface-Reihe" in fact.summary


def test_fact_extractor_uses_only_first_numbered_item():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://www.microsoft.com/de-de/news/detail",
        canonical_url="https://www.microsoft.com/de-de/news/detail",
        title="Microsoft stellt neue Cloud-Funktion vor",
        source_label="microsoft.com",
        snippet=(
            "1. Microsoft stellt eine neue Cloud-Funktion fuer Unternehmenskunden vor. "
            "Die Funktion soll Teams beim Betrieb von KI-Anwendungen helfen. "
            "2. Microsoft meldet neue Surface-Geraete. "
            "3. Microsoft kuendigt Gaming-Neuigkeiten an."
        ),
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "was gibt es neues zu Microsoft?")

    assert "Cloud-Funktion" in fact.summary
    assert "Surface" not in fact.summary
    assert "Gaming" not in fact.summary


def test_fact_extractor_rejects_provider_citation_noise_in_summary():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://borncity.com/news/ey-und-microsoft-investieren-eine-milliarde-in-ki-revolution",
        canonical_url="https://borncity.com/news/ey-und-microsoft-investieren-eine-milliarde-in-ki-revolution",
        title="EY und Microsoft investieren eine Milliarde in KI-Revolution",
        source_label="borncity.com",
        snippet=(
            "Quelle: [BornCity: Microsoft raeumt Copilot-Button weg](https://borncity.com/news/copilot). "
            "Zuvor hatten Nutzer bemaengelt, dass das schwebende Symbol wichtige Datenzellen verdeckte."
        ),
        page_excerpt=(
            "EY und Microsoft investieren eine Milliarde in KI-Revolution. "
            "Die Unternehmen erweitern ihre Zusammenarbeit rund um kuenstliche Intelligenz und Copilot."
        ),
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "was gibt es neues zu Microsoft?")

    assert "Quelle:" not in fact.summary
    assert "](" not in fact.summary
    assert "EY und Microsoft" in fact.summary


def test_fact_extractor_rejects_unclosed_provider_citation_noise():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://borncity.com/news/microsoft-ueberarbeitet-copilot-neue-steuerung-fuer-office-profis",
        canonical_url="https://borncity.com/news/microsoft-ueberarbeitet-copilot-neue-steuerung-fuer-office-profis",
        title="Microsoft ueberarbeitet Copilot: Neue Steuerung fuer Office-Profis",
        source_label="borncity.com",
        snippet=(
            "Copilot-Update: Neue Steuerung fuer Office-Anwendungen Microsoft hat im Mai 2026 "
            "ein umfangreiches Update fuer den KI-Assistenten Copilot in der Office-Suite veroeffentlicht. "
            "[borncity.com - Microsoft ueberarbeitet C"
        ),
        page_excerpt="Microsoft ueberarbeitet Copilot und fuehrt neue Steuerungen fuer Office-Anwendungen ein.",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "was gibt es neues zu Microsoft?")

    assert "[borncity.com" not in fact.summary
    assert "Copilot-Update" in fact.summary


def test_fact_extractor_does_not_repeat_curated_briefing_title_as_summary():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://www.filmstarts.de/nachrichten/1000204924.html",
        canonical_url="https://www.filmstarts.de/nachrichten/1000204924.html",
        title=(
            "Neu auf Netflix im Juni 2026: Die beste Fantasy-Trilogie aller Zeiten, "
            "eine der lustigsten Serien ueberhaupt & noch viel mehr - Kino News"
        ),
        source_label="filmstarts.de",
        snippet="Neu auf Netflix im Juni 2026: Die beste Fantasy-Trilogie aller Zeiten.",
        page_excerpt="Der Artikel nennt unter anderem \"Der Herr der Ringe\", \"Brooklyn Nine-Nine\" und \"Spider-Man\".",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
        source_type="curated_briefing",
        evidence_score=0.74,
    )

    fact = extract_supported_fact(source, "was gibt es neues im Kino?")

    assert fact.summary != fact.title + "."
    assert "Der Herr der Ringe" in fact.summary


def test_fact_extractor_avoids_generic_trailer_headline_as_film_title():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://kinocheck.de/news/5lujqe/diese-neuen-film-trailer-kommen-bald-2025-2026",
        canonical_url="https://kinocheck.de/news/5lujqe/diese-neuen-film-trailer-kommen-bald-2025-2026",
        title="Diese neuen Trailer kommen bald! (2025 & 2026) - Film & Serien News | KinoCheck",
        source_label="kinocheck.de",
        snippet="Diese neuen Trailer kommen bald. Erfolgreich in den deutschen Kinos gestartet.",
        page_excerpt="Film & Serien News mit neuen Trailern, Ankuendigungen und kommenden Kinofilmen.",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
        source_type="curated_briefing",
        evidence_score=0.74,
    )

    fact = extract_supported_fact(source, "was gibt es neues im Kino?")

    assert "unter anderem Diese neuen Trailer" not in fact.summary
    assert "erfolgreich in den deutschen Kinos gestartet" not in fact.summary


def test_fact_extractor_mentions_gaming_titles_from_grounded_release_snippet():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://www.gamepro.de/artikel/state-of-play-juni-2026-sony,3453326.html",
        canonical_url="https://www.gamepro.de/artikel/state-of-play-juni-2026-sony,3453326.html",
        title="State of Play im Juni 2026 offiziell angekuendigt: Sony verspricht PS5-Ankuendigungen",
        source_label="gamepro.de",
        snippet=(
            "PlayStation: State of Play & Marvel's Wolverine. "
            "Sony hat fuer den fruehen Juni ein grosses Event angekuendigt. "
            "* **State of Play Juni 2026:** Sony hat offiziell eine neue Ausgabe angekuendigt. "
            "* **Marvel's Wolverine:** Die Show soll einen ausfuehrlichen Einblick bieten."
        ),
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "was gibt es neues im Gaming?")

    assert "Gaming-Neuigkeiten" in fact.summary
    assert "Marvel's Wolverine" in fact.summary


def test_fact_extractor_uses_gaming_title_when_excerpt_starts_with_navigation():
    source = VerifiedSource(
        url="https://diezukunft.de/news/game/gaming-highlights-im-mai-2026-1-teil",
        canonical_url="https://diezukunft.de/news/game/gaming-highlights-im-mai-2026-1-teil",
        title="Gaming-Highlights im Mai 2026 (1. Teil) | Die Zukunft",
        source_label="diezukunft.de",
        snippet="",
        page_excerpt=(
            "Navigation Shop Login Newsletter Buch Comic Film Gadget Game Science Kolumne News. "
            "Gaming-Highlights im Mai 2026 stellt aktuelle Spiele und Releases fuer PC und Konsole vor."
        ),
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "was gibt es neues im Gaming?")

    assert "Navigation" not in fact.summary
    assert "Gaming-Highlights im Mai 2026" in fact.summary


def test_fact_extractor_uses_title_fallback_instead_of_empty_details_phrase():
    source = VerifiedSource(
        url="https://www.netzwelt.de/news/253987-137-luecken-windows-gefunden-microsoft-word-teams-copilot-betroffen.html",
        canonical_url="https://www.netzwelt.de/news/253987-137-luecken-windows-gefunden-microsoft-word-teams-copilot-betroffen.html",
        title="137 Luecken in Windows gefunden: Microsoft Word, Teams und Copilot betroffen",
        source_label="netzwelt.de",
        snippet="Zum Inhalt springen Navigation Newsletter Suche",
        page_excerpt="Zum Inhalt springen Navigation Newsletter Suche Anzeigen Datenschutz Footer",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "Microsoft aktuelle Nachrichten 2026")

    assert "Details stehen" not in fact.summary
    assert "137 Luecken" in fact.summary


def test_fact_extractor_mentions_film_titles_from_grounded_release_snippet():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://www.kino-zeit.de/news/kinostarts-mai-2026",
        canonical_url="https://www.kino-zeit.de/news/kinostarts-mai-2026",
        title="Kinostarts der Woche: Neue Filme im Kino",
        source_label="kino-zeit.de",
        snippet=(
            "Neue Kinostarts im Mai. "
            "* **Das gewisse Etwas:** startet diese Woche. "
            "* **Passenger:** kommt neu in die Kinos."
        ),
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "was gibt es neues im Kino?")

    assert "Film-/Kino-Neuigkeiten" in fact.summary
    assert "Das gewisse Etwas" in fact.summary
    assert "Passenger" in fact.summary


def test_fact_extractor_uses_known_film_site_title_for_film_summary():
    source = VerifiedSource(
        url="https://www.filmstarts.de/kritiken/1000027770.html",
        canonical_url="https://www.filmstarts.de/kritiken/1000027770.html",
        title="Das gewisse Etwas - Film 2026",
        source_label="filmstarts.de",
        snippet="Babygirl, Die Eiskoenigin 3, Charts, alle Filme, Serien, News, Trailer.",
        page_excerpt="Kino Die besten Filme Filme im Kino Kommende Filme Premieren Kinoprogramm.",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    fact = extract_supported_fact(source, "was gibt es neues im Kino?")

    assert "Das gewisse Etwas" in fact.summary
    assert "Charts" not in fact.summary


@pytest.mark.asyncio
async def test_non_german_non_official_tech_site_is_rejected_for_german_news_query():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://wccftech.com/nvidia-moves-gaming-segment-under-edge-computing-gaming-slows-down-due-to-elevated-prices",
                    "title": (
                        "NVIDIA Moves Gaming Segment Under Edge Computing, Posts Revenue Growth "
                        "But Gaming GPUs Slow Down Due To Elevated Memory Prices"
                    ),
                    "snippet": "Mai 2026 veroeffentlichte Nvidia seine Zahlen fuer das erste Geschaeftsquartal 2027.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                "NVIDIA moves its gaming segment under edge computing. The company reported revenue growth "
                "from Blackwell workstations while gaming GPUs slowed down due to elevated memory prices."
            ),
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.single_verified_news("aktuelle Nachrichten zu Nvidia?")

    assert result.status == "no_source"
    assert any(
        "non_german_non_official_source" in item["reasons"]
        for item in pipeline.last_search_metadata["rejected_sources"]
    )


def test_topic_labeler_assigns_expected_labels():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://example.com/openai-klage",
        canonical_url="https://example.com/openai-klage",
        title="OpenAI steht wegen Copyright vor Gericht",
        source_label="example.com",
        snippet="Ein Gericht verhandelt eine Copyright-Klage gegen OpenAI.",
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    assert label_source_topic(source) == "Recht & Regulierung"


def test_topic_labeler_does_not_let_nav_dax_override_product_title():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://www.t-online.de/digital/aktuelles/id_101243290/neue-ki-version-openai-tauscht-chatgpts-standardmodell-aus.html",
        canonical_url="https://www.t-online.de/digital/aktuelles/id_101243290/neue-ki-version-openai-tauscht-chatgpts-standardmodell-aus.html",
        title="Neue KI-Version: OpenAI tauscht ChatGPTs Standardmodell aus",
        source_label="t-online.de",
        snippet="Neue KI-Version: OpenAI tauscht ChatGPTs Standardmodell aus Wetter DAX Jobsuche Partnersuche Telefonverz.",
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    assert label_source_topic(source) == "Produkt & Technik"


def test_topic_labeler_assigns_public_sector_label():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://www.bayern.de/digitalminister-mehring-eroeffnet-ki-werkstatt-fuer-mittelstand-von-openai-in-muenchen",
        canonical_url="https://www.bayern.de/digitalminister-mehring-eroeffnet-ki-werkstatt-fuer-mittelstand-von-openai-in-muenchen",
        title="Digitalminister Mehring eroeffnet KI-Werkstatt fuer Mittelstand von OpenAI in Muenchen",
        source_label="bayern.de",
        snippet="Innovation lebt von Anwendung.",
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    assert label_source_topic(source) == "Politik & Standort"


def test_topic_labeler_assigns_film_specific_label():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://www.moviejones.de/news/news-neuer-trailer-zu-minions-monsters_50459.html",
        canonical_url="https://www.moviejones.de/news/news-neuer-trailer-zu-minions-monsters_50459.html",
        title="Sie sind wieder da: Neuer Trailer zu Minions & Monsters bringt Chaos!",
        source_label="moviejones.de",
        snippet="Der neue Trailer zeigt konkrete Szenen aus Minions & Monsters.",
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    assert label_source_topic(source) == "Trailer & Filmnews"


def test_topic_labeler_prefers_film_source_over_incidental_game_marker():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://kinocheck.de/news/5lujqe/diese-neuen-film-trailer-kommen-bald-2025-2026",
        canonical_url="https://kinocheck.de/news/5lujqe/diese-neuen-film-trailer-kommen-bald-2025-2026",
        title="Diese neuen Trailer kommen bald! (2025 & 2026) - Film & Serien News",
        source_label="kinocheck.de",
        snippet="Neue Filmtrailer, Squid Game und weitere Film- und Serien-News.",
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    assert label_source_topic(source) == "Trailer & Filmnews"


def test_topic_labeler_prefers_film_content_on_gaming_site_when_no_gaming_signal():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://www.gamepro.de/artikel/toy-story-5-release-streaming-mehr-alle-wichtigen-infos,3451227.html",
        canonical_url="https://www.gamepro.de/artikel/toy-story-5-release-streaming-mehr-alle-wichtigen-infos,3451227.html",
        title="Toy Story 5: Release, Streaming & mehr - Alle wichtigen Infos zur naechsten Fortsetzung der Pixar-Reihe",
        source_label="gamepro.de",
        snippet="Der Kinofilm Toy Story 5 hat einen Release-Termin und neue Infos zur Pixar-Fortsetzung.",
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    assert label_source_topic(source) == "Kinostarts"


def test_topic_labeler_treats_heldenderfreizeit_game_releases_as_gaming():
    from backend.services.websearch_v3.models import VerifiedSource

    source = VerifiedSource(
        url="https://www.heldenderfreizeit.com/alle-game-releases-2026",
        canonical_url="https://www.heldenderfreizeit.com/alle-game-releases-2026",
        title="Game Releases 2026 - alle neuen Spiele immer im Blick",
        source_label="heldenderfreizeit.com",
        snippet="Paralives fuer PC und weitere neue Spiele erscheinen 2026.",
        page_excerpt="",
        language="de",
        published_at=None,
        is_reachable=True,
        is_detail_page=True,
        topic_match_score=1.0,
        source_quality_score=1.0,
    )

    assert label_source_topic(source) == "Spiele-Releases"


def test_gemini_v3_phase1_prompt_is_short_and_source_first():
    prompt = _build_phase1_prompt("was gibt es neues zu Microsoft?")

    assert len(prompt) < 800
    assert "aktuellen Nachrichten zu Microsoft" in prompt
    assert "Verwende Google Search" in prompt
    assert "deutschsprachige Detailartikel" in prompt
    assert "Aktienkursseiten" in prompt
    assert "Englische Quellen nur" in prompt


def test_query_planner_handles_domain_news_subjects():
    assert is_simple_news_query("was gibt es neues im Kino?")
    assert is_simple_news_query("upcoming movies May June 2026 release dates")
    assert is_simple_news_query("Nvidia Q1 2026 earnings report date results")
    assert is_broad_briefing_query("was gibt es neues im Gaming?")
    assert is_broad_briefing_query("Neues im Kino aktuelle Kinostarts Deutschland Mai 2026")
    assert len(build_briefing_search_queries("was gibt es neues im Gaming?")) == 4
    kino_queries = build_briefing_search_queries("was gibt es neues im Kino?")
    assert any("Filmtrailer" in query or "Filmankündigungen" in query for query in kino_queries)
    assert not any("Filmpreis" in query or "Festival" in query for query in kino_queries)
    assert extract_subject("was gibt es neues im Gaming?") == "Gaming"
    assert extract_subject("was gibt es neues vom FC Bayern?") == "FC Bayern"


def test_gemini_v3_prompt_has_film_and_gaming_profiles():
    film_prompt = _build_phase1_prompt("was gibt es neues im Kino?")
    gaming_prompt = _build_phase1_prompt("was gibt es neues im Gaming?")

    assert "Film- und Kinonews" in film_prompt
    assert "Keine Woerterbuecher" in film_prompt
    assert "IMDb-Kalender" in film_prompt
    assert "Gaming-News" in gaming_prompt
    assert "Keine Store-Seiten" in gaming_prompt


@pytest.mark.asyncio
async def test_two_source_mode_prefers_distinct_topic_labels_when_available():
    urls = [
        "https://www.heise.de/news/microsoft-stellt-neue-cloud-funktion-vor-987654.html",
        "https://www.computerwoche.de/a/microsoft-bringt-copilot-update,123456",
        "https://www.bayern.de/digitalminister-mehring-eroeffnet-ki-werkstatt-fuer-mittelstand-von-openai-in-muenchen",
    ]

    async def search(_query):
        return {
            "sources": [
                {
                    "url": urls[0],
                    "title": "Microsoft stellt neue Cloud-Funktion vor",
                    "snippet": "Microsoft stellt eine neue Cloud-Funktion fuer Unternehmenskunden vor.",
                },
                {
                    "url": urls[1],
                    "title": "Microsoft bringt Copilot Update fuer Teams",
                    "snippet": "Microsoft aktualisiert Copilot mit neuen KI-Funktionen fuer Teams.",
                },
                {
                    "url": urls[2],
                    "title": "Digitalminister eroeffnet Microsoft KI-Werkstatt in Muenchen",
                    "snippet": "Eine KI-Werkstatt soll den Mittelstand in Bayern unterstuetzen.",
                },
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=f"{candidate.title}. {candidate.snippet} Microsoft meldet diese Neuigkeit in Deutschland.",
        )

    result = await WebSearchV3Pipeline(search, fetch).verified_news("was gibt es neues zu Microsoft?", max_sources=2)

    assert result.status == "ok"
    assert [fact.topic_label for fact in result.facts] == ["Produkt & Technik", "Politik & Standort"]
    assert [fact.source.canonical_url for fact in result.facts] == [urls[0], urls[2]]


@pytest.mark.asyncio
async def test_dictionary_and_movie_calendar_pages_are_rejected_for_film_news():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://dict.leo.org/englisch-deutsch/upcoming",
                    "title": "upcoming - LEO: Uebersetzung im Englisch Deutsch Woerterbuch",
                    "snippet": "Lernen Sie die Uebersetzung fuer upcoming.",
                },
                {
                    "url": "https://www.imdb.com/calendar/",
                    "title": "Upcoming releases - IMDb",
                    "snippet": "IMDb calendar for upcoming releases.",
                },
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text="Kinostarts Filme Deutschland Mai Juni aktuelle Meldung Detailartikel mit vielen Informationen.",
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=2)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "low_value_host" in reasons
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_year_level_movie_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.kino.de/filme/jahre/2026",
                    "title": "Die besten Filme 2026",
                    "snippet": "Jahresuebersicht mit Filmen 2026.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text="Die besten Filme 2026. Kino Film Kinostarts Deutschland Jahresuebersicht mit vielen Filmen.",
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_streaming_guide_without_cinema_evidence():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://kinocheck.de/news/88gtcr/neu-auf-netflix-im-mai-2026-kinocheck-streaming-guide",
                    "title": "Neu auf Netflix im Mai 2026... KinoCheck Streaming Guide - Film & Serien News",
                    "snippet": "Der Streaming Guide nennt Gladiator 2, Berlin und die Dame mit dem Hermelin.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                "Neu auf Netflix im Mai 2026. KinoCheck Streaming Guide mit Filmen und Serien. "
                "Film & Serien News Deutschland mit vielen Details zu Streamingstarts."
            ),
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "streaming_guide_for_cinema_query" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_generic_filmstarts_listing_path():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://kinocheck.de/filmstarts/all/recently",
                    "title": "Aktuelle Filmstarts | KinoCheck",
                    "snippet": "Entdecke die besten Filme des kommenden Kinoprogramms.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text="Aktuelle Filmstarts KinoCheck Filmstarts Streams Filme Serien Finder App Kinoprogramm.",
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_genre_level_filmstarts_listing_path():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://kinocheck.de/filmstarts/scifi",
                    "title": "Aktuelle Filmstarts: alle Science Fiction-Filme | KinoCheck",
                    "snippet": "Eine Genre-Uebersicht mit aktuellen Science-Fiction-Filmen.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Filmstarts Science Fiction Filme Liste KinoCheck.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_cinehits_filmstarts_listing_path():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.cinehits.de/film/filmstarts.html",
                    "title": "Filmstarts Deutschland 2026",
                    "snippet": "Liste der Filmstarts in Deutschland 2026.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Filmstarts Deutschland 2026 Kino Filme Liste.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_kino_de_current_category_page():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.kino.de/filme/aktuell/komoedie",
                    "title": "Aktuell im Kino: Komödien",
                    "snippet": "Kino.de zeigt aktuelle Komödien im Kino.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Aktuell im Kino Komoedien Filme Kinoprogramm Liste.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_moviejones_year_level_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.moviejones.de/kinofilme/kinofilme-2026-seite-1.html",
                    "title": "Alle Kinofilme 2026",
                    "snippet": "Jahresuebersicht aller Kinofilme 2026.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text="Alle Kinofilme 2026 Cannes Filmfestival Goldene Palme Trailer Kino Film.",
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_moviejones_filme_year_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.moviejones.de/filme/kinofilme-2026-seite-1.html",
                    "title": "Alle Kinofilme 2026 | Moviejones",
                    "snippet": "Jahresübersicht aller Kinofilme 2026.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Alle Kinofilme 2026 Filmstarts Kino Jahresuebersicht.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("Neues im Kino aktuelle Kinostarts Deutschland Mai 2026", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_moviejones_current_cinema_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.moviejones.de/filmstarts/aktuell-im-kino/1",
                    "title": "Kinostarts 2026 - Mai | Moviejones",
                    "snippet": "Liste aktueller Kinostarts.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Kinostarts 2026 Mai Liste Filmstarts Kino.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_moviejones_month_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.moviejones.de/filmstarts/2026/mai",
                    "title": "Kinostarts 2026 - Mai | Moviejones",
                    "snippet": "Liste aktueller Kinostarts im Mai.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Kinostarts 2026 Mai Liste Filmstarts Kino.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_filmportal_event_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.filmportal.de/news/events",
                    "title": "Aktuelle Veranstaltungen | filmportal.de",
                    "snippet": "Veranstaltungen und Termine rund um Film.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Aktuelle Veranstaltungen Filmportal Events Kino Termine.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_filmportal_monthly_cinema_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.filmportal.de/news/cinema/month/202601",
                    "title": "Kinostarts | filmportal.de",
                    "snippet": "Monatsuebersicht der Kinostarts.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Kinostarts Monatsuebersicht Filme Kino Filmportal.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_filmstarts_premiere_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.filmstarts.de/filme-imkino/vorpremiere",
                    "title": "Alle Premieren im Kino - FILMSTARTS.de",
                    "snippet": "Übersicht der Vorpremieren im Kino.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Alle Premieren im Kino Filmstarts Liste.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("Neues im Kino aktuelle Kinostarts Deutschland Mai 2026", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_filmstarts_cinema_program_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.filmstarts.de/filme-imkino/kinos",
                    "title": "Filme im Kino - FILMSTARTS.de",
                    "snippet": "Kinoprogramm und laufende Filme in Kinos.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Filme im Kino Kinoprogramm Kinos Filmstarts Liste.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_calendar_kinostarts_page():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://film.kleiner-kalender.de/rubrik/kinostarts.html",
                    "title": "Kinostarts",
                    "snippet": "Kalenderuebersicht kommender Kinostarts.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Kinostarts Kalender Filme Kino Mai Juni.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Kino?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "low_value_host" in reasons


@pytest.mark.asyncio
async def test_broad_kino_rejects_epd_festivalberichte_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.epd-film.de/aktuell/festivalberichte",
                    "title": "Festivalberichte | epd Film",
                    "snippet": "Festivalberichte und Archivmeldungen.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Festivalberichte epd Film Archiv.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("Neues im Kino aktuelle Kinostarts Deutschland Mai 2026", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_gaming_rejects_sports_federation_false_positive():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.badminton.de/news/badminton/39-deutsche-meisterschaften-o35-o80-2026",
                    "title": "39. Deutsche Meisterschaften O35 - O80 2026 | Deutscher Badminton Verband",
                    "snippet": "Games-Foerderung 2026 und 120 Millionen Euro.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text="39. Deutsche Meisterschaften O35 - O80 2026 Deutscher Badminton Verband Sport Turnier.",
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Gaming?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "domain_not_primary_topic" in reasons


@pytest.mark.asyncio
async def test_company_news_rejects_source_where_company_is_not_primary_topic():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.gob.de/news/pressemitteilungen/gob-praesentiert-digitale-prozessoptimierung-und-ki-gestuetzte-erp-innovationen-auf-der-logimat-2026",
                    "title": "LogiMAT 2026: Prozessoptimierung, KI-Funktionen | Presse",
                    "snippet": "GOB praesentiert ERP-Innovationen und Prozessoptimierung auf der LogiMAT.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                "LogiMAT 2026: Prozessoptimierung, KI-Funktionen. GOB praesentiert neue ERP-Innovationen "
                "fuer Kunden, Branchenloesungen und Dienstleistungen. Microsoft wird nur in einer langen "
                "Partnerliste am Seitenende genannt."
            ),
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("Microsoft aktuelle Nachrichten 2026", max_sources=2)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "subject_not_primary_topic" in reasons


@pytest.mark.asyncio
async def test_company_news_rejects_official_region_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://news.microsoft.com/source/emea/region/germany-de?lang=de",
                    "title": "Germany Region - Source EMEA",
                    "snippet": "Microsoft Source EMEA Nachrichten aus Deutschland.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Microsoft in Deutschland Region News Uebersicht.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues zu Microsoft?", max_sources=2)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_company_news_rejects_partner_landing_page():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.infinigate.com/de/lp/h/microsoft/microsoft-news",
                    "title": "Microsoft News - Infinigate | Deutschland",
                    "snippet": "Landingpage mit Microsoft News und Partnerinformationen.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Microsoft News Infinigate Deutschland Landingpage.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues zu Microsoft?", max_sources=2)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_general_company_news_rejects_stock_site_even_with_results_markers():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.deraktionaer.de/artikel/aktien/megatrend-folger-das-haben-alle-bei-den-nvidia-zahlen-uebersehen-20401412.html",
                    "title": "Megatrend Folger: Das haben alle bei den Nvidia-Zahlen uebersehen - DER AKTIONAER",
                    "snippet": "Nvidia Zahlen, Aktie, Analysten und Kursreaktion.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Nvidia Zahlen Aktie Analysten Kurs Megatrend Folger.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("aktuelle Nachrichten zu Nvidia?", max_sources=2)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "financial_news_source" in reasons


@pytest.mark.asyncio
async def test_company_news_rejects_generic_topic_news_page():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.computerbase.de/news/openai",
                    "title": "OpenAI - ComputerBase",
                    "snippet": "OpenAI News und aktuelle Meldungen.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="OpenAI News ComputerBase Artikel Uebersicht.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues zu OpenAI?", max_sources=2)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_company_news_rejects_generic_driver_download_page():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.pcwelt.de/article/1154148/grafikkartentreiber-nvidia-geforce-treiber.html",
                    "title": "Nvidia GeForce Treiber - PC-WELT",
                    "snippet": "Downloadseite fuer Nvidia GeForce Treiber.",
                }
            ],
            "metadata": {"provider": "openai"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Nvidia GeForce Treiber Download Updateverlauf Anleitung.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("aktuelle Nachrichten zu Nvidia?", max_sources=2)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_company_news_rejects_official_latest_news_listing():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://nvidianews.nvidia.com/news/latest",
                    "title": "Latest News | NVIDIA Newsroom",
                    "snippet": "NVIDIA latest newsroom updates.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="NVIDIA latest news newsroom overview.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("aktuelle Nachrichten zu Nvidia?", max_sources=2)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "not_detail_page" in reasons


@pytest.mark.asyncio
async def test_company_news_rejects_official_press_release_category():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://news.microsoft.com/de-at/category/press-releases",
                    "title": "Press Releases – News Center",
                    "snippet": "Microsoft Press Releases.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text="Microsoft Press Releases News Center Kategorie.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues zu Microsoft?", max_sources=2)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_general_company_news_rejects_finanztreff_and_phemex():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.finanztreff.de/nachrichten/2026-05-20-breaking-die-nvidia-zahlen-sind-da-800704",
                    "title": "Nvidia: Die Zahlen sind da!",
                    "snippet": "Nvidia Zahlen, Aktie, Markt und Kursreaktion.",
                },
                {
                    "url": "https://phemex.com/de/news/article/openai-ceo-sam-altman-suggests-ipo-delay-amid-market-uncertainty-84287",
                    "title": "OpenAI-CEO deutet IPO-Verschiebung wegen Markt an",
                    "snippet": "OpenAI IPO Markt Unsicherheit.",
                },
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(candidate.url, title=candidate.title, text=f"{candidate.title}. Aktie Markt IPO Kurs.")

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("aktuelle Nachrichten zu Nvidia?", max_sources=2)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert reasons.count("financial_news_source") >= 2


@pytest.mark.asyncio
async def test_broad_gaming_query_accepts_games_industry_detail_article():
    source_url = "https://www.game.de/game-branchenbarometer-2026-stimmung-in-der-deutschen-games-branche-hellt-sich-langsam-auf"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": source_url,
                    "title": "Games-Branchenbarometer 2026: Stimmung hellt sich langsam auf",
                    "snippet": "Die deutsche Games-Branche bewertet die Lage wieder etwas besser.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                "Die deutsche Games-Branche bewertet die wirtschaftliche Lage wieder etwas besser. "
                "Das Branchenbarometer zeigt aktuelle Trends fuer Studios, Publisher und den Games-Standort Deutschland."
            ),
        )

    result = await WebSearchV3Pipeline(search, fetch).verified_news("was gibt es neues im Gaming?", max_sources=4)

    assert result.status == "ok"
    assert result.fact is not None
    assert result.fact.source.canonical_url == source_url


@pytest.mark.asyncio
async def test_broad_gaming_rejects_community_giveaway_thread():
    async def search(_query):
        return {
            "sources": [
                {
                    "url": "https://www.ntower.de/community/thread/109961-gewinnspiel-zum-der-super-mario-galaxy-film/",
                    "title": "Gewinnspiel zum Der Super Mario Galaxy Film - Intern - ntower",
                    "snippet": "Wir verlosen ein Fanpaket mit einem digitalen Downloadcode.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                "Gewinnspiel zum Der Super Mario Galaxy Film. Community Thread und internes Gewinnspiel "
                "mit Fanpaket. Gaming News Deutschland Nintendo Switch."
            ),
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Gaming?", max_sources=4)

    assert result.status == "no_source"
    reasons = [reason for item in pipeline.last_search_metadata["rejected_sources"] for reason in item["reasons"]]
    assert "generic_news_listing" in reasons


@pytest.mark.asyncio
async def test_broad_gaming_does_not_treat_trailer_prediction_as_finance():
    source_url = "https://www.gamepro.de/artikel/gta-6-wann-kommt-trailer-3-aktuelle-prognosen,3453419.html"

    async def search(_query):
        return {
            "sources": [
                {
                    "url": source_url,
                    "title": "GTA 6: Wann kommt Trailer 3? Aktuelle Prognosen",
                    "snippet": "Fans warten auf neue Details zum naechsten Rockstar-Trailer.",
                }
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                "GTA 6: Wann kommt Trailer 3? Aktuelle Prognosen zum naechsten Trailer. "
                "Gaming News Deutschland Detailartikel zu Rockstar, PlayStation und Xbox. "
                "Der Artikel ordnet Geruechte, moegliche Termine, Plattformen und den naechsten offiziellen "
                "Auftritt von Take-Two fuer Spielerinnen und Spieler ein."
            ),
        )

    result = await WebSearchV3Pipeline(search, fetch).verified_news("was gibt es neues im Gaming?", max_sources=4)

    assert result.status == "ok"
    assert result.fact is not None
    assert result.fact.source.canonical_url == source_url


@pytest.mark.asyncio
async def test_gemini_briefing_passes_each_search_direction_to_grounding(monkeypatch):
    seen_queries: list[str] = []
    monkeypatch.setenv("JANUS_WEBSEARCH_V3_MAX_SOURCES", "4")

    async def fake_gemini_grounding(*, api_key, query, model=None):
        seen_queries.append(query)
        return {
            "candidates": [
                {
                    "groundingMetadata": {
                        "groundingChunks": [
                            {"web": {"uri": "https://www.gamepro.de/artikel/gta-6-neuer-trailer,3450001.html", "title": "GTA 6: Neuer Trailer wird erwartet"}}
                        ],
                        "groundingSupports": [
                            {
                                "segment": {"text": "Rockstar bereitet neue Details zu GTA 6 vor."},
                                "groundingChunkIndices": [0],
                            }
                        ],
                    }
                }
            ]
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                "GTA 6: Neuer Trailer wird erwartet. Rockstar bereitet neue Details zu GTA 6 vor. "
                "Gaming News Deutschland Detailartikel mit belegten Informationen zu aktuellen Spielen."
            ),
        )

    monkeypatch.setattr("backend.services.websearch_v3.pipeline.search_gemini_grounded_phase1", fake_gemini_grounding)

    from backend.services.websearch_v3.pipeline import execute_single_verified_news

    result = await execute_single_verified_news(
        query="was gibt es neues im Gaming?",
        api_key="gemini-key",
        provider="gemini",
        model="gemini-3-flash-preview",
    )

    assert result["metadata"]["verified_source_mode"] == "briefing"
    assert any("GTA 6" in query for query in seen_queries)


@pytest.mark.asyncio
async def test_briefing_mode_collects_one_verified_source_per_search_direction():
    calls: list[str] = []
    source_rows = {
        "GTA 6": {
            "url": "https://www.gamepro.de/artikel/gta-6-neuer-trailer,3450001.html",
            "title": "GTA 6: Neuer Trailer wird erwartet",
            "snippet": "Rockstar bereitet neue Details zu GTA 6 vor.",
        },
            "neue Spiele": {
                "url": "https://www.gamestar.de/artikel/neue-spiele-im-juni,3450002.html",
                "title": "Neue Spiele im Juni: Replaced und Dune Awakening",
                "snippet": "Mehrere neue PC- und Konsolenspiele stehen vor dem Release.",
            },
            "Releases": {
                "url": "https://www.gamestar.de/artikel/neue-spiele-im-juni,3450002.html",
                "title": "Neue Spiele im Juni: Replaced und Dune Awakening",
                "snippet": "Mehrere neue PC- und Konsolenspiele stehen vor dem Release.",
            },
        "Studios": {
            "url": "https://www.gameswirtschaft.de/wirtschaft/publisher-studios-umbau-2026/",
            "title": "Publisher und Studios bauen ihre Strategie um",
            "snippet": "Mehrere Studios passen Budgets und Plattformstrategien an.",
        },
        "KI": {
            "url": "https://www.heise.de/news/ki-in-spielen-neue-tools-fuer-npcs-987654.html",
            "title": "KI in Spielen: Neue Tools fuer NPCs",
            "snippet": "KI-Systeme sollen Dialoge und Entwicklungsprozesse in Spielen veraendern.",
        },
    }

    async def search(search_query):
        calls.append(search_query)
        for marker, row in source_rows.items():
            if marker in search_query:
                return {"sources": [row], "metadata": {"provider": "gemini"}}
        return {"sources": [], "metadata": {"provider": "gemini"}}

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                f"{candidate.title}. {candidate.snippet} Gaming News Deutschland Detailartikel mit belegten "
                "Informationen zu aktuellen Spielen, Plattformen, Studios, Techniktrends und konkreten Terminen."
            ),
        )

    result = await WebSearchV3Pipeline(search, fetch).verified_news("was gibt es neues im Gaming?", max_sources=4)
    rendered = render_single_verified_news(result)

    assert result.status == "ok"
    assert len(result.facts) >= 3
    assert len(calls) >= 3
    assert "Kurzlage: Es liegen aktuell" in rendered
    assert "Quelle:" in rendered


@pytest.mark.asyncio
async def test_briefing_mode_keeps_partial_results_when_one_search_direction_fails():
    async def search(search_query):
        if "GTA 6" in search_query:
            raise RuntimeError("provider timeout")
        if "Releases" in search_query:
            return {
                "sources": [
                    {
                        "url": "https://www.gamestar.de/artikel/neue-spiele-im-juni,3450002.html",
                        "title": "Neue Spiele im Juni: Replaced und Dune Awakening",
                        "snippet": "Mehrere neue PC- und Konsolenspiele stehen vor dem Release.",
                    }
                ],
                "metadata": {"provider": "gemini"},
            }
        return {"sources": [], "metadata": {"provider": "gemini"}}

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                f"{candidate.title}. {candidate.snippet} Gaming News Deutschland Detailartikel mit belegten "
                "Informationen zu aktuellen Spielen, Plattformen und Terminen."
            ),
        )

    pipeline = WebSearchV3Pipeline(search, fetch)
    result = await pipeline.verified_news("was gibt es neues im Gaming?", max_sources=4)

    assert result.status == "ok"
    assert result.fact is not None
    assert any(item["status"] == "error" for item in pipeline.last_search_metadata["briefing_queries"])


def test_company_search_queries_are_subject_specific():
    queries = build_company_search_queries("aktuelle Nachrichten zu Nvidia?")

    assert len(queries) >= 3
    assert any("Newsroom" in query for query in queries)
    assert any("Blackwell" in query or "KI Chips" in query for query in queries)


@pytest.mark.asyncio
async def test_company_mode_collects_across_multiple_search_directions():
    calls: list[str] = []
    official_url = "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2027"
    german_url = "https://www.heise.de/news/nvidia-eroeffnet-ki-fabrik-in-muenchen-987654.html"

    async def search(search_query):
        calls.append(search_query)
        if "aktuelle Meldung" in search_query:
            return {
                "sources": [
                    {
                        "url": official_url,
                        "title": "NVIDIA Announces Financial Results for First Quarter Fiscal 2027 | NVIDIA Newsroom",
                        "snippet": "NVIDIA reports record revenue driven by AI and data center demand.",
                    }
                ],
                "metadata": {"provider": "gemini"},
            }
        if "aktuelle Nachrichten" in search_query:
            return {
                "sources": [
                    {
                        "url": german_url,
                        "title": "Nvidia und Telekom eröffnen KI-Fabrik in München",
                        "snippet": "Nvidia und die Deutsche Telekom eröffnen eine KI-Fabrik in München.",
                    }
                ],
                "metadata": {"provider": "gemini"},
            }
        return {"sources": [], "metadata": {"provider": "gemini"}}

    async def fetch(candidate: SearchCandidate):
        if candidate.url == official_url:
            return PageFetchResult(
                url=candidate.url,
                final_url=candidate.url,
                status_code=200,
                title=candidate.title,
                text=(
                    "NVIDIA announced financial results for the first quarter of fiscal 2027. "
                    "The company reported record revenue driven by AI, data center demand and Blackwell systems."
                ),
                language_hint="en",
            )
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                "Nvidia und die Deutsche Telekom eröffnen eine KI-Fabrik in München. "
                "Der Fachartikel beschreibt aktuelle KI-Infrastruktur, Rechenzentren und den deutschen Markt."
            ),
        )

    result = await WebSearchV3Pipeline(search, fetch).verified_news("aktuelle Nachrichten zu Nvidia?", max_sources=2)

    assert result.status == "ok"
    assert len(result.facts) == 2
    assert len(calls) == 2
    assert {fact.source.canonical_url for fact in result.facts} == {official_url, german_url}


@pytest.mark.asyncio
async def test_company_mode_never_returns_more_facts_than_policy_target():
    counter = 0

    async def search(_search_query):
        nonlocal counter
        counter += 1
        base = counter * 10
        return {
            "sources": [
                {
                    "url": f"https://www.heise.de/news/microsoft-copilot-update-{base}.html",
                    "title": f"Microsoft Copilot Update {base}",
                    "snippet": "Microsoft stellt neue Copilot-Funktionen vor.",
                },
                {
                    "url": f"https://www.computerwoche.de/a/microsoft-cloud-news-{base + 1},98765.html",
                    "title": f"Microsoft Cloud News {base + 1}",
                    "snippet": "Microsoft erweitert Cloud- und KI-Angebote.",
                },
            ],
            "metadata": {"provider": "gemini"},
        }

    async def fetch(candidate: SearchCandidate):
        return _page(
            candidate.url,
            title=candidate.title,
            text=(
                f"{candidate.title}. Microsoft KI Cloud Copilot Detailartikel aktuelle Nachrichten Deutschland. "
                "Der Artikel beschreibt neue Funktionen, Produktstrategie, Kundenkontext und technische "
                "Einordnung der aktuellen Microsoft-Meldung mit ausreichend redaktionellem Text fuer die "
                "Quellenpruefung."
            ),
        )

    result = await WebSearchV3Pipeline(search, fetch).verified_news("was gibt es neues zu Microsoft?", max_sources=4)
    rendered = render_single_verified_news(result)

    assert result.status == "ok"
    assert len(result.facts) == 2
    assert "3 belegte Meldungen" not in rendered

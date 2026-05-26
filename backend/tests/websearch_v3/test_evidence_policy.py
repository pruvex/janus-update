from __future__ import annotations

from backend.services.websearch_v3.evidence_policy import evidence_rejection_reason
from backend.services.websearch_v3.models import PageFetchResult, SearchCandidate
from backend.services.websearch_v3.source_classifier import SourceClassification, classify_source


def _candidate(url: str, *, title: str, snippet: str = "") -> SearchCandidate:
    return SearchCandidate(provider="fixture", url=url, title=title, snippet=snippet, rank=1)


def _page(url: str, *, title: str, text: str) -> PageFetchResult:
    return PageFetchResult(url=url, final_url=url, status_code=200, title=title, text=text)


def test_policy_rejects_calendar_listing_for_broad_entertainment_briefing():
    classification = SourceClassification("calendar_or_listing", 0.25, ("calendar_or_listing",))

    reason = evidence_rejection_reason("was gibt es neues im Kino?", classification)

    assert reason == "insufficient_briefing_evidence"


def test_policy_allows_release_detail_for_broad_entertainment_briefing():
    classification = SourceClassification("release_detail", 0.8, ("release_detail",))

    reason = evidence_rejection_reason("was gibt es neues im Gaming?", classification)

    assert reason == ""


def test_policy_allows_curated_briefing_for_broad_entertainment_briefing():
    classification = SourceClassification("curated_briefing", 0.74, ("curated_briefing",))

    reason = evidence_rejection_reason("was gibt es neues im Kino?", classification)

    assert reason == ""


def test_classifier_marks_concrete_kinostarts_overview_as_curated_briefing():
    candidate = _candidate(
        "https://www.filmstarts.de/filme-imkino/neu",
        title="Kinostarts der Woche - FILMSTARTS.de",
        snippet="Neue Filme im Kino: Resurrection, The Mandalorian & Grogu und Perfect Blue.",
    )

    classification = classify_source(
        candidate,
        _page(
            candidate.url,
            title=candidate.title,
            text='Diese Woche starten "Resurrection", "The Mandalorian & Grogu" und "Perfect Blue" im Kino.',
        ),
    )

    assert classification.source_type == "curated_briefing"


def test_classifier_keeps_month_calendar_as_listing_even_with_titles():
    candidate = _candidate(
        "https://www.uncut.at/movies/monat.php",
        title="Filmstarts Mai 2026 - UNCUT",
        snippet="Monatsuebersicht mit Kinostarts wie Resurrection und Perfect Blue.",
    )

    classification = classify_source(
        candidate,
        _page(candidate.url, title=candidate.title, text='Im Mai starten "Resurrection" und "Perfect Blue".'),
    )

    assert classification.source_type == "calendar_or_listing"


def test_classifier_keeps_release_notes_as_listing():
    candidate = _candidate(
        "https://learn.microsoft.com/de-de/officeupdates/microsoft365-apps-security-updates",
        title="Versionshinweise fuer Microsoft Office-Sicherheitsupdates - Office release notes",
        snippet="Release notes und Versionshinweise fuer Microsoft 365 Apps.",
    )

    classification = classify_source(
        candidate,
        _page(candidate.url, title=candidate.title, text="Release notes Versionshinweise Updateverlauf Liste."),
    )

    assert classification.source_type == "calendar_or_listing"


def test_policy_rejects_topic_listing_for_general_company_news():
    classification = SourceClassification("topic_listing", 0.25, ("topic_listing",))

    reason = evidence_rejection_reason("was gibt es neues zu Microsoft?", classification)

    assert reason == "source_type_topic_listing"


def test_classifier_marks_official_newsroom_detail_as_official_release():
    candidate = _candidate(
        "https://news.microsoft.com/source/emea/2026/05/microsoft-kuendigt-neue-cloud-funktion-an",
        title="Microsoft kuendigt neue Cloud-Funktion an",
        snippet="Microsoft stellt eine neue Cloud-Funktion vor.",
    )

    classification = classify_source(
        candidate,
        _page(candidate.url, title=candidate.title, text="Microsoft Newsroom Pressemitteilung launch release official."),
    )

    assert classification.source_type == "official_release"
    assert classification.evidence_score >= 0.78


def test_classifier_marks_forum_thread_as_community():
    candidate = _candidate(
        "https://example.com/community/thread/12345",
        title="OpenAI News Diskussion",
        snippet="Nutzer diskutieren Geruechte.",
    )

    classification = classify_source(
        candidate,
        _page(candidate.url, title=candidate.title, text="Login | Registrieren Forum Community Thread."),
    )

    assert classification.source_type == "community"
    assert evidence_rejection_reason("was gibt es neues zu OpenAI?", classification) == "source_type_community"


def test_classifier_marks_presseportal_st_page_as_topic_listing():
    candidate = _candidate(
        "https://www.presseportal.de/st/Microsoft",
        title="Offizielle News zu Microsoft 2026 | Presseportal",
        snippet="Presseportal-Themenseite mit Meldungen zu Microsoft.",
    )

    classification = classify_source(
        candidate,
        _page(candidate.url, title=candidate.title, text="Presseportal Microsoft News Meldungen Uebersicht."),
    )

    assert classification.source_type == "topic_listing"
    assert evidence_rejection_reason("was gibt es neues zu Microsoft?", classification) == "source_type_topic_listing"

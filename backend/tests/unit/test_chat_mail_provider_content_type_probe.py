from backend.services.chat_orchestrator import ChatOrchestrator
from types import SimpleNamespace


def test_sender_keyword_probe_detects_generic_provider_and_recipe():
    probe = ChatOrchestrator._sender_keyword_mail_probe("Finde alle Rezeptmails von Rewe.")
    assert probe is not None
    assert "Rewe" in probe["title"]
    assert "subject:rezept" in probe["query"]
    assert probe["sender"] == "Rewe"
    assert probe["content_type_label"] == "Rezepte"


def test_sender_keyword_probe_detects_provider_keyword_variant_anbieter():
    probe = ChatOrchestrator._sender_keyword_mail_probe("Zeig mir alle Bons von Anbieter Lidl.")
    assert probe is not None
    assert "Lidl" in probe["title"]
    assert "subject:bon" in probe["query"]
    assert probe["content_type_label"] == "Bons/Belege"


def test_sender_keyword_probe_detects_invoice_category():
    probe = ChatOrchestrator._sender_keyword_mail_probe("Liste alle Rechnungen von Vodafone")
    assert probe is not None
    assert "Rechnungen" in probe["title"]
    assert "subject:invoice" in probe["query"]

def test_sender_keyword_probe_returns_ambiguity_for_multiple_providers():
    probe = ChatOrchestrator._sender_keyword_mail_probe("Welche Rezepte von Rewe oder Lidl finden wir in meinen Mails?")
    assert probe is not None
    assert probe.get("ambiguous") == "provider"
    assert "Rewe" in probe.get("provider_candidates", [])
    assert "Lidl" in probe.get("provider_candidates", [])


def test_sender_keyword_probe_returns_ambiguity_for_multiple_categories():
    probe = ChatOrchestrator._sender_keyword_mail_probe("Zeig mir Rezepte und Rechnungen von Rewe")
    assert probe is not None
    assert probe.get("ambiguous") == "content_type"
    assert "Rezepte" in probe.get("content_type_candidates", [])
    assert "Rechnungen" in probe.get("content_type_candidates", [])


def test_mail_search_clarification_prompt_for_missing_provider():
    prompt = ChatOrchestrator._mail_search_clarification_prompt("Zeig mir alle Mails mit Rechnungen")
    assert prompt == "Von welchem Anbieter soll ich diese Mails suchen?"


def test_mail_search_clarification_prompt_for_missing_content_type():
    prompt = ChatOrchestrator._mail_search_clarification_prompt("Zeig mir alle Mails von Rewe")
    assert prompt is not None
    assert "Welche Art von Mails" in prompt


def test_mail_row_category_evidence_positive_from_subject():
    row = SimpleNamespace(subject="Dein Rezept der Woche", snippet="")
    ok, evidence = ChatOrchestrator._mail_row_category_evidence(row, ("rezept", "rezepte"))
    assert ok is True
    assert "rezept" in evidence


def test_mail_row_category_evidence_negative_without_terms():
    row = SimpleNamespace(subject="Hallo aus dem Kundenservice", snippet="Nur eine allgemeine Nachricht")
    ok, evidence = ChatOrchestrator._mail_row_category_evidence(row, ("rechnung", "invoice"))
    assert ok is False
    assert evidence == ""


def test_mail_search_clarification_prompt_does_not_interfere_with_latest_mails_flow():
    prompt = ChatOrchestrator._mail_search_clarification_prompt("Zeig mir die letzten 5 Mails")
    assert prompt is None


def test_sender_keyword_probe_ignores_non_category_sender_query():
    probe = ChatOrchestrator._sender_keyword_mail_probe("Zeig mir die Mail von Rewe")
    assert probe is None


def test_mail_row_category_evidence_positive_from_snippet():
    row = SimpleNamespace(subject="Dein Wochenupdate", snippet="Hier ist deine Rechnung als Anhang.")
    ok, evidence = ChatOrchestrator._mail_row_category_evidence(row, ("rechnung", "invoice"))
    assert ok is True
    assert "rechnung" in evidence


def test_format_provider_category_mail_rows_renders_content_entries():
    orchestrator = ChatOrchestrator.__new__(ChatOrchestrator)
    orchestrator._format_mail_when = lambda _row: "2026-05-31"
    rows = [
        SimpleNamespace(
            subject="Picnic Rezept der Woche",
            snippet="Heute mit Pasta und Tomaten.",
        )
    ]
    text = orchestrator._format_provider_category_mail_rows(
        rows=rows,
        title="Rezepte von Picnic aus deinen Mails:",
        provider="Picnic",
        category="Rezepte",
        category_terms=("rezept", "rezepte"),
        limit=20,
    )
    assert "Anbieter: Picnic" in text
    assert "Kategorie: Rezepte" in text
    assert "Evidenz: Signal im Betreff/Kurzinhalt:" in text
    assert "Mails mit Anh" not in text


def test_format_provider_category_mail_rows_reports_no_matches():
    orchestrator = ChatOrchestrator.__new__(ChatOrchestrator)
    orchestrator._format_mail_when = lambda _row: "2026-05-31"
    rows = [SimpleNamespace(subject="Status Update", snippet="Allgemeine Information")]
    text = orchestrator._format_provider_category_mail_rows(
        rows=rows,
        title="Rezepte von Picnic aus deinen Mails:",
        provider="Picnic",
        category="Rezepte",
        category_terms=("rezept", "rezepte"),
        limit=20,
    )
    assert "Keine passenden Rezepte-Mails von Picnic gefunden." in text


def test_keyword_metadata_from_query_detects_provider_and_recipe_category():
    meta = ChatOrchestrator._keyword_metadata_from_query("from:(picnic) (subject:rezept OR subject:rezepte)")
    assert meta is not None
    assert meta["keyword_sender"] == "picnic"
    assert meta["keyword_category"] == "Rezepte"
    assert "rezept" in meta["keyword_subject_terms"]


def test_recipe_provider_query_is_not_attachment_query():
    text = "welche rezepte von picnic finden wir in meinen mails?"
    assert ChatOrchestrator._sender_keyword_mail_probe(text) is not None
    assert ChatOrchestrator._CHAT_MAIL_ATTACHMENTS_RE.match(text) is None

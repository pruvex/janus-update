from __future__ import annotations

from typing import Any
import re
from datetime import date

from .query_planner import extract_subject, query_domain


def _subject_from_query(query: str) -> str:
    return extract_subject(re.sub(r"\s+", " ", str(query or "")).strip(" ?!."))


def _build_phase1_prompt(query: str) -> str:
    subject = _subject_from_query(query)
    domain = query_domain(query)
    today = date.today().strftime("%d.%m.%Y")
    if domain == "film":
        return (
            "Was sind aktuelle Film- und Kinonews in Deutschland? "
            f"Stand heute: {today}. "
            f"Konkreter Suchfokus: {subject}. "
            "Verwende Google Search und gib Quellenlinks an. "
            "Nenne nur aktuell passende Treffer aus dem laufenden Jahr oder eindeutig aktuelle Detailartikel. "
            "Suche auf Deutsch nach konkreten Detailartikeln zu Kinostarts, neuen Filmtrailern, "
            "neuen Filmankuendigungen, Produktionen oder Streamingstarts. "
            "Bevorzuge deutschsprachige Detailartikel von Film-, Kino- oder Kulturmedien. "
            "Keine Woerterbuecher, Uebersetzungsseiten, Startseiten, reinen Kalenderuebersichten, "
            "Festivalberichte, Eventlisten, IMDb-Kalender, Suchseiten oder Bilddateien."
        )
    if domain == "gaming":
        return (
            "Was sind aktuelle Gaming-News in Deutschland? "
            f"Stand heute: {today}. "
            f"Konkreter Suchfokus: {subject}. "
            "Verwende Google Search und gib Quellenlinks an. "
            "Nenne nur aktuell passende Treffer aus dem laufenden Jahr oder eindeutig aktuelle Detailartikel. "
            "Suche auf Deutsch nach konkreten Detailartikeln zu Games, Studios, Releases, Plattformen, "
            "Hardware, E-Sport oder Branchenmeldungen. "
            "Bevorzuge deutschsprachige Detailartikel von Gaming- oder Tech-Medien. "
            "Keine Store-Seiten, reinen Release-Kalender, Startseiten, Suchseiten, Woerterbuecher oder Bilddateien."
        )
    return (
        f"Was sind die aktuellen Nachrichten zu {subject}? "
        "Verwende Google Search und gib Quellenlinks an. "
        "Formuliere die Google-Suchanfragen auf Deutsch, zum Beispiel mit 'aktuelle Nachrichten', "
        "'deutsch', 'Deutschland' oder 'deutsche Quelle'. "
        "Bevorzuge deutschsprachige Detailartikel, deutschsprachige offizielle Seiten, .de-Quellen, "
        "/de/-, /de-de/- oder ?lang=de-URLs. "
        "Englische Quellen nur nennen, wenn keine deutschsprachige Detailquelle gefunden wird. "
        "Keine Suchseiten, Startseiten, Themenseiten, Ankuendigungsuebersichten, Aktienkursseiten oder Bilddateien."
    )


async def search_gemini_grounded_phase1(
    *,
    api_key: str,
    query: str,
    model: str | None = None,
    timeout: int = 25,
) -> dict[str, Any]:
    model_name = str(model or "gemini-3-flash-preview").strip()
    if not model_name.lower().startswith("gemini"):
        model_name = "gemini-3-flash-preview"

    def _request() -> dict[str, Any]:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=max(timeout, 5) * 1000),
        )
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        response = client.models.generate_content(
            model=model_name,
            contents=_build_phase1_prompt(query),
            config=types.GenerateContentConfig(
                tools=[grounding_tool],
                temperature=0.1,
                max_output_tokens=2048,
            ),
        )
        if hasattr(response, "model_dump"):
            return response.model_dump(exclude_none=True)
        if hasattr(response, "to_dict"):
            return response.to_dict()
        return {}

    import asyncio

    return await asyncio.wait_for(asyncio.to_thread(_request), timeout=timeout + 5)

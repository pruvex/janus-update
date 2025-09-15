import random
import logging
import re
from backend.llm_gateway import simple_llm_generate_content

async def creative_writer(input_text: str, provider: str, model: str, api_key: str, style: str = "poetisch", selection: str = "first"):
    """
    Intelligenter Dispatcher für kreatives Schreiben.
    Analysiert den Nutzerwunsch und wählt automatisch die passende Pipeline
    für kurze oder lange Texte.
    """
    # Schlüsselwörter, die auf einen langen Text hindeuten
    LONG_TEXT_KEYWORDS = [
        "geschichte", "story", "erzählung", "artikel", "blogpost",
        "kapitel", "szene", "reportage", "essay", "absätze",
        "seite", "wörter"
    ]
    # Analyse des Inputs: Prüfen, ob Keywords für lange Texte enthalten sind
    # Wir prüfen den Input in Kleinbuchstaben, um die Erkennung zu verbessern.
    is_long_form_request = any(keyword in input_text.lower() for keyword in LONG_TEXT_KEYWORDS)
    if is_long_form_request:
        # Der Nutzer wünscht sich wahrscheinlich einen langen Text.
        # Wir rufen die Long-Form-Pipeline auf.
        # Der Stil wird für Geschichten standardmäßig auf "narrativ" (erzählend) gesetzt,
        # falls der Nutzer nicht explizit einen anderen Stil angibt (z.B. "humorvoll").
        if style == "poetisch": # "poetisch" ist ein schlechter Stil für eine lange Geschichte
            style = "narrativ"
        return await _creative_writer_long_form_pipeline(input_text, provider, model, api_key, style, selection)
    else:
        # Keine Indikatoren für einen langen Text gefunden.
        # Wir rufen die sichere und schnelle Short-Form-Pipeline auf.
        return await _creative_writer_short_form_pipeline(input_text, provider, model, api_key, style, selection)


logger = logging.getLogger('janus_backend')

async def _creative_writer_short_form_pipeline(input_text: str, provider: str, model: str, api_key: str, style: str = "poetisch", selection: str = "first"):
    """
    Implementiert eine Pipeline für kreatives Schreiben.

    Args:
        input_text (str): Das Thema oder der Ausgangstext für die kreative Generierung.
        provider (str): Der LLM-Provider (z.B. "gemini", "openai").
        model (str): Das zu verwendende LLM-Modell.
        api_key (str): Der API-Schlüssel für den LLM-Provider.
        style (str): Der gewünschte Schreibstil (z.B. "haiku", "märchenhaft", "ballade", "modern").
        selection (str): Auswahlmethode für Entwürfe ("first", "random", "best").

    Returns:
        str: Die polierte Endfassung des Textes.
    """

    # 1. Ideenphase
    ideas_prompt = f"""Finde kreative Ideen, Metaphern und Bilder für das Thema "{input_text}".
Erstelle 3 unterschiedliche Varianten."""
    ideas_response = await simple_llm_generate_content(
        provider=provider,
        model=model,
        api_key=api_key,
        prompt=ideas_prompt
    )
    ideas = ideas_response.get('text', '') # Annahme: simple_llm_generate_content gibt ein Objekt mit .text zurück
    logger.info(f"Creative Writer - Ideas Prompt: {ideas_prompt}")
    logger.info(f"Creative Writer - Ideas Generated: {ideas[:500]}...") # Log first 500 chars

    # 2. Entwurfsphase
    drafts_prompt = f"""Schreibe 3 kurze Entwürfe im Stil "{style}"
basierend auf folgenden Ideen:
{ideas}"""
    drafts_response = await simple_llm_generate_content(
        provider=provider,
        model=model,
        api_key=api_key,
        prompt=drafts_prompt
    )
    drafts_text = drafts_response.get('text', '')
    logger.info(f"Creative Writer - Drafts Prompt: {drafts_prompt}")
    logger.info(f"Creative Writer - Raw Drafts Response: {drafts_text[:800]}...") # Log raw response for debugging
    # Neue, robuste Extraktion der Entwürfe
    # Wir suchen nach der Markierung "### Entwurf" und nehmen alles, was danach kommt.
    # re.split behält den Trenner nicht, was hier ideal ist, um die Einleitung loszuwerden.
    # Das Muster sucht nach einer neuen Zeile, gefolgt von '---' und optional '### Entwurf'.
    drafts_list = re.split(r'\n---\n\n### Entwurf \d+:.*?\n|\n### Entwurf \d+:.*?\n', drafts_text)
    # Das erste Element ist oft die Einleitung oder leer. Wir filtern es und leere Strings heraus.
    if drafts_list:
        drafts_list = [draft.strip() for draft in drafts_list[1:] if draft and draft.strip()]
    # Fallback-Mechanismus: Wenn die neue Methode keine Entwürfe findet,
    # wird die alte Methode als Sicherheit verwendet.
    if not drafts_list:
        logger.warning("Creative Writer - No structured drafts found. Falling back to simple split method.")
        # Wir filtern hierbei aber direkt alles heraus, was zu kurz ist oder wie eine Einleitung klingt.
        all_parts = drafts_text.split("\n\n")
        drafts_list = [part.strip() for part in all_parts if len(part) > 100 and "Entwurf" not in part[:20]]
    # Sicherheitscheck: Wenn immer noch keine Entwürfe da sind, kann etwas nicht stimmen.
    if not drafts_list:
        logger.error("Creative Writer - CRITICAL: Could not parse any valid drafts from the LLM response.")
        # Im Fehlerfall wird der erste, nicht leere Block der alten Methode genommen, um einen Totalausfall zu verhindern.
        drafts_list = [part.strip() for part in drafts_text.split("\n\n") if part.strip()]
        if not drafts_list: # Absolute Notsicherung
            return "Fehler: Es konnten keine kreativen Entwürfe aus der Antwort extrahiert werden."
    logger.info(f"Creative Writer - Parsed Drafts List: {drafts_list}")

    chosen_draft = ""
    if selection == "random":
        chosen_draft = random.choice(drafts_list)
    elif selection == "best":
        # Hier müsste später eine Bewertungslogik implementiert werden
        chosen_draft = drafts_list[0] # Vorerst einfach den ersten Entwurf nehmen
    else: # "first" oder Standard
        chosen_draft = drafts_list[0]
    logger.info(f"Creative Writer - Chosen Draft: {chosen_draft[:500]}...") # Log first 500 chars

    # 3. Endfassung
    final_prompt = f"""Überarbeite den folgenden Entwurf zu einer polierten Endfassung im Stil "{style}".
Gib NUR die polierte Endfassung aus, ohne zusätzliche Kommentare oder Optionen.

Entwurf:
{chosen_draft}"""
    final_response = await simple_llm_generate_content(
        provider=provider,
        model=model,
        api_key=api_key,
        prompt=final_prompt
    )
    final_text = final_response.get('text', '')
    logger.info(f"Creative Writer - Final Prompt: {final_prompt}")
    logger.info(f"Creative Writer - Final Text: {final_text[:500]}...") # Log first 500 chars

    return final_text


async def _creative_writer_long_form_pipeline(input_text: str, provider: str, model: str, api_key: str, style: str = "narrativ", selection: str = "first"):
    """
    Implementiert eine Pipeline für lange kreative Texte (z.B. Kurzgeschichten).
    Generiert zuerst 3 Konzepte, wählt eines aus und schreibt dann den finalen Text.
    """
    logger.info("Creative Writer - Long-form pipeline selected.")
    # 1. Konzeptphase
    concepts_prompt = f"""Für das Thema "{input_text}" im Stil "{style}", erstelle 3 unterschiedliche und kreative Konzepte bzw. kurze Zusammenfassungen (Synopsen).
Jede Synopsis sollte die Hauptfiguren, den zentralen Konflikt und eine grobe Handlungsidee für eine längere Geschichte skizzieren. Gib NUR die 3 Konzepte aus, getrennt durch '---'."""
    concepts_response = await simple_llm_generate_content(
        provider=provider,
        model=model,
        api_key=api_key,
        prompt=concepts_prompt
    )
    concepts_list = concepts_response.get('text', '').split("---")
    concepts_list = [c.strip() for c in concepts_list if c.strip()]
    logger.info(f"Creative Writer - Concepts Prompt: {concepts_prompt}")
    logger.info(f"Creative Writer - Concepts List: {concepts_list}")
    if not concepts_list:
        logger.error("Creative Writer - CRITICAL: Could not parse any valid concepts.")
        return "Fehler: Es konnten keine kreativen Konzepte aus der Antwort extrahiert werden."
    chosen_concept = ""
    if selection == "random":
        chosen_concept = random.choice(concepts_list)
    else: # "first" oder "best" (noch keine Bewertungslogik)
        chosen_concept = concepts_list[0]
    logger.info(f"Creative Writer - Chosen Concept: {chosen_concept[:500]}...")
    # 2. Ausarbeitungsphase
    writing_prompt = f"""Schreibe eine vollständige und detaillierte Geschichte im Stil "{style}" basierend auf dem folgenden Konzept.
Die Geschichte sollte fesselnd sein und einen klaren Anfang, Hauptteil und Schluss haben.
Gib NUR die fertige Geschichte aus, ohne zusätzliche Kommentare.
Konzept:{chosen_concept}"""
    final_response = await simple_llm_generate_content(
        provider=provider,
        model=model,
        api_key=api_key,
        prompt=writing_prompt
    )
    final_text = final_response.get('text', '')
    logger.info(f"Creative Writer - Writing Prompt: {writing_prompt}")
    logger.info(f"Creative Writer - Final Text Generated (first 500 chars): {final_text[:500]}...")
    return final_text

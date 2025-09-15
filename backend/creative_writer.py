import random
import logging
from backend.llm_gateway import simple_llm_generate_content

logger = logging.getLogger('janus_backend')

async def creative_writer(input_text: str, provider: str, model: str, api_key: str, style: str = "poetisch", selection: str = "first"):
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
    drafts_list = drafts_response.get('text', '').split("\n\n") # Annahme: Entwürfe sind durch doppelte Zeilenumbrüche getrennt
    logger.info(f"Creative Writer - Drafts Prompt: {drafts_prompt}")
    logger.info(f"Creative Writer - Drafts List: {drafts_list}")

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
    final_prompt = f"""Überarbeite den folgenden Entwurf zu einer polierten Endfassung:
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


# Beispiel-Aufruf (für lokale Tests, nicht Teil der eigentlichen Implementierung)
# async def main():
#     text = await creative_writer("Sternenhimmel", style="haiku")
#     print(text)

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())

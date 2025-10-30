# backend/services/creative_writer.py

import logging
from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.services.rag_manager import query_knowledge_base

logger = logging.getLogger("janus_backend")


async def add_vocal_directions(text: str, api_key: str, model: str) -> str:
    """
    Ein LLM-Agent, der einen fertigen Text analysiert und ihn mit
    Markierungen für Pausen (...) und Betonungen (*kursiv*) anreichert,
    um die TTS-Ausgabe natürlicher klingen zu lassen.
    """
    logger.info("Creative Writer: Übergebe Text an den Regie-Agenten für stimmliche Anweisungen...")
    
    provider = OpenAIServiceProvider()

    system_prompt = (
        "Du bist ein Regisseur für Hörbücher. Deine Aufgabe ist es, den folgenden Text so zu formatieren, "
        "dass eine KI-Stimme ihn als fesselnde Geschichte vorlesen kann. Ändere KEIN EINZIGES WORT des Inhalts. "
        "Deine einzigen Werkzeuge sind:\n"
        "1. **Pausen:** Füge Ellipsen (...) an Stellen ein, an denen eine dramatische oder nachdenkliche Pause hingehört. Nutze sie sparsam.\n"
        "2. **Betonung:** Setze einzelne, wichtige Wörter in Kursivschrift (*Wort*), um eine leichte Betonung zu signalisieren.\n\n"
        "BEISPIEL:\n"
        "Original: Er öffnete die Tür und sah nichts. Dann hörte er ein Geräusch.\n"
        "Deine Version: Er öffnete die Tür ... und sah nichts. Dann hörte er ein *Geräusch*.\n\n"
        "Gib NUR den final formatierten Text zurück."
    )

    full_prompt = f"{system_prompt}\n\n--- TEXT ---\n{text}"

    try:
        response = await provider.call_llm(
            api_key=api_key,
            model_id=model,
            messages=[{"role": "user", "content": full_prompt}]
        )
        directed_text = response.get("text", text)
        logger.info("Regie-Anweisungen erfolgreich zum Text hinzugefügt.")
        return directed_text
    except Exception as e:
        logger.error(f"Fehler im Regie-Agenten: {e}", exc_info=True)
        return text


async def creative_writer(
    prompt: str,
    provider: str,
    model: str,
    api_key: str,
    style: str = "poetisch",
) -> str:
    llm_provider = OpenAIServiceProvider()

    # STUFE 1: RAG-Kontext-Anreicherung (falls relevant)
    context = query_knowledge_base(prompt, collection_name=selected_collection)
    if context:
        logger.info(f"Creative Writer: Nutze RAG-Kontext: {context[:100]}...")
        final_prompt = f"ANTWORT-STIL: {style.upper()}\n\nKONTEXT:\n{context}\n\nAUFGABE:\n{prompt}"
    else:
        logger.info("Kein relevanter Kontext gefunden. Verwende Standard-Prompt.")
        final_prompt = prompt

    # STUFE 2: Schreiber-Phase (erster Entwurf)
    logger.info("Creative Writer: Generiere ersten Entwurf (Schreiber-Phase)...")
    draft_response = await llm_provider.call_llm(
        api_key, model, messages=[{"role": "user", "content": final_prompt}]
    )
    draft_text = draft_response.get("text", "Ich konnte leider keinen Text erstellen.").strip()

    # STUFE 3: Lektor-Phase (Verfeinerung)
    logger.info("Creative Writer: Übergebe Entwurf an den Lektor-Agenten zur Verfeinerung...")
    lektor_prompt = (
        "Du bist ein strenger und detailverliebter Lektor. Deine Aufgabe ist es, den folgenden Textentwurf zu analysieren und zu verbessern. "
        "Konzentriere dich auf folgende Punkte:\n"
        "1.  **Unpassende Metaphern:** Finde Bilder oder Vergleiche, die physikalisch oder logisch keinen Sinn ergeben (z.B. \"Licht widerhallen\"). Ersetze sie durch präzisere und stimmigere Formulierungen.\n"
        "2.  **'Unmenschliche' Sprache:** Identifiziere Sätze, die unbeholfen oder unnatürlich klingen. Formuliere sie neu, damit sie flüssiger und menschlicher wirken.\n"
        "3.  **Logische Konsistenz:** Achte auf kleine logische Brüche in der Handlung oder in den Beschreibungen.\n\n"
        "Gib als Ergebnis NUR den finalen, polierten und verbesserten Text zurück. Füge keine Kommentare oder Erklärungen hinzu.\n\n"
        f"**TEXTENTWURF ZUR ÜBERARBEITUNG:**\n---\n{draft_text}\n---\n\n**VERBESSERTE VERSION:**\n"
    )
    
    lektor_response = await llm_provider.call_llm(
        api_key,
        model,
        messages=[{"role": "user", "content": lektor_prompt}],
    )
    final_text = lektor_response.get("text", draft_text).strip()
    logger.info("Creative Writer: Lektor-Phase abgeschlossen.")

    # STUFE 4: Regie-Phase (Vorbereitung für TTS)
    final_text_with_directions = await add_vocal_directions(final_text, api_key, model)
    
    logger.info("Creative Writer: Regie-Phase abgeschlossen. Gebe finale Version zurück.")
    return final_text_with_directions
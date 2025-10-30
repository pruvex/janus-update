# backend/services/creative_writer.py

import logging
from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.services.rag_manager import query_rag_collection

logger = logging.getLogger("janus_backend")

# --- NEU START: Der Regie-Agent ---
async def add_vocal_directions(text: str, api_key: str, model: str) -> str:
    """
    Ein LLM-Agent, der einen fertigen Text analysiert und ihn mit
    Markierungen für Pausen (...) und Betonungen (*kursiv*) anreichert,
    um die TTS-Ausgabe natürlicher klingen zu lassen.
    """
    logger.info("Creative Writer: Übergebe Text an den Regie-Agenten für stimmliche Anweisungen...")
    
    provider = OpenAIServiceProvider()

    # Ein sehr präziser Prompt, der dem LLM seine Aufgabe als "Regisseur" erklärt
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

    full_prompt = f"{system_prompt}\n\n---
TEXT ---
{text}"

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
        # Im Fehlerfall geben wir den Originaltext zurück, damit nichts kaputtgeht
        return text
# --- NEU ENDE ---


async def creative_writer(
    prompt: str,
    provider: str,
    model: str,
    api_key: str,
    style: str = "poetisch",
) -> str:
    # (Die ersten Teile der Funktion bleiben unverändert)
    # ...
    # STUFE 1: RAG-Kontext-Anreicherung (bleibt gleich)
    # ...
    # STUFE 2: Schreiber-Phase (bleibt gleich)
    # ...
    # STUFE 3: Lektor-Phase (bleibt gleich)
    
    # --- Integration der neuen Logik ---
    
    final_text = "" # Initialisiere die Variable

    # ... (Der bestehende Code für RAG, Schreiber und Lektor bleibt hier)
    # Hier ist der relevante Ausschnitt zur Orientierung:
    
    # STUFE 1: RAG
    available_collections = rag_manager.list_collections()
    logger.info(f"Verfügbare Wissens-Bibliotheken: {available_collections}")

    selected_collection = None
    if available_collections:
        selection_model = "gpt-4o-mini" if provider == "openai" else model
        selection_prompt = f"""Basierend auf der folgenden Benutzeranfrage, welche der verfügbaren Wissens-Bibliotheken ist am relevantesten? Antworte NUR mit dem exakten Namen der am besten passenden Bibliothek aus der Liste. Wenn keine passt, antworte mit "None".

Verfügbare Bibliotheken: {", ".join(available_collections)}
Benutzeranfrage: "{prompt}"
Beste Bibliothek:"""

        try:
            llm_response = await OpenAIServiceProvider().call_llm(
                api_key,
                selection_model,
                messages=[{"role": "user", "content": selection_prompt}],
                temperature=0.0,
            )
            best_choice = (
                llm_response.get("text", "").strip().replace("'", "").replace('"', "")
            )
            if best_choice in available_collections:
                selected_collection = best_choice
                logger.info(
                    f"LLM hat die Wissensbasis '{selected_collection}' ausgewählt."
                )
            else:
                logger.info(
                    f"LLM hat keine passende Bibliothek gefunden (Antwort: '{best_choice}')."
                )
        except Exception as e:
            logger.error(f"Fehler bei der Auswahl der Bibliothek: {e}")

    # STUFE 2: Schreiber
    retrieved_context = []
    if selected_collection:
        retrieved_context = rag_manager.query_knowledge_base(
            prompt, collection_name=selected_collection, n_results=7
        )

    schreiber_prompt = prompt
    if retrieved_context:
        logger.info(
            f"{len(retrieved_context)} Kontext-Abschnitte aus '{selected_collection}' gefunden."
        )
        context_string = "\n\n".join([f"- {item}" for item in retrieved_context])
        schreiber_prompt = f"""Du bist ein meisterhafter kreativer Autor im Stil von {style}. Dein Ziel ist es, eine Geschichte zu schreiben, die nicht nur stilistisch, sondern auch in ihren Metaphern und Beschreibungen konzeptionell stimmig ist. Achte auf logische und physikalisch plausible Bilder.

**WICHTIG:** Nutze die folgenden Textausschnitte aus der Wissensbasis '{selected_collection}' als Inspiration für deinen Stil, Ton und Vokabular. Baue diese Elemente in deine Antwort ein, um sie authentischer zu machen, aber kopiere sie nicht einfach.
---
**INSPIRATIONS-KONTEXT:**
{context_string}
---
**ANFRAGE DES BENUTZERS:**
{prompt}"""
    else:
        logger.info("Kein relevanter Kontext gefunden. Verwende Standard-Prompt.")

    first_draft = ""
    try:
        logger.info("Creative Writer: Generiere ersten Entwurf (Schreiber-Phase)...")
        draft_response = await OpenAIServiceProvider().call_llm(
            api_key,
            model,
            messages=[{"role": "user", "content": schreiber_prompt}],
        )
        first_draft = draft_response.get("text", "")
        if not first_draft:
            logger.warning("Der Schreiber-Agent hat einen leeren Entwurf erstellt.")
            return "Es tut mir leid, ich konnte keinen Entwurf für die Geschichte erstellen."
    except Exception as e:
        logger.error(f"Fehler in der Schreiber-Phase: {e}", exc_info=True)
        return f"Ein Fehler ist beim Erstellen des Entwurfs aufgetreten: {e}"

    # STUFE 3: Lektor
    logger.info("Creative Writer: Übergebe Entwurf an den Lektor-Agenten zur Verfeinerung...")
    lektor_model = "gpt-4o-mini" if provider == "openai" else model

    lektor_prompt = (
        "Du bist ein strenger und detailverliebter Lektor. Deine Aufgabe ist es, den folgenden Textentwurf zu analysieren und zu verbessern. "
        "Konzentriere dich auf folgende Punkte:\n"
        "1.  **Unpassende Metaphern:** Finde Bilder oder Vergleiche, die physikalisch oder logisch keinen Sinn ergeben (z.B. \"Licht widerhallen\"). Ersetze sie durch präzisere und stimmigere Formulierungen.\n"
        "2.  **'Unmenschliche' Sprache:** Identifiziere Sätze, die unbeholfen oder unnatürlich klingen. Formuliere sie neu, damit sie flüssiger und menschlicher wirken.\n"
        "3.  **Logische Konsistenz:** Achte auf kleine logische Brüche in der Handlung oder in den Beschreibungen.\n\n"
        "Gib als Ergebnis NUR den finalen, polierten und verbesserten Text zurück. Füge keine Kommentare oder Erklärungen hinzu.\n\n"
        f"**TEXTENTWURF ZUR ÜBERARBEITUNG:**\n---\n{first_draft}\n---\n\n**VERBESSERTE VERSION:**\n"
    )
    
    lektor_response = await OpenAIServiceProvider().call_llm(
        api_key,
        lektor_model,
        messages=[{"role": "user", "content": lektor_prompt}],
    )
    final_text = lektor_response.get("text", first_draft).strip()
    logger.info("Creative Writer: Lektor-Phase abgeschlossen.")

    # --- NEU START: STUFE 4 - Regie-Phase ---
    # Wir rufen den neuen Agenten auf, um den finalen Text für die Vertonung vorzubereiten.
    final_text_with_directions = await add_vocal_directions(final_text, api_key, model)
    # --- NEU ENDE ---
    
    logger.info(f"Creative Writer: Lektor-Phase abgeschlossen. Gebe finale Version zurück.")
    
    # Wir geben den Text mit den Regieanweisungen zurück
    return final_text_with_directions
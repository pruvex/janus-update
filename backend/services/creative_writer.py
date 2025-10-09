from . import rag_manager
from .llm_gateway import call_llm
import logging

logger = logging.getLogger("janus_backend")


async def creative_writer(
    prompt: str, provider: str, model: str, api_key: str, style: str
):
    # === SCHRITT 1: Wissensbasis auswählen (wie bisher) ===
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
            llm_response = await call_llm(
                provider,
                selection_model,
                api_key,
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

    # === SCHRITT 2: RAG-Kontext abrufen (wie bisher) ===
    retrieved_context = []
    if selected_collection:
        retrieved_context = rag_manager.query_knowledge_base(
            prompt, collection_name=selected_collection, n_results=7
        )

    # === SCHRITT 3: Der Schreiber-Agent (mit verbessertem Prompt - Strategie 2) ===

    # Verbessertes Prompt-Engineering
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
        draft_response = await call_llm(
            provider,
            model,
            api_key,
            messages=[{"role": "user", "content": schreiber_prompt}],
        )
        first_draft = draft_response.get("text", "")
        if not first_draft:
            logger.warning("Der Schreiber-Agent hat einen leeren Entwurf erstellt.")
            return "Es tut mir leid, ich konnte keinen Entwurf für die Geschichte erstellen."
    except Exception as e:
        logger.error(f"Fehler in der Schreiber-Phase: {e}", exc_info=True)
        return f"Ein Fehler ist beim Erstellen des Entwurfs aufgetreten: {e}"

    # === SCHRITT 4: Der Lektor-Agent (Strategie 3) ===

    logger.info(
        "Creative Writer: Übergebe Entwurf an den Lektor-Agenten zur Verfeinerung..."
    )

    # Wir können für den Lektor ein schnelles und günstiges Modell verwenden
    lektor_model = "gpt-4o-mini" if provider == "openai" else model

    lektor_prompt = f"""Du bist ein strenger und detailverliebter Lektor. Deine Aufgabe ist es, den folgenden Textentwurf zu analysieren und zu verbessern. Konzentriere dich auf folgende Punkte:
1.  **Unpassende Metaphern:** Finde Bilder oder Vergleiche, die physikalisch oder logisch keinen Sinn ergeben (z.B. "Licht widerhallen"). Ersetze sie durch präzisere und stimmigere Formulierungen.
2.  **'Unmenschliche' Sprache:** Identifiziere Sätze, die unbeholfen oder unnatürlich klingen. Formuliere sie neu, damit sie flüssiger und menschlicher wirken.
3.  **Logische Konsistenz:** Achte auf kleine logische Brüche in der Handlung oder in den Beschreibungen.

Gib als Ergebnis NUR den finalen, polierten und verbesserten Text zurück. Füge keine Kommentare oder Erklärungen hinzu.

**TEXTENTWURF ZUR ÜBERARBEITUNG:**
---
{first_draft}
---

**VERBESSERTE VERSION:**
"""

    try:
        final_response = await call_llm(
            provider,
            lektor_model,
            api_key,
            messages=[{"role": "user", "content": lektor_prompt}],
        )
        final_version = final_response.get(
            "text", first_draft
        ).strip()  # Fallback auf den ersten Entwurf

        logger.info(
            "Creative Writer: Lektor-Phase abgeschlossen. Gebe finale Version zurück."
        )
        return final_version

    except Exception as e:
        logger.error(f"Fehler in der Lektor-Phase: {e}", exc_info=True)
        logger.warning(
            "Lektor-Phase fehlgeschlagen. Gebe den unkorrigierten ersten Entwurf zurück."
        )
        return first_draft  # Wichtig: Im Fehlerfall geben wir den guten ersten Entwurf zurück

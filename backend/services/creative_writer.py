# backend/services/creative_writer.py

import asyncio
import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict, Optional

from backend.services import llm_gateway, rag_manager
from backend.tool_registry import TOOL_REGISTRY
from backend.services.tool_manager import tool_manager
from backend.utils import intent_classifier  # <-- DIESE ZEILE HINZUFÜGEN
from backend.utils.paths import resource_path

logger = logging.getLogger("janus_backend")

# ==============================================================================
#  HELFERFUNKTIONEN
# ==============================================================================


@lru_cache(maxsize=1)
def load_style_profiles() -> Dict[str, Any]:
    """Lädt die manuell erstellten Stil-Profile aus der JSON-Datei und speichert sie im Cache."""
    profiles_path = resource_path("backend/config/style_profiles.json")
    if not os.path.exists(profiles_path):
        logger.warning(f"Stil-Profil-Datei nicht gefunden unter {profiles_path}")
        return {}
    try:
        with open(profiles_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Stil-Profile: {e}")
        return {}


def load_prompt_template(filename: str) -> str:
    """Lädt eine Prompt-Vorlage aus dem prompts-Verzeichnis."""
    template_path = resource_path(f"backend/prompts/{filename}")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt-Vorlage nicht gefunden: {template_path}")
        return ""


def _extract_json(text: str) -> Optional[Any]:
    """Extrahiert die erste valide JSON-Struktur (Objekt oder Array) aus einem Text."""
    json_starters = ["[", "{"]
    for starter in json_starters:
        start_index = text.find(starter)
        if start_index == -1:
            continue
        closer = "]" if starter == "[" else "}"
        depth = 0
        for i, char in enumerate(text[start_index:], start=start_index):
            if char == starter:
                depth += 1
            elif char == closer:
                depth -= 1
                if depth == 0:
                    json_string = text[start_index : i + 1]
                    try:
                        return json.loads(json_string)
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"JSON-Decode-Fehler trotz balancierter Klammern: {e}. String war: '{json_string}'"
                        )
                        continue
    return None


def _strip_markdown_json_fences(text: str) -> str:
    """Entfernt ```json ... ``` bzw. ``` ... ``` Code-Fences aus LLM-Antworten."""
    cleaned = (text or "").strip()
    if not cleaned.startswith("```"):
        return cleaned

    lines = cleaned.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


# ==============================================================================
#  META-AGENTEN (Analyse & Forschung)
# ==============================================================================


async def analyze_creative_request(
    prompt: str, api_key: str, model: str, provider: str
) -> Dict[str, Any]:
    # (Diese Funktion bleibt unverändert, nutzt aber _extract_json)
    logger.info(
        "Creative Director: Kein manuelles Profil gefunden. Führe dynamische Analyse durch..."
    )
    analysis_prompt_template = load_prompt_template(
        "analyze_creative_request.prompt"
    )  # Annahme: prompt existiert
    analysis_prompt = (
        analysis_prompt_template.format(prompt=prompt)
        if analysis_prompt_template
        else f"Analysiere: '{prompt}'"
    )

    try:
        response = await llm_gateway.call_llm(
            provider, model, api_key, messages=[{"role": "user", "content": analysis_prompt}]
        )
        analysis_result = _extract_json(response.get("text", "{}"))
        if not isinstance(analysis_result, dict) or not analysis_result:
            raise ValueError("Leere oder invalide Analyse-Antwort von LLM.")
        logger.info(f"Dynamisches Analyse-Ergebnis: {analysis_result}")
        return analysis_result
    except ValueError as e:
        logger.error(f"Fehler bei der dynamischen Kreativ-Analyse: {e}", exc_info=True)
        return {
            "genre": "Kurzgeschichte",
            "author_style": "N/A",
            "key_elements": ["Spannungsaufbau", "Charakterentwicklung"],
            "complexity": "komplex",
        }


async def generate_style_profile_from_rag(
    collection_name: str, api_key: str, model: str, provider: str
) -> dict:
    """
    Analysiert Textproben aus einer RAG-Datenbank UND nutzt eine Websuche zur Kontextanreicherung,
    um ein hochqualitatives Stil-Profil zu generieren.
    """
    logger.info(
        f"Meta-Agent (Forscher): Starte Stilanalyse für RAG-Collection '{collection_name}'."
    )

    # 1. Sammle Textproben aus der RAG-Datenbank
    try:
        text_samples = rag_manager.get_all_documents_from_collection(collection_name, limit=15)
        if not text_samples:
            raise FileNotFoundError(
                f"Keine Dokumente in der Collection '{collection_name}' gefunden."
            )
        corpus = "\n\n---\n\n".join(text_samples)
        max_length = 8000  # Wir kürzen den Corpus etwas, um Platz für die Suchergebnisse zu lassen
        if len(corpus) > max_length:
            corpus = corpus[:max_length]
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von Dokumenten aus Collection '{collection_name}': {e}")
        raise

    # 2. NEU: Führe eine Websuche zur Kontextanreicherung durch
    web_search_context = "Keine zusätzlichen Informationen gefunden."
    try:
        # Wir versuchen, einen relevanten Namen aus dem Corpus zu erraten (oft im Text erwähnt)
        # Dies ist eine einfache Heuristik, die man verfeinern könnte.
        author_guess = collection_name  # Oft ist der Collection-Name der Autorenname
        canonical_websearch_skill = "system.websearch"

        logger.info(f"Meta-Agent: Führe Websuche für Kontext zu '{author_guess}' durch.")
        websearch_tool = next(
            (
                tool_def
                for tool_name, tool_def in TOOL_REGISTRY.items()
                if tool_manager.get_skill_id(tool_name) == canonical_websearch_skill
            ),
            None,
        )
        if websearch_tool:
            # Wir rufen die Funktion direkt auf
            search_query = f"Schreibstil und typische Genre von {author_guess}"
            tool_output = await websearch_tool.func(websearch_args={"query": search_query})
            web_search_context = tool_output.get("text", "Keine Ergebnisse.")
        else:
            logger.warning("Websearch-Tool nicht im Tool-Registry gefunden.")

    except Exception as e:
        logger.error(f"Meta-Agent: Fehler bei der Websuche: {e}", exc_info=True)

    # 3. Erstelle den neuen, verbesserten Meta-Prompt
    meta_prompt = (
        "Du bist ein hochintelligenter Literaturanalyst. Deine Aufgabe ist es, aus ZWEI Quellen ein detailliertes Stil-Profil im JSON-Format zu extrahieren. "
        "Dieses Profil wird als Anweisung für andere KI-Agenten dienen.\n\n"
        "**QUELLE 1: Der Textkorpus.** Dies ist die primäre Wahrheit. Analysiere die Prosa, den Satzbau und den Ton direkt aus diesen Texten.\n"
        "**QUELLE 2: Die Web-Recherche.** Nutze diese Informationen, um den Kontext zu verstehen, den Autor und das Genre zu validieren und deine Analyse zu untermauern.\n\n"
        "Das JSON MUSS exakt die folgenden Felder enthalten:\n"
        "1. `genre`: Eine prägnante Beschreibung des Genres (z.B. 'Krimi', 'Horror / Thriller').\n"
        "2. `author_style`: Der Name des Autors oder der Stilrichtung (z.B. 'Arthur Conan Doyle', 'Stephen King').\n"
        "3. `key_elements`: Eine Liste von 3-4 prägnanten, umsetzbaren stilistischen Merkmalen.\n"
        "4. `complexity`: Entweder 'einfach' oder 'komplex'.\n\n"
        "Analysiere beide Quellen und gib NUR das fertige JSON-Objekt als Antwort zurück.\n\n"
        f"--- QUELLE 1: TEXTKORPUS ---\n{corpus}\n\n"
        f"--- QUELLE 2: WEB-RECHERCHE ---\n{web_search_context}\n\n"
        "--- JSON-STIL-PROFIL ---"
    )

    # 4. Rufe das LLM auf und parse die Antwort (mit der robusten Methode)
    try:
        response = await llm_gateway.call_llm(
            provider, model, api_key, messages=[{"role": "user", "content": meta_prompt}]
        )
        llm_response_text = response.get("text", "")
        cleaned_response_text = _strip_markdown_json_fences(llm_response_text)

        style_profile_result = None
        try:
            style_profile_result = json.loads(cleaned_response_text)
        except (json.JSONDecodeError, TypeError):
            style_profile_result = _extract_json(cleaned_response_text)

        if isinstance(style_profile_result, str):
            style_profile_result = _extract_json(style_profile_result)

        if not isinstance(style_profile_result, dict):
            raise ValueError(
                f"Keine JSON-Struktur in der LLM-Antwort gefunden. Antwort war: '{llm_response_text}'"
            )

        logger.info(
            f"Meta-Agent hat Stil-Profil (mit Web-Kontext) erfolgreich generiert: {style_profile_result}"
        )
        return style_profile_result
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Meta-Agent konnte die LLM-Antwort nicht als JSON parsen. Fehler: {e}")
        raise ValueError("Konnte kein valides Stil-Profil aus der LLM-Antwort erstellen.") from e


# ==============================================================================
#  REGISSEUR- UND SCHREIBER-AGENT
# ==============================================================================


async def create_story_screenplay(
    prompt: str, style_info: dict, api_key: str, model: str, provider: str
) -> list:
    # (Bleibt unverändert, nutzt aber _extract_json)
    logger.info(
        "Regisseur-Agent (Version 2.1): Erstelle detailliertes Drehbuch für die Geschichte..."
    )
    screenplay_prompt_template = load_prompt_template("create_story_screenplay.prompt")
    if not screenplay_prompt_template:
        return []
    screenplay_prompt = screenplay_prompt_template.format(
        style_author=style_info.get("author_style", "N/A"),
        prompt=prompt,
        style_elements=", ".join(style_info.get("key_elements", [])),
    )
    try:
        response = await llm_gateway.call_llm(
            provider, model, api_key, messages=[{"role": "user", "content": screenplay_prompt}]
        )
        screenplay = _extract_json(response.get("text", "[]"))
        if not isinstance(screenplay, list):
            raise ValueError("Keine JSON-Array-Struktur in der Drehbuch-Antwort.")
        logger.info(f"Regisseur-Agent V2.1 hat ein Drehbuch mit {len(screenplay)} Szenen erstellt.")
        return screenplay
    except ValueError as e:
        logger.error(
            f"Regisseur-Agent V2.1 konnte kein valides Drehbuch erstellen. Fehler: {e}",
            exc_info=True,
        )
        return []


async def write_scene(scene_prompt: str, api_key: str, model: str, provider: str) -> str:
    # (Bleibt unverändert)
    logger.info(f"Schreiber-Agent: Schreibe Szene basierend auf Prompt: '{scene_prompt[:80]}...'")
    messages = [
        {
            "role": "system",
            "content": "Du bist ein talentierter Ghostwriter. Schreibe exakt das, was der folgende Prompt von dir verlangt. Füge keine eigenen Kommentare, Titel oder Einleitungen hinzu. Beginne direkt mit dem Text der Szene.",
        },
        {"role": "user", "content": scene_prompt},
    ]
    response = await llm_gateway.call_llm(provider, model, api_key, messages=messages)
    return response.get("text", "").strip()


# ==============================================================================
#  POST-PRODUKTION (NEUE, KONSOLIDIERTE PIPELINE)
# ==============================================================================


async def master_editor(
    text: str, style_info: dict, api_key: str, model: str, provider: str, critique: str
) -> str:
    """Ein konsolidierter "Super-Lektor", der basierend auf vorgegebener Kritik überarbeitet."""
    editor_prompt_template = load_prompt_template("master_editor.prompt")
    if not editor_prompt_template:
        return text
    editor_prompt = editor_prompt_template.format(
        style_author=style_info.get("author_style", "N/A"),
        style_genre=style_info.get("genre", "unbekannt"),
        style_elements=", ".join(style_info.get("key_elements", [])),
        critique=critique,
        text=text,
    )
    response = await llm_gateway.call_llm(
        provider, model, api_key, messages=[{"role": "user", "content": editor_prompt}]
    )
    return response.get("text", text).strip()


async def self_critique_and_refine(
    text: str, style_info: dict, api_key: str, provider: str, critique_model: str, editor_model: str
) -> str:
    """Führt einen zweistufigen Prozess aus: Kritik und anschließende Überarbeitung."""
    logger.info("-> Starte Self-Critique-Prozess...")
    critique_prompt_template = load_prompt_template("critique_prose.prompt")
    if not critique_prompt_template:
        return await master_editor(
            text, style_info, api_key, editor_model, provider, "Keine Kritikpunkte vorhanden."
        )

    critique_prompt = critique_prompt_template.format(text=text)
    critique_response = await llm_gateway.call_llm(
        provider, critique_model, api_key, messages=[{"role": "user", "content": critique_prompt}]
    )
    critique = critique_response.get("text", "Keine wesentlichen Probleme gefunden.").strip()
    logger.info(f"-> Kritiker-Agent hat folgende Punkte identifiziert:\n{critique}")

    if "Keine wesentlichen Probleme gefunden" in critique:
        logger.info("-> Keine Probleme gefunden. Szene wird beibehalten.")
        return text

    logger.info("-> Übergebe Szene und Kritik an den Master-Editor zur finalen Überarbeitung...")
    final_scene = await master_editor(text, style_info, api_key, editor_model, provider, critique)
    return final_scene


async def add_ssml_directions(text: str, api_key: str, model: str, provider: str) -> str:
    """
    Ein spezialisierter Agent, der einen reinen Text in SSML (Speech Synthesis Markup Language)
    umwandelt, um Pausen, Betonung und Rhythmus für die Audio-Vertonung zu steuern.
    """
    logger.info("Creative Writer: Übergebe Text an den SSML-Regie-Agenten...")

    # Annahme: Sie erstellen eine neue Prompt-Datei namens 'generate_ssml.prompt'
    ssml_prompt_template = load_prompt_template("generate_ssml.prompt")
    if not ssml_prompt_template:
        logger.warning("SSML-Prompt-Template nicht gefunden. Gebe reinen Text zurück.")
        return text

    # Um XML-Probleme im Prompt zu vermeiden, ersetzen wir spitze Klammern im Rohtext
    escaped_text = text.replace("<", "&lt;").replace(">", "&gt;")

    ssml_prompt = ssml_prompt_template.format(text=escaped_text)

    try:
        response = await llm_gateway.call_llm(
            provider, model, api_key, messages=[{"role": "user", "content": ssml_prompt}]
        )
        ssml_output = response.get("text", text).strip()

        # Sicherheitsprüfung: Stellt sicher, dass die Antwort valides XML/SSML ist
        if not ssml_output.startswith("<speak>") or not ssml_output.endswith("</speak>"):
            logger.warning(
                "SSML-Agent hat kein valides SSML zurückgegeben. Fallback auf reinen Text."
            )
            return text

        logger.info("SSML-Regieanweisungen erfolgreich generiert.")
        return ssml_output
    except Exception as e:
        logger.error(f"Fehler im SSML-Regie-Agenten: {e}", exc_info=True)
        return text  # Fallback auf den reinen Text bei Fehlern


# ==============================================================================
#  NEUE WORKER-FUNKTION FÜR PARALLELE VERARBEITUNG
# ==============================================================================


async def _process_single_scene(
    scene: dict,
    scene_index: int,
    total_scenes: int,
    style_info: dict,
    context: Optional[str],
    api_key: str,
    provider: str,
    writer_model: str,
    critique_model: str,
    editor_model: str,
) -> str:
    """Asynchrone Pipeline zur Verarbeitung einer einzelnen Szene: Schreiben -> Kritisieren -> Überarbeiten."""
    scene_prompt = scene.get("prompt_for_writer_agent")
    if not scene_prompt:
        return ""

    logger.info(
        f"Starte Verarbeitung für Szene {scene_index}/{total_scenes}: '{scene.get('scene_name')}'..."
    )

    enriched_scene_prompt = f"{scene_prompt}\n\nNUTZE FÜR INSPIRATION DEN FOLGENDEN KONTEXT:\n---\n{context or 'Kein zusätzlicher Kontext.'}\n---"
    raw_scene_part = await write_scene(enriched_scene_prompt, api_key, writer_model, provider)

    final_scene = await self_critique_and_refine(
        raw_scene_part, style_info, api_key, provider, critique_model, editor_model
    )

    logger.info(f"Szene {scene_index}/{total_scenes} erfolgreich abgeschlossen.")
    return final_scene


# ==============================================================================
#  DER "CREATIVE DIRECTOR" (HAUPTFUNKTION) - JETZT MIT PARALLELISIERUNG
# ==============================================================================


async def creative_writer(
    prompt: str,
    provider: str,
    model: str,
    api_key: str,
    style: str = "geschichte",
) -> str:
    # --- START: NEUE, ROBUSTE INTENT-ERKENNUNG ---
    is_image_request = intent_classifier._is_image_generation_request(prompt)

    if is_image_request:
        logger.info(
            f"Creative Writer: Anfrage als Bildgenerierung erkannt für Provider '{provider}'."
        )
        # Wir rufen direkt den llm_gateway auf, der die provider-spezifische Logik kennt
        response = await llm_gateway.generate_image(
            provider=provider,
            model_id=model,  # Das vom User gewählte Modell sollte die Info haben, welches Bild-Modell zu nutzen ist
            api_key=api_key,
            prompt=prompt,
        )
        # Wir geben hier bewusst nur eine Erfolgsmeldung zurück, da die main.py das Bildhandling übernimmt.
        # Für eine Text-zu-Text-Ausgabe würde dies nicht funktionieren, aber für Text-zu-Bild ist es ok.
        if response.get("image_url"):
            return f"Bild wurde erfolgreich mit {provider.capitalize()} generiert."
        else:
            return f"Fehler bei der Bildgenerierung mit {provider.capitalize()}."
    # --- ENDE: NEUE, ROBUSTE INTENT-ERKENNUNG ---

    # Die folgende Logik wird jetzt nur noch für TEXT-Anfragen ausgeführt
    style_profiles = load_style_profiles()
    prompt_lower = prompt.lower()
    style_key = None
    if "haiku" in prompt_lower:
        style_key = "Haiku"
    elif "holmes" in prompt_lower or "doyle" in prompt_lower:
        style_key = "ArthurConanDoyle"
    elif "warhammer" in prompt_lower or "space marine" in prompt_lower:
        style_key = "Warhammer40k"
    elif "stephen king" in prompt_lower or "king-stil" in prompt_lower:
        style_key = "StephenKing"

    style_info = None
    if style_key and style_key in style_profiles:
        logger.info(f"Manuelles Stil-Profil '{style_key}' gefunden und geladen.")
        style_info = style_profiles[style_key]
    else:
        style_info = await analyze_creative_request(prompt, api_key, model, provider)

    # Globaler Kontext-Abruf als Fallback (bleibt unverändert)
    context = None
    collection_name = style_info.get("author_style", "N/A").replace(" ", "")
    available_collections = rag_manager.list_collections()
    if collection_name in available_collections:
        logger.info(
            f"Globale RAG-Bibliothek '{collection_name}' gefunden. Frage initiales Wissen ab..."
        )
        rag_result = rag_manager.query_knowledge_base(query_text=prompt, n_results=15)
        if rag_result.status == "ok":
            ctx = (rag_result.data or {}).get("context")
            if ctx:
                context = ctx

    if style_info.get("complexity") == "einfach":
        logger.info("Führe einfachen Kreativ-Workflow aus.")
        simple_prompt = f"Schreibe ein {style_info.get('genre')} zum Thema '{prompt}' im Stil von {style_info.get('author_style', 'einem neutralen Dichter')}. Gib das Ergebnis direkt als Text im Chat aus und benutze dafür keine Werkzeuge."
        response = await llm_gateway.call_llm(
            provider, model, api_key, messages=[{"role": "user", "content": simple_prompt}]
        )
        # Für einfache Anfragen wie Haiku wollen wir kein SSML
        return response.get("text", "Ich konnte leider keinen Text erstellen.").strip()

    else:
        logger.info(
            f"Starte optimierten, parallelen Regisseur-Workflow für Genre '{style_info.get('genre')}'."
        )

        writer_model = model
        editor_model = model
        critique_model = (
            "gpt-5.4-nano" if provider == "openai" else "gemini-3-flash-preview"
        )  # Using internal model aliases

        logger.info(f"Modell-Setup: Writer/Editor -> {writer_model}, Kritiker -> {critique_model}")

        screenplay = await create_story_screenplay(prompt, style_info, api_key, model, provider)
        if not screenplay:
            return (
                "Entschuldigung, ich konnte keinen kreativen Plan für diese Geschichte entwickeln."
            )

        tasks = []
        total_scenes = len(screenplay)
        for i, scene in enumerate(screenplay, 1):
            scene_context = context
            scene_prompt_for_rag = scene.get("prompt_for_writer_agent", prompt)

            if collection_name in available_collections:
                logger.info(
                    f"[Szene {i}] Passende RAG-Bibliothek '{collection_name}' gefunden. Frage Wissen für diese Szene ab..."
                )
                scene_rag = rag_manager.query_knowledge_base(
                    query_text=scene_prompt_for_rag, n_results=15
                )
                if scene_rag.status == "ok":
                    sctx = (scene_rag.data or {}).get("context")
                    if sctx:
                        scene_context = sctx

            task = _process_single_scene(
                scene=scene,
                scene_index=i,
                total_scenes=total_scenes,
                style_info=style_info,
                context=scene_context,
                api_key=api_key,
                provider=provider,
                writer_model=writer_model,
                critique_model=critique_model,
                editor_model=editor_model,
            )
            tasks.append(task)

        logger.info(f"Starte parallele Verarbeitung von {len(tasks)} Szenen...")
        polished_scenes = await asyncio.gather(*tasks)
        logger.info("Alle Szenen-Pipelines parallel abgeschlossen.")

        polished_story = "\n\n".join(filter(None, polished_scenes))

        final_ssml_output = await add_ssml_directions(polished_story, api_key, model, provider)

        logger.info("Alle Phasen des optimierten Regisseur-Workflows abgeschlossen.")
        return final_ssml_output

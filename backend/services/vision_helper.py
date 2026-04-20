import logging
import base64
import json
import re
from backend.services import llm_gateway
from backend.services.quality_gate import quality_gate_service
from backend.services import cost_service, cost_calculator

logger = logging.getLogger("janus_backend")


OBJECT_ONLY_PROMPT = (
    "Analysiere das Bild auf Kleidung, Accessoires, sichtbare Szene-Elemente und Pose-Hinweise. "
    "Erstelle eine JSON-Liste: [{'name': '...', 'color': '...', 'material': '...', 'details': '...'}]. "
    "Regel: Nur Objekte aufnehmen, die physisch vorhanden und deutlich sichtbar sind. "
    "Nimm auch klar sichtbare Umgebungsobjekte auf (z.B. Geländer, Glasfassade, Straße, Gebäude) "
    "sowie markante sichtbare Beauty-Details (z.B. roter Lippenstift), falls eindeutig erkennbar. "
    "Wenn keine Details erkennbar sind, lasse das Feld leer. "
    "Gib NUR das JSON-Array zurück, keinen Text davor oder danach."
)

OBJECT_FALLBACK_PROMPT = (
    "Analysiere Kleidung, Accessoires, Materialien, Muster, sichtbare Szeneobjekte, Pose und Perspektive des Bildes. "
    "Erzeuge ein JSON-Array mit Objekten im Format "
    "[{'name':'...','color':'...','material':'...','details':'...'}]. "
    "Wenn sichtbar, erfasse auch Umgebungsanker wie Geländer, Glasfassade, Gebäude, Straße und eindeutige Make-up-Signale wie Lippenstift. "
    "Falls Details unsicher sind, nutze 'details' für beobachtbare Hinweise (z.B. Hibiskus-Print, Lackleder, Fisheye/Weitwinkel). "
    "Gib NUR das JSON-Array zurück."
)


def _extract_json_array(text: str):
    payload = (text or "").strip()
    if not payload:
        return []

    if "```" in payload:
        payload = payload.replace("```json", "").replace("```", "").strip()

    for candidate in (payload, re.search(r"\[[\s\S]*\]", payload).group(0) if re.search(r"\[[\s\S]*\]", payload) else ""):
        if not candidate:
            continue
        normalized = candidate.replace("'", '"')
        try:
            parsed = json.loads(normalized)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            continue

    return []


async def analyze_image_with_cloud(image_base64, provider, api_key):
    """Runs a strict object-only cloud vision pass and returns a normalized dictionary."""
    if not image_base64 or not api_key:
        return {"objects": []}

    try:
        base64_payload = image_base64.split(",", 1)[1] if "," in image_base64 else image_base64
        data_url = f"data:image/jpeg;base64,{base64_payload}"
        model_mapping = {
            "openai": "gpt-4o",
            "gemini": "gemini-3-flash-preview",
        }
        model_id = model_mapping.get(provider, "gpt-4o")
        response = await llm_gateway.call_llm(
            provider=provider,
            model_id=model_id,
            api_key=api_key,
            messages=[{"role": "user", "content": OBJECT_ONLY_PROMPT}],
            image_data=data_url,
            is_image_analysis_request=True,
            max_tokens=1200,
        )
        raw_text = response.get("text") or ""
        if not raw_text and response.get("tool_calls"):
            raw_text = json.dumps(response["tool_calls"], ensure_ascii=False)
        objects = _extract_json_array(raw_text)

        if not objects:
            fallback_response = await llm_gateway.call_llm(
                provider=provider,
                model_id=model_id,
                api_key=api_key,
                messages=[{"role": "user", "content": OBJECT_FALLBACK_PROMPT}],
                image_data=data_url,
                is_image_analysis_request=True,
                max_tokens=1400,
            )
            fallback_text = fallback_response.get("text") or ""
            if not fallback_text and fallback_response.get("tool_calls"):
                fallback_text = json.dumps(fallback_response["tool_calls"], ensure_ascii=False)
            objects = _extract_json_array(fallback_text)
            if not objects and fallback_text.strip():
                objects = [
                    {
                        "name": "scene-observation",
                        "color": "",
                        "material": "",
                        "details": fallback_text.strip(),
                    }
                ]

        normalized = []
        for item in objects:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            details = str(item.get("details", "")).strip()

            if name.lower() == "scene-observation" and details.startswith("["):
                nested = _extract_json_array(details)
                if nested:
                    for nested_item in nested:
                        if not isinstance(nested_item, dict):
                            continue
                        normalized.append(
                            {
                                "name": str(nested_item.get("name", "")).strip(),
                                "color": str(nested_item.get("color", "")).strip(),
                                "material": str(nested_item.get("material", "")).strip(),
                                "details": str(nested_item.get("details", "")).strip(),
                            }
                        )
                    continue

            normalized.append(
                {
                    "name": name,
                    "color": str(item.get("color", "")).strip(),
                    "material": str(item.get("material", "")).strip(),
                    "details": details,
                }
            )
        return {"objects": normalized}
    except Exception as e:
        logger.error(f"Fehler in analyze_image_with_cloud: {e}")
        return {"objects": []}

async def analyze_image_strict_provider(provider, api_key, base64_image, db, profile, media_type="image/jpeg"):
    """
    Nutzt den existierenden quality_gate_service aus dem Image Studio.
    Inklusive exakt gleichem Cost-Tracking.
    """
    try:
        # Base64 zu Bytes (wie es der Service erwartet)
        if "," in base64_image:
            base64_image = base64_image.split(",")[1]
        image_bytes = base64.b64decode(base64_image)

        # --- REUSE: Quality Gate Service aufrufen ---
        evaluation = await quality_gate_service.evaluate_image(
            provider=provider,
            api_key=api_key,
            image_bytes=image_bytes,
            prompt=profile.ANALYSIS_PROMPT,
            force_json_schema=False # Wir wollen Text, kein JSON
        )

        # --- REUSE: Cost Tracking (Exakt wie in images.py) ---
        usage_data = evaluation.get("usage")
        model_used = evaluation.get("model")
        
        if usage_data and model_used:
            try:
                # Berechne Kosten mit dem zentralen Calculator
                _, cost_info = cost_calculator.calculate_cost(
                    model_id=model_used, 
                    usage_data=usage_data
                )
                
                cost_service.create_cost_entry(
                    db=db,
                    amount=cost_info.get("total_cost", 0.0),
                    model=model_used,
                    provider=provider,
                    source_type="chat_vision_bridge", # Markierung für das Dashboard
                    input_tokens=usage_data.get("input_tokens", 0),
                    output_tokens=usage_data.get("output_tokens", 0)
                )
            except Exception as cost_e:
                logger.warning(f"Cost tracking failed in vision bridge: {cost_e}")

        # Die "Suggestion" des Quality-Gates enthält bei diesem Prompt die Bildbeschreibung
        return evaluation.get("suggestion", "")

    except Exception as e:
        logger.error(f"Fehler in der Image-Studio-Bridge: {e}")
        return ""

import base64
import io
import logging
from typing import Dict

import openai
from PIL import Image
from backend.services import image_manager
from backend.services.cost_calculator import calculate_cost
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from openai import APIStatusError, APITimeoutError, BadRequestError

logger = logging.getLogger("janus_backend")


def _is_retryable_error(e):
    """Gibt True zurück, wenn es sich um einen Serverfehler/Timeout handelt, sonst False."""
    # NICHT wiederholen bei 4xx-Client-Fehlern (z.B. "Invalid ID", Content Policy)
    if isinstance(e, BadRequestError):
        logger.warning(f"OpenAI Client Error (400) - KEIN Retry: {e}")
        return False
    # Wiederholen bei 5xx-Server-Fehlern
    if isinstance(e, APIStatusError):
        is_server_error = e.status_code >= 500
        if is_server_error:
            logger.warning(f"OpenAI Server Error ({e.status_code}) - Starte Retry...")
        return is_server_error
    # Wiederholen bei Timeouts
    if isinstance(e, APITimeoutError):
        logger.warning("OpenAI Timeout Error - Starte Retry...")
        return True
    
    logger.warning(f"Unbekannter Fehlertyp für Retry-Logik: {type(e)}")
    return False  # Standard: Bei unbekannten Fehlern nicht wiederholen


def _calculate_and_log_cost(model_id_base: str, usage_data: dict = None, custom_prompt: str = None):
    """Helper to calculate and log cost."""
    quality = usage_data.get("quality", "medium")
    size = usage_data.get("size", "1024x1024")
    full_model_id_for_catalog_lookup = model_id_base
    
    updated_usage_data = usage_data.copy() if usage_data else {}
    updated_usage_data["quality"] = quality
    updated_usage_data["size"] = size

    usage, cost = calculate_cost(full_model_id_for_catalog_lookup, updated_usage_data, custom_prompt)
    logger.info(
        f"\n--- USAGE TRACKING ---\n"
        f"Model: {full_model_id_for_catalog_lookup}\n"
        f"Input Tokens: {usage.get('input_tokens', 'N/A')}\n"
        f"Output Tokens: {usage.get('output_tokens', 'N/A')}\n"
        f"Image Quality: {usage.get('image_quality', 'N/A')}\n"
        f"Image Size: {usage.get('image_size', 'N/A')}\n"
        f"Total Cost: {cost.get('total_cost', 0):.8f} €\n"
        f"----------------------"
    )
    return usage, cost


class OpenAIImageGeneration:
    """
    Encapsulates the image generation functionality for the OpenAI provider.
    """
    
    def _is_high_risk_portrait(self, prompt: str) -> bool:
        """
        Analysiert, ob der Prompt mit hoher Wahrscheinlichkeit eine Person/Portrait darstellt.
        """
        prompt_lower = prompt.lower()
        
        # Starke Indikatoren für Menschen/Portraits (JETZT MIT DEUTSCH!)
        person_triggers = [
            # Englisch
            "woman", "man", "girl", "boy", "person", "model", "face", "portrait",
            "headshot", "bust", "selfie", "posing", "looking at camera", "eyes",
            "hair", "wearing", "dress", "suit", "fashion", "human", "character",
            # Deutsch
            "frau", "mann", "mädchen", "junge", "person", "model", "gesicht", "porträt",
            "portrait", "aufnahme einer frau", "aufnahme eines mannes", "menschen",
            "kamera", "augen", "haare", "kleid", "anzug", "mode", "charakter", "gestalt"
        ]
        
        if any(trigger in prompt_lower for trigger in person_triggers):
            return True
            
        return False
    
    async def _upload_bytes_to_openai(self, client: openai.AsyncOpenAI, file_bytes: bytes, filename: str = "image.png") -> str:
        """Uploads bytes as a file to OpenAI and returns the file_id."""
        import io
        # Bytes in ein file-like Object verpacken
        file_obj = io.BytesIO(file_bytes)
        file_obj.name = filename # Wichtig für MIME-Type Erkennung der API
        
        try:
            uploaded_file = await client.files.create(
                file=file_obj,
                purpose="vision" # Vision ist der korrekte Zweck für Bild-Inputs
            )
            logger.info(f"Uploaded temp file to OpenAI: {uploaded_file.id}")
            return uploaded_file.id
        except Exception as e:
            logger.error(f"Failed to upload file to OpenAI: {e}")
            raise e
    
    async def introduce_image(self, api_key: str, image_bytes: bytes):
        """
        Registers an uploaded image with OpenAI for subsequent editing.
        """
        client = openai.AsyncOpenAI(api_key=api_key)
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        try:
            response = await client.responses.create(
                model="gpt-5-nano",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": "Register this uploaded image for editing."},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/png;base64,{base64_image}"
                            }
                        ]
                    }
                ],
                tools=[{"type": "image_generation", "model": "gpt-image-1.5"}]
            )
            
            image_call = next(
                (o for o in response.output if hasattr(o, 'type') and o.type == "image_generation_call"),
                None
            )
            
            return {
                "previous_response_id": response.id,
                "previous_image_id": image_call.id if image_call else response.id
            }
            
        except Exception as e:
            logger.error(f"Error registering image with OpenAI: {str(e)}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(_is_retryable_error)
    )
    async def generate_image(self, api_key: str, model: str, prompt: str, narrative_prompt: str, preset_context: Dict, image_bytes_list: list = None, **kwargs) -> Dict:
        """
        Generates an image using a two-step "Director-Painter" process.
        """
        client = openai.AsyncOpenAI(api_key=api_key)
        
        # --- FIX: Initialisierung GANZ OBEN ---
        # Wir holen das erste Bild aus der Liste, falls vorhanden
        image_bytes = None
        if image_bytes_list and len(image_bytes_list) > 0:
            image_bytes = image_bytes_list[0]

        mask_b64 = kwargs.get("mask_image_data")
        
        # ... jetzt kommt der Inpainting Block ...

        # --- INPAINTING LOGIC (DALL-E 2 FALLBACK - ROBUST) ---
        if mask_b64 and image_bytes:
            logger.info("Mode: Inpainting requested. Falling back to DALL-E 2 for pixel precision.")
            
            # 1. Dekodieren
            if "base64," in mask_b64: mask_b64 = mask_b64.split("base64,")[1]
            mask_raw_bytes = base64.b64decode(mask_b64)

            # 2. Bild zu PNG konvertieren (im Speicher)
            try:
                with Image.open(io.BytesIO(image_bytes)) as img:
                    img = img.convert("RGBA") 
                    # DALL-E 2 Edit braucht exakt quadratische Bilder
                    # Wir croppen es sicherheitshalber zentral, falls es nicht quadratisch ist
                    if img.width != img.height:
                        s = min(img.width, img.height)
                        left = (img.width - s) // 2
                        top = (img.height - s) // 2
                        img = img.crop((left, top, left + s, top + s))
                        img = img.resize((1024, 1024))
                    else:
                        img = img.resize((1024, 1024))

                    image_io = io.BytesIO()
                    img.save(image_io, format="PNG")
                    final_image_bytes = image_io.getvalue()
            except Exception as e:
                logger.error(f"Image Conversion Error: {e}")
                raise ValueError("Fehler beim Verarbeiten des Bildes für Inpainting.")

            # 3. Maske zu PNG konvertieren (im Speicher)
            try:
                with Image.open(io.BytesIO(mask_raw_bytes)) as mask:
                    mask = mask.convert("RGBA")
                    # Muss exakt die gleiche Größe haben wie das Bild
                    mask = mask.resize((1024, 1024))
                    
                    mask_io = io.BytesIO()
                    mask.save(mask_io, format="PNG")
                    final_mask_bytes = mask_io.getvalue()
            except Exception as e:
                logger.error(f"Mask Conversion Error: {e}")
                raise ValueError("Fehler beim Verarbeiten der Maske.")
                
            # 4. API Call mit expliziten Tuples
            try:
                logger.info("Sending Inpainting Request to DALL-E 2...")
                response = await client.images.edit(
                    # Das Tuple-Format (Dateiname, Bytes, Mime-Type) zwingt den Header korrekt zu setzen
                    image=("image.png", final_image_bytes, "image/png"),
                    mask=("mask.png", final_mask_bytes, "image/png"),
                    prompt=prompt, # Hier den Original-Prompt nutzen!
                    n=1,
                    size="1024x1024",
                    model="dall-e-2" 
                )
                
                image_url = response.data[0].url
                
                # Herunterladen
                import httpx
                async with httpx.AsyncClient() as h_client:
                    r = await h_client.get(image_url)
                    img_data = r.content
                    
                saved_url = image_manager.save_image_from_bytes(
                    img_data, description="inpainting_dalle2", file_extension="png"
                )
                
                return {
                    "image_url": saved_url,
                    "previous_response_id": None,
                    "previous_image_id": None,
                    "usage": {"size": "1024x1024", "quality": "standard"},
                    "cost": {"total_cost": 0.020}
                }
                
            except Exception as e:
                logger.error(f"DALL-E 2 Inpainting failed: {e}")
                raise ValueError(f"Inpainting fehlgeschlagen: {str(e)}")

        # --- PROMPT PASSTHROUGH (Diamond Standard) ---
        # Der DirectorService hat bereits den perfekten Prompt (Route A oder B) erstellt.
        # Wir reichen ihn unverändert weiter, damit keine doppelte Logik entsteht.
        final_image_prompt = narrative_prompt
        logger.info("Generator: Using final prompt from Director (Pass-through).")

        # --- MAIN GENERATION (DALL-E 3 / GPT Image) ---

        target_image_model = model
        orchestrator_model = "gpt-5.2"  # Using the most powerful available model for best results
        
        prev_res_id = kwargs.get("previous_response_id")
        prev_img_id = kwargs.get("previous_image_id")
        
        # Backward compatibility: handle single image case
        image_bytes = image_bytes_list[0] if image_bytes_list and len(image_bytes_list) > 0 else None
        has_images = image_bytes_list is not None and len(image_bytes_list) > 0
        is_multi_image = has_images and len(image_bytes_list) > 1
        
        # --- DIAMANTSTANDARD ROUTING: SMART FORMAT & FRAMING ---
        original_size_requested = kwargs.get("size", "1024x1024")
        perform_square_crop = False
        api_request_size = original_size_requested
        
        # Wir greifen nur ein, wenn der User explizit 1:1 (Quadrat) wollte
        if original_size_requested == "1024x1024":
            
            # Entscheidung: Ist es ein Mensch (Risiko) oder ein Objekt (Safe)?
            # Bei Refinements/Inpainting (mask_b64) fassen wir die Größe NICHT an.
            is_refinement = (prev_res_id is not None) or (mask_b64 is not None)
            
            if not is_refinement and self._is_high_risk_portrait(prompt):
                # SZENARIO A: PERSON -> PLAN B AKTIVIEREN
                # Wir bestellen Hochformat, um Kopfraum zu garantieren, und schneiden später zu.
                api_request_size = "1024x1536"  # <--- HIER KORRIGIERT
                perform_square_crop = True
                
                # Prompt-Injektion für Sicherheit (Headroom)
                framing_safety = "wide angle, ample headroom above subject, fully visible head and hair"
                if "Style:" in final_image_prompt:
                    final_image_prompt = final_image_prompt.replace("Style:", f"{framing_safety}. Style:")
                else:
                    final_image_prompt += f". {framing_safety}"
                    
                logger.info(f"Smart Routing [PERSON]: Plan B aktiviert. Bestelle {api_request_size} + Top-Crop.")
            
            else:
                # SZENARIO B: OBJEKT / LANDSCHAFT / INPAINTING -> NATIV SQUARE
                # Wir bleiben bei 1024x1024. DALL-E zentriert Objekte im Quadrat sehr gut.
                # Ein Crop würde hier das Objekt (Apfel) abschneiden.
                
                if not is_refinement:
                    # Prompt-Injektion für Zentrierung
                    centering_safety = "centered composition, whole object fully visible in frame, symmetrical padding"
                    if "Style:" in final_image_prompt:
                        final_image_prompt = final_image_prompt.replace("Style:", f"{centering_safety}. Style:")
                    else:
                        final_image_prompt += f". {centering_safety}"
                
                logger.info(f"Smart Routing [OBJECT/DEFAULT]: Plan B inaktiv. Bestelle natives {api_request_size}.")
        
        selected_quality = kwargs.get("quality", "medium")

        # Tool Definition mit manipulierter Größe
        image_tool = {
            "type": "image_generation",
            "model": target_image_model,
            "size": api_request_size, 
            "quality": selected_quality
        }
        
        if "mini" not in target_image_model:
            image_tool["input_fidelity"] = "high"  # Bessere Erhaltung der Bildkomposition
        
        mask_file_id = None

        try:
            if target_image_model.startswith("gpt-image-"):
                logger.info(f"Responses API Call: Orchestrator={orchestrator_model}, Image-Tool={target_image_model}")
                
                # --- INPAINTING LOGIC (Responses API) ---
                image_file_id = None
                mask_file_id = None
                
                if mask_b64 and image_bytes:
                    logger.info("Mode: DALL-E 3 Inpainting (via Responses API)")
                    
                    # 1. Dekodieren
                    if "base64," in mask_b64: mask_b64 = mask_b64.split("base64,")[1]
                    mask_bytes = base64.b64decode(mask_b64)
                    
                    # 2. Upload (Helper muss in der Klasse sein!)
                    # Wir laden das Originalbild UND die Maske hoch
                    image_file_id = await self._upload_bytes_to_openai(client, image_bytes, "image.png")
                    mask_file_id = await self._upload_bytes_to_openai(client, mask_bytes, "mask.png")

                # --- REQUEST BAUEN ---
                # Initialisiere request_params mit den erforderlichen Feldern
                request_params = { "model": orchestrator_model, "tools": [image_tool] }
                
                if mask_file_id:
                    logger.info(f"Building Inpainting Request with Mask ID: {mask_file_id}")
                    
                    # 1. Das Tool-Objekt muss die Maske direkt enthalten
                    # WICHTIG: Wir erstellen eine KOPIE von image_tool, um das Original nicht zu ändern
                    inpainting_tool = image_tool.copy()
                    
                    # Laut Doku muss 'input_image_mask' direkt im Tool-Objekt stehen (auf Ebene von 'type' und 'quality')
                    # NICHT in 'image_generation' verschachtelt, sondern im Tool-Definition-Block.
                    # ABER: Bei der Responses API ist die Struktur oft: tool -> type -> parameters.
                    # Wir halten uns strikt an das Beispiel:
                    inpainting_tool["input_image_mask"] = {
                        "file_id": mask_file_id
                    }
                    
                    # 2. Der Prompt muss das Originalbild UND den Text enthalten
                    request_params["input"] = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": final_image_prompt},
                                {"type": "input_image", "file_id": image_file_id}
                            ]
                        }
                    ]
                    request_params["tools"] = [inpainting_tool] # Hier ist das modifizierte Tool drin!
                    
                    perform_square_crop = False
                
                # ... (Hier folgt der bestehende Code für Refinement und Edit Mode als 'elif') ...
                elif prev_res_id and prev_res_id.startswith("resp"):
                    logger.info(f"Mode: Refinement via OpenAI Context (History ID: {prev_res_id})")
                    
                    request_params["previous_response_id"] = prev_res_id
                    request_params["input"] = [{"role": "user", "content": [{"type": "input_text", "text": final_image_prompt}]}]
                    
                    perform_square_crop = False

                # ZWEITENS (FALLBACK): Wenn keine gültige ID da ist, aber Bilddaten -> Robuster Edit Mode
                elif has_images:
                    logger.info(f"Mode: Image Edit (Bytes). Fallback for cross-provider or uploads. Image Count: {len(image_bytes_list)}")
                    
                    if is_multi_image:
                         content_list = [{"type": "input_text", "text": f"Combine these images: {final_image_prompt}"}]
                         for img_bytes in image_bytes_list:
                             mime_type = "image/png"
                             if img_bytes.startswith(b'\xff\xd8'): mime_type = "image/jpeg"
                             elif img_bytes.startswith(b'RIFF'): mime_type = "image/webp"
                             b64_img = base64.b64encode(img_bytes).decode('utf-8')
                             content_list.append({"type": "input_image", "image_url": f"data:{mime_type};base64,{b64_img}"})
                         request_params["input"] = [{"role": "user", "content": content_list}]
                    else:
                        img_bytes = image_bytes_list[0]
                        mime_type = "image/png"
                        if img_bytes.startswith(b'\xff\xd8'): mime_type = "image/jpeg"
                        elif img_bytes.startswith(b'RIFF'): mime_type = "image/webp"
                        b64_img = base64.b64encode(img_bytes).decode('utf-8')
                        # Optimierter Prompt für echte Fotos (Edit-Mode)
                        instruction_type = "STYLE TRANSFORMATION" if "Stil-Transfer" in final_image_prompt else "IMAGE EDIT"
                        
                        content_list = [
                            {"type": "input_image", "image_url": f"data:{mime_type};base64,{b64_img}"},
                            {
                                "type": "input_text", 
                                "text": (
                                    f"TASK: {instruction_type}.\n"
                                    f"MODIFICATION: {final_image_prompt}.\n"
                                    f"CRITICAL RULES FOR REALISM:\n"
                                    f"1. SUBJECT IDENTITY: Keep the person's face 100% recognizable.\n"
                                    f"2. LIGHT WRAP: The light from the new background MUST wrap around the subject. "
                                    f"If there is neon, show colorful highlights on the hair and skin. If there is fire, show warm flickering light.\n"
                                    f"3. TEXTURE MATCH: Adapt the skin texture to the environment. (e.g., if in a cave, add subtle grit; if in a movie scene, use cinematic skin rendering).\n"
                                    f"4. GLOBAL COHESION: The subject and background must share the same focal depth, grain, and color science. NO sharp 'cut-out' edges."
                                )
                            }
                        ]
                        request_params["input"] = [{"role": "user", "content": content_list}]
                    
                    perform_square_crop = False

                # DRITTENS: Wenn nichts davon zutrifft -> Text-zu-Bild
                else:
                    logger.info("Mode: Text-to-Image (New)")
                    request_params["input"] = [{"role": "user", "content": [{"type": "input_text", "text": final_image_prompt}]}]

                # --- API CALL ---
                response = await client.responses.create(**request_params)

                image_call = next((o for o in response.output if o.type == "image_generation_call"), None)

                if not image_call or not image_call.result:
                    text_output = next((o for o in response.output if o.type == "message"), None)
                    reason = text_output.content[0].text if text_output and text_output.content else "Unbekannter Fehler"
                    logger.warning(f"OpenAI konnte kein Bild liefern: {reason}")
                    return {"type": "text", "text": f"Hinweis von OpenAI: {reason}", "image_url": None}
                
                revised_prompt = None
                try:
                    if hasattr(image_call, 'image_generation') and image_call.image_generation:
                         revised_prompt = image_call.image_generation.prompt
                except Exception: pass

                image_bytes_result = base64.b64decode(image_call.result)
                new_response_id = response.id
                new_image_id = image_call.id

            else:
                # LEGACY PATH (DALL-E 3 direct)
                logger.info(f"Standard DALL-E generation for {model}")
                response = await client.images.generate(
                    model=model,
                    prompt=prompt,
                    n=1,
                    size=api_request_size, # Auch hier: Manipulierte Größe
                    quality=selected_quality
                )
                
                image_url_temp = response.data[0].url
                import httpx
                async with httpx.AsyncClient() as h_client:
                    img_res = await h_client.get(image_url_temp)
                    img_res.raise_for_status()
                    image_bytes_result = img_res.content
                
                new_response_id = None
                new_image_id = None
                revised_prompt = response.data[0].revised_prompt

            # --- PLAN B: CROPPING LOGIC ---
            # Wenn wir heimlich Hochformat bestellt haben, müssen wir es jetzt zuschneiden.
            if perform_square_crop:
                try:
                    with Image.open(io.BytesIO(image_bytes_result)) as img:
                        width, height = img.size 
                        target_size = 1024
                        
                        # FIX: Top-Aligned Crop (Schneidet unten ab, behält Kopf)
                        left = (width - target_size) / 2
                        top = 0  # Wir starten ganz oben!
                        right = (width + target_size) / 2
                        bottom = target_size  # Wir nehmen die ersten 1024px von oben
                        
                        # Crop durchführen
                        img_cropped = img.crop((left, top, right, bottom))
                        
                        # Zurück in Bytes (PNG)
                        out_io = io.BytesIO()
                        img_cropped.save(out_io, format="PNG")
                        image_bytes_result = out_io.getvalue()
                        
                        logger.info(f"Plan B: Erfolgreich von {width}x{height} auf 1024x1024 gecroppt (Top-Aligned).")
                except Exception as e:
                    logger.error(f"Plan B Crop failed: {e}. Verwende Originalbild.", exc_info=True)

            # --- SPEICHERN ---
            image_url = image_manager.save_image_from_bytes(
                image_bytes_result, 
                description=revised_prompt if revised_prompt else "generated_image", 
                file_extension="png"
            )

            # Kosten mit den tatsächlichen Parametern berechnen (wir haben 1024x1792 bezahlt!)
            actual_usage = kwargs.copy()
            actual_usage["size"] = api_request_size # Wichtig für korrekte Kosten
            usage, cost = _calculate_and_log_cost(model, usage_data=actual_usage, custom_prompt=prompt)

            return {
                "image_url": image_url,
                "previous_response_id": new_response_id,
                "previous_image_id": new_image_id,
                "usage": usage,
                "cost": cost,
                "revised_prompt": revised_prompt
            }

        except openai.BadRequestError as e:
            error_data = e.response.json().get('error', {})
            if error_data.get('code') == 'moderation_blocked':
                return {"type": "text", "text": "FEHLER: Safety Violation.", "image_url": None}
            raise e

        # NEU: RateLimitError (Quota) explizit durchlassen!
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI RateLimit/Quota Error: {e}")
            raise e

        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=True)
            return {"type": "text", "text": f"Fehler: {e}", "image_url": None}
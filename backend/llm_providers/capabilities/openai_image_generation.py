import base64
import io
import logging
import os
from datetime import datetime
from typing import Dict

import openai
from PIL import Image, ImageOps
from backend.llm_providers.utils import _extract_image_description
from backend.services import image_manager
from backend.services.cost_calculator import calculate_cost
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("janus_backend")


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
                model="gpt-4o",
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(self, api_key: str, model: str, prompt: str, image_bytes_list: list = None, **kwargs) -> Dict:
        """
        Generates or EDITS an image using either the standard DALL-E API or the new Responses API.
        Supports multiple input images for combination/merging.
        """
        client = openai.AsyncOpenAI(api_key=api_key)

        use_dalle2_inpainting = kwargs.get("use_dalle2_inpainting", False)
        mask_b64 = kwargs.get("mask_image_data")

        if use_dalle2_inpainting:
            logger.info("Mode: DALL-E 2 Inpainting")
            if not mask_b64 or not image_bytes_list:
                raise ValueError("DALL-E 2 inpainting requires an image and a mask.")

            try:
                # 1. Decode mask and prepare images
                if "base64," in mask_b64:
                    mask_b64 = mask_b64.split("base64,")[1]
                mask_bytes = base64.b64decode(mask_b64)

                original_image_pil = Image.open(io.BytesIO(image_bytes_list[0]))
                original_image_pil = ImageOps.exif_transpose(original_image_pil)
                mask_image_pil = Image.open(io.BytesIO(mask_bytes))

                if original_image_pil.size != mask_image_pil.size:
                    logger.info(f"Resizing mask from {mask_image_pil.size} to {original_image_pil.size}")
                    mask_image_pil = mask_image_pil.resize(original_image_pil.size, Image.Resampling.NEAREST)
                
                # Ensure RGBA for mask, as required by DALL-E 2
                if mask_image_pil.mode != 'RGBA':
                    mask_image_pil = mask_image_pil.convert('RGBA')
                
                if original_image_pil.mode != 'RGBA':
                    original_image_pil = original_image_pil.convert('RGBA')

                img_byte_arr = io.BytesIO()
                original_image_pil.save(img_byte_arr, format='PNG')
                final_image_bytes = img_byte_arr.getvalue()

                mask_byte_arr = io.BytesIO()
                mask_image_pil.save(mask_byte_arr, format='PNG')
                final_mask_bytes = mask_byte_arr.getvalue()

                # 2. Call DALL-E 2 edit endpoint
                dalle2_size = kwargs.get("size", "1024x1024")
                if dalle2_size not in ["256x256", "512x512", "1024x1024"]:
                    dalle2_size = "1024x1024"

                response = await client.images.edit(
                    model="dall-e-2",
                    image=final_image_bytes,
                    mask=final_mask_bytes,
                    prompt=prompt,
                    n=1,
                    size=dalle2_size
                )

                image_url_temp = response.data[0].url
                import httpx
                async with httpx.AsyncClient() as h_client:
                    img_res = await h_client.get(image_url_temp)
                    img_res.raise_for_status()
                    image_bytes_result = img_res.content

                # 3. Save and return
                cleaned_description = _extract_image_description(prompt)
                image_url = image_manager.save_image_from_bytes(
                    image_bytes_result, description=cleaned_description, file_extension="png"
                )
                
                usage, cost = _calculate_and_log_cost("dall-e-2", usage_data=kwargs, custom_prompt=prompt)

                return {
                    "image_url": image_url,
                    "previous_response_id": None,
                    "previous_image_id": None,
                    "usage": usage,
                    "cost": cost
                }

            except Exception as e:
                logger.error(f"Error during DALL-E 2 inpainting: {e}", exc_info=True)
                raise


        target_image_model = model
        orchestrator_model = "gpt-5.2"  # UPGRADE: Uses the newer, more intelligent model as director
        
        prev_res_id = kwargs.get("previous_response_id")
        prev_img_id = kwargs.get("previous_image_id")
        
        # Backward compatibility: handle single image case
        image_bytes = image_bytes_list[0] if image_bytes_list and len(image_bytes_list) > 0 else None
        has_images = image_bytes_list is not None and len(image_bytes_list) > 0
        is_multi_image = has_images and len(image_bytes_list) > 1
        
        GPT_IMAGE_SERIES_SIZES = ["1024x1024", "1024x1536", "1536x1024"]
        DALLE_LEGACY_SIZES = ["1024x1024", "1792x1024", "1024x1792"]

        selected_size = kwargs.get("size", "1024x1024")
        selected_quality = kwargs.get("quality", "medium")

        if target_image_model.startswith("gpt-image-") and selected_size not in GPT_IMAGE_SERIES_SIZES:
            selected_size = "1024x1024"
        elif not target_image_model.startswith("gpt-image-") and selected_size not in DALLE_LEGACY_SIZES:
            selected_size = "1024x1024"

        # Tool Definition
        image_tool = {
            "type": "image_generation",
            "model": target_image_model,
            "size": selected_size,
            "quality": selected_quality
        }
        
        # Fidelity nur für unterstützte Modelle setzen (Mini kann es nicht)
        if "mini" not in target_image_model:
            image_tool["input_fidelity"] = "high"  # Für bessere Gesichtskonsistenz
        
        # Temporäre Variable für die Masken-ID, falls benötigt
        mask_file_id = None

        try:
            if target_image_model.startswith("gpt-image-"):
                logger.info(f"Responses API Call: Orchestrator={orchestrator_model}, Image-Tool={target_image_model}")
                
                # Initialize request parameters early
                request_params = {
                    "model": orchestrator_model,
                    # input will be set later
                    "tools": [image_tool]
                }
                
                # FALL 0: Inpainting / Masking (Höchste Priorität)
                if mask_b64 and image_bytes_list and len(image_bytes_list) > 0:
                    logger.info("Mode: Inpainting with Mask (Processing via PIL)")
                    
                    try:
                        # 1. Maske decodieren
                        if "base64," in mask_b64:
                            mask_b64 = mask_b64.split("base64,")[1]
                        mask_bytes = base64.b64decode(mask_b64)
                        
                        # 2. Bilder in PIL laden
                        original_image_pil = Image.open(io.BytesIO(image_bytes_list[0]))
                        
                        # EXIF ROTATION FIX
                        # Stellt sicher, dass das Bild für Python genauso aussieht wie im Browser
                        original_image_pil = ImageOps.exif_transpose(original_image_pil)
                        
                        mask_image_pil = Image.open(io.BytesIO(mask_bytes))
                        
                        # 3. GOLDSTANDARD FIX: Größe angleichen!
                        # Die Maske muss EXAKT so groß sein wie das Originalbild.
                        # Falls das Frontend um 1px abweicht, fixen wir das hier.
                        if original_image_pil.size != mask_image_pil.size:
                            logger.info(f"Resizing mask from {mask_image_pil.size} to {original_image_pil.size}")
                            mask_image_pil = mask_image_pil.resize(original_image_pil.size, Image.Resampling.NEAREST)
                        
                        # 4. In Bytes zurückkonvertieren (PNG erzwingen)
                        # Originalbild
                        img_byte_arr = io.BytesIO()
                        original_image_pil.save(img_byte_arr, format='PNG')
                        final_image_bytes = img_byte_arr.getvalue()
                        
                        # Maske
                        mask_byte_arr = io.BytesIO()
                        mask_image_pil.save(mask_byte_arr, format='PNG')
                        final_mask_bytes = mask_byte_arr.getvalue()

                    except Exception as e:
                        logger.error(f"Error processing inpainting images: {e}")
                        raise ValueError("Fehler bei der Bildverarbeitung für Inpainting.")

                    # 5. Upload zu OpenAI
                    image_file_id = await self._upload_bytes_to_openai(client, final_image_bytes, "original.png")
                    mask_file_id = await self._upload_bytes_to_openai(client, final_mask_bytes, "mask.png")
                    
                    # 6. Prompting
                    system_instruction = (
                        f"TASK: Perform inpainting on the attached image using the provided mask.\n"
                        f"USER REQUEST: {prompt}\n"
                        "CRITICAL EXECUTION RULES:\n"
                        "1. TARGET: You MUST fill ALL transparent areas of the mask. Do not ignore any marked spot.\n"
                        "2. QUANTITY: If the mask contains multiple disconnected areas, place the requested object(s) in EACH area, even if the user used singular wording (e.g., 'a worm' -> put a worm in every hole).\n"
                        "3. COHERENCE: Blend the new elements seamlessly into the existing lighting and style.\n"
                        "4. PRESERVATION: Keep the unmasked (opaque) areas pixel-perfectly unchanged."
                    )

                    input_data = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": system_instruction},
                                {"type": "input_image", "file_id": image_file_id}
                            ]
                        }
                    ]
                    
                    # Tool konfigurieren
                    image_tool["input_image_mask"] = {"file_id": mask_file_id}
                    
                    # FIX: Fidelity High entfernen bei Inpainting!
                    # Die Maske selbst ist der "Schutz". Fidelity High kann dazu führen, 
                    # dass das Modell die Änderungen ignoriert oder falsch platziert.
                    if "input_fidelity" in image_tool:
                        del image_tool["input_fidelity"]
                    logger.info("Inpainting Mode: Removed input_fidelity parameter to avoid conflicts.")
                    
                    request_params["input"] = input_data
                    
                    # API-Aufruf
                    response = await client.responses.create(**request_params)
                    
                    # Aufräumen: Hochgeladene Dateien löschen
                    try:
                        if image_file_id:
                            await client.files.delete(image_file_id)
                        if mask_file_id:
                            await client.files.delete(mask_file_id)
                    except Exception as e:
                        logger.warning(f"Could not delete temporary files: {e}")
                        
                    # Sicherstellen, dass die Masken-Referenz nicht für zukünftige Aufrufe erhalten bleibt
                    if "input_image_mask" in image_tool:
                        del image_tool["input_image_mask"]
                    
                    # Verarbeite die Antwort
                    image_call = next((o for o in response.output if o.type == "image_generation_call"), None)
                    
                    if not image_call or not image_call.result:
                        text_output = next((o for o in response.output if o.type == "message"), None)
                        reason = text_output.content[0].text if text_output and text_output.content else "Unbekannter Fehler"
                        logger.warning(f"OpenAI konnte kein Bild liefern: {reason}")
                        return {
                            "type": "text",
                            "text": f"Hinweis von OpenAI: {reason}",
                            "image_url": None,
                            "usage": {},
                            "cost": {}
                        }
                    
                    try:
                        image_bytes_result = base64.b64decode(image_call.result)
                        new_response_id = response.id
                        new_image_id = image_call.id
                        
                        # Speichern des Bildes
                        cleaned_description = _extract_image_description(prompt)
                        image_url = image_manager.save_image_from_bytes(
                            image_bytes_result, description=cleaned_description, file_extension="png"
                        )
                        
                        usage, cost = _calculate_and_log_cost(model, usage_data=kwargs, custom_prompt=prompt)
                        
                        return {
                            "image_url": image_url,
                            "previous_response_id": new_response_id,
                            "previous_image_id": new_image_id,
                            "usage": usage,
                            "cost": cost
                        }
                        
                    except Exception as e:
                        logger.error(f"Error processing inpainting result: {e}", exc_info=True)
                        return {
                            "type": "text",
                            "text": f"Fehler bei der Verarbeitung des Inpainting-Ergebnisses: {str(e)}",
                            "image_url": None,
                        }
                
                # --- INTELLIGENTE LOGIK-WEICHE (Safe Mode) ---

                # FALL 0: Inpainting / Masking (Höchste Priorität, Code von vorhin)
                if mask_b64 and has_images:
                    # ... (Existing inpainting code remains exactly the same) ...
                    pass 

                # FALL 1: Combine-Modus (Mehrere Bilder)
                elif has_images and is_multi_image:
                    logger.info("Mode: Multi-Image Combine")
                    user_content = [{"type": "input_text", "text": f"Combine these images based on this description: {prompt}"}]
                    for idx, img_bytes in enumerate(image_bytes_list):
                        # MIME Type Logic
                        mime_type = "image/png"
                        if img_bytes.startswith(b'\xff\xd8'): mime_type = "image/jpeg"
                        elif img_bytes.startswith(b'RIFF'): mime_type = "image/webp"
                        b64_img = base64.b64encode(img_bytes).decode('utf-8')
                        user_content.append({"type": "input_image", "image_url": f"data:{mime_type};base64,{b64_img}"})
                    
                    input_data = [{"role": "user", "content": user_content}]

                # FALL 2: Native Refinement mit Context (DER GPT GOLDSTANDARD)
                # WICHTIG: Das kommt VOR dem Single Image Edit.
                # Wenn wir eine ID haben, nutzen wir IMMER die ID, egal ob Bytes da sind oder nicht.
                # Das schützt den funktionierenden GPT->GPT Workflow.
                elif prev_res_id:
                    logger.info(f"Mode: Refinement via Context (History ID: {prev_res_id})")
                    enhanced_prompt = (
                        f"TASK: Edit the generated image from our conversation.\n"
                        f"USER REQUEST: {prompt}\n"
                        "STRICT CONSTRAINT: The pixel identity of the person MUST remain 100% frozen."
                    )
                    input_data = [{"role": "user", "content": [{"type": "input_text", "text": enhanced_prompt}]}]
                    request_params["previous_response_id"] = prev_res_id

                # FALL 3: Single Image Edit / Cross-Provider (Fallback)
                # Das greift NUR, wenn wir KEINE ID haben (z.B. Gemini Bild), aber Bytes.
                elif has_images: 
                    logger.info("Mode: Single Image Edit / Cross-Provider (Bytes only)")
                    img_bytes = image_bytes_list[0]
                    # MIME Type
                    mime_type = "image/png"
                    if img_bytes.startswith(b'\xff\xd8'): mime_type = "image/jpeg"
                    elif img_bytes.startswith(b'RIFF'): mime_type = "image/webp"
                    b64_img = base64.b64encode(img_bytes).decode('utf-8')

                    input_data = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": f"Edit the attached image: {prompt}"},
                                {"type": "input_image", "image_url": f"data:{mime_type};base64,{b64_img}"}
                            ]
                        }
                    ]

                # FALL 4: Text-to-Image (Neu)
                else:
                    logger.info("Mode: Text-to-Image (New)")
                    input_data = [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}]
                
                # Set the input data in the request parameters
                request_params["input"] = input_data
                
                response = await client.responses.create(**request_params)

                image_call = next((o for o in response.output if o.type == "image_generation_call"), None)

                if not image_call or not image_call.result:
                    text_output = next((o for o in response.output if o.type == "message"), None)
                    reason = "Unbekannter Fehler"
                    if text_output and text_output.content:
                        if isinstance(text_output.content, list) and len(text_output.content) > 0:
                            reason = text_output.content[0].text
                        elif isinstance(text_output.content, str):
                            reason = text_output.content
                    
                    logger.warning(f"OpenAI konnte kein Bild liefern: {reason}")
                    return {
                        "type": "text",
                        "text": f"Hinweis von OpenAI: {reason}",
                        "image_url": None,
                        "usage": {},
                        "cost": {}
                    }
                
                try:
                    image_bytes_result = base64.b64decode(image_call.result)
                    new_response_id = response.id
                    new_image_id = image_call.id
                except Exception as e:
                    logger.error(f"Error decoding image data: {e}", exc_info=True)
                    return {"type": "text", "text": "Fehler beim Verarbeiten des generierten Bildes."}

            else:
                # LEGACY PATH: For dall-e-3 etc.
                logger.info(f"Standard DALL-E generation for {model}")
                response = await client.images.generate(
                    model=model,
                    prompt=prompt,
                    n=1,
                    size=selected_size,
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

            # Save image
            cleaned_description = _extract_image_description(prompt)
            image_url = image_manager.save_image_from_bytes(
                image_bytes_result, description=cleaned_description, file_extension="png"
            )

            usage, cost = _calculate_and_log_cost(model, usage_data=kwargs, custom_prompt=prompt)

            return {
                "image_url": image_url,
                "previous_response_id": new_response_id,
                "previous_image_id": new_image_id,
                "usage": usage,
                "cost": cost
            }

        except openai.BadRequestError as e:
            # Spezielle Behandlung für Moderationsfehler
            error_data = e.response.json().get('error', {})
            error_code = error_data.get('code')
            error_msg = error_data.get('message', str(e))
            
            if error_code == 'moderation_blocked':
                friendly_msg = "Das Bild oder der Prompt verstoßen gegen die Sicherheitsrichtlinien von OpenAI (Moderation Blocked)."
                logger.warning(f"Safety Violation: {error_msg}")
                # Wir geben ein Dummy-Objekt zurück, damit das Frontend nicht abstürzt, sondern den Text anzeigt
                return {
                    "type": "text",
                    "text": f"FEHLER: {friendly_msg}",
                    "image_url": None,
                    "usage": {},
                    "cost": {}
                }
            
            # Sonstige Bad Requests (z.B. falsche Parameter)
            logger.error(f"OpenAI Bad Request: {error_msg}", exc_info=True)
            raise e  # Weiterwerfen für generischen 500er im Router oder handled dort

        except openai.APIStatusError as e: 
            error_message = f"OpenAI API Fehler (Status {e.status_code}): {e.response.json().get('error', {}).get('message', 'Unbekannter Fehler')}"
            logger.error(error_message, exc_info=True)
            return {
                "type": "text",
                "text": f"Fehler bei der Bildgenerierung: {error_message}",
                "image_url": None,
            }
        except Exception as e:
            logger.error(f"Error generating image with OpenAI API: {e}", exc_info=True)
            return {
                "type": "text",
                "text": f"Fehler bei der Bildgenerierung: {e}",
                "image_url": None,
            }
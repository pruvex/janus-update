
import logging
from typing import Optional, Dict, List
import base64
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from backend import image_manager
from backend.llm_providers.utils import _extract_image_description
from backend.cost_calculator import calculate_cost

logger = logging.getLogger('janus_backend')

def _calculate_and_log_cost(model_id, usage_data=None, custom_prompt=None):
    """Helper to calculate and log cost."""
    usage, cost = calculate_cost(model_id, usage_data, custom_prompt)
    logger.info(f"\n--- USAGE TRACKING ---\n" 
                f"Model: {model_id}\n" 
                f"Input Tokens: {usage.get('input_tokens', 'N/A')}\n" 
                f"Output Tokens: {usage.get('output_tokens', 'N/A')}\n" 
                f"Image Quality: {usage.get('image_quality', 'N/A')}\n" 
                f"Image Size: {usage.get('image_size', 'N/A')}\n" 
                f"Total Cost: {cost.get('total_cost', 0):.8f} €\n" 
                f"----------------------")
    return usage, cost

class GeminiImageGeneration:
    """
    Encapsulates the image generation functionality for the Gemini provider.
    """
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(self, api_key: str, model: str, prompt: str, reference_image_path: Optional[str] = None, **kwargs) -> dict:
        """
        Generates an image using the Gemini API, with optional support for a reference image.
        """
        genai.configure(api_key=api_key)
        genai_model = genai.GenerativeModel(model)
        
        # Prepare the content payload for the API
        contents = []
        parts = []
        
        try:
            # --- START: New Image-to-Image Logic ---
            if reference_image_path and isinstance(reference_image_path, str):
                logger.info(f"Reference image provided: {reference_image_path}. Preparing image-to-image generation.")
                try:
                    # We need the absolute path to the file on the server
                    from backend.utils.paths import get_app_data_dir
                    import os
                    
                    # The path from DB is web-style (/user_images/...), convert to OS-style path
                    # IMPORTANT: The replace call might be platform-dependent.
                    # Let's make it more robust by handling both / and \ separators.
                    relative_path = reference_image_path.replace("/user_images/", "").replace("\\user_images\\", "")
                    
                    # Construct the full, absolute path
                    absolute_path = os.path.join(get_app_data_dir(), "images", relative_path)
                    
                    logger.info(f"Attempting to open reference image at absolute path: {absolute_path}")

                    with open(absolute_path, "rb") as image_file:
                        image_bytes = image_file.read()
                    
                    # Simple mime type detection from extension
                    file_ext = absolute_path.split('.')[-1].lower()
                    mime_type = f"image/{file_ext}" if file_ext in ['jpeg', 'jpg', 'png', 'webp'] else "image/png"

                    # Construct the multi-part content as per Google's documentation
                    # IMPORTANT: The order matters for some models. Text first, then image.
                    parts.append({"text": prompt})
                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(image_bytes).decode('utf-8')
                        }
                    })
                except FileNotFoundError:
                    logger.error(f"Reference image not found at path: {absolute_path}. Falling back to text-only.")
                    parts.append({"text": prompt})
                except Exception as e:
                    logger.error(f"An unexpected error occurred during reference image processing: {e}", exc_info=True)
                    parts.append({"text": prompt}) # Fallback
            else:
                # Fallback to original text-to-image logic
                parts.append({"text": prompt})
            
            if parts:
                contents.append({'role': 'user', 'parts': parts})
            # --- END: New Image-to-Image Logic ---

            logger.info(f"Calling Gemini image model '{model}' with prompt: '{prompt}' and reference image: {bool(reference_image_path)}")
            response = await genai_model.generate_content_async(contents)
            
            image_data = None
            text_response = None

            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    # Check for direct 'data' field as suggested by curl example
                    if hasattr(part, 'data') and part.data:
                        image_data = part.data
                        break
                    elif part.inline_data and part.inline_data.data:
                        image_data = part.inline_data.data
                        break
                    if part.text:
                        text_response = part.text
            
            image_url = None
            if image_data:
                cleaned_description = _extract_image_description(prompt)
                image_url = image_manager.save_image_from_bytes(image_data, description=cleaned_description, file_extension="png")
                text_response = "Bild wurde erfolgreich generiert."  # If we get an image, we don't want to return text

            usage, cost = _calculate_and_log_cost(model)
            
            return {"text": text_response, "image_url": image_url, "usage": usage, "cost": cost}

        except Exception as e:
            logger.error(f"Error generating image with Gemini (attempt failed): {e}", exc_info=True)
            raise

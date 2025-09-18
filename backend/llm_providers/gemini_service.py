# VOLLSTÄNDIGER, FINALER UND GETESTETER INHALT FÜR: backend/llm_providers/gemini_service.py

import logging
import re
from typing import List, Dict, Optional
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InvalidArgument
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.cost_calculator import calculate_cost
from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.capabilities.gemini_image_generation import GeminiImageGeneration
from backend.llm_providers.capabilities.gemini_web_search import GeminiWebSearch
from backend.llm_providers.capabilities.gemini_multimodal import GeminiMultiModal
from backend.llm_providers.capabilities.gemini_text_generation import GeminiTextGeneration

logger = logging.getLogger('janus_backend')

def _extract_image_description(prompt: str) -> str:
    """Extracts a concise, filename-safe description from the user's prompt."""
    prompt = re.sub(r'\b(zeichne|male|erstelle|generiere|create|draw|generate|ein bild von)\b', '', prompt, flags=re.IGNORECASE)
    safe_prompt = re.sub(r'[^a-zA-Z0-9\s-]', '', prompt).strip()
    filename = safe_prompt.replace(' ', '-').lower()[:50]
    return filename or "generated-image"

def _calculate_and_log_cost(model_id, usage_data=None, custom_prompt=None):
    """Berechnet die Kosten und gibt sie im Log aus."""
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


class GeminiServiceProvider(BaseLLMProvider):

    def __init__(self):
        self.image_generator = GeminiImageGeneration()
        self.web_search = GeminiWebSearch()
        self.multimodal_generator = GeminiMultiModal()
        self.text_generator = GeminiTextGeneration()

    def _convert_tools_to_gemini_format(self, tools: List[Dict]) -> Optional[List[genai.types.Tool]]:
        """
        Konvertiert das interne Tool-Format in das von der Gemini API erwartete Format.
        Behebt insbesondere das Kompatibilitätsproblem mit Pydantic's 'Optional' Feldern (anyOf).
        """
        if not tools:
            return None
        
        from backend.tool_registry import get_all_tools
        tool_registry = get_all_tools()
        
        gemini_tools = []
        for tool_def in tools:
            func_name = tool_def.get("function", {}).get("name")
            if func_name in tool_registry:
                schema = tool_registry[func_name].args_schema.model_json_schema()
                
                properties = schema.get("properties", {})
                
                # --- NEU: Schema-Bereinigung ---
                # Diese Schleife behebt das 'anyOf'-Problem für optionale Felder.
                for prop_name, prop_details in properties.items():
                    if 'anyOf' in prop_details:
                        # Finde den Nicht-Null-Typ in der 'anyOf'-Liste
                        non_null_type = next((t for t in prop_details['anyOf'] if t.get('type') != 'null'), None)
                        if non_null_type:
                            # Ersetze die 'anyOf'-Struktur durch eine einfache Typdefinition
                            new_prop = non_null_type
                            # Behalte wichtige Metadaten wie die Beschreibung bei
                            if 'description' in prop_details:
                                new_prop['description'] = prop_details['description']
                            properties[prop_name] = new_prop
                # --- ENDE: Schema-Bereinigung ---
                            
                for prop in properties.values():
                    prop.pop("title", None)

                function_declaration = genai.types.FunctionDeclaration(
                    name=func_name,
                    description=tool_def.get("function", {}).get("description", ""),
                    parameters={
                        'type': 'object',
                        'properties': properties,
                        'required': schema.get("required", [])
                    }
                )
                gemini_tools.append(function_declaration)

        return [genai.types.Tool(function_declarations=gemini_tools)] if gemini_tools else None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(self, api_key: str, model: str, messages: List[Dict], tools: Optional[List[Dict]] = None, image_data: Optional[str] = None, **kwargs) -> Dict:
        genai.configure(api_key=api_key)

        if image_data:
            return await self.multimodal_generator.generate_with_image(model, messages, image_data)

        system_instruction = None
        gemini_history_for_api = []
        for msg in messages:
            if msg.get("role") == "system":
                system_instruction = msg.get("content")
                continue
            
            content = msg.get("content")
            if content is None or content == "":
                continue
                
            role = "user" if msg["role"] == "user" else "model"
            if isinstance(content, list):
                text_content = next((part['text'] for part in content if part['type'] == 'text'), '')
                if text_content:
                     gemini_history_for_api.append({'role': role, 'parts': [{'text': text_content}]})
            elif isinstance(content, str):
                gemini_history_for_api.append({'role': role, 'parts': [{'text': content}]})

        gemini_tools = self._convert_tools_to_gemini_format(tools)

        try:
            genai_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                tools=gemini_tools
            )
        except Exception as e:
            logger.error(f"Error initializing Gemini model: {e}", exc_info=True)
            return {"type": "text", "text": f"Fehler bei der Initialisierung des Modells: {e}"}

        try:
            usage_metadata = None  # Initialize to prevent UnboundLocalError
            response = await genai_model.generate_content_async(gemini_history_for_api)
            
            if not response.candidates: # Move this check to the beginning
                logger.warning(f"Gemini returned no candidates, possibly due to safety filters or an empty prompt. History: {gemini_history_for_api}")
                return {"type": "text", "text": "Ich konnte keine passende Antwort generieren. Möglicherweise wurde sie durch einen Sicherheitsfilter blockiert."}

            first_candidate = response.candidates[0]
            
            if not first_candidate.content.parts:
                finish_reason = first_candidate.finish_reason.name
                safety_ratings = [str(rating) for rating in first_candidate.safety_ratings]
                error_message = f"Gemini response was blocked. Reason: {finish_reason}. Safety Ratings: {safety_ratings}"
                logger.warning(error_message)
                return {"type": "text", "text": "Meine Antwort wurde aufgrund von Sicherheitsrichtlinien blockiert. Bitte formuliere die Anfrage anders."}

            first_part = first_candidate.content.parts[0]

            if hasattr(first_part, 'function_call') and first_part.function_call:
                tool_call = first_part.function_call
                tool_name = tool_call.name
                tool_args = {key: value for key, value in tool_call.args.items()}
                
                logger.info(f"Gemini requested tool call: {tool_name} with args: {tool_args}")
                
                usage_metadata = response.usage_metadata
                if usage_metadata:
                    usage, cost = _calculate_and_log_cost(model, {
                        "prompt_tokens": usage_metadata.prompt_token_count,
                        "completion_tokens": usage_metadata.candidates_token_count
                    })
                else:
                    usage, cost = {}, {}

                return {
                    "type": "tool_code",
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "usage": usage,
                    "cost": cost
                }
            else:
                text_response = response.text
                usage_metadata = response.usage_metadata
                if usage_metadata:
                    usage, cost = _calculate_and_log_cost(model, {
                        "prompt_tokens": usage_metadata.prompt_token_count,
                        "completion_tokens": usage_metadata.candidates_token_count
                    })
                else:
                    usage, cost = {}, {}
                return {
                    "type": "text",
                    "text": text_response,
                    "usage": usage,
                    "cost": cost
                }

        except (ResourceExhausted, InvalidArgument) as e:
            logger.error(f"API Error with Gemini: {e}", exc_info=True)
            return {"type": "text", "text": f"API-Fehler bei Gemini: {e}"}
        except Exception as e:
            if "response.candidates is empty" in str(e):
                 logger.warning(f"Gemini returned no candidates, possibly due to safety filters or an empty prompt. History: {gemini_history_for_api}")
                 return {"type": "text", "text": "Ich konnte keine passende Antwort generieren. Möglicherweise wurde sie durch einen Sicherheitsfilter blockiert."}
            logger.error(f"An unexpected error occurred with Gemini SDK: {e}", exc_info=True)
            return {"type": "text", "text": f"Ein unerwarteter Fehler ist aufgetreten: {e}"}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(self, api_key: str, model: str, prompt: str, reference_image_path: Optional[str] = None, **kwargs) -> Dict:
        return await self.image_generator.generate_image(api_key, model, prompt, reference_image_path=reference_image_path, **kwargs)
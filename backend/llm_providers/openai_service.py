import logging
from typing import Any, Dict, List, Optional, Type

import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel

from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.capabilities.openai_image_generation import (
    OpenAIImageGeneration,
)
from backend.services.cost_calculator import calculate_cost

logger = logging.getLogger("janus_backend")


def _calculate_and_log_cost(model_id, usage_data=None, custom_prompt=None):
    """
    Berechnet die Kosten und gibt sie formatiert im Log aus (analog zu Gemini).
    """
    usage, cost = calculate_cost(model_id, usage_data, custom_prompt)
    
    # Visuelles Logging für das Terminal
    input_tokens = usage.get('input_tokens', 0) if usage else 0
    output_tokens = usage.get('output_tokens', 0) if usage else 0
    total_cost = cost.get('total_cost', 0)
    
    logger.info(
        f"\n--- USAGE TRACKING (OpenAI) ---\n"
        f"Model: {model_id}\n"
        f"Input Tokens: {input_tokens}\n"
        f"Output Tokens: {output_tokens}\n"
        f"Total Cost: {total_cost:.8f} €\n"
        f"-----------------------------"
    )
    return usage, cost


class OpenAIServiceProvider(BaseLLMProvider):
    def __init__(self):
        self.image_generator = OpenAIImageGeneration()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        image_data: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        client = openai.AsyncOpenAI(api_key=api_key)
        try:
            # 1. Input-Bereinigung
            clean_messages = []
            for msg in messages:
                if msg.get("role") == "system" and not msg.get("content"):
                    continue
                # Entferne leere Tool Calls, die OpenAI verwirren könnten
                if "tool_calls" in msg and msg["tool_calls"] is None:
                    del msg["tool_calls"]
                clean_messages.append(msg)

            api_call_params = {
                "model": model,
                "messages": clean_messages,
            }

            if tools:
                api_call_params["tools"] = tools
                api_call_params["tool_choice"] = "auto"

            # 2. API Aufruf
            response = await client.chat.completions.create(**api_call_params)

            # --- START DER FINALEN KORREKTUR ---

            # Extrahiere das usage-Objekt aus der Antwort. Es ist nicht None.
            usage_data = response.usage

            # Rufe den Kostenrechner jetzt mit den echten Nutzungsdaten auf.
            usage, cost = _calculate_and_log_cost(model, usage_data=usage_data)

            # --- ENDE DER FINALEN KORREKTUR ---
            
            response_message = response.choices[0].message

            # 3. Tool Call Handling (Goldstandard)
            if response_message.tool_calls:
                tool_calls_list = [tc.model_dump() for tc in response_message.tool_calls]

                logger.info(f"OpenAI triggered {len(tool_calls_list)} tool calls.")

                return {
                    "type": "tool_code",
                    "tool_calls": tool_calls_list,
                    "usage": usage,
                    "cost": cost,
                    "raw_assistant_response": response_message.model_dump(),
                }

            # 4. Standard Text Antwort
            text_response = response_message.content
            
            # Prüfung auf Refusal (Safety)
            if hasattr(response_message, "refusal") and response_message.refusal:
                logger.warning(f"OpenAI Refusal: {response_message.refusal}")
                return {
                    "type": "text",
                    "text": f"Anfrage abgelehnt: {response_message.refusal}",
                    "usage": usage,
                    "cost": cost,
                }

            return {
                "type": "text",
                "text": text_response,
                "image_url": None,
                "usage": usage,
                "cost": cost,
            }

        except Exception as e:
            logger.error(f"An error occurred with OpenAI API: {e}", exc_info=True)
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_structured_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        response_format: Type[BaseModel],
        **kwargs,
    ) -> tuple[BaseModel, Dict[str, Any]]:
        client = openai.AsyncOpenAI(api_key=api_key)
        try:
            clean_messages = []
            for msg in messages:
                if msg.get("role") == "system" and not msg.get("content"):
                    continue
                clean_messages.append(msg)

            # Beta Parse Call
            completion = await client.beta.chat.completions.parse(
                model=model,
                messages=clean_messages,
                response_format=response_format,
            )

            # Kostenberechnung
            cost_data = {} # Default
            usage = {}
            if completion.usage:
                usage_dict = {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens
                }
                usage, cost_data = _calculate_and_log_cost(model, usage_data=usage_dict)

            message = completion.choices[0].message

            if message.refusal:
                logger.warning(f"OpenAI Refusal during structured output: {message.refusal}")
                raise ValueError(f"Model refused request: {message.refusal}")

            # RÜCKGABE: Tuple (Parsed Object, Cost Data)
            return message.parsed, cost_data

        except Exception as e:
            logger.error(f"Error in generate_structured_response (OpenAI): {e}", exc_info=True)
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(self, api_key: str, model: str, prompt: str, image_bytes: bytes = None, **kwargs) -> Dict:
        return await self.image_generator.generate_image(api_key, model, prompt, image_bytes=image_bytes, **kwargs)
        
    def prepare_history_for_second_call(
        self,
        chat_history: List[Dict],
        raw_assistant_response: Dict,
        tool_results: List[Dict]
    ) -> List[Dict]:
        """
        Bereitet die Chat-Historie für den Folgeaufruf nach einer Tool-Ausführung vor.
        
        Für OpenAI werden die Assistenten-Antwort und die Tool-Ergebnisse
        einfach an die Historie angehängt. Es ist keine spezielle Behandlung nötig.
        
        Args:
            chat_history: Die bisherige Chat-Historie
            raw_assistant_response: Die rohe Antwort des Assistenten mit dem Tool-Aufruf
            tool_results: Die Ergebnisse der Tool-Ausführung(en)
            
        Returns:
            Die vorbereitete Chat-Historie für den nächsten Aufruf
        """
        # Für OpenAI: Einfach die Antwort des Assistenten und die Tool-Ergebnisse anhängen
        return chat_history + [raw_assistant_response] + tool_results
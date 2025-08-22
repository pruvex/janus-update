import tiktoken
import logging
from typing import List, Dict

logger = logging.getLogger('janus_backend')

RESPONSE_BUFFER = 1000

def count_tokens(text: str, model: str) -> int:
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(text))
    except KeyError:
        logger.warning(f"Could not find encoding for model {model}. Falling back to gpt-2 encoding.")
        encoding = tiktoken.get_encoding("gpt2")
        return len(encoding.encode(text))

class ContextManager:
    def __init__(self, model_catalog: List[Dict]):
        self.model_limits = {model['id']: model.get('context_window', 8000) for model in model_catalog}

    def build_prompt_history(self, messages: List[Dict], model_id: str, global_memory: str = None) -> List[Dict]:
        max_tokens = self.model_limits.get(model_id, 8000) - RESPONSE_BUFFER
                
        system_prompt = None
        if global_memory:
            # KORRIGIERTER MEHRZEILIGER STRING
            system_prompt_text = (
                "Du bist ein persönlicher Assistent. Nutze die folgenden globalen Erinnerungen, um die Anfrage des Benutzers bestmöglich zu beantworten.\n"
                "--- Globale Erinnerungen ---\n"
                f"{global_memory}"
            )
            system_prompt = {"role": "system", "content": system_prompt_text}
            max_tokens -= count_tokens(system_prompt_text, model_id)

        current_tokens = 0
        truncated_history = []

        for message in reversed(messages):
            message_content = message.get("content", "")
            if not message_content:
                continue

            message_tokens = count_tokens(message_content, model_id)
                        
            if current_tokens + message_tokens > max_tokens:
                logger.info(f"Context limit reached for model {model_id}. Truncating older messages.")
                break
                        
            truncated_history.insert(0, message)
            current_tokens += message_tokens

        if system_prompt:
            truncated_history.insert(0, system_prompt)
                
        return truncated_history

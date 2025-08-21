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

    def build_prompt_history(self, messages: List[Dict], model_id: str) -> List[Dict]:
        max_tokens = self.model_limits.get(model_id, 8000) - RESPONSE_BUFFER
        
        current_tokens = 0
        truncated_history = []

        # Wir iterieren von der neuesten zur ältesten Nachricht (von hinten nach vorne)
        for message in reversed(messages):
            message_content = message.get("content", "")
            if not message_content:
                continue

            message_tokens = count_tokens(message_content, model_id)
            
            if current_tokens + message_tokens > max_tokens:
                logger.info(f"Context limit reached for model {model_id}. Truncating older messages.")
                break # Stop adding messages if the limit is exceeded
            
            # Add the message to the beginning of our list to maintain the original order
            truncated_history.insert(0, message)
            current_tokens += message_tokens

        return truncated_history
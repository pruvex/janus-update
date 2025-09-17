import tiktoken
import logging
from typing import List, Dict
from backend import llm_gateway # Import llm_gateway here
import keyring # NEW IMPORT for accessing API keys

logger = logging.getLogger('janus_backend')

RESPONSE_BUFFER = 1000

class ContextManager:
    def __init__(self, model_catalog: List[Dict]):
        self.model_limits = {model['id']: model.get('context_window', 8000) for model in model_catalog}
        self.system_prompt_text = (
            "Du bist Janus, ein hilfreicher und freundlicher KI-Assistent. "
            "Du antwortest immer auf Deutsch. "
            "Integriere nahtlos dein umfangreiches Allgemeinwissen mit den spezifischen Informationen, die im Abschnitt 'GEDÄCHTNIS' bereitgestellt werden. "
            "**REGEL: Die Informationen im 'GEDÄCHTNIS'-Abschnitt haben immer Vorrang und sind die absolute Wahrheit über den Benutzer und seine Welt. Beziehe dich bei jeder Antwort explizit darauf, wenn es relevant ist.**"
        )

    def get_system_instruction(self) -> str:
        return self.system_prompt_text

    def count_tokens(self, text: str, model: str) -> int:
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")
            return len(encoding.encode(text))
        except KeyError:
            logger.warning(f"Could not find encoding for model {model}. Falling back to gpt-2 encoding.")
            encoding = tiktoken.get_encoding("gpt2")
            return len(encoding.encode(text))

    async def _summarize_chat_segment(self, messages: List[Dict], model_id: str, provider: str, api_key: str) -> Dict:
        """Summarizes a segment of chat history using an LLM."""
        # Use a smaller, efficient model for summarization if possible, or the main model
        # For now, we'll use the provided model for summarization.
        summary_model_id = model_id
        summary_provider = provider

        # Retrieve API key for summarization
        summary_api_key = api_key
        if not summary_api_key:
            logger.error(f"API key not found for {summary_provider} summarization. Skipping summarization.")
            return {"role": "system", "content": f"--- ÄLTERER CHATVERLAUF (ZUSAMMENFASSUNG FEHLGESCHLAGEN: KEIN {summary_provider.upper()} KEY) ---"}

        # Construct a prompt for summarization
        prompt_messages = [
            {"role": "system", "content": "Fasse den folgenden Chatverlauf prägnant zusammen. Konzentriere dich auf die Kernpunkte und wichtigen Informationen, die für eine Fortsetzung des Gesprächs relevant sind. Die Zusammenfassung sollte nicht länger als 200 Wörter sein."},
        ]
        prompt_messages.extend(messages) # Add the chat segment to be summarized

        try:
            # Call the LLM gateway for summarization
            response = await llm_gateway.call_llm(
                provider=summary_provider,
                model_id=summary_model_id,
                prompt="", # Prompt is in chat_history
                api_key=summary_api_key, # Use the retrieved API key
                chat_history=prompt_messages
            )
            return {"role": "system", "content": f"--- ZUSAMMENFASSUNG DES ÄLTEREN CHATVERLAUFS ---\n{response.get('text', '')}"}
        except Exception as e:
            logger.error(f"Error summarizing chat segment: {e}")
            # Fallback: return a truncated version or a generic message
            return {"role": "system", "content": "--- ÄLTERER CHATVERLAUF (ZUSAMMENFASSUNG FEHLGESCHLAGEN) ---"}

    async def build_final_context(self, user_prompt: str, chat_history: List[Dict], memory_context: str, model_id: str, api_key: str, budget_config: Dict, provider: str) -> List[Dict]:
        max_tokens = self.model_limits.get(model_id, 8000) - RESPONSE_BUFFER
        current_tokens = 0
        final_history = []

        # 1. System Prompt (highest priority)
        system_prompt_tokens = self.count_tokens(self.system_prompt_text, model_id)
        if system_prompt_tokens > max_tokens * budget_config.get("system_prompt_ratio", 0.1):
            logger.warning("System prompt too long, will be truncated or ignored.")
            # In a real scenario, we might truncate the system prompt or simplify it.
            # For now, we assume it fits or is critical.

        final_history.append({"role": "system", "content": self.system_prompt_text})
        current_tokens += system_prompt_tokens

        # 2. Memory Context (high priority, but can be truncated)
        memory_context_tokens = self.count_tokens(memory_context, model_id)
        memory_budget = max_tokens * budget_config.get("memory_ratio", 0.3)

        if memory_context_tokens > 0:
            if memory_context_tokens > memory_budget:
                logger.info(f"Memory context too long ({memory_context_tokens} tokens), truncating to {memory_budget} tokens.")
                # Simple truncation: take the most recent parts if it's a list of snippets
                # For now, we'll just truncate the string, which might cut off facts mid-sentence.
                # A more sophisticated approach would involve re-summarizing or selecting top-k snippets.
                truncated_memory_context = memory_context[:int(memory_budget * 4)] # Rough char estimate for tokens
                final_history.append({"role": "system", "content": f"--- RELEVANTE ERINNERUNGEN ---\n{truncated_memory_context}\n"})
                current_tokens += self.count_tokens(truncated_memory_context, model_id)
            else:
                final_history.append({"role": "system", "content": f"--- RELEVANTE ERINNERUNGEN ---\n{memory_context}\n"})
                current_tokens += memory_context_tokens

        # 3. Chat History (medium priority, rolling window with summarization)
        chat_history_budget = max_tokens * budget_config.get("chat_history_ratio", 0.5)
        
        # Calculate total tokens of the full chat history
        full_chat_history_tokens = sum(self.count_tokens(msg.get("content", ""), model_id) for msg in chat_history)

        SUMMARIZATION_THRESHOLD_TOKENS = 1500 # Example threshold for summarization
        # Only summarize if the chat history is substantial and exceeds a threshold
        if full_chat_history_tokens > SUMMARIZATION_THRESHOLD_TOKENS and len(chat_history) > 5: # Also check number of messages
            logger.info(f"Chat history ({full_chat_history_tokens} tokens) exceeds summarization threshold. Attempting to summarize older parts.")
            
            # Find the split point for summarization
            # Iterate from the oldest messages to find a segment to summarize
            tokens_to_summarize = 0
            split_index = 0
            for i, message in enumerate(chat_history):
                tokens_to_summarize += self.count_tokens(message.get("content", ""), model_id)
                if tokens_to_summarize > SUMMARIZATION_THRESHOLD_TOKENS / 2: # Summarize roughly half the threshold
                    split_index = i + 1
                    break
            
            if split_index > 0:
                messages_to_summarize = chat_history[:split_index]
                remaining_messages = chat_history[split_index:]

                summarized_segment = await self._summarize_chat_segment(messages_to_summarize, model_id, provider, api_key)
                
                # Reconstruct chat_history with summary and remaining messages
                chat_history = [summarized_segment] + remaining_messages
                logger.info(f"Chat history summarized. Original tokens: {full_chat_history_tokens}. New history length: {len(chat_history)} messages.")
            else:
                logger.info("Chat history not long enough for effective summarization despite token count.")


        # Now, proceed with the rolling window logic on the potentially summarized history
        remaining_budget = max_tokens - current_tokens
        truncated_chat_history = []
        for message in reversed(chat_history):
            message_content = message.get("content", "")
            message_tokens = self.count_tokens(message_content, model_id)

            # Check if adding this message + user prompt exceeds max_tokens
            # The user prompt is added last, so we need to account for its size
            # Also account for the system prompt and memory context already added
            if current_tokens + message_tokens + self.count_tokens(user_prompt, model_id) > max_tokens:
                logger.info(f"Chat history limit reached. Truncating older messages.")
                break
            
            truncated_chat_history.insert(0, message)
            current_tokens += message_tokens
        
        if truncated_chat_history:
            final_history.extend(truncated_chat_history)

        # 4. User Prompt (always included, highest priority for remaining budget)
        final_history.append({"role": "user", "content": user_prompt})
        current_tokens += self.count_tokens(user_prompt, model_id)

        logger.info(f"Final context built. Total tokens: {current_tokens}/{max_tokens}")
        return final_history

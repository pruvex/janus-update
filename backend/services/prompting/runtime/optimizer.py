import logging

from ..core.model import Prompt

logger = logging.getLogger("janus_backend")


class PromptOptimizer:
    def optimize(self, prompt_ast: Prompt, model_id: str, max_tokens: int) -> Prompt:
        model_id_l = str(model_id or "").lower()
        is_small_model = any(m in model_id_l for m in ["nano", "mini"])

        if is_small_model:
            original_count = len(prompt_ast.blocks)
            prompt_ast.blocks = [b for b in prompt_ast.blocks if b.required or b.priority < 8]
            if len(prompt_ast.blocks) < original_count:
                logger.info(
                    "OPTIMIZER: Prompt-Leck gestoppt. %s Blöcke für %s entfernt.",
                    original_count - len(prompt_ast.blocks),
                    model_id,
                )

        return prompt_ast

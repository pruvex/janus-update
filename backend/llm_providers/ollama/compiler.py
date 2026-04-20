from backend.services.prompting.compilers.base import BasePromptCompiler
from backend.services.prompting.core.model import Prompt


class OllamaCompiler(BasePromptCompiler):
    """
    Compiler für lokale Modelle (Llama 3, Gemma 2 etc.).
    Fokussiert auf radikale Kürze und Plaintext ohne Overhead.
    """

    def compile(self, prompt_ast: Prompt, model_id: str, max_tokens: int) -> str:
        compiled_parts = ["Du bist Janus."]
        for block in prompt_ast.blocks:
            if block.type == "skill_directive":
                instruction_set = getattr(block.content, "instruction_set", {}) or {}
                selected = instruction_set.get("mini") or instruction_set.get("nano") or instruction_set.get("standard") or ""
                if selected:
                    compiled_parts.append(selected)
            else:
                compiled_parts.append(str(block.content))
        return "\n".join(compiled_parts)

from typing import Any, Dict

from ..core.model import Prompt, PromptBlock, SkillDirective
from ..factory import get_compiler
from .optimizer import PromptOptimizer


class PromptBuilder:
    def __init__(self):
        self.prompt = Prompt()
        self.optimizer = PromptOptimizer()

    def add_block(self, block_type: str, content: Any, priority: int = 10, required: bool = False):
        self.prompt.blocks.append(
            PromptBlock(type=block_type, content=content, priority=priority, required=required)
        )
        return self

    def add_skill_directive(
        self,
        skill_id: str,
        instruction_set: Dict[str, str],
        priority: int = 2,
        required: bool = False,
    ):
        self.prompt.blocks.append(
            PromptBlock(
                type="skill_directive",
                content=SkillDirective(skill_id=skill_id, instruction_set=instruction_set),
                priority=priority,
                required=required,
            )
        )
        return self

    def compile(self, provider: str, model_id: str, max_tokens: int = 4000) -> str:
        optimized_ast = self.optimizer.optimize(self.prompt, model_id, max_tokens)
        compiler = get_compiler(provider)
        return compiler.compile(optimized_ast, model_id, max_tokens)

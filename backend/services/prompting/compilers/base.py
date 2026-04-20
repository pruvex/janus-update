# backend/services/prompting/compilers/base.py
from abc import ABC, abstractmethod

from ..core.model import Prompt


class BasePromptCompiler(ABC):
    """
    Abstrakte Basisklasse für alle Provider-spezifischen Prompt-Compiler.
    Jeder Compiler ist dafür verantwortlich, ein Prompt-AST in einen finalen,
    für das Ziel-LLM optimierten String zu rendern.
    """

    @abstractmethod
    def compile(self, prompt_ast: Prompt, model_id: str, max_tokens: int) -> str:
        """Kompiliert das Prompt-AST modell-spezifisch."""
        raise NotImplementedError

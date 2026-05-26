from backend.services.prompting.compilers.base import BasePromptCompiler
from backend.llm_providers.gemini.compiler import GeminiCompiler
from backend.llm_providers.ollama.compiler import OllamaCompiler
from backend.llm_providers.openai.compiler import OpenAICompiler


def get_compiler(provider: str) -> BasePromptCompiler:
    p_lower = str(provider or "").lower()
    if p_lower == "openai":
        return OpenAICompiler()
    if p_lower == "gemini":
        return GeminiCompiler()
    if p_lower == "ollama":
        return OllamaCompiler()
    return OpenAICompiler()

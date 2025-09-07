# backend/llm_providers/base_provider.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLMProvider(ABC):
    """
    Abstrakte Basisklasse, die das Interface für alle LLM-Provider definiert.
    """

    @abstractmethod
    async def generate_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generiert eine textbasierte Antwort oder eine Tool-Call-Anfrage.
        """
        pass

    @abstractmethod
    async def generate_image(
        self,
        api_key: str,
        model: str,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generiert ein Bild und gibt ein Dictionary mit der URL und den Kosten zurück.
        """
        pass

    def get_available_models(self) -> List[str]:
        """
        Gibt eine Liste der verfügbaren Modelle für diesen Provider zurück.
        Standardimplementierung gibt eine leere Liste zurück.
        """
        return []

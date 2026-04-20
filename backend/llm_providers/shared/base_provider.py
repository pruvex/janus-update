# backend/llm_providers/base_provider.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel  # <--- WICHTIG: Dieser Import fehlte

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
        image_data: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generiert eine textbasierte Antwort oder eine Tool-Call-Anfrage.
        """
        pass

    @abstractmethod
    async def generate_structured_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        response_format: type[BaseModel],
        **kwargs,
    ) -> tuple[BaseModel, Dict[str, Any]]: # <--- ÄNDERUNG: Tuple statt nur BaseModel
        """
        Generiert eine strukturierte Antwort.
        Returns:
            tuple: (Das validierte Pydantic-Objekt, Das Dictionary mit Kosten/Usage-Daten)
        """
        pass

    @abstractmethod
    async def generate_image(
        self, 
        api_key: str, 
        model: str, 
        prompt: str, 
        narrative_prompt: str,
        preset_context: Dict,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generiert ein Bild und gibt ein Dictionary mit der URL und den Kosten zurück.
        
        Args:
            api_key: API-Schlüssel für den Dienst
            model: Modellname, das für die Generierung verwendet werden soll
            prompt: Der primäre Prompt für die Bildgenerierung
            narrative_prompt: Eine narrative Beschreibung des gewünschten Ergebnisses
            preset_context: Kontextinformationen für Preset-Einstellungen
            **kwargs: Zusätzliche parameter-spezifische Argumente
            
        Returns:
            Ein Dictionary mit der generierten Bild-URL und Metadaten
        """
        pass
        
    @abstractmethod
    def prepare_history_for_second_call(
        self,
        chat_history: List[Dict],
        raw_assistant_response: Dict,
        tool_results: List[Dict]
    ) -> List[Dict]:
        """
        Bereitet die Chat-Historie für den Folgeaufruf nach einer Tool-Ausführung vor.
        Ermöglicht provider-spezifische Anpassungen, wie das Hinzufügen von
        Trigger-Nachrichten.
        
        Args:
            chat_history: Die bisherige Chat-Historie
            raw_assistant_response: Die rohe Antwort des Assistenten mit dem Tool-Aufruf
            tool_results: Die Ergebnisse der Tool-Ausführung(en)
            
        Returns:
            Die vorbereitete Chat-Historie für den nächsten Aufruf
        """
        pass

    def get_available_models(self) -> List[str]:
        """
        Gibt eine Liste der verfügbaren Modelle für diesen Provider zurück.
        Standardimplementierung gibt eine leere Liste zurück.
        """
        return []

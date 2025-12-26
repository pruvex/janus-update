from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseWebSearchProvider(ABC):
    """
    Abstrakte Basisklasse, die das Interface für alle Websuche-Provider definiert.
    """
    @abstractmethod
    async def search(self, api_key: str, query: str, model: str) -> Dict[str, Any]:
        """
        Führt eine Suche durch und gibt ein standardisiertes Dictionary mit
        'text', 'urls', 'usage' und 'cost' zurück.
        """
        pass

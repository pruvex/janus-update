# Umsetzungsplan: Refactoring des LLM-Gateways mit Provider-Abstraktion

**Ziel:** Implementierung einer Abstraktionsschicht für LLM-Provider, um die Kopplung zu reduzieren, die Wartbarkeit zu erhöhen und die Erweiterbarkeit des Systems zu verbessern, wie in `Entkopplung.md` vorgeschlagen.

**Referenzdokument:** `Entkopplung.md`

---

## Schritt-für-Schritt-Umsetzungsplan

### Phase 1: Schaffung der Abstraktion

**1.1. Erstellen der abstrakten Basisklasse**

*   **Aktion:** Neue Datei `backend/llm_providers/base_provider.py` erstellen.
*   **Inhalt:**
    ```python
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

        # Diese Methode ist optional, aber gut für die Zukunft
        def get_available_models(self) -> List[str]:
            """
            Gibt eine Liste der verfügbaren Modelle für diesen Provider zurück.
            Standardimplementierung gibt eine leere Liste zurück.
            """
            return []
    ```

### Phase 2: Anpassung der konkreten Provider

**2.1. Refactoring von `openai_service.py`**

*   **Aktion:** Die Datei `backend/llm_providers/openai_service.py` anpassen.
*   **Änderungen:**
    1.  Die bestehenden Funktionen `_call_openai_api` und `generate_image_tool` in eine neue Klasse `OpenAIServiceProvider` verschieben und zu Methoden machen.
    2.  Die Klasse von `BaseLLMProvider` erben lassen.
    3.  Die Methodensignaturen an den `BaseLLMProvider`-Vertrag anpassen.
    4.  Die Logik aus den alten Funktionen in die neuen Methoden integrieren.

*   **Neuer Code-Ausschnitt:**
    ```python
    # backend/llm_providers/openai_service.py
    from .base_provider import BaseLLMProvider
    # ... weitere imports

    class OpenAIServiceProvider(BaseLLMProvider):
        async def generate_response(self, api_key: str, model: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, **kwargs) -> Dict[str, Any]:
            # Logik aus der alten _call_openai_api Funktion hier einfügen
            # client = openai.AsyncOpenAI(api_key=api_key)
            # ...
            pass

        async def generate_image(self, api_key: str, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
            # Logik aus der alten generate_image_tool Funktion hier einfügen
            # client = openai.AsyncOpenAI(api_key=api_key)
            # ...
            # Wichtig: Das Ergebnis muss dem erwarteten Format entsprechen (z.B. {"image_url": ..., "usage": ..., "cost": ...})
            pass
    ```

**2.2. Refactoring von `gemini_service.py`**

*   **Aktion:** Die Datei `backend/llm_providers/gemini_service.py` anpassen.
*   **Änderungen:**
    1.  Eine neue Klasse `GeminiServiceProvider` erstellen, die von `BaseLLMProvider` erbt.
    2.  Die Logik aus `_call_gemini_api` in die `generate_response`-Methode der Klasse verschieben.
    3.  Die Logik aus `_call_gemini_image_generation_api` in die `generate_image`-Methode der Klasse verschieben.
    4.  Sicherstellen, dass die Rückgabewerte dem Vertrag entsprechen.

*   **Neuer Code-Ausschnitt:**
    ```python
    # backend/llm_providers/gemini_service.py
    from .base_provider import BaseLLMProvider
    # ... weitere imports

    class GeminiServiceProvider(BaseLLMProvider):
        async def generate_response(self, api_key: str, model: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, **kwargs) -> Dict[str, Any]:
            # Logik aus der alten _call_gemini_api Funktion hier einfügen
            # genai.configure(api_key=api_key)
            # ...
            pass

        async def generate_image(self, api_key: str, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
            # Logik aus der alten _call_gemini_image_generation_api Funktion hier einfügen
            # genai.configure(api_key=api_key)
            # ...
            pass
    ```

### Phase 3: Simplifizierung des Gateways und der Aufrufer

**3.1. Refactoring von `llm_gateway.py`**

*   **Aktion:** Die Datei `backend/llm_gateway.py` stark vereinfachen.
*   **Änderungen:**
    1.  Die `if/elif`-Logik komplett entfernen.
    2.  Die Provider-Klassen und die Factory-Funktion implementieren.
    3.  Die `call_llm`-Funktion so anpassen, dass sie die Factory nutzt.

*   **Neuer Code:**
    ```python
    # backend/llm_gateway.py
    import logging
    from typing import List, Dict, Optional
    from backend.llm_providers.base_provider import BaseLLMProvider
    from backend.llm_providers.gemini_service import GeminiServiceProvider
    from backend.llm_providers.openai_service import OpenAIServiceProvider

    logger = logging.getLogger('janus_backend')

    PROVIDER_MAP = {
        "gemini": GeminiServiceProvider,
        "openai": OpenAIServiceProvider,
    }

    def get_provider(provider_name: str) -> BaseLLMProvider:
        """Factory-Funktion, die eine Instanz des angeforderten Providers zurückgibt."""
        provider_class = PROVIDER_MAP.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unbekannter Provider: {provider_name}")
        return provider_class()

    async def call_llm(provider: str, model_id: str, api_key: str, messages: List[Dict], **kwargs):
        """Ruft den entsprechenden LLM-Provider auf, um eine Antwort zu generieren."""
        llm_provider = get_provider(provider)
        # Das 'messages' Argument wird hier zu 'messages' in der Methode
        return await llm_provider.generate_response(api_key=api_key, model=model_id, messages=messages, **kwargs)

    async def generate_image(provider: str, model_id: str, api_key: str, prompt: str, **kwargs):
        """Ruft den entsprechenden Provider auf, um ein Bild zu generieren."""
        llm_provider = get_provider(provider)
        return await llm_provider.generate_image(api_key=api_key, model=model_id, prompt=prompt, **kwargs)

    # Die Funktion 'reason_and_respond' muss ebenfalls angepasst werden, um die neuen,
    # vereinfachten Gateway-Funktionen zu nutzen.
    async def reason_and_respond(...)
        # ...
        response = await call_llm(provider, model, ..., messages=final_chat_history, tools=tools)
        # ...
    ```

**3.2. Anpassung von `main.py`**

*   **Aktion:** Die Aufrufe im `handle_chat_request` in `backend/main.py` überprüfen.
*   **Änderungen:**
    1.  Der spezielle Codepfad für die Gemini-Bildgenerierung muss angepasst werden, um die neue `llm_gateway.generate_image`-Funktion zu verwenden.
    2.  Der Aufruf von `llm_gateway.reason_and_respond` muss überprüft werden, um sicherzustellen, dass alle Parameter noch stimmen.

### Phase 4: Testen und Verifizieren

**4.1. Teststrategie**

1.  **Unit-Tests für Provider:** Erstelle/aktualisiere Tests für `GeminiServiceProvider` und `OpenAIServiceProvider`, um deren Methoden isoliert zu testen (mit Mocks für die externen APIs).
2.  **Unit-Tests für Gateway:** Erstelle/aktualisiere Tests für `llm_gateway.py`, insbesondere für die `get_provider`-Factory.
3.  **Integrationstests:** Passe die bestehenden Integrationstests in `waechter/` an, die den gesamten Flow von `main.py` bis zum (gemockten) Provider testen.
4.  **Manueller Test:** Führe nach der Implementierung manuelle Tests für beide Provider durch (sowohl Text- als auch Bildgenerierung), um die korrekte Funktion des gesamten Systems zu verifizieren.

---

Dieser Plan bricht die Aufgabe in logische, überschaubare Schritte herunter und stellt sicher, dass die Architekturverbesserung kontrolliert und verifizierbar umgesetzt wird.

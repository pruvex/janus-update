Ziel: Das websearch_tool so umzubauen, dass es komplett unabhängig von OpenAI funktioniert und von jedem LLM (inklusive Gemini) korrekt genutzt werden kann, sowohl bei direkter Anforderung als auch im Fallback-Szenario.
Schritt 1: Die Umgebung vorbereiten (Das neue Werkzeug installieren)
Wir geben unserem System die Fähigkeit, selbstständig zu suchen.
Anwendung stoppen: Gehen Sie zu Ihrem PowerShell-Terminal und beenden Sie den laufenden Prozess vollständig mit STRG + C, bis Sie wieder an der PS C:\KI\Janus-Projekt>-Eingabeaufforderung sind.
Virtuelle Umgebung aktivieren:
code
Powershell
.\backend\venv\Scripts\activate
(Die Eingabeaufforderung sollte nun mit (venv) beginnen.)
Unabhängige Such-Bibliothek installieren:
code
Powershell
pip install googlesearch-python
Schritt 2: Das websearch_tool austauschen
Wir ersetzen die alte, abhängige Logik durch die neue, unabhängige.
Datei öffnen: Navigieren Sie zu der Datei, in der Ihre Werkzeuge definiert sind. Basierend auf Ihren Logs ist dies höchstwahrscheinlich C:\KI\Janus-Projekt\backend\tool_registry.py.
Code ersetzen: Ersetzen Sie die gesamte, existierende websearch_tool-Funktion mit dem folgenden Codeblock. Fügen Sie außerdem die beiden import-Zeilen ganz oben in der Datei hinzu.
code
Python
# FÜGEN SIE DIESE IMPORTE GANZ OBEN IN tool_registry.py HINZU
from googlesearch import search
import logging

# ... (eventuell andere imports)

logger = logging.getLogger('janus_backend')

# ... (Definitionen Ihrer anderen Werkzeuge)

# ERSETZEN SIE DIE ALTE websearch_tool FUNKTION KOMPLETT HIERMIT:
def websearch_tool(query: str) -> str:
    """
    Führt eine Websuche mit der googlesearch-python Bibliothek durch und gibt die
    Top-Ergebnisse als formatierten String zurück. Benötigt keinen API-Schlüssel.
    """
    logger.info(f"Performing independent web search for query: '{query}'")
    try
        search_results = list(search(query, num_results=5, lang="de"))

        if not search_results:
            return "Die Websuche ergab keine Ergebnisse."

        formatted_results = "Hier sind die Top-Ergebnisse der Websuche:\n"
        for i, result in enumerate(search_results, 1):
            formatted_results += f"[{i}] {result}\n"
        
        return formatted_results

    except Exception as e:
        logger.error(f"Error during independent web search: {e}", exc_info=True)
        return f"Fehler bei der Websuche: {e}"

# ... (Rest der Datei)
Schritt 3: Die Fallback-Logik im Gateway reparieren
Wir bringen dem System bei, auch dann das neue Werkzeug zu benutzen, wenn das LLM "aufgibt".
Datei öffnen: Öffnen Sie C:\KI\Janus-Projekt\backend\llm_gateway.py.
Import hinzufügen: Fügen Sie ganz oben in der Datei diese Import-Anweisung hinzu:
code
Python
from backend.tool_registry import TOOL_REGISTRY
Logikblock ersetzen: Suchen Sie in der reason_and_respond-Funktion den folgenden Block (ca. Zeile 78):
code
Python
# FINDEN SIE DIESEN BLOCK
if response.get("type") == "text" and response.get("text") == "Ich habe dazu keine Informationen in meinen Fakten.":
    logger.info("LLM indicated no information in facts. Performing web search...")
    web_result = await perform_websearch(user_prompt)
    return {
        "type": "text",
        "text": web_result,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "model": "websearch"},
        "cost": {"total_cost": WEBSEARCH_COST_PER_QUERY}
    }
Ersetzen Sie den gesamten Block mit dieser korrigierten Version:
code
Python
# ERSETZEN SIE DEN BLOCK MIT DIESEM
if response.get("type") == "text" and "Ich habe dazu keine Informationen" in response.get("text", ""):
    logger.info("LLM indicated no information in facts. Performing independent fallback web search...")
    
    websearch_tool_func = TOOL_REGISTRY.get("websearch_tool").func
    
    web_result = websearch_tool_func(query=user_prompt)

    return {
        "type": "text",
        "text": web_result,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "model": "independent_websearch"},
        "cost": {"total_cost": WEBSEARCH_COST_PER_QUERY}
    }
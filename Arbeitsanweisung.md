Schritt 2: Entfernen der Sonderlogik im llm_gateway.py
Wir entfernen die if provider == 'gemini':-Logik, die wir zur Aktivierung der nativen Suche hinzugefügt hatten.
Aktion: Öffnen Sie die Datei C:\KI\Janus-Projekt\backend\llm_gateway.py. Suchen und löschen Sie den folgenden oder einen ähnlichen Code-Block aus der reason_and_respond-Funktion:
code
Python
# FINDEN UND LÖSCHEN SIE DIESEN GESAMTEN BLOCK
kwargs_for_llm = {}
if provider == 'gemini' and tools:
    tools = [tool for tool in tools if tool.get('function', {}).get('name') != 'websearch_tool']
    kwargs_for_llm['enable_native_search'] = True
    logger.info("Requesting Gemini native search instead of generic websearch_tool.")
Stellen Sie außerdem sicher, dass der Aufruf der call_llm-Funktion am Ende keine **kwargs_for_llm mehr enthält. Er sollte so aussehen:
code
Python
# STELLEN SIE SICHER, DASS DER AUFRUF SO AUSSIEHT
response = await call_llm(
    provider, 
    model, 
    api_key, 
    messages=final_chat_history, 
    tools=tools
)
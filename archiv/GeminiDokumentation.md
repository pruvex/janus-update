Technische Dokumentation: Function Calling für KI-Modelle (OpenAI & Gemini)
1. Zweck und Kernkonzept
Function Calling ist ein Mechanismus, der es einem Sprachmodell (LLM) ermöglicht, externe Werkzeuge (Tools) zu verwenden, um Informationen zu beschaffen oder Aktionen in der realen Welt auszuführen.
Die Goldene Regel: Das LLM führt den Code NICHT selbst aus. Es agiert als intelligenter "Scheduler" oder "Entscheidungsfinder". Der Prozess ist immer ein Dialog zwischen der KI und unserer Anwendung.
2. Der Workflow (Analyse des Diagramms)
Der Prozess des Function Calling läuft immer in den folgenden, klar definierten Schritten ab. Ein Fehler in einem dieser Schritte unterbricht die gesamte Kette.
Benutzeranfrage: Der Benutzer stellt eine Anfrage in natürlicher Sprache (z.B., "Erstelle einen Ordner namens 'Projekte' auf meinem Desktop").
Anfrage an die KI (mit Werkzeugen): Unsere Anwendung sendet nicht nur den Prompt des Benutzers an die KI, sondern auch eine Liste aller verfügbaren Werkzeuge in einem speziell formatierten Schema.
KI-Antwort: Funktionsaufruf (Function Call): Die KI analysiert den Prompt und die Werkzeugliste. Wenn sie ein passendes Werkzeug findet, antwortet sie NICHT mit Text, sondern mit einem strukturierten Datenobjekt (JSON), das den Namen des zu verwendenden Werkzeugs und die extrahierten Argumente enthält.
Beispiel-Antwort der KI: { "name": "create_directory_tool", "arguments": { "path": "Desktop/Projekte" } }
Anwendung führt die Funktion aus: Unsere Anwendung empfängt dieses JSON-Objekt.
Sie sucht in ihrer internen Registrierung (tool_registry.py) nach der Python-Funktion, die zu "create_directory_tool" gehört.
Sie führt diese echte Python-Funktion (filesystem_manager.create_directory) mit den übergebenen Argumenten (path="Desktop/Projekte") aus.
Ergebnis an die KI zurücksenden: Die Anwendung nimmt das Ergebnis der Python-Funktion (z.B., "Ordner 'Desktop/Projekte' wurde erfolgreich erstellt.") und sendet es in einer zweiten Anfrage zurück an die KI. Diese Anfrage enthält den gesamten bisherigen Gesprächsverlauf, einschließlich des ursprünglichen Funktionsaufrufs und dessen Ergebnis.
Finale KI-Antwort an den Benutzer: Die KI erhält das Ergebnis der Werkzeugausführung. Basierend auf diesem Ergebnis formuliert sie eine finale, menschenlesbare Antwort (z.B., "Okay, ich habe den Ordner 'Projekte' auf deinem Desktop für dich erstellt.").
3. Technische Implementierungsdetails
3.1. Die Tool-Definition (Das Schema) - Der kritischste Punkt
Dies ist die "Bedienungsanleitung" für die KI und die häufigste Fehlerquelle. Jeder Anbieter (OpenAI, Gemini) hat hier extrem strenge und leicht unterschiedliche Anforderungen.
Umgang mit Optionalen Parametern:
Pydantic wandelt Optional[str] in ein komplexes JSON-Schema mit anyOf um (z.B. {"anyOf": [{"type": "string"}, {"type": "null"}]}). Dies ist für Gemini ungültig. Das Schema muss vor dem Senden an die API bereinigt werden, sodass nur der primäre Typ (z.B. {"type": "string"}) übrig bleibt.
OpenAI-Format:
OpenAI erwartet eine Struktur, die explizit als "type": "function" deklariert ist. Die Parameterbeschreibung selbst muss ein Objekt sein, das als "type": "object" definiert ist.
Beispiel für OpenAI:
code
JSON
{
  "type": "function",
  "function": {
    "name": "list_directory_tool",
    "description": "Listet den Inhalt eines Ordners auf...",
    "parameters": {
      "type": "object",
      "properties": {
        "path": { "type": "string" },
        "pattern": { "type": "string" }
      },
      "required": ["path"]
    }
  }
}
Gemini-Format:
Gemini erwartet eine flachere Struktur. Die Parameter-Typen müssen großgeschrieben werden (STRING, INTEGER, etc.). Die umschließende parameters-Definition darf KEIN "type": "object" enthalten. Die gesamte Definition wird nicht in ein "function"-Objekt verpackt.
Beispiel für Gemini:
code
JSON
{
  "name": "list_directory_tool",
  "description": "Listet den Inhalt eines Ordners auf...",
  "parameters": {
    "properties": {
      "path": { "type": "STRING" },
      "pattern": { "type": "STRING" }
    },
    "required": ["path"]
  }
}
Wichtig für Gemini: Die finale Liste aller Tools muss in ein spezielles GeminiTool-Objekt verpackt werden, bevor sie an die API gesendet wird: [GeminiTool(function_declarations=[...])].
3.2. Die API-Aufrufe
Erste Anfrage: model.generate_content_async(prompt, tools=[...])
Zweite Anfrage (nach Tool-Ausführung): model.generate_content_async(chat_history_with_tool_result)
4. Zusammenfassung & Goldene Regeln für den Coding Agent
Die KI führt niemals Code aus. Sie schlägt nur vor, welches Werkzeug mit welchen Argumenten verwendet werden soll. Unsere Anwendung ist immer die ausführende Instanz.
Das Schema ist König. 99 % aller InvalidArgument-Fehler liegen an einem falsch formatierten Tool-Schema. Die Schemas für OpenAI und Gemini sind nicht identisch.
Unterschiede strikt beachten:
OpenAI: Benötigt {"type": "function", "function": {...}} und {"type": "object"} für Parameter.
Gemini: Benötigt eine flache Liste von Funktionsdeklarationen, großgeschriebene Typen (z.B. STRING), und darf kein "type": "object" in der Parameter-Definition haben.
Einfachheit bevorzugen: Die KI kommt besser mit einfachen, klaren Tool-Beschreibungen und Parameter-Definitionen zurecht. Vermeide komplexe, verschachtelte Schemas, wenn möglich. Bereinige Pydantic-generierte Schemas von unnötigen Feldern (title, anyOf), bevor sie an die API gesendet werden.
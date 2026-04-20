Fundierung mit der Google Suche



Durch die Fundierung mit der Google Suche wird das Gemini-Modell mit Echtzeit-Webinhalten verknüpft. Diese Funktion ist in allen verfügbaren Sprachen verfügbar. So kann Gemini genauere Antworten geben und überprüfbare Quellen zitieren, die über den Wissensstand des Modells hinausgehen.

Mithilfe von Grounding können Sie Anwendungen erstellen, die Folgendes können:

Faktische Richtigkeit erhöhen:Modellhalluzinationen werden reduziert, indem Antworten auf realen Informationen basieren.
Echtzeitinformationen abrufen:Fragen zu aktuellen Ereignissen und Themen beantworten.
Zitierungen angeben:Sie können das Vertrauen der Nutzer stärken, indem Sie die Quellen für die Behauptungen des Modells angeben.

Python
JavaScript
REST

curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "contents": [
      {
        "parts": [
          {"text": "Who won the euro 2024?"}
        ]
      }
    ],
    "tools": [
      {
        "google_search": {}
      }
    ]
  }'
Weitere Informationen finden Sie im Notebook zum Suchtool.

So funktioniert die Fundierung mit der Google Suche
Wenn Sie das Tool google_search aktivieren, übernimmt das Modell den gesamten Workflow der Suche, Verarbeitung und Quellenangabe von Informationen automatisch.

grounding-overview

Nutzer-Prompt:Ihre Anwendung sendet den Prompt eines Nutzers mit aktiviertem google_search-Tool an die Gemini API.
Prompt-Analyse:Das Modell analysiert den Prompt und ermittelt, ob eine Google-Suche die Antwort verbessern kann.
Google Suche:Bei Bedarf generiert das Modell automatisch eine oder mehrere Suchanfragen und führt sie aus.
Verarbeitung der Suchergebnisse:Das Modell verarbeitet die Suchergebnisse, fasst die Informationen zusammen und formuliert eine Antwort.
Fundierte Antwort:Die API gibt eine endgültige, nutzerfreundliche Antwort zurück, die auf den Suchergebnissen basiert. Diese Antwort enthält die Textantwort des Modells und groundingMetadata mit den Suchanfragen, Webergebnissen und Quellenangaben.
Antworten verstehen, die auf Informationen aus dem Web basieren
Wenn eine Antwort erfolgreich fundiert ist, enthält sie das Feld groundingMetadata. Diese strukturierten Daten sind unerlässlich, um Behauptungen zu überprüfen und eine umfassende Zitationsfunktion in Ihrer Anwendung zu erstellen.


{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "Spain won Euro 2024, defeating England 2-1 in the final. This victory marks Spain's record fourth European Championship title."
          }
        ],
        "role": "model"
      },
      "groundingMetadata": {
        "webSearchQueries": [
          "UEFA Euro 2024 winner",
          "who won euro 2024"
        ],
        "searchEntryPoint": {
          "renderedContent": "<!-- HTML and CSS for the search widget -->"
        },
        "groundingChunks": [
          {"web": {"uri": "https://vertexaisearch.cloud.google.com.....", "title": "aljazeera.com"}},
          {"web": {"uri": "https://vertexaisearch.cloud.google.com.....", "title": "uefa.com"}}
        ],
        "groundingSupports": [
          {
            "segment": {"startIndex": 0, "endIndex": 85, "text": "Spain won Euro 2024, defeatin..."},
            "groundingChunkIndices": [0]
          },
          {
            "segment": {"startIndex": 86, "endIndex": 210, "text": "This victory marks Spain's..."},
            "groundingChunkIndices": [0, 1]
          }
        ]
      }
    }
  ]
}
Die Gemini API gibt die folgenden Informationen mit dem groundingMetadata zurück:

webSearchQueries : Array der verwendeten Suchanfragen. Das ist nützlich, um Fehler zu beheben und den Denkprozess des Modells nachzuvollziehen.
searchEntryPoint : Enthält das HTML und CSS zum Rendern der erforderlichen Suchvorschläge. Die vollständigen Nutzungsbedingungen finden Sie in den Nutzungsbedingungen.
groundingChunks : Array von Objekten, die die Webquellen (uri und title) enthalten.
groundingSupports : Array von Chunks, um die Modellantwort text mit den Quellen in groundingChunks zu verknüpfen. Jeder Chunk verknüpft einen Text segment (definiert durch startIndex und endIndex) mit einem oder mehreren groundingChunkIndices. Das ist der Schlüssel zum Erstellen von Inline-Zitaten.
Die Fundierung mit der Google Suche kann auch in Kombination mit dem Tool für URL-Kontext verwendet werden, um Antworten sowohl auf öffentlichen Webdaten als auch auf den von Ihnen angegebenen spezifischen URLs zu fundieren.

Quellen mit Inline-Zitationen angeben
Die API gibt strukturierte Zitationsdaten zurück, sodass Sie die Quellen in Ihrer Benutzeroberfläche beliebig darstellen können. Mit den Feldern groundingSupports und groundingChunks können Sie die Aussagen des Modells direkt mit den Quellen verknüpfen. Hier ist ein gängiges Muster für die Verarbeitung der Metadaten, um eine Antwort mit Inline-Zitaten zu erstellen, auf die geklickt werden kann.

Python
JavaScript

def add_citations(response):
    text = response.text
    supports = response.candidates[0].grounding_metadata.grounding_supports
    chunks = response.candidates[0].grounding_metadata.grounding_chunks

    # Sort supports by end_index in descending order to avoid shifting issues when inserting.
    sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

    for support in sorted_supports:
        end_index = support.segment.end_index
        if support.grounding_chunk_indices:
            # Create citation string like [1](link1)[2](link2)
            citation_links = []
            for i in support.grounding_chunk_indices:
                if i < len(chunks):
                    uri = chunks[i].web.uri
                    citation_links.append(f"[{i + 1}]({uri})")

            citation_string = ", ".join(citation_links)
            text = text[:end_index] + citation_string + text[end_index:]

    return text

# Assuming response with grounding metadata
text_with_citations = add_citations(response)
print(text_with_citations)
Die neue Antwort mit Inline-Zitaten sieht so aus:


Spain won Euro 2024, defeating England 2-1 in the final.[1](https:/...), [2](https:/...), [4](https:/...), [5](https:/...) This victory marks Spain's record-breaking fourth European Championship title.[5]((https:/...), [2](https:/...), [3](https:/...), [4](https:/...)
Preise
Wenn Sie die Fundierung mit der Google Suche mit Gemini 3 verwenden, wird Ihr Projekt für jede Suchanfrage abgerechnet, die das Modell ausführt. Wenn das Modell mehrere Suchanfragen ausführt, um eine einzelne Aufforderung zu beantworten (z. B. wenn in demselben API-Aufruf nach "UEFA Euro 2024 winner" und "Spain vs England Euro 2024 final score" gesucht wird), zählt dies für diese Anfrage als zwei abrechenbare Nutzungen des Tools. Für Abrechnungszwecke werden leere Websuchanfragen beim Zählen eindeutiger Anfragen ignoriert. Dieses Abrechnungsmodell gilt nur für Gemini 3-Modelle. Wenn Sie die Suche als Fundierung mit Gemini 2.5 oder älteren Modellen verwenden, wird Ihr Projekt pro Prompt abgerechnet.

Ausführliche Preisinformationen finden Sie auf der Seite Gemini API-Preise.

Unterstützte Modelle
Eine vollständige Liste der Funktionen finden Sie auf der Modellübersichtsseite.

Modell	Fundierung mit der Google Suche
Gemini 3.1 Flash Image Preview	✔️
Gemini 3.1 Pro (Vorabversion)	✔️
Gemini 3 Pro Image (Vorabversion)	✔️
Gemini 3 Flash (Vorabversion)	✔️
Gemini 2.5 Pro	✔️
Gemini 2.5 Flash	✔️
Gemini 2.5 Flash-Lite	✔️
Gemini 2.0 Flash	✔️
Hinweis :Bei älteren Modellen wird das Tool google_search_retrieval verwendet. Verwenden Sie für alle aktuellen Modelle das google_search-Tool, wie in den Beispielen gezeigt.
Unterstützte Kombinationen von Tools
Sie können Grounding mit der Google Suche zusammen mit anderen Tools wie Codeausführung und URL-Kontext verwenden, um komplexere Anwendungsfälle zu ermöglichen.
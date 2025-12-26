Bildgenerierung mit Gemini (auch bekannt als Nano Banana und Nano Banana Pro)

content_copy



Gemini kann Bilder im Rahmen von Unterhaltungen generieren und verarbeiten. Sie können die Bildmodelle Gemini 2.5 Flash (Nano Banana) oder Gemini 3 Pro (Nano Banana Pro) mit Text, Bildern oder einer Kombination aus beidem auffordern, Bilder zu erstellen, zu bearbeiten und zu iterieren.

Text, Bild und mehrere Bilder zu Bild:Generieren Sie hochwertige Bilder aus Textbeschreibungen, verwenden Sie Text-Prompts, um ein bestimmtes Bild zu bearbeiten und anzupassen, oder verwenden Sie mehrere Eingabebilder, um neue Szenen zu erstellen und Stile zu übertragen.
Iterative Optimierung:Sie können Ihr Bild in mehreren Schritten optimieren und kleine Anpassungen vornehmen, bis es perfekt ist.
Text-Rendering in hoher Qualität:Bilder mit lesbarem und gut platziertem Text werden präzise generiert. Das ist ideal für Logos, Diagramme und Poster.
Alle generierten Bilder enthalten ein SynthID-Wasserzeichen.

Bildgenerierung (Text-zu-Bild)
Python
JavaScript
Ok
Java
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [
        {"text": "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"}
      ]
    }]
  }'
KI-generiertes Bild eines Nano Banana-Gerichts
KI-generiertes Bild eines Nano Banana-Gerichts in einem Restaurant mit Gemini-Thema
Bildbearbeitung (Text-und-Bild-zu-Bild)
Zur Erinnerung: Sie müssen die erforderlichen Rechte an den Bildern haben, die Sie hochladen möchten. Erstelle keine Inhalte, durch die die Rechte anderer verletzt werden, einschließlich Videos oder Bildern, durch die andere getäuscht, belästigt oder geschädigt werden. Ihre Nutzung dieses auf generativer KI basierenden Dienstes unterliegt unserer Richtlinie zur unzulässigen Nutzung.

Sie können ein Bild bereitstellen und Text-Prompts verwenden, um Elemente hinzuzufügen, zu entfernen oder zu ändern, den Stil zu ändern oder die Farbkorrektur anzupassen.

Im folgenden Beispiel wird das Hochladen von base64-codierten Bildern veranschaulicht. Informationen zu mehreren Bildern, größeren Nutzlasten und unterstützten MIME-Typen finden Sie auf der Seite Bildanalyse.

Python
JavaScript
Ok
Java
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\":[
            {\"text\": \"'Create a picture of my cat eating a nano-banana in a fancy restaurant under the Gemini constellation\"},
            {
              \"inline_data\": {
                \"mime_type\":\"image/jpeg\",
                \"data\": \"<BASE64_IMAGE_DATA>\"
              }
            }
        ]
      }]
    }"
KI-generiertes Bild einer Katze, die eine Banane isst
KI-generiertes Bild einer Katze, die eine Nano-Banane isst
Multi-Turn-Bildbearbeitung
Bilder weiterhin per Prompt generieren und bearbeiten Wir empfehlen, Bilder in einem Chat oder einer Multi-Turn Conversation zu optimieren. Im folgenden Beispiel wird ein Prompt zum Generieren einer Infografik zur Fotosynthese gezeigt.

Python
JavaScript
Ok
Java
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "role": "user",
      "parts": [
        {"text": "Create a vibrant infographic that explains photosynthesis as if it were a recipe for a plants favorite food. Show the \"ingredients\" (sunlight, water, CO2) and the \"finished dish\" (sugar/energy). The style should be like a page from a colorful kids cookbook, suitable for a 4th grader."}
      ]
    }],
    "generationConfig": {
      "responseModalities": ["TEXT", "IMAGE"]
    }
  }'
KI-generierte Infografik zur Fotosynthese
KI-generierte Infografik zur Fotosynthese
Sie können dann denselben Chat verwenden, um die Sprache der Grafik in Spanisch zu ändern.

Python
JavaScript
Ok
Java
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [
      {
        "role": "user",
        "parts": [{"text": "Create a vibrant infographic that explains photosynthesis..."}]
      },
      {
        "role": "model",
        "parts": [{"inline_data": {"mime_type": "image/png", "data": "<PREVIOUS_IMAGE_DATA>"}}]
      },
      {
        "role": "user",
        "parts": [{"text": "Update this infographic to be in Spanish. Do not change any other elements of the image."}]
      }
    ],
    "tools": [{"google_search": {}}],
    "generationConfig": {
      "responseModalities": ["TEXT", "IMAGE"],
      "imageConfig": {
        "aspectRatio": "16:9",
        "imageSize": "2K"
      }
    }
  }'
KI-generierte Infografik zur Fotosynthese auf Spanisch
KI-generierte Infografik zur Fotosynthese auf Spanisch
Neu mit Gemini 3 Pro Image
Gemini 3 Pro Image (gemini-3-pro-image-preview) ist ein hochmodernes Modell für die Bildgenerierung und ‑bearbeitung, das für die professionelle Asset-Produktion optimiert ist. Das Modell wurde entwickelt, um die anspruchsvollsten Workflows durch fortschrittliches logisches Denken zu bewältigen. Es eignet sich hervorragend für komplexe Aufgaben, die mehrere Schritte erfordern, um Inhalte zu erstellen und zu ändern.

Ausgabe in hoher Auflösung: Integrierte Funktionen zum Generieren von Bildern in 1K-, 2K- und 4K-Auflösung.
Innovatives Text-Rendering: Das Modell kann gut lesbaren, stilisierten Text für Infografiken, Menüs, Diagramme und Marketing-Assets generieren.
Fundierung mit der Google Suche: Das Modell kann die Google Suche als Tool verwenden, um Fakten zu überprüfen und Bilder auf Grundlage von Echtzeitdaten zu generieren (z.B. aktuelle Wetterkarten, Aktiencharts, aktuelle Ereignisse).
Thinking-Modus: Das Modell verwendet einen „Denkprozess“, um komplexe Prompts zu analysieren. Es werden vorläufige „Gedankenbilder“ generiert (im Backend sichtbar, aber nicht kostenpflichtig), um die Komposition zu optimieren, bevor die endgültige hochwertige Ausgabe erstellt wird.
Bis zu 14 Referenzbilder: Sie können jetzt bis zu 14 Referenzbilder kombinieren, um das endgültige Bild zu erstellen.
Bis zu 14 Referenzbilder verwenden
Mit Gemini 3 Pro (Vorabversion) können Sie bis zu 14 Referenzbilder kombinieren. Diese 14 Bilder können Folgendes enthalten:

Bis zu 6 Bilder von Objekten mit hoher Wiedergabetreue, die in das endgültige Bild aufgenommen werden sollen
Bis zu 5 Bilder von Menschen, um das Aussehen des Charakters beizubehalten

Python
JavaScript
Ok
Java
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\":[
            {\"text\": \"An office group photo of these people, they are making funny faces.\"},
            {\"inline_data\": {\"mime_type\":\"image/png\", \"data\": \"<BASE64_DATA_IMG_1>\"}},
            {\"inline_data\": {\"mime_type\":\"image/png\", \"data\": \"<BASE64_DATA_IMG_2>\"}},
            {\"inline_data\": {\"mime_type\":\"image/png\", \"data\": \"<BASE64_DATA_IMG_3>\"}},
            {\"inline_data\": {\"mime_type\":\"image/png\", \"data\": \"<BASE64_DATA_IMG_4>\"}},
            {\"inline_data\": {\"mime_type\":\"image/png\", \"data\": \"<BASE64_DATA_IMG_5>\"}}
        ]
      }],
      \"generationConfig\": {
        \"responseModalities\": [\"TEXT\", \"IMAGE\"],
        \"imageConfig\": {
          \"aspectRatio\": \"5:4\",
          \"imageSize\": \"2K\"
        }
      }
    }"
KI-generiertes Gruppenfoto vom Büro
KI-generiertes Gruppenfoto vom Büro
Fundierung mit der Google Suche
Mit dem Google Suche-Tool können Sie Bilder auf Grundlage von Echtzeitinformationen wie Wettervorhersagen, Aktiencharts oder aktuellen Ereignissen generieren.

Hinweis: Wenn Sie die Fundierung mit der Google Suche für die Bildgenerierung verwenden, werden bildbasierte Suchergebnisse nicht an das Generierungsmodell übergeben und sind nicht in der Antwort enthalten.

Python
JavaScript
Java
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "Visualize the current weather forecast for the next 5 days in San Francisco as a clean, modern weather chart. Add a visual on what I should wear each day"}]}],
    "tools": [{"google_search": {}}],
    "generationConfig": {
      "responseModalities": ["TEXT", "IMAGE"],
      "imageConfig": {"aspectRatio": "16:9"}
    }
  }'
KI-generiertes 5‑Tages-Wetterdiagramm für San Francisco
KI-generiertes 5‑Tages-Wetterdiagramm für San Francisco
Die Antwort enthält groundingMetadata mit den folgenden erforderlichen Feldern:

searchEntryPoint: Enthält das HTML und CSS zum Rendern der erforderlichen Suchvorschläge.
groundingChunks: Gibt die drei wichtigsten Webquellen zurück, die zur Fundierung des generierten Bildes verwendet wurden.
Bilder mit einer Auflösung von bis zu 4K generieren
Gemini 3 Pro Image generiert standardmäßig Bilder mit einer Auflösung von 1.000 Pixeln, kann aber auch Bilder mit einer Auflösung von 2.000 und 4.000 Pixeln ausgeben. Wenn Sie Assets mit höherer Auflösung generieren möchten, geben Sie die image_size in der generation_config an.

Sie müssen ein großes „K“ verwenden, z.B. 1K, 2K, 4K). Parameter in Kleinbuchstaben (z.B. 1.000) werden abgelehnt.

Python
JavaScript
Ok
Java
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "Da Vinci style anatomical sketch of a dissected Monarch butterfly. Detailed drawings of the head, wings, and legs on textured parchment with notes in English."}]}],
    "tools": [{"google_search": {}}],
    "generationConfig": {
      "responseModalities": ["TEXT", "IMAGE"],
      "imageConfig": {"aspectRatio": "1:1", "imageSize": "1K"}
    }
  }'
Das folgende Bild wurde mit diesem Prompt generiert:

KI-generierte anatomische Skizze eines sezierten Monarchfalters im Stil von Leonardo da Vinci.
KI-generierte anatomische Skizze eines sezierten Monarchfalters im Stil von Leonardo da Vinci.
Denkprozess
Das Gemini 3 Pro Image Preview-Modell ist ein Thinking Model und verwendet einen Denkprozess („Thinking“) für komplexe Prompts. Dieses Feature ist standardmäßig aktiviert und kann in der API nicht deaktiviert werden. Weitere Informationen zum Denkprozess finden Sie im Leitfaden Gemini Thinking.

Das Modell generiert bis zu zwei Zwischenbilder, um Komposition und Logik zu testen. Das letzte Bild unter „Thinking“ ist auch das endgültige gerenderte Bild.

Sie können sich die Überlegungen ansehen, die zur Erstellung des endgültigen Bildes geführt haben.

Python
JavaScript

for part in response.parts:
    if part.thought:
        if part.text:
            print(part.text)
        elif image:= part.as_image():
            image.show()
Thought Signatures
Gedankensignaturen sind verschlüsselte Darstellungen des internen Denkprozesses des Modells und werden verwendet, um den Kontext der Argumentation bei Interaktionen mit mehreren Zügen beizubehalten. Alle Antworten enthalten das Feld thought_signature. In der Regel sollten Sie eine Gedanken-Signatur, die Sie in einer Modellantwort erhalten, genau so zurückgeben, wie Sie sie erhalten haben, wenn Sie den Unterhaltungsverlauf im nächsten Zug senden. Wenn keine Gedanken-Signaturen verteilt werden, kann dies dazu führen, dass die Antwort fehlschlägt. Weitere Informationen zu Signaturen im Allgemeinen finden Sie in der Dokumentation zur Gedankensignatur.

Hinweis :Wenn Sie die offiziellen Google Gen AI SDKs verwenden und die Chatfunktion nutzen oder das vollständige Modellantwortobjekt direkt an den Verlauf anhängen, werden Gedanken-Signaturen automatisch verarbeitet. Sie müssen sie nicht manuell extrahieren oder verwalten und auch Ihren Code nicht ändern.
So funktionieren Gedanken-Signaturen:

Alle inline_data-Teile mit dem Bild mimetype, die Teil der Antwort sind, müssen eine Signatur haben.
Wenn es direkt nach den Gedanken am Anfang (vor einem Bild) Text gibt, sollte auch der erste Textteil eine Signatur haben.
Gedanken haben keine Signaturen. Wenn inline_data-Teile mit dem Bild mimetype Teil von Gedanken sind, haben sie keine Signaturen.
Der folgende Code zeigt ein Beispiel dafür, wo Gedankensignaturen enthalten sind:


[
  {
    "inline_data": {
      "data": "<base64_image_data_0>",
      "mime_type": "image/png"
    },
    "thought": true // Thoughts don't have signatures
  },
  {
    "inline_data": {
      "data": "<base64_image_data_1>",
      "mime_type": "image/png"
    },
    "thought": true // Thoughts don't have signatures
  },
  {
    "inline_data": {
      "data": "<base64_image_data_2>",
      "mime_type": "image/png"
    },
    "thought": true // Thoughts don't have signatures
  },
  {
    "text": "Here is a step-by-step guide to baking macarons, presented in three separate images.\n\n### Step 1: Piping the Batter\n\nThe first step after making your macaron batter is to pipe it onto a baking sheet. This requires a steady hand to create uniform circles.\n\n",
    "thought_signature": "<Signature_A>" // The first non-thought part always has a signature
  },
  {
    "inline_data": {
      "data": "<base64_image_data_3>",
      "mime_type": "image/png"
    },
    "thought_signature": "<Signature_B>" // All image parts have a signatures
  },
  {
    "text": "\n\n### Step 2: Baking and Developing Feet\n\nOnce piped, the macarons are baked in the oven. A key sign of a successful bake is the development of \"feet\"—the ruffled edge at the base of each macaron shell.\n\n"
    // Follow-up text parts don't have signatures
  },
  {
    "inline_data": {
      "data": "<base64_image_data_4>",
      "mime_type": "image/png"
    },
    "thought_signature": "<Signature_C>" // All image parts have a signatures
  },
  {
    "text": "\n\n### Step 3: Assembling the Macaron\n\nThe final step is to pair the cooled macaron shells by size and sandwich them together with your desired filling, creating the classic macaron dessert.\n\n"
  },
  {
    "inline_data": {
      "data": "<base64_image_data_5>",
      "mime_type": "image/png"
    },
    "thought_signature": "<Signature_D>" // All image parts have a signatures
  }
]
Andere Modi zur Bildgenerierung
Gemini unterstützt je nach Promptstruktur und Kontext auch andere Modi für die Bildinteraktion:

Text zu Bild(ern) und Text (verschachtelt): Gibt Bilder mit zugehörigem Text aus.
Beispiel-Prompt: „Erstelle ein illustriertes Rezept für eine Paella.“
Bild(er) und Text zu Bild(ern) und Text (verschachtelt): Verwendet Eingabebilder und ‑text, um neue zugehörige Bilder und Texte zu erstellen.
Beispiel-Prompt: (Mit einem Bild eines möblierten Zimmers) „Welche anderen Sofafarben würden in meinen Raum passen? Kannst du das Bild aktualisieren?“
Bilder im Batch generieren
Wenn Sie viele Bilder generieren müssen, können Sie die Batch API verwenden. Sie erhalten höhere Ratenlimits im Austausch für eine Bearbeitungszeit von bis zu 24 Stunden.

In der Dokumentation zur Batch API-Bildgenerierung und im Kochbuch finden Sie Beispiele und Code für die Batch API-Bildgenerierung.

Anleitung und Strategien für Prompts
Die Bildgenerierung basiert auf einem grundlegenden Prinzip:

Beschreiben Sie die Szene, anstatt nur Keywords aufzulisten. Die Stärke des Modells liegt in seinem tiefen Sprachverständnis. Ein narrativer, beschreibender Absatz führt fast immer zu einem besseren, kohärenteren Bild als eine Liste mit unzusammenhängenden Wörtern.

Prompts zum Generieren von Bildern
Die folgenden Strategien helfen Ihnen dabei, effektive Prompts zu erstellen, mit denen Sie genau die Bilder generieren können, die Sie suchen.

1. Fotorealistische Szenen
Verwenden Sie fotografische Begriffe, um realistische Bilder zu erstellen. Geben Sie Kamerawinkel, Objektivtypen, Beleuchtung und feine Details an, um das Modell in Richtung eines fotorealistischen Ergebnisses zu lenken.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [
        {"text": "A photorealistic close-up portrait of an elderly Japanese ceramicist with deep, sun-etched wrinkles and a warm, knowing smile. He is carefully inspecting a freshly glazed tea bowl. The setting is his rustic, sun-drenched workshop with pottery wheels and shelves of clay pots in the background. The scene is illuminated by soft, golden hour light streaming through a window, highlighting the fine texture of the clay and the fabric of his apron. Captured with an 85mm portrait lens, resulting in a soft, blurred background (bokeh). The overall mood is serene and masterful."}
      ]
    }]
  }'
Ein fotorealistisches Porträt als Nahaufnahme eines älteren japanischen Keramikers...
Ein fotorealistisches Nahaufnahmeporträt eines älteren japanischen Keramikers…
2. Stilisierte Illustrationen und Sticker
Wenn Sie Sticker, Symbole oder Assets erstellen möchten, geben Sie den Stil genau an und fordern Sie einen transparenten Hintergrund an.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [
        {"text": "A kawaii-style sticker of a happy red panda wearing a tiny bamboo hat. It is munching on a green bamboo leaf. The design features bold, clean outlines, simple cel-shading, and a vibrant color palette. The background must be white."}
      ]
    }]
  }'
Ein Sticker im Kawaii-Stil mit einem fröhlichen roten…
Ein Sticker im Kawaii-Stil mit einem fröhlichen roten Panda...
3. Genaue Darstellung von Text in Bildern
Gemini ist hervorragend im Rendern von Text. Beschreiben Sie den Text, den Schriftstil und das Gesamtdesign so genau wie möglich. Gemini 3 Pro Image Preview für die professionelle Asset-Produktion verwenden

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [
        {"text": "Create a modern, minimalist logo for a coffee shop called The Daily Grind. The text should be in a clean, bold, sans-serif font. The color scheme is black and white. Put the logo in a circle. Use a coffee bean in a clever way."}
      ]
    }],
    "generationConfig": {
      "imageConfig": {
        "aspectRatio": "1:1"
      }
    }
  }'
Erstelle ein modernes, minimalistisches Logo für ein Café namens „The Daily Grind“...
Erstelle ein modernes, minimalistisches Logo für ein Café namens „The Daily Grind“...
4. Produkt-Mockups und kommerzielle Fotografie
Ideal für die Erstellung von sauberen, professionellen Produktaufnahmen für E-Commerce, Werbung oder Branding.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [
        {"text": "A high-resolution, studio-lit product photograph of a minimalist ceramic coffee mug in matte black, presented on a polished concrete surface. The lighting is a three-point softbox setup designed to create soft, diffused highlights and eliminate harsh shadows. The camera angle is a slightly elevated 45-degree shot to showcase its clean lines. Ultra-realistic, with sharp focus on the steam rising from the coffee. Square image."}
      ]
    }]
  }'
Ein hochauflösendes, im Studio aufgenommenes Produktfoto einer minimalistischen Kaffeetasse aus Keramik…
Ein hochauflösendes, im Studio aufgenommenes Produktfoto einer minimalistischen Keramiktasse…
5. Minimalistisches Design und Negativraum
Hervorragend geeignet, um Hintergründe für Websites, Präsentationen oder Marketingmaterialien zu erstellen, auf denen Text eingeblendet werden soll.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [
        {"text": "A minimalist composition featuring a single, delicate red maple leaf positioned in the bottom-right of the frame. The background is a vast, empty off-white canvas, creating significant negative space for text. Soft, diffused lighting from the top left. Square image."}
      ]
    }]
  }'
Eine minimalistische Komposition mit einem einzelnen, zarten roten Ahornblatt…
Eine minimalistische Komposition mit einem einzelnen, zarten roten Ahornblatt...
6. Sequenzielle Kunst (Comic-Panel / Storyboard)
Baut auf der Konsistenz der Charaktere und der Szenenbeschreibung auf, um Panels für das visuelle Storytelling zu erstellen. Für eine hohe Genauigkeit bei Text und Storytelling eignen sich diese Prompts am besten für die Bildvorschau von Gemini 3 Pro.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [
        {"text": "Make a 3 panel comic in a gritty, noir art style with high-contrast black and white inks. Put the character in a humurous scene."},
        {"inline_data": {"mime_type": "image/jpeg", "data": "<BASE64_IMAGE_DATA>"}}
      ]
    }]
  }'
Eingabe

Ausgabe

Mann mit weißer Brille
Eingabebild
Erstelle einen dreiteiligen Comic im düsteren Noir-Stil…
Erstelle einen Comic mit drei Bildern im düsteren Noir-Stil...
7. Fundierung mit der Google Suche
Mit der Google Suche können Sie Bilder auf Grundlage aktueller oder Echtzeitinformationen generieren. Das ist nützlich für Nachrichten, Wetter und andere zeitkritische Themen.

Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "Make a simple but stylish graphic of last nights Arsenal game in the Champions League"}]}],
    "tools": [{"google_search": {}}],
    "generationConfig": {
      "responseModalities": ["TEXT", "IMAGE"],
      "imageConfig": {"aspectRatio": "16:9"}
    }
  }'
KI-generierte Grafik mit dem Ergebnis eines Fußballspiels von Arsenal
KI-generierte Grafik mit dem Ergebnis eines Fußballspiels von Arsenal
Prompts zum Bearbeiten von Bildern
In diesen Beispielen wird gezeigt, wie Sie Bilder zusammen mit Ihren Text-Prompts für die Bearbeitung, Komposition und Stilübertragung bereitstellen.

1. Elemente hinzufügen und entfernen
Stellen Sie ein Bild bereit und beschreiben Sie die Änderung. Das Modell entspricht dem Stil, der Beleuchtung und der Perspektive des Originalbilds.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\":[
            {\"text\": \"Using the provided image of my cat, please add a small, knitted wizard hat on its head. Make it look like it's sitting comfortably and not falling off.\"},
            {
              \"inline_data\": {
                \"mime_type\":\"image/png\",
                \"data\": \"<BASE64_IMAGE_DATA>\"
              }
            }
        ]
      }]
    }"
Eingabe

Ausgabe

Ein fotorealistisches Bild einer flauschigen roten Katze.
Ein fotorealistisches Bild einer flauschigen roten Katze…
Füge dem bereitgestellten Bild meiner Katze einen kleinen, gestrickten Zaubererhut hinzu…
Füge dem bereitgestellten Bild meiner Katze einen kleinen, gestrickten Zaubererhut hinzu…
2. Übermalen (semantische Maskierung)
Sie können eine „Maske“ im Dialog definieren, um einen bestimmten Teil eines Bildes zu bearbeiten, während der Rest unverändert bleibt.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\":[
            {
              \"inline_data\": {
                \"mime_type\":\"image/png\",
                \"data\": \"<BASE64_IMAGE_DATA>\"
              }
            },
            {\"text\": \"Using the provided image of a living room, change only the blue sofa to be a vintage, brown leather chesterfield sofa. Keep the rest of the room, including the pillows on the sofa and the lighting, unchanged.\"}
        ]
      }]
    }"
Eingabe

Ausgabe

Eine Weitwinkelaufnahme eines modernen, gut beleuchteten Wohnzimmers…
Eine Weitwinkelaufnahme eines modernen, gut beleuchteten Wohnzimmers…
Ändere auf dem bereitgestellten Bild eines Wohnzimmers nur das blaue Sofa in ein braunes Chesterfield-Sofa aus Vintage-Leder.
Ändere auf dem bereitgestellten Bild eines Wohnzimmers nur das blaue Sofa in ein braunes Chesterfield-Sofa aus Leder im Vintage-Stil…
3. Stilübertragung
Stellen Sie ein Bild zur Verfügung und bitten Sie das Modell, den Inhalt in einem anderen künstlerischen Stil neu zu erstellen.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\":[
            {
              \"inline_data\": {
                \"mime_type\":\"image/png\",
                \"data\": \"<BASE64_IMAGE_DATA>\"
              }
            },
            {\"text\": \"Transform the provided photograph of a modern city street at night into the artistic style of Vincent van Gogh's 'Starry Night'. Preserve the original composition of buildings and cars, but render all elements with swirling, impasto brushstrokes and a dramatic palette of deep blues and bright yellows.\"}
        ]
      }]
    }"
Eingabe

Ausgabe

Ein fotorealistisches Foto einer belebten Straße in hoher Auflösung…
Ein fotorealistisches, hochauflösendes Foto einer belebten Straße in einer Stadt...
Verwandle das bereitgestellte Foto einer modernen Stadtstraße bei Nacht…
Wandle das bereitgestellte Foto einer modernen Stadtstraße bei Nacht um…
4. Erweiterte Komposition: Mehrere Bilder kombinieren
Stellen Sie mehrere Bilder als Kontext bereit, um eine neue, zusammengesetzte Szene zu erstellen. Das ist ideal für Produkt-Mockups oder kreative Collagen.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\":[
            {
              \"inline_data\": {
                \"mime_type\":\"image/png\",
                \"data\": \"<BASE64_IMAGE_DATA_1>\"
              }
            },
            {
              \"inline_data\": {
                \"mime_type\":\"image/png\",
                \"data\": \"<BASE64_IMAGE_DATA_2>\"
              }
            },
            {\"text\": \"Create a professional e-commerce fashion photo. Take the blue floral dress from the first image and let the woman from the second image wear it. Generate a realistic, full-body shot of the woman wearing the dress, with the lighting and shadows adjusted to match the outdoor environment.\"}
        ]
      }]
    }"
Eingabe 1

Eingabe 2

Ausgabe

Ein professionell aufgenommenes Foto eines blauen Sommerkleids mit Blumenmuster…
Ein professionell aufgenommenes Foto eines blauen Sommerkleids mit Blumenmuster…
Ganzkörperaufnahme einer Frau mit einem Dutt…
Ganzkörperaufnahme einer Frau mit einem Dutt…
Erstelle ein professionelles E‑Commerce-Modefoto…
Erstelle ein professionelles E‑Commerce-Foto von Mode…
5. High-Fidelity-Detailwiedergabe
Damit wichtige Details wie ein Gesicht oder ein Logo bei der Bearbeitung erhalten bleiben, beschreiben Sie sie zusammen mit Ihrem Bearbeitungswunsch sehr detailliert.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\":[
            {
              \"inline_data\": {
                \"mime_type\":\"image/png\",
                \"data\": \"<BASE64_IMAGE_DATA_1>\"
              }
            },
            {
              \"inline_data\": {
                \"mime_type\":\"image/png\",
                \"data\": \"<BASE64_IMAGE_DATA_2>\"
              }
            },
            {\"text\": \"Take the first image of the woman with brown hair, blue eyes, and a neutral expression. Add the logo from the second image onto her black t-shirt. Ensure the woman's face and features remain completely unchanged. The logo should look like it's naturally printed on the fabric, following the folds of the shirt.\"}
        ]
      }]
    }"
Eingabe 1

Eingabe 2

Ausgabe

Ein professionelles Porträt einer Frau mit braunen Haaren und blauen Augen…
Ein professionelles Porträt einer Frau mit braunen Haaren und blauen Augen...
Ein einfaches, modernes Logo mit den Buchstaben „G“ und „A“...
Ein einfaches, modernes Logo mit den Buchstaben „G“ und „A“...
Nimm das erste Bild der Frau mit braunen Haaren, blauen Augen und einem neutralen Gesichtsausdruck…
Nimm das erste Bild der Frau mit braunen Haaren, blauen Augen und einem neutralen Gesichtsausdruck...
6. Etwas zum Leben erwecken
Laden Sie eine grobe Skizze oder Zeichnung hoch und bitten Sie das Modell, sie in ein fertiges Bild umzuwandeln.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\":[
            {
              \"inline_data\": {
                \"mime_type\":\"image/png\",
                \"data\": \"<BASE64_IMAGE_DATA>\"
              }
            },
            {\"text\": \"Turn this rough pencil sketch of a futuristic car into a polished photo of the finished concept car in a showroom. Keep the sleek lines and low profile from the sketch but add metallic blue paint and neon rim lighting.\"}
        ]
      }]
    }"
Eingabe

Ausgabe

Skizze eines Autos
Grobe Skizze eines Autos
Ausgabe mit dem endgültigen Konzeptfahrzeug
Polierte Aufnahme eines Autos
7. Charaktere mit Wiedererkennungswert: 360°-Ansicht
Sie können 360‑Grad-Ansichten eines Charakters generieren, indem Sie iterativ nach verschiedenen Blickwinkeln fragen. Die besten Ergebnisse erzielen Sie, wenn Sie zuvor generierte Bilder in nachfolgende Prompts einfügen, um die Konsistenz zu wahren. Bei komplexen Posen sollten Sie ein Referenzbild der gewünschten Pose einfügen.

Vorlage
Prompt
Python
Java
JavaScript
Ok
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\":[
            {\"text\": \"A studio portrait of this man against white, in profile looking right\"},
            {
              \"inline_data\": {
                \"mime_type\":\"image/jpeg\",
                \"data\": \"<BASE64_IMAGE_DATA>\"
              }
            }
        ]
      }]
    }"
Eingabe

Ausgabe 1

Ausgabe 2

Originaleingabe eines Mannes mit weißer Brille
Originalbild
Ausgabe eines Mannes mit weißer Brille, der nach rechts blickt
Mann mit weißer Brille blickt nach rechts
Ausgabe eines Mannes mit weißer Brille, der nach vorn schaut
Mann mit weißer Brille blickt nach vorn
Best Practices
Mit diesen professionellen Strategien können Sie Ihre Ergebnisse von gut zu sehr gut verbessern.

Seien Sie sehr spezifisch:Je mehr Details Sie angeben, desto mehr Kontrolle haben Sie. Beschreiben Sie die Rüstung, anstatt nur „Fantasy-Rüstung“ zu schreiben: „aufwendige elfenhafte Plattenrüstung, mit silbernen Blattmustern geätzt, mit hohem Kragen und Schulterstücken in Form von Falkenflügeln“.
Kontext und Intention angeben:Erläutern Sie den Zweck des Bildes. Das Kontextverständnis des Modells beeinflusst die endgültige Ausgabe. Ein Beispiel: „Erstelle ein Logo für eine hochwertige, minimalistische Hautpflege-Marke“ liefert bessere Ergebnisse als „Erstelle ein Logo“.
Wiederholen und verfeinern:Erwarten Sie nicht, dass Sie beim ersten Versuch ein perfektes Bild erhalten. Nutzen Sie die Konversationsfunktion des Modells, um kleine Änderungen vorzunehmen. Verwende Folge-Prompts wie „Das ist toll, aber kannst du die Beleuchtung etwas wärmer gestalten?“ oder „Lass alles so, aber ändere den Gesichtsausdruck der Figur zu einem ernsteren.“
Schritt-für-Schritt-Anleitung verwenden:Bei komplexen Szenen mit vielen Elementen sollten Sie Ihren Prompt in Schritte unterteilen. „Erstelle zuerst einen Hintergrund mit einem ruhigen, nebligen Wald bei Sonnenaufgang. Fügen Sie dann im Vordergrund einen moosbewachsenen alten Steinaltar hinzu. Stelle schließlich ein einzelnes, leuchtendes Schwert auf den Altar.“
Semantische negative Prompts verwenden: Anstatt „keine Autos“ zu sagen, beschreiben Sie die gewünschte Szene positiv: „eine leere, verlassene Straße ohne Anzeichen von Verkehr“.
Kamera steuern:Verwenden Sie fotografische und filmische Sprache, um die Komposition zu steuern. Begriffe wie wide-angle shot, macro shot, low-angle perspective.
Beschränkungen
Die beste Leistung erzielen Sie, wenn Sie die folgenden Sprachen verwenden: DE, EN, ar-EG, es-MX, fr-FR, hi-IN, id-ID, it-IT, ja-JP, ko-KR, pt-BR, ru-RU, ua-UA, vi-VN, zh-CN.
Bei der Bildgenerierung werden keine Audio- oder Videoeingaben unterstützt.
Das Modell gibt nicht immer genau die Anzahl an Bildern aus, die der Nutzer explizit anfordert.
gemini-2.5-flash-image funktioniert am besten mit bis zu 3 Eingabebildern, während gemini-3-pro-image-preview bis zu 5 Bilder mit hoher Qualität und insgesamt bis zu 14 Bilder unterstützt.
Wenn Sie Text für ein Bild generieren, funktioniert Gemini am besten, wenn Sie zuerst den Text generieren und dann ein Bild mit dem Text anfordern.
Alle generierten Bilder enthalten ein SynthID-Wasserzeichen.
Optionale Konfigurationen
Optional können Sie die Antwortmodalitäten und das Seitenverhältnis der Modellausgabe im Feld config von generate_content-Aufrufen konfigurieren.

Ausgabetypen
Standardmäßig gibt das Modell Text- und Bildantworten zurück (d.h. response_modalities=['Text', 'Image']). Sie können die Antwort so konfigurieren, dass nur Bilder ohne Text zurückgegeben werden, indem Sie response_modalities=['Image'] verwenden.

Python
JavaScript
Ok
Java
REST

curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [
        {"text": "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"}
      ]
    }],
    "generationConfig": {
      "responseModalities": ["Image"]
    }
  }'
Seitenverhältnisse und Bildgröße
Standardmäßig wird die Größe des Ausgabebilds an die Größe des Eingabebilds angepasst. Andernfalls werden quadratische Bilder mit einem Seitenverhältnis von 1:1 generiert. Sie können das Seitenverhältnis des Ausgabebilds mit dem Feld aspect_ratio unter image_config in der Antwortanfrage steuern, wie hier gezeigt:

Python
JavaScript
Ok
Java
REST

# For gemini-2.5-flash-image
curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{
      "parts": [
        {"text": "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"}
      ]
    }],
    "generationConfig": {
      "imageConfig": {
        "aspectRatio": "16:9"
      }
    }
  }'

# For gemini-3-pro-image-preview
curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{
      "parts": [
        {"text": "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"}
      ]
    }],
    "generationConfig": {
      "imageConfig": {
        "aspectRatio": "16:9",
        "imageSize": "2K"
      }
    }
  }'
Die verschiedenen verfügbaren Seitenverhältnisse und die Größe des generierten Bildes sind in den folgenden Tabellen aufgeführt:

Gemini 2.5 Flash Image

Seitenverhältnis	Auflösung	Tokens
1:1	1024x1024	1290
2:3	832 × 1248	1290
3:2	1248 × 832	1290
3:4	864 × 1184	1290
4:3	1184 × 864	1290
4:5	896 × 1152	1290
5:4	1152 × 896	1290
9:16	768 × 1344	1290
16:9	1344 × 768	1290
21:9	1536 × 672	1290
Gemini 3 Pro Image Preview

Seitenverhältnis	1K-Auflösung	1.000 Tokens	2K-Auflösung	2.000 Tokens	4K-Auflösung	4K-Tokens
1:1	1024x1024	1.120	2.048 x 2.048	1.120	4096 x 4096	2000
2:3	848 × 1264	1.120	1696 × 2528	1.120	3392 × 5056	2000
3:2	1264 × 848	1.120	2528 × 1696	1.120	5056 × 3392	2000
3:4	896 × 1200	1.120	1792 × 2400	1.120	3584 × 4800	2000
4:3	1200 × 896	1.120	2400 × 1792	1.120	4800 × 3584	2000
4:5	928 × 1152	1.120	1856 × 2304	1.120	3712 × 4608	2000
5:4	1152 × 928	1.120	2304 × 1856	1.120	4608 × 3712	2000
9:16	768 × 1376	1.120	1536 × 2752	1.120	3072 × 5504	2000
16:9	1376 × 768	1.120	2752 × 1536	1.120	5504 × 3072	2000
21:9	1584 × 672	1.120	3168 × 1344	1.120	6336 × 2688	2000
Modellauswahl
Wählen Sie das Modell aus, das am besten für Ihren speziellen Anwendungsfall geeignet ist.

Gemini 3 Pro Image Preview (Nano Banana Pro Preview) wurde für die professionelle Asset-Produktion und komplexe Anweisungen entwickelt. Dieses Modell bietet eine Verankerung in der realen Welt durch Google Suche, einen standardmäßigen „Denkprozess“, der die Komposition vor der Generierung verfeinert, und kann Bilder mit einer Auflösung von bis zu 4K generieren. Weitere Informationen finden Sie auf der Seite Modellpreise und ‑funktionen.

Gemini 2.5 Flash Image (Nano Banana) wurde für Geschwindigkeit und Effizienz entwickelt. Dieses Modell ist für Aufgaben mit hohem Volumen und niedriger Latenz optimiert und generiert Bilder mit einer Auflösung von 1.024 Pixeln. Weitere Informationen finden Sie auf der Seite Modellpreise und ‑funktionen.

Wann sollte Imagen verwendet werden?
Zusätzlich zu den integrierten Funktionen von Gemini zur Bildgenerierung können Sie über die Gemini API auch auf Imagen zugreifen, unser spezialisiertes Modell zur Bildgenerierung.

Imagen 4 ist das Modell, das Sie verwenden sollten, wenn Sie mit der Bildgenerierung mit Imagen beginnen. Wählen Sie Imagen 4 Ultra für erweiterte Anwendungsfälle oder wenn Sie die beste Bildqualität benötigen. Beachten Sie, dass jeweils nur ein Bild generiert werden kann.

Nano Banana (Bildgenerierung)

Nano Banana ist der Name für die nativen Bildgenerierungsfunktionen von Gemini. Derzeit bezieht sich der Begriff auf zwei verschiedene Modelle, die in der Gemini API verfügbar sind:

Nano Banana: Das Modell Gemini 2.5 Flash Image (gemini-2.5-flash-image). Dieses Modell ist auf Geschwindigkeit und Effizienz ausgelegt und für Aufgaben mit hohem Volumen und geringer Latenz optimiert.
Nano Banana Pro: Das Modell Gemini 3 Pro Image Preview (gemini-3-pro-image-preview). Dieses Modell wurde für die professionelle Asset-Produktion entwickelt. Es nutzt fortschrittliche Schlussfolgerungen („Thinking“), um komplexe Anweisungen zu befolgen und Text in hoher Qualität zu rendern.

Unser natives Modell für die Bildgenerierung, das für Geschwindigkeit, Flexibilität und Kontextverständnis optimiert ist. Texteingabe und -ausgabe kosten dasselbe wie Gemini 3 Pro.

Vorschaumodelle können sich ändern, bevor sie stabil werden, und haben restriktivere Ratenlimits.

Standard
Batch
Kostenlose Stufe	Kostenpflichtige Stufe, pro 1 Million Tokens in USD
Eingabepreis	Nicht verfügbar	2,00 $ (Text/Bild),
entspricht 0,0011 $pro Bild*
Ausgabepreis	Nicht verfügbar	12,00 $ (Text und Denken)
120,00 $ (Bilder)
entspricht 0,134 $pro 1K-/2K-Bild**
und 0,24 $pro 4K-Bild**
Zur Verbesserung unserer Produkte	Ja	Nein
* Die Bildeingabe ist auf 560 Tokens oder 0,0011 $pro Bild festgelegt.

** Die Bildausgabe wird mit 120 $pro 1.000.000 Tokens berechnet. Für Ausgabebilder mit einer Größe von 1024 × 1024 Pixel (1K) bis 2048 × 2048 Pixel (2K) werden 1120 Tokens verwendet, was 0,134 $pro Bild entspricht. Ausgabebilder mit einer Größe von bis zu 4096 × 4096 Pixeln (4K) verbrauchen 2.000 Tokens und entsprechen 0,24 $pro Bild.

Unser natives Modell für die Bildgenerierung, das für Geschwindigkeit, Flexibilität und Kontextverständnis optimiert ist. Die Preise für Texteingabe und -ausgabe entsprechen denen von 2.5 Flash.

Vorschaumodelle können sich ändern, bevor sie stabil werden, und haben restriktivere Ratenlimits.

Standard
Batch
Kostenlose Stufe	Kostenpflichtige Stufe, pro 1 Million Tokens in USD
Eingabepreis	Nicht verfügbar	0,30 $ (Text / Bild)
Ausgabepreis	Nicht verfügbar	0,039 $ pro Bild*
Zur Verbesserung unserer Produkte	Ja	Nein
[*] Die Bildausgabe kostet 30 $pro 1.000.000 Tokens. Ausgabebilder mit einer Größe von bis zu 1.024 × 1.024 Pixel verbrauchen 1.290 Tokens und kosten 0,039 $pro Bild.
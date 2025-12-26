Bilder mit Gemini generieren (auch als Nano Banana bezeichnet)


Gemini kann Bilder im Rahmen von Unterhaltungen generieren und verarbeiten. Sie können Gemini mit Text, Bildern oder einer Kombination aus beidem auffordern, um Bilder mit beispielloser Kontrolle zu erstellen, zu bearbeiten und zu optimieren:

Text-to-Image::Generieren Sie hochwertige Bilder aus einfachen oder komplexen Textbeschreibungen.
Bild + Text-zu-Bild (Bearbeitung): Sie stellen ein Bild bereit und verwenden Text-Prompts, um Elemente hinzuzufügen, zu entfernen oder zu ändern, den Stil zu ändern oder die Farbkorrektur anzupassen.
Mehrere Bilder zu einem Bild (Komposition und Stilübertragung): Verwenden Sie mehrere Eingabebilder, um eine neue Szene zu erstellen oder den Stil eines Bildes auf ein anderes zu übertragen.
Iterative Optimierung:Sie können sich mit dem KI-Modell unterhalten, um Ihr Bild schrittweise zu optimieren. Dabei werden in mehreren Schritten kleine Anpassungen vorgenommen, bis das Bild perfekt ist.
Textwiedergabe in hoher Qualität:Bilder mit gut lesbarem und gut platziertem Text werden präzise generiert. Das ist ideal für Logos, Diagramme und Poster.
Alle generierten Bilder enthalten ein SynthID-Wasserzeichen.

Bildgenerierung (Text-zu-Bild)
Der folgende Code zeigt, wie ein Bild auf Grundlage eines beschreibenden Prompts generiert wird.

Python
JavaScript
Ok
REST

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client()

prompt = (
    "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"
)

response = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=[prompt],
)

for part in response.candidates[0].content.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = Image.open(BytesIO(part.inline_data.data))
        image.save("generated_image.png")
KI-generiertes Bild eines Gerichts mit Nanobananen
KI-generiertes Bild eines Gerichts mit Nanobananen in einem Restaurant mit Gemini-Thema
Bildbearbeitung (Text-und-Bild-zu-Bild)
Zur Erinnerung: Sie müssen die erforderlichen Rechte an den Bildern haben, die Sie hochladen möchten. Erstellen Sie keine Inhalte, durch die die Rechte anderer verletzt werden, einschließlich Videos oder Bilder, die jemanden täuschen, belästigen oder schädigen können. Ihre Verwendung dieses auf generativer KI basierenden Dienstes unterliegt unserer Richtlinie zur unzulässigen Nutzung.

Im folgenden Beispiel wird das Hochladen von base64-codierten Bildern veranschaulicht. Informationen zu mehreren Bildern, größeren Nutzlasten und unterstützten MIME-Typen finden Sie auf der Seite Bildanalyse.

Python
JavaScript
Ok
REST

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client()

prompt = (
    "Create a picture of my cat eating a nano-banana in a "
    "fancy restaurant under the Gemini constellation",
)

image = Image.open("/path/to/cat_image.png")

response = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=[prompt, image],
)

for part in response.candidates[0].content.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = Image.open(BytesIO(part.inline_data.data))
        image.save("generated_image.png")
KI-generiertes Bild einer Katze, die eine Anano-Banane isst
KI-generiertes Bild einer Katze, die eine Nanobananen isst
Andere Modi zur Bildgenerierung
Gemini unterstützt je nach Prompt-Struktur und Kontext auch andere Modi für die Bildinteraktion:

Text zu Bild(ern) und Text (verschachtelt): Es werden Bilder mit zugehörigem Text ausgegeben.
Beispiel-Prompt: „Erstelle ein illustriertes Rezept für eine Paella.“
Bild(er) und Text zu Bild(ern) und Text (verschachtelt): Verwendet Eingabebilder und ‑text, um neue zugehörige Bilder und Texte zu erstellen.
Beispielprompt: (Mit einem Bild eines möblierten Zimmers) „Welche anderen Farben für Sofas würden in meinem Raum passen? Kannst du das Bild aktualisieren?“
Multi-Turn-Bildbearbeitung (Chat): Sie können Bilder im Chat generieren und bearbeiten lassen.
Beispiel-Prompts: [Lade ein Bild eines blauen Autos hoch.] , „Mach aus diesem Auto ein Cabriolet.“ „Ändere die Farbe jetzt in Gelb.“
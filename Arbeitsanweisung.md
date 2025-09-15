Bildverständnis

Gemini-Modelle sind von Grund auf multimodal konzipiert und ermöglichen eine Vielzahl von Bildverarbeitungs- und Computer Vision-Aufgaben, darunter Bilduntertitelung, ‑klassifizierung und Visual Question Answering, ohne dass spezielle ML-Modelle trainiert werden müssen.

Tipp :Gemini-Modelle (2.0 und höher) bieten neben ihren allgemeinen multimodalen Funktionen durch zusätzliches Training eine höhere Genauigkeit für bestimmte Anwendungsfälle wie Objekterkennung und Segmentierung. Weitere Informationen finden Sie im Abschnitt Funktionen.
Bilder an Gemini übergeben
Sie haben zwei Möglichkeiten, Bilder als Eingabe für Gemini bereitzustellen:

Inline-Bilddaten übergeben: Ideal für kleinere Dateien (Gesamtanfragegröße unter 20 MB, einschließlich Prompts).
Bilder mit der File API hochladen: Empfohlen für größere Dateien oder wenn Bilder in mehreren Anfragen wiederverwendet werden sollen.
Inline-Bilddaten übergeben
Sie können Inline-Bilddaten im Request an generateContent übergeben. Sie können Bilddaten als Base64-codierte Strings bereitstellen oder lokale Dateien direkt lesen (je nach Sprache).

Im folgenden Beispiel wird gezeigt, wie ein Bild aus einer lokalen Datei gelesen und zur Verarbeitung an die generateContent API übergeben wird.

Python
JavaScript
Ok
REST

  from google.genai import types

  with open('path/to/small-sample.jpg', 'rb') as f:
      image_bytes = f.read()

  response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[
      types.Part.from_bytes(
        data=image_bytes,
        mime_type='image/jpeg',
      ),
      'Caption this image.'
    ]
  )

  print(response.text)
Sie können auch ein Bild von einer URL abrufen, es in Byte konvertieren und an generateContent übergeben, wie in den folgenden Beispielen gezeigt.

Python
JavaScript
Ok
REST

from google import genai
from google.genai import types

import requests

image_path = "https://goo.gle/instrument-img"
image_bytes = requests.get(image_path).content
image = types.Part.from_bytes(
  data=image_bytes, mime_type="image/jpeg"
)

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=["What is this image?", image],
)

print(response.text)
Hinweis: Durch Inline-Bilddaten wird die Gesamtgröße der Anfrage (Text-Prompts, Systemanweisungen und Inline-Bytes) auf 20 MB begrenzt. Bei größeren Anfragen laden Sie Bilddateien mit der File API hoch. Die Files API ist auch effizienter für Szenarien, in denen dasselbe Bild wiederholt verwendet wird.
Bilder mit der File API hochladen
Verwenden Sie für große Dateien oder um dieselbe Bilddatei wiederholt verwenden zu können, die Files API. Mit dem folgenden Code wird eine Bilddatei hochgeladen und dann in einem Aufruf von generateContent verwendet. Weitere Informationen und Beispiele finden Sie im Leitfaden zur Files API.

Python
JavaScript
Ok
REST

from google import genai

client = genai.Client()

my_file = client.files.upload(file="path/to/sample.jpg")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[my_file, "Caption this image."],
)

print(response.text)
Prompts mit mehreren Bildern erstellen
Sie können in einem einzelnen Prompt mehrere Bilder angeben, indem Sie mehrere Part-Objekte für Bilder in das contents-Array einfügen. Dabei kann es sich um eine Mischung aus Inline-Daten (lokale Dateien oder URLs) und File API-Referenzen handeln.

Python
JavaScript
Ok
REST

from google import genai
from google.genai import types

client = genai.Client()

# Upload the first image
image1_path = "path/to/image1.jpg"
uploaded_file = client.files.upload(file=image1_path)

# Prepare the second image as inline data
image2_path = "path/to/image2.png"
with open(image2_path, 'rb') as f:
    img2_bytes = f.read()

# Create the prompt with text and multiple images
response = client.models.generate_content(

    model="gemini-2.5-flash",
    contents=[
        "What is different between these two images?",
        uploaded_file,  # Use the uploaded file reference
        types.Part.from_bytes(
            data=img2_bytes,
            mime_type='image/png'
        )
    ]
)

print(response.text)
Objekterkennung
Ab Gemini 2.0 werden Modelle weiter trainiert, um Objekte in einem Bild zu erkennen und die Koordinaten ihrer Begrenzungsrahmen zu ermitteln. Die Koordinaten werden relativ zu den Bilddimensionen auf [0, 1000] skaliert. Sie müssen diese Koordinaten anhand der Originalbildgröße herunterskalieren.

Python

from google import genai
from google.genai import types
from PIL import Image
import json

client = genai.Client()
prompt = "Detect the all of the prominent items in the image. The box_2d should be [ymin, xmin, ymax, xmax] normalized to 0-1000."

image = Image.open("/path/to/image.png")

config = types.GenerateContentConfig(
  response_mime_type="application/json"
  )

response = client.models.generate_content(model="gemini-2.5-flash",
                                          contents=[image, prompt],
                                          config=config
                                          )

width, height = image.size
bounding_boxes = json.loads(response.text)

converted_bounding_boxes = []
for bounding_box in bounding_boxes:
    abs_y1 = int(bounding_box["box_2d"][0]/1000 * height)
    abs_x1 = int(bounding_box["box_2d"][1]/1000 * width)
    abs_y2 = int(bounding_box["box_2d"][2]/1000 * height)
    abs_x2 = int(bounding_box["box_2d"][3]/1000 * width)
    converted_bounding_boxes.append([abs_x1, abs_y1, abs_x2, abs_y2])

print("Image size: ", width, height)
print("Bounding boxes:", converted_bounding_boxes)

Hinweis : Das Modell unterstützt auch das Generieren von Begrenzungsrahmen basierend auf benutzerdefinierten Anweisungen wie „Zeige Begrenzungsrahmen aller grünen Objekte in diesem Bild“. Außerdem werden benutzerdefinierte Labels wie „Kennzeichne die Artikel mit den Allergenen, die sie enthalten können“ unterstützt.
Weitere Beispiele finden Sie in den folgenden Notebooks im Gemini Cookbook:

Notebook zum räumlichen 2D-Verständnis
Experimentelles 3D-Zeigegerät für Notebooks
Segmentierung
Ab Gemini 2.5 können Modelle Elemente nicht nur erkennen, sondern auch segmentieren und ihre Konturmasken bereitstellen.

Das Modell sagt eine JSON-Liste voraus, wobei jedes Element eine Segmentierungsmaske darstellt. Jedes Element hat einen Begrenzungsrahmen („box_2d“) im Format [y0, x0, y1, x1] mit normalisierten Koordinaten zwischen 0 und 1000, ein Label („label“), das das Objekt identifiziert, und schließlich die Segmentierungsmaske innerhalb des Begrenzungsrahmens als Base64-codiertes PNG, das eine Wahrscheinlichkeitskarte mit Werten zwischen 0 und 255 ist. Die Maske muss an die Abmessungen des umgebenden Rechtecks angepasst und dann mit dem von Ihnen festgelegten Konfidenzwert (127 für den Mittelpunkt) binarisiert werden.

Hinweis :Wenn Sie das Thinking-Budget auf 0 setzen, lassen sich bessere Ergebnisse erzielen. Ein Beispiel finden Sie im Codebeispiel unten.
Python

from google import genai
from google.genai import types
from PIL import Image, ImageDraw
import io
import base64
import json
import numpy as np
import os

client = genai.Client()

def parse_json(json_output: str):
  # Parsing out the markdown fencing
  lines = json_output.splitlines()
  for i, line in enumerate(lines):
    if line == "```json":
      json_output = "\n".join(lines[i+1:])  # Remove everything before "```json"
      output = json_output.split("```")[0]  # Remove everything after the closing "```"
      break  # Exit the loop once "```json" is found
  return json_output

def extract_segmentation_masks(image_path: str, output_dir: str = "segmentation_outputs"):
  # Load and resize image
  im = Image.open(image_path)
  im.thumbnail([1024, 1024], Image.Resampling.LANCZOS)

  prompt = """
  Give the segmentation masks for the wooden and glass items.
  Output a JSON list of segmentation masks where each entry contains the 2D
  bounding box in the key "box_2d", the segmentation mask in key "mask", and
  the text label in the key "label". Use descriptive labels.
  """

  config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0) # set thinking_budget to 0 for better results in object detection
  )

  response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[prompt, im], # Pillow images can be directly passed as inputs (which will be converted by the SDK)
    config=config
  )

  # Parse JSON response
  items = json.loads(parse_json(response.text))

  # Create output directory
  os.makedirs(output_dir, exist_ok=True)

  # Process each mask
  for i, item in enumerate(items):
      # Get bounding box coordinates
      box = item["box_2d"]
      y0 = int(box[0] / 1000 * im.size[1])
      x0 = int(box[1] / 1000 * im.size[0])
      y1 = int(box[2] / 1000 * im.size[1])
      x1 = int(box[3] / 1000 * im.size[0])

      # Skip invalid boxes
      if y0 >= y1 or x0 >= x1:
          continue

      # Process mask
      png_str = item["mask"]
      if not png_str.startswith("data:image/png;base64,"):
          continue

      # Remove prefix
      png_str = png_str.removeprefix("data:image/png;base64,")
      mask_data = base64.b64decode(png_str)
      mask = Image.open(io.BytesIO(mask_data))

      # Resize mask to match bounding box
      mask = mask.resize((x1 - x0, y1 - y0), Image.Resampling.BILINEAR)

      # Convert mask to numpy array for processing
      mask_array = np.array(mask)

      # Create overlay for this mask
      overlay = Image.new('RGBA', im.size, (0, 0, 0, 0))
      overlay_draw = ImageDraw.Draw(overlay)

      # Create overlay for the mask
      color = (255, 255, 255, 200)
      for y in range(y0, y1):
          for x in range(x0, x1):
              if mask_array[y - y0, x - x0] > 128:  # Threshold for mask
                  overlay_draw.point((x, y), fill=color)

      # Save individual mask and its overlay
      mask_filename = f"{item['label']}_{i}_mask.png"
      overlay_filename = f"{item['label']}_{i}_overlay.png"

      mask.save(os.path.join(output_dir, mask_filename))

      # Create and save overlay
      composite = Image.alpha_composite(im.convert('RGBA'), overlay)
      composite.save(os.path.join(output_dir, overlay_filename))
      print(f"Saved mask and overlay for {item['label']} to {output_dir}")

# Example usage
if __name__ == "__main__":
  extract_segmentation_masks("path/to/image.png")

Ein detaillierteres Beispiel finden Sie im Segmentierungsbeispiel im Cookbook-Leitfaden.

Ein Tisch mit Cupcakes, auf dem die Holz- und Glasobjekte hervorgehoben sind
Beispiel für eine Segmentierungsausgabe mit Objekten und Segmentierungsmasken
Unterstützte Bildformate
Gemini unterstützt die folgenden MIME-Typen für Bildformate:

PNG - image/png
JPEG - image/jpeg
WEBP - image/webp
HEIC – image/heic
HEIF - image/heif
Leistungsspektrum
Alle Gemini-Modellversionen sind multimodal und können für eine Vielzahl von Bildverarbeitungs- und Computer Vision-Aufgaben verwendet werden, einschließlich, aber nicht beschränkt auf Bilduntertitelung, Visual Question Answering, Bildklassifizierung, Objekterkennung und Segmentierung.

Je nach Ihren Qualitäts- und Leistungsanforderungen kann Gemini die Notwendigkeit reduzieren, spezielle ML-Modelle zu verwenden.

Einige spätere Modellversionen werden speziell darauf trainiert, die Genauigkeit von spezialisierten Aufgaben zusätzlich zu den allgemeinen Funktionen zu verbessern:

Gemini 2.0-Modelle werden weiter trainiert, um eine verbesserte Objekterkennung zu unterstützen.

Gemini 2.5-Modelle werden zusätzlich trainiert, um neben der Objekterkennung auch eine verbesserte Segmentierung zu unterstützen.

Einschränkungen und wichtige technische Informationen
Dateilimit
Gemini 2.5 Pro/Flash, 2.0 Flash, 1.5 Pro und 1.5 Flash unterstützen maximal 3.600 Bilddateien pro Anfrage.

Tokenberechnung
Gemini 1.5 Flash und Gemini 1.5 Pro: 258 Tokens, wenn beide Dimensionen kleiner oder gleich 384 Pixel sind. Größere Bilder werden gekachelt (mind. 256 Pixel, max. 768 Pixel, auf 768 × 768 Pixel skaliert). Jede Kachel kostet 258 Tokens.
Gemini 2.0 Flash und Gemini 2.5 Flash/Pro: 258 Tokens, wenn beide Dimensionen kleiner oder gleich 384 Pixel sind. Größere Bilder werden in Kacheln mit 768 × 768 Pixeln aufgeteilt, die jeweils 258 Tokens kosten.
Tipps und Best Practices
Prüfen Sie, ob die Bilder richtig gedreht sind.
Verwenden Sie klare, nicht verschwommene Bilder.
Wenn Sie ein einzelnes Bild mit Text verwenden, platzieren Sie den Text-Prompt nach dem Bildteil im contents-Array.
Nächste Schritte
In diesem Leitfaden erfahren Sie, wie Sie Bilddateien hochladen und Textausgaben aus Bildeingaben generieren. Weitere Informationen finden Sie in den folgenden Ressourcen:

Files API: Hier finden Sie weitere Informationen zum Hochladen und Verwalten von Dateien für die Verwendung mit Gemini.
Systemanweisungen: Mit Systemanweisungen können Sie das Verhalten des Modells entsprechend Ihren spezifischen Anforderungen und Anwendungsfällen steuern.
Strategien für Dateiprompts: Die Gemini API unterstützt Prompts mit Text-, Bild-, Audio- und Videodaten, auch bekannt als multimodale Prompts.
Sicherheitshinweise: Generative KI-Modelle können manchmal unerwartete Ausgaben liefern, z. B. ungenaue, voreingenommene oder anstößige Ausgaben. Die Nachbearbeitung und menschliche Bewertung sind unerlässlich, um das Risiko von Schäden durch solche Ausgaben zu begrenzen.
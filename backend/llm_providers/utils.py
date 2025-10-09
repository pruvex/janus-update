import re


def _extract_image_description(prompt: str) -> str:
    cleaned_prompt = prompt.lower()
    prefixes = [
        "gemini:",
        "gpt:",
        "mache ein bild von",
        "erstelle ein bild von",
        "generiere ein bild von",
        "make an image of",
        "generate an image of",
        "create an image of",
        "zeig mir bild von",
        "zeig mir ein bild von",
        "zeige mir bild von",
        "zeige mir ein bild von",
        "zeichne",
        "mache",
        "erstelle",
    ]
    for prefix in prefixes:
        if cleaned_prompt.startswith(prefix):
            cleaned_prompt = cleaned_prompt[len(prefix) :].strip()
    cleaned_prompt = cleaned_prompt.replace(" ", "-")
    cleaned_prompt = re.sub(r"[^a-z0-9-]", "", cleaned_prompt)
    cleaned_prompt = re.sub(r"-+", "-", cleaned_prompt).strip("-")
    return cleaned_prompt

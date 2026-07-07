import re

def normalize_heading(text: str) -> str:
    cleaned = text.strip().lower()
    return cleaned.title()

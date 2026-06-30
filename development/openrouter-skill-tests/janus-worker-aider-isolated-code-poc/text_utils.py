def normalize_heading(text: str) -> str:
    cleaned = text.strip().lower()
    return ' '.join(word.capitalize() for word in cleaned.split())

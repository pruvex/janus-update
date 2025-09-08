# backend/websearch.py
from typing import Any

def perform_websearch(query: str) -> dict:
    # GPT hat schon ein eingebautes web.search Tool
    # D.h. du leitest die Anfrage nur an GPT weiter
    return {
        "tool": "web.search",
        "arguments": {"query": query}
    }

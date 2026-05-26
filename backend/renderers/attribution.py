from __future__ import annotations

from typing import Optional


def weather_source_label(source: Optional[str]) -> str:
    raw = str(source or "").strip().lower()
    if not raw:
        return ""
    labels = {
        "open-meteo": "Open-Meteo",
        "open_meteo": "Open-Meteo",
        "met.no": "MET Norway (met.no)",
        "wttr.in": "wttr.in",
    }
    return labels.get(raw, source or "")


def append_quelle_line(text: str, source_label: Optional[str]) -> str:
    base = str(text or "").strip()
    source = str(source_label or "").strip()
    if not source:
        return base
    return f"{base}\n\nQuelle: {source}"

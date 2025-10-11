# -*- coding: utf-8 -*-
"""
'Gold Standard' German TTS pre-normalizer v5.2 (Final Verified)
This version uses a strict, multi-pass approach and a foolproof currency method.
"""

from __future__ import annotations
import logging
import re
from num2words import num2words

logger = logging.getLogger("janus_backend")

# --- Konfiguration und Konstanten ---
_MONTHS_MAP = {
    "januar": "Januar", "februar": "Februar", "märz": "März", "maerz": "März", "april": "April",
    "mai": "Mai", "juni": "Juni", "juli": "Juli", "august": "August", "september": "September",
    "oktober": "Oktober", "november": "November", "dezember": "Dezember",
}
_UNIT_MAP = {
    "km/h": "Kilometer pro Stunde", "km": "Kilometer", "m": "Meter", "cm": "Zentimeter", "mm": "Millimeter",
    "kg": "Kilogramm", "g": "Gramm", "mg": "Milligramm", "l": "Liter", "ml": "Milliliter",
}
_ABBREVIATIONS_MAP = {
    r"z\.B\.": "zum Beispiel", r"usw\.": "und so weiter", r"u\.a\.": "unter anderem",
    r"ggf\.": "gegebenenfalls", r"Dr\.": "Doktor", r"Prof\.": "Professor", r"ca\.": "circa",
}
_SYMBOLS_MAP = {"&": " und ", "+": " plus ", "=": " gleich "}
_DIRECTIONS_MAP = {
    "n": "Nord", "nord": "Nord", "o": "Ost", "ost": "Ost", "s": "Süd", "süd": "Süd",
    "w": "West", "west": "West", "no": "Nordost", "nord-ost": "Nordost", "so": "Südost",
    "süd-ost": "Südost", "sw": "Südwest", "süd-west": "Südwest", "nw": "Nordwest", "nord-west": "Nordwest",
}
_PHONETIC_WORKAROUNDS = {
    re.compile(r"\bBudget\b", re.IGNORECASE): "Büdschee",
    re.compile(r"\bcirca\b", re.IGNORECASE): "zirka",
}
_YEAR_MIN, _YEAR_MAX = 1000, 2999

# --- Kompilierte Reguläre Ausdrücke ---
_MONTHS_PATTERN = "|".join(_MONTHS_MAP.keys())
_UNITS_PATTERN = "|".join(_UNIT_MAP.keys())

_NUMBER_RANGE_PERCENT_RE = re.compile(r"\b(\d+)\s*-\s*(\d+)\s*%")
_DATE_RANGE_RE = re.compile(rf"\b(?P<prefix>am|den)\s+(?P<day1>\d{{1,2}})\.\s*und\s*(?P<day2>\d{{1,2}})\.\s*(?P<month>{_MONTHS_PATTERN})\b", re.IGNORECASE)
_DATE_RE = re.compile(rf"(?:\b(?P<prefix>der|am|den)\s*)?\b(?P<day>\d{{1,2}})\.\s*(?P<month>{_MONTHS_PATTERN})(?:\s+(?P<year>\d{{4}}))?(?P<dot>\.)?", re.IGNORECASE)
_IM_JAHR_RE = re.compile(r"\bim\s+jahr\s+(?P<year>\d{4})\b", re.IGNORECASE)
_UHR_RE = re.compile(r"\b(\d{1,2}):(\d{2})\s+Uhr\b")
_NUMBER_RANGE_RE = re.compile(r"\b(\d+)\s*-\s*(\d+)\b")
# KORRIGIERT: Eine einzige, robuste Regex für Währungen
_CURRENCY_RE = re.compile(r"(\d[\d\.,]*)\s*(€|EUR|Euro)\b")
_PERCENT_RE = re.compile(r"(\d[\d,\.]*)\s*%")
_UNIT_RE = re.compile(rf"(\d[\d,\.]*)\s*({_UNITS_PATTERN})\b", re.IGNORECASE)
_ORDINAL_RE = re.compile(r"\b(\d+)\.(?!\d)")
_PARAGRAPH_RE = re.compile(r"§\s*(\d+)\b")

# --- Hilfsfunktionen ---
def _num_to_words(num_str: str, **kwargs) -> str:
    # KORRIGIERT: Behandelt NUR noch ganze Zahlen. Keine Komma-Manipulation mehr.
    num_str_clean = num_str.replace('.', '').replace(',', '')
    try:
        return num2words(int(num_str_clean), lang='de', **kwargs)
    except (ValueError, TypeError):
        return num_str

def _replace_currency(match: re.Match) -> str:
    # KORRIGIERT: Vollständig eigenständige Logik.
    num_str = match.group(1)
    
    # Entferne Tausendertrennzeichen (Punkte)
    num_str_no_dots = num_str.replace('.', '')
    
    if ',' in num_str_no_dots:
        parts = num_str_no_dots.split(',')
        euro_part_str = parts[0]
        cent_part_str = parts[1]
        
        euro_words = num2words(int(euro_part_str), lang='de')
        
        # Nur Cent-Teil hinzufügen, wenn er größer als Null ist
        if int(cent_part_str) > 0:
            cent_words = num2words(int(cent_part_str), lang='de')
            return f"{euro_words} Euro {cent_words}"
        else:
            return f"{euro_words} Euro"
    else:
        # Fallback für ganze Zahlen ohne Komma
        return f"{num2words(int(num_str_no_dots), lang='de')} Euro"

# --- Haupt-Normalisierungsfunktion ---
def normalize_text_de(text: str) -> str:
    logger.debug(f"normalize_text_de: input='{text}'")
    out = text

    # Stufe 1: Kritische Abkürzungen & Phonetische Workarounds
    for pattern, replacement in _ABBREVIATIONS_MAP.items():
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
    for pattern, replacement in _PHONETIC_WORKAROUNDS.items():
        out = pattern.sub(replacement, out)

    # Stufe 2: Himmelsrichtungen
    for dir_pattern, dir_replacement in _DIRECTIONS_MAP.items():
        out = re.sub(rf"\b{dir_pattern}\b", dir_replacement, out, flags=re.IGNORECASE)

    # Stufe 3: Spezifische, zusammengesetzte Muster
    out = _NUMBER_RANGE_PERCENT_RE.sub(lambda m: f"{_num_to_words(m.group(1))} bis {_num_to_words(m.group(2))} Prozent", out)
    out = _CURRENCY_RE.sub(_replace_currency, out)
    out = _PERCENT_RE.sub(lambda m: f"{_num_to_words(m.group(1))} Prozent", out)
    out = _UNIT_RE.sub(lambda m: f"{_num_to_words(m.group(1))} {_UNIT_MAP.get(m.group(2).lower(), m.group(2))}", out)
    out = _UHR_RE.sub(lambda m: f"{_num_to_words(m.group(1))} Uhr {_num_to_words(m.group(2)) if m.group(2) != '00' else ''}".strip(), out)
    out = _NUMBER_RANGE_RE.sub(lambda m: f"{_num_to_words(m.group(1))} bis {_num_to_words(m.group(2))}", out)
    out = _PARAGRAPH_RE.sub(lambda m: f"Paragraph {_num_to_words(m.group(1))}", out)
    out = out.replace("°C", " Grad Celsius")

    # Stufe 4: Datumsangaben
    def replace_date_range(m):
        prefix, day1, day2, month_raw = m.groups()
        month = _MONTHS_MAP.get(month_raw.lower(), month_raw)
        return f"{prefix} {num2words(int(day1), lang='de', to='ordinal')}n und {num2words(int(day2), lang='de', to='ordinal')}n {month}"
    out = _DATE_RANGE_RE.sub(replace_date_range, out)
    
    def replace_date(m):
        prefix, day, month_raw, year_raw, dot = m.groups()
        day_word = num2words(int(day), lang='de', to='ordinal')
        if prefix and prefix.lower() in ["am", "den"]: day_word += 'n'
        year_str = ""
        if year_raw:
            year = int(year_raw)
            if _YEAR_MIN <= year <= _YEAR_MAX: year_str = f" {num2words(year, lang='de')}"
            else: year_str = f" {year}"
        return f"{prefix + ' ' if prefix else ''}{day_word} {_MONTHS_MAP.get(month_raw.lower(), month_raw)}{year_str}{dot or ''}"
    out = _DATE_RE.sub(replace_date, out)
    out = _IM_JAHR_RE.sub(lambda m: f"im Jahr {num2words(int(m.group('year')), lang='de')}", out)

    # Stufe 5: Allgemeine Ordnungszahlen
    out = _ORDINAL_RE.sub(lambda m: num2words(int(m.group(1)), lang='de', to='ordinal'), out)

    # Stufe 6: Allgemeine Symbole
    for symbol, word in _SYMBOLS_MAP.items():
        out = out.replace(symbol, word)

    # Finale Bereinigung
    out = re.sub(r'\s+', ' ', out).strip()
    logger.debug(f"normalize_text_de: output='{out}'")
    return out
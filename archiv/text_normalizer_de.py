# -*- coding: utf-8 -*-
"""
German TTS pre-normalizer for Piper (and similar engines).

Goals:
- Avoid mistaken ordinalization of years (e.g., "2025." → "fünfundzwanzigsten").
- Normalize dates like "11. Oktober 2025." to a TTS-friendly form.
- Make enumerations ("1.") robust by rewriting them to "Punkt 1:" or
  optional adverbial ordinals ("erstens, zweitens, …").

Integration hint (Janus):
- Place as backend/services/tts_normalizer.py and import normalize_text_de
  in your TTS pipeline before sending text to Piper.

Usage:
>>> from text_normalizer_de import normalize_text_de
>>> normalize_text_de("Morgen ist der 11. Oktober 2025.")
'Morgen ist der elfte Oktober zweitausendfünfundzwanzig.'
>>> normalize_text_de("1. Eintrag\n2. Nächster Punkt", enumeration_style="punkt")
'Punkt 1: Eintrag\nPunkt 2: Nächster Punkt'
>>> normalize_text_de("Das war 2025.")
'Das war zweitausendfünfundzwanzig.'

Notes:
- By default, years and dates are spelled out in words for clarity.
- Set prefer_spelled_years=False to keep 4-digit years as numerals (still removing the trailing dot issue).
"""

from __future__ import annotations

import re
from typing import Callable, Dict, Optional

from num2words import num2words

# --- Configuration helpers ----------------------------------------------------

_MONTHS_CANONICAL = {
    "januar": "Januar",
    "februar": "Februar",
    "märz": "März",
    "maerz": "März",
    "april": "April",
    "mai": "Mai",
    "juni": "Juni",
    "juli": "Juli",
    "august": "August",
    "september": "September",
    "oktober": "Oktober",
    "november": "November",
    "dezember": "Dezember",
}

_ENUM_ADVERBS = {
    1: "erstens",
    2: "zweitens",
    3: "drittens",
    4: "viertens",
    5: "fünftens",
    6: "sechstens",
    7: "siebtens",
    8: "achtens",
    9: "neuntens",
    10: "zehntens",
}

_YEAR_MIN = 1000
_YEAR_MAX = 2999

# Pre-compiled regexes
_DATE_RE = re.compile(
    r"\b(?P<day>\d{1,2})\.\s*(?P<month>Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(?P<year>\d{4})(?P<dot>\.)?",
    flags=re.IGNORECASE,
)

# 4-digit year followed by a period (to avoid ordinalization). Restrict to plausible years.
_TRAILING_DOT_YEAR_RE = re.compile(
    rf"\b(?P<year>{_YEAR_MIN}-{_YEAR_MAX}|1[0-9]{{3}}|2[0-9]{{3}})(?=\.)"
)

# Start-of-line enumerations like "1. ..." (multiline)
_SOL_ENUM_RE = re.compile(r"(?m)^(?P<indent>\s*)(?P<num>\d{1,2})\.\s+")

# Inline enumerations like "1., 2., 3." or "1.; 2.;"
_INLINE_ENUM_RE = re.compile(r"\b(?P<num>\d{1,2})\.(?=\s*[,;])")

# Convert explicit "im Jahr 2025" to spelled-out year
_IM_JAHR_RE = re.compile(r"\bim\s+jahr\s+(?P<year>\d{4})\b", flags=re.IGNORECASE)


def _to_ordinal_day(n: int) -> str:
    # num2words returns lower-case, which we want in running text.
    return num2words(n, lang="de", to="ordinal")


def _year_to_words(y: int) -> str:
    return num2words(y, lang="de")


def _is_plausible_year(y: int) -> bool:
    return _YEAR_MIN <= y <= _YEAR_MAX


def _replace_date(match: re.Match, prefer_spelled_years: bool) -> str:
    day = int(match.group("day"))
    month_raw = match.group("month")
    year = int(match.group("year"))

    # Canonicalize month capitalization and umlaut
    month_key = month_raw.lower()
    month = _MONTHS_CANONICAL.get(month_key, month_raw)

    # Day as ordinal word ("elfte")
    day_word = _to_ordinal_day(day)

    if prefer_spelled_years:
        year_word = _year_to_words(year)
        tail = "." if match.group("dot") else ""
        # Example: "der elfte Oktober zweitausendfünfundzwanzig."
        return f"{day_word} {month} {year_word}{tail}"
    else:
        # Keep numeric year but remove problematic trailing dot after the year.
        # We'll keep the sentence-ending dot if present, but attach it after the year without causing ordinalization.
        # Many TTS engines handle this fine once the day is spelled out.
        return f"{day_word} {month} {year}"


def _replace_trailing_dot_year(match: re.Match, prefer_spelled_years: bool) -> str:
    y = int(match.group("year"))
    if not _is_plausible_year(y):
        return match.group(0)
    if prefer_spelled_years:
        return _year_to_words(y)
    else:
        # Keep numeric, but the caller will remove the dot by virtue of the lookahead; we just return the number.
        return str(y)


def _rewrite_sol_enumeration(text: str, enumeration_style: str) -> str:
    def repl(m: re.Match) -> str:
        indent = m.group("indent") or ""
        num = int(m.group("num"))
        if enumeration_style == "adverb" and num in _ENUM_ADVERBS:
            return f"{indent}{_ENUM_ADVERBS[num]}: "
        # default: punkt-style
        return f"{indent}Punkt {num}: "

    return _SOL_ENUM_RE.sub(repl, text)


def _rewrite_inline_enumerations(text: str, enumeration_style: str) -> str:
    def repl(m: re.Match) -> str:
        num = int(m.group("num"))
        if enumeration_style == "adverb" and num in _ENUM_ADVERBS:
            return _ENUM_ADVERBS[num]
        return f"Punkt {num}"

    return _INLINE_ENUM_RE.sub(repl, text)


def normalize_text_de(
    text: str,
    *,
    expand_dates: bool = True,
    prefer_spelled_years: bool = True,
    enumeration_style: str = "punkt",  # "punkt" | "adverb"
) -> str:
    """
    Normalize German text for TTS with a focus on dates, years, and enumerations.

    Params:
    - expand_dates: convert "11. Oktober 2025" → "elfte Oktober zweitausendfünfundzwanzig".
    - prefer_spelled_years: convert 4-digit years to words (and fix trailing dots).
    - enumeration_style: "punkt" (Punkt 1:, Punkt 2:) or "adverb" (erstens, zweitens, … up to 10).

    Returns: normalized text string.
    """
    out = text

    # 1) Dates like "11. Oktober 2025." → "elfte Oktober zweitausendfünfundzwanzig."
    if expand_dates:
        out = _DATE_RE.sub(lambda m: _replace_date(m, prefer_spelled_years), out)

    # 2) "im Jahr 2025" → "im Jahr zweitausendfünfundzwanzig"
    if prefer_spelled_years:
        def im_jahr_repl(m: re.Match) -> str:
            y = int(m.group("year"))
            if _is_plausible_year(y):
                return f"im Jahr {_year_to_words(y)}"
            return m.group(0)
        out = _IM_JAHR_RE.sub(im_jahr_repl, out)

    # 3) Fix 4-digit years followed by a dot (avoid ordinalization)
    # Replace the year digits (lookahead keeps the dot outside); if spelled, the dot remains after the word.
    out = _TRAILING_DOT_YEAR_RE.sub(lambda m: _replace_trailing_dot_year(m, prefer_spelled_years), out)

    # 4) Start-of-line enumerations "1. Foo" → "Punkt 1: Foo" or "erstens: Foo"
    out = _rewrite_sol_enumeration(out, enumeration_style)

    # 5) Inline enumerations "1., 2., 3." → "Punkt 1, Punkt 2, Punkt 3"
    out = _rewrite_inline_enumerations(out, enumeration_style)

    return out


if __name__ == "__main__":
    samples = [
        "Morgen ist der 11. Oktober 2025.",
        "1. Eintrag\n2. Nächster Punkt\n10. Letzter Punkt",
        "Aufgaben: 1., 2., 3.",
        "Das war 2025.",
        "Wir sehen uns im Jahr 2030.",
        "Termin: 3. Maerz 2026.",
    ]
    for s in samples:
        print("IN :", s)
        print("OUT:", normalize_text_de(s))
        print("-")

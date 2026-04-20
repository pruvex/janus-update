from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, List

HEALTH_KEYWORDS = (
    "allergi",
    "unverträglich",
    "intoleranz",
    "medikament",
    "erkrankung",
    "krankheit",
    "diabetes",
    "asthma",
    "epilepsie",
    "blutdruck",
    "gesundheit",
    "health",
    "allergen",
    "medizin",
    "medication",
    "medical",
)

NEG_PREF_KW = (
    "hasst",
    "mag nicht",
    "mag kein",
    "verabscheut",
    "nicht leiden",
    "nicht ausstehen",
    "abneigung",
    "hass",
    "ekelt",
    "trinkt kein",
    "isst kein",
    "verträgt kein",
    "lehnt ab",
)

FAMILY_RELATION_RE = re.compile(
    r"\b(bruder|schwester|vater|mutter|eltern|sohn|tochter|oma|opa|"
    r"großvater|großmutter|mann|frau|kind|kinder|cousin|cousine|tante|onkel|familie)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PromptDirective:
    name: str
    detector: Callable[[str], bool]
    directive_text: str
    position: str  # "prepend" | "after_identity"
    log_tag: str


def _medical_warning_detector(ctx: str) -> bool:
    lower_ctx = str(ctx or "").lower()
    return any(kw in lower_ctx for kw in HEALTH_KEYWORDS)


def _family_context_detector(ctx: str) -> bool:
    return bool(FAMILY_RELATION_RE.search(str(ctx or "")))


def _negative_preferences_detector(ctx: str) -> bool:
    lower_ctx = str(ctx or "").lower()
    return any(kw in lower_ctx for kw in NEG_PREF_KW)


DIRECTIVES: List[PromptDirective] = [
    PromptDirective(
        name="medical_warning",
        detector=_medical_warning_detector,
        directive_text=(
            "!!! CRITICAL MEDICAL WARNING !!!\n"
            "Der Nutzer hat medizinische Einschränkungen oder Allergien gespeichert. "
            "Du MUSST alle gesundheitsrelevanten Fakten aus dem Kontext zwingend "
            "beachten, bevor du Lebensmittel, Medikamente oder Empfehlungen gibst. "
            "Ignoriere NIEMALS Allergie- oder Gesundheitsdaten aus dem Kontext!\n"
            "Du MUSST bei angefragten Lebensmitteln (wie Studentenfutter) ZWINGEND nachdenken, "
            "ob sie versteckte Allergene (wie Nüsse) enthalten. Warne sofort und verbiete "
            "den Verzehr, falls zutreffend!\n"
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n"
        ),
        position="prepend",
        log_tag="[MEDICAL-OVERRIDE-021]",
    ),
    PromptDirective(
        name="family_context",
        detector=_family_context_detector,
        directive_text=(
            "Du kennst auch die Familienmitglieder des Nutzers aus dem "
            "gespeicherten Kontext. "
            "VERBOTEN: 'Ich habe keine Informationen dazu', "
            "'Das ist mir nicht bekannt' — "
            "nutze den verfügbaren Kontext und antworte direkt!\n\n"
        ),
        position="after_identity",
        log_tag="[INSTRUCTION-HARDENING-021]",
    ),
    PromptDirective(
        name="negative_preferences",
        detector=_negative_preferences_detector,
        directive_text=(
            "NEGATIV-PRÄFERENZEN ERKANNT: Im Kontext stehen "
            "Dinge, die der User HASST oder NICHT MAG. "
            "Bei Fragen nach Vorlieben/Gewohnheiten MÜSSEN "
            "diese Abneigungen EXPLIZIT und VOLLSTÄNDIG "
            "genannt werden — positive UND negative!\n"
        ),
        position="after_identity",
        log_tag="[NEGATIVE-PREF-DETECT]",
    ),
]


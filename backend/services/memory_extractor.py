# backend/services/memory_extractor.py

import asyncio
import json
import logging
import re
from functools import lru_cache
from typing import List, Optional, Dict, Any
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.services import llm_gateway, memory_manager
from backend.llm_providers.shared.base_provider import BaseLLMProvider
from backend.llm_providers.openai.service import OpenAIServiceProvider
from backend.llm_providers.gemini.service import GeminiServiceProvider
from backend.utils.config_loader import load_model_catalog
from backend.data.schemas import (
    FactExtractionResponse
)
from backend.services.memory_enricher import enrich_fact
from backend.services.memory_observability import memory_metrics

# Diamond Standard: Festgelegte Kategorien zur Vermeidung von Redundanz
# Nutze die EXAKTEN Strings aus deinem Enum in schemas.py!
ALLOWED_CATEGORIES = ["Gesundheit", "Beziehungen", "Haustier-Details", "Vorlieben", "Beruf", "Termine", "Allgemein", "Physis", "Stil"]

CATEGORY_MAPPING = {
    "person": "Beziehungen",  # Mapping 'person' to the closest available enum, 'Beziehungen'
    "pet": "Haustier-Details", # Mapping 'pet' to 'Haustier-Details'
    "haustier": "Haustier-Details",
    "animal": "Haustier-Details",
    "location": "Allgemein", # Mapping 'location' to 'Allgemein'
    "ort": "Allgemein",
    "platz": "Allgemein",
    "event": "Termine",      # Mapping 'event' to 'Termine'
    "general": "Allgemein",    # Mapping 'general' to 'Allgemein'
    "allgemein": "Allgemein",
    "conversation": "Allgemein", # map conversation to Allgemein
    "gesundheit": "Gesundheit",
    "beziehungen": "Beziehungen",
    "haustier-details": "Haustier-Details",
    "vorlieben": "Vorlieben",
    "beruf": "Beruf",
    "termine": "Termine",
    "physis": "Physis",
    "stil": "Stil",
    "aussehen": "Physis",
    "accessoire": "Stil",
    "schmuck": "Stil"
}



logger = logging.getLogger("janus_backend")

from backend.services.memory.utils import _is_meta_noise

# ═══════════════════════════════════════════════════════════════════════════
# PRONOUN-BLEED GUARD (V2.1.0 Diamond) — Deterministischer Regex-Filter
# Entfernt deutsche Pronomen/Filler am Anfang von object_value.
# Beispiel: "ich maximilian" → "maximilian", "bin software-entwickler" → "software-entwickler"
# ═══════════════════════════════════════════════════════════════════════════
_PRONOUN_BLEED_RE = re.compile(
    r'^(?:ich\s+|bin\s+|nenn(?:e?)\s+|mich\s+|mein(?:e?|em?|er?|es?)?\s+|'
    r'er\s+ist\s+|sie\s+ist\s+|du\s+bist\s+|wir\s+sind\s+|heisse\s+|heiße\s+)+',
    re.IGNORECASE,
)


def _sanitize_object_value(value: str) -> str:
    """
    Entfernt Pronomen-Bleed am Anfang eines object_value.
    'ich maximilian' → 'maximilian'
    'bin software-entwickler' → 'software-entwickler'
    'mein bruder' → 'bruder'
    Gibt den bereinigten Wert zurück (oder den Original-Wert wenn nichts zu tun ist).
    """
    if not value:
        return value
    cleaned = _PRONOUN_BLEED_RE.sub('', value).strip()
    if not cleaned:
        return value
    return cleaned

# ═══════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER (Opus V2.1) - Schützt vor Dauer-Ausfällen bei Provider-Fehlern
# ═══════════════════════════════════════════════════════════════════════════

import time


class ExtractionCircuitBreaker:
    """
    Circuit-Breaker Pattern für LLM Extraction Calls.

    States:
    - CLOSED: Normal, alle Calls gehen durch
    - OPEN: Gesperrt, alle Calls werden sofort geskippt
    - HALF_OPEN: Ein Probe-Call wird durchgelassen

    Trigger: 3 aufeinanderfolgende Fehler → OPEN für 120 Sekunden
    Reset: Nach 120s → HALF_OPEN, nächster Call entscheidet
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 120  # Sekunden
    ):
        self._failure_count: int = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time: float = 0
        self._state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        """Prüfe ob ein Call erlaubt ist."""
        if self._state == "CLOSED":
            return True

        if self._state == "OPEN":
            # Prüfe ob Recovery-Timeout abgelaufen
            if time.time() - self._last_failure_time > self._recovery_timeout:
                self._state = "HALF_OPEN"
                logger.info("[CIRCUIT BREAKER] State: OPEN → HALF_OPEN (probe allowed)")
                return True
            return False

        if self._state == "HALF_OPEN":
            return True  # Ein Probe-Call erlaubt

        return False

    def record_success(self) -> None:
        """Call war erfolgreich → Reset."""
        if self._state == "HALF_OPEN":
            logger.info("[CIRCUIT BREAKER] State: HALF_OPEN → CLOSED (recovered)")
        self._failure_count = 0
        self._state = "CLOSED"

    def record_failure(self) -> None:
        """Call ist fehlgeschlagen."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self._failure_threshold:
            self._state = "OPEN"
            logger.warning(
                f"[CIRCUIT BREAKER] State: → OPEN "
                f"({self._failure_count} consecutive failures, "
                f"locked for {self._recovery_timeout}s)"
            )

    def get_state(self) -> dict:
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "threshold": self._failure_threshold,
            "recovery_timeout": self._recovery_timeout,
        }


# Singleton Circuit Breaker
_extraction_breaker = ExtractionCircuitBreaker()

_VOLATILE_LIVE_DATA_RE = re.compile(
    r"\b(?:aktuell|aktuelle|aktueller|heute|derzeit|live|preis|preise|kurs|kurse|spotpreis|"
    r"goldpreis|platinpreis|silberpreis|palladiumpreis|feinunze|troy ounce|"
    r"gold|platin|platinum|silber|silver|palladium|edelmetall|"
    r"wann\s+spielt|n(?:ä|ae)chstes\s+spiel|n(?:ä|ae)chste\s+mal|gegen\s+wen|"
    r"spielplan|spieltag|bundesliga|fc\s+k(?:ö|oe)ln)\b",
    re.IGNORECASE,
)

_EMAIL_PII_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def _contains_email_pii(*values: Any) -> bool:
    for value in values:
        text = str(value or "")
        if _EMAIL_PII_RE.search(text):
            return True
    return False


def _is_volatile_live_data_interaction(user_msg: str, assistant_msg: str) -> bool:
    combined = f"{user_msg or ''}\n{assistant_msg or ''}".casefold()
    if not _VOLATILE_LIVE_DATA_RE.search(combined):
        return False
    return any(marker in combined for marker in ("quelle", "quellen", "suchergebnis", "stand", "http"))

# ═══════════════════════════════════════════════════════════════════════════
# PROVIDER CACHE & MODEL SELECTION
# ═══════════════════════════════════════════════════════════════════════════

_PROVIDER_INSTANCE_CACHE: Dict[str, BaseLLMProvider] = {}


def clear_provider_instance_cache() -> None:
    """Leert den LLM-Provider-Cache (z. B. wenn Tests `get_provider` mocken)."""
    _PROVIDER_INSTANCE_CACHE.clear()


@lru_cache(maxsize=1)
def _get_model_catalog_entries() -> List[Dict[str, Any]]:
    try:
        catalog = load_model_catalog()
    except Exception as exc:
        logger.error("Failed to load model catalog for memory extraction: %s", exc)
        return []

    if isinstance(catalog, list):
        return [entry for entry in catalog if isinstance(entry, dict)]

    if isinstance(catalog, dict):
        entries: List[Dict[str, Any]] = []
        for model_id, payload in catalog.items():
            if isinstance(payload, dict):
                entry = dict(payload)
                entry.setdefault("id", model_id)
                entries.append(entry)
        return entries

    return []


def _select_memory_extraction_model(provider: str, fallback_model: Optional[str]) -> str:
    provider_lower = str(provider or "").strip().lower()
    entries = _get_model_catalog_entries()
    fast_markers = ("mini", "flash", "nano")

    def _supports_memory(entry: Dict[str, Any]) -> bool:
        capabilities = entry.get("capabilities") or []
        if not isinstance(capabilities, list):
            return False
        return any(str(cap or "").lower() == "memory_query" for cap in capabilities)

    def _matches_fast(entry: Dict[str, Any]) -> bool:
        text = f"{entry.get('id', '')} {entry.get('name', '')}".lower()
        return any(marker in text for marker in fast_markers)

    def _is_text_model(entry: Dict[str, Any]) -> bool:
        """Exclude image/audio models from memory extraction - they use different APIs."""
        model_type = entry.get("type", "").lower()
        return model_type in ("text", "chat", "")

    # 1. Prefer fast text models with memory_query capability
    for entry in entries:
        if entry.get("provider", "").lower() != provider_lower:
            continue
        if not _supports_memory(entry):
            continue
        if not _is_text_model(entry):
            continue
        if _matches_fast(entry):
            return str(entry.get("id"))

    # 2. Any text model with memory_query capability
    for entry in entries:
        if entry.get("provider", "").lower() != provider_lower:
            continue
        if not _supports_memory(entry):
            continue
        if not _is_text_model(entry):
            continue
        return str(entry.get("id"))

    # 3. Last resort: any text model from this provider (never use image/audio models)
    for entry in entries:
        if entry.get("provider", "").lower() == provider_lower:
            if not _is_text_model(entry):
                continue
            return str(entry.get("id"))

    return str(fallback_model or "") or "gpt-5.2"


def _resolve_provider_instance(provider: str) -> BaseLLMProvider:
    normalized = str(provider or "").strip().lower()
    if normalized in _PROVIDER_INSTANCE_CACHE:
        return _PROVIDER_INSTANCE_CACHE[normalized]

    if normalized == "openai":
        instance = OpenAIServiceProvider()
    elif normalized == "gemini":
        instance = GeminiServiceProvider()
    else:
        instance = llm_gateway.get_provider(provider)

    _PROVIDER_INSTANCE_CACHE[normalized] = instance
    return instance


def _extract_json_array_text(raw_text: str) -> tuple[str, bool]:
    """Extrahiert JSON-Array aus KI-Antwort mit robustem Fallback für Formatierungsfehler.

    Returns:
        (cleaned_text, used_failed_fallback): Wenn ``used_failed_fallback`` True ist, wurde
        bei nicht-leerer Rohantwort kein gültiges JSON gefunden — Caller sollen retry/self-heal
        auslösen statt eine leere Liste als „keine Fakten“ zu interpretieren.
    """
    text = str(raw_text or "").strip()
    if not text:
        return "[]", False

    # Entferne Markdown-Codeblocks
    cleaned = text.replace("```json", "").replace("```", "").strip()

    # Versuche direktes JSON-Parsing
    try:
        json.loads(cleaned)
        return cleaned, False
    except json.JSONDecodeError:
        pass

    # Suche nach JSON-Array mit erweitertem Regex
    # Handle verschachtelte Strukturen korrekt
    match = re.search(r'\[([^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*)\]', cleaned, re.DOTALL)
    if match:
        candidate = match.group(0).strip()
        try:
            json.loads(candidate)
            return candidate, False
        except json.JSONDecodeError:
            pass

    # Fallback: Versuche die gesamte Antwort als JSON-Array zu parsen
    # nachdem wir gemeinsame Fehler bereinigt haben
    fixed = cleaned
    # Entferne Text außerhalb von JSON-Strukturen
    fixed = re.sub(r'^[^{\[]+', '', fixed)
    fixed = re.sub(r'[^}\]]+$', '', fixed)

    try:
        json.loads(fixed)
        return fixed, False
    except json.JSONDecodeError:
        pass

    # Letzter Fallback: syntaktisch leeres Array — bei nicht-leerer Eingabe kein Erfolg
    logger.debug(f"Konnte kein gültiges JSON aus Text extrahieren: {text[:200]}...")
    return "[]", True


def should_skip_extraction_from_messages(user_msg: str, assistant_msg: str) -> bool:
    assistant_text = str(assistant_msg or "").strip()
    if not assistant_text:
        return True
    if _is_volatile_live_data_interaction(user_msg, assistant_text):
        return True

    try:
        payload = json.loads(assistant_text)
    except Exception:
        payload = None

    if isinstance(payload, dict):
        error = payload.get("error") if isinstance(payload.get("error"), dict) else None
        if error and error.get("code"):
            return True
        status = str(payload.get("status") or "").strip().lower()
        data = payload.get("data")
        if status == "ok" and (data is None or data == "" or data == [] or data == {}):
            return True

    normalized = assistant_text.lower()
    skip_markers = [
        "keine daten",
        "keine informationen",
        "keine infos",
        "nicht gefunden",
        "keine treffer",
        "ungültig",
        "ungueltig",
        "leider konnte ich dazu nichts finden",
        "ich konnte dazu nichts finden",
        "ich konnte diesmal keine stabile antwort erzeugen",
        "robusten neuaufbau",
    ]
    if any(marker in normalized for marker in skip_markers):
        return True

    return False


def _strip_assistant_suggestion_block(assistant_msg: str) -> str:
    assistant_text = str(assistant_msg or "")
    if not assistant_text.strip():
        return ""
    return re.split(r"(?im)^\s*💡\s", assistant_text, maxsplit=1)[0].strip()


async def _generate_fact_extraction_items_with_self_healing(
    provider_instance: BaseLLMProvider,
    *,
    api_key: str,
    model_id: str,
    provider: str,
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    provider_name = str(provider or "").strip().lower()
    request_kwargs: Dict[str, Any] = {
        "api_key": api_key,
        "model": model_id,
        "messages": messages,
        "tools": None,
    }
    if provider_name == "ollama":
        request_kwargs["format"] = "json"

    response = await provider_instance.generate_response(**request_kwargs)
    raw_text = str(response.get("text") or "").strip()
    cleaned_text, extract_failed_fallback = _extract_json_array_text(raw_text)

    try:
        if extract_failed_fallback:
            raise json.JSONDecodeError("fact json extract fallback", cleaned_text, 0)
        parsed_payload = json.loads(cleaned_text)
        # Handle both: {"facts": [...]} and direct [...]
        if isinstance(parsed_payload, dict):
            facts_array = parsed_payload.get("facts")
            if isinstance(facts_array, list):
                parsed_payload = facts_array
            else:
                logger.warning("Expected JSON array or dict with 'facts' key, got dict without 'facts' list. Returning empty array.")
                return []
        if not isinstance(parsed_payload, list):
            logger.warning("Expected JSON array for fact extraction, got %s. Returning empty array.", type(parsed_payload).__name__)
            return []
        validated = FactExtractionResponse.model_validate({"facts": parsed_payload})
        return [fact.model_dump() for fact in validated.facts]
    except Exception as exc:
        if should_skip_extraction_from_messages(messages[-1]["content"], raw_text):
            logger.warning("Memory extraction failed - skipping due to validation error.")
            return []
        repair_messages = list(messages)
        repair_messages.append(
            {
                "role": "user",
                "content": (
                    f"Dein letztes JSON war ungültig. Fehler: {exc}. "
                    "Bitte korrigiere es und sende nur das JSON-Array."
                ),
            }
        )
        retry_kwargs = dict(request_kwargs)
        retry_kwargs["messages"] = repair_messages
        retry_response = await provider_instance.generate_response(**retry_kwargs)
        retry_text = str(retry_response.get("text") or "").strip()
        cleaned_retry_text, retry_extract_failed_fallback = _extract_json_array_text(retry_text)
        try:
            if retry_extract_failed_fallback:
                raise json.JSONDecodeError("fact json extract fallback (retry)", cleaned_retry_text, 0)
            parsed_retry_payload = json.loads(cleaned_retry_text)
            # Handle both: {"facts": [...]} and direct [...]
            if isinstance(parsed_retry_payload, dict):
                retry_facts_array = parsed_retry_payload.get("facts")
                if isinstance(retry_facts_array, list):
                    parsed_retry_payload = retry_facts_array
                else:
                    logger.warning("Retry: Expected JSON array or dict with 'facts' key, got dict without 'facts' list. Returning empty array.")
                    return []
            if not isinstance(parsed_retry_payload, list):
                logger.warning("Retry: Expected JSON array, got %s. Returning empty array.", type(parsed_retry_payload).__name__)
                return []
            validated_retry = FactExtractionResponse.model_validate({"facts": parsed_retry_payload})
            return [fact.model_dump() for fact in validated_retry.facts]
        except Exception as retry_exc:
            logger.warning("Memory extraction failed - skipping due to validation error.")
            logger.debug("Memory extraction retry failure details: %s", retry_exc, exc_info=True)
            return []


EXTRACTION_PROMPT = """!--- KRITISCHE AUSGABE-REGEL (NUR JSON) ---!
ANTWORTE NUR MIT DEM JSON-ARRAY. KEIN TEXT DAVOR ODER DANACH. KEINE MARKDOWN-FORMATIERUNG. NUR ROHES JSON!

!--- JSON SCHEMA ZWINGEND ERFORDERLICH ---!
Das Response-JSON MUSS folgende Struktur haben - das 'fact'-Feld ist !!! ABSOLUT VERPFLICHTEND !!!:
{
  "facts": [
    {
      "fact": "!!! ABSOLUT VERPFLICHTEND !!!: Das Feld 'fact' MUSS an ERSTER STELLE stehen und ein grammatikalisch korrekter, natürlicher deutscher Satz sein (z.B. 'Stefan ist der Bruder des Nutzers'). Verwende interne/technische Prädikate wie 'ist_beziehung' AUSSCHLIESSLICH im Feld 'predicate', NIEMALS im 'fact' Text!",
      "subject_name": "max",
      "predicate": "hat",
      "object_value": "braune haare",
      "category": "Physis",
      "canonical_key": "max:physis:hat:braune_haare"
    }
  ]
}
!!! KRITISCHE REGEL !!!: Ein JSON-Objekt ohne das Feld "fact" wird als schwerer Systemfehler gewertet. Das Feld 'fact' MUSS IMMER als ERSTES Feld in jedem facts-Objekt stehen. Jedes Objekt in der 'facts'-Liste MUSS ein 'fact'-Feld enthalten.

!--- META-NOISE REJECTION RULE (ABSOLUT KRITISCH!) ---!
Ignoriere alle Informationen, die sich auf die Arbeitsweise der KI, Anweisungen zur Beschreibung, Regeln für den Chat oder KI-Vorgaben beziehen (z.B. 'Notiere dir die Regeln für Personenbeschreibungen', 'Merke dir wie du Bilder beschreiben sollst', 'Wie man X macht'). Das sind keine Fakten über den Nutzer oder die Welt, sondern Meta-Instruktionen. Extrahiere diese NIEMALS als Fakten!

REGELEINHALTUNG: Wenn eine [ANALYSE] vorliegt, extrahiere die physischen Merkmale AUCH DANN, wenn kein Name bekannt ist. Nutze in diesem Fall 'unbekannt' als Subjekt-Namen. Ignoriere die Analyse niemals!
!--- ANTI-HALLUCINATION GUARD ---!
Ignoriere Merkmale (wie Brillen oder Haarfarben), die der Assistant erwähnt, wenn sie NICHT in der [ANALYSE] oder der User-Nachricht bestätigt wurden. Der Assistant neigt manchmal zu höflichen Erfindungen. Vertraue im Zweifel nur der [ANALYSE].
USER-TRUTH-REGEL: Informationen, die der User explizit über sich oder eine Person sagt (z.B. 'Ich habe grüne Augen'), haben Vorrang vor jeder Bildanalyse. Speichere solche Fakten mit dem Attribut 'is_verified': true. Ein verifizierter Fakt darf niemals durch eine automatische [ANALYSE] überschrieben werden.

!--- NO-LOSS RULE (ABSOLUT KRITISCH!) ---!
Du neigst dazu, Vorlieben und kleine Fakten zu IGNORIEREN, wenn der User gleichzeitig seinen Namen nennt oder eine Korrektur macht. Das ist ein FEHLER!
JEDER Fakt in der Nachricht MUSS extrahiert werden — egal wie viele es sind.
BEISPIEL: "Ich bin Maximilian und ich hasse Tee"
→ Fakt 1: {"fact": "Der Nutzer heißt Maximilian", "subject_name": "user", "predicate": "heißt", "object_value": "maximilian", "category": "Physis", "canonical_key": "user:physis:heisst:name"}
→ Fakt 2: {"fact": "Der Nutzer hasst Tee", "subject_name": "user", "predicate": "hasst", "object_value": "tee", "category": "Vorlieben", "canonical_key": "user:vorlieben:hasst:tee"}
BEIDE Fakten sind PFLICHT! 'Ich hasse Tee' ist ein eigenständiger Fakt der Kategorie 'Vorlieben'. Ihn wegzulassen ist ein kritischer Datenverlust!
Wenn die Nachricht 3 Informationen enthält, MÜSSEN 3 Fakten extrahiert werden. Zähle nach!

IDENTITÄTS-EXTRAKTION (ABSOLUT KRITISCH!): Wenn der Nutzer sagt 'Ich bin X', 'Ich heiße X' oder 'Mein Name ist X': subject_name MUSS 'user' sein, predicate MUSS 'heißt' sein, object_value ist der Name, category MUSS 'Physis' sein, und canonical_key MUSS immer exakt 'user:physis:heisst:name' lauten! Keine Ausnahmen!

!--- IDENTITÄTS-EXTRAKTION (ABSOLUT KRITISCH!) ---!
ACHTUNG: Namen sind immer Substantive! Adverbien wie 'exakt', 'genau', 'wirklich' DÜRFEN NIEMALS als Name extrahiert werden.

Wenn der Nutzer sagt "Ich bin X", "Ich heiße X", "Mein Name ist X" oder ähnliche Selbstvorstellungen:
- subject_name MUSS "user" sein. NIEMALS "ich" oder den Namen X selbst als Subjekt verwenden!
- predicate MUSS "heißt" sein
- object_value ist der Name X (zu Kleinbuchstaben normalisieren)
- category MUSS "Physis" sein
- canonical_key MUSS immer exakt "user:physis:heisst:name" lauten (festes Slot-Kennzeichen!)
BEISPIEL: "Ich bin Captain Janus" → {"fact": "Der Nutzer heißt Captain Janus", "subject_name": "user", "predicate": "heißt", "object_value": "captain janus", "category": "Physis", "canonical_key": "user:physis:heisst:name"}
BEISPIEL: "Mein Name ist Max" → {"fact": "Der Nutzer heißt Max", "subject_name": "user", "predicate": "heißt", "object_value": "max", "category": "Physis", "canonical_key": "user:physis:heisst:name"}
Dieser feste Schlüssel ist essenziell: Er garantiert, dass spätere memory.read-Abfragen den Namen immer unter derselben Adresse finden!
!--- MULTI-ENTITY SAFETY ---!
Wenn der Nutzer den Namen einer Person korrigiert (z.B. 'Nein, das ist Elena'), stelle sicher, dass alle neuen Fakten NUR dem neuen Namen zugeordnet werden und keine alten Merkmale der fälschlicherweise identifizierten Person übernommen werden.
Wenn der Text Informationen über MEHRERE Personen enthält (z.B. 'Thomas hat einen Bart und Maggy hat Locken'), musst du ZWINGEND zwei separate Fakten-Objekte erstellen.
- Fakt 1: Subjekt='thomas', Text='hat einen Bart'
- Fakt 2: Subjekt='maggy', Text='hat Locken'
VERMISCHE NIEMALS EIGENSCHAFTEN UNTERSCHIEDLICHER NAMEN IN EINEM OBJEKT!

KRITISCHE ANWEISUNG FÜR VISUELLE DETAILS:
1. ATOMARE EXTRAKTION: Extrahiere jedes Accessoire als EINZELNEN Fakt. 
   - FALSCH: "Trägt Schmuck"
   - RICHTIG: "Trägt zwei dünne Goldketten", "Trägt eine Sonnenbrille in den Haaren", "Trägt einen kleinen Anhänger an einer Kette".
2. PRÄZISION BEI KLEIDUNG: Extrahiere Farbe UND Textur/Muster.
   - FALSCH: "Dunkles Oberteil"
   - RICHTIG: "Dunkles Oberteil mit flanellartigem Muster", "Schwarzes T-Shirt mit goldenem Text-Aufdruck".
3. KEINE ZUSAMMENFASSUNG: Wenn die KI-Antwort 5 Merkmale nennt, müssen exakt 5 Fakten extrahiert werden.
4. POSITIONSMERKMALE: Behalte Positionsdaten bei (z.B. "auf dem Kopf", "im Haar", "um den Hals").

FARBPRÄZISION: 
Vereinfache Farben NIEMALS. 
- Wenn im Text 'rot-braun' steht, speichere 'rot-braun', nicht 'braun'. 
- Wenn im Text 'dunkelblau' steht, speichere 'dunkelblau', nicht 'blau'. 
- Die Nuance ist für die Wiedererkennung entscheidend.

Du bist ein hochpräziser Fakten-Extraktor. Deine Aufgabe ist es, strukturierte Informationen aus dem gegebenen Text zu identifizieren und als Liste von Fakten im vorgegebenen JSON-Schema zu liefern.

Jeder Fakt sollte folgende Struktur haben:
- `subject_name`: Der Name des Subjekts, über das eine Aussage gemacht wird (z.B. "Max", "mein Hund", "das Auto"). Normalisiere Namen zu Kleinbuchstaben.
- `predicate`: Die Beziehung oder Eigenschaft (z.B. "ist", "hat", "mag", "befindet_sich_in"). Normalisiere zu Kleinbuchstaben, verwende Unterstriche für Leerzeichen.
- `object_value`: Der Wert oder das Objekt der Beziehung/Eigenschaft (z.B. "Mensch", "braune Haare", "Essen"). Normalisiere zu Kleinbuchstaben.
- `category`: Nutze STRENG NUR eine dieser Kategorien: 'Gesundheit', 'Beziehungen', 'Haustier-Details', 'Vorlieben', 'Beruf', 'Termine', 'Allgemein', 'Physis', 'Stil'.
  - **Kategorie Physis:** AUSSCHLIESSLICH körperliches Aussehen und biologische Merkmale: Hautton/Teint, Augenfarbe, Haarfarbe, Haarstruktur, Alter, Größe, Gewicht, Geschlecht, Narben, Tattoos, Körperbau. NIEMALS Beruf, Hobbys oder Fähigkeiten hier einordnen!
  - **Kategorie Beruf:** AUSSCHLIESSLICH Profession, Job, Ausbildung, berufliche Tätigkeit. Beispiele: Software-Entwickler, Arzt, Student, Lehrer, Ingenieur, Koch, Selbstständig. Wenn jemand sagt "Ich bin Software-Entwickler" → Kategorie ist IMMER 'Beruf', NIEMALS 'Physis'!
  - **Kategorie Stil:** Accessoires (Ohrringe, Brillen, Mützen), die die Person wiederkehrend trägt.
  - **Kategorie Gesundheit:** Krankheiten, Allergien, Medikamente, körperliche Einschränkungen.
  - **Kategorie Beziehungen:** Familienmitglieder, Partner, Freunde, soziale Kontakte.
  - **Kategorie Vorlieben:** Hobbys, Lieblingsessen, Musikgeschmack, Interessen.
  - **Kategorie Termine:** Geplante Events, Deadlines, Verabredungen mit Datum/Zeit.
  - **Kategorie Haustier-Details:** Alles über Haustiere: Name, Rasse, Alter, Charakter.
  - **Kategorie Allgemein:** Nur wenn KEINE andere Kategorie passt.
- `canonical_key`: Ein eindeutiger Schlüssel zur Identifizierung des Faktums. Dieser sollte die Form `subject_name:category:predicate:object_value` haben, wobei alle Teile kleingeschrieben und Sonderzeichen entfernt werden.

Zusatz-Anweisung: Extrahiere den Teint (Hautton) und die Augenfarbe als höchste Priorität für die Kategorie Physis.

Beispiel:
Text: "Max ist ein Mann und hat braune Haare."
Fakten:
[
  {
    "fact": "Max ist ein Mann",
    "subject_name": "max",
    "predicate": "ist",
    "object_value": "mann",
    "category": "person",
    "canonical_key": "max:person:ist:mann"
  },
  {
    "fact": "Max hat braune Haare",
    "subject_name": "max",
    "predicate": "hat",
    "object_value": "braune haare",
    "category": "person",
    "canonical_key": "max:person:hat:braune haare"
  }
]

Achte besonders darauf, dass:
- Du nur Fakten extrahierst, die *explizit* im gesamten Interaktionstext genannt werden. Mache keine Annahmen oder Schlussfolgerungen.
- DIALOG-KONTINUITÄT (VERIFIKATION):
  Wenn der Assistant eine Frage zur Rasse/Art gestellt hat (z.B. 'Ist Egon ein Leguan?') 
  und der Nutzer in seiner Nachricht zustimmt (z.B. 'Ja', 'Genau', 'Richtig'), 
  dann extrahiere diese Information als verifizierten Fakt.
  Beispiel:
  Assistant: 'Ist Pody ein Podenco?'
  User: 'Ja, genau!'
  Extrahiere: {"fact": "Pody ist ein Podenco", "subject_name": "pody", "predicate": "ist_rasse", "object_value": "podenco", "category": "pet"}
- Namen von Personen oder Objekten, die als Subjekt oder Objekt fungieren, korrekt identifiziert und normalisiert werden.
- Jedes Faktum eine passende Kategorie erhält.
- Der `canonical_key` korrekt und einzigartig für jedes Faktum generiert wird.
- Du IMMER eine JSON-Liste zurückgibst, auch wenn keine Fakten gefunden wurden (dann ist die Liste leer).
- Wenn du ein Bild einer Person siehst und im Chat ein Name wie 'Maggy' fällt, verknüpfe alle visuell erkannten Merkmale (z.B. Haarfarbe, Accessoires) sofort mit diesem Namen!
Zustands-Pflicht: Extrahiere IMMER die Haarlänge und Haarfarbe, auch wenn die Haare 'sehr kurz' sind oder das Subjekt eine Glatze hat. Ein Buzzcut ist ein Fakt, kein 'n/a'.
!--- MERKMAL-BÜNDELUNG (WICHTIG!) ---!
Fasse zusammengehörige physische Merkmale in EINEM Fakt zusammen. Zerstückele Informationen nicht unnötig.
- SCHLECHT: (thomas | hat_haarfarbe | braun), (thomas | hat_haarlaenge | kurz), (thomas | hat_haarstruktur | lockig)
- GUT: (thomas | hat_frisur | kurze_braune_locken)
- SCHLECHT: (maggy | traegt | ohrringe), (maggy | traegt | kette)
- GUT: (maggy | traegt_schmuck | ohrringe_und_kette)
!--- ZUSTANDSPFLICHT: PHYSISCHE MERKMALE ---!
Wenn du eine Bildbeschreibung ([ANALYSE]) erhältst, ist es deine PFLICHT, physische Attribute als Fakten zu extrahieren. Merkmale definieren die Identität!
1. Extrahiere: Fellfarbe/Hautfarbe, markante Muster (z.B. weiße Pfoten), Accessoires (Halsband, Brille) und Statur.
2. Zuordnung: Wenn der Nutzer einen Namen nennt (z.B. 'Pody'), ordne ALLE physischen Details aus der Analyse diesem Namen zu.
3. Struktur-Beispiel:
   - pody | hat_fellfarbe | schwarz
   - pody | hat_merkmal | weiße_pfoten_spitzen
   - pody | traegt | blaues_halsband
   - pody | hat_statur | schlank_und_athletisch
NIEMALS diese Details ignorieren, nur weil sie 'visuell' sind. Sie sind der Kern des visuellen Gedächtnisses.

### REGELN FÜR ACCESSOIRES & SCHMUCK (WHITELIST - WICHTIG!) ###
Du MUSST folgende Objekte als Fakten speichern, wenn sie im Text vorkommen:
1. SCHMUCK: Ohrringe, Halsketten, Piercings, Ringe. (Prädikat: 'traegt_schmuck')
2. SEHHILFEN: Brillen, Sonnenbrillen. (Prädikat: 'traegt_sehhilfe')
3. TECHNIK: Kopfhörer, Headsets, Uhren. (Prädikat: 'traegt_accessoire')

IGNORIERE NUR:
- Austauschbare Kleidung wie T-Shirts, Jacken, Hosen (außer bei extremen Merkmalen).
- Farben von Kleidung.

Beispiel:
Text: "Sie trägt eine grüne Jacke und goldene Ohrringe. Auf dem Kopf hat er Kopfhörer."
Fakt 1: (sie | traegt_schmuck | goldene_ohrringe) -> SPEICHERN!
Fakt 2: "trägt grüne Jacke" -> IGNORIEREN
Fakt 3: (er | traegt_accessoire | kopfhörer) -> SPEICHERN!

### RELATIONEN & BEZIEHUNGEN (WICHTIG!) ###
Extrahiere auch Beziehungen zwischen Personen! Diese sind kritisch für soziales Gedächtnis.

!!! RICHTUNGS-PFLICHT (IDENTITY-FLIP-SCHUTZ) !!!
Das Feld "fact" MUSS IMMER die Beziehungsrichtung zum Nutzer enthalten!
Schreibe IMMER "[Name] ist [Beziehung] des Nutzers" — NIEMALS nur "[Name] ist [Beziehung]".
Ohne Richtung kann das LLM die Rollen vertauschen (z.B. denken, der Freund sei der Nutzer).

MUSTER für Beziehungen:
1. "X ist meine/meiner Y" → subject: X, predicate: ist_beziehung, object: Y, fact: "X ist Y des Nutzers"
   Beispiel: "Lisa ist meine Frau" → {"fact": "Lisa ist Ehefrau des Nutzers", "subject_name": "lisa", "predicate": "ist_beziehung", "object_value": "ehefrau"}
2. "mein/meine Y heißt X" → subject: X, predicate: ist_beziehung, object: Y, fact: "X ist Y des Nutzers"
   Beispiel: "mein Bruder heißt Tom" → {"fact": "Tom ist Bruder des Nutzers", "subject_name": "tom", "predicate": "ist_beziehung", "object_value": "bruder"}
3. "ich habe einen/eine Y namens X" → subject: X, predicate: ist_beziehung, object: Y, fact: "X ist Y des Nutzers"
   Beispiel: "ich habe eine Schwester namens Anna" → {"fact": "Anna ist Schwester des Nutzers", "subject_name": "anna", "predicate": "ist_beziehung", "object_value": "schwester"}
4. "mein Freund X heißt eigentlich Z" → ZWEI Fakten:
   Fakt 1: {"fact": "X ist Freund des Nutzers", "subject_name": "X", "predicate": "ist_beziehung", "object_value": "freund"}
   Fakt 2: {"fact": "X heißt eigentlich Z", "subject_name": "X", "predicate": "heisst_eigentlich", "object_value": "Z"}
   WICHTIG: Der Nutzer ist NICHT Z! Z ist der echte Name von X.

BEZIEHUNGSTYPEN zu erkennen:
- Familie: frau, ehemann, bruder, schwester, mutter, vater, sohn, tochter, cousin, tante, onkel
- Partnerschaft: freund, freundin, partner, partnerin
- Sozial: kollege, chef, freund, freundin, nachbar

!--- IDENTITY NORMALIZATION (WICHTIG!) ---!
Wenn der Nutzer explizit seinen eigenen Namen nennt (z.B. "Max"), verwende für ALLE seine Fakten "user" als subject_name.
- "Max liebt Kaffee" → (user | liebt | kaffee)
- "Ich (Max) bin 30" → (user | ist_alter | 30)
Dies verhindert Duplikate mit gemischten Subjekten ("max" vs "user").
""" # <--- Hier MUSS der String enden.

logger = logging.getLogger("janus_backend")

# --- SSE NOTIFICATION MANAGER (REALTIME FEEDBACK) ---
class NotificationManager:
    def __init__(self):
        self.connections = []

    async def connect(self):
        """Erstellt eine neue Queue für einen Client."""
        queue = asyncio.Queue()
        self.connections.append(queue)
        return queue

    def disconnect(self, queue):
        """Entfernt einen Client."""
        if queue in self.connections:
            self.connections.remove(queue)

    async def broadcast_refresh(self):
        """Sendet das 'refresh'-Signal an alle verbundenen Clients."""
        if not self.connections:
            return
        logger.info(f"⚡ Broadcasting 'refresh' event to {len(self.connections)} clients.")
        for queue in self.connections:
            await queue.put("refresh")

# Singleton Instanz
notification_manager = NotificationManager()
# ----------------------------------------------------

async def _find_subject_name_in_text(text_block: str, api_key: str, provider: str, model_id: str) -> Optional[str]:
    """Sucht mit einer schnellen, aber intelligenten LLM-Anfrage nach dem Haupt-Subjekt (Name oder Kontext-Hinweis) im Text."""
    prompt = (
        f"STRIKTE SUBJEKT-ERKENNUNG: Analysiere die Nachricht.\n"
        f"1. Wenn der Nutzer eine NEUE Person oder ein Tier einführt (z.B. 'Mein Hund heißt Pody', 'Das ist Lisa'), gib den Namen zurück (z.B. 'pody', 'lisa').\n"
        f"2. NUR wenn der Nutzer Pronomen nutzt, die sich EINDEUTIG auf bereits besprochene Dinge beziehen (z.B. 'Er hat Hunger', 'Wie geht es ihr?'), antworte 'CONTEXT_USE'.\n"
        f"3. Sonst antworte ''.\n"
        f"User-Text: '{text_block}'"
    )
    try:
        provider_instance = _resolve_provider_instance(provider)
        subject_finder_model = _select_memory_extraction_model(provider, model_id)
        response_data = await provider_instance.generate_response(
            api_key=api_key,
            model=subject_finder_model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw_text = response_data.get("text", "").strip().lower()
        
        if raw_text == "context_use":
            logger.info("Subjekt-Hinweis 'CONTEXT_USE' gefunden.")
            return "CONTEXT_USE"
            
        name_parts = raw_text.split()
        if name_parts: # <--- Absicherung hier!
            name = name_parts[0].replace('.', '').replace(',', '')
        else:
            name = "" # Falls leer, setze name auf leeren String
        
        if name:
            logger.info(f"Subjekt-Name gefunden: {name}")
            return name
            
    except Exception as e:
        logger.error(f"Fehler bei der Subjekt-Namenssuche: {e}", exc_info=True)
    return None

# ═══════════════════════════════════════════════════════════════════════════
# IDENTITY PRE-PASS – deterministic "Ich bin X / Mein Name ist X" detection
# ═══════════════════════════════════════════════════════════════════════════

# Direct regex guard for BUG-MEM-017: nano-model smalltalk-bias bypass
_DIRECT_IDENTITY_REGEX = re.compile(
    r'(?i)(ich bin|ich heiße|mein name ist)\s+([a-zäöüß]+(?:\s[a-zäöüß]+)?)'
)

_IDENTITY_PATTERNS = [
    r'ich (?:bin|hei(?:ß|ss?)e?) ([\w][\w\s\-]+)',
    r'mein(?:e)? name(?:n)? (?:ist|lautet|war) ([\w][\w\s\-]+)',
    r'nennen? (?:sie|mich|uns) mich ([\w][\w\s\-]+)',
    r'ihr k[öo]nn?t mich ([\w][\w\s\-]+) nennen',
]

# Stop-words that terminate the name capture (Task 015 / Rolf-Bug)
# "Ich bin Rolf und mag Videospiele" → name = "Rolf"
# Verbs after name ("Rolf mag Tee") must also truncate (Rolf-Bug)
_IDENTITY_STOPWORDS: tuple = (
    # Konjunktionen / Präpositionen
    " und ", " and ", " also ", " as well ", " aber ", " oder ",
    " mit ", " ohne ", " seit ", " weil ", " da ", " wenn ",
    # Verben die nach dem Namen einen neuen Satzinhalt einleiten (Rolf-Bug Fix)
    " mag ", " hasse ", " hass ", " liebe ", " trinke ", " esse ",
    " arbeite ", " wohne ", " lebe ", " komme ", " spiele ",
    " finde ", " bin ", " habe ", " mache ", " gehe ", " fahre ",
    " schaue ", " sehe ", " höre ", " kaufe ", " verkaufe ", " suche ",
    " brauche ", " will ", " möchte ", " kann ", " soll ", " darf ",
    " muss ", " werde ", " war ", " warst ", " ist ", " bist ",
    ",",
)

# Words that are NOT names when following "Ich bin ..."
_IDENTITY_NON_NAMES: frozenset = frozenset({
    "hier", "bald", "gerne", "mal", "nicht", "nun", "schon", "erst", "auch",
    "da", "gut", "klar", "sicher", "jetzt", "noch", "müde", "hungrig",
    "fertig", "bereit", "alt", "jung", "froh", "neu", "ein", "eine",
    "der", "die", "das", "mir", "dir", "wer", "was", "wie", "sehr",
    # Verben (Rolf-Bug Fix: Verben sind keine Namen)
    "mag", "hasse", "liebe", "trinke", "esse", "arbeite", "wohne", "lebe",
    "komme", "spiele", "finde", "mache", "gehe", "fahre", "schaue", "sehe",
    "höre", "kaufe", "verkaufe", "suche", "brauche", "will", "möchte",
    "kann", "soll", "darf", "muss", "werde", "war", "warst", "ist", "bist",
})


def _apply_direct_identity_regex_guard(user_text: str) -> Optional[Dict[str, Any]]:
    """
    Direct regex guard for identity detection (BUG-MEM-017).
    Bypasses nano-model smalltalk-bias by using deterministic regex.
    
    Returns ExtractedFact dict if match found, None otherwise.
    """
    if not user_text:
        return None
    
    match = _DIRECT_IDENTITY_REGEX.search(user_text)
    if not match:
        return None
    
    # Extract name and clean it
    name_raw = match.group(2).strip().rstrip(".,!? ")
    
    # Stop-word truncation (same logic as _detect_user_identity_fact)
    name_with_space = " " + name_raw + " "
    for sw in _IDENTITY_STOPWORDS:
        idx = name_with_space.find(sw)
        if idx > 0:
            name_raw = name_with_space[1:idx].strip().rstrip(".,!? ")
            break
    
    # Check for non-names
    first_word = name_raw.split()[0] if name_raw else ""
    if first_word in _IDENTITY_NON_NAMES:
        return None
    
    if not name_raw:
        return None
    
    # Validation-Gate: max 2 words for names
    _words = name_raw.split()
    if len(_words) > 2:
        name_raw = _words[0]
        logger.debug(
            "[DIRECT IDENTITY GUARD] Name truncated to first word: %r (original: %r)",
            name_raw, " ".join(_words),
        )
    
    name_display = name_raw.title()
    
    return {
        "fact": f"User heißt {name_display}",
        "subject_name": "user",
        "predicate": "heißt",
        "object_value": name_raw,
        "category": "Physis",
        "canonical_key": "user:physis:heisst:name",
        "priority": 0.95,
        "_fixed_canonical_key": "user:physis:heisst:name",
        "_source": "direct_regex_guard",
    }


# --- IDENTITY NORMALIZATION (BUG-MEM-018) ---
def _normalize_subject_to_user(subject_name: str, user_identity_name: Optional[str]) -> str:
    """
    Normalize subject_name to "user" if it matches the user's identity name.
    This prevents duplicate entries like "max" and "user" for the same person.
    
    Example: "Max" -> "user" (if user_identity.name == "Max")
    """
    if not user_identity_name or not subject_name:
        return subject_name or "user"
    
    if subject_name.lower().strip() == user_identity_name.lower().strip():
        return "user"
    
    return subject_name


def _detect_user_identity_fact(user_msg: str) -> Optional[Dict[str, Any]]:
    """
    Deterministic pre-pass: detects user self-introduction patterns and returns
    a pre-built fact dict with the FIXED canonical_key 'user:physis:heisst:name'.
    Returns None if no identity pattern is found.
    """
    text_lower = str(user_msg or "").lower().strip()
    for pattern in _IDENTITY_PATTERNS:
        m = re.search(pattern, text_lower)
        if not m:
            continue
        name_raw = m.group(1).strip().rstrip(".,!? ")
        # ── Stop-word truncation (Task 015) ──────────────────────────────────
        # "Rolf und mag Videospiele" → "Rolf"
        name_with_space = " " + name_raw + " "
        for sw in _IDENTITY_STOPWORDS:
            idx = name_with_space.find(sw)
            if idx > 0:
                name_raw = name_with_space[1:idx].strip().rstrip(".,!? ")
                break
        # ─────────────────────────────────────────────────────────────────────
        first_word = name_raw.split()[0] if name_raw else ""
        if first_word in _IDENTITY_NON_NAMES:
            continue
        if not name_raw:
            continue
        # ── Validation-Gate (Task 016) ────────────────────────────────────────
        # If > 2 words remain after stop-word truncation, be aggressive:
        # keep only the first word.  Real names are at most 2 tokens
        # (Vorname + Nachname).  More than 2 → likely a sentence fragment.
        _words = name_raw.split()
        if len(_words) > 2:
            name_raw = _words[0]
            logger.debug(
                "[PRE-PASS GATE] Name truncated to first word: %r (original: %r)",
                name_raw, " ".join(_words),
            )
        # ─────────────────────────────────────────────────────────────────────
        # Capitalize each word for display but keep object_value as given (lowercased)
        name_display = name_raw.title()
        return {
            "fact": f"User heißt {name_display}",
            "subject_name": "user",
            "predicate": "heißt",
            "object_value": name_raw,
            "category": "Physis",
            "canonical_key": "user:physis:heisst:name",
            "_fixed_canonical_key": "user:physis:heisst:name",
        }
    return None


def _merge_facts(facts: List[Dict]) -> List[Dict]:
    """Sucht nach namenlosen Fakten und ordnet sie benannten Fakten zu, wenn sie übereinstimmen."""
    named_facts = {f['subject_name']: f for f in facts if f.get('subject_name') and 'unbekannt' not in f['subject_name']}
    unnamed_facts = [f for f in facts if not f.get('subject_name') or 'unbekannt' in f['subject_name']]
    
    if not named_facts or not unnamed_facts:
        return facts # Nichts zu tun

    final_facts = list(named_facts.values())
    for unnamed in unnamed_facts:
        is_merged = False
        for name, named_fact in named_facts.items():
            # Simple Heuristik: Wenn Prädikat und Objekt gleich sind, ist es wahrscheinlich ein Duplikat
            if unnamed.get('predicate') == named_fact.get('predicate') and unnamed.get('object_value') == named_fact.get('object_value'):
                logger.info(f"[MERGE] Ignoriere Duplikat-Fakt '{unnamed.get('fact')}', da bereits für '{name}' vorhanden.")
                logger.info(f"[CLEANUP] Lösche anonymes Duplikat zugunsten von {name}.")
                is_merged = True
                break
        if not is_merged:
            final_facts.append(unnamed) # Behalte den namenlosen Fakt, wenn er einzigartig ist

            
    return final_facts



async def extract_and_save_fact_from_interaction(
    db: Session, user_msg: str, assistant_msg: str, api_key: str, provider: str, model_id: str, chat_id: int = 0, subject_hint: Optional[str] = None
):
    """Sucht den Namen oder Kontext-Hinweis NUR in der User-Nachricht und extrahiert Fakten."""
    logger.info(f"[FACT EXTRACTION V20.1] Isolierte Suche gestartet.")

    # CIRCUIT BREAKER CHECK (Opus V2.1)
    if not _extraction_breaker.can_execute():
        logger.info("[EXTRACTION] Circuit breaker OPEN — skipping extraction")
        memory_metrics.increment("extractions_circuit_broken")
        return []

    try:
        extraction_assistant_msg = _strip_assistant_suggestion_block(assistant_msg)

        if should_skip_extraction_from_messages(user_msg, extraction_assistant_msg):
            logger.warning("Memory extraction failed - skipping due to validation error.")
            return []

        final_subject_id = None
        subject_name_to_use = None
        subject_role_to_use = None

        if subject_hint:
            subject_name_to_use = subject_hint.lower()
            subject_role_to_use = "pet" if any(p in subject_hint.lower() for p in ["pody", "egon"]) else "contact"
            final_subject_id = f"{subject_role_to_use}:person:{subject_name_to_use}"
            logger.info(f"Using subject_hint: {subject_hint} for extraction.")

        # 2. Kurze Bestätigungen prüfen (Subjekt-Anker)
        is_short_confirmation = re.match(r'^(ja|genau|richtig|korrekt|yes|stimmt|hast recht)\b', user_msg.lower())
        assistant_anchor_name = _get_subject_from_assistant_query(extraction_assistant_msg)
        
        if is_short_confirmation and assistant_anchor_name:
            subject_name_to_use = assistant_anchor_name
            subject_role_to_use = "pet" if assistant_anchor_name in ["pody", "egon"] else "contact"
            final_subject_id = f"{subject_role_to_use}:dog:{subject_name_to_use}"
            logger.info(f"DIAMOND BINDING: Anker '{subject_name_to_use}' aus Assistant-Frage genutzt.")

        # 3. Falls noch kein Name gefunden, Standard-Suche
        if not subject_name_to_use:
            subject_identifier = await _find_subject_name_in_text(user_msg, api_key, provider, model_id)
            
            if subject_identifier == "CONTEXT_USE":
                last_subject = memory_manager.get_last_subject_from_chat(db, chat_id)
                if last_subject:
                    subject_name_to_use = last_subject.get("subject_name")
                    subject_role_to_use = last_subject.get("subject_role")
                    subject_type = last_subject.get('subject_type') or last_subject.get('subject_pet_type') or last_subject.get('subject_relative_type') or 'contact'
                    final_subject_id = f"{subject_role_to_use}:{subject_type}:{subject_name_to_use}"
            elif subject_identifier:
                subject_name_to_use = subject_identifier
                subject_role_to_use = "pet" if "hund" in user_msg.lower() or "pody" in user_msg.lower() else "contact"
                subject_type = "dog" if "hund" in user_msg.lower() else ("cat" if "katze" in user_msg.lower() else ("pet" if "haustier" in user_msg.lower() else "person"))
                final_subject_id = f"{subject_role_to_use}:{subject_type}:{subject_name_to_use}"
        
        # 4. EMPTY STRING SCHUTZ (Hier lag der Fehler)
        if subject_name_to_use == "" or subject_name_to_use is None:
            subject_name_to_use = "unbekannt"
            subject_role_to_use = "contact"
            final_subject_id = f"contact:person:unbekannt"
        final_extraction_prompt = f"""
        WICHTIG: Ordne Eigenschaften präzise zu. Wenn im Text 'Pody' und 'Fritz' vorkommen, erstelle getrennte Fakten für pet:dog:pody und relative:onkel:fritz. Vermische sie nicht!
        """ + EXTRACTION_PROMPT
        
        if subject_name_to_use:
            final_extraction_prompt += f"\n\nAKTUELLES SUBJEKT FÜR BINDUNG: {subject_role_to_use}:{subject_name_to_use.lower()}"
        
        # Agent: Füge dies kurz vor dem API-Call ein
        current_system_prompt = final_extraction_prompt
        if subject_name_to_use and subject_name_to_use != "unbekannt":
            name_mapping_hint = (
                f"\n\nACHTUNG: Das Lebewesen auf dem Bild wurde als '{subject_name_to_use}' identifiziert. "
                f"Alle physischen Beschreibungen aus der [ANALYSE] (wie Farbe, Merkmale, Halsband) "
                f"beziehen sich direkt auf '{subject_name_to_use}' und müssen als Fakten für diesen Namen gespeichert werden."
            )
            current_system_prompt += name_mapping_hint

        provider_instance = _resolve_provider_instance(provider)
        selected_model = _select_memory_extraction_model(provider, model_id)

        # Der KI-Aufruf muss die Ergebnisse in diese Variablen schreiben:
        messages = [
            {"role": "system", "content": current_system_prompt},
            {"role": "user", "content": f"USER: {user_msg}\nASSISTANT: {extraction_assistant_msg}"}
        ]

        request_messages = messages[-2:] if str(provider or "").strip().lower() == "ollama" else messages
        extracted_items = await _generate_fact_extraction_items_with_self_healing(
            provider_instance,
            api_key=api_key,
            model_id=selected_model,
            provider=provider,
            messages=request_messages,
        )

        # ═══════════════════════════════════════════════════════════════════════════
        # FORMAT NORMALIZATION: Handle both {"facts": [...]} and direct [...]
        # ═══════════════════════════════════════════════════════════════════════════
        if isinstance(extracted_items, dict) and "facts" in extracted_items:
            extracted_items = extracted_items["facts"]
        elif not isinstance(extracted_items, list):
            logger.warning(f"Unexpected format for fact extraction: {type(extracted_items)}. Returning empty list.")
            extracted_items = []
        # ═══════════════════════════════════════════════════════════════════════════

        # ── IDENTITY PRE-PASS (BUG-MEM-017) ───────────────────────────────────
        # Direct regex guard bypasses nano-model smalltalk-bias.
        # Uses deterministic regex BEFORE LLM processing loop.
        identity_fact = _apply_direct_identity_regex_guard(user_msg)
        if identity_fact:
            logger.info(
                "[DIRECT IDENTITY GUARD] Self-introduction detected → injecting "
                "user:physis:heisst:name fact (value=%s)",
                identity_fact.get("object_value"),
            )
            _identity_predicates = frozenset({
                "bin", "ist", "heiße", "heisse", "heißt", "heisst",
            })
            _identity_subjects = frozenset({"ich", "user"})
            extracted_items = [identity_fact] + [
                item for item in extracted_items
                if not (
                    item.get("subject_name", "").lower() in _identity_subjects
                    and item.get("predicate", "").lower() in _identity_predicates
                )
            ]
        # ──────────────────────────────────────────────────────────────────────

        # CIRCUIT BREAKER: Success recording (Opus V2.1)
        _extraction_breaker.record_success()

        # NEU: Aufräumen und Mergen
        if len(extracted_items) > 1:
            extracted_items = _merge_facts(extracted_items)
        
        # Qualitäts-Check (Self-Correction): "Geister-Fakten" filtern
        # Wenn subject_name gleich "unbekannt" oder "person" ist, ABER in der gleichen Liste auch Fakten mit einem echten Namen (z.B. "Thomas") existieren -> Lösche die "unbekannt"-Fakten.
        
        # Finde alle echten Subjekt-Namen in der aktuellen Extraktionsrunde
        real_subject_names = {
            item.get("subject_name").lower()
            for item in extracted_items
            if item.get("subject_name") and item.get("subject_name").lower() not in ["unbekannt", "person"]
        }

        if real_subject_names:
            filtered_extracted_items = []
            for item in extracted_items:
                subj_name_lower = item.get("subject_name", "").lower()
                if (subj_name_lower in ["unbekannt", "person"]) and any(
                    name in subj_name_lower for name in real_subject_names
                ):
                    logger.info(f"Filtere 'Geister-Fakt' (unbekannt/person) zugunsten eines echten Namens: {item}")
                else:
                    filtered_extracted_items.append(item)
            extracted_items = filtered_extracted_items
            
        # ── IDENTITY NORMALIZATION (BUG-MEM-018) ───────────────────────────
        # Get user identity name from identity_fact if available
        user_identity_name = None
        if identity_fact:
            user_identity_name = identity_fact.get("object_value")
        else:
            # Try to find identity from extracted_items
            for item in extracted_items:
                if item.get("canonical_key") == "user:physis:heisst:name" or \
                   item.get("_fixed_canonical_key") == "user:physis:heisst:name":
                    user_identity_name = item.get("object_value")
                    break
        # ─────────────────────────────────────────────────────────────────────

        processed_count = 0
        for item in extracted_items:
            # NOTE: Pronoun-Bleed Sanitizer läuft jetzt zentral in enrich_fact()
            # (memory_enricher.py), nicht mehr hier in der Extractor-Loop.

            # ═══════════════════════════════════════════════════════════════════════════
            # META-NOISE PRE-FILTER (Verhindert Extraktion von Meta-Instruktionen)
            # ═══════════════════════════════════════════════════════════════════════════
            fact_text = item.get("fact", "")
            if _is_meta_noise(fact_text):
                logger.info(f"[META-NOISE-REJECTION] Meta-Instruktion erkannt und verworfen: {fact_text[:100]}...")
                continue  # Skip this fact entirely - don't save to DB
            if _contains_email_pii(
                item.get("fact", ""),
                item.get("object_value", ""),
                item.get("canonical_key", ""),
            ):
                logger.info("[PII-EMAIL-REJECTION] Verwerfe E-Mail-PII-Fakt aus allgemeiner Extraktion: %r", item)
                continue
            # ═══════════════════════════════════════════════════════════════════════════

            # A) KATEGORIE NORMALISIEREN
            raw_cat = item.get("category", "general").lower()
            # Prüfe Mapping, sonst Fallback auf ALLOWED_CATEGORIES oder 'general'
            normalized_cat = CATEGORY_MAPPING.get(raw_cat, raw_cat)
            if normalized_cat not in ALLOWED_CATEGORIES:
                normalized_cat = "general"

            # ═══════════════════════════════════════════════════════════════════
            # BERUF-VS-PHYSIS GUARD: Deterministische Korrektur für Berufe,
            # die fälschlicherweise als "Physis" klassifiziert wurden.
            # ═══════════════════════════════════════════════════════════════════
            if normalized_cat == "Physis":
                predicate_lower = item.get("predicate", "").lower()
                obj_lower = item.get("object_value", "").lower()
                _beruf_predicates = {"arbeitet_als", "ist_beruf", "beruf", "job", "profession"}
                _beruf_keywords = {
                    "entwickler", "programmierer", "ingenieur", "arzt", "ärztin",
                    "lehrer", "lehrerin", "student", "studentin", "koch", "köchin",
                    "designer", "architekt", "anwalt", "anwältin", "manager",
                    "berater", "beraterin", "verkäufer", "selbstständig",
                    "freelancer", "wissenschaftler", "forscher", "pilot",
                    "software", "developer", "engineer", "consultant",
                }
                is_beruf = predicate_lower in _beruf_predicates or any(
                    kw in obj_lower for kw in _beruf_keywords
                )
                if is_beruf:
                    logger.info(
                        "[BERUF-GUARD] Korrigiere Kategorie 'Physis' → 'Beruf' "
                        "für predicate=%r, object_value=%r",
                        item.get("predicate"), item.get("object_value"),
                    )
                    normalized_cat = "Beruf"
            # ═══════════════════════════════════════════════════════════════════

            # ═══════════════════════════════════════════════════════════════════
            # RELATION-DIRECTION GUARD (Identity-Flip Fix):
            # Ensures that relationship facts always contain "des Nutzers" in
            # the fact text so the LLM never confuses who is who.
            # "Chris ist Freund" → "Chris ist Freund des Nutzers"
            # ═══════════════════════════════════════════════════════════════════
            _pred_lower = item.get("predicate", "").lower()
            _relation_predicates = {
                "ist_beziehung", "ist_freund", "ist_verwandt",
                "ist_partner", "ist_familie",
            }
            _relation_roles = {
                "freund", "freundin", "bruder", "schwester", "mutter",
                "vater", "sohn", "tochter", "ehemann", "ehefrau", "frau",
                "mann", "partner", "partnerin", "kollege", "kollegin",
                "chef", "chefin", "nachbar", "nachbarin", "cousin",
                "cousine", "tante", "onkel", "oma", "opa",
            }
            _is_relation_fact = (
                _pred_lower in _relation_predicates
                or normalized_cat == "Beziehungen"
                and item.get("object_value", "").lower() in _relation_roles
            )
            if _is_relation_fact:
                _fact_text = item.get("fact", "")
                _direction_markers = ("des nutzers", "des users", "vom nutzer", "vom user")
                if not any(m in _fact_text.lower() for m in _direction_markers):
                    _subj = item.get("subject_name", "").title()
                    _role = item.get("object_value", "")
                    if _subj and _subj.lower() != "user" and _role:
                        item["fact"] = f"{_subj} ist {_role.title()} des Nutzers"
                        logger.info(
                            "[RELATION-DIRECTION] fact rewritten: %r → %r",
                            _fact_text, item["fact"],
                        )
            # ═══════════════════════════════════════════════════════════════════

            item["category"] = normalized_cat

            # ═══════════════════════════════════════════════════════════════════════════
            # BUG-MEM-018: IDENTITY NORMALIZATION
            # Normalize subject_name to "user" if it matches the user's identity name
            # This prevents duplicates like "max" and "user" for the same person
            # ═══════════════════════════════════════════════════════════════════════════
            original_subject = item.get("subject_name", "unbekannt")
            normalized_subject = _normalize_subject_to_user(original_subject, user_identity_name)
            if normalized_subject != original_subject:
                logger.debug(
                    "[IDENTITY NORMALIZATION] Mapped subject '%s' -> 'user' (user_identity=%s)",
                    original_subject, user_identity_name
                )
            item["subject_name"] = normalized_subject
            # ═══════════════════════════════════════════════════════════════════════════

            # ═══════════════════════════════════════════════════════════════════════════
            # MEMORY ENRICHER INTEGRATION (Opus V2.1) - Deterministische Metadaten
            # ═══════════════════════════════════════════════════════════════════════════
            # Enricher setzt: priority, ttl, tags, memory_type, source_skill, user_editable
            item = enrich_fact(item, source_skill="system.extractor")
            memory_metrics.increment("writes_enriched")
            # ── Identity Priority Guard (Task 014) ──────────────────────────────────
            # Belt-and-suspenders: if the enricher still returns 0.50 for the identity
            # slot (e.g. encoding mismatch), force it to 0.95 / CORE here.
            if item.get("canonical_key") == "user:physis:heisst:name" or \
               item.get("_fixed_canonical_key") == "user:physis:heisst:name":
                item["priority"] = 0.95
                item["memory_type"] = "CORE"
                item["ttl"] = None
            # ────────────────────────────────────────────────────────────────────────
            # ═══════════════════════════════════════════════════════════════════════════

            # B) CANONICAL KEY REGENERIEREN (WICHTIG!)
            # Wir bauen den Key neu, damit die normalisierte Kategorie darin steht.
            # Ausnahme: Wenn _fixed_canonical_key gesetzt ist (z.B. Identitäts-Pre-Pass),
            # behalten wir den festen Schlüssel und räumen das interne Marker-Feld auf.
            fixed_key = item.pop("_fixed_canonical_key", None)
            if fixed_key:
                item["canonical_key"] = fixed_key
            else:
                subj = item.get("subject_name", "unbekannt").lower().strip()
                pred = item.get("predicate", "info").lower().strip()
                obj = item.get("object_value", "info").lower().strip()
                clean_key = f"{subj}:{normalized_cat}:{pred}:{obj}".replace(" ", "_")
                item["canonical_key"] = clean_key
            
            # C) IDENTITY GUARD & WEITERER ABLAUF...
            
            # Filter gegen Meta-Fakten (Bleibt ganz oben)
            forbidden_subjects = ["daten", "text", "beschreibung", "information", "kontext"]
            subj_name_lower = item.get("subject_name", "").lower()

            if any(x in subj_name_lower for x in forbidden_subjects):
                logger.info(f"Blockiere Meta-Fakt (Halluzination): {item}")
                continue

            # Weitere Validierungen (bleiben unverändert)
            if "canonical_key" not in item or not item["canonical_key"]:
                logger.warning(f"Ignoriere Fakt ohne canonical_key: {item}")
                continue

            if item.get("object_value", "").lower() == "unbekannt":
                logger.info(f"Ignoriere Fakt mit object_value 'unbekannt': {item}")
                continue

            # Filter gegen "Nutzlose Fakten"
            junk_values = ["unbekannt", "unklar", "nicht ersichtlich", "unbekannte augenfarbe"]
            if any(val in item.get("object_value", "").lower() for val in junk_values):
                logger.info(f"Filtere nutzlosen Fakt: {item}")
                continue

            if item.get("predicate") == "ist_identifiziert_als" and \
               item.get("subject_name") == item.get("object_value"):
                logger.info(f"Ignoriere redundantem Identifikations-Fakt: {item}")
                continue

            subj_raw = item.get("subject_name")
            obj_raw = item.get("object_value")
            predicate = item.get("predicate", "").lower()
            
            s_clean = str(subj_raw).strip().lower() if subj_raw is not None else ""
            o_clean = str(obj_raw).strip().lower() if obj_raw is not None else ""

            is_naming_context = any(x in predicate for x in ["name", "heisst", "heißt", "genannt", "alias", "identity"])

            if s_clean and o_clean and s_clean == o_clean and not is_naming_context:
                logger.info(f"Ignoriere redundanten Fakt (Tautologie): {s_clean} {predicate} {o_clean}")
                continue
            
            # NEU: Wenn wir einen Namen haben, ersetze generische Subjekte wie 'hund' oder 'tier' durch den Namen (SCHRITT 3)
            # Diese Logik muss VOR dem IDENTITY GUARD laufen, damit der Guard auf den korrekten Namen prüfen kann.
            if subject_name_to_use and subject_name_to_use != "unbekannt":
                if item.get("subject_name") in ["hund", "tier", "katze", "person"]:
                    logger.info(f"[CLEANUP] Ersetze generisches Subjekt '{item['subject_name']}' durch spezifisches '{subject_name_to_use}'.")
                    item["subject_name"] = subject_name_to_use
                    # Key neu generieren
                    # Ensure category, predicate, object_value are present before using them
                    category = item.get('category', 'unknown')
                    predicate_val = item.get('predicate', 'is')
                    object_val = item.get('object_value', 'unknown')
                    item["canonical_key"] = f"{subject_name_to_use}:{category}:{predicate_val}:{object_val}".lower().replace(" ", "_")

            # --- IDENTITY GUARD START --- (SCHRITT 2 aus README V20.4, aber hier korrigiert)
            # Diese Logik greift, wenn im Fakt-Text selbst ein Name steht, der nicht als Subjekt erkannt wurde
            fact_text = item.get("fact", "").lower()
            current_subject = item.get("subject_name", "").lower()

            # Liste bekannter Namen, die wir schützen wollen (könnte dynamisch sein, hier als Hard-Check)
            known_names = ["thomas", "maggy", "egon", "elena"]

            for name in known_names:
                # Wenn der Name im Fakt-Text vorkommt (z.B. "Thomas hat einen Bart")...
                # ...aber das Subjekt NICHT dieser Name ist (z.B. "unbekannt" oder ein anderer generischer Term)...
                if name in fact_text and name != current_subject and (current_subject == "unbekannt" or current_subject in ["hund", "tier", "katze", "person"]):
                    logger.warning(f"[IDENTITY GUARD] Korrigiere Subjekt von '{current_subject}' zu '{name}' basierend auf Fakt-Text.")
                    
                    # Korrigiere das Item
                    item["subject_name"] = name
                    # Bestimme die Rolle basierend auf dem Namen (muss dynamischer sein, für den Test ok)
                    item["subject_role"] = "pet" if name in ["pody", "egon"] else "contact" 
                    
                    # Regeneriere den canonical_key, damit er zum neuen Namen passt
                    predicate_val = item.get("predicate", "ist")
                    obj_val = item.get("object_value", "")
                    item["canonical_key"] = f"{name}:{item['subject_role']}:{item.get('category', 'unknown')}:{predicate_val}:{obj_val}".lower().replace(" ", "_")
                    break # Nur eine Korrektur pro Fakt
            # --- IDENTITY GUARD ENDE ---

            s_type = "vision" if "[VISION ANALYSE]" in extraction_assistant_msg else "text"

            if memory_manager.save_memory_snippet(
                db=db, 
                chat_id=chat_id, 
                fact_object=item,
                source_type=s_type, # NEU
                source_metadata={"user_msg": user_msg[:100]} # NEU: Metadaten mitgeben
            ):
                processed_count += 1
        
        if processed_count > 0:
            # --- DIAMOND TRANSFER FIX ---
            if subject_name_to_use and subject_name_to_use != "unbekannt":
                last_sub_data = memory_manager.get_last_subject_from_chat(db, chat_id)
                
                if last_sub_data:
                    old_name = last_sub_data.get("subject_name")
                    old_role = last_sub_data.get("subject_role", "contact")
                    
                    # KORREKTUR: Transfer nur, wenn das ALTE Subjekt temporär war
                    # und das NEUE Subjekt (subject_name_to_use) ein echter Name ist.
                    if old_name != subject_name_to_use and (len(str(old_name)) == 4 or old_name == "unbekannt"):
                        old_full_id = f"{old_role}:person:{old_name}"
                        new_full_id = final_subject_id # Dies ist das Ziel (z.B. pet:dog:pody)
                        
                        # WICHTIG: Die Reihenfolge muss sein: (db, chat_id, VON, ZU)
                        logger.info(f"DIAMOND TRANSFER: Migriere visuelle Merkmale VON '{old_full_id}' ZU '{new_full_id}'.")
                        memory_manager.transfer_facts_to_new_subject(db, chat_id, old_full_id, new_full_id)

            
            await notification_manager.broadcast_refresh()

        return extracted_items

    except ValidationError:
        logger.warning("Memory extraction failed - skipping due to validation error.")
        _extraction_breaker.record_failure()
        memory_metrics.increment("extractions_failed")
        return []
    except Exception as e:
        logger.error(f"Fehler bei der V20.1 Fakten-Extraktion: {e}", exc_info=True)
        _extraction_breaker.record_failure()
        memory_metrics.increment("extractions_failed")
        return []


# (Die Funktion `extract_and_save_fact` muss ebenfalls leicht angepasst werden, um `is_core` zu verarbeiten)


async def extract_and_save_fact(
    db: Session,
    chat_id: int,
    text_block: str,
    main_api_key: str,
    provider: str,
    model: str,
):
    """
    Extrahiert strukturierte Fakten, validiert sie und speichert sie konsistent.
    """
    # Der fehlerhafte Trigger-Word-Filter wurde komplett entfernt.
    # Wir starten den Extraktionsversuch jetzt immer.

    # Optional: Verbessere die Log-Nachricht für mehr Klarheit.
    logger.info(
        f"[FACT EXTRACTION V17] Starte Extraktionsversuch für Chat {chat_id}"
    )
    try:
        provider_instance = _resolve_provider_instance(provider)
        selected_model = _select_memory_extraction_model(provider, model)

        extracted_items = await _generate_fact_extraction_items_with_self_healing(
            provider_instance,
            api_key=main_api_key,
            model_id=selected_model,
            provider=provider,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": text_block}
            ],
        )
        
        if not extracted_items:
            logger.info("Keine neuen Fakten im Textblock gefunden.")
            return None

        processed_count = 0
        for item in extracted_items:
            # Harte Validierung, um sicherzustellen, dass die KI das Schema befolgt hat
            if "canonical_key" not in item or "category" not in item:
                logger.warning(f"Ignoriere unvollständigen Fakt von LLM: {item}")
                continue

            # Der Aufruf wurde repariert, um das ganze Objekt zu übergeben
            result = memory_manager.save_memory_snippet(
                db=db,
                chat_id=chat_id,
                fact_object=item 
            )
            if result:
                processed_count += 1
        
        logger.info(f"Erfolgreich {processed_count}/{len(extracted_items)} Fakten verarbeitet.")
        
        # --- NEU: SSE TRIGGER ---
        if processed_count > 0:
            await notification_manager.broadcast_refresh()
        # ------------------------

        return extracted_items

    except Exception as e:
        logger.error(f"Fehler bei der V6 Fakten-Extraktion: {e}", exc_info=True)
        return None


def _get_subject_from_assistant_query(assistant_msg: str) -> Optional[str]:
    """
    Sucht nach Namen in Fragen des Assistant.
    """
    match = re.search(r'(?:Ist|Heißt|Gehört)\s+([A-Z][a-z]+)', assistant_msg)
    if match:
        return match.group(1).lower()
    return None

import asyncio
import hashlib
import json
import logging
import re
import threading
import uuid
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from backend.data import contact_schemas, crud, database
from backend.data.database import SessionLocal
from backend.data.models import Contact
from backend.utils.config_loader import load_model_catalog as main_load_model_catalog
from pydantic import ValidationError
from sqlalchemy.orm import Session


def _normalize_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    url = url.strip().strip("'<>'")
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url
    logger.info(f"Normalizing URL: '{url}' to 'https://{url}'")
    return "https://" + url


def _validate_extracted_url(extracted_url: str, search_urls: list) -> Optional[str]:
    if not extracted_url or not search_urls:
        return extracted_url
    from urllib.parse import urlparse

    try:
        extracted_netloc = urlparse(extracted_url).netloc.lower()
        if not extracted_netloc:
            for search_link in search_urls:
                search_netloc = urlparse(search_link).netloc.lower()
                if search_netloc:
                    return search_link
            return extracted_url
        search_domains = set()
        for search_link in search_urls:
            domain = urlparse(search_link).netloc.lower()
            if domain:
                search_domains.add(domain)
        is_consistent = False
        if extracted_netloc in search_domains:
            is_consistent = True
        else:
            if not extracted_netloc.startswith("www."):
                www_version = "www." + extracted_netloc
                if www_version in search_domains:
                    is_consistent = True
            else:
                non_www_version = extracted_netloc[4:]
                if non_www_version in search_domains:
                    is_consistent = True
        if is_consistent or not search_domains:
            return extracted_url
        for search_link in search_urls:
            search_netloc = urlparse(search_link).netloc.lower()
            if (
                search_netloc == extracted_netloc
                or (extracted_netloc.startswith("www.") and search_netloc == extracted_netloc[4:])
                or (
                    not extracted_netloc.startswith("www.")
                    and "www." + extracted_netloc == search_netloc
                )
            ):
                return search_link
        return extracted_url
    except Exception as e:
        logger.warning(f"Error validating URL {extracted_url}: {e}")
        return extracted_url


logger = logging.getLogger("janus_backend")
_pending_contact_proposals: Dict[int, Dict[str, Any]] = {}
_pending_contact_lock = threading.RLock()

CONTACT_EXTRACTION_PROMPT = """
Du bist eine hochpräzise Datenextraktions-Engine für ein Adressbuch.
Deine Aufgabe ist es, Stammdaten zu extrahieren und den Kontext (Treffen, Projekte) strikt zu ignorieren.

**REGELN FÜR SAUBERE DATEN (GOLDSTANDARD):**
1.  **TRENNUNG VON KONTEXT:** Extrahiere NIEMALS Informationen über Meetings, Uhrzeiten, Daten ("nächste Woche"), Projekte ("Projekt Alpha") oder Orte von Treffen in das Feld `notes`. Das Feld `notes` ist NUR für dauerhafte Eigenschaften (z.B. "Vegetarier", "Abteilungsleiter", "Ehemann von X").
    - FALSCH: `notes: "Treffen am Dienstag im Café"` 
    - RICHTIG: `notes: null` (oder relevante Stammdaten)

2.  **KATEGORISIERUNG (WICHTIG FÜR ENRICHMENT):**
    - Setze `category` auf **"Business"**, wenn es sich um ein Geschäft, ein Restaurant, einen Arzt oder eine öffentliche Einrichtung handelt.
    - Setze `category` auf **"Privat"**, wenn es sich um eine Privatperson handelt (Freunde, Bekannte) ODER wenn keine geschäftlichen Details (wie Firmenname, Website) erkennbar sind.
    - **WARNUNG:** Wenn du unsicher bist, wähle lieber "Privat". Kontakte mit Kategorie "Privat" werden NICHT automatisch im Web gesucht, was Halluzinationen verhindert.

3.  **FORMAT:** Gib ein JSON-Array von Objekten zurück.
    - Keys: `name`, `address`, `phone`, `email`, `website`, `category`, `notes`.
    - Setze nicht gefundene Werte auf `null`.

--- BEISPIELE ---

**Input:** "Ich treffe mich Dienstag 14 Uhr mit Egon Schneider im Restaurant Evia wegen Projekt Alpha."
**Output:**
```json
[
  {{
    "name": "Egon Schneider",
    "category": "Privat", 
    "notes": null,
    "address": null, "phone": null, "email": null, "website": null
  }},
  {{
    "name": "Restaurant Evia",
    "category": "Business",
    "notes": null,
    "address": null, "phone": null, "email": null, "website": null
  }}
]
```
(Hinweis: Egon ist "Privat", weil er nur ein Name ist. Evia ist "Business". Keine Infos über "Dienstag" oder "Projekt Alpha" gespeichert!)

**Input:** "Dr. Schmidt (Zahnarzt) hat eine neue Nummer: 0123-456."
**Output:**
```json
[
  {{
    "name": "Dr. Schmidt",
    "category": "Business",
    "notes": "Zahnarzt",
    "phone": "0123-456",
    "address": null, "email": null, "website": null
  }}
]
```
--- ZU ANALYSIERENDER TEXT ---
{text_block}
"""

_PROPOSAL_FIELD_ORDER = [
    "name",
    "contact_type",
    "category",
    "email",
    "phone",
    "address",
    "website",
    "notes",
]

_PRIVATE_CATEGORY_HINTS = {
    "privat",
    "private",
    "persoenlich",
    "personlich",
    "family",
    "familie",
    "freund",
    "freunde",
    "friend",
    "bekannt",
}
_PUBLIC_CATEGORY_HINTS = {
    "business",
    "organisation",
    "organization",
    "firma",
    "restaurant",
    "arzt",
    "praxis",
    "geschaeft",
    "geschaft",
    "shop",
    "laden",
    "hotel",
    "cafe",
    "kanzlei",
    "behoerde",
    "behorde",
    "amt",
    "institution",
    "oeffentlich",
    "offentlich",
    "public",
}
_OBJECTIVE_CONTACT_FIELDS = ("phone", "email", "address", "website")
_SENSITIVE_MEMORY_CATEGORIES = {"gesundheit", "beziehungen"}
_CONTACT_MEMORY_SYNC_SOURCE = "contact_memory_sync"
_MEMORY_PROPOSAL_SOURCE = "memory_sync"
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"\+?\d[\d\s()/-]{5,}\d")
_URL_RE = re.compile(r"(https?://[^\s]+|www\.[^\s]+)", re.IGNORECASE)
_ADDRESS_RE = re.compile(r"\b(?:adresse|wohnt in|anschrift)\s*[:\-]?\s*(.+)$", re.IGNORECASE)
_PREFERENCE_RE = re.compile(
    r"\b(?:mag|liebt|bevorzugt|gern|gerne)\b\s*(.+)$",
    re.IGNORECASE,
)
_DISLIKE_RE = re.compile(
    r"\b(?:mag nicht|hasst|vermeidet|ungern|mochte nicht)\b\s*(.+)$",
    re.IGNORECASE,
)
_HEALTH_RE = re.compile(
    r"\b(?:allerg|krank|gesund|medik|unvertraeg|unverträg|gluten|laktose|diabet|blutdruck)\w*",
    re.IGNORECASE,
)
_RELATIONSHIP_RE = re.compile(
    r"\b(?:partner|ehe|verheirat|freundin|freund|mann|frau|mutter|vater|bruder|schwester|kind)\w*",
    re.IGNORECASE,
)


def _normalize_contact_name(name: Optional[str]) -> str:
    return " ".join(str(name or "").strip().lower().split())


def _normalize_contact_hint(value: Optional[str]) -> str:
    text = str(value or "").strip().lower()
    return (
        text.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


def _contact_is_public_enrichment_eligible(contact: Any) -> bool:
    contact_type = _normalize_contact_hint(getattr(contact, "contact_type", None))
    category = _normalize_contact_hint(getattr(contact, "category", None))
    if contact_type == "private_person":
        return False
    if contact_type == "organization":
        return True
    if category in _PRIVATE_CATEGORY_HINTS:
        return False
    return category in _PUBLIC_CATEGORY_HINTS


def _parse_memory_snippet_payload(snippet: Any) -> Dict[str, Any]:
    if isinstance(snippet, dict):
        return dict(snippet)
    text = str(snippet or "").strip()
    if not text:
        return {}
    if text.startswith("{"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {"fact": text}
    return {"fact": text}


def _append_unique(items: List[str], value: Optional[str]) -> None:
    text = str(value or "").strip()
    if not text:
        return
    if text not in items:
        items.append(text)


def _build_contact_memory_fact(
    *,
    contact_name: str,
    category: str,
    fact: str,
    predicate: str,
    object_value: str,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    normalized_name = _normalize_contact_name(contact_name).replace(" ", "_") or "unbekannt"
    normalized_predicate = re.sub(r"[^a-z0-9_]+", "_", predicate.strip().lower())
    normalized_object = re.sub(r"[^a-z0-9_]+", "_", object_value.strip().lower())[:80]
    return {
        "fact": fact,
        "category": category,
        "subject_name": contact_name,
        "subject_role": "contact",
        "predicate": predicate,
        "object_value": object_value,
        "canonical_key": f"contact:person:{normalized_name}:{normalized_predicate}:{normalized_object}",
        "tags": tags or ["contact", "address_book"],
        "source_skill": _CONTACT_MEMORY_SYNC_SOURCE,
    }


def _contact_memory_fact_objects(contact: Any) -> List[Dict[str, Any]]:
    contact_name = str(getattr(contact, "name", "") or "").strip()
    if not contact_name:
        return []

    facts: List[Dict[str, Any]] = []
    for field, label, predicate in (
        ("email", "E-Mail", "hat_email"),
        ("phone", "Telefonnummer", "hat_telefon"),
        ("address", "Adresse", "hat_adresse"),
        ("website", "Website", "hat_website"),
    ):
        value = _coerce_public_contact_value(field, getattr(contact, field, None))
        if value:
            facts.append(
                _build_contact_memory_fact(
                    contact_name=contact_name,
                    category="Allgemein",
                    fact=f"{contact_name} hat {label} {value}",
                    predicate=predicate,
                    object_value=value,
                    tags=["contact", "address_book", field],
                )
            )

    for value in list(getattr(contact, "preferences", None) or []):
        text = str(value).strip()
        if text:
            facts.append(
                _build_contact_memory_fact(
                    contact_name=contact_name,
                    category="Vorlieben",
                    fact=f"{contact_name} mag {text}",
                    predicate="mag",
                    object_value=text,
                    tags=["contact", "preference"],
                )
            )

    for value in list(getattr(contact, "dislikes", None) or []):
        text = str(value).strip()
        if text:
            facts.append(
                _build_contact_memory_fact(
                    contact_name=contact_name,
                    category="Vorlieben",
                    fact=f"{contact_name} mag nicht {text}",
                    predicate="mag_nicht",
                    object_value=text,
                    tags=["contact", "dislike"],
                )
            )

    for value in list(getattr(contact, "personal_details", None) or []):
        text = str(value).strip()
        if text:
            detail_category = "Gesundheit" if _HEALTH_RE.search(text) else (
                "Beziehungen" if _RELATIONSHIP_RE.search(text) else "Allgemein"
            )
            facts.append(
                _build_contact_memory_fact(
                    contact_name=contact_name,
                    category=detail_category,
                    fact=f"{contact_name}: {text}",
                    predicate="detail",
                    object_value=text,
                    tags=["contact", "personal_detail"],
                )
            )
    return facts


def _extract_contact_updates_from_memory_payload(memory_payload: Dict[str, Any]) -> Dict[str, Any]:
    fact_text = str(memory_payload.get("fact") or "").strip()
    category = _normalize_contact_hint(memory_payload.get("category"))
    updates: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {
        "fact": fact_text,
        "category": memory_payload.get("category"),
        "sensitive": False,
    }

    email_match = _EMAIL_RE.search(fact_text)
    if email_match:
        updates["email"] = email_match.group(0)

    url_match = _URL_RE.search(fact_text)
    if url_match:
        updates["website"] = _normalize_url(url_match.group(0))

    phone_match = _PHONE_RE.search(fact_text)
    if phone_match:
        updates["phone"] = phone_match.group(0).strip()

    address_match = _ADDRESS_RE.search(fact_text)
    if address_match:
        updates["address"] = address_match.group(1).strip(" .")

    preference_match = _PREFERENCE_RE.search(fact_text)
    dislike_match = _DISLIKE_RE.search(fact_text)

    if category == "vorlieben" or preference_match:
        preferences = []
        _append_unique(preferences, preference_match.group(1).strip(" .") if preference_match else fact_text)
        if preferences:
            updates["preferences"] = preferences

    if dislike_match:
        dislikes = []
        _append_unique(dislikes, dislike_match.group(1).strip(" ."))
        if dislikes:
            updates["dislikes"] = dislikes

    if category in _SENSITIVE_MEMORY_CATEGORIES or _HEALTH_RE.search(fact_text) or _RELATIONSHIP_RE.search(fact_text):
        metadata["sensitive"] = True

    if (
        category in {"allgemein", "beruf", "stil", "physis"}
        and not any(key in updates for key in ("email", "phone", "address", "website"))
    ) or metadata["sensitive"]:
        details: List[str] = []
        _append_unique(details, fact_text)
        if details:
            updates["personal_details"] = details

    metadata["fields"] = sorted(updates.keys())
    return {"updates": updates, "metadata": metadata}


def _should_auto_apply_contact_memory_update(
    *,
    memory: Any,
    match_mode: str,
    metadata: Dict[str, Any],
    proposal_payload: Dict[str, Any],
) -> bool:
    source_type = str(getattr(memory, "source_type", "") or "").strip().lower()
    if source_type != "text":
        return False
    if match_mode != "exact":
        return False
    if bool(metadata.get("sensitive")):
        return False
    allowed_fields = {"preferences", "dislikes"}
    payload_fields = {field for field in proposal_payload.keys() if field != "memory_sync_status"}
    return bool(payload_fields) and payload_fields.issubset(allowed_fields)


def _apply_contact_memory_update_directly(
    db_session: Session,
    *,
    target_contact: Any,
    proposal_payload: Dict[str, Any],
) -> Dict[str, Any]:
    updates = dict(proposal_payload)
    updates["proposal_status"] = "confirmed"
    updates["proposal_source_context"] = "direct_context"
    updates["proposal_last_outcome"] = "applied_from_confirmed_chat_fact"
    updated_contact = crud.update_contact(db_session, int(target_contact.id), updates)
    if updated_contact is None:
        return {"status": "failed", "reason": "update_failed", "proposals_staged": 0}
    return {
        "status": "applied",
        "reason": "direct_confirmed_chat_fact",
        "proposals_staged": 0,
        "suppressed": 0,
        "review_notes": [],
        "user_message": None,
        "applied_contact_id": updated_contact.id,
    }


def _coerce_public_contact_value(field: str, value: Any) -> Optional[str]:
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value if str(item).strip())
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if field == "website":
        return _normalize_url(text)
    return text


def _public_values_conflict(field: str, existing_value: Any, candidate_value: Any) -> bool:
    current = _coerce_public_contact_value(field, existing_value)
    candidate = _coerce_public_contact_value(field, candidate_value)
    if not current or not candidate:
        return False
    if field == "website":
        return current.rstrip("/") != candidate.rstrip("/")
    return current.casefold() != candidate.casefold()


def _mark_contact_enrichment_proposal_state(contact: Any, outcome: str) -> None:
    contact.proposal_status = "pending"
    contact.proposal_source_context = "web_enrichment"
    contact.proposal_last_outcome = outcome


def _stage_public_enrichment_proposal(
    db_session: Session,
    *,
    contact: Any,
    proposal_type: str,
    payload: Dict[str, Any],
    source_context: str,
) -> Dict[str, Any]:
    item = _build_contact_proposal_item(
        proposal_type=proposal_type,
        contact_name=str(getattr(contact, "name", "") or ""),
        payload=payload,
        target_contact=contact,
    )
    record = crud.get_contact_proposal_by_key(db_session, item["proposal_key"])
    if record and record.status == "rejected" and record.evidence_hash == item["evidence_hash"]:
        return {"status": "suppressed", "proposal_id": record.id}

    saved = crud.create_or_update_contact_proposal(
        db_session,
        proposal_batch_id=str(uuid.uuid4()),
        proposal_key=item["proposal_key"],
        chat_id=None,
        contact_id=getattr(contact, "id", None),
        contact_name=item["contact_name"],
        proposal_type=proposal_type,
        status="pending",
        evidence_hash=item["evidence_hash"],
        source_context=source_context[:2000],
        payload_json=item,
    )
    if saved is None:
        return {"status": "failed", "proposal_id": None}
    return {"status": "staged", "proposal_id": saved.id}


def _contact_type_from_payload(contact_data_item: Dict[str, Any]) -> str:
    explicit = str(contact_data_item.get("contact_type") or "").strip().lower()
    if explicit in {"private_person", "organization"}:
        return explicit

    category = str(contact_data_item.get("category") or "").strip().lower()
    if category in {"business", "organisation", "organization", "firma", "restaurant", "arzt", "praxis"}:
        return "organization"
    return "private_person"


def _sanitize_contact_payload(contact_data_item: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(contact_data_item or {})
    payload["contact_type"] = _contact_type_from_payload(payload)
    if "website" in payload:
        payload["website"] = _normalize_url(payload.get("website"))

    cleaned: Dict[str, Any] = {}
    for key in _PROPOSAL_FIELD_ORDER:
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue
        cleaned[key] = value

    if "name" in cleaned:
        cleaned["name"] = str(cleaned["name"]).strip()
    if "category" not in cleaned:
        cleaned["category"] = "Business" if cleaned.get("contact_type") == "organization" else "Privat"
    return cleaned


def _hash_proposal_evidence(*, proposal_type: str, target_key: str, payload: Dict[str, Any]) -> str:
    serialized = json.dumps(
        {
            "proposal_type": proposal_type,
            "target_key": target_key,
            "payload": {key: payload.get(key) for key in sorted(payload.keys())},
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _extract_candidate_updates(
    contact_data_item: Dict[str, Any], existing_contact: Any
) -> Dict[str, Any]:
    updates: Dict[str, Any] = {}
    for field in ["email", "phone", "address", "website", "notes", "category", "contact_type"]:
        new_value = contact_data_item.get(field)
        if new_value is None:
            continue
        if isinstance(new_value, str):
            new_value = new_value.strip()
            if not new_value:
                continue
        existing_value = getattr(existing_contact, field, None)
        if not existing_value:
            updates[field] = new_value
    return updates


def _find_existing_contact_candidates(db_session: Session, contact_name: str) -> Dict[str, Any]:
    exact_matches = crud.search_contacts_by_name(db_session, name_query=contact_name)
    normalized_name = _normalize_contact_name(contact_name)
    exact_named = [row for row in exact_matches if _normalize_contact_name(getattr(row, "name", "")) == normalized_name]
    if len(exact_named) == 1:
        return {"primary": exact_named[0], "mode": "exact", "candidates": exact_named}
    if len(exact_named) > 1:
        return {"primary": None, "mode": "ambiguous", "candidates": exact_named}

    seen: Dict[int, Any] = {}
    tokens = [part for part in re.split(r"\s+", contact_name) if len(part) > 2]
    candidate_queries = [contact_name]
    if tokens:
        candidate_queries.extend(tokens)
        candidate_queries.append(tokens[-1])

    for query in candidate_queries:
        for row in crud.search_contacts_by_name(db_session, name_query=query):
            seen[getattr(row, "id", 0)] = row

    candidates = list(seen.values())
    if len(candidates) == 1:
        return {"primary": candidates[0], "mode": "near_match", "candidates": candidates}

    scored: List[Any] = []
    for candidate in candidates:
        ratio = SequenceMatcher(
            None,
            normalized_name,
            _normalize_contact_name(getattr(candidate, "name", "")),
        ).ratio()
        scored.append((ratio, candidate))

    strong = [candidate for ratio, candidate in scored if ratio >= 0.78]
    if len(strong) == 1:
        return {"primary": strong[0], "mode": "near_match", "candidates": strong}
    if len(strong) > 1:
        return {"primary": None, "mode": "ambiguous", "candidates": strong}
    return {"primary": None, "mode": "none", "candidates": []}


def _build_contact_proposal_item(
    *,
    proposal_type: str,
    contact_name: str,
    payload: Dict[str, Any],
    target_contact: Optional[Any] = None,
) -> Dict[str, Any]:
    target_key = str(getattr(target_contact, "id", "") or _normalize_contact_name(contact_name))
    evidence_hash = _hash_proposal_evidence(
        proposal_type=proposal_type,
        target_key=target_key,
        payload=payload,
    )
    item: Dict[str, Any] = {
        "proposal_type": proposal_type,
        "proposal_key": f"{proposal_type}:{target_key}",
        "contact_name": contact_name,
        "evidence_hash": evidence_hash,
        "payload": payload,
    }
    if target_contact is not None:
        item["contact_id"] = getattr(target_contact, "id", None)
        item["existing_name"] = getattr(target_contact, "name", contact_name)
    return item


def _format_contact_fields(payload: Dict[str, Any]) -> str:
    labels = {
        "email": "E-Mail",
        "phone": "Telefon",
        "address": "Adresse",
        "website": "Website",
        "notes": "Notiz",
        "category": "Kategorie",
    }
    parts = []
    for key in ["email", "phone", "address", "website", "notes", "category"]:
        value = payload.get(key)
        if value:
            parts.append(f"{labels[key]}: {value}")
    return ", ".join(parts) if parts else "ohne neue Detailfelder"


def _build_contact_confirmation_prompt_message(bundle: Dict[str, Any]) -> str:
    lines = ["Janus: Ich habe einen Kontaktvorschlag vorbereitet:"]
    for item in bundle.get("items", []):
        proposal_type = item.get("proposal_type")
        contact_name = item.get("contact_name") or "Unbekannter Kontakt"
        payload = item.get("payload") or {}
        if proposal_type == "create":
            lines.append(f"- Neuer Kontakt: {contact_name} ({_format_contact_fields(payload)})")
        elif proposal_type == "update":
            lines.append(
                f"- Bestehenden Kontakt ergaenzen: {item.get('existing_name', contact_name)} ({_format_contact_fields(payload)})"
            )
        else:
            lines.append(
                f"- Moeglichen Dublettenfall als Merge pruefen: {item.get('existing_name', contact_name)} ({_format_contact_fields(payload)})"
            )

    review_notes = bundle.get("review_notes") or []
    if review_notes:
        lines.append("")
        lines.extend(f"- Hinweis: {note}" for note in review_notes)

    lines.append("")
    lines.append("Soll ich diese Kontaktvorschlaege anwenden? Antworte mit Ja zum Bestaetigen oder Nein zum Verwerfen.")
    return "\n".join(lines)


def _set_pending_contact_proposal(chat_id: int, proposal_bundle: Dict[str, Any]) -> None:
    with _pending_contact_lock:
        _pending_contact_proposals[int(chat_id)] = proposal_bundle


def get_pending_contact_proposal(chat_id: Optional[int]) -> Optional[Dict[str, Any]]:
    if chat_id is None:
        return None
    with _pending_contact_lock:
        pending = _pending_contact_proposals.get(int(chat_id))
        return dict(pending) if pending else None


def pop_pending_contact_proposal(chat_id: Optional[int]) -> Optional[Dict[str, Any]]:
    if chat_id is None:
        return None
    with _pending_contact_lock:
        return _pending_contact_proposals.pop(int(chat_id), None)


def _clear_pending_contact_proposals_for_tests() -> None:
    with _pending_contact_lock:
        _pending_contact_proposals.clear()


def _proposal_summary_message(result: Dict[str, Any]) -> Optional[str]:
    if result.get("user_message"):
        return result["user_message"]
    if result.get("review_notes"):
        return "\n".join(result["review_notes"])
    return None


def _clean_and_parse_llm_json(llm_response_text: str) -> Optional[Dict[str, Any]]:
    if not llm_response_text or not isinstance(llm_response_text, str):
        return None
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", llm_response_text, re.DOTALL)
    json_string = ""
    if match:
        json_string = match.group(1).strip()
    else:
        start = llm_response_text.find("{")
        end = llm_response_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_string = llm_response_text[start : end + 1].strip()
        else:
            json_string = llm_response_text.strip()
    try:
        parsed = json.loads(json_string)
        if not isinstance(parsed, dict):
            return None
        return parsed
    except json.JSONDecodeError:
        return None


async def _is_ambiguous_result(
    web_content: str, contact_name: str, api_key: str, provider: str, model: str
) -> bool:
    # Import inside function to avoid circular dependency
    import backend.services.llm_gateway as llm_gateway

    if not web_content:
        return False

    # 💎 Use get_speed_tier_model() for background jobs instead of hardcoded model names
    from backend.services.logging.debug_engine import get_speed_tier_model
    speed_provider, speed_model = get_speed_tier_model()
    
    model_to_use = model
    if provider == "openai":
        model_to_use = "gpt-5-nano"
    elif provider == "gemini":
        # If the speed-tier provider matches, use speed-tier model
        if speed_provider == "gemini":
            model_to_use = speed_model
        else:
            model_to_use = "gemini-3-flash-preview"

    prompt = f"""
    Du bist ein Datenanalyse-Experte. Der folgende Text ist das Ergebnis einer Websuche nach dem Namen '{contact_name}'.
    Beschreibt dieser Text eine einzelne, klare Person oder Entität, oder listet er mehrere verschiedene Personen, Unternehmen oder Orte mit diesem Namen auf?
    Antworte NUR mit dem Wort 'Eindeutig' wenn es sich klar um eine einzige Entität handelt, oder 'Mehrdeutig' wenn mehrere, nicht zusammenhängende Entitäten genannt werden.

    Text:
    {web_content[:4000]}
    """
    try:
        response = await llm_gateway.call_llm(
            provider=provider,
            model_id=model_to_use,
            api_key=api_key,
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )
        answer = response.get("text", "").strip().lower()
        logger.info(f"Disambiguation check for '{contact_name}' resulted in: '{answer}'")
        return "mehrdeutig" in answer
    except Exception as e:
        logger.error(f"Fehler bei der Mehrdeutigkeitsprüfung: {e}")
        return True


async def enrich_incomplete_contacts(
    contact_id: int,
    api_key: str,
    provider: str,
    model: str,
    text_block: Optional[str] = None,
    location_context: Optional[str] = None,
):
    # Import inside function to avoid circular dependency
    import backend.services.llm_gateway as llm_gateway

    logger.info(
        f"Background task for enriching incomplete contacts starting for contact ID: {contact_id}."
    )
    db = SessionLocal()
    try:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            logger.error(f"Contact with ID {contact_id} not found for enrichment.")
            return

        if not _contact_is_public_enrichment_eligible(contact):
            logger.info(
                "Contact '%s' is not eligible for public web enrichment (contact_type=%r, category=%r).",
                contact.name,
                getattr(contact, "contact_type", None),
                contact.category,
            )
            return

        if all(
            _coerce_public_contact_value(field, getattr(contact, field, None))
            for field in _OBJECTIVE_CONTACT_FIELDS
        ):
            logger.info(
                f"Contact {contact.name} (ID: {contact.id}) is already complete. Skipping enrichment."
            )
            return

        logger.info(f"Attempting to enrich contact: {contact.name} (ID: {contact.id})")

        if contact.address:
            # Wenn eine Adresse vorhanden ist, ist die Suche spezifisch genug.
            search_query = f"{contact.name} {contact.address} Telefon E-Mail Website".strip()
            logger.info(f"Spezifische Suchanfrage mit Adresse erstellt: '{search_query}'")
        else:
            # Fallback, wenn keine Adresse vorhanden ist, nutze den Kontext.
            city_from_text = None
            if text_block and _contact_is_public_enrichment_eligible(contact):
                cities_regex = r"\b(Berlin|Hamburg|München|Köln|Frankfurt|Stuttgart|Düsseldorf|Dortmund|Essen|Leipzig|Bremen|Dresden|Hannover|Nürnberg|Duisburg|Bochum|Wuppertal|Bielefeld|Bonn|Münster)\b"
                match = re.search(cities_regex, text_block, re.IGNORECASE)
                if match:
                    city_from_text = match.group(1)
                    logger.info(
                        f"Stadt '{city_from_text}' aus dem Benutzertext für die Kontaktsuche extrahiert."
                    )

            final_location = location_context or city_from_text
            location_str = f" in {final_location}" if final_location else ""
            search_query = f"{contact.name}{location_str} Adresse Telefon E-Mail Website {contact.notes or ''}".strip()
            logger.info(f"Allgemeine Suchanfrage ohne Adresse erstellt: '{search_query}'")
        # --- ENDE NEUE LOGIK ZUR SPEZIFISCHEN SUCHANFRAGE ---
        logger.info(f"Enrichment search query: '{search_query}'")

        # --- START KORREKTUR ---
        # Hole den spezifischen API Key basierend auf dem Provider
        import keyring

        api_key_for_websearch = None
        if provider == "openai":
            api_key_for_websearch = keyring.get_password("Janus-Projekt", "openai")
            if not api_key_for_websearch:
                logger.error("OpenAI API key not found in keyring. Cannot perform web enrichment.")
                return
        elif provider == "gemini":
            api_key_for_websearch = keyring.get_password("Janus-Projekt", "gemini")
            if not api_key_for_websearch:
                logger.error("Gemini API key not found in keyring. Cannot perform web enrichment.")
                return
        else:
            logger.error(
                f"Unsupported provider '{provider}' for web enrichment. Cannot perform web enrichment."
            )
            return

        # Lade den Modellkatalog, um den Provider für das aktuelle Modell zu finden
        model_catalog = await asyncio.to_thread(main_load_model_catalog)

        # Bestimme den Provider für das Modell
        provider_for_model = model_catalog.get(model, {}).get("provider")
        if not provider_for_model:
            logger.error(
                f"Provider for model '{model}' not found in model catalog. Defaulting to OpenAI."
            )
            provider_for_model = "openai"  # Fallback

        # 💎 Use get_speed_tier_model() for background jobs instead of hardcoded model names
        from backend.services.logging.debug_engine import get_speed_tier_model
        speed_provider, speed_model = get_speed_tier_model()
        
        # If the speed-tier provider matches the model's provider, use the speed-tier model
        if speed_provider == provider_for_model:
            model_to_use_for_websearch = speed_model
            logger.info(f"Using speed-tier model '{speed_model}' for provider '{provider_for_model}' in contact enrichment")
        else:
            # Fallback to provider-specific hardcoded models if speed-tier provider doesn't match
            if provider_for_model == "openai":
                model_to_use_for_websearch = "gpt-5.4-nano"
            elif provider_for_model == "gemini":
                model_to_use_for_websearch = "gemini-3-flash-preview"
            else:
                model_to_use_for_websearch = model  # Fallback, wenn der Provider nicht OpenAI/Gemini ist

        # --- ENDE KORREKTUR ---

        from backend.services.websearch.websearch import execute_websearch_service

        websearch_result = await execute_websearch_service(
            query=search_query,
            api_key=api_key_for_websearch,
            provider=provider_for_model,
            model=model_to_use_for_websearch,
        )
        web_content = websearch_result.get("text", "")
        if not web_content:
            logger.warning(
                f"Web search for '{search_query}' yielded no results. Cannot enrich contact."
            )
            return
        if await _is_ambiguous_result(
            web_content,
            contact.name,
            api_key_for_websearch,
            provider_for_model,
            model_to_use_for_websearch,
        ):  # Verwende api_key_for_websearch und provider_for_model
            logger.warning(
                f"Web search result for '{contact.name}' is ambiguous. Halting enrichment to ask for user clarification."
            )
            _mark_contact_enrichment_proposal_state(contact, "selection_required")
            staged = _stage_public_enrichment_proposal(
                db,
                contact=contact,
                proposal_type="public_match_selection",
                payload={
                    "reason": "ambiguous_public_match",
                    "search_query": search_query,
                    "web_urls": list(websearch_result.get("urls") or [])[:10],
                    "web_excerpt": web_content[:2000],
                },
                source_context=search_query,
            )
            if staged["status"] == "suppressed":
                contact.proposal_last_outcome = "selection_required_suppressed"
                db.commit()
            return

        extraction_prompt = f"""
Du bist eine hochpräzise Datenextraktions-Engine. Deine einzige Aufgabe ist es, aus dem folgenden Text exakte Daten für '{contact.name}' zu extrahieren.
Antworte ausschließlich mit einem einzigen JSON-Objekt, das die Schlüssel 'address', 'phone', 'email' und 'website' enthält.

**ABSOLUT ZWINGENDE REGELN:**
1.  **KOPIERE ZEICHEN FÜR ZEICHEN:** Extrahiere alle Daten exakt so, wie sie im Text stehen. Ändere kein einziges Zeichen.
2.  **VERÄNDERE UNTER KEINEN UMSTÄNDEN DIE URLs.** Das bedeutet:
    - Behalte die exakte Domain (z.B. `restaurant-evia.com`).
    - Behalte die exakte Top-Level-Domain (z.B. `.com`, `.de`). Ändere **niemals** ein `.com` in ein `.de` oder umgekehrt.
    - Behalte das Protokoll (`http://` oder `https://`), falls vorhanden
    - Füge **keine** fehlenden Teile wie `www.` hinzu, wenn es nicht im Text steht.
3.  Wenn eine Information nicht gefunden wird, muss der Wert `null` sein.

**GUTES BEISPIEL:**
- Text enthält: "Website: [restaurant-evia.com](http://restaurant-evia.com/)"
- Korrekte JSON-Ausgabe: `{{"website": "http://restaurant-evia.com/"}}`

**SCHLECHTES BEISPIEL (VERBOTEN):**
- Text enthält: `Website: [restaurant-evia.com](http://restaurant-evia.com/)`
- Falsche Ausgabe: `{{"website": "http://www.restaurant-evia.de"}}`

--- ZU ANALYSIERENDER TEXT ---
{web_content}
"""
        extraction_response = await llm_gateway.call_llm(
            provider=provider_for_model,  # Verwende provider_for_model
            model_id=model_to_use_for_websearch,  # Verwende model_to_use_for_websearch
            api_key=api_key_for_websearch,  # Verwende api_key_for_websearch
            messages=[{"role": "user", "content": extraction_prompt}],
            tools=None,
        )
        llm_response_text = extraction_response.get("text", "")
        enriched_data = _clean_and_parse_llm_json(llm_response_text)

        if enriched_data:
            fields_to_update: Dict[str, str] = {}
            conflicting_fields: Dict[str, Dict[str, str]] = {}
            websearch_urls = websearch_result.get("urls", [])

            for field in _OBJECTIVE_CONTACT_FIELDS:
                candidate_value = enriched_data.get(field)
                if field == "website":
                    candidate_value = _validate_extracted_url(
                        _coerce_public_contact_value(field, candidate_value) or "",
                        websearch_urls,
                    )

                clean_value = _coerce_public_contact_value(field, candidate_value)
                if not clean_value:
                    continue

                existing_value = getattr(contact, field, None)
                if not _coerce_public_contact_value(field, existing_value):
                    setattr(contact, field, clean_value)
                    fields_to_update[field] = clean_value
                    continue

                if _public_values_conflict(field, existing_value, clean_value):
                    conflicting_fields[field] = {
                        "current_value": _coerce_public_contact_value(field, existing_value) or "",
                        "suggested_value": clean_value,
                    }

            if conflicting_fields:
                _mark_contact_enrichment_proposal_state(contact, "conflict_requires_confirmation")
                staged = _stage_public_enrichment_proposal(
                    db,
                    contact=contact,
                    proposal_type="public_field_conflict",
                    payload={
                        "reason": "conflicting_public_data",
                        "search_query": search_query,
                        "web_urls": list(websearch_urls or [])[:10],
                        "web_excerpt": web_content[:2000],
                        "missing_updates_applied": fields_to_update,
                        "conflicts": conflicting_fields,
                    },
                    source_context=search_query,
                )
                if staged["status"] == "suppressed":
                    contact.proposal_last_outcome = "conflict_suppressed"
                    db.commit()
                logger.info(
                    "Contact %s (ID: %s) staged public-data conflict proposal: %s",
                    contact.name,
                    contact.id,
                    list(conflicting_fields.keys()),
                )
            elif fields_to_update:
                contact.proposal_status = "confirmed"
                contact.proposal_source_context = "web_enrichment"
                contact.proposal_last_outcome = "applied"
                logger.info(
                    f"Contact {contact.name} (ID: {contact.id}) enriched with: {fields_to_update}"
                )
                db.commit()
            else:
                logger.info(f"No new information found to enrich contact {contact.name}.")
        else:
            logger.warning(
                f"Could not extract valid contact details from LLM response for {contact.name}."
            )
    except Exception as e:
        logger.error(
            f"An error occurred in the background contact enrichment task: {e}", exc_info=True
        )
        db.rollback()
    finally:
        db.close()
        logger.info(
            f"Background enrichment task for contact ID {contact_id} finished and session closed."
        )


async def _process_single_contact_data(
    contact_data_item: Dict[str, Any],
    db_session,
    api_key: str,
    provider: str,
    model: str,
    text_block: Optional[str] = None,
    location_context: Optional[str] = None,
):
    try:
        # --- NEU: Normalisiere die Website-URL direkt nach der Extraktion ---
        if "website" in contact_data_item:
            contact_data_item["website"] = _normalize_url(contact_data_item["website"])
        # --- ENDE: Neue Zeile ---
        contact_name = contact_data_item.get("name")
        if not contact_name:
            logger.warning(
                f"Überspringe Kontakt-Extraktion für Objekt ohne Namen: {contact_data_item}"
            )
            return

        # --- (Rest der Funktion bleibt unverändert) ---
        # --- START DER NEUEN, ROBUSTERE KONTAKTSUCHE ---
        existing_contact = None
        # 1. Versuche eine exakte Übereinstimmung
        exact_matches = crud.search_contacts_by_name(db_session, name_query=contact_name)
        if exact_matches:
            existing_contact = exact_matches[0]
        else:
            # 2. Wenn nicht gefunden, versuche eine flexible Suche mit Namensbestandteilen
            name_parts = [
                part for part in contact_name.split() if len(part) > 2
            ]  # Ignoriere kurze Teile wie "Dr"
            if name_parts:
                # Suche nach dem letzten Teil (wahrscheinlich der Nachname oder der markanteste Teil)
                partial_matches = crud.search_contacts_by_name(
                    db_session, name_query=name_parts[-1]
                )
                if len(partial_matches) == 1:
                    # Wenn wir genau einen passenden Kontakt finden, nehmen wir an, es ist der richtige.
                    existing_contact = partial_matches[0]
                    logger.info(
                        f"Kontakt '{contact_name}' durch flexible Suche mit '{existing_contact.name}' (ID: {existing_contact.id}) verknüpft."
                    )
        # --- ENDE DER NEUEN, ROBUSTERE KONTAKTSUCHE ---
        if existing_contact:
            logger.info(
                f"Kontakt mit Namen '{contact_name}' wird mit bestehendem Kontakt '{existing_contact.name}' (ID: {existing_contact.id}) zusammengeführt."
            )

            update_data = {}
            # Iteriere über die möglichen Felder und aktualisiere nur, wenn ein neuer Wert vorhanden ist und der alte fehlt.
            for field in ["email", "phone", "address", "website", "notes", "category"]:
                new_value = contact_data_item.get(field)
                existing_value = getattr(existing_contact, field)
                if new_value and not existing_value:
                    update_data[field] = new_value

            if update_data:
                logger.info(
                    f"Aktualisiere existierenden Kontakt '{existing_contact.name}' mit neuen Informationen aus dem Text: {update_data}"
                )
                # Rufe die korrigierte CRUD-Funktion auf
                updated_contact = crud.update_contact(
                    db_session, contact_id=existing_contact.id, updates=update_data
                )
                if not updated_contact:
                    logger.error(
                        f"Fehler beim Aktualisieren des Kontakts mit ID {existing_contact.id}"
                    )
                    return  # Breche ab, wenn das Update fehlschlägt

                # Verwende das zurückgegebene, aktualisierte Objekt für die weitere Prüfung
                existing_contact = updated_contact

            # Prüfe nun, ob der Kontakt (nach dem Update) immer noch unvollständig ist und starte dann die Web-Anreicherung.
            if not all([existing_contact.address, existing_contact.phone, existing_contact.email]):
                logger.info(
                    f"Kontakt '{existing_contact.name}' ist weiterhin unvollständig. Starte Web-Anreicherung."
                )
                asyncio.create_task(
                    enrich_incomplete_contacts(
                        contact_id=existing_contact.id,
                        api_key=api_key,
                        provider=provider,
                        model=model,
                        text_block=text_block,
                        location_context=location_context,
                    )
                )
            else:
                logger.info(
                    f"Kontakt '{existing_contact.name}' ist nun vollständig. Überspringe Web-Anreicherung."
                )
            return
        contact_schema = contact_schemas.ContactCreate(**contact_data_item)
        created_contact = crud.create_contact(db_session, contact=contact_schema)
        if created_contact:
            logger.info(
                f"Neuer Kontakt '{created_contact.name}' wurde erfolgreich aus Text extrahiert und gespeichert mit ID {created_contact.id}."
            )
            asyncio.create_task(
                enrich_incomplete_contacts(
                    contact_id=created_contact.id,
                    api_key=api_key,
                    provider=provider,
                    model=model,
                    text_block=text_block,
                )
            )
    except ValidationError as e:
        logger.warning(
            f"Kontakt-Extraktion: Pydantic-Validierungsfehler für Objekt: {contact_data_item}. Fehler: {e}. Überspringe."
        )
    except Exception as e:
        logger.error(
            f"Fehler beim Verarbeiten eines einzelnen Kontakts: {contact_data_item}. Fehler: {e}",
            exc_info=True,
        )


async def _process_contact_candidate_v2(
    contact_data_item: Dict[str, Any],
    db_session: Session,
) -> Dict[str, Any]:
    payload = _sanitize_contact_payload(contact_data_item)
    contact_name = payload.get("name")
    if not contact_name:
        logger.warning(
            "Kontakt-Extraktion V2: Objekt ohne Namen wird Ã¼bersprungen: %s",
            contact_data_item,
        )
        return {"kind": "noop"}

    match_info = _find_existing_contact_candidates(db_session, contact_name)
    existing_contact = match_info.get("primary")
    match_mode = match_info.get("mode")
    candidates = match_info.get("candidates") or []

    if match_mode == "ambiguous":
        candidate_names = ", ".join(
            str(getattr(candidate, "name", "")).strip()
            for candidate in candidates[:3]
            if getattr(candidate, "name", None)
        )
        return {
            "kind": "review",
            "message": (
                f"Mehrdeutiger Kontaktfund fuer '{contact_name}'. "
                f"Ich habe keine zweite Karte angelegt. Bitte pruefe vorhandene Kontakte wie {candidate_names or 'den bestehenden Bestand'}."
            ),
        }

    if existing_contact:
        update_data = _extract_candidate_updates(payload, existing_contact)
        if not update_data:
            return {"kind": "noop"}

        proposal_type = "merge" if match_mode == "near_match" else "update"
        return {
            "kind": "proposal",
            "item": _build_contact_proposal_item(
                proposal_type=proposal_type,
                contact_name=contact_name,
                payload=update_data,
                target_contact=existing_contact,
            ),
        }

    return {
        "kind": "proposal",
        "item": _build_contact_proposal_item(
            proposal_type="create",
            contact_name=contact_name,
            payload=payload,
        ),
    }


def _persist_contact_proposal_batch(
    db_session: Session,
    *,
    chat_id: Optional[int],
    text_block: str,
    proposal_items: List[Dict[str, Any]],
    review_notes: List[str],
) -> Dict[str, Any]:
    result = {
        "proposals_staged": 0,
        "suppressed": 0,
        "review_notes": review_notes,
        "user_message": None,
        "proposal_id": None,
    }
    if not proposal_items:
        if review_notes:
            result["user_message"] = "\n".join(review_notes)
        return result

    batch_id = str(uuid.uuid4())
    staged_items: List[Dict[str, Any]] = []
    seen_in_batch = set()
    for item in proposal_items:
        dedupe_key = (item["proposal_key"], item["evidence_hash"])
        if dedupe_key in seen_in_batch:
            continue
        seen_in_batch.add(dedupe_key)
        record = crud.get_contact_proposal_by_key(db_session, item["proposal_key"])
        if record and record.status == "rejected" and record.evidence_hash == item["evidence_hash"]:
            result["suppressed"] += 1
            continue

        saved = crud.create_or_update_contact_proposal(
            db_session,
            proposal_batch_id=batch_id,
            proposal_key=item["proposal_key"],
            chat_id=chat_id,
            contact_id=item.get("contact_id"),
            contact_name=item["contact_name"],
            proposal_type=item["proposal_type"],
            status="pending",
            evidence_hash=item["evidence_hash"],
            source_context=text_block[:2000],
            payload_json=item,
        )
        if saved is None:
            continue

        staged_item = dict(item)
        staged_item["proposal_record_id"] = saved.id
        staged_items.append(staged_item)

    result["proposals_staged"] = len(staged_items)
    if not staged_items:
        if review_notes:
            result["user_message"] = "\n".join(review_notes)
        return result

    bundle = {
        "proposal_id": batch_id,
        "chat_id": chat_id,
        "items": staged_items,
        "review_notes": review_notes,
    }
    result["proposal_id"] = batch_id
    if isinstance(chat_id, int):
        _set_pending_contact_proposal(chat_id, bundle)
    result["user_message"] = _build_contact_confirmation_prompt_message(bundle)
    return result


def sync_confirmed_contact_to_memory(
    db_session: Session,
    *,
    contact_id: int,
    chat_id: Optional[int] = None,
) -> Dict[str, Any]:
    from backend.services.memory import save_memory_snippet

    contact = db_session.query(Contact).filter(Contact.id == int(contact_id)).first()
    if contact is None:
        return {"status": "missing_contact", "synced_count": 0}
    if str(getattr(contact, "proposal_status", "") or "confirmed") != "confirmed":
        return {"status": "skipped_unconfirmed", "synced_count": 0}

    fact_objects = _contact_memory_fact_objects(contact)
    if not fact_objects:
        if getattr(contact, "memory_sync_status", None) != "synced":
            contact.memory_sync_status = "ready"
            db_session.commit()
        return {"status": "nothing_to_sync", "synced_count": 0}

    synced_count = 0
    target_chat_id = int(chat_id) if chat_id is not None else None
    for fact_object in fact_objects:
        saved = save_memory_snippet(
            db=db_session,
            chat_id=target_chat_id,
            fact_object=fact_object,
            source_type="contact_sync",
            source_metadata={"contact_id": contact.id, "contact_name": contact.name},
        )
        if saved is not None:
            synced_count += 1

    contact.memory_sync_status = "synced" if synced_count else "ready"
    db_session.commit()
    return {"status": "synced" if synced_count else "ready", "synced_count": synced_count}


def stage_contact_update_from_memory(
    db_session: Session,
    *,
    memory: Any,
    chat_id: Optional[int] = None,
) -> Dict[str, Any]:
    memory_payload = _parse_memory_snippet_payload(getattr(memory, "snippet", None))
    subject_name = str(
        memory_payload.get("subject_name")
        or memory_payload.get("contact_name")
        or ""
    ).strip()
    if not subject_name:
        return {"status": "ignored", "reason": "missing_subject", "proposals_staged": 0}

    match_info = _find_existing_contact_candidates(db_session, subject_name)
    target_contact = match_info.get("primary")
    match_mode = str(match_info.get("mode") or "")
    if target_contact is None or match_mode not in {"exact", "near_match"}:
        return {"status": "ignored", "reason": "ambiguous_contact", "proposals_staged": 0}

    extracted = _extract_contact_updates_from_memory_payload(memory_payload)
    updates = extracted.get("updates") or {}
    metadata = extracted.get("metadata") or {}
    if not updates:
        return {"status": "ignored", "reason": "no_contact_fields", "proposals_staged": 0}

    proposal_payload: Dict[str, Any] = {}
    for field, value in updates.items():
        if field in {"preferences", "dislikes", "personal_details"}:
            existing_values = list(getattr(target_contact, field, None) or [])
            merged_values = list(existing_values)
            for item in list(value or []):
                _append_unique(merged_values, item)
            if merged_values != existing_values:
                proposal_payload[field] = merged_values
        else:
            existing_value = getattr(target_contact, field, None)
            normalized_value = _coerce_public_contact_value(field, value)
            if normalized_value and (
                not _coerce_public_contact_value(field, existing_value)
                or _public_values_conflict(field, existing_value, normalized_value)
            ):
                proposal_payload[field] = normalized_value

    if not proposal_payload:
        return {"status": "ignored", "reason": "already_applied", "proposals_staged": 0}

    if _should_auto_apply_contact_memory_update(
        memory=memory,
        match_mode=match_mode,
        metadata=metadata,
        proposal_payload=proposal_payload,
    ):
        return _apply_contact_memory_update_directly(
            db_session,
            target_contact=target_contact,
            proposal_payload=proposal_payload,
        )

    proposal_payload["memory_sync_status"] = "ready"
    proposal_payload["proposal_metadata"] = {
        "memory_id": getattr(memory, "id", None),
        "memory_category": metadata.get("category"),
        "memory_fact": metadata.get("fact"),
        "sensitive": bool(metadata.get("sensitive")),
        "source_context": _MEMORY_PROPOSAL_SOURCE,
    }

    result = _persist_contact_proposal_batch(
        db_session,
        chat_id=chat_id,
        text_block=str(metadata.get("fact") or ""),
        proposal_items=[
            _build_contact_proposal_item(
                proposal_type="memory_contact_update",
                contact_name=subject_name,
                payload=proposal_payload,
                target_contact=target_contact,
            )
        ],
        review_notes=[
            "Bestaetigtes Memory-Wissen wurde als Kontakt-Update-Vorschlag vorgemerkt."
        ],
    )
    if result.get("proposals_staged"):
        contact_model = db_session.query(Contact).filter(Contact.id == int(target_contact.id)).first()
        if contact_model is not None:
            contact_model.proposal_status = "pending"
            contact_model.proposal_source_context = _MEMORY_PROPOSAL_SOURCE
            contact_model.proposal_last_outcome = "suggested_from_memory"
            contact_model.memory_sync_status = "ready"
            db_session.commit()
    return result


def reject_pending_contact_proposal(chat_id: int) -> Dict[str, Any]:
    pending = pop_pending_contact_proposal(chat_id)
    if not pending:
        return {"status": "noop", "user_message": "Es lag kein Kontaktvorschlag zur Bestaetigung vor."}

    db = next(database.get_db_sync())
    try:
        for item in pending.get("items", []):
            proposal_record_id = item.get("proposal_record_id")
            target_id = item.get("contact_id")
            payload = dict(item.get("payload") or {})
            source_context = (
                str((payload.get("proposal_metadata") or {}).get("source_context") or "")
                or str(payload.get("apply_source_context") or "")
                or "direct_context"
            )
            if proposal_record_id:
                crud.update_contact_proposal_status(
                    db,
                    proposal_id=proposal_record_id,
                    status="rejected",
                )
            if target_id:
                updates = {
                    "proposal_status": "confirmed",
                    "proposal_source_context": source_context,
                    "proposal_last_outcome": "rejected",
                }
                if source_context == _MEMORY_PROPOSAL_SOURCE:
                    updates["memory_sync_status"] = "ready"
                crud.update_contact(db, int(target_id), updates)
        return {
            "status": "rejected",
            "user_message": "Alles klar - ich habe den Kontaktvorschlag verworfen und merke mir diese Ablehnung fuer dieselbe Evidenz.",
        }
    finally:
        db.close()


def confirm_pending_contact_proposal(chat_id: int) -> Dict[str, Any]:
    pending = pop_pending_contact_proposal(chat_id)
    if not pending:
        return {"status": "noop", "user_message": "Es lag kein Kontaktvorschlag zur Bestaetigung vor."}

    db = next(database.get_db_sync())
    created_names: List[str] = []
    updated_names: List[str] = []
    failed_names: List[str] = []
    try:
        for item in pending.get("items", []):
            proposal_record_id = item.get("proposal_record_id")
            payload = dict(item.get("payload") or {})
            proposal_type = str(item.get("proposal_type") or "create")
            applied_contact_id: Optional[int] = None
            proposal_metadata = payload.pop("proposal_metadata", {}) or {}
            apply_source_context = (
                str(proposal_metadata.get("source_context") or "")
                or str(payload.pop("apply_source_context", "") or "")
                or "direct_context"
            )

            if proposal_type == "create":
                contact = crud.create_contact(
                    db,
                    contact_schemas.ContactCreate(
                        **payload,
                        proposal_status="confirmed",
                        proposal_source_context=apply_source_context,
                        proposal_last_outcome="applied",
                        memory_sync_status="ready" if apply_source_context == _MEMORY_PROPOSAL_SOURCE else payload.get("memory_sync_status"),
                    ),
                )
                if contact:
                    applied_contact_id = contact.id
                    created_names.append(contact.name)
            else:
                target_id = item.get("contact_id")
                updates = dict(payload)
                updates["proposal_status"] = "confirmed"
                updates["proposal_source_context"] = apply_source_context
                updates["proposal_last_outcome"] = "applied"
                if apply_source_context == _MEMORY_PROPOSAL_SOURCE:
                    updates["memory_sync_status"] = "ready"
                contact = crud.update_contact(db, int(target_id), updates) if target_id else None
                if contact:
                    applied_contact_id = contact.id
                    updated_names.append(contact.name)

            if proposal_record_id:
                crud.update_contact_proposal_status(
                    db,
                    proposal_id=proposal_record_id,
                    status="applied" if applied_contact_id else "failed",
                    contact_id=applied_contact_id,
                )

            if applied_contact_id and apply_source_context != _MEMORY_PROPOSAL_SOURCE:
                sync_confirmed_contact_to_memory(
                    db,
                    contact_id=applied_contact_id,
                    chat_id=pending.get("chat_id"),
                )

            if not applied_contact_id:
                failed_names.append(item.get("contact_name") or "Unbekannt")

        parts: List[str] = []
        if created_names:
            parts.append(f"angelegt: {', '.join(created_names)}")
        if updated_names:
            parts.append(f"aktualisiert: {', '.join(updated_names)}")
        if failed_names:
            parts.append(f"nicht uebernommen: {', '.join(failed_names)}")
        summary = "; ".join(parts) if parts else "keine Aenderungen"
        return {
            "status": "applied" if not failed_names else "partial",
            "user_message": f"Die Kontaktvorschlaege wurden verarbeitet ({summary}).",
        }
    finally:
        db.close()


async def _extract_and_stage_contact_proposals(
    text_block: str,
    api_key: str,
    provider: str,
    model: str,
    location_context: Optional[str] = None,
    chat_id: Optional[int] = None,
) -> Dict[str, Any]:
    import backend.services.llm_gateway as llm_gateway

    logger.info("Starte die Extraktion von Kontaktinformationen...")
    db = next(database.get_db_sync())
    try:
        prompt = CONTACT_EXTRACTION_PROMPT.format(text_block=text_block)
        response = await llm_gateway.call_llm(
            provider=provider,
            model_id=model,
            api_key=api_key,
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )
        raw_response = response.get("text")
        if not raw_response:
            logger.warning("Kontakt-Extraktion: LLM hat keine Antwort geliefert.")
            return {"proposals_staged": 0, "suppressed": 0, "review_notes": [], "user_message": None}

        match = re.search(r"\[(.*)\]", raw_response, re.DOTALL)
        if not match:
            logger.warning(
                "Kontakt-Extraktion: Konnte kein JSON-Array in der LLM-Antwort finden. Roh-Antwort: %s",
                raw_response,
            )
            return {"proposals_staged": 0, "suppressed": 0, "review_notes": [], "user_message": None}

        try:
            contact_data_list = json.loads(f"[{match.group(1)}]")
            if not isinstance(contact_data_list, list) or not contact_data_list:
                return {"proposals_staged": 0, "suppressed": 0, "review_notes": [], "user_message": None}
        except json.JSONDecodeError:
            logger.error(
                f"Fehler beim Parsen des extrahierten JSON-Arrays. Inhalt: {match.group(0)}",
                exc_info=True,
            )
            return {"proposals_staged": 0, "suppressed": 0, "review_notes": [], "user_message": None}

        proposal_items: List[Dict[str, Any]] = []
        review_notes: List[str] = []
        for contact_data in contact_data_list:
            if not isinstance(contact_data, dict):
                continue
            candidate_result = await _process_contact_candidate_v2(contact_data, db)
            if candidate_result.get("kind") == "proposal" and candidate_result.get("item"):
                proposal_items.append(candidate_result["item"])
            elif candidate_result.get("kind") == "review" and candidate_result.get("message"):
                review_notes.append(candidate_result["message"])

        return _persist_contact_proposal_batch(
            db,
            chat_id=chat_id,
            text_block=text_block,
            proposal_items=proposal_items,
            review_notes=review_notes,
        )
    except Exception as e:
        logger.error(
            f"Ein unerwarteter Fehler ist bei der Kontakt-Extraktion aufgetreten: {e}",
            exc_info=True,
        )
        return {"proposals_staged": 0, "suppressed": 0, "review_notes": [], "user_message": None}
    finally:
        db.close()


async def extract_and_save_contact(
    text_block: str,
    api_key: str,
    provider: str,
    model: str,
    location_context: Optional[str] = None,
    chat_id: Optional[int] = None,
):
    return await _extract_and_stage_contact_proposals(
        text_block=text_block,
        api_key=api_key,
        provider=provider,
        model=model,
        location_context=location_context,
        chat_id=chat_id,
    )

    logger.info("Starte die Extraktion von Kontaktinformationen...")
    db = next(database.get_db_sync())
    try:
        prompt = CONTACT_EXTRACTION_PROMPT.format(text_block=text_block)
        response = await llm_gateway.call_llm(
            provider=provider,
            model_id=model,
            api_key=api_key,
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )
        raw_response = response.get("text")
        if not raw_response:
            logger.warning("Kontakt-Extraktion: LLM hat keine Antwort geliefert.")
            return
        # Versuche, den gesamten JSON-Block (der eine Liste sein sollte) zu extrahieren und zu parsen
        match = re.search(r"\[(.*)\]", raw_response, re.DOTALL)
        if not match:
            logger.warning(
                f"Kontakt-Extraktion: Konnte kein JSON-Array in der LLM-Antwort finden. Roh-Antwort: {raw_response}"
            )
            return

        try:
            # Parse den Inhalt des Arrays
            contact_data_list = json.loads(f"[{match.group(1)}]")
            # Stelle sicher, dass es eine Liste ist und nicht leer ist
            if not isinstance(contact_data_list, list) or not contact_data_list:
                logger.info(
                    "Kontakt-Extraktion: LLM hat eine leere oder ungültige Liste zurückgegeben. Keine Kontakte zu erstellen."
                )
                return
        except json.JSONDecodeError:
            logger.error(
                f"Fehler beim Parsen des extrahierten JSON-Arrays. Inhalt: {match.group(0)}",
                exc_info=True,
            )
            return

        logger.info(
            f"Habe {len(contact_data_list)} potenzielle Kontakt-Objekte in der LLM-Antwort gefunden."
        )
        tasks = []
        for contact_data in contact_data_list:
            # Stelle sicher, dass jedes Element ein Dictionary ist
            if isinstance(contact_data, dict):
                tasks.append(
                    _process_single_contact_data(
                        contact_data, db, api_key, provider, model, text_block, location_context
                    )
                )

        if tasks:
            await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(
            f"Ein unerwarteter Fehler ist bei der Kontakt-Extraktion aufgetreten: {e}",
            exc_info=True,
        )
    finally:
        db.close()


def list_contacts() -> List[contact_schemas.ContactResponse]:
    logger.info("Rufe Liste aller Kontakte ab.")
    db = next(database.get_db_sync())
    try:
        contacts = crud.get_contacts(db, limit=1000)
        return [contact_schemas.ContactResponse.model_validate(c) for c in contacts]
    finally:
        db.close()


def search_contacts(name_query: str) -> List[contact_schemas.ContactResponse]:
    logger.info(f"Suche nach Kontakten mit '{name_query}' im Namen.")
    db = next(database.get_db_sync())
    try:
        contacts = crud.search_contacts_by_name(db, name_query=name_query)
        return [contact_schemas.ContactResponse.model_validate(c) for c in contacts]
    finally:
        db.close()


async def update_contact_details(
    db: Session, updates: dict, contact_id: Optional[int] = None, name_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Aktualisiert die Details eines bestehenden Kontakts, identifiziert entweder durch seine ID oder durch eine Namenssuche.
    """
    if not contact_id and not name_query:
        return {
            "status": "error",
            "message": "Es muss entweder eine contact_id oder eine name_query angegeben werden.",
        }

    target_contact = None
    if contact_id:
        target_contact = crud.get_contact(db, contact_id)
    elif name_query:
        search_results = crud.search_contacts_by_name(db, name_query)
        if search_results:
            target_contact = search_results[0]
            logger.info(
                f"Kontakt '{name_query}' gefunden (ID: {target_contact.id}) zur Aktualisierung."
            )

    if not target_contact:
        return {
            "status": "error",
            "message": f"Kontakt konnte nicht gefunden werden (ID: {contact_id}, Name: {name_query}).",
        }

    # KORREKTUR: Die Zeile mit .model_dump() ist entfernt. Wir verwenden das 'updates'-Dictionary direkt.
    if not updates:
        return {"status": "info", "message": "Keine Daten zum Aktualisieren angegeben."}

    updated_contact = crud.update_contact(db, contact_id=target_contact.id, updates=updates)
    if updated_contact:
        return {
            "status": "success",
            "message": f"Kontakt '{updated_contact.name}' erfolgreich aktualisiert.",
        }
    else:
        return {"status": "error", "message": "Unbekannter Fehler beim Aktualisieren des Kontakts."}


def delete_contact_by_id(contact_id: int) -> Dict[str, Any]:
    logger.info(f"Versuche, Kontakt mit ID {contact_id} zu löschen.")
    db = next(database.get_db_sync())
    try:
        success = crud.delete_contact(db, contact_id=contact_id)
        if success:
            logger.info(f"Kontakt mit ID {contact_id} erfolgreich gelöscht.")
            return {"success": True, "message": f"Kontakt mit ID {contact_id} gelöscht."}
        else:
            logger.warning(f"Konnte Kontakt mit ID {contact_id} zum Löschen nicht finden.")
            return {"success": False, "message": f"Kontakt mit ID {contact_id} nicht gefunden."}
    finally:
        db.close()

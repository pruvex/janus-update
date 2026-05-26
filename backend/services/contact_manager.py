import asyncio
import json
import logging
import re
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

        # --- WICHTIG: Prüfung der Kategorie (Privatsphäre-Schutz) ---
        if contact.category and contact.category.lower() in ["privat", "persönlich", "private"]:
            logger.info(
                f"Contact '{contact.name}' is categorized as '{contact.category}'. Skipping web enrichment for private individuals."
            )
            return

        if contact.phone and contact.email and contact.address:
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
            if (
                text_block
                and contact.category
                and contact.category.lower() not in ["privat", "persönlich"]
            ):
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
            # --- BUGFIX START: Hilfsfunktion für Listen-Handling ---
            def ensure_string(value):
                """Wandelt Listen (z.B. mehrere Telefonnummern) in einen String um."""
                if isinstance(value, list):
                    return ", ".join(str(v) for v in value)
                return value

            # --- BUGFIX END ---

            fields_to_update = {}

            # Phone
            if enriched_data.get("phone") and not contact.phone:
                clean_phone = ensure_string(enriched_data["phone"])
                contact.phone = clean_phone
                fields_to_update["phone"] = clean_phone

            # Email
            if enriched_data.get("email") and not contact.email:
                clean_email = ensure_string(enriched_data["email"])
                contact.email = clean_email
                fields_to_update["email"] = clean_email

            # Address
            if enriched_data.get("address") and not contact.address:
                clean_address = ensure_string(enriched_data["address"])
                contact.address = clean_address
                fields_to_update["address"] = clean_address

            # Website (hier war deine Validierungslogik, wir wenden ensure_string auch hier sicherheitshalber an, falls LLM eine Liste von URLs sendet)
            if enriched_data.get("website") and not contact.website:
                raw_url = ensure_string(enriched_data["website"])

                # Validate the extracted URL against search results
                websearch_urls = websearch_result.get("urls", [])
                validated_url = _validate_extracted_url(raw_url, websearch_urls)

                if validated_url and validated_url != raw_url:
                    logger.warning(
                        f"Corrected URL for {contact.name}: {raw_url} -> {validated_url}"
                    )

                normalized_website = _normalize_url(validated_url or raw_url)
                if normalized_website:
                    contact.website = normalized_website
                    fields_to_update["website"] = normalized_website
            if fields_to_update:
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


async def extract_and_save_contact(
    text_block: str, api_key: str, provider: str, model: str, location_context: Optional[str] = None
):
    # Import inside function to avoid circular dependency
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

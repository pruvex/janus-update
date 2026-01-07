import asyncio
import logging
from typing import Optional

import requests
from geopy.geocoders import Nominatim
from pydantic import BaseModel, Field

from backend.services import llm_gateway

# Imports aus dem Backend
from backend.services.websearch.websearch import perform_websearch_service

logger = logging.getLogger("janus_backend")

# --- Pydantic Models für Tool Arguments ---


class CleanGetDistanceArgs(BaseModel):
    origin: str = Field(..., description="Startadresse (Stadt/Ort).")
    destination: str = Field(..., description="Zieladresse (Stadt/Ort).")
    mode: str = Field(
        "driving", description="Modus: 'driving' (Auto). Aktuell wird primär Auto unterstützt."
    )


class FindLocalBusinessArgs(BaseModel):
    query: str = Field(
        ..., description="Was gesucht wird (z.B. 'Pizzeria', 'Kino', 'Museum', 'Park')."
    )
    location: Optional[str] = Field(
        None, description="Ort (z.B. 'Köln'). Wenn leer, wird 'in meiner Nähe' angenommen."
    )


class GetCountryInfoToolArgs(BaseModel):
    country_name: str = Field(..., description="Name des Landes.")


# --- Helper ---


def _format_duration(seconds: float) -> str:
    """Formatiert Sekunden in Std. und Min."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours} Std. {minutes} Min."
    return f"{minutes} Min."


# --- Tools ---


async def get_distance_and_route_tool(
    origin: str, destination: str, mode: str = "driving", **kwargs
) -> dict:
    """
    Berechnet die echte Distanz und Fahrzeit zwischen zwei Orten mittels OSRM (Open Source Routing Machine).
    Benötigt keinen API Key.
    """
    geolocator = Nominatim(user_agent="janus_geo_tool", timeout=20)

    try:
        # 1. Geocoding: Koordinaten finden
        logger.info(f"Geocoding für Route: {origin} -> {destination}")
        # Nutzung von asyncio.to_thread, um den Main-Loop nicht zu blockieren
        loc_origin = await asyncio.to_thread(geolocator.geocode, origin)
        loc_dest = await asyncio.to_thread(geolocator.geocode, destination)

        if not loc_origin or not loc_dest:
            return {
                "status": "error",
                "output": f"Konnte einen der Orte nicht finden: '{origin}' oder '{destination}'. Bitte präzisiere die Eingabe.",
            }

        # 2. OSRM API Anfrage (Kostenlos)
        # WICHTIG: OSRM erwartet Format {longitude},{latitude}
        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{loc_origin.longitude},{loc_origin.latitude};{loc_dest.longitude},{loc_dest.latitude}?overview=false"

        response = await asyncio.to_thread(requests.get, osrm_url, timeout=30)

        if response.status_code != 200:
            return {
                "status": "error",
                "output": "Fehler bei der Routenberechnung (OSRM API nicht erreichbar).",
            }

        data = response.json()

        if "routes" not in data or not data["routes"]:
            return {"status": "error", "output": "Keine Route zwischen diesen Orten gefunden."}

        route = data["routes"][0]
        # OSRM gibt Meter zurück -> in km umrechnen
        distance_km = round(route["distance"] / 1000, 1)
        # OSRM gibt Sekunden zurück -> formatieren
        duration_str = _format_duration(route["duration"])

        maps_link = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&travelmode={mode}"

        result_text = (
            f"Die Route von **{origin}** nach **{destination}** beträgt ca. **{distance_km} km**.\n"
            f"Die geschätzte Fahrzeit (ohne Verkehr) beträgt **{duration_str}**.\n"
            f"[Route auf Google Maps öffnen]({maps_link})"
        )

        return {
            "status": "success",
            "origin": origin,
            "destination": destination,
            "distance_km": distance_km,
            "duration": duration_str,
            "output": result_text,
            "maps_link": maps_link,
        }

    except Exception as e:
        logger.error(f"Fehler im Geo-Tool: {e}", exc_info=True)
        return {"status": "error", "message": f"Fehler bei der Berechnung: {str(e)}"}


async def find_local_business_tool(
    query: str,
    location: Optional[str] = None,
    api_key: str = "",
    provider: str = "openai",
    model: str = "gpt-5-nano",  # Internal alias for the default model
    **kwargs,
) -> dict:
    """
    Sucht nach lokalen Orten, Geschäften oder Dienstleistern und extrahiert strukturierte Daten.
    """
    try:
        loc_str = location if location else "in meiner Nähe"

        # OPTIMIERUNG: Suchanfrage auf Daten fokussieren
        search_query = f"{query} in {loc_str} Adresse Öffnungszeiten offizielle Website"

        logger.info(f"Lokal-Suche gestartet: '{search_query}'")

        search_results = await perform_websearch_service(
            query=search_query, api_key=api_key, provider=provider, model=model
        )

        raw_text = search_results.get("text", "")
        if not raw_text:
            return {
                "status": "error",
                "output": f"Keine Suchergebnisse für {query} in {loc_str} gefunden.",
            }

        # OPTIMIERUNG: Strengerer Prompt gegen Google Maps Links
        extraction_prompt = f"""
        Du bist ein Daten-Analyst für lokale Suchergebnisse.
        
        DEINE AUFGABE:
        Analysiere die Suchergebnisse für "{query}" in "{loc_str}".
        Erstelle eine Liste der 3-5 besten Treffer.

        REGELN FÜR DIE AUSGABE:
        1. **Format:** Markdown-Liste.
        2. **Adresse:** Extrahiere Straße und Hausnummer. Falls NICHT im Text, schreibe "Adresse folgt".
        3. **Website:** 
           - Das Ziel ist die OFFIZIELLE Website (z.B. www.name-des-lokals.de).
           - IGNORIERE Links, die mit 'google.com/maps', 'facebook.com', 'instagram.com' oder Bewertungsportalen beginnen, es sei denn, es gibt nichts anderes.
           - Wenn du nur einen Google-Maps-Link findest, lass das Feld 'Website' lieber leer oder schreibe "Keine Website gefunden".
        4. **Beschreibung:** Ein kurzer Satz zum Angebot.

        SUCHERGEBNISSE:
        {raw_text[:7000]}
        """

        response = await llm_gateway.call_llm(
            provider=provider,
            model_id=model,
            api_key=api_key,
            messages=[{"role": "user", "content": extraction_prompt}],
            tools=None,
            force_no_tools=True,
        )

        extracted_info = response.get("text", "Konnte Ergebnisse nicht zusammenfassen.")

        # Trigger Background Enrichment (Adressbuch)
        if extracted_info and len(extracted_info) > 50:
            try:
                from backend.services import contact_manager

                logger.info("Starte automatische Adressbuch-Speicherung für Suchergebnisse...")
                asyncio.create_task(
                    contact_manager.extract_and_save_contact(
                        text_block=extracted_info,
                        api_key=api_key,
                        provider=provider,
                        model=model,
                        location_context=loc_str,
                    )
                )
            except Exception as cm_e:
                logger.error(f"Fehler beim Anstoßen der Kontakt-Speicherung: {cm_e}")

        return {
            "status": "success",
            "output": extracted_info,
            "search_url": f"https://www.google.com/search?q={search_query.replace(' ', '+')}",
        }

    except Exception as e:
        logger.error(f"Fehler in find_local_business_tool: {e}", exc_info=True)
        return {"status": "error", "output": f"Fehler bei der Lokalsuche: {str(e)}"}


async def get_country_info_tool(
    country_name: str,
    api_key: str = "",
    provider: str = "openai",
    model: str = "gpt-5-nano",  # Internal alias for the default model
    **kwargs,
) -> dict:
    """
    Liefert Basisinformationen über ein Land.
    """
    try:
        query = f"Fakten über {country_name}: Hauptstadt, Einwohnerzahl, Währung, Sprache"
        search_results = await perform_websearch_service(
            query=query, api_key=api_key, provider=provider, model=model
        )
        return {"status": "success", "output": search_results.get("text", "Keine Infos gefunden.")}
    except Exception as e:
        return {"status": "error", "output": str(e)}

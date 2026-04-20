import json
from typing import Any, Dict, List, Optional


def _is_renderable_local_business(item: Dict[str, Any]) -> bool:
    if not isinstance(item, dict):
        return False
    name = " ".join(str(item.get("name") or "").strip().lower().split())
    address = " ".join(str(item.get("address") or "").strip().lower().split())
    website = str(item.get("website") or "").strip()
    blocked_name_markers = {
        "keine passenden suchergebnisse gefunden",
        "keine passenden treffer gefunden",
        "keine treffer gefunden",
        "keine passenden restaurants gefunden",
        "adresse nicht gefunden",
        "nicht gefunden",
    }
    if not name:
        return False
    if any(marker in name for marker in blocked_name_markers):
        return False
    if address == "adresse nicht gefunden" and not website:
        return False
    return True


def render_local_business_from_tool_results(tool_results: List[Dict[str, Any]]) -> Optional[str]:
    businesses: List[Dict[str, Any]] = []
    location = ""
    query = ""
    for res in tool_results or []:
        if not isinstance(res, dict):
            continue
        if str(res.get("_skill_id") or "").strip() != "system.local_business":
            continue
        try:
            payload = json.loads(res.get("content", "{}"))
        except Exception:
            continue
        if not isinstance(payload, dict) or payload.get("status") != "ok":
            continue
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        location = str(data.get("location") or location or "").strip()
        query = str(data.get("query") or query or "").strip()
        items = data.get("businesses") if isinstance(data.get("businesses"), list) else []
        for item in items:
            if isinstance(item, dict) and _is_renderable_local_business(item):
                businesses.append(item)
    if not businesses:
        return None
    intro = "Hier sind passende Läden"
    if query and location:
        intro = f"Hier sind passende {query} in {location}"
    elif query:
        intro = f"Hier sind passende {query}"
    elif location:
        intro = f"Hier sind passende Läden in {location}"
    lines: List[str] = [f"{intro}:", ""]
    for business in businesses:
        name = str(business.get("name") or "Unbekannter Laden").strip()
        description = str(business.get("description") or "").strip()
        category = str(business.get("category") or "").strip()
        address = str(business.get("address") or "Adresse nicht gefunden").strip()
        opening_hours = str(business.get("opening_hours") or "").strip()
        phone = str(business.get("phone") or "").strip()
        website = str(business.get("website") or "").strip()
        menu_url = str(business.get("menu_url") or "").strip()
        reservation_url = str(business.get("reservation_url") or "").strip()

        lines.append(f"**{name}**")
        if description:
            lines.append(description)
        if category:
            lines.append(f"_{category}_")
        lines.append(f"Adresse: {address}")
        if opening_hours:
            lines.append(f"Öffnungszeiten: {opening_hours}")
        if phone:
            lines.append(f"Telefon: {phone}")
        if website:
            lines.append(f"Website: {website}")
        if menu_url:
            lines.append(f"Speisekarte: [Link]({menu_url})")
        if reservation_url:
            lines.append(f"Reservierung: [Link]({reservation_url})")
        lines.append("")
    return "\n".join(lines).strip()


def render_local_business_no_results_text(tool_results: List[Dict[str, Any]]) -> Optional[str]:
    location = ""
    query = ""
    result_count: Optional[int] = None
    message = ""
    for res in tool_results or []:
        if not isinstance(res, dict):
            continue
        if str(res.get("_skill_id") or "").strip() != "system.local_business":
            continue
        try:
            payload = json.loads(res.get("content", "{}"))
        except Exception:
            continue
        if not isinstance(payload, dict) or payload.get("status") != "ok":
            continue
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        location = str(data.get("location") or location or "").strip()
        query = str(data.get("query") or query or "").strip()
        if isinstance(data.get("result_count"), int):
            result_count = int(data.get("result_count"))
        message = str(data.get("message") or message or "").strip()
        items = data.get("businesses") if isinstance(data.get("businesses"), list) else []
        if any(isinstance(item, dict) and _is_renderable_local_business(item) for item in items):
            return None
    if result_count is not None and result_count > 0:
        return None
    if query and location:
        return (
            f"Ich konnte aktuell keine verlässlichen Treffer für {query} in {location} extrahieren. "
            "Bitte versuche es gleich noch einmal oder formuliere die Suche etwas konkreter, z. B. mit Straße, Bezirk oder Restaurant-Typ."
        )
    if message:
        return message
    return None


def render_routing_segments_text(segments: List[Dict[str, str]]) -> str:
    lines: List[str] = []
    for idx, seg in enumerate(segments or [], start=1):
        distance = f"{seg['distance_km']} km" if seg.get("distance_km") else "Distanz n/a"
        duration = seg.get("duration") or "Dauer n/a"
        lines.append(f"{idx}. {seg['origin']} -> {seg['destination']}: {distance}, {duration}")

    unique_links: List[str] = []
    for seg in segments or []:
        link = str(seg.get("maps_link") or "").strip()
        if link and link not in unique_links:
            unique_links.append(link)

    body = "Routenuebersicht (aus Tool-Ergebnissen):\n" + "\n".join(lines)
    if unique_links:
        body += "\n\nGoogle Maps Links:\n" + "\n".join(f"- {link}" for link in unique_links)
    return body


def append_missing_pdf_paths(text: str, pdf_paths: List[str]) -> str:
    normalized_text = str(text or "")
    missing_paths = [str(path).strip() for path in (pdf_paths or []) if str(path).strip() and str(path).strip() not in normalized_text]
    if not missing_paths:
        return normalized_text
    path_lines = "\n".join(f"- {path}" for path in missing_paths)
    suffix = f"\n\nGespeicherte PDF-Datei(en):\n{path_lines}"
    return f"{normalized_text.rstrip()}{suffix}" if normalized_text.strip() else f"Gespeicherte PDF-Datei(en):\n{path_lines}"


def append_missing_pdf_facts(text: str, facts: List[str]) -> str:
    normalized_text = str(text or "")
    lowered = normalized_text.lower()
    missing_facts = [str(fact).strip() for fact in (facts or []) if str(fact).strip() and str(fact).strip().lower() not in lowered]
    if not missing_facts:
        return normalized_text
    facts_block = "\n".join(f"- {fact}" for fact in missing_facts)
    suffix = f"\n\nHier sind die recherchierten Fakten:\n{facts_block}"
    return f"{normalized_text.rstrip()}{suffix}" if normalized_text.strip() else f"Hier sind die recherchierten Fakten:\n{facts_block}"

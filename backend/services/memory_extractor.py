# backend/services/memory_extractor.py

import asyncio
import datetime
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.services import llm_gateway, memory_manager, vector_service
from backend.llm_providers.base_provider import BaseLLMProvider
from backend.data.schemas import (
    ExtractedFact,
    FactExtractionResponse,
    MemoryCategory
)

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

# DIAMOND MEMORY EXTRACTION (V17 - STRUCTURED GOLD STANDARD)
EXTRACTION_PROMPT = """
Du bist eine deutsche, hyper-pedantische Logik-Engine. Deine einzige Funktion ist die Umwandlung von Gesprächsfetzen in strukturierte, atomare Fakten im JSON-Format. Halte dich exakt und ohne Ausnahme an die folgenden Regeln.

### REGEL 1: ZERLEGUNG & STRUKTURIERUNG
Zerlege jede Information in ihre kleinsten, logischen Bestandteile und fülle die Felder des `ExtractedFact` Schemas aus.

### REGEL 1.5: IDENTITÄT VS. ZUSTAND TRENNEN
Wenn eine Person mit Name, Beziehung UND einer Eigenschaft genannt wird (z.B. "meine oma gertrude liebt katzen"), MUSST du IMMER ZWEI atomare Fakten erstellen:
1.  **Einen Identitäts-Fakt:** Wer diese Person ist.
2.  **Einen Zustands-Fakt:** Welche Eigenschaft diese Person hat.

### REGEL 1.6: KANONISCHE SCHLÜSSEL FÜR PROJEKTE UND ENTSCHEIDUNGEN
- Verwende für Projekte das Format: `projekt:<projektname>` (z.B. `projekt:aquila`)
- Für Prioritäten: `hat_prioritaet|projekt:<name>|<prioritaet>` (z.B. `hat_prioritaet|projekt:aquila|leistung`)
- Für Budget: `hat_budget|projekt:<name>|<budgetstufe>` (z.B. `hat_budget|projekt:aquila|niedrig`)
- Für Zeitrahmen: `hat_zeitrahmen|projekt:<name>|<zeitrahmen>` (z.B. `hat_zeitrahmen|projekt:aquila|kurz`)
- Für Team-Expertise: `hat_expertise|projekt:<name>|<stufe>` (z.B. `hat_expertise|projekt:aquila|hoch`)
- Für Risikotoleranz: `hat_risikotoleranz|projekt:<name>|<stufe>` (z.B. `hat_risikotoleranz|projekt:aquila|mittel`)

**Beispiel Input 1:** "Projekt Aquila hat hohe Priorität auf Leistung"
**Korrekter Output:**
[
  {
    "fact": "Das Projekt Aquila hat hohe Priorität auf Leistung.",
    "category": "Projektmanagement",
    "type": "CORE_DETAIL",
    "canonical_key": "hat_prioritaet|projekt:aquila|leistung",
    "subject_role": "project",
    "subject_name": "Aquila",
    "predicate": "hat_prioritaet",
    "object_value": "leistung",
    "evidence": "Projekt Aquila hat hohe Priorität auf Leistung"
  }
]

**Beispiel Input 2:** "Für das Projekt Aquila haben wir nur ein kleines Budget"
**Korrekter Output:**
[
  {
    "fact": "Das Projekt Aquila hat ein kleines Budget.",
    "category": "Finanzen",
    "type": "CORE_DETAIL",
    "canonical_key": "hat_budget|projekt:aquila|niedrig",
    "subject_role": "project",
    "subject_name": "Aquila",
    "predicate": "hat_budget",
    "object_value": "niedrig",
    "evidence": "Für das Projekt Aquila haben wir nur ein kleines Budget"
  }
]

**Beispiel Input 3:** "Unser Team hat hohe Expertise in Python"
**Korrekter Output:**
[
  {
    "fact": "Das Team hat hohe Expertise in Python.",
    "category": "Team",
    "type": "CORE_DETAIL",
    "canonical_key": "hat_expertise|team|python",
    "subject_role": "team",
    "subject_name": "Team",
    "predicate": "hat_expertise",
    "object_value": "python",
    "evidence": "Unser Team hat hohe Expertise in Python"
  }
]

### REGEL 2: KANONISCHER SCHLÜSSEL (`canonical_key`)
Jeder Fakt MUSS einen kanonischen Schlüssel haben, der wie folgt aufgebaut ist: `predicate|subject|object`

1. **PRÄDIKAT (predicate):**
   - Beschreibt die Beziehung zwischen Subjekt und Objekt
   - Im Infinitiv (z.B. 'haben', 'sein', 'mögen', 'brauchen')
   - Keine Leerzeichen, stattdessen Unterstriche verwenden
   - Beispiele: 'hat_allergie', 'mag', 'ist', 'hat_hobby'

2. **SUBJEKT (subject):**
   - Format: `rolle:typ:name` (z.B. `relative:onkel:hubert`)
   - Mögliche Rollen: 'user', 'relative', 'pet', 'contact', 'location', 'object'
   - Typen sind rollenspezifisch (z.B. für 'relative': 'vater', 'mutter', 'onkel', 'tante')
   - Namen in Kleinbuchstaben, Umlaute ersetzen (ä→ae, ö→oe, ü→ue, ß→ss)
   - Wenn kein Name bekannt: `rolle:typ`

3. **OBJEKT (object):**
   - Der Wert oder das Ziel der Beziehung
   - Im Singular, Kleinbuchstaben, keine Umlaute
   - Keine Sonderzeichen außer Unterstrichen
   - Wenn es sich um eine Eigenschaft handelt (z.B. Alter, Größe), das Format 'eigenschaft:wert' verwenden

4. **NORMALISIERUNG (OBLIGATORISCH):**
   - ALLE Zeichen in Kleinbuchstaben
   - Umlaute ersetzen: ä→ae, ö→oe, ü→ue, ß→ss
   - Leerzeichen und Sonderzeichen durch Unterstriche ersetzen
   - Immer Singular verwenden
   - Keine Artikel (der, die, das, ein, eine)
   - Keine Präpositionen (mit, für, zu, etc.)

5. **BEISPIELE:**
   - `hat_allergie|relative:onkel:hubert|katzenhaare`
   - `mag|user|schokolade`
   - `hat_geburtstag|relative:oma:gertrude|15_maerz`
   - `ist|user|vegetarier`
   - `wohnt_in|user|berlin`
   - `hat_alter|relative:vater|alter:65`

6. **FEHLER VERMEIDEN:**
   - Jeder Fakt MUSS einen gültigen canonical_key haben
   - Der Key MUSS dem Format entsprechen
   - Keine doppelten Unterstriche oder führende/abschließende Unterstriche
   - Keine Leerzeichen, Sonderzeichen oder Umlaute im Key

### REGEL 3: STRIKTES KATEGORIEN- & TYPEN-MANIFEST
Verwende NUR die erlaubten Werte aus dem `ExtractedFact` JSON Schema für `category`, `type`, `predicate`, `subject_role` etc.

### REGEL 4: "EVIDENCE"-PFLICHT (ANTI-HALLUZINATION)
Jeder Fakt MUSS ein `evidence`-Feld haben, das den exakten, kurzen Textausschnitt des Benutzers enthält, der den Fakt belegt. Wenn du keinen direkten Beleg im User-Text findest, darfst du den Fakt NICHT generieren. KEINE INFERENZ!

### REGEL 5: ANTI-REDUNDANZ
Erzeuge für denselben Sachverhalt immer denselben `canonical_key`. Das System verwirft Duplikate automatisch.

Dein Output muss ein valides `FactExtractionResponse` JSON sein.
"""


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
        provider_instance = llm_gateway.get_provider(provider)
        from backend.services.cost_service import create_cost_entry

        extracted_data, cost_data = await provider_instance.generate_structured_response(
            api_key=main_api_key,
            model=model,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": text_block}
            ],
            response_format=FactExtractionResponse
        )

        if cost_data and "total_cost" in cost_data:
            try:
                create_cost_entry(
                    db=db, amount=cost_data["total_cost"], model=model, provider=provider,
                    source_type="fact_extraction", input_tokens=cost_data.get("input_tokens", 0),
                    output_tokens=cost_data.get("output_tokens", 0)
                )
            except Exception as e:
                logger.error(f"Kosten für Memory-Extraktion konnten nicht gespeichert werden: {e}")

        extracted_items = [fact.dict() for fact in extracted_data.facts]
        
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

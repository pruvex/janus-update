import logging
import base64
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from collections import defaultdict
from sqlalchemy.orm import Session

from backend.data import crud, schemas
from backend.services import memory_manager, vector_service
from backend.utils import intent_classifier
from backend.utils.paths import get_app_data_dir
from backend.prompts import tool_directive, fact_directive

logger = logging.getLogger("janus_backend")

class ContextBuilder:
    """
    Baut den Kontext (Nachrichten, System-Prompt, Bilder) für das LLM zusammen.
    """
    def __init__(self, db: Session):
        self.db = db

    def build_system_message(
        self, 
        active_personality: Dict, 
        user_prompt: str, 
        email_context: List[Any] = None,
        facts: List[Any] = None
    ) -> Optional[Dict]:
        """Erstellt den System-Prompt basierend auf Persönlichkeit, Memory und Kontext.
        
        Args:
            active_personality: Dictionary mit den Persönlichkeitseinstellungen
            user_prompt: Die aktuelle Nutzereingabe
            email_context: Optionaler E-Mail-Kontext
            facts: Liste der relevanten Fakten für den aktuellen Kontext
            
        Returns:
            Dictionary mit der Rolle "system" und dem formatierten Inhalt
        """
        # 1. Basis-Persona
        name = active_personality.get("name", "Janus")
        traits = ", ".join(active_personality.get("traits", ["hilfsbereit", "kompetent"]))
        style = active_personality.get("communication_style", "klar und direkt")
        
        # 2. Zeit-Anker
        now = datetime.now()
        date_str = now.strftime("%A, der %d. %B %Y")
        time_str = now.strftime("%H:%M Uhr")
        
        # 3. RAG / Memory Kontext (Fakten)
        memory_text = self._get_memory_context(facts) if facts else ""
        
        # 4. Adressbuch
        address_text = self._get_address_book_context(user_prompt)
        
        # 5. E-Mail Kontext
        email_text = ""
        if email_context:
            email_text = "**Zuletzt gesehene E-Mails:**\n" + "\n".join(
                [f"- {i+1}. Von: {e.get('from')}, Betreff: {e.get('subject')}" 
                 for i, e in enumerate(email_context)]
            )

        # DIAMOND STANDARD PROMPT (Strict No-Citation Version)
        system_prompt = f"""
PRIMÄRDIREKTIVE: Du bist {name}, ein {traits}er KI-Assistent. Dein Kommunikationsstil ist {style}.
Dein Ziel sind korrekte, klare und umsetzbare Antworten.

--- ZEIT-ANKER ---
HEUTIGES DATUM: {date_str}.
AKTUELLE UHRZEIT: {time_str}.
------------------

[WICHTIG: UMGANG MIT WISSEN]
Alle Informationen, die unter 'INFORMATIONEN AUS DEM LANGZEITGEDÄCHTNIS' stehen, sind ab sofort DEIN EIGENES WISSEN.
1. Nutze dieses Wissen direkt.
2. **VERBOT:** Nenne NIEMALS die Quelle (z.B. "Laut Datenbank", "Quelle: Unterhaltung", "Wie ich sehe"). Das zerstört die Illusion eines intelligenten Assistenten.
3. Sprich einfach aus, was du weißt.
   - Falsch: "Laut meiner Erinnerung heißt dein Hund Pody."
   - Richtig: "Dein Hund heißt Pody."

[WERKZEUG-NUTZUNG]
- Wenn der Nutzer eine Aktion wünscht (Termin, Suche, Mail), nutze das entsprechende Tool.
- Erfinde niemals Aktionen, die du nicht ausgeführt hast.

[ANTWORT-STRUKTUR]
- Nutze Markdown für bessere Lesbarkeit.
- Fasse dich kurz.
"""
        
        # Zusammenbau
        full_content_parts = [
            system_prompt.strip(),
            tool_directive,
            fact_directive,
        ]
        
        if address_text: full_content_parts.append(address_text)
        if email_text: full_content_parts.append(email_text)
        if memory_text: full_content_parts.append(memory_text)

        return {"role": "system", "content": "\n\n".join(full_content_parts)}

    def build_chat_history(self, chat_id: int, limit: int = 20) -> List[Dict]:
        """Lädt die letzten N Nachrichten aus der DB."""
        db_msgs = crud.get_messages_by_chat_id(self.db, chat_id)
        history = []
        
        # Wir nehmen die letzten 'limit' Nachrichten
        # Da db_msgs chronologisch sind (alt -> neu), nehmen wir das Ende
        relevant_msgs = db_msgs[-limit:] if len(db_msgs) > limit else db_msgs
        
        for m in relevant_msgs:
            role = "user" if m.sender == "user" else "assistant"
            history.append({"role": role, "content": m.content})
            
        return history

    def build_planner_prompt(self, candidates: List[Dict]) -> str:
        """
        Erstellt einen System-Prompt, der das LLM zwingt, einen Plan zu schmieden.
        
        Args:
            candidates: Liste von Dictionaries mit 'tool_name' und 'confidence' für jedes Tool
            
        Returns:
            str: Formatierten Prompt-Text für das LLM
        """
        tools_list = ", ".join([c["tool_name"] for c in candidates])
        return (
            f"SYSTEM INSTRUCTION: AMBIGUOUS INTENT DETECTION\n"
            f"The user's request is ambiguous, but likely involves these tools: {tools_list}.\n"
            f"DO NOT execute tools yet. DO NOT output JSON.\n"
            f"Instead, analyze the request and propose a plan or ask clarifying questions to the user.\n"
            f"Output a natural language response explaining what you intend to do or what information is missing."
        )

    def prepare_image_input(self, image_url: Optional[str], chat_id: int, user_prompt: str) -> Optional[str]:
        """
        Entscheidet, ob ein Bild geladen werden soll (neu oder aus History).
        Gibt den Base64-String oder URL zurück.
        """
        if image_url:
            return image_url # User hat gerade eins hochgeladen

        # Check: Sollen wir eins aus der History holen?
        # FIX: Nutze die interne Methode mit Unterstrich, wie im originalen Code
        if hasattr(intent_classifier, "_is_image_unrelated_task"):
             if intent_classifier._is_image_unrelated_task(user_prompt):
                return None
        elif hasattr(intent_classifier, "is_image_unrelated_task"):
             if intent_classifier.is_image_unrelated_task(user_prompt):
                return None

        # Suche letztes Bild im Chat
        messages = crud.get_messages_by_chat_id(self.db, chat_id)
        for msg in reversed(messages):
            if msg.image_path:
                # Versuche zu laden
                try:
                    base_dir = os.path.join(get_app_data_dir(), "images")
                    rel_path = msg.image_path.replace("/user_images/", "")
                    full_path = os.path.join(base_dir, rel_path)
                    
                    if os.path.exists(full_path):
                        with open(full_path, "rb") as f:
                            encoded = base64.b64encode(f.read()).decode("utf-8")
                            return f"data:image/png;base64,{encoded}"
                except Exception as e:
                    logger.warning(f"Failed to load history image: {e}")
        return None

    def _get_memory_context(self, facts: List[Any]) -> str:
        """
        Formats the provided facts into a clean, readable format for the LLM.
        
        Args:
            facts: List of fact objects to format
            
        Returns:
            Formatted string with facts grouped by category
        """
        if not facts:
            return ""
            
        try:
            from backend.data.schemas import ExtractedFact
            
            # Group facts by category for better organization
            facts_by_category = {}
            for fact in facts:
                if not isinstance(fact, ExtractedFact):
                    continue
                    
                category = getattr(fact, 'category', 'Allgemein')
                if category not in facts_by_category:
                    facts_by_category[category] = []
                facts_by_category[category].append(fact)
            
            # Build the formatted context
            context_parts = ["**INFORMATIONEN AUS DEM LANGZEITGEDÄCHTNIS:**\n"]
            
            for category, facts in facts_by_category.items():
                context_parts.append(f"**{category.upper()}**")
                
                for fact in facts:
                    # Clean up the fact text
                    fact_text = getattr(fact, 'fact', '').strip()
                    if not fact_text:
                        continue
                        
                    # Remove any existing markdown formatting that might interfere
                    fact_text = fact_text.replace('**', '').replace('`', '')
                    
                    # Add evidence if available
                    evidence = getattr(fact, 'evidence', '')
                    if evidence and evidence not in fact_text:
                        fact_text = f"{fact_text} (Quelle: \"{evidence}\")"
                    
                    # Add to context with proper formatting
                    context_parts.append(f"- {fact_text}")
                
                context_parts.append("")  # Add spacing between categories
            
            # Add a note about memory behavior
            context_parts.append(
                "\n**HINWEIS:** Diese Informationen stammen aus deinem Langzeitgedächtnis. "
                "Falls sich etwas geändert hat, teile mir dies bitte mit, damit ich meine Aufzeichnungen aktualisieren kann."
            )
            
            return "\n".join(context_parts).strip()
            
        except Exception as e:
            logger.error(f"Fehler beim Formatieren des Memory-Kontexts: {str(e)}", exc_info=True)
            return ""

    def _get_address_book_context(self, query: str) -> str:
        """Sucht Kontakte basierend auf Namen im Prompt."""
        if intent_classifier.is_greeting(query): return ""
        
        try:
            names = crud.get_all_contact_names(self.db)
            query_lower = query.lower()
            found = [n for n in names if n.lower() in query_lower]
            
            # Immer User-Namen dazu
            user_name = crud.get_user_name(self.db)
            if user_name: found.append(user_name)
            
            contacts = []
            seen_ids = set()
            
            for name in found:
                matches = crud.search_contacts_by_name(self.db, name)
                for c in matches:
                    if c.id not in seen_ids:
                        seen_ids.add(c.id)
                        contacts.append(f"Kontakt: {c.name} ({c.email or 'Keine Mail'})")
            
            if contacts:
                return "**Adressbuch:**\n" + "\n".join(contacts)
        except Exception:
            pass
        return ""

    def build_chat_history_for_execution(self, chat_id: int, user_prompt: str, active_personality: Dict, 
                                       email_context: Optional[List[Any]] = None, facts: Optional[List[Any]] = None) -> List[Dict]:
        """
        Baut die vollständige Nachrichtenliste für einen LLM-Aufruf,
        inklusive System-Prompt, Verlauf und aktueller User-Nachricht.
        
        Args:
            chat_id: ID des aktuellen Chats
            user_prompt: Die aktuelle Nutzereingabe
            active_personality: Dictionary mit den Persönlichkeitseinstellungen
            email_context: Optionaler E-Mail-Kontext
            facts: Liste der relevanten Fakten für den aktuellen Kontext
            
        Returns:
            Liste von Nachrichten-Dictionaries für den LLM-Aufruf
        """
        # System-Prompt erstellen
        system_message = self.build_system_message(
            active_personality=active_personality,
            user_prompt=user_prompt,
            email_context=email_context,
            facts=facts
        )
        history = self.build_chat_history(chat_id)
        
        messages = []
        if system_message:
            messages.append(system_message)
        messages.extend(history)
        # messages.append({"role": "user", "content": user_prompt}) # Entfernt, da schon in history enthalten
        
        return messages

    def build_safety_prompt(self, risky_candidates: List[str]) -> str:
        """Erstellt einen System-Prompt für die Sicherheitsabfrage."""
        tools_list = ", ".join(risky_candidates)
        return (
            f"SYSTEM ALERT: RISK DETECTED\n"
            f"The user wants to perform a potentially dangerous action with these tools: {tools_list}.\n"
            f"DO NOT execute the tool yet.\n"
            f"Ask the user for confirmation (Yes/No)."
        )

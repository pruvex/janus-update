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
        email_context: List[Any] = None
    ) -> Optional[Dict]:
        """Erstellt den System-Prompt basierend auf Persönlichkeit, Memory und Kontext."""
        
        # 1. Basis-Persona
        persona_text = active_personality.get("prompt", "Du bist ein hilfreicher Assistent.")
        
        # 2. Zeit-Anker
        now = datetime.now()
        days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        time_anchor = (
            f"\n\n--- ZEIT-ANKER ---\n"
            f"HEUTIGES DATUM: {days[now.weekday()]}, der {now.strftime('%d. %B %Y')}.\n"
            f"AKTUELLE UHRZEIT: {now.strftime('%H:%M')} Uhr.\n------------------"
        )
        
        # 3. RAG / Memory Kontext (Fakten)
        memory_text = self._get_memory_context(user_prompt)
        
        # 4. Adressbuch
        address_text = self._get_address_book_context(user_prompt)
        
        # 5. E-Mail Kontext
        email_text = ""
        if email_context:
            email_text = "**Zuletzt gesehene E-Mails:**\n" + "\n".join(
                [f"- {i+1}. Von: {e.get('from')}, Betreff: {e.get('subject')}" 
                 for i, e in enumerate(email_context)]
            )

        # Zusammenbau
        full_content_parts = [
            persona_text, 
            time_anchor, 
            tool_directive, 
            fact_directive
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

    def _get_memory_context(self, query: str) -> str:
        """Sucht relevante Fakten im Vektor-Speicher."""
        all_memories = memory_manager.get_all_searchable_memories(self.db)
        if not all_memories: return ""
        
        snippets = vector_service.find_similar_snippets(
            query_text=query, memories=all_memories, top_k=5, threshold=0.35
        )
        if not snippets: return ""

        # Touch STM (Short Term Memory access update)
        for mem in snippets:
            if hasattr(mem, "memory_type") and mem.memory_type == "stm":
                memory_manager.touch_memory_snippet(self.db, mem.id)

        # Formatieren
        context = ["**WISSENS-KONTEXT:**"]
        for mem in snippets:
            cat = getattr(mem, "category", "Info")
            context.append(f"- [{cat}] {mem.snippet}")
        
        return "\n".join(context)

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

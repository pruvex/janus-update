import logging
import base64
import os
import re
from difflib import SequenceMatcher
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from backend.data import crud
from backend.data.schemas import ExtractedFact
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

[ADRESSBUCH-KONTAKTE]
Wenn unter "**Adressbuch:**" genau passende Kontaktinformationen zur Anfrage stehen, beantworte die Frage direkt mit diesen lokalen Kontaktdaten.
Frage dann NICHT, ob der Nutzer sich selbst oder eine andere Person meint. Namen im Adressbuch sind Kontakte.
Wenn nur wenige Details vorliegen, nenne kurz genau diese bekannten Details und erfinde nichts dazu.

[WERKZEUG-NUTZUNG]
- Wenn der Nutzer eine Aktion wünscht (Termin, Suche, Mail), nutze das entsprechende Tool.
- Erfinde niemals Aktionen, die du nicht ausgeführt hast.

[ANTWORT-STRUKTUR]
- Nutze Markdown für bessere Lesbarkeit.
- Fasse dich kurz.
- **VERBOT:** Gib keine generischen Begrüßungen wie "Hallo", "Hallo Admin", "Wie kann ich helfen?" als Antwort auf konkrete Anfragen.
- Antworte direkt auf die Frage oder Anfrage ohne Smalltalk, es sei denn der Nutzer begrüßt dich explizit.
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
            # Wir prüfen, ob das Attribut 'role' existiert, sonst Fallback auf 'sender' (Legacy Support)
            if hasattr(m, "role"):
                role = m.role  # Das sollte 'user' oder 'assistant' sein
                # Mapping falls in DB 'model' steht:
                if role == "model": 
                    role = "assistant"
            else:
                # Fallback für alte Code-Stellen
                role = "user" if getattr(m, "sender", "user") == "user" else "assistant"
            
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
            f"IMPORTANT: Short direct instructions like 'Erkläre kurz', 'Fasse zusammen', 'Zeig mir' should NOT be treated as ambiguous.\n"
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

    def _get_memory_context(self, facts: List[ExtractedFact]) -> str:
        if not facts:
            return ""

        # 1. Gruppierung nach Subjekt
        grouped_facts = {}
        for fact in facts:
            # Extrahiere den Namen aus dem canonical_key oder subject_name
            # Fallback: Nutze "Allgemein/Unbekannt" wenn kein klares Subjekt erkennbar
            subject = fact.subject_name if fact.subject_name else "Allgemein"
            
            # Normalisierung (Kleinschreibung für Gruppierung)
            subject_key = subject.lower().strip()
            
            if subject_key not in grouped_facts:
                grouped_facts[subject_key] = []
            grouped_facts[subject_key].append(fact.fact)

        # 2. String Construction
        context_parts = ["<memory_context>"]
        context_parts.append("HINWEIS: Hier sind gespeicherte Fakten, gruppiert nach Identität. Vermische NIEMALS Eigenschaften verschiedener Gruppen!")
        
        for subject, fact_list in grouped_facts.items():
            # Überschrift für die Identität (z.B. [MAGGY])
            context_parts.append(f"\n[IDENTITÄT: {subject.upper()}]")
            # Liste der Fakten
            for f_text in fact_list:
                context_parts.append(f"- {f_text}")
        
        context_parts.append("</memory_context>")
        
        return "\n".join(context_parts)


    def _get_address_book_context(self, query: str) -> str:
        """Sucht Kontakte basierend auf Namen im Prompt."""
        if intent_classifier.is_greeting(query): return ""
        
        try:
            query_lower = query.lower()
            query_tokens = {
                token
                for token in re.findall(r"[\wäöüÄÖÜß-]{3,}", query_lower)
                if token
            }
            contacts = []
            seen_ids = set()

            for c in crud.get_contacts(self.db, limit=500):
                aliases = [
                    str(value or "").strip().lower()
                    for value in (getattr(c, "name", None), getattr(c, "nickname", None))
                    if str(value or "").strip()
                ]
                alias_tokens = {
                    token
                    for alias in aliases
                    for token in re.findall(r"[\wäöüÄÖÜß-]{3,}", alias)
                }
                alias_token_match = bool(query_tokens.intersection(alias_tokens))
                if not alias_token_match:
                    alias_token_match = any(
                        SequenceMatcher(None, query_token, alias_token).ratio() >= 0.88
                        for query_token in query_tokens
                        for alias_token in alias_tokens
                    )
                if not (
                    any(
                        alias and re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", query_lower)
                        for alias in aliases
                    )
                    or alias_token_match
                ):
                    continue
                if c.id in seen_ids:
                    continue
                seen_ids.add(c.id)

                fields = []
                if getattr(c, "nickname", None):
                    fields.append(f"Nickname: {c.nickname}")
                if getattr(c, "email", None):
                    fields.append(f"E-Mail: {c.email}")
                if getattr(c, "preferences", None):
                    fields.append("Vorlieben: " + ", ".join(c.preferences))
                if getattr(c, "dislikes", None):
                    fields.append("Abneigungen: " + ", ".join(c.dislikes))
                if getattr(c, "personal_details", None):
                    fields.append("Details: " + ", ".join(c.personal_details))
                contacts.append(f"Kontakt: {c.name} ({'; '.join(fields) if fields else 'Keine Details'})")
            
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

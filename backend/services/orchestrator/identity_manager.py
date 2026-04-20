"""Diamond Identity Manager - Extrahierte Identity-Regex & Realtime-Logik.

Zentralisiert alle Identitäts-basierten Erkennungen für den Orchestrator.
Keine harten Regex-Patterns mehr im Orchestrator - nur noch saubere Service-Calls.
"""

import re
import logging
from typing import List, Optional, Pattern, Any
from dataclasses import dataclass

logger = logging.getLogger("janus_backend")


# ═══════════════════════════════════════════════════════════════════════════════
# IDENTITY REGEX PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

IDENTITY_REGEX_PATTERNS: List[Pattern] = [
    re.compile(r'(?i)(ich bin|ich heiße|mein name ist)\s+([a-zäöüß]+)', re.IGNORECASE),
]

# Wörter die definitiv KEINE Namen sind (für Realtime-Extraction)
NON_NAMES: frozenset = frozenset({
    "hier", "bald", "gerne", "mal", "nicht", "nun", "schon", "erst",
    "auch", "da", "gut", "klar", "sicher", "jetzt", "noch", "müde",
    "hungrig", "fertig", "bereit", "alt", "jung", "froh", "neu",
    "ein", "eine", "der", "die", "das", "mir", "dir", "wer", "was",
    "wie", "sehr",
})


@dataclass
class IdentityDetectionResult:
    """Ergebnis einer Identity-Erkennung."""
    name_found: bool = False
    name: Optional[str] = None
    raw_match: Optional[str] = None
    pattern_used: Optional[str] = None


class IdentityManager:
    """
    Diamond Identity Manager - Zentrale Identitäts-Erkennung.
    
    Verwaltet:
    - Identity-Regex-Patterns für Namenserkennung
    - Realtime-Name-Extraktion aus User-Text
    - Chat-History-Scan nach erwähnten Namen
    - Tracking welche Chats bereits nach dem Namen gefragt haben
    """
    
    def __init__(self) -> None:
        """Initialize regex patterns, stopword set, and in-memory chat/face tracking."""
        self.patterns: List[Pattern] = IDENTITY_REGEX_PATTERNS
        self.non_names: frozenset = NON_NAMES
        # Klassen-weite Tracking-Sets (werden vom ChatOrchestrator genutzt)
        self._identity_asked_chat_ids: set = set()
        self._unknown_face_buffer: dict = {}
    
    # ─────────────────────────────────────────────────────────────────────────
    # Pattern Matching
    # ─────────────────────────────────────────────────────────────────────────
    
    def extract_name_from_text(self, text: str) -> IdentityDetectionResult:
        """
        Extrahiert einen Namen aus dem gegebenen Text via Regex.
        
        Returns:
            IdentityDetectionResult mit extrahiertem Namen (title-cased) oder None
        """
        if not text:
            return IdentityDetectionResult()
        
        for pattern in self.patterns:
            match = pattern.search(text)
            if not match:
                continue
            
            # Gruppe 2 ist der Name (nach "ich bin/ich heiße/mein name ist")
            try:
                name = match.group(2).strip().rstrip(".,!? ")
            except IndexError:
                continue
            
            if not name or name.lower() in self.non_names:
                continue
            
            return IdentityDetectionResult(
                name_found=True,
                name=name.title(),
                raw_match=name,
                pattern_used=pattern.pattern
            )
        
        return IdentityDetectionResult()
    
    def is_name_mentioned(self, text: str) -> bool:
        """Return True if ``extract_name_from_text`` finds a plausible personal name."""
        return self.extract_name_from_text(text).name_found
    
    # ─────────────────────────────────────────────────────────────────────────
    # Chat History Analysis
    # ─────────────────────────────────────────────────────────────────────────
    
    def is_name_mentioned_in_history(self, chat_history: List[Any]) -> bool:
        """
        Check if user mentioned their name in the last messages (BUG-MEM-017).
        
        Args:
            chat_history: Liste von Message-Objekten (mindestens .role und .content)
        
        Returns:
            True wenn Identity-Pattern in recent user messages gefunden
        """
        if not chat_history:
            return False
        
        # Get last 2 user messages (from last 10 messages max)
        recent_user_msgs = [
            msg for msg in chat_history[-10:]
            if hasattr(msg, 'role') and msg.role == 'user'
        ][-2:]
        
        for msg in recent_user_msgs:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            if not content:
                continue
            
            if self.is_name_mentioned(content):
                logger.debug("[IDENTITY-MANAGER] Name mentioned in recent message: %r", content[:50])
                return True
        
        return False
    
    # ─────────────────────────────────────────────────────────────────────────
    # Realtime Extraction
    # ─────────────────────────────────────────────────────────────────────────
    
    def extract_realtime_identity_name(self, user_text: str) -> Optional[str]:
        """
        Rolf-Bug Fix: Extract user name from the CURRENT message via regex.
        
        Prevents the paradox where the LLM greets "Hallo Rolf" but the
        identity fallback appends "Wie heißt du?" because _identity was
        loaded before the extraction pipeline could persist the name.
        
        Args:
            user_text: Der aktuelle User-Text
            
        Returns:
            Title-cased name or None
        """
        result = self.extract_name_from_text(user_text)
        return result.name if result.name_found else None
    
    # ─────────────────────────────────────────────────────────────────────────
    # Chat Tracking
    # ─────────────────────────────────────────────────────────────────────────
    
    def mark_identity_asked(self, chat_id: int) -> None:
        """Markiert dass für diesen Chat bereits nach dem Namen gefragt wurde."""
        self._identity_asked_chat_ids.add(int(chat_id))
        logger.debug("[IDENTITY-MANAGER] Chat %s marked as identity-asked", chat_id)
    
    def is_identity_already_asked(self, chat_id: Optional[int]) -> bool:
        """Prüft ob für diesen Chat bereits nach dem Namen gefragt wurde."""
        if chat_id is None:
            return False
        return int(chat_id) in self._identity_asked_chat_ids
    
    def clear_identity_asked(self, chat_id: int) -> None:
        """Entfernt den Tracking-Eintrag für einen Chat (z.B. nach erfolgreicher Namenserkennung)."""
        self._identity_asked_chat_ids.discard(int(chat_id))
    
    # ─────────────────────────────────────────────────────────────────────────
    # Unknown Face Buffer (für Lern-Modus)
    # ─────────────────────────────────────────────────────────────────────────
    
    def store_unknown_face(self, chat_id: int, face_data: dict) -> None:
        """Speichert unbekannte Gesichtsdaten für potenzielles Lernen."""
        self._unknown_face_buffer[int(chat_id)] = face_data
        logger.debug("[IDENTITY-MANAGER] Unknown face buffered for chat %s", chat_id)
    
    def get_unknown_face(self, chat_id: int) -> Optional[dict]:
        """Holt gepufferte Gesichtsdaten für einen Chat."""
        return self._unknown_face_buffer.get(int(chat_id))
    
    def clear_unknown_face(self, chat_id: int) -> Optional[dict]:
        """Entfernt gepufferte Gesichtsdaten und gibt sie zurück."""
        return self._unknown_face_buffer.pop(int(chat_id), None)
    
    def has_unknown_face_buffered(self, chat_id: int) -> bool:
        """Prüft ob unbekannte Gesichtsdaten für einen Chat gepuffert sind."""
        return int(chat_id) in self._unknown_face_buffer
    
    # ─────────────────────────────────────────────────────────────────────────
    # Convenience Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def should_trigger_identity_prompt(
        self,
        chat_id: int,
        chat_history: List[Any],
        current_identity_name: Optional[str] = None
    ) -> bool:
        """
        Bestimmt ob ein Identity-Prompt ausgelöst werden sollte.
        
        Args:
            chat_id: Die Chat-ID
            chat_history: Die Chat-History
            current_identity_name: Der aktuell bekannte Name (falls vorhanden)
            
        Returns:
            True wenn ein Identity-Prompt angezeigt werden soll
        """
        # Kein Prompt wenn bereits ein Name bekannt ist
        if current_identity_name is not None:
            return False
        
        # Kein Prompt wenn bereits gefragt wurde
        if self.is_identity_already_asked(chat_id):
            return False
        
        # Kein Prompt wenn Name bereits in History erwähnt wurde
        if self.is_name_mentioned_in_history(chat_history):
            return False
        
        return True


# Singleton-Instanz für globalen Zugriff
identity_manager = IdentityManager()

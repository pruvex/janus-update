"""Diamond Tool Result Schema — Phase 1: Skill Contract (V1)

Zweck: Einheitlicher Vertrag für alle Tool-Rückgabewerte in backend/tools/.
Dies ermöglicht der Suggestion Engine eine konsistente Datenbasis.

Migration-Guide:
- geo_service.py: Passt fast 1:1 (status="ok"|"error", data, error-Dict)
- calendar_tools.py: Erfordert Mapping (status="success"→"ok", output→message, fehlende error-Struktur)

Version: 1.0.0 — Phase 1 Schema Design
Erstellt: 2026-04-10
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


class ToolErrorDetails(BaseModel):
    """Strukturierte Fehlerinformation für Tool-Ausführungen."""

    code: str = Field(
        ...,
        description="Maschinenlesbarer Fehlercode (z.B. 'VALIDATION_ERROR', 'API_TIMEOUT')",
        examples=["NOT_FOUND", "VALIDATION_ERROR", "API_TIMEOUT", "PERMISSION_DENIED"],
    )
    message: str = Field(
        ...,
        description="Human-readable Fehlerbeschreibung für UI/Logs",
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Zusätzliche Kontextdaten (z.B. request_id, retry_after, invalid_fields)",
    )


class ToolResultV1(BaseModel):
    """
    Einheitlicher Rückgabevertrag für alle Diamond Tools.

    Design-Prinzipien:
    - Jede Tool-Ausführung liefert garantiert status + data
    - Fehler sind explizit (nicht implizit durch fehlende Daten)
    - Meta-Informationen (Timing, Provider, etc.) separat im metadata-Feld
    - UI-Message optional für direkte Anzeige oder Logging

    Legacy (Serialization):
    - Bei ``model_dump()`` / ``model_dump_json()`` werden zusätzlich ausgedrückt:
      ``success`` (bool) und ``output`` (str), damit ältere Prompts/Consumer weiter funktionieren.
    """

    status: Literal["ok", "error", "dry_run_success"] = Field(
        ...,
        description=(
            "Ausführungsstatus: ok = Erfolg, error = Fehler, "
            "dry_run_success = erfolgreiche Simulation/Vorschau ohne Commit (z.B. PDF-Preview)."
        ),
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Die eigentlichen Ergebnisdaten des Tools (immer ein Dict, auch bei leerem Ergebnis)",
    )
    message: Optional[str] = Field(
        default=None,
        description="UI-geeignete Nachricht oder Log-Hinweis (z.B. '5 Termine gefunden')",
    )
    error: Optional[ToolErrorDetails] = Field(
        default=None,
        description="Strukturierte Fehlerdetails (nur bei status='error')",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Ausführungsmetadaten: execution_time_ms, provider, cache_hit, etc.",
    )
    is_final_response: bool = Field(
        default=False,
        description=(
            "Wenn True, signalisiert dies, dass das Tool-Ergebnis bereits die finale Antwort "
            "für den Nutzer ist und keine weitere Synthese durch den LLM erforderlich ist. "
            "Dies spart Kosten und Latenz, da der zweite LLM-Call übersprungen wird."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _strip_legacy_input_keys(cls, data: Any) -> Any:
        """Entfernt legacy ``success``/``output`` aus Roh-Dicts, damit Validierung nicht kollidiert."""
        if isinstance(data, dict):
            cleaned = {k: v for k, v in data.items() if k not in ("success", "output")}
            return cleaned
        return data

    @computed_field
    @property
    def success(self) -> bool:
        """Legacy: True bei status ``ok`` oder ``dry_run_success`` (in ``model_dump`` enthalten)."""
        return self.status in ("ok", "dry_run_success")

    @computed_field
    @property
    def output(self) -> str:
        """Legacy: Spiegel von ``message`` oder leerer String (in ``model_dump`` enthalten)."""
        return self.message if self.message is not None else ""

    @field_validator("error")
    @classmethod
    def validate_error_consistency(cls, v: Optional[ToolErrorDetails], info) -> Optional[ToolErrorDetails]:
        """Ensures error field is only set when status is 'error'."""
        values = info.data
        status = values.get("status")
        if status == "error" and v is None:
            raise ValueError("Field 'error' is required when status='error'")
        if status in ("ok", "dry_run_success") and v is not None:
            raise ValueError("Field 'error' must be None when status is 'ok' or 'dry_run_success'")
        return v

    def is_success(self) -> bool:
        """Convenience check for success status."""
        return self.status in ("ok", "dry_run_success")

    def has_data(self, key: str) -> bool:
        """Check if specific data key exists and is not None."""
        return key in self.data and self.data[key] is not None

    def get_data(self, key: str, default: Any = None) -> Any:
        """Safe accessor for nested data fields."""
        return self.data.get(key, default)


class SuggestionMetadata(BaseModel):
    """
    Metadaten für die Suggestion Engine.

    Enthält Informationen, die bestimmen, wie ein Tool-Ergebnis
    für Follow-up-Vorschläge verwertet werden kann.
    """

    relevance_tags: List[str] = Field(
        default_factory=list,
        description="Tags zur Kategorisierung für die Suggestion Engine (z.B. 'calendar', 'location', 'contact')",
        examples=[["calendar", "appointment"], ["location", "restaurant", "menu"]],
    )
    suggest_follow_up: bool = Field(
        default=True,
        description="Ob dieses Ergebnis Follow-up-Aktionen vorschlagen soll",
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Konfidenz-Score für die Qualität dieses Ergebnisses (0.0-1.0)",
    )
    primary_entity_id: Optional[str] = Field(
        default=None,
        description="ID des primären Entities (z.B. event_id, contact_id) für Follow-up-Referenzen",
    )
    primary_entity_name: Optional[str] = Field(
        default=None,
        description="Name/Label des primären Entities für UI-Anzeige",
    )
    related_skills: List[str] = Field(
        default_factory=list,
        description="Skill-IDs, die als Follow-up relevant sein könnten",
        examples=[["update_calendar_event", "share_appointment"]],
    )
    user_intent_context: Optional[str] = Field(
        default=None,
        description="Klassifizierter Intent des ursprünglichen Requests (z.B. 'create', 'search', 'modify')",
    )
    temporal_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Zeitlicher Kontext: {'start_time': ISO8601, 'end_time': ISO8601, 'all_day': bool}",
    )


class SuggestionCandidate(BaseModel):
    """
    Ein Kandidat für die Suggestion Engine.

    Kombiniert Tool-Ergebnis mit Suggestion-Metadaten für
    intelligentes Follow-up-Matching.
    """

    result: ToolResultV1 = Field(
        ...,
        description="Das zugrunde liegende Tool-Ergebnis",
    )
    suggestion_meta: SuggestionMetadata = Field(
        default_factory=SuggestionMetadata,
        description="Metadaten für Suggestion-Engine-Verarbeitung",
    )
    source_tool: str = Field(
        ...,
        description="Name/ID des ausführenden Tools (z.B. 'calendar_tools.create_event')",
    )
    source_skill_id: Optional[str] = Field(
        default=None,
        description="Skill-ID, falls über Skill-Registry aufgerufen",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp der Erstellung (UTC)",
    )

    # Factory-Methoden für bequeme Erstellung
    @classmethod
    def from_success(
        cls,
        tool_name: str,
        data: Dict[str, Any],
        message: Optional[str] = None,
        relevance_tags: Optional[List[str]] = None,
        suggest_follow_up: bool = True,
        **kwargs,
    ) -> "SuggestionCandidate":
        """Erstellt einen erfolgreichen SuggestionCandidate."""
        result = ToolResultV1(
            status="ok",
            data=data,
            message=message,
        )
        meta = SuggestionMetadata(
            relevance_tags=relevance_tags or [],
            suggest_follow_up=suggest_follow_up,
            **kwargs,
        )
        return cls(result=result, suggestion_meta=meta, source_tool=tool_name)

    @classmethod
    def from_error(
        cls,
        tool_name: str,
        error_code: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        relevance_tags: Optional[List[str]] = None,
    ) -> "SuggestionCandidate":
        """Erstellt einen fehlerhaften SuggestionCandidate."""
        error = ToolErrorDetails(
            code=error_code,
            message=error_message,
            details=error_details,
        )
        result = ToolResultV1(
            status="error",
            error=error,
        )
        meta = SuggestionMetadata(
            relevance_tags=relevance_tags or [],
            suggest_follow_up=False,  # Bei Fehlern keine Vorschläge
        )
        return cls(result=result, suggestion_meta=meta, source_tool=tool_name)


# =============================================================================
# MIGRATION-ANALYSE: Aktuelle Tool-Rückgaben
# =============================================================================

"""
## geo_service.py — MAPPING

Aktueller Stil (bereits nah am Ziel):
    return {
        "status": "ok",
        "data": {"businesses": [...], "location": {...}},
        "error": None,
    }
    # oder bei Fehler:
    return {
        "status": "error",
        "data": None,
        "error": {"code": "NOT_FOUND", "message": "...", "details": {...}},
    }

Migration:
    - Minimal: Wrap mit ToolResultV1(**result_dict)
    - Optimal: Direkte Konstruktion mit ToolResultV1(status="ok", data={...})
    - Keine Breaking Changes nötig

## calendar_tools.py — MAPPING

Aktueller Stil (inkonsistent):
    return {"status": "success", "output": "Keine Termine...", "events": []}
    return {"status": "error", "output": "Fehler beim..."}
    return {"status": "info", "output": "Ähnlicher Termin existiert..."}

Migration:
    - "success" → "ok"
    - "output" → "message"
    - "events" → data["events"]
    - Fehler: output-String → error.message, strukturierte error-Details nötig
    - "info" → "ok" mit suggest_follow_up=False im SuggestionMetadata

Beispiel-Migration:
    # ALT:
    return {"status": "success", "output": "Termin erstellt", "event_id": "123"}
    
    # NEU:
    return ToolResultV1(
        status="ok",
        data={"event_id": "123", "summary": "Meeting"},
        message="Termin erstellt",
    )

## Weitere Tools (Vorschau)

- gmail_tools.py: Ähnlich calendar_tools — Migration analog
- pdf_editor.py: Komplexere Datenstrukturen, data-Feld wichtig
- memory_tools.py: Erfordert entity_id im SuggestionMetadata
- contact_tools.py: Kontakt-IDs als primary_entity_id

## Empfohlene Rollout-Reihenfolge

1. geo_service.py (niedriges Risiko, bereits nah am Schema)
2. calendar_tools.py (hohes Nutzen-Potential für Suggestions)
3. gmail_tools.py (ähnliche Struktur wie calendar)
4. contact_tools.py (Kontext für Follow-ups)
5. memory_tools.py (Integration mit Memory-System)
6. Übrige Tools (pdf_editor, media_tools, etc.)
"""

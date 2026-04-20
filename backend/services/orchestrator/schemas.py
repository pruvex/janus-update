from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.data.schemas import ModalRequest


class AuditContext(BaseModel):
    doc_name: str = ""
    status: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    found_in_history: bool = False


class OrchestratorContext(BaseModel):
    history: List[Dict[str, str]] = Field(default_factory=list)
    memories: List[str] = Field(default_factory=list)
    audit_context: AuditContext = Field(default_factory=AuditContext)
    identity: Optional[Any] = None  # IdentitySlot (Task 013) — Any avoids circular import


class ExecutionResponse(BaseModel):
    sender: str = "model"
    text: str = ""
    image_url: Optional[str] = None
    agent_payload: Optional[Dict[str, Any]] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    is_agent_flow: bool = False
    raw_response: Optional[Any] = None
    ui_command: Optional[Dict[str, Any]] = None
    font_fallback_notice: Optional[str] = None
    factcheck_modifications_detected: Optional[bool] = None
    error: Optional[Dict[str, Any]] = None
    # 💎 AGGREGATOR FIX: Sammle alle Tool-Resultate für finale Aggregation
    all_tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    # 💎 COST-AGGREGATION FIX: Usage und Cost für Sidebar-Anzeige
    usage: Dict[str, Any] = Field(default_factory=dict)
    cost: Dict[str, Any] = Field(default_factory=dict)
    modal_request: Optional[ModalRequest] = None

    def _alias_value(self, key: str) -> Any:
        if key == "agent":
            return self.agent_payload
        return getattr(self, key)

    def __getitem__(self, key: str) -> Any:
        return self._alias_value(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            value = self._alias_value(key)
        except Exception:
            return default
        # 💎 ALIAS-SAFETY: the "agent" alias maps to Optional agent_payload.
        # When unset, return the caller-supplied default so chained dict-style
        # access (e.g. response.get("agent", {}).get("name")) stays crash-safe.
        if value is None and key == "agent":
            return default
        return value


class ToolDefinition(BaseModel):
    name: str
    description: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SyncResult(BaseModel):
    status: str = "skipped"
    message_id: Optional[int] = None
    success: bool = False

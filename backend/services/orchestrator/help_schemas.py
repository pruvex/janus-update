"""Help System Schemas — FEAT-HELP-001.

Pydantic schemas for the Janus Help & Capability System.
Deterministic, NO LLM — pure template rendering from Registry.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

# MCL-Compatible Action Types (§7.3)
# See: documentation/architecture/JANUS_MCL_SPECIFICATION.md
HelpActionType = Literal[
    "open_settings",
    "open_module",
    "focus_section",
]

HelpIntentType = Literal["capability_overview", "how_to", "navigation"]


class HelpInput(BaseModel):
    """Input contract for Help Skill.
    
    Attributes:
        query: The user's help query text.
        intent_type: Classified intent type (capability, how-to, navigation).
        context: Optional context (e.g., chat_id, user_preferences).
        language: ISO 639-1 language code (default: "de").
    """
    query: str
    intent_type: HelpIntentType
    context: Optional[Dict[str, Any]] = None
    language: str = "de"


class HelpAction(BaseModel):
    """UI action payload bridged to MCL (Modal Contract Layer).
    
    Action types are restricted to MCL-compatible operations.
    See: documentation/architecture/JANUS_MCL_SPECIFICATION.md §7.3
    
    Attributes:
        type: MCL action type (open_settings, open_module, focus_section).
        payload: Action-specific data (e.g., module name, section id).
    """
    type: HelpActionType
    payload: Dict[str, Any] = Field(default_factory=dict)


class HelpOutput(BaseModel):
    """Output contract for Help Skill (deterministic, NO LLM).
    
    This response is generated purely from Registry data and templates.
    No LLM calls are made in the Help Skill path.
    
    Attributes:
        answer: The rendered help answer text.
        suggestions: Follow-up query suggestions for the user.
        actions: MCL-compatible UI actions (e.g., open settings page).
        source_category: Source category in Registry (for audit/tests).
        fallback_used: True if "Dazu habe ich keine Information" was returned.
    """
    answer: str
    suggestions: List[str] = Field(default_factory=list)
    actions: List[HelpAction] = Field(default_factory=list)
    source_category: Optional[str] = None
    fallback_used: bool = False

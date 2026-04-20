# backend/services/prompting/core/model.py
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


class PromptBlock(BaseModel):
    """
    Ein logischer, atomarer Block innerhalb eines Prompts.
    Jeder Block hat eine Priorität, die dem Optimizer hilft, bei Token-Limits zu entscheiden, was gekürzt wird.
    """

    type: Literal[
        "system_role",
        "grounding_rules",
        "output_contract",
        "skill_directive",
        "tool_rules",
        "memory",
        "user_prompt",
        "synthesis_instruction",
    ] = Field(..., description="Der logische Typ des Blocks.")

    content: Any = Field(
        ..., description="Der Inhalt des Blocks, kann ein String oder ein strukturiertes Objekt (Directive) sein."
    )

    priority: int = Field(
        10,
        ge=1,
        description="Die Priorität des Blocks. 1 = höchste Priorität (wird nie gekürzt), 10 = niedrigste Priorität.",
    )

    required: bool = Field(
        False, description="Wenn True, darf dieser Block vom Optimizer niemals entfernt werden, nur gekürzt."
    )


class Prompt(BaseModel):
    """
    Das abstrakte Datenmodell eines kompletten Prompts, bevor er in einen provider-spezifischen String kompiliert wird.
    """

    blocks: List[PromptBlock] = Field(
        default_factory=list, description="Eine geordnete Liste von Prompt-Blöcken."
    )
    version: str = "v0.5.0"


# --- Beispiel für stark typisierte Direktiven (erweiterbar) ---


class StrictGroundingDirective(BaseModel):
    source: str = Field(
        ..., description="Die einzige erlaubte Wahrheitsquelle, z.B. 'web_search_tool_output'."
    )


class OutputContractDirective(BaseModel):
    format: Literal["json", "markdown_list", "prose"] = Field(
        ..., description="Das geforderte Ausgabeformat."
    )
    fields: List[str] = Field(
        default_factory=list, description="Bei JSON, die geforderten Felder."
    )


class SkillDirective(BaseModel):
    skill_id: str
    instruction_set: Dict[str, str] = Field(
        ..., description="Mapping von Model-Klasse (nano/mini/standard) auf Instruktion."
    )

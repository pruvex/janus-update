# backend/data/schemas_qa.py
"""
QA Framework Schemas für Pruki Memory System Testing.

Pruki Memory QA Framework - Diamond Standard
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ExpectedResult(BaseModel):
    """Erwartetes Ergebnis eines Memory-Testfalls."""
    
    logs: List[str] = Field(
        default_factory=list,
        description="Liste von erwarteten Log-Patterns (Regex-Strings)"
    )
    min_priority: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimale erwartete Priority (0.0-1.0)"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Erwartete Tags im gespeicherten Memory"
    )
    tags_present: List[str] = Field(
        default_factory=list,
        description="Tags die im Ergebnis vorhanden sein müssen"
    )
    semantic_intent: Optional[str] = Field(
        default=None,
        description="Semantische Beschreibung des erwarteten Verhaltens"
    )
    memory_type: Optional[str] = Field(
        default=None,
        description="Erwarteter Memory-Typ (CORE, GENERAL, TEMPORAL)"
    )
    max_latency_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Maximale erlaubte Latenz in Millisekunden"
    )
    min_budget_utilization: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimale Budget-Ausnutzung (0.0-1.0)"
    )
    
    @field_validator("logs", "tags", "tags_present", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return v


class MemoryTestCase(BaseModel):
    """Einzelner Memory-Testfall."""
    
    id: str = Field(
        ...,
        description="Eindeutige Test-ID (z.B. 'T001')",
        pattern=r"^T\d+$"
    )
    name: str = Field(
        ...,
        min_length=3,
        description="Menschlich lesbarer Testname"
    )
    setup_context: List[str] = Field(
        default_factory=list,
        description="Vorab-Setup Nachrichten für komplexe Szenarien"
    )
    input_text: str = Field(
        ...,
        min_length=1,
        description="Simulierte User-Nachricht"
    )
    expected: ExpectedResult = Field(
        ...,
        description="Erwartetes Ergebnis"
    )
    
    @field_validator("setup_context", mode="before")
    @classmethod
    def ensure_setup_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "T001",
                    "name": "Identity Extraction",
                    "input_text": "Ich bin Max",
                    "expected": {
                        "logs": [r"\[ENRICHER\]"],
                        "min_priority": 0.85,
                        "tags": ["identity"]
                    }
                }
            ]
        }
    }


class TestReport(BaseModel):
    """Ergebnis eines einzelnen Testlaufs."""
    
    test_id: str = Field(..., description="Referenz zur TestCase-ID")
    status: str = Field(
        ...,
        pattern=r"^(PASSED|FAILED|SKIPPED|ERROR)$",
        description="Test-Status"
    )
    latency_ms: float = Field(
        ...,
        ge=0.0,
        description="Gesamtlatenz in Millisekunden"
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Erreichter Score (1.0 = 100% Match)"
    )
    details: Optional[dict] = Field(
        default=None,
        description="Zusätzliche Details (Cache-Hits, Metrics, etc.)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Fehlermeldung bei FAILED/ERROR"
    )


class TestSuiteReport(BaseModel):
    """Aggregierter Report für eine komplette Test-Suite."""
    
    total_tests: int
    passed: int
    failed: int
    skipped: int
    total_latency_ms: float
    overall_score: float
    reports: List[TestReport]
    timestamp: str

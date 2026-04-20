from dataclasses import dataclass, field
from typing import Dict


def get_default_total_budget_seconds(provider: str) -> float:
    return 90.0 if str(provider or "").strip().lower() == "ollama" else 180.0


def get_phase_budget(
    budget: "RequestBudget",
    *,
    provider: str,
    phase: str,
) -> float:
    provider_key = str(provider or "").strip().lower()
    normalized_phase = str(phase or "").strip().lower()
    if provider_key != "ollama":
        return budget.allocate(normalized_phase, preferred_seconds=60.0, min_seconds=15.0)
    if normalized_phase == "final_synthesis":
        return budget.allocate(normalized_phase, preferred_seconds=20.0, min_seconds=8.0)
    if normalized_phase == "synthesis":
        return budget.allocate(normalized_phase, preferred_seconds=30.0, min_seconds=10.0)
    return budget.allocate(normalized_phase, preferred_seconds=45.0, min_seconds=10.0)


def should_skip_expensive_synthesis(budget: "RequestBudget", *, provider: str) -> bool:
    provider_key = str(provider or "").strip().lower()
    if provider_key != "ollama":
        return False
    return budget.remaining_seconds <= 12.0


@dataclass
class RequestBudget:
    total_seconds: float
    spent_seconds: float = 0.0
    allocations: Dict[str, float] = field(default_factory=dict)

    @property
    def remaining_seconds(self) -> float:
        return max(0.0, float(self.total_seconds) - float(self.spent_seconds))

    def allocate(self, phase: str, *, preferred_seconds: float, min_seconds: float) -> float:
        preferred = max(float(min_seconds), float(preferred_seconds))
        minimum = max(0.0, float(min_seconds))
        remaining = self.remaining_seconds
        if remaining <= 0.0:
            granted = minimum
        else:
            granted = min(preferred, remaining)
            if granted < minimum:
                granted = minimum
        self.allocations[str(phase)] = granted
        self.spent_seconds += granted
        return granted

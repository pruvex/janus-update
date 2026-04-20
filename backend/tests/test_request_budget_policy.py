from backend.services.request_budget import (
    RequestBudget,
    should_skip_expensive_synthesis,
)


def test_should_skip_expensive_synthesis_when_remaining_budget_is_low():
    budget = RequestBudget(total_seconds=20.0)
    budget.allocate("tool_phase", preferred_seconds=15.0, min_seconds=10.0)

    assert should_skip_expensive_synthesis(budget, provider="ollama") is True


def test_should_not_skip_expensive_synthesis_when_budget_is_sufficient():
    budget = RequestBudget(total_seconds=90.0)
    budget.allocate("tool_phase", preferred_seconds=20.0, min_seconds=10.0)

    assert should_skip_expensive_synthesis(budget, provider="ollama") is False

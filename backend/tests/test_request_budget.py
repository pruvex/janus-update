from backend.services.request_budget import RequestBudget


def test_request_budget_allocates_remaining_time_with_caps():
    budget = RequestBudget(total_seconds=90.0)

    first = budget.allocate("planning", preferred_seconds=15.0, min_seconds=5.0)
    second = budget.allocate("tool_phase", preferred_seconds=40.0, min_seconds=10.0)

    assert 5.0 <= first <= 15.0
    assert 10.0 <= second <= 40.0
    assert budget.remaining_seconds <= 90.0


def test_request_budget_never_returns_negative_time():
    budget = RequestBudget(total_seconds=1.0)

    budget.allocate("phase1", preferred_seconds=1.0, min_seconds=0.5)
    final = budget.allocate("phase2", preferred_seconds=1.0, min_seconds=0.1)

    assert final >= 0.1

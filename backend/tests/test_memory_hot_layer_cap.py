import backend.services.memory_budget as memory_budget
from backend.services.memory_budget import MemorySlot, TokenBudget, select_slots_by_budget
from backend.services.memory_observability import memory_metrics


def test_core_hot_layer_cap_keeps_protected_slots(monkeypatch):
    monkeypatch.setattr(memory_budget, "MEMORY_HOT_LAYER_CAP_ENABLED", True)
    monkeypatch.setattr(memory_budget, "MAX_CORE_ALWAYS_TOKENS", 100)

    before = memory_metrics.slots_dropped_core_cap
    slots = [
        MemorySlot(
            text="Protected allergy fact",
            tokens=80,
            tier="core_always",
            priority=0.99,
            memory_id=1,
            tags=["health"],
        ),
        MemorySlot(
            text="High priority identity fact",
            tokens=60,
            tier="core_always",
            priority=0.98,
            memory_id=2,
            tags=["identity"],
        ),
        MemorySlot(
            text="Smaller identity fact",
            tokens=20,
            tier="core_always",
            priority=0.97,
            memory_id=3,
            tags=["identity"],
        ),
        MemorySlot(
            text="Regular contextual fact",
            tokens=30,
            tier="stm",
            priority=0.40,
            memory_id=4,
            tags=[],
        ),
    ]

    selected = select_slots_by_budget(slots, TokenBudget(max_tokens=6000, memory_ratio=0.5))
    selected_ids = {slot.memory_id for slot in selected}

    assert 1 in selected_ids
    assert 3 in selected_ids
    assert 2 not in selected_ids
    assert memory_metrics.slots_dropped_core_cap == before + 1


def test_core_hot_layer_cap_flag_off_preserves_legacy_selection(monkeypatch):
    monkeypatch.setattr(memory_budget, "MEMORY_HOT_LAYER_CAP_ENABLED", False)
    monkeypatch.setattr(memory_budget, "MAX_CORE_ALWAYS_TOKENS", 100)

    slots = [
        MemorySlot(
            text="Protected allergy fact",
            tokens=80,
            tier="core_always",
            priority=0.99,
            memory_id=1,
            tags=["health"],
        ),
        MemorySlot(
            text="High priority identity fact",
            tokens=60,
            tier="core_always",
            priority=0.98,
            memory_id=2,
            tags=["identity"],
        ),
    ]

    selected = select_slots_by_budget(slots, TokenBudget(max_tokens=6000, memory_ratio=0.5))

    assert {slot.memory_id for slot in selected} == {1, 2}

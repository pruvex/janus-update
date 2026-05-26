"""
Tests für Memory V2 Budget-Aware Context Selection
Diamond Standard - Phase 4 Test Suite
"""

import importlib
import os
import sys

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.memory_budget import (
    MemorySlot,
    TokenBudget,
    _extract_readable_text,
    _get_tiktoken_encoder,
    estimate_tokens,
    format_memory_context,
    select_slots_by_budget,
)


class TestTokenBudget:
    """Test #1, #2: Budget-Calculation mit verschiedenen max_tokens"""

    def test_budget_calc_8000_tokens(self):
        """Test #1: Budget-Calc mit max_tokens=8000, buffer=1000"""
        budget = TokenBudget(max_tokens=8000, response_buffer=1000)
        
        # available = 8000 - 1000 = 7000
        # system_budget = 7000 * 0.10 = 700
        # memory_budget = 7000 * 0.30 = 2100
        # history_budget = 7000 * 0.50 = 3500
        
        assert budget.available == 7000
        assert budget.system_budget == 700
        assert budget.memory_budget == 2100
        assert budget.history_budget == 3500
    
    def test_budget_calc_4000_tokens(self):
        """Test #2: Budget-Calc mit max_tokens=4000, buffer=1000"""
        budget = TokenBudget(max_tokens=4000, response_buffer=1000)
        
        # available = 4000 - 1000 = 3000
        # system_budget = 3000 * 0.10 = 300
        # memory_budget = 3000 * 0.30 = 900
        # history_budget = 3000 * 0.50 = 1500
        
        assert budget.available == 3000
        assert budget.system_budget == 300
        assert budget.memory_budget == 900
        assert budget.history_budget == 1500


class TestKnapsackSelection:
    """Test #3, #4, #5: Knapsack-Algorithmus"""

    def test_knapsack_skip_big(self):
        """Test #3: Knapsack überspringt großen Slot, wählt kleinere"""
        # Slots: [500tk, 2200tk, 300tk], budget=2100
        # Erwartet: selected=[500tk, 300tk], skipped=[2200tk]
        slots = [
            MemorySlot(text="Slot A", tokens=500, tier="stm", priority=0.8, memory_id=1, tags=[]),
            MemorySlot(text="Slot B", tokens=2200, tier="stm", priority=0.7, memory_id=2, tags=[]),
            MemorySlot(text="Slot C", tokens=300, tier="stm", priority=0.6, memory_id=3, tags=[]),
        ]
        budget = TokenBudget(max_tokens=8000)  # memory_budget = 2100
        
        selected = select_slots_by_budget(slots, budget)
        
        assert len(selected) == 2
        assert selected[0].memory_id == 1  # 500tk
        assert selected[1].memory_id == 3  # 300tk (2200tk wurde übersprungen)
        assert budget.remaining_memory == 2100 - 800  # 1300
    
    def test_knapsack_full(self):
        """Test #4: Knapsack füllt Budget vollständig"""
        # 25 Slots mit je 100tk, budget=2100
        # Erwartet: 21 Slots (2100tk)
        slots = [
            MemorySlot(text=f"Slot {i}", tokens=100, tier="stm", priority=0.5, memory_id=i, tags=[])
            for i in range(25)
        ]
        budget = TokenBudget(max_tokens=8000)  # memory_budget = 2100
        
        selected = select_slots_by_budget(slots, budget)
        
        assert len(selected) == 21  # 21 * 100 = 2100
        assert sum(s.tokens for s in selected) == 2100
    
    def test_knapsack_empty(self):
        """Test #5: Knapsack mit leerer Slot-Liste"""
        slots = []
        budget = TokenBudget(max_tokens=8000)
        
        selected = select_slots_by_budget(slots, budget)
        
        assert len(selected) == 0
        assert budget.remaining_memory == 2100


class TestPrioritySorting:
    """Test #6: Priority-Sortierung"""

    def test_priority_sort_order(self):
        """Test #6: Slots sortieren nach Priority (absteigend)"""
        slots = [
            MemorySlot(text="Low", tokens=100, tier="stm", priority=0.5, memory_id=1, tags=[]),
            MemorySlot(text="High", tokens=100, tier="stm", priority=0.9, memory_id=2, tags=[]),
            MemorySlot(text="Medium", tokens=100, tier="stm", priority=0.7, memory_id=3, tags=[]),
        ]
        budget = TokenBudget(max_tokens=8000)
        
        selected = select_slots_by_budget(slots, budget)
        
        # Erwartete Reihenfolge: 0.9, 0.7, 0.5
        assert selected[0].memory_id == 2  # priority=0.9
        assert selected[1].memory_id == 3  # priority=0.7
        assert selected[2].memory_id == 1  # priority=0.5


class TestTierFormatting:
    """Test #7: Tier-Formatierung"""

    def test_tier_format_sections(self):
        """Test #7: core_always Slots erscheinen in ### CORE IDENTITY section"""
        slots = [
            MemorySlot(text="Core Fact", tokens=100, tier="core_always", priority=0.95, memory_id=1, tags=[]),
            MemorySlot(text="STM Fact", tokens=100, tier="stm", priority=0.5, memory_id=2, tags=[]),
        ]
        
        context = format_memory_context(slots)
        
        assert "### CORE IDENTITY" in context
        assert "- Core Fact" in context
        assert "### CONTEXT" in context
        assert "- STM Fact" in context


class TestFeatureFlag:
    """Test #8: Feature-Flag"""

    def test_feature_flag_off(self, monkeypatch):
        """Test #8: MEMORY_V2_ENABLED=false verwendet alten Code-Path"""
        # Simuliere MEMORY_V2_ENABLED=false
        monkeypatch.setenv("MEMORY_V2_ENABLED", "false")

        # Re-import mit neuem Flag
        importlib.reload(__import__('backend.services.memory_budget', fromlist=['']))
        from backend.services.memory_budget import MEMORY_V2_ENABLED

        assert MEMORY_V2_ENABLED is False

    def test_feature_flag_on(self, monkeypatch):
        """Test: MEMORY_V2_ENABLED=true (default) verwendet V2"""
        # Simuliere MEMORY_V2_ENABLED=true (default)
        monkeypatch.setenv("MEMORY_V2_ENABLED", "true")

        importlib.reload(__import__('backend.services.memory_budget', fromlist=['']))
        from backend.services.memory_budget import MEMORY_V2_ENABLED

        assert MEMORY_V2_ENABLED is True


class TestTokenEstimation:
    """Tests für präzise Token-Zählung via tiktoken"""

    def test_tiktoken_available(self):
        """Test: tiktoken cl100k_base Encoder ist geladen"""
        enc = _get_tiktoken_encoder()
        assert enc is not None, "tiktoken sollte verfügbar sein (in requirements.txt)"

    def test_estimate_tokens_basic(self):
        """Test: Token-Schätzung für kurze Texte (tiktoken-präzise)"""
        text = "Dies ist ein kurzer Test."
        tokens = estimate_tokens(text)
        # tiktoken gibt exakte Werte; mindestens 1 Token, sinnvoller Bereich
        assert tokens >= 1
        assert tokens <= len(text)  # Nie mehr Tokens als Zeichen

    def test_estimate_tokens_long(self):
        """Test: Token-Schätzung für lange Texte"""
        text = "A" * 400  # 400 Zeichen
        tokens = estimate_tokens(text)
        # tiktoken: 400x 'A' wird nicht exakt 100 sein, aber sinnvoll
        assert tokens >= 1
        assert tokens <= 400

    def test_estimate_tokens_empty(self):
        """Test: Leerer String gibt mindestens 1 Token"""
        assert estimate_tokens("") == 1

    def test_estimate_tokens_german_text(self):
        """Test: Deutscher Text mit Umlauten"""
        text = "Der Benutzer heißt Müller und wohnt in München."
        tokens = estimate_tokens(text)
        assert tokens >= 5  # Sinnvoller Mindest-Token-Count
        assert tokens <= len(text)


class TestBudgetAllocation:
    """Zusätzliche Tests für Budget-Allokation"""

    def test_allocate_success(self):
        """Test: Erfolgreiche Token-Allokation"""
        budget = TokenBudget(max_tokens=8000)
        
        result = budget.allocate(500)
        
        assert result is True
        assert budget.used_memory == 500
        assert budget.remaining_memory == 1600
    
    def test_allocate_failure(self):
        """Test: Fehlgeschlagene Token-Allokation (über Budget)"""
        budget = TokenBudget(max_tokens=8000)  # memory_budget = 2100
        
        result = budget.allocate(2500)  # Über 2100
        
        assert result is False
        assert budget.used_memory == 0
    
    def test_get_stats(self):
        """Test: Budget-Statistiken"""
        budget = TokenBudget(max_tokens=8000)
        budget.allocate(500)
        budget.allocate(300)
        
        stats = budget.get_stats()
        
        assert stats["max_tokens"] == 8000
        assert stats["memory_budget"] == 2100
        assert stats["used_memory"] == 800
        assert stats["remaining_memory"] == 1300
        assert stats["selected_count"] == 2


class TestFormatMemoryContext:
    """Zusätzliche Tests für Context-Formatierung"""

    def test_format_empty_slots(self):
        """Test: Leere Slot-Liste gibt leeren String"""
        context = format_memory_context([])
        
        assert context == ""
    
    def test_format_core_query_section(self):
        """Test: core_query Slots in RELEVANT TRAITS section"""
        slots = [
            MemorySlot(text="Query Fact", tokens=100, tier="core_query", priority=0.75, memory_id=1, tags=[]),
        ]
        
        context = format_memory_context(slots)
        
        assert "### RELEVANT TRAITS" in context
        assert "- Query Fact" in context
    
    def test_format_ephemeral_section(self):
        """Test: ephemeral Slots in ACTIVE FACTS section"""
        slots = [
            MemorySlot(text="Ephemeral Fact", tokens=100, tier="ephemeral", priority=0.6, memory_id=1, tags=[]),
        ]
        
        context = format_memory_context(slots)
        
        assert "### ACTIVE FACTS" in context
        assert "- Ephemeral Fact" in context


class TestExtractReadableText:
    """Tests für GAP-5 Fix: JSON-Snippet zu lesbarem Text"""

    def test_plain_text_passthrough(self):
        """Test: Plain-Text bleibt unverändert"""
        assert _extract_readable_text("Hallo Welt") == "Hallo Welt"

    def test_json_fact_extraction(self):
        """Test: Extrahiert 'fact' aus JSON-Snippet"""
        snippet = '{"fact": "Der Hund heißt Bello", "canonical_key": "name_is|pet:dog:bello|Bello"}'
        result = _extract_readable_text(snippet)
        assert result == "Der Hund heißt Bello"

    def test_json_evidence_priority(self):
        """Test: 'evidence' hat Vorrang vor 'fact'"""
        snippet = '{"evidence": "Max hat einen Hund namens Bello.", "fact": "name_is"}'
        result = _extract_readable_text(snippet)
        assert result == "Max hat einen Hund namens Bello."

    def test_json_canonical_key_fallback(self):
        """Test: canonical_key als letzter Fallback"""
        snippet = '{"fact": "", "canonical_key": "owns|user|dog"}'
        result = _extract_readable_text(snippet)
        assert result == "owns|user|dog"

    def test_empty_string(self):
        """Test: Leerer String gibt leeren String"""
        assert _extract_readable_text("") == ""

    def test_invalid_json(self):
        """Test: Ungültiges JSON gibt Original zurück"""
        snippet = '{broken json'
        assert _extract_readable_text(snippet) == snippet


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

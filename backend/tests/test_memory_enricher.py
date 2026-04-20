"""
Unit Tests für Memory Enricher (Phase 3)
Memory System V2.1.0 - Diamond Standard

12 Testfälle:
1-3: Priority Rules (Core Identity, Core Physical, Pet Identity)
4-6: TTL Rules (Temporal, Permanent, Tag Auto-Assign)
7-8: Priority Guard (Clamp, Passthrough)
9-11: Merge Strategy (MAX-Priority, UNION-Tags, Source-Keep)
12: CircuitBreaker States
"""

import pytest
import time
from backend.services.memory_enricher import (
    calculate_priority,
    calculate_ttl,
    calculate_tags,
    determine_memory_type,
    apply_priority_guard,
    enrich_fact,
    PRIORITY_CAPS,
)
from backend.services.memory_extractor import ExtractionCircuitBreaker


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1-3: PRIORITY RULES
# ═══════════════════════════════════════════════════════════════════════════

class TestPriorityRules:
    """Testet die 9 Priority Rules des Enrichers."""

    def test_core_identity_priority(self):
        """Test 1: Core Identity Priority - Name ist Max → priority=0.95"""
        fact = {"category": "Physis", "predicate": "name_is", "fact": "Max heißt Max"}
        result = calculate_priority(fact)
        assert result == 0.95, f"Expected 0.95, got {result}"

    def test_core_physical_priority(self):
        """Test 2: Core Physical Priority - hat_frisur → priority=0.90"""
        fact = {"category": "Physis", "predicate": "hat_frisur", "fact": "Max hat braune Haare"}
        result = calculate_priority(fact)
        assert result == 0.90, f"Expected 0.90, got {result}"

    def test_pet_identity_priority(self):
        """Test 3: Pet Identity Priority - Haustier name_is → priority=0.88"""
        fact = {"category": "Haustier-Details", "predicate": "name_is", "fact": "Pody ist ein Hund"}
        result = calculate_priority(fact)
        assert result == 0.88, f"Expected 0.88, got {result}"

    def test_default_priority(self):
        """Default Priority für unbekannte Kategorien → priority=0.50"""
        fact = {"category": "Unbekannt", "predicate": "irgendwas"}
        result = calculate_priority(fact)
        assert result == 0.50, f"Expected 0.50, got {result}"

    def test_core_relationship_priority(self):
        """Core Relationship - Beziehungen name_is → priority=0.85"""
        fact = {"category": "Beziehungen", "predicate": "name_is", "fact": "Lisa ist die Schwester"}
        result = calculate_priority(fact)
        assert result == 0.85, f"Expected 0.85, got {result}"

    def test_temporal_priority(self):
        """Temporal Priority - Termine → priority=0.60"""
        fact = {"category": "Termine", "predicate": "hat_termin", "fact": "Doktortermin morgen"}
        result = calculate_priority(fact)
        assert result == 0.60, f"Expected 0.60, got {result}"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4-6: TTL & TAGS
# ═══════════════════════════════════════════════════════════════════════════

class TestTTLRules:
    """Testet TTL-Regeln."""

    def test_temporal_ttl(self):
        """Test 4: Temporal TTL - Termine → 30 Tage (2592000 Sekunden)"""
        ttl = calculate_ttl("Termine")
        assert ttl == 2592000, f"Expected 2592000 (30 days), got {ttl}"

    def test_permanent_ttl(self):
        """Test 5: Permanent TTL - Physis → None (kein Ablauf)"""
        ttl = calculate_ttl("Physis")
        assert ttl is None, f"Expected None, got {ttl}"


class TestTagRules:
    """Testet Tag-Mappings."""

    def test_tag_auto_assign(self):
        """Test 6: Tag Auto-Assign - Stil + traegt_brille → tags enthält fashion, wearing"""
        fact = {"category": "Stil", "predicate": "traegt_brille", "fact": "Max trägt eine Brille"}
        tags = calculate_tags(fact)
        assert "fashion" in tags, f"Expected 'fashion' in {tags}"
        assert "wearing" in tags, f"Expected 'wearing' in {tags}"

    def test_vision_tag(self):
        """Vision Tag - source_type=vision → tags enthält 'visual'"""
        fact = {"category": "Physis", "predicate": "hat", "source_type": "vision"}
        tags = calculate_tags(fact)
        assert "visual" in tags, f"Expected 'visual' in {tags}"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 7-8: PRIORITY GUARD
# ═══════════════════════════════════════════════════════════════════════════

class TestPriorityGuard:
    """Testet den Priority Guard (Clamping)."""

    def test_guard_clamp(self):
        """Test 7: Guard Clamp - skill.save_fact versucht 0.99 → capped auf 0.85"""
        raw_priority = 0.99
        source_skill = "skill.save_fact"
        result = apply_priority_guard(raw_priority, source_skill)
        assert result == 0.85, f"Expected 0.85 (capped), got {result}"

    def test_guard_passthrough(self):
        """Test 8: Guard Passthrough - system 0.80 → unchanged 0.80"""
        raw_priority = 0.80
        source_skill = "system.extractor"
        result = apply_priority_guard(raw_priority, source_skill)
        assert result == 0.80, f"Expected 0.80 (unchanged), got {result}"

    def test_guard_system_unlimited(self):
        """System hat Cap 1.0 - kann alles durchlassen"""
        raw_priority = 0.99
        source_skill = "system"
        result = apply_priority_guard(raw_priority, source_skill)
        assert result == 0.99, f"Expected 0.99, got {result}"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 9-11: MEMORY TYPE & ENRICH_FACT
# ═══════════════════════════════════════════════════════════════════════════

class TestMemoryType:
    """Testet Memory Type Bestimmung."""

    def test_core_memory_type(self):
        """Priority >= 0.85 → CORE"""
        result = determine_memory_type(0.90, None)
        assert result == "CORE", f"Expected CORE, got {result}"

    def test_temporal_memory_type(self):
        """TTL gesetzt → TEMPORAL"""
        result = determine_memory_type(0.70, 2592000)
        assert result == "TEMPORAL", f"Expected TEMPORAL, got {result}"

    def test_general_memory_type(self):
        """Keine TTL, low priority → GENERAL"""
        result = determine_memory_type(0.50, None)
        assert result == "GENERAL", f"Expected GENERAL, got {result}"


class TestEnrichFact:
    """Testet die Haupt-Enricher-Funktion."""

    def test_enrich_fact_full(self):
        """Vollständige Enrichment eines Fakts"""
        fact = {
            "fact": "Max hat braune Haare",
            "category": "Physis",
            "predicate": "hat_frisur",
            "subject_name": "max"
        }
        result = enrich_fact(fact, source_skill="system.extractor")
        
        assert result["priority"] == 0.90, f"Priority should be 0.90, got {result['priority']}"
        assert result["memory_type"] == "CORE", f"Type should be CORE, got {result['memory_type']}"
        assert result["ttl"] is None, f"TTL should be None (permanent), got {result['ttl']}"
        assert "appearance" in result["tags"], f"Tags should contain 'appearance'"
        assert result["source_skill"] == "system.extractor"
        assert result["user_editable"] is True

    def test_enrich_fact_user_requested(self):
        """User expliziter Request erhöht Priority"""
        fact = {"category": "Allgemein", "fact": "Wichtige Info"}
        result = enrich_fact(fact, user_requested=True)
        
        assert result["priority"] >= 0.90, f"Priority should be >= 0.90, got {result['priority']}"
        assert result["source_skill"] == "user.explicit"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 12: CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════════════════════

class TestCircuitBreaker:
    """Testet den Extraction Circuit Breaker."""

    def test_circuit_breaker_initially_closed(self):
        """Frischer Circuit Breaker ist CLOSED"""
        cb = ExtractionCircuitBreaker()
        assert cb.can_execute() is True
        assert cb.get_state()["state"] == "CLOSED"

    def test_circuit_breaker_opens_after_failures(self):
        """Test 12: CircuitBreaker States - 3× record_failure() → state=OPEN"""
        cb = ExtractionCircuitBreaker(failure_threshold=3, recovery_timeout=120)
        
        # 3 Fehler simulieren
        cb.record_failure()
        assert cb.can_execute() is True  # Noch nicht offen
        
        cb.record_failure()
        assert cb.can_execute() is True  # Noch nicht offen
        
        cb.record_failure()
        # Jetzt sollte er OPEN sein
        assert cb.can_execute() is False
        assert cb.get_state()["state"] == "OPEN"
        assert cb.get_state()["failure_count"] == 3

    def test_circuit_breaker_recovery(self):
        """Circuit Breaker recovery nach success"""
        cb = ExtractionCircuitBreaker(failure_threshold=2)
        
        cb.record_failure()
        cb.record_failure()  # Jetzt OPEN
        assert cb.can_execute() is False
        
        cb.record_success()  # Reset
        assert cb.can_execute() is True
        assert cb.get_state()["state"] == "CLOSED"
        assert cb.get_state()["failure_count"] == 0

    def test_circuit_breaker_half_open_probe(self):
        """HALF_OPEN lässt einen Probe-Call durch"""
        cb = ExtractionCircuitBreaker(failure_threshold=1, recovery_timeout=0.5)  # 500ms recovery

        cb.record_failure()  # OPEN
        assert cb.can_execute() is False  # Blockiert
        
        # Warte auf Recovery
        time.sleep(0.6)
        
        # Jetzt sollte HALF_OPEN sein und einen Call erlauben
        assert cb.can_execute() is True
        assert cb.get_state()["state"] == "HALF_OPEN"


# ═══════════════════════════════════════════════════════════════════════════
# PRIORITY CAPS VERIFIKATION
# ═══════════════════════════════════════════════════════════════════════════

class TestPriorityCaps:
    """Verifiziert alle Priority Caps."""

    def test_all_caps_defined(self):
        """Alle wichtigen Source Skills haben Caps definiert"""
        assert PRIORITY_CAPS["system"] == 1.0
        assert PRIORITY_CAPS["system.extractor"] == 0.95
        assert PRIORITY_CAPS["skill.save_fact"] == 0.85
        assert PRIORITY_CAPS["skill.websearch"] == 0.60

    def test_unknown_source_gets_default_cap(self):
        """Unbekannte Quellen bekommen Default Cap 0.60"""
        result = apply_priority_guard(0.99, "unknown.source")
        assert result == 0.60, f"Unknown source should be capped to 0.60, got {result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

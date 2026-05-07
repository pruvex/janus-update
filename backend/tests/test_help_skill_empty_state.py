"""Unit Test for HelpSkill Empty-State (TASK-071).

Tests that the empty-state text contains all required elements from Spec Section 4.
"""

import pytest
from unittest.mock import MagicMock

from backend.services.help_skill import HelpSkill
from backend.services.capability_registry import CapabilityRegistry


def test_handle_capability_overview_empty_state_contains_all_required_elements():
    """
    TASK-071: Verify empty-state text contains all 4 required elements from Spec Section 4.
    
    Required Elements:
    1. Clear statement that no capabilities can currently be displayed
    2. Neutral explanation of possible causes (not loaded, not initialized, no data available)
    3. Reassuring hint that the state may be temporary
    4. Recommendation to try the request again later
    """
    # Create mock registry that returns empty capabilities list
    mock_registry = MagicMock(spec=CapabilityRegistry)
    mock_registry.get_verified_capabilities_for_overview.return_value = []
    
    # Create HelpSkill with mock registry
    help_skill = HelpSkill(registry=mock_registry)
    
    # Call _handle_capability_overview
    result = help_skill._handle_capability_overview("Was kannst du?", "de")
    
    # Verify fallback_used is True
    assert result.fallback_used is True, "fallback_used should be True when capabilities are empty"
    
    # Extract the answer text
    answer = result.answer
    
    # Verify all 4 required elements are present
    # 1. Clear statement that no capabilities can currently be displayed
    assert "Fähigkeiten" in answer or "fähigkeiten" in answer.lower(), \
        "Missing required element: statement about capabilities not being displayable"

    # 2. Neutral explanation of possible causes
    assert ("nicht geladen" in answer or "nicht verfügbar" in answer or
            "nicht initialisiert" in answer), \
        "Missing required element: explanation of possible causes"

    # 3. Reassuring hint that the state may be temporary
    assert "temporär" in answer or "später" in answer, \
        "Missing required element: reassuring hint about temporary state"

    # 4. Recommendation to try the request again later
    assert "später" in answer or "erneut" in answer, \
        "Missing required element: recommendation to try again later"


def test_handle_capability_overview_with_data_returns_normal_overview():
    """
    TASK-071: Non-Regression test - verify normal capability overview with data.
    
    This test ensures that the empty-state change does NOT affect the normal
    capability overview when data is available.
    """
    # Create mock registry that returns some capabilities
    mock_registry = MagicMock(spec=CapabilityRegistry)
    mock_registry.get_verified_capabilities_for_overview.return_value = [
        {
            "id": "test.capability",
            "name": "Test Capability",
            "description": "A test capability",
            "category": "Test Category",
            "status": "verified",
            "confidence": 0.9
        }
    ]
    
    # Create HelpSkill with mock registry
    help_skill = HelpSkill(registry=mock_registry)
    
    # Call _handle_capability_overview
    result = help_skill._handle_capability_overview("Was kannst du?", "de")
    
    # Verify fallback_used is False (normal path)
    assert result.fallback_used is False, "fallback_used should be False when capabilities are available"
    
    # Verify the answer contains normal capability overview structure
    assert "## Das kann ich aktuell" in result.answer, \
        "Normal capability overview should start with '## Das kann ich aktuell'"
    
    # Verify the answer does NOT contain empty-state text
    assert "nicht geladen" not in result.answer.lower(), \
        "Normal overview should not contain empty-state text"

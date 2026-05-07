"""Unit tests for path_resolution_hint directive in prompt_registry.py."""

import pytest

from backend.services.orchestrator.prompt_registry import prompt_registry, apply_verbosity_control


class TestPathResolutionHint:
    """Test that path_resolution_hint directive is correctly defined and applied."""

    def test_path_resolution_hint_directive_exists(self):
        """Test that path_resolution_hint directive exists in registry."""
        directive = prompt_registry.get_directive("path_resolution_hint")
        assert directive is not None
        assert "PFAD-AUFLÖSUNGS-HINWEIS" in directive
        assert "desktop" in directive
        assert "documents" in directive
        assert "downloads" in directive
        assert "pictures" in directive

    def test_path_resolution_hint_contains_desktop_mapping(self):
        """Test that path_resolution_hint contains desktop path mapping."""
        directive = prompt_registry.get_directive("path_resolution_hint")
        assert "desktop" in directive.lower()
        assert "C:\\Users\\<username>\\Desktop" in directive or "C:\\\\Users\\\\<username>\\\\Desktop" in directive

    def test_apply_verbosity_control_includes_path_resolution_hint(self):
        """Test that apply_verbosity_control includes path_resolution_hint directive."""
        base_prompt = "Du bist Janus."
        enhanced_prompt = apply_verbosity_control(base_prompt)
        assert "PFAD-AUFLÖSUNGS-HINWEIS" in enhanced_prompt
        assert "desktop" in enhanced_prompt.lower()

    def test_path_resolution_hint_not_duplicated(self):
        """Test that path_resolution_hint is not duplicated if already present."""
        full_directive = prompt_registry.get_directive("path_resolution_hint")
        base_prompt = f"Du bist Janus.\n\n{full_directive}"
        enhanced_prompt = apply_verbosity_control(base_prompt)
        # Count occurrences of the directive marker
        count = enhanced_prompt.count("PFAD-AUFLÖSUNGS-HINWEIS")
        assert count == 1, f"Directive should appear exactly once, but appeared {count} times"

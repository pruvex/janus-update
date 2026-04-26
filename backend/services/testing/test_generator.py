"""
Test Generator for Janus-Skills Quality System.

Generates deterministic test blueprints for skills based on skill_type.
NO AI-based generation - purely deterministic rule-based approach.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class TestGenerator:
    """Deterministic test generator for skill testing."""
    
    def __init__(self, output_dir: str = "config/skill_tests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_testset(self, skill_id: str, skill_type: str) -> Dict[str, Any]:
        """
        Generate a test blueprint for a given skill.
        
        Args:
            skill_id: Unique skill identifier (e.g., "namespace.action")
            skill_type: Type of skill (e.g., "tool", "agent", "renderer")
        
        Returns:
            Test blueprint dictionary with happy_path, edge_case, and failure_case tests
        """
        blueprint = {
            "skill_id": skill_id,
            "skill_type": skill_type,
            "generated_at": datetime.utcnow().isoformat(),
            "tests": {
                "happy_path": self._generate_happy_path(skill_id, skill_type),
                "edge_case": self._generate_edge_case(skill_id, skill_type),
                "failure_case": self._generate_failure_case(skill_id, skill_type)
            }
        }
        
        # Save to file
        filename = f"{skill_id.replace('.', '_')}_test.json"
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(blueprint, f, indent=2)
        
        return blueprint
    
    def _generate_happy_path(self, skill_id: str, skill_type: str) -> Dict[str, Any]:
        """Generate happy path test case."""
        return {
            "name": "happy_path",
            "description": "Standard successful execution",
            "input": self._get_standard_input(skill_type),
            "validation": {
                "type": "contains",
                "field": "status",
                "value": "success"
            }
        }
    
    def _generate_edge_case(self, skill_id: str, skill_type: str) -> Dict[str, Any]:
        """Generate edge case test case."""
        return {
            "name": "edge_case",
            "description": "Boundary condition or unusual input",
            "input": self._get_edge_input(skill_type),
            "validation": {
                "type": "not_crash",
                "description": "Should not crash on edge input"
            }
        }
    
    def _generate_failure_case(self, skill_id: str, skill_type: str) -> Dict[str, Any]:
        """Generate failure case test case."""
        return {
            "name": "failure_case",
            "description": "Invalid input or error condition",
            "input": self._get_failure_input(skill_type),
            "validation": {
                "type": "contains",
                "field": "status",
                "value": "error"
            }
        }
    
    def _get_standard_input(self, skill_type: str) -> Dict[str, Any]:
        """Get standard input based on skill type."""
        templates = {
            "tool": {"parameters": {"query": "test query"}},
            "agent": {"message": "Hello, how can you help?"},
            "renderer": {"content": "Sample content to render"}
        }
        return templates.get(skill_type, {"input": "default input"})
    
    def _get_edge_input(self, skill_type: str) -> Dict[str, Any]:
        """Get edge case input based on skill type."""
        templates = {
            "tool": {"parameters": {"query": ""}},  # Empty query
            "agent": {"message": "a" * 10000},  # Very long message
            "renderer": {"content": None}  # Null content
        }
        return templates.get(skill_type, {"input": "edge input"})
    
    def _get_failure_input(self, skill_type: str) -> Dict[str, Any]:
        """Get failure case input based on skill type."""
        templates = {
            "tool": {"parameters": None},  # Missing parameters
            "agent": {"message": 12345},  # Wrong type
            "renderer": {"content": "invalid"} * 1000  # Too large
        }
        return templates.get(skill_type, {"input": "failure input"})


def generate_testset(skill_id: str, skill_type: str) -> Dict[str, Any]:
    """
    Convenience function to generate a testset.
    
    Args:
        skill_id: Unique skill identifier
        skill_type: Type of skill
    
    Returns:
        Test blueprint dictionary
    """
    generator = TestGenerator()
    return generator.generate_testset(skill_id, skill_type)

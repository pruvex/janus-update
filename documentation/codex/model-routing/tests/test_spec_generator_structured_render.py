from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


runner = load_module(
    "codex_spec_generator_review_runner_structured_render",
    SCRIPTS_DIR / "codex_spec_generator_review_runner.py",
)


class SpecGeneratorStructuredRenderTests(unittest.TestCase):
    def test_structured_spec_renders_validator_friendly_markdown(self) -> None:
        input_payload = {
            "source_path": "documentation/codex/model-routing/example_decision_summary.md",
            "target_spec_path": "documentation/SPEC/example.md",
            "required_headings": [
                "# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3",
                "## SPEC REVIEW EXECUTION ROUTING",
                "## FEATURE IDENTITY",
                "## USER VALUE",
                "## TARGET SURFACE",
                "## USER ACTION SURFACE",
                "## SYSTEM BEHAVIOR",
                "## DATA / PERSISTENCE",
                "## CONSTRAINTS",
                "## SECURITY / PRIVACY",
                "## EDGE CASES",
                "## DEFINITION OF DONE",
                "## TEST STRATEGY",
                "## OUT OF SCOPE",
                "## INTERNAL COMPLEXITY BREAKDOWN",
            ],
        }
        payload = {
            "status": "PASS",
            "source_type": "LATEST_DECISION_SUMMARY",
            "source_path": input_payload["source_path"],
            "target_spec_path": input_payload["target_spec_path"],
            "recommended_next_skill": "janus-spec-review",
            "mechanical_cleanup_required": "NO",
            "notes": ["Structured draft is complete."],
            "structured_spec": {
                "routing": {
                    "target_skill": "janus-spec-review",
                    "recommended_model": "5.4",
                    "recommended_reasoning": "medium",
                    "new_chat": "no",
                    "complexity_score": 42,
                    "confidence": "MEDIUM",
                    "dashboard_hint": "SAFE",
                    "reason": "Bounded feature spec with moderate complexity.",
                },
                "feature_identity": {
                    "Feature Name": "Example Feature",
                    "Primary Goal": "Create one bounded example spec.",
                },
                "user_value": [
                    "Operators get a consistent feature specification from a locked decision source."
                ],
                "target_surface": {
                    "Primary Surface": "documentation/SPEC/",
                },
                "user_action_surface": {
                    "Trigger": "Operator requests spec generation from a locked decision summary."
                },
                "system_behavior": [
                    "The system renders one deterministic feature spec draft from structured delegated output."
                ],
                "data_persistence": {
                    "Persistence Required": "NO",
                    "Stored Artifact": "Markdown spec draft",
                },
                "constraints": [
                    "No implementation details or task breakdowns appear in the spec."
                ],
                "security_privacy": {
                    "Data Classification": "No secrets or personal data required."
                },
                "edge_cases": [
                    "If one core decision is missing, the flow must block instead of drafting around ambiguity."
                ],
                "definition_of_done": [
                    "Wenn die Entscheidung gesperrt ist, dann entsteht ein vollstaendiger Spec-Entwurf mit allen Pflichtsektionen."
                ],
                "test_strategy": {
                    "Primary Validation": "Render output and validate required headings plus routing block."
                },
                "out_of_scope": [
                    "Task creation, implementation, and release actions remain outside this flow."
                ],
                "internal_complexity_breakdown": {
                    "Scope Size": 8,
                    "Architectural Risk": 7,
                    "State / Persistence Complexity": 6,
                    "Cross-System Dependencies": 9,
                    "Ambiguity Level": 12,
                    "Total Complexity Score": 42,
                    "Routing Decision": "5.4",
                    "Routing Reasoning": "medium",
                    "Routing Confidence": "MEDIUM",
                    "Dashboard Hint": "SAFE",
                },
            },
        }

        rendered = runner.build_rendered_spec_markdown(payload)
        self.assertIn("## SPEC REVIEW EXECUTION ROUTING", rendered)
        self.assertIn("target_skill: janus-spec-review", rendered)
        self.assertIn("- [ ] Wenn die Entscheidung gesperrt ist", rendered)
        self.assertIn("Total Complexity Score: 42", rendered)

        issues = runner.validate_result_payload(payload, input_payload)
        self.assertEqual([], issues)


if __name__ == "__main__":
    unittest.main()

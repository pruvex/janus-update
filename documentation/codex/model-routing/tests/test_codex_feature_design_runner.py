from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

RUNNER_SPEC = importlib.util.spec_from_file_location(
    "codex_feature_design_runner",
    SCRIPTS_DIR / "codex_feature_design_runner.py",
)
runner = importlib.util.module_from_spec(RUNNER_SPEC)
assert RUNNER_SPEC and RUNNER_SPEC.loader
sys.modules[RUNNER_SPEC.name] = runner
RUNNER_SPEC.loader.exec_module(runner)


def make_response_summary(cost: float = 0.00016096) -> dict[str, object]:
    return {
        "generation_id": "gen-test-feature-design-001",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 475,
            "completion_tokens": 473,
            "cost": cost,
        },
    }


class TestCodexFeatureDesignRunner(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)
        self.original_run_root = runner.RUN_ROOT
        self.original_model_routing_dir = runner.MODEL_ROUTING_DIR
        runner.RUN_ROOT = self.temp_path / "runs"
        runner.MODEL_ROUTING_DIR = self.temp_path / "model-routing"
        self.addCleanup(self._restore_paths)

    def _restore_paths(self) -> None:
        runner.RUN_ROOT = self.original_run_root
        runner.MODEL_ROUTING_DIR = self.original_model_routing_dir

    def test_prompt_summary_contains_visible_gate_fields(self) -> None:
        result = runner.prompt_summary(
            workflow_id="WF-FD-PROMPT-001",
            task_label="Feature design review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.00024,
            cost_estimate_confidence_percent=68.0,
        )

        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OR")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertIn("1 = Codex", result["operator_prompt_lines"])
        self.assertIn("2 = OR", result["operator_prompt_lines"])

    def test_run_consumer_flow_delegated_fixture_passes(self) -> None:
        run_dir = runner.RUN_ROOT / "WF-FD-FIXTURE-001"
        run_dir.mkdir(parents=True, exist_ok=True)
        response_body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "status": "PASS",
                                "decision_state": "DECISION_SUMMARY_READY",
                                "recommended_next_skill": "janus-spec-generator",
                                "notes": [
                                    "Bounded consolidation only.",
                                    "Codex remains final decision owner.",
                                ],
                                "structured_decision_summary": {
                                    "Feature Name": "Operator-facing Codex-oder-OR-Wahl in bestehenden Janus-Skills",
                                    "Primary Goal": "In passenden bestehenden Janus-Skills soll am Einstieg sichtbar zwischen lokalem Codex-Pfad und bounded OR-Pfad gewaehlt werden koennen.",
                                    "User Problem": "Der Nutzer will je nach Codex-Kontingent und erwarteten OR-Kosten flexibel entscheiden koennen, welcher Pfad fuer eine konkrete Aufgabe sinnvoller ist.",
                                    "User Value": "Flexiblere Wahl zwischen lokalem Codex-Pfad und bounded OR-Pfad mit klarem Guardrail-Verhalten.",
                                    "Primary Target Surface": "bestehende Janus-Skill-Einstiege",
                                    "Existing or New Surface": "bestehend",
                                    "Existence Confirmation": "confirmed by user",
                                    "User Trigger": "Start eines geeigneten Janus-Skills mit bounded OR-Kandidaten",
                                    "Success Behavior": "Der Skill zeigt sichtbar 1 = Codex und 2 = OR inklusive Kosten-/Evidenzhinweis und faellt fail-closed lokal zurueck, wenn kein freigegebener bounded OR-Lane passt.",
                                    "Failure Behavior": "Nicht freigegebene, partielle oder ungesunde OR-Lanes duerfen nicht als normale Wahl erscheinen; in solchen Faellen bleibt nur der lokale Codex-Pfad sichtbar.",
                                    "User Action Surface": "bewusste Auswahl zwischen Codex und OR am Skill-Einstieg",
                                    "Data / Persistence": "nur Telemetrie, Gate-Evidenz und vorhandene Skill-/Routing-Artefakte; keine neue Produktpersistenz",
                                    "Security / Privacy": "keine broad delegated authority, keine Production-Routing-Aktivierung, Codex behaelt finale Validierung und Autoritaet",
                                    "Edge Cases": "fehlende Gate-Daten, fehlende OR-Freigabe, partielle Kandidaten, unvollstaendige Telemetrie, Healthcheck-Fehler",
                                    "Out of Scope": "globale OR-Freigabe, canonical routing-table update, broad delegated repo authority, release actions",
                                    "Routing Decision": "FULL FEATURE PIPELINE",
                                    "Routing Reason": "Die Antworten sind ausreichend gelockt und betreffen ein groesseres produktentscheidendes Verhalten.",
                                    "Recommended Next Skill": "janus-spec-generator",
                                },
                            }
                        )
                    }
                }
            ]
        }
        (run_dir / "response_body.json").write_text(json.dumps(response_body), encoding="utf-8")
        (run_dir / "response_summary.json").write_text(json.dumps(make_response_summary()), encoding="utf-8")

        with patch.object(
            runner,
            "invoke_file_first_wrapper",
            return_value=type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        ), patch.object(
            runner,
            "run_healthcheck",
            return_value={"status": "PASS"},
        ):
            result = runner.run_consumer_flow(
                workflow_id="WF-FD-FIXTURE-001",
                task_label="Feature design delegated fixture",
                normal_target_model="5.4 medium",
                delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
                estimated_or_cost=0.00024,
                cost_estimate_confidence_percent=68.0,
                input_package_json=Path("development/openrouter-skill-tests/janus-feature-design/feature_design_input_package.json"),
                use_local_or_fixture=True,
                or_local_fixture_response_path=self.temp_path / "fixture-response.json",
                execute_direct_or=False,
            )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "FEATURE_DESIGN_REVIEW_READY_FOR_CODEX_VALIDATION")
        self.assertEqual(result["selected_path"], "delegated_feature_design_review")
        self.assertIn("Tatsaechliche OR-Kosten", result["operator_result_lines"][2])


if __name__ == "__main__":
    unittest.main()

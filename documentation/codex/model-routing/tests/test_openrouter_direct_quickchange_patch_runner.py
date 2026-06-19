from __future__ import annotations

import importlib.util
import sys
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "openrouter_direct_quickchange_patch_runner.py"
)
SPEC = importlib.util.spec_from_file_location("openrouter_direct_quickchange_patch_runner", SCRIPT_PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


class OpenRouterDirectQuickchangePatchRunnerTests(unittest.TestCase):
    def make_args(self, model: str = "qwen/qwen3-coder-flash", response_format: str = "json_schema") -> Namespace:
        return Namespace(
            task_label="Tiny quickchange",
            editable_path=["frontend/index.html"],
            max_touched_files=1,
            model=model,
            temperature=0.0,
            max_tokens=1200,
            response_format=response_format,
        )

    def test_qwen_request_uses_no_think_provider_guard_and_response_healing(self) -> None:
        request = runner.make_request_body(self.make_args(), "Replace one placeholder.")

        self.assertIn("/no_think", request["messages"][0]["content"])
        self.assertEqual(request["provider"]["require_parameters"], True)
        self.assertEqual(request["plugins"], [{"id": "response-healing"}])
        self.assertEqual(request["response_format"]["type"], "json_schema")

    def test_non_qwen_json_schema_still_uses_provider_guard_and_healing(self) -> None:
        request = runner.make_request_body(self.make_args(model="deepseek/deepseek-v4-flash"), "Replace one placeholder.")

        self.assertNotIn("/no_think", request["messages"][0]["content"])
        self.assertEqual(request["provider"]["require_parameters"], True)
        self.assertEqual(request["plugins"], [{"id": "response-healing"}])

    def test_response_format_none_skips_structured_output_hardening(self) -> None:
        request = runner.make_request_body(self.make_args(response_format="none"), "Replace one placeholder.")

        self.assertNotIn("provider", request)
        self.assertNotIn("plugins", request)
        self.assertNotIn("response_format", request)


if __name__ == "__main__":
    unittest.main()

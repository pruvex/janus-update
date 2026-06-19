from __future__ import annotations

import importlib.util
import sys
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "openrouter_qwen_apply_patch_runner.py"
)
SPEC = importlib.util.spec_from_file_location("openrouter_qwen_apply_patch_runner", SCRIPT_PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


class OpenRouterQwenApplyPatchRunnerTests(unittest.TestCase):
    def make_args(self) -> Namespace:
        return Namespace(
            task_label="Fixture patch",
            max_touched_files=1,
            model="qwen/qwen3-coder-flash",
            temperature=0.0,
            max_output_tokens=1800,
        )

    def test_request_body_uses_responses_shape_and_apply_patch_tool(self) -> None:
        request = runner.make_request_body(
            self.make_args(),
            "Change one placeholder.",
            [
                {
                    "path": "frontend/index.html",
                    "content": "placeholder=\"Nachricht an Janus schreiben...\"",
                    "content_mode": "excerpt",
                    "excerpt_line_ranges": [{"start_line": 10, "end_line": 16}],
                    "full_line_count": 100,
                }
            ],
        )

        self.assertEqual(request["model"], "qwen/qwen3-coder-flash")
        self.assertEqual(request["tools"][0]["type"], "openrouter:apply_patch")
        self.assertEqual(request["tool_choice"], "auto")
        self.assertEqual(request["parallel_tool_calls"], False)
        self.assertEqual(request["max_tool_calls"], 1)
        self.assertIn("/no_think", request["input"][0]["content"][0]["text"])
        self.assertIn("unified diff hunks only", request["input"][0]["content"][0]["text"])
        self.assertEqual(request["input"][1]["role"], "user")
        self.assertEqual(request["input"][1]["content"][0]["type"], "input_text")

    def test_extract_prompt_targets_reads_backtick_values(self) -> None:
        prompt = (
            "Edit only `frontend/index.html`.\n"
            "Change `Nachricht an Janus schreiben...` to `Nachricht an Janus senden...`."
        )

        targets = runner.extract_prompt_targets(prompt)

        self.assertIn("Nachricht an Janus schreiben...", targets)
        self.assertIn("Nachricht an Janus senden...", targets)

    def test_load_allowed_file_inputs_prefers_excerpt_for_large_file(self) -> None:
        prompt = (
            "Edit only `frontend/index.html`.\n"
            "Change `Nachricht an Janus schreiben...` to `Nachricht an Janus senden...`."
        )

        file_inputs = runner.load_allowed_file_inputs(["frontend/index.html"], prompt, context_lines=2)

        self.assertEqual(len(file_inputs), 1)
        self.assertEqual(file_inputs[0]["content_mode"], "excerpt")
        self.assertGreater(len(file_inputs[0]["excerpt_line_ranges"]), 0)
        self.assertIn("Nachricht an Janus schreiben...", file_inputs[0]["content"])
        self.assertLess(len(file_inputs[0]["content"]), 5000)

    def test_extract_apply_patch_calls_reads_patch_from_arguments_dict(self) -> None:
        response = {
            "output": [
                {"type": "message", "content": []},
                {
                    "id": "apc_1",
                    "type": "apply_patch_call",
                    "status": "completed",
                    "name": "openrouter:apply_patch",
                    "arguments": {
                        "patch": "*** Begin Patch\n*** Update File: frontend/index.html\n@@\n-placeholder=\"Nachricht an Janus schreiben...\"\n+placeholder=\"Nachricht an Janus senden...\"\n*** End Patch"
                    },
                },
            ]
        }

        calls = runner.extract_apply_patch_calls(response)

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["type"], "apply_patch_call")
        self.assertIn("*** Update File: frontend/index.html", calls[0]["patch"])

    def test_extract_apply_patch_calls_reads_openrouter_operation_shape(self) -> None:
        response = {
            "output": [
                {
                    "id": "st_1",
                    "type": "openrouter:apply_patch",
                    "status": "completed",
                    "operation": {
                        "type": "update_file",
                        "path": "frontend/index.html",
                        "diff": "```diff\n@@ -1,1 +1,1 @@\n-old\n+new\n```",
                    },
                },
                {
                    "id": "st_2",
                    "type": "openrouter:apply_patch",
                    "status": "in_progress",
                    "operation": {
                        "type": "update_file",
                        "path": "frontend/index.html",
                        "diff": "@@ -1,1 +1,1 @@\n-old\n+new",
                    },
                },
            ]
        }

        calls = runner.extract_apply_patch_calls(response)

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["type"], "openrouter:apply_patch")
        self.assertEqual(calls[0]["operation_type"], "update_file")
        self.assertEqual(calls[0]["path"], "frontend/index.html")
        self.assertEqual(calls[1]["status"], "in_progress")

    def test_validate_apply_patch_calls_accepts_bounded_update_patch(self) -> None:
        patch = "\n".join(
            [
                "*** Begin Patch",
                "*** Update File: frontend/index.html",
                "@@",
                '-                        placeholder="Nachricht an Janus schreiben..."',
                '+                        placeholder="Nachricht an Janus senden..."',
                "*** End Patch",
            ]
        )
        result, issues, touched = runner.validate_apply_patch_calls(
            calls=[
                {
                    "id": "apc_1",
                    "type": "apply_patch_call",
                    "status": "completed",
                    "name": "openrouter:apply_patch",
                    "patch": patch,
                }
            ],
            editable_paths=["frontend/index.html"],
            max_touched_files=1,
        )

        self.assertEqual(result, "PASS")
        self.assertEqual(issues, [])
        self.assertEqual(touched, ["frontend/index.html"])

    def test_validate_apply_patch_calls_accepts_openrouter_update_file_diff(self) -> None:
        diff = "\n".join(
            [
                "```diff",
                "@@ -342,7 +342,7 @@",
                '                      <textarea',
                '                        id="user-input-A"',
                '                        rows="1"',
                '-                        placeholder="Nachricht an Janus schreiben..."',
                '+                        placeholder="Nachricht an Janus senden..."',
                '                        autocomplete="off"',
                '                        spellcheck="true"',
                '                      ></textarea>',
                "```",
            ]
        )
        result, issues, touched = runner.validate_apply_patch_calls(
            calls=[
                {
                    "id": "st_1",
                    "type": "openrouter:apply_patch",
                    "status": "completed",
                    "name": "openrouter:apply_patch",
                    "operation_type": "update_file",
                    "path": "frontend/index.html",
                    "diff": diff,
                }
            ],
            editable_paths=["frontend/index.html"],
            max_touched_files=1,
        )

        self.assertEqual(result, "PASS")
        self.assertEqual(issues, [])
        self.assertEqual(touched, ["frontend/index.html"])

    def test_validate_apply_patch_calls_accepts_openrouter_unified_diff_context_prefix(self) -> None:
        diff = "\n".join(
            [
                "@@ -433,7 +433,7 @@",
                "                       <textarea",
                '                         id="user-input-A"',
                '                         rows="1"',
                '-                        placeholder="Nachricht an Janus schreiben..."',
                '+                        placeholder="Nachricht an Janus senden..."',
                '                         autocomplete="off"',
                '                         spellcheck="true"',
                '                       ></textarea>',
            ]
        )
        result, issues, touched = runner.validate_apply_patch_calls(
            calls=[
                {
                    "id": "st_ctx",
                    "type": "openrouter:apply_patch",
                    "status": "in_progress",
                    "name": "openrouter:apply_patch",
                    "operation_type": "update_file",
                    "path": "frontend/index.html",
                    "diff": diff,
                }
            ],
            editable_paths=["frontend/index.html"],
            max_touched_files=1,
        )

        self.assertEqual(result, "PASS")
        self.assertEqual(issues, [])
        self.assertEqual(touched, ["frontend/index.html"])

    def test_validate_apply_patch_calls_rejects_add_file(self) -> None:
        patch = "\n".join(
            [
                "*** Begin Patch",
                "*** Add File: tmp/example.txt",
                "+hello",
                "*** End Patch",
            ]
        )
        result, issues, touched = runner.validate_apply_patch_calls(
            calls=[
                {
                    "id": "apc_1",
                    "type": "apply_patch_call",
                    "status": "completed",
                    "name": "openrouter:apply_patch",
                    "patch": patch,
                }
            ],
            editable_paths=["frontend/index.html"],
            max_touched_files=1,
        )

        self.assertEqual(result, "FAIL")
        self.assertTrue(any("add/delete/move" in issue for issue in issues))
        self.assertEqual(touched, [])


if __name__ == "__main__":
    unittest.main()

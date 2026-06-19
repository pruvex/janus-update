from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "openrouter_qwen_execution_patch_candidate_runner.py"
)
SPEC = importlib.util.spec_from_file_location("openrouter_qwen_execution_patch_candidate_runner", SCRIPT_PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


class OpenRouterQwenExecutionPatchCandidateRunnerTests(unittest.TestCase):
    def make_args(self) -> Namespace:
        return Namespace(
            task_label="Execution fixture patch",
            max_touched_files=2,
            model="qwen/qwen3-coder-flash",
            temperature=0.0,
            max_output_tokens=2200,
        )

    def make_input_payload(self) -> dict[str, object]:
        return {
            "workflow_id": "BACKLOG-107-R1-EXECUTION-PATCH-CANDIDATE-001",
            "bound_skill_context": "janus-executioner",
            "target_task": "TASK-BACKLOG-107-R1.1",
            "spec_path": "documentation/tasks/backlog_BACKLOG-107_first_apply_slice_runtime_log_target_alignment.md",
            "precheck_status": "PRE-CHECK PASSED",
            "allowed_files": [
                "scripts/dev-log-utils.cjs",
                "documentation/codex/skills/janus-health-check/scripts/health_snapshot.py",
            ],
            "max_touched_files": 2,
            "mini_test_plan": [
                "python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo C:\\KI\\Janus-Projekt --mode MONTHLY",
                "rg -n \"debug_logs|documentation/logs/dev-runtime|runWithLogs\" scripts documentation -S",
            ],
            "manual_validation_gate": "Codex must keep local validation ownership.",
            "delegation_question": "Produce one bounded patch candidate that aligns runtime-log references only.",
        }

    def make_repo_temp_file(self, relative_path: str, content: str) -> str:
        base_dir = Path(tempfile.mkdtemp(dir=runner.REPO_ROOT / "documentation" / "codex" / "model-routing" / "tests"))
        target = base_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self.addCleanup(lambda: shutil.rmtree(base_dir, ignore_errors=True))
        return target.relative_to(runner.REPO_ROOT).as_posix()

    def test_build_execution_prompt_text_contains_allowed_files_and_required_behavior(self) -> None:
        prompt_text = runner.build_execution_prompt_text(self.make_input_payload())

        self.assertIn("scripts/dev-log-utils.cjs", prompt_text)
        self.assertIn("documentation/codex/skills/janus-health-check/scripts/health_snapshot.py", prompt_text)
        self.assertIn("Use the apply_patch tool for the proposal.", prompt_text)
        self.assertIn("Preserve Codex-owned manual validation", prompt_text)

    def test_make_request_body_uses_responses_shape_and_apply_patch_tool(self) -> None:
        request = runner.make_request_body(
            self.make_args(),
            "Execution prompt",
            [
                {
                    "path": "scripts/dev-log-utils.cjs",
                    "content": 'const logDir = path.join(process.cwd(), "documentation", "logs", "dev-runtime");',
                    "content_mode": "excerpt",
                    "excerpt_line_ranges": [{"start_line": 12, "end_line": 18}],
                    "full_line_count": 80,
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

    def test_extract_search_terms_picks_repo_relevant_tokens(self) -> None:
        prompt = (
            "Use `scripts/dev-log-utils.cjs` and align `documentation/logs/dev-runtime` references. "
            "Mini test includes `runWithLogs` and `debug_logs` checks."
        )

        terms = runner.extract_search_terms(prompt)

        self.assertIn("scripts/dev-log-utils.cjs", terms)
        self.assertIn("documentation/logs/dev-runtime", terms)
        self.assertIn("runWithLogs", terms)
        self.assertIn("debug_logs", terms)

    def test_load_allowed_file_inputs_uses_term_anchor_excerpt_for_large_file(self) -> None:
        repo_path = self.make_repo_temp_file(
            "tmp/large_anchor.js",
            "\n".join(
                ["const filler = 0;"] * 700
                + ['const target = "documentation/logs/dev-runtime";']
                + ["const tail = 1;"] * 700
            ),
        )

        prompt = (
            "Produce one bounded patch candidate.\n"
            "Keep `documentation/logs/dev-runtime` aligned and verify `runWithLogs`."
        )
        file_inputs = runner.load_allowed_file_inputs([repo_path], prompt, context_lines=2)

        self.assertEqual(len(file_inputs), 1)
        self.assertEqual(file_inputs[0]["content_mode"], "excerpt")
        self.assertGreater(len(file_inputs[0]["excerpt_line_ranges"]), 0)
        self.assertIn("documentation/logs/dev-runtime", file_inputs[0]["content"])

    def test_load_allowed_file_inputs_falls_back_to_head_tail_for_large_file_without_anchors(self) -> None:
        repo_path = self.make_repo_temp_file(
            "tmp/large_no_anchor.js",
            "\n".join([f"const line_{index} = {index};" for index in range(1200)]),
        )

        prompt = "Produce one bounded patch candidate without matching source anchors."
        file_inputs = runner.load_allowed_file_inputs([repo_path], prompt, context_lines=2)

        self.assertEqual(file_inputs[0]["content_mode"], "head_tail_fallback")
        self.assertEqual(len(file_inputs[0]["excerpt_line_ranges"]), 2)
        self.assertIn("# excerpt lines 1-", file_inputs[0]["content"])

    def test_extract_apply_patch_calls_reads_openrouter_operation_shape(self) -> None:
        response = {
            "output": [
                {
                    "id": "st_1",
                    "type": "openrouter:apply_patch",
                    "status": "completed",
                    "operation": {
                        "type": "update_file",
                        "path": "scripts/dev-log-utils.cjs",
                        "diff": "```diff\n@@ -1,1 +1,1 @@\n-old\n+new\n```",
                    },
                }
            ]
        }

        calls = runner.extract_apply_patch_calls(response)

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["type"], "openrouter:apply_patch")
        self.assertEqual(calls[0]["operation_type"], "update_file")
        self.assertEqual(calls[0]["path"], "scripts/dev-log-utils.cjs")

    def test_validate_apply_patch_calls_accepts_bounded_openrouter_diff(self) -> None:
        repo_path = self.make_repo_temp_file(
            "tmp/apply_patch_target.js",
            "\n".join(
                [
                    "function createLogStreams(prefix) {",
                    '  const logDir = path.join(process.cwd(), "documentation", "logs", "dev-runtime");',
                    "  return logDir;",
                    "}",
                ]
            ),
        )
        diff = "\n".join(
            [
                "```diff",
                "@@ -1,4 +1,5 @@",
                " function createLogStreams(prefix) {",
                '+  const repoLogRoot = path.join(process.cwd(), "documentation", "logs");',
                '-  const logDir = path.join(process.cwd(), "documentation", "logs", "dev-runtime");',
                '+  const logDir = path.join(repoLogRoot, "dev-runtime");',
                "   return logDir;",
                " }",
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
                    "path": repo_path,
                    "diff": diff,
                }
            ],
            editable_paths=[repo_path],
            max_touched_files=1,
        )

        self.assertEqual(result, "PASS")
        self.assertEqual(issues, [])
        self.assertEqual(touched, [repo_path])


if __name__ == "__main__":
    unittest.main()

from pathlib import Path

from backend.scripts.run_intent_benchmark import (
    DEFAULT_CASES_PATH,
    DEFAULT_M2_PROOF_REPORT_PATH,
    DEFAULT_PROOF_REPORT_PATH,
    DEFAULT_REPORT_PATH,
    AUX_DETERMINISTIC_PROFILE,
    _benchmark_profile_context,
    load_cases,
    parse_baseline_report,
    render_m2_proof_report,
    render_report,
    render_m1_proof_report,
    run_benchmark,
    run_m2_proof,
    run_m1_proof,
)
from backend.services.orchestrator import intent_aux_classifier, intent_config


def test_intent_benchmark_fixture_meets_minimum_corpus_requirements():
    cases = load_cases(DEFAULT_CASES_PATH)

    assert len(cases) >= 80

    subset_counts = {}
    for case in cases:
        subset_counts[case.subset] = subset_counts.get(case.subset, 0) + 1

    assert subset_counts["contact"] >= 20
    assert subset_counts["pet"] >= 15
    assert subset_counts["recall"] >= 15
    assert subset_counts["calendar"] >= 15


def test_intent_benchmark_runner_produces_separated_subset_summary():
    summary = run_benchmark()

    assert summary["overall"]["total"] >= 80
    assert summary["profile"] == "legacy"
    assert summary["latency_ms"]["p95"] >= 0.0
    assert "contact" in summary["subset_rows"]
    assert "pet" in summary["subset_rows"]
    assert "recall" in summary["subset_rows"]
    assert "calendar" in summary["subset_rows"]


def test_intent_benchmark_report_can_be_written(tmp_path):
    summary = run_benchmark()
    report = render_report(summary)
    output_path = tmp_path / "INTENT_BENCHMARK_BASELINE.md"
    output_path.write_text(report, encoding="utf-8")

    written = output_path.read_text(encoding="utf-8")
    assert "INTENT Benchmark Baseline" in written
    assert "## Subset Summary" in written
    assert "## Operator Checklist (Roadmap Section 9)" in written


def test_default_benchmark_paths_are_repo_local():
    assert DEFAULT_CASES_PATH == Path("backend/tests/fixtures/intent_benchmark_cases.jsonl").resolve()
    assert DEFAULT_REPORT_PATH == Path("documentation/test-runs/INTENT_BENCHMARK_BASELINE.md").resolve()
    assert DEFAULT_PROOF_REPORT_PATH == Path(
        "documentation/test-runs/TASK-INTENT-M1.3_benchmark_uplift_2026-07-08.md"
    ).resolve()
    assert DEFAULT_M2_PROOF_REPORT_PATH == Path(
        "documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md"
    ).resolve()


def test_parse_baseline_report_reads_repo_shape(tmp_path):
    report_path = tmp_path / "baseline.md"
    report_path.write_text(
        "\n".join(
            [
                "# INTENT Benchmark Baseline",
                "",
                "- Cases: `10`",
                "- Passed: `7`",
                "- Accuracy: `70.0%`",
                "",
                "## Subset Summary",
                "",
                "| Subset | Passed | Total | Accuracy |",
                "| --- | ---: | ---: | ---: |",
                "| calendar | 1 | 2 | 50.0% |",
                "| contact | 2 | 3 | 66.7% |",
                "| pet | 1 | 2 | 50.0% |",
                "| recall | 3 | 3 | 100.0% |",
                "",
                "## Cluster Summary",
                "",
                "| Cluster | Passed | Total | Accuracy |",
                "| --- | ---: | ---: | ---: |",
                "| contact_fact_telling | 2 | 3 | 66.7% |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_baseline_report(report_path)

    assert parsed["overall"]["total"] == 10
    assert parsed["overall"]["passed"] == 7
    assert parsed["subset_rows"]["contact"]["passed"] == 2
    assert parsed["cluster_rows"]["contact_fact_telling"]["total"] == 3


def test_m1_proof_report_renders_delta_on_small_case_set(tmp_path):
    all_cases = load_cases(DEFAULT_CASES_PATH)
    selected_ids = {"INT-M0-C005", "INT-M0-P003", "INT-M0-R001", "INT-M0-K002"}
    cases = [case for case in all_cases if case.case_id in selected_ids]

    legacy_summary = run_benchmark(cases)
    baseline_path = tmp_path / "INTENT_BENCHMARK_BASELINE.md"
    baseline_path.write_text(render_report(legacy_summary), encoding="utf-8")

    proof_summary = run_m1_proof(cases, baseline_report_path=baseline_path)
    report = render_m1_proof_report(proof_summary)

    assert proof_summary["flag_off_parity_pass"] is True
    assert proof_summary["aux_deterministic"]["profile"] == AUX_DETERMINISTIC_PROFILE.name
    assert "TASK-INTENT-M1.3 Benchmark Uplift Proof" in report
    assert "## Required Subset Delta" in report


def test_m2_proof_report_renders_delta_on_small_case_set(tmp_path):
    all_cases = load_cases(DEFAULT_CASES_PATH)
    selected_ids = {"INT-M0-C005", "INT-M0-P003", "INT-M0-R001", "INT-M0-K002"}
    cases = [case for case in all_cases if case.case_id in selected_ids]

    legacy_summary = run_benchmark(cases)
    baseline_path = tmp_path / "INTENT_BENCHMARK_BASELINE.md"
    baseline_path.write_text(render_report(legacy_summary), encoding="utf-8")

    proof_summary = run_m2_proof(cases, baseline_report_path=baseline_path)
    report = render_m2_proof_report(proof_summary)

    assert proof_summary["flag_off_parity_pass"] is True
    assert proof_summary["aux_deterministic"]["profile"] == AUX_DETERMINISTIC_PROFILE.name
    assert "TASK-INTENT-M2.1 Confidence Routing Proof" in report
    assert "## Required Subset Delta" in report


def test_deterministic_benchmark_profile_overrides_config_based_default_provider(monkeypatch):
    async def exploding_provider(user_text, context):
        raise AssertionError("real default provider path must not run in deterministic benchmark mode")

    monkeypatch.setattr(intent_aux_classifier, "_default_provider_callable", exploding_provider)

    with _benchmark_profile_context(AUX_DETERMINISTIC_PROFILE):
        result = intent_aux_classifier.classify_sync(
            "was weisst du ueber chris?",
            config=intent_config.IntentAuxClassifierConfig(enabled=True),
        )

    assert result.action == "recall"
    assert result.subject == "contact"
    assert result.source == "aux_llm"

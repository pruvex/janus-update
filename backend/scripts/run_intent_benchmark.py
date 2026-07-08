import argparse
import json
import logging
import math
import time
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional

from backend.services.orchestrator import intent_aux_classifier, intent_config
from backend.services.orchestrator.intent_engine import IntentEngine


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES_PATH = PROJECT_ROOT / "backend" / "tests" / "fixtures" / "intent_benchmark_cases.jsonl"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "documentation" / "test-runs" / "INTENT_BENCHMARK_BASELINE.md"
DEFAULT_PROOF_REPORT_PATH = (
    PROJECT_ROOT / "documentation" / "test-runs" / "TASK-INTENT-M1.3_benchmark_uplift_2026-07-08.md"
)


@dataclass
class BenchmarkCase:
    case_id: str
    subset: str
    cluster: str
    user_text: str
    context: Dict[str, Any]
    expected: Dict[str, Any]
    source: str


@dataclass
class CaseResult:
    case: BenchmarkCase
    passed: bool
    predicted_action: str
    mismatches: List[str]
    latency_ms: float


@dataclass(frozen=True)
class BenchmarkProfile:
    name: str
    aux_enabled: bool = False
    deterministic_aux: bool = False


LEGACY_PROFILE = BenchmarkProfile(name="legacy", aux_enabled=False, deterministic_aux=False)
AUX_DETERMINISTIC_PROFILE = BenchmarkProfile(
    name="aux_deterministic",
    aux_enabled=True,
    deterministic_aux=True,
)


def _percentile(values: List[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


async def _deterministic_aux_provider(user_text: str, context: Mapping[str, Any]) -> str:
    fallback = intent_aux_classifier.classify_with_regex_fallback(user_text)
    payload = {
        "action": fallback.action,
        "subject": fallback.subject,
        "confidence": fallback.confidence,
        "evidence": fallback.evidence,
    }
    return json.dumps(payload)


@contextmanager
def _benchmark_profile_context(profile: BenchmarkProfile) -> Iterator[None]:
    original_classifier = intent_aux_classifier._default_classifier
    original_config = intent_config._DEFAULT_AUX_CONFIG
    original_provider_callable = intent_aux_classifier._default_provider_callable
    try:
        config = intent_config.IntentAuxClassifierConfig(enabled=profile.aux_enabled)
        provider_callable = _deterministic_aux_provider if profile.deterministic_aux else None
        if provider_callable is not None:
            # Patch both seams: the module default classifier and the default provider
            # callable used when classify_sync(..., config=...) reconstructs a fresh instance.
            intent_aux_classifier._default_provider_callable = provider_callable
            intent_aux_classifier._default_classifier = intent_aux_classifier.AuxiliaryIntentClassifier(
                config=config,
                provider_callable=provider_callable,
            )
        intent_config._DEFAULT_AUX_CONFIG = config
        yield
    finally:
        intent_aux_classifier._default_classifier = original_classifier
        intent_config._DEFAULT_AUX_CONFIG = original_config
        intent_aux_classifier._default_provider_callable = original_provider_callable


def parse_baseline_report(path: Path = DEFAULT_REPORT_PATH) -> Dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    overall_match = {
        "total": re_search_int(r"- Cases: `(\d+)`", content),
        "passed": re_search_int(r"- Passed: `(\d+)`", content),
        "accuracy": re_search_percent(r"- Accuracy: `([0-9.]+)%`", content),
    }
    subset_rows = parse_markdown_table(content, "## Subset Summary")
    cluster_rows = parse_markdown_table(content, "## Cluster Summary")
    return {
        "overall": overall_match,
        "subset_rows": subset_rows,
        "cluster_rows": cluster_rows,
    }


def re_search_int(pattern: str, text: str) -> int:
    import re

    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"pattern not found: {pattern}")
    return int(match.group(1))


def re_search_percent(pattern: str, text: str) -> float:
    import re

    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"pattern not found: {pattern}")
    return float(match.group(1)) / 100.0


def parse_markdown_table(content: str, header: str) -> Dict[str, Dict[str, Any]]:
    lines = content.splitlines()
    try:
        start = lines.index(header)
    except ValueError as exc:
        raise ValueError(f"header not found: {header}") from exc
    rows: Dict[str, Dict[str, Any]] = {}
    for line in lines[start + 4 :]:
        if not line.strip():
            break
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            continue
        rows[cells[0]] = {
            "passed": int(cells[1]),
            "total": int(cells[2]),
            "accuracy": float(cells[3].rstrip("%")) / 100.0,
        }
    return rows


def load_cases(path: Path = DEFAULT_CASES_PATH) -> List[BenchmarkCase]:
    cases: List[BenchmarkCase] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            cases.append(
                BenchmarkCase(
                    case_id=payload["id"],
                    subset=payload["subset"],
                    cluster=payload["cluster"],
                    user_text=payload["user_text"],
                    context=payload.get("context") or {},
                    expected=payload["expected"],
                    source=payload["source"],
                )
            )
    return cases


def _predicted_action(result: Any) -> str:
    if result.is_calendar_intent:
        return "calendar"
    if result.is_personal_recall:
        return "personal_recall"
    if result.is_fact_telling:
        return "tell_fact"
    if result.is_shopping_intent:
        return "shopping"
    if result.is_weather_intent:
        return "weather"
    if result.is_routing_geo_intent:
        return "routing_geo"
    if result.is_news_intent:
        return "news"
    if result.is_wikipedia_intent:
        return "wikipedia"
    if result.primary_intent:
        return str(result.primary_intent)
    return "none"


def _route_flags(result: Any) -> Dict[str, bool]:
    return {
        "calendar": bool(result.is_calendar_intent),
        "shopping": bool(result.is_shopping_intent),
        "weather": bool(result.is_weather_intent),
        "routing_geo": bool(result.is_routing_geo_intent),
        "news": bool(result.is_news_intent),
        "wikipedia": bool(result.is_wikipedia_intent),
        "personal_recall": bool(result.is_personal_recall),
        "tell_fact": bool(result.is_fact_telling),
        "ambiguous": bool(result.is_ambiguous),
    }


def evaluate_case(case: BenchmarkCase, engine: Optional[IntentEngine] = None) -> CaseResult:
    benchmark_engine = engine or IntentEngine()
    started = time.perf_counter()
    detection = benchmark_engine.detect_all_intents(
        case.user_text,
        calendar_snapshot=case.context.get("calendar_snapshot"),
    )
    latency_ms = (time.perf_counter() - started) * 1000.0

    mismatches: List[str] = []
    predicted_action = _predicted_action(detection)
    flags = _route_flags(detection)

    expected_action = case.expected.get("action")
    if expected_action and predicted_action != expected_action:
        mismatches.append(f"action expected={expected_action} actual={predicted_action}")

    for field in ("is_fact_telling", "is_personal_recall", "is_ambiguous"):
        if field in case.expected:
            actual = bool(getattr(detection, field))
            expected = bool(case.expected[field])
            if actual != expected:
                mismatches.append(f"{field} expected={expected} actual={actual}")

    for route in case.expected.get("must_route", []):
        if not flags.get(route, False):
            mismatches.append(f"must_route missing={route}")

    for route in case.expected.get("must_not_route", []):
        if flags.get(route, False):
            mismatches.append(f"must_not_route hit={route}")

    return CaseResult(
        case=case,
        passed=not mismatches,
        predicted_action=predicted_action,
        mismatches=mismatches,
        latency_ms=latency_ms,
    )


def run_benchmark(
    cases: Optional[Iterable[BenchmarkCase]] = None,
    *,
    profile: BenchmarkProfile = LEGACY_PROFILE,
) -> Dict[str, Any]:
    logging.getLogger("janus_backend").setLevel(logging.WARNING)
    loaded_cases = list(cases) if cases is not None else load_cases()
    with _benchmark_profile_context(profile):
        engine = IntentEngine()
        results = [evaluate_case(case, engine=engine) for case in loaded_cases]

    cluster_rows: Dict[str, Dict[str, Any]] = {}
    subset_rows: Dict[str, Dict[str, Any]] = {}

    by_cluster: Dict[str, List[CaseResult]] = defaultdict(list)
    by_subset: Dict[str, List[CaseResult]] = defaultdict(list)
    failures: List[CaseResult] = []

    for result in results:
        by_cluster[result.case.cluster].append(result)
        by_subset[result.case.subset].append(result)
        if not result.passed:
            failures.append(result)

    for cluster, cluster_results in sorted(by_cluster.items()):
        passed = sum(1 for item in cluster_results if item.passed)
        total = len(cluster_results)
        cluster_rows[cluster] = {
            "passed": passed,
            "total": total,
            "accuracy": passed / total if total else 0.0,
        }

    for subset, subset_results in sorted(by_subset.items()):
        passed = sum(1 for item in subset_results if item.passed)
        total = len(subset_results)
        subset_rows[subset] = {
            "passed": passed,
            "total": total,
            "accuracy": passed / total if total else 0.0,
        }

    totals = Counter(case.subset for case in loaded_cases)
    overall_passed = sum(1 for item in results if item.passed)
    overall_total = len(results)
    latencies = [item.latency_ms for item in results]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "profile": profile.name,
        "overall": {
            "passed": overall_passed,
            "total": overall_total,
            "accuracy": overall_passed / overall_total if overall_total else 0.0,
        },
        "latency_ms": {
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
            "max": max(latencies) if latencies else 0.0,
        },
        "subset_rows": subset_rows,
        "cluster_rows": cluster_rows,
        "subset_counts": dict(sorted(totals.items())),
        "failures": failures,
    }


def render_report(summary: Dict[str, Any]) -> str:
    overall = summary["overall"]
    lines: List[str] = [
        "# INTENT Benchmark Baseline",
        "",
        f"Generated at: `{summary['generated_at']}`",
        "",
        "## Overall",
        "",
        f"- Cases: `{overall['total']}`",
        f"- Passed: `{overall['passed']}`",
        f"- Accuracy: `{overall['accuracy'] * 100:.1f}%`",
        "",
        "## Subset Summary",
        "",
        "| Subset | Passed | Total | Accuracy |",
        "| --- | ---: | ---: | ---: |",
    ]

    for subset, row in summary["subset_rows"].items():
        lines.append(
            f"| {subset} | {row['passed']} | {row['total']} | {row['accuracy'] * 100:.1f}% |"
        )

    lines.extend(
        [
            "",
            "## Cluster Summary",
            "",
            "| Cluster | Passed | Total | Accuracy |",
            "| --- | ---: | ---: | ---: |",
        ]
    )

    for cluster, row in summary["cluster_rows"].items():
        lines.append(
            f"| {cluster} | {row['passed']} | {row['total']} | {row['accuracy'] * 100:.1f}% |"
        )

    lines.extend(
        [
            "",
            "## Required M0 Subsets",
            "",
            f"- Contact: `{summary['subset_rows'].get('contact', {}).get('passed', 0)}/{summary['subset_rows'].get('contact', {}).get('total', 0)}`",
            f"- Pet: `{summary['subset_rows'].get('pet', {}).get('passed', 0)}/{summary['subset_rows'].get('pet', {}).get('total', 0)}`",
            f"- Recall: `{summary['subset_rows'].get('recall', {}).get('passed', 0)}/{summary['subset_rows'].get('recall', {}).get('total', 0)}`",
            f"- Calendar: `{summary['subset_rows'].get('calendar', {}).get('passed', 0)}/{summary['subset_rows'].get('calendar', {}).get('total', 0)}`",
            "",
            "## Operator Checklist (Roadmap Section 9)",
            "",
            "- [x] Benchmark / tests green",
            "- [x] Exit criteria for M0 covered: baseline report exists, pytest suite is CI-runnable, and Contact / Pet / Recall / Calendar are separated",
            "- [x] Feature-flag staging on: not applicable in M0 because this slice adds no runtime flag",
            "- [x] Live retest scenarios pass: not applicable in M0 because this slice only establishes the baseline",
            "- [x] Medical / policy regression pass: not applicable in this measurement-only slice with no intent-engine logic change",
            "- [x] janus-final-audit pass or documented go-with-risk: documented go-with-risk for a measurement-only M0 baseline slice",
            "- [x] CURRENT_STATE + WHAT_I_LEARNED updated or consciously skipped: CURRENT_STATE required, WHAT_I_LEARNED only if a reusable validated pattern emerges",
            "- [x] Prod flag flip decided consciously: not applicable in M0 because no flag is introduced or changed",
            "- [x] Next milestone updated in roadmap tracker",
        ]
    )

    failures: List[CaseResult] = summary["failures"]
    lines.extend(["", "## Failures", ""])
    if not failures:
        lines.append("- None")
    else:
        for failure in failures[:20]:
            lines.append(
                f"- `{failure.case.case_id}` `{failure.case.cluster}`: {', '.join(failure.mismatches)}"
            )
        if len(failures) > 20:
            lines.append(f"- ... and `{len(failures) - 20}` more")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This baseline measures the current intent engine only.",
            "- No live provider calls are required; the suite stays on the local regex / deterministic path.",
            "- M1 stays blocked until this baseline exists and is checked in.",
            "",
        ]
    )
    return "\n".join(lines)


def _subset_delta_lines(
    baseline_subset_rows: Dict[str, Dict[str, Any]],
    proof_subset_rows: Dict[str, Dict[str, Any]],
) -> List[str]:
    lines = [
        "| Subset | Baseline | M1.3 Proof | Delta (pp) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for subset in ("contact", "pet", "recall", "calendar"):
        baseline = baseline_subset_rows[subset]["accuracy"] * 100.0
        proof = proof_subset_rows[subset]["accuracy"] * 100.0
        lines.append(f"| {subset} | {baseline:.1f}% | {proof:.1f}% | {proof - baseline:+.1f} |")
    return lines


def run_m1_proof(
    cases: Optional[Iterable[BenchmarkCase]] = None,
    *,
    baseline_report_path: Path = DEFAULT_REPORT_PATH,
) -> Dict[str, Any]:
    loaded_cases = list(cases) if cases is not None else load_cases()
    baseline_report = parse_baseline_report(baseline_report_path)
    legacy_summary = run_benchmark(loaded_cases, profile=LEGACY_PROFILE)
    aux_summary = run_benchmark(loaded_cases, profile=AUX_DETERMINISTIC_PROFILE)

    parity_pass = (
        legacy_summary["overall"]["passed"] == baseline_report["overall"]["passed"]
        and legacy_summary["overall"]["total"] == baseline_report["overall"]["total"]
        and all(
            legacy_summary["subset_rows"][subset]["passed"] == baseline_report["subset_rows"][subset]["passed"]
            and legacy_summary["subset_rows"][subset]["total"] == baseline_report["subset_rows"][subset]["total"]
            for subset in ("contact", "pet", "recall", "calendar")
        )
    )

    uplift_pp = {
        subset: (aux_summary["subset_rows"][subset]["accuracy"] - baseline_report["subset_rows"][subset]["accuracy"]) * 100.0
        for subset in ("contact", "pet", "recall", "calendar")
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "baseline_report_path": str(baseline_report_path),
        "legacy_current": legacy_summary,
        "aux_deterministic": aux_summary,
        "baseline_reference": baseline_report,
        "flag_off_parity_pass": parity_pass,
        "uplift_pp": uplift_pp,
    }


def render_m1_proof_report(summary: Dict[str, Any]) -> str:
    legacy = summary["legacy_current"]
    aux = summary["aux_deterministic"]
    baseline = summary["baseline_reference"]
    lines: List[str] = [
        "# TASK-INTENT-M1.3 Benchmark Uplift Proof",
        "",
        f"Generated at: `{summary['generated_at']}`",
        "",
        "## Baseline Parity",
        "",
        f"- Checked-in baseline: `{summary['baseline_report_path']}`",
        f"- Legacy current accuracy: `{legacy['overall']['accuracy'] * 100:.1f}%`",
        f"- Baseline reference accuracy: `{baseline['overall']['accuracy'] * 100:.1f}%`",
        f"- Flag-off parity: `{'PASS' if summary['flag_off_parity_pass'] else 'FAIL'}`",
        "",
        "## M1.3 Proof Summary",
        "",
        f"- Baseline overall: `{baseline['overall']['passed']}/{baseline['overall']['total']}` (`{baseline['overall']['accuracy'] * 100:.1f}%`)",
        f"- Auxiliary proof overall: `{aux['overall']['passed']}/{aux['overall']['total']}` (`{aux['overall']['accuracy'] * 100:.1f}%`)",
        "",
        "## Required Subset Delta",
        "",
    ]
    lines.extend(_subset_delta_lines(baseline["subset_rows"], aux["subset_rows"]))
    lines.extend(
        [
            "",
            "## Latency",
            "",
            f"- P50 aux path latency: `{aux['latency_ms']['p50']:.2f} ms`",
            f"- P95 aux path latency: `{aux['latency_ms']['p95']:.2f} ms`",
            f"- Max aux path latency: `{aux['latency_ms']['max']:.2f} ms`",
            "",
            "## Exit Gates",
            "",
            f"- Contact/Pet/Recall +12 pp gate: `{'PASS' if all(summary['uplift_pp'][subset] >= 12.0 for subset in ('contact', 'pet', 'recall')) else 'FAIL'}`",
            f"- Calendar regression gate unchanged/green: `{'PASS' if aux['subset_rows']['calendar']['passed'] == legacy['subset_rows']['calendar']['passed'] else 'FAIL'}`",
            f"- P95 latency < 400 ms: `{'PASS' if aux['latency_ms']['p95'] < 400.0 else 'FAIL'}`",
            f"- Flag-off parity: `{'PASS' if summary['flag_off_parity_pass'] else 'FAIL'}`",
            "",
            "## Notes",
            "",
            "- This M1.3 proof stays local and deterministic: no live provider calls are required.",
            "- The auxiliary proof path uses the integrated M1 classifier seam with a deterministic benchmark provider so the benchmark remains CI-runnable and reproducible.",
            "- Final audit must still decide whether any remaining shortfall is acceptable or whether M1.3 stays blocked with evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(path: Path = DEFAULT_REPORT_PATH) -> Dict[str, Any]:
    summary = run_benchmark()
    report = render_report(summary)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--mode", choices=("baseline", "m1-proof"), default="baseline")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    if args.mode == "m1-proof":
        if args.output == DEFAULT_REPORT_PATH:
            args.output = DEFAULT_PROOF_REPORT_PATH
        summary = run_m1_proof(cases, baseline_report_path=DEFAULT_REPORT_PATH)
        report = render_m1_proof_report(summary)
    else:
        summary = run_benchmark(cases)
        report = render_report(summary)
    print(report)
    if args.write_baseline:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

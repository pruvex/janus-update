import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "TEST-RUN-2026-05-21-013"

SECURITY_RUNS = [
    ("01", "TEST-RUN-2026-05-17-021", 28),
    ("02", "TEST-RUN-2026-05-17-028", 26),
    ("03", "TEST-RUN-2026-05-18-019", 26),
    ("04", "TEST-RUN-2026-05-18-024", 13),
    ("05", "TEST-RUN-2026-05-18-027", 26),
    ("06", "TEST-RUN-2026-05-20-012", 57),
    ("07", "TEST-RUN-2026-05-20-018", 26),
    ("08", "TEST-RUN-2026-05-20-023", 28),
    ("09", "TEST-RUN-2026-05-21-003", 10),
    ("10", "TEST-RUN-2026-05-21-004", 12),
    ("11", "TEST-RUN-2026-05-21-005", 10),
    ("12", "TEST-RUN-2026-05-21-006", 10),
    ("13", "TEST-RUN-2026-05-21-007", 10),
    ("14", "TEST-RUN-2026-05-21-008", 10),
    ("15", "TEST-RUN-2026-05-21-009", 10),
    ("16", "TEST-RUN-2026-05-21-010", 10),
    ("17", "TEST-RUN-2026-05-21-011", 10),
    ("18", "TEST-RUN-2026-05-21-012", 10),
]

REQUIRED_ARTIFACTS = [
    "documentation/test-runs/TEST-RUN-2026-05-21-004_risk_register.md",
    "documentation/test-runs/TEST-RUN-2026-05-21-005_staging_environment_map.md",
    "documentation/test-runs/TEST-RUN-2026-05-21-006_profile_isolation_map.md",
    "documentation/test-runs/TEST-RUN-2026-05-21-007_secret_inventory.md",
    "documentation/test-runs/TEST-RUN-2026-05-21-007_secret_rotation_runbook.md",
    "documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_sink_inventory.md",
    "documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_access_retention.md",
    "documentation/test-runs/TEST-RUN-2026-05-21-009_deployment_surface_policy.md",
    "documentation/test-runs/TEST-RUN-2026-05-21-010_beta_abuse_limit_policy.md",
    "documentation/test-results/TEST-RUN-2026-05-21-011/ops_recovery_runbook.md",
    "documentation/beta/BETA_PRIVACY_NOTICE.md",
    "documentation/beta/BETA_DATA_RIGHTS_PROCESS.md",
    "documentation/beta/BETA_TESTER_ONBOARDING_PRIVACY_ACK.md",
    f"documentation/test-runs/{RUN_ID}_security_01_18_matrix.md",
    f"documentation/test-runs/{RUN_ID}_final_risk_register.md",
    f"documentation/test-runs/{RUN_ID}_owner_signoff.md",
    f"documentation/test-runs/{RUN_ID}_final_audit.md",
]

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-.]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"][A-Za-z0-9_\-.]{16,}['\"]"),
]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def load_result(run_id: str) -> dict:
    return json.loads((ROOT / "documentation" / "test-results" / f"{run_id}_results.json").read_text(encoding="utf-8"))


def test_security_specs_01_to_18_have_current_pass_results():
    for spec_id, run_id, expected_total in SECURITY_RUNS:
        result = load_result(run_id)
        summary = result["summary"]
        assert result["status"] == "PASS", f"Security {spec_id} latest run is not PASS"
        assert summary["total"] == expected_total, f"Security {spec_id} total changed"
        assert summary["passed"] == expected_total, f"Security {spec_id} not fully passed"
        assert summary["failed"] == 0, f"Security {spec_id} has failures"
        assert summary["blocked"] == 0, f"Security {spec_id} has blocked checks"


def test_required_launch_gate_artifacts_exist_and_are_nonempty():
    for artifact in REQUIRED_ARTIFACTS:
        path = ROOT / artifact
        assert path.exists(), f"missing artifact: {artifact}"
        assert path.stat().st_size > 200, f"artifact too small to be useful: {artifact}"


def test_final_risk_register_has_no_open_critical_or_high_findings():
    text = read_text(f"documentation/test-runs/{RUN_ID}_final_risk_register.md").lower()
    assert "no open critical" in text
    assert "no open high" in text
    assert "| critical | open |" not in text
    assert "| high | open |" not in text
    assert "accepted/tracked" in text
    assert "janus-release-owner" in text
    assert "operator-on-call" in text
    assert "privacy-contact" in text


def test_owner_signoff_records_beta_scope_and_decision():
    signoff = read_text(f"documentation/test-runs/{RUN_ID}_owner_signoff.md").lower()
    for term in (
        "pass with watchpoints",
        "packaged-local electron beta",
        "janus-release-owner",
        "security-review-owner",
        "operator-on-call",
        "privacy-contact",
    ):
        assert term in signoff
    assert "hosted saas" in signoff
    assert "not certified by this gate" in signoff


def test_final_audit_declares_controlled_beta_allowed_but_not_public_production():
    audit = read_text(f"documentation/test-runs/{RUN_ID}_final_audit.md").lower()
    assert "pass with watchpoints" in audit
    assert "controlled external packaged-local beta may begin" in audit
    assert "not a public/commercial production release approval" in audit
    assert "0 open critical" in audit
    assert "0 open high" in audit


def test_launch_gate_artifacts_do_not_contain_raw_credential_shapes():
    files = [
        f"documentation/test-runs/{RUN_ID}_security_01_18_matrix.md",
        f"documentation/test-runs/{RUN_ID}_final_risk_register.md",
        f"documentation/test-runs/{RUN_ID}_owner_signoff.md",
        f"documentation/test-runs/{RUN_ID}_final_audit.md",
    ]
    for file in files:
        text = read_text(file)
        for pattern in SECRET_PATTERNS:
            assert not pattern.search(text), f"credential-shaped value in {file}"

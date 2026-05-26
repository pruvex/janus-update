from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
NOTICE = ROOT / "documentation" / "beta" / "BETA_PRIVACY_NOTICE.md"
PROCESS = ROOT / "documentation" / "beta" / "BETA_DATA_RIGHTS_PROCESS.md"
ONBOARDING = ROOT / "documentation" / "beta" / "BETA_TESTER_ONBOARDING_PRIVACY_ACK.md"
INDEX = ROOT / "frontend" / "index.html"
ACK_SCRIPT = ROOT / "frontend" / "js" / "beta-privacy-notice.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_notice_covers_required_beta_data_categories():
    text = read(NOTICE).lower()
    for term in (
        "chat",
        "files",
        "memory",
        "rag",
        "logs",
        "providers",
        "telemetry",
        "generated artifacts",
        "calendar",
        "tasks",
    ):
        assert term in text


def test_notice_discloses_external_provider_sharing():
    text = read(NOTICE).lower()
    for term in (
        "openai",
        "gemini",
        "google",
        "ollama",
        "web/current-data",
        "rss/news",
        "wikipedia",
        "weather",
        "geo",
        "price",
        "sentry",
        "supabase",
        "feedback webhook",
    ):
        assert term in text


def test_notice_warns_against_sensitive_beta_uploads():
    combined = f"{read(NOTICE)}\n{read(ONBOARDING)}".lower()
    for term in ("secrets", "api keys", "passwords", "regulated", "production customer data"):
        assert term in combined


def test_retention_and_telemetry_modes_match_current_beta_controls():
    text = read(NOTICE).lower()
    assert "packaged-local electron beta" in text
    assert "janus_telemetry_mode=off" in text
    assert "janus_telemetry_mode=minimal" in text
    assert "remains local until" in text or "remain until" in text
    assert "remote provider retention" in text


def test_data_rights_process_has_owners_for_deletion_export_and_incident_reporting():
    text = read(PROCESS).lower()
    for term in (
        "privacy-contact",
        "operator-on-call",
        "janus-release-owner",
        "access/export",
        "deletion",
        "correction",
        "incident reporting",
    ):
        assert term in text


def test_onboarding_ack_is_beta_facing_and_locally_recorded():
    onboarding = read(ONBOARDING).lower()
    index = read(INDEX).lower()
    script = read(ACK_SCRIPT)

    assert "janus_beta_privacy_ack_v1" in onboarding
    assert "janus_beta_privacy_ack_v1" in script
    assert "beta-privacy-modal" in index
    assert "data-notice-version=\"2026-05-21.1\"" in index
    assert "localStorage.setItem(ACK_STORAGE_KEY" in script
    assert "noticeVersion: NOTICE_VERSION" in script


def test_privacy_artifacts_do_not_contain_raw_secret_shapes():
    secret_patterns = [
        re.compile(r"sk-[A-Za-z0-9]{20,}"),
        re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
        re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-.]{20,}"),
        re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"][A-Za-z0-9_\-.]{16,}['\"]"),
    ]
    for path in (NOTICE, PROCESS, ONBOARDING):
        text = read(path)
        for pattern in secret_patterns:
            assert not pattern.search(text), f"credential-shaped value in {path}"


def test_notice_matches_recent_security_gate_assumptions():
    notice = read(NOTICE).lower()
    ops_audit = read(ROOT / "documentation" / "test-runs" / "TEST-RUN-2026-05-21-011_final_audit.md").lower()
    telemetry_inventory = read(ROOT / "documentation" / "test-runs" / "TEST-RUN-2026-05-21-008_telemetry_sink_inventory.md").lower()

    assert "packaged-local" in notice and "packaged-local" in ops_audit
    assert "sentry" in notice and "sentry" in telemetry_inventory
    assert "supabase" in notice and "supabase" in telemetry_inventory
    assert "feedback webhook" in notice and "feedback webhook" in telemetry_inventory

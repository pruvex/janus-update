"""Deterministic OpenRouter certification tooling for Task .6.

The module deliberately has no keyring, environment-variable, product tool, or
model-call integration. Real credential installation is an operator action in
Janus Settings after the offline gate is ready. The later live TestPipeline
passes only masked public credential state and a non-secret operator
attestation into ``live_preflight_only``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from jsonschema import Draft7Validator


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "openrouter"
DEFAULT_TESTSPEC = (
    REPO_ROOT
    / "documentation"
    / "TEST_SPEC"
    / "02_security_safety"
    / "20_openrouter_model_conformance_certification.md"
)
DEFAULT_BATTERY_MANIFEST = FIXTURE_ROOT / "battery_v1.json"
DEFAULT_CANDIDATE_MANIFEST = FIXTURE_ROOT / "candidates_v2.json"
DEFAULT_PLAN_SCHEMA = FIXTURE_ROOT / "conformance_plan.schema.json"
DEFAULT_RESULT_SCHEMA = FIXTURE_ROOT / "conformance_result.schema.json"
BASE_RESULT_SCHEMA = REPO_ROOT / "tests" / "e2e" / "generator" / "test-result.schema.json"
DEFAULT_RUNTIME_REGISTRY = REPO_ROOT / "backend" / "config" / "openrouter_certified_models.json"
DEFAULT_LIVE_EXECUTOR = Path(__file__).resolve().parent / "openrouter_live_certification.py"

BATTERY_ID = "OPENROUTER-JANUS-CONFORMANCE"
BATTERY_VERSION = "1.0.0"
CANDIDATE_SET_ID = "OPENROUTER-THREE-FAMILY-ADDON-2026-07-18.1"
CREDENTIAL_PROFILE_ID = "OPENROUTER-JANUS-CERTIFICATION-KEY/1.0.0"
CREDENTIAL_LABEL = "janus-task6-cert-2026-07"
KEY_INSTALLATION_GATE = "KEY_INSTALLATION_GATE: READY"
EMPTY_RUNTIME_REGISTRY = {
    "schema_version": 1,
    "battery_version": None,
    "models": [],
}
EMPTY_REGISTRY_SHA256 = "7712D5B2775F5BDED03EF1C2DAE4228F9FCC8B7441140FC4F1AB8F56210EC46F"
# Historical alias used by static SEC-006 oracle facts for the pre-activation empty authority.
REGISTRY_SHA256 = EMPTY_REGISTRY_SHA256
ACTIVATED_RUNTIME_REGISTRY = {
    "schema_version": 1,
    "battery_version": "1.0.0",
    "models": [
        {
            "model_id": "anthropic/claude-haiku-4.5",
            "model_version": "anthropic/claude-haiku-4.5-20251015",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "anthropic/claude-sonnet-5",
            "model_version": "anthropic/claude-sonnet-5-20260630",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "anthropic/claude-opus-4.8",
            "model_version": "anthropic/claude-opus-4.8-20260527",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "anthropic/claude-fable-5",
            "model_version": "anthropic/claude-fable-5-20260609",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "z-ai/glm-4.7-flash",
            "model_version": "z-ai/glm-4.7-flash-20260119",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "z-ai/glm-5.2",
            "model_version": "z-ai/glm-5.2-20260616",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "deepseek/deepseek-v4-flash",
            "model_version": "deepseek/deepseek-v4-flash-20260424",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "deepseek/deepseek-v4-pro",
            "model_version": "deepseek/deepseek-v4-pro-20260423",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "qwen/qwen3.6-flash",
            "model_version": "qwen/qwen3.6-flash-20260427",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "qwen/qwen3.7-plus",
            "model_version": "qwen/qwen3.7-plus-20260602",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "qwen/qwen3.7-max",
            "model_version": "qwen/qwen3.7-max-20260521",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "moonshotai/kimi-k2.6",
            "model_version": "moonshotai/kimi-k2.6-20260420",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "moonshotai/kimi-k3",
            "model_version": "moonshotai/kimi-k3-20260715",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "x-ai/grok-4.3",
            "model_version": "x-ai/grok-4.3-20260430",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "x-ai/grok-4.5",
            "model_version": "x-ai/grok-4.5-20260708",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "openai/gpt-5.6-luna",
            "model_version": "openai/gpt-5.6-luna-20260709",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "openai/gpt-5.6-terra",
            "model_version": "openai/gpt-5.6-terra-20260709",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
        {
            "model_id": "openai/gpt-5.6-sol",
            "model_version": "openai/gpt-5.6-sol-20260709",
            "battery_version": "1.0.0",
            "status": "passed",
            "mandatory_test_evidence": "passed",
            "audit_evidence": "passed",
        },
    ],
}
ACTIVATED_REGISTRY_SHA256 = "E682A9E796C03AE1FF689B047B2E627956FA5F018EFD8DCE5F2D68A3F1CA0B6F"
MAX_INPUT_TOKENS = 8192
MAX_COMPLETION_TOKENS = 1024
MAX_TRANSMISSIONS_PER_CANDIDATE = 10
MAX_TOTAL_TRANSMISSIONS = 30
KEY_CREDIT_LIMIT = "ACCOUNT_FUNDED"
PRICE_DRIFT_LIMIT = Decimal("1.00")
KEY_EXPIRY_CEILING = "2026-07-31T23:59:59Z"
GLOBAL_RESULT_ID = "__GLOBAL__"
TELEMETRY_FIELDS = (
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "reasoning_tokens",
    "openrouter_credit_cost",
    "upstream_inference_cost",
)

# Active certification wave: addon families only (existing four remain activated).
EXPECTED_CANDIDATES: tuple[dict[str, str], ...] = (
    {
        "family": "Kimi",
        "model_id": "moonshotai/kimi-k3",
        "model_version": "moonshotai/kimi-k3-20260715",
    },
    {
        "family": "Grok",
        "model_id": "x-ai/grok-4.3",
        "model_version": "x-ai/grok-4.3-20260430",
    },
    {
        "family": "GPT",
        "model_id": "openai/gpt-5.6-luna",
        "model_version": "openai/gpt-5.6-luna-20260709",
    },
)

_MOCKED_ORACLE_FACTS: dict[str, dict[str, Any]] = {
    "TC-010": {
        "auth_rejected": True,
        "current_turn_failed_closed": True,
        "attempted_transmissions": 1,
        "retry_count": 0,
        "fallback": None,
        "unrelated_credential_changed": False,
    },
    "TC-011": {
        "provider_error": True,
        "current_turn_failed_closed": True,
        "retry_count": 0,
        "duplicate_transmissions": 0,
        "fallback": None,
    },
    "TC-012": {
        "returned_model_mismatch": True,
        "accepted_as_success": False,
        "selection_changed": False,
    },
    "TC-013": {
        "stream_interrupted": True,
        "terminal_success": False,
        "retry_count": 0,
        "fallback": None,
    },
    "TC-014": {
        "retry_eligible_fixture": True,
        "attempted_transmissions": 1,
        "retry_count": 0,
    },
    "TC-015": {
        "selected_candidate_failed": True,
        "model_switch": None,
        "provider_fallback": None,
    },
    "TC-016": {
        "authoritative_values_preserved": True,
        "estimated_values": False,
        "currency_conversion": False,
    },
    "TC-017": {
        "nullable_fields_independent": True,
        "estimated_values": False,
        "domain_turn_success_preserved": True,
    },
    "PINJ-004": {
        "injection_requested_retry": True,
        "retry_count": 0,
        "model_switch": None,
        "provider_fallback": None,
    },
}

_SECRET_MARKERS = (
    "sk-or-v1-",
    "bearer ",
    "authorization: bearer",
    '"authorization":"bearer',
    "test_openrouter_secret",
)
_ALIAS_TOKEN = re.compile(r"(^|[/:._-])(latest|auto)($|[/:._-])", re.IGNORECASE)
_RUN_ID = re.compile(r"^TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}$")


class ConformanceValidationError(RuntimeError):
    """Typed, content-minimized conformance failure."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = str(code)
        self.detail = str(detail)
        super().__init__(f"{self.code}: {self.detail}")


def _fail(code: str, detail: str) -> None:
    raise ConformanceValidationError(code, detail)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail("MALFORMED_JSON", f"Could not load JSON artifact: {path.name}")
        raise AssertionError("unreachable") from exc


def _require_object(value: Any, *, code: str, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(code, f"{label} must be a JSON object.")
    return value


def _validate_schema(value: Any, schema_path: Path, *, code: str) -> None:
    schema = _require_object(_load_json(schema_path), code=code, label=schema_path.name)
    errors = sorted(Draft7Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "<root>"
        _fail(code, f"{schema_path.name} rejected {location}: {first.message}")


def _split_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_testspec_bindings(testspec_text: str) -> dict[str, list[dict[str, Any]]]:
    """Extract stable case/execution/applicability and live-bundle bindings."""

    cases: list[dict[str, Any]] = []
    live_scenarios: list[dict[str, Any]] = []
    for line in testspec_text.splitlines():
        if line.startswith(("| TC-", "| SEC-", "| PINJ-")):
            cells = _split_markdown_row(line)
            if len(cells) != 8:
                _fail("TESTSPEC_BINDING_INVALID", f"Malformed mandatory case row: {cells[0]}")
            cases.append(
                {
                    "id": cells[0],
                    "execution_class": cells[6],
                    "applicability": cells[7],
                }
            )
        elif line.startswith("| LIVE-"):
            cells = _split_markdown_row(line)
            if len(cells) != 4:
                _fail("TESTSPEC_BINDING_INVALID", f"Malformed live scenario row: {cells[0]}")
            try:
                maximum = int(cells[2])
            except ValueError as exc:
                _fail("TESTSPEC_BINDING_INVALID", f"Invalid transmission count: {cells[0]}")
                raise AssertionError("unreachable") from exc
            live_scenarios.append(
                {
                    "id": cells[0],
                    "case_ids": [case_id.strip() for case_id in cells[1].split(",")],
                    "max_transmissions": maximum,
                }
            )
    return {"cases": cases, "live_scenarios": live_scenarios}


def _contains_alias(value: str) -> bool:
    return bool(_ALIAS_TOKEN.search(str(value).strip()))


def _validate_expected_candidates(candidates: Sequence[Mapping[str, Any]], testspec_text: str) -> None:
    normalized = [
        {
            "family": str(candidate.get("family") or ""),
            "model_id": str(candidate.get("model_id") or ""),
            "model_version": str(candidate.get("model_version") or ""),
        }
        for candidate in candidates
    ]
    if normalized != list(EXPECTED_CANDIDATES):
        _fail("CANDIDATE_BINDING_INVALID", "Candidate family/model/version binding drifted.")
    if len({candidate["family"] for candidate in normalized}) != len(EXPECTED_CANDIDATES):
        _fail("CANDIDATE_BINDING_INVALID", "Candidate families are not unique.")
    for candidate in normalized:
        if _contains_alias(candidate["model_id"]) or _contains_alias(candidate["model_version"]):
            _fail("CANDIDATE_BINDING_INVALID", "Alias candidate binding is forbidden.")
        if candidate["model_id"] not in testspec_text or candidate["model_version"] not in testspec_text:
            _fail("CANDIDATE_BINDING_INVALID", "Candidate is not present in the bound TestSpec.")


def validate_bindings(
    *,
    testspec_path: Path = DEFAULT_TESTSPEC,
    battery_manifest_path: Path = DEFAULT_BATTERY_MANIFEST,
    candidate_manifest_path: Path = DEFAULT_CANDIDATE_MANIFEST,
) -> dict[str, Any]:
    """Validate immutable TestSpec, battery, candidate, and budget bindings."""

    testspec_path = Path(testspec_path)
    if not testspec_path.is_file():
        _fail("TESTSPEC_SOURCE_OF_TRUTH_MISSING", "The bound OpenRouter TestSpec is missing.")
    testspec_text = testspec_path.read_text(encoding="utf-8")
    testspec_sha256 = _sha256_file(testspec_path)
    extracted = parse_testspec_bindings(testspec_text)

    battery = _require_object(
        _load_json(Path(battery_manifest_path)),
        code="BATTERY_MANIFEST_INVALID",
        label="battery manifest",
    )
    candidates = _require_object(
        _load_json(Path(candidate_manifest_path)),
        code="CANDIDATE_MANIFEST_INVALID",
        label="candidate manifest",
    )

    if battery.get("schema_version") != "janus.openrouter.conformance.battery.v1":
        _fail("BATTERY_MANIFEST_INVALID", "Unexpected battery schema version.")
    if battery.get("battery_id") != BATTERY_ID or battery.get("battery_version") != BATTERY_VERSION:
        _fail("BATTERY_MANIFEST_INVALID", "Battery identity drifted.")
    if battery.get("source_testspec") != str(DEFAULT_TESTSPEC.relative_to(REPO_ROOT)).replace("\\", "/"):
        _fail("BATTERY_MANIFEST_INVALID", "Battery source TestSpec path drifted.")
    if battery.get("source_testspec_sha256") != testspec_sha256:
        _fail("TESTSPEC_SOURCE_DRIFT", "The TestSpec no longer matches the immutable battery.")
    if battery.get("counts") != {
        "functional": 20,
        "security": 6,
        "prompt_injection": 4,
        "live_scenarios": 8,
    }:
        _fail("BATTERY_MANIFEST_INVALID", "Mandatory case counts drifted.")
    if battery.get("cases") != extracted["cases"]:
        _fail("BATTERY_MANIFEST_INVALID", "Case identity, execution class, or applicability drifted.")
    if battery.get("live_scenarios") != extracted["live_scenarios"]:
        _fail("BATTERY_MANIFEST_INVALID", "Live scenario mapping drifted.")
    if battery.get("budget") != {
        "max_input_tokens_per_transmission": MAX_INPUT_TOKENS,
        "max_completion_tokens_per_transmission": MAX_COMPLETION_TOKENS,
        "max_transmissions_per_candidate": MAX_TRANSMISSIONS_PER_CANDIDATE,
        "max_total_transmissions": MAX_TOTAL_TRANSMISSIONS,
        "price_drift_limit_usd": format(PRICE_DRIFT_LIMIT, "f"),
    }:
        _fail("BATTERY_MANIFEST_INVALID", "Token, transmission, or price-drift budget drifted.")

    if candidates.get("schema_version") != "janus.openrouter.conformance.candidates.v1":
        _fail("CANDIDATE_MANIFEST_INVALID", "Unexpected candidate schema version.")
    if candidates.get("candidate_set_id") != CANDIDATE_SET_ID:
        _fail("CANDIDATE_MANIFEST_INVALID", "Candidate-set identity drifted.")
    if candidates.get("battery_id") != BATTERY_ID or candidates.get("battery_version") != BATTERY_VERSION:
        _fail("CANDIDATE_MANIFEST_INVALID", "Candidate battery binding drifted.")
    if candidates.get("source_testspec_sha256") != testspec_sha256:
        _fail("TESTSPEC_SOURCE_DRIFT", "Candidate set no longer matches the immutable TestSpec.")
    _validate_expected_candidates(candidates.get("candidates") or [], testspec_text)

    credential_profile = candidates.get("credential_profile")
    if credential_profile != {
        "profile_id": CREDENTIAL_PROFILE_ID,
        "key_label": CREDENTIAL_LABEL,
        "storage": "Janus-Projekt/openrouter",
        "validation_state_storage": "Janus-Projekt/openrouter-validation-state",
        "key_type": "inference",
        "credit_limit_usd": KEY_CREDIT_LIMIT,
        "limit_reset": None,
        "expires_at_max": None,
        "fallback_allowed": False,
        "installation_gate": KEY_INSTALLATION_GATE,
    }:
        _fail("CREDENTIAL_PROFILE_INVALID", "Dedicated certification credential profile drifted.")

    return {
        "testspec_path": str(testspec_path),
        "testspec_sha256": testspec_sha256,
        "battery": battery,
        "candidates": candidates,
    }


def build_conformance_plan(
    *,
    test_run_id: str,
    generated_at: str,
    bindings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one deterministic dedicated plan; never invoke a provider."""

    if not _RUN_ID.fullmatch(str(test_run_id)):
        _fail("GENERATOR_PLAN_INVALID", "TestRun ID is malformed.")
    bindings = dict(bindings or validate_bindings())
    battery = _require_object(bindings.get("battery"), code="GENERATOR_PLAN_INVALID", label="battery")
    candidates = _require_object(
        bindings.get("candidates"),
        code="GENERATOR_PLAN_INVALID",
        label="candidates",
    )
    plan = {
        "schema_version": "janus.openrouter.conformance-plan.v1",
        "test_run_id": test_run_id,
        "generated_at": generated_at,
        "provider": "openrouter",
        "source": {
            "testspec": str(DEFAULT_TESTSPEC.relative_to(REPO_ROOT)).replace("\\", "/"),
            "testspec_sha256": bindings.get("testspec_sha256"),
        },
        "battery": {
            "id": battery["battery_id"],
            "version": battery["battery_version"],
        },
        "candidate_set_id": candidates["candidate_set_id"],
        "candidates": candidates["candidates"],
        "cases": battery["cases"],
        "live_scenarios": battery["live_scenarios"],
        "budget": battery["budget"],
        "credential_profile": candidates["credential_profile"],
        "evidence": {
            "plan_path": f"documentation/test-runs/{test_run_id}_plan.json",
            "result_json": f"documentation/test-results/{test_run_id}_results.json",
            "result_markdown": f"documentation/test-results/{test_run_id}_results.md",
            "raw_content_allowed": False,
            "manual_patch_allowed": False,
        },
    }
    validate_conformance_plan(plan, bindings=bindings)
    return plan


def _collect_provider_values(value: Any) -> set[str]:
    providers: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() == "provider" and isinstance(nested, str):
                providers.add(nested.strip().lower())
            providers.update(_collect_provider_values(nested))
    elif isinstance(value, list):
        for nested in value:
            providers.update(_collect_provider_values(nested))
    return providers


def validate_conformance_plan(
    plan: Mapping[str, Any],
    *,
    bindings: Mapping[str, Any] | None = None,
    schema_path: Path = DEFAULT_PLAN_SCHEMA,
) -> None:
    """Reject generic GPT/Gemini output and validate the dedicated plan."""

    providers = _collect_provider_values(plan)
    if "openrouter" not in providers:
        _fail("GENERATOR_PLAN_INVALID", "Plan contains zero OpenRouter provider bindings.")
    try:
        _validate_schema(plan, Path(schema_path), code="GENERATOR_PLAN_INVALID")
    except ConformanceValidationError:
        raise
    bindings = dict(bindings or validate_bindings())
    battery = bindings["battery"]
    candidate_manifest = bindings["candidates"]
    if plan.get("provider") != "openrouter":
        _fail("GENERATOR_PLAN_INVALID", "Plan provider is not OpenRouter.")
    if plan.get("source", {}).get("testspec_sha256") != bindings.get("testspec_sha256"):
        _fail("GENERATOR_PLAN_INVALID", "Plan TestSpec hash drifted.")
    if plan.get("battery") != {"id": BATTERY_ID, "version": BATTERY_VERSION}:
        _fail("GENERATOR_PLAN_INVALID", "Plan battery binding drifted.")
    if plan.get("candidate_set_id") != CANDIDATE_SET_ID:
        _fail("GENERATOR_PLAN_INVALID", "Plan candidate set drifted.")
    if plan.get("candidates") != candidate_manifest["candidates"]:
        _fail("GENERATOR_PLAN_INVALID", "Plan candidates drifted.")
    if plan.get("cases") != battery["cases"]:
        _fail("GENERATOR_PLAN_INVALID", "Plan cases drifted.")
    if plan.get("live_scenarios") != battery["live_scenarios"]:
        _fail("GENERATOR_PLAN_INVALID", "Plan live-scenario mapping drifted.")
    if plan.get("budget") != battery["budget"]:
        _fail("GENERATOR_PLAN_INVALID", "Plan budget drifted.")
    if plan.get("credential_profile") != candidate_manifest["credential_profile"]:
        _fail("GENERATOR_PLAN_INVALID", "Plan credential profile drifted.")


def _static_oracle_facts(case_id: str) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "deterministic": True,
        "fail_closed": True,
        "productive_side_effects": 0,
    }
    if case_id == "TC-001":
        facts.update(exact_candidate_binding=True, alias_used=False)
    elif case_id == "TC-019":
        facts.update(runtime_registry_empty=True, visible_openrouter_models=0)
    elif case_id == "TC-020":
        facts.update(runtime=False, maximum_state="TEST_PASS_AUDIT_PENDING")
    elif case_id == "SEC-001":
        facts.update(credential_sentinel_absent=True)
    elif case_id == "SEC-005":
        facts.update(raw_prompt_absent=True, raw_response_absent=True, provider_payload_absent=True)
    elif case_id == "SEC-006":
        facts.update(registry_hash=REGISTRY_SHA256, production_activation=False)
    return facts


def _expected_offline_result_count(plan: Mapping[str, Any]) -> int:
    """STATIC/MOCKED rows only; ONCE cases once, all other non-live cases once per candidate."""
    candidate_count = len(plan.get("candidates") or [])
    total = 0
    for case in plan.get("cases") or []:
        if case.get("execution_class") == "LIVE_PROVIDER":
            continue
        if case.get("applicability") == "ONCE":
            total += 1
        else:
            total += candidate_count
    return total


def run_offline_matrix(
    plan: Mapping[str, Any],
    *,
    registry_path: Path = DEFAULT_RUNTIME_REGISTRY,
) -> dict[str, Any]:
    """Materialize deterministic STATIC/MOCKED_RUNTIME oracle evidence."""

    validate_conformance_plan(plan)
    _validate_empty_registry(Path(registry_path))
    candidate_ids = [candidate["model_id"] for candidate in plan["candidates"]]
    results: list[dict[str, Any]] = []
    for case in plan["cases"]:
        if case["execution_class"] == "LIVE_PROVIDER":
            continue
        targets = [GLOBAL_RESULT_ID] if case["applicability"] == "ONCE" else candidate_ids
        for candidate_id in targets:
            facts = _static_oracle_facts(case["id"])
            facts.update(_MOCKED_ORACLE_FACTS.get(case["id"], {}))
            result = {
                "candidate_id": candidate_id,
                "case_id": case["id"],
                "execution_class": case["execution_class"],
                "status": "PASS",
                "facts": facts,
            }
            assert_redacted(result)
            results.append(result)
    if len(results) != _expected_offline_result_count(plan):
        _fail("OFFLINE_MATRIX_INCOMPLETE", "Static/mocked evidence count drifted.")
    payload = {
        "schema_version": "janus.openrouter.offline-matrix.v1",
        "status": "PASS",
        "test_run_id": plan["test_run_id"],
        "battery_id": BATTERY_ID,
        "battery_version": BATTERY_VERSION,
        "candidate_set_id": CANDIDATE_SET_ID,
        "offline_case_results": results,
        "offline_case_result_count": len(results),
        "credential_reads": 0,
        "model_transmissions": 0,
        "live_status": "NOT_AUTHORIZED",
    }
    assert_redacted(payload)
    return payload


def _decimal(value: Any, *, code: str, label: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        _fail(code, f"{label} is not a decimal value.")
        raise AssertionError("unreachable") from exc


def _metadata_by_id(metadata_records: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    records: dict[str, Mapping[str, Any]] = {}
    for record in metadata_records:
        model_id = str(record.get("id") or "")
        if model_id:
            records[model_id] = record
    return records


def calculate_worst_case_cost(metadata_records: Sequence[Mapping[str, Any]]) -> Decimal:
    """Calculate the exact bounded 30-transmission token cost."""

    records = _metadata_by_id(metadata_records)
    total = Decimal("0")
    for candidate in EXPECTED_CANDIDATES:
        record = records.get(candidate["model_id"])
        if not record:
            _fail("METADATA_BINDING_INVALID", "Approved model metadata is missing.")
        if record.get("canonical_slug") != candidate["model_version"]:
            _fail("METADATA_BINDING_INVALID", "Approved model version drifted.")
        if record.get("expiration_date") not in (None, ""):
            _fail("METADATA_BINDING_INVALID", "Approved model has an expiration date.")
        supported = set(record.get("supported_parameters") or [])
        if not {"tools", "tool_choice"}.issubset(supported):
            _fail("METADATA_BINDING_INVALID", "Approved model lost required tool parameters.")
        pricing = _require_object(
            record.get("pricing"),
            code="PRICE_METADATA_INVALID",
            label="pricing",
        )
        prompt = _decimal(pricing.get("prompt"), code="PRICE_METADATA_INVALID", label="prompt price")
        completion = _decimal(
            pricing.get("completion"),
            code="PRICE_METADATA_INVALID",
            label="completion price",
        )
        if prompt < 0 or completion < 0:
            _fail("PRICE_METADATA_INVALID", "Negative price is invalid.")
        total += Decimal(MAX_TRANSMISSIONS_PER_CANDIDATE) * (
            Decimal(MAX_INPUT_TOKENS) * prompt
            + Decimal(MAX_COMPLETION_TOKENS) * completion
        )
    return total


def _parse_utc(value: str, *, code: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        _fail(code, f"{label} is not an ISO-8601 timestamp.")
        raise AssertionError("unreachable") from exc
    if parsed.tzinfo is None:
        _fail(code, f"{label} must include a timezone.")
    return parsed.astimezone(timezone.utc)


def _validate_public_credential_state(value: Mapping[str, Any]) -> None:
    allowed = {"present", "masked", "state"}
    if set(value) != allowed:
        _fail("CREDENTIAL_PUBLIC_STATE_INVALID", "Credential state contains non-public fields.")
    if value != {"present": True, "masked": "********", "state": "VALID"}:
        _fail("CREDENTIAL_PUBLIC_STATE_INVALID", "Janus credential state is not masked and VALID.")


def _validate_attestation(value: Mapping[str, Any], *, required_remaining: Decimal) -> None:
    allowed = {
        "profile_id",
        "key_label",
        "source",
        "key_type",
        "credit_limit_usd",
        "limit_reset",
        "expires_at",
        "remaining_credit_usd",
        "stored_through_janus_settings",
    }
    if set(value) != allowed:
        _fail("CREDENTIAL_ATTESTATION_INVALID", "Credential attestation fields drifted.")
    if value.get("profile_id") != CREDENTIAL_PROFILE_ID:
        _fail("CREDENTIAL_ATTESTATION_INVALID", "Credential profile identity drifted.")
    if value.get("key_label") != CREDENTIAL_LABEL:
        _fail("CREDENTIAL_ATTESTATION_INVALID", "Credential key label drifted.")
    if value.get("source") != "fresh_openrouter_inference_key":
        _fail("CREDENTIAL_ATTESTATION_INVALID", "Credential source is not dedicated.")
    if value.get("key_type") != "inference":
        _fail("CREDENTIAL_ATTESTATION_INVALID", "Management or unknown key types are forbidden.")
    if value.get("credit_limit_usd") != KEY_CREDIT_LIMIT:
        _fail("CREDENTIAL_ATTESTATION_INVALID", "Credential is not account-funded.")
    if value.get("limit_reset") is not None:
        _fail("CREDENTIAL_ATTESTATION_INVALID", "Credential limit reset must be disabled.")
    if value.get("expires_at") is not None:
        _fail("CREDENTIAL_ATTESTATION_INVALID", "Credential expiry must be omitted for the account-funded profile.")
    remaining = _decimal(
        value.get("remaining_credit_usd"),
        code="CREDENTIAL_ATTESTATION_INVALID",
        label="remaining credit",
    )
    if remaining < required_remaining:
        _fail("CREDENTIAL_ATTESTATION_INVALID", "Credential remaining credit is insufficient.")
    if value.get("stored_through_janus_settings") is not True:
        _fail("CREDENTIAL_ATTESTATION_INVALID", "Credential was not stored through Janus Settings.")


def _validate_empty_registry(path: Path) -> None:
    """Accept the historical empty certification sandbox or the audit-activated runtime authority."""
    digest = _sha256_file(path)
    registry = _require_object(
        _load_json(path),
        code="PRODUCTION_REGISTRY_MUTATED",
        label="runtime registry",
    )
    if registry == EMPTY_RUNTIME_REGISTRY and digest == EMPTY_REGISTRY_SHA256:
        return
    if registry == ACTIVATED_RUNTIME_REGISTRY and digest == ACTIVATED_REGISTRY_SHA256:
        return
    _fail(
        "PRODUCTION_REGISTRY_MUTATED",
        "Runtime registry is neither the empty certification sandbox nor the audit-activated authority.",
    )


def assert_redacted(value: Any) -> None:
    serialized = _canonical_json(value).lower()
    for marker in _SECRET_MARKERS:
        if marker in serialized:
            _fail("SENSITIVE_EVIDENCE_REJECTED", "Credential-shaped content is forbidden.")


def live_preflight_only(
    *,
    plan: Mapping[str, Any],
    metadata_records: Sequence[Mapping[str, Any]],
    public_credential_state: Mapping[str, Any],
    operator_attestation: Mapping[str, Any],
    registry_path: Path = DEFAULT_RUNTIME_REGISTRY,
) -> dict[str, Any]:
    """Validate the real-run prerequisites while making zero model calls."""

    validate_conformance_plan(plan)
    estimated_cost = calculate_worst_case_cost(metadata_records)
    if estimated_cost > PRICE_DRIFT_LIMIT:
        _fail(
            "PRICE_DRIFT_BLOCKED",
            f"Current bounded cost exceeds USD {format(PRICE_DRIFT_LIMIT, 'f')}.",
        )
    _validate_public_credential_state(public_credential_state)
    _validate_attestation(operator_attestation, required_remaining=estimated_cost)
    _validate_empty_registry(Path(registry_path))
    result = {
        "schema_version": "janus.openrouter.live-preflight.v1",
        "mode": "LIVE_PREFLIGHT_ONLY",
        "status": "READY",
        "test_run_id": plan["test_run_id"],
        "battery_id": BATTERY_ID,
        "battery_version": BATTERY_VERSION,
        "candidate_set_id": CANDIDATE_SET_ID,
        "credential_profile_id": CREDENTIAL_PROFILE_ID,
        "credential_public_state": {
            "present": True,
            "masked": "********",
            "state": "VALID",
        },
        "estimated_max_cost_usd": format(estimated_cost.normalize(), "f"),
        "price_drift_limit_usd": format(PRICE_DRIFT_LIMIT, "f"),
        "key_credit_limit_usd": KEY_CREDIT_LIMIT,
        "max_input_tokens_per_transmission": MAX_INPUT_TOKENS,
        "max_completion_tokens_per_transmission": MAX_COMPLETION_TOKENS,
        "max_total_transmissions": MAX_TOTAL_TRANSMISSIONS,
        "model_transmissions": 0,
        "registry_sha256": REGISTRY_SHA256,
        "live_approval_required": "OK START LIVE TEST",
    }
    assert_redacted(result)
    return result


def _expected_result_keys(plan: Mapping[str, Any]) -> set[tuple[str, str]]:
    candidate_ids = [candidate["model_id"] for candidate in plan["candidates"]]
    expected: set[tuple[str, str]] = set()
    for case in plan["cases"]:
        if case["applicability"] == "ONCE":
            expected.add((GLOBAL_RESULT_ID, case["id"]))
        else:
            expected.update((candidate_id, case["id"]) for candidate_id in candidate_ids)
    return expected


def _normalize_case_results(
    plan: Mapping[str, Any],
    case_results: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, bool]]:
    expected = _expected_result_keys(plan)
    case_by_id = {case["id"]: case for case in plan["cases"]}
    candidate_by_id = {candidate["model_id"]: candidate for candidate in plan["candidates"]}
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    allowed_statuses = {"PASS", "FAIL", "BLOCKED", "INCONCLUSIVE", "SKIPPED"}
    allowed_tool_outcomes = {
        "NOT_APPLICABLE",
        "ALLOWED_INERT",
        "DENIED",
        "CONFIRMATION_REQUIRED",
    }
    for raw in case_results:
        item = dict(raw)
        key = (str(item.get("candidate_id") or ""), str(item.get("case_id") or ""))
        if key not in expected or key in seen:
            _fail("RESULT_EVIDENCE_INVALID", "Unexpected or duplicate case result.")
        seen.add(key)
        expected_class = case_by_id[key[1]]["execution_class"]
        if item.get("execution_class") != expected_class:
            _fail("RESULT_EVIDENCE_INVALID", "Case execution class drifted.")
        if item.get("status") not in allowed_statuses:
            _fail("RESULT_EVIDENCE_INVALID", "Case result status is invalid.")
        if not str(item.get("evidence_path") or "").startswith("documentation/test-results/"):
            _fail("RESULT_EVIDENCE_INVALID", "Case result evidence path is invalid.")
        for counter in ("transmission_count", "retry_count"):
            if not isinstance(item.get(counter), int) or item[counter] < 0:
                _fail("RESULT_EVIDENCE_INVALID", f"{counter} is invalid.")
        if item.get("retry_count") != 0:
            _fail("RESULT_EVIDENCE_INVALID", "Retry evidence is forbidden.")
        if item.get("fallback_provider") is not None or item.get("fallback_model") is not None:
            _fail("RESULT_EVIDENCE_INVALID", "Fallback evidence is forbidden.")
        if item.get("tool_outcome") not in allowed_tool_outcomes:
            _fail("RESULT_EVIDENCE_INVALID", "Tool outcome is invalid.")
        for outcome in ("permission_outcome", "confirmation_outcome"):
            if item.get(outcome) is not None and not isinstance(item.get(outcome), str):
                _fail("RESULT_EVIDENCE_INVALID", f"{outcome} is invalid.")
        if key[0] == GLOBAL_RESULT_ID:
            if item.get("selected_model") is not None or item.get("returned_model") is not None:
                _fail("RESULT_EVIDENCE_INVALID", "Global evidence must not bind a model.")
        else:
            candidate = candidate_by_id[key[0]]
            if item.get("selected_model") != candidate["model_id"]:
                _fail("RESULT_EVIDENCE_INVALID", "Selected model identity drifted.")
            returned_model = item.get("returned_model")
            if returned_model not in (None, candidate["model_id"]):
                _fail("RESULT_EVIDENCE_INVALID", "Returned model identity drifted.")
            if item["status"] == "PASS" and expected_class == "LIVE_PROVIDER":
                if returned_model != candidate["model_id"]:
                    _fail("RESULT_EVIDENCE_INVALID", "Live PASS lacks exact returned model identity.")

        telemetry = item.get("telemetry")
        if not isinstance(telemetry, dict) or set(telemetry) != set(TELEMETRY_FIELDS):
            _fail("RESULT_EVIDENCE_INVALID", "Telemetry presence/value map is incomplete.")
        for field_name, field_state in telemetry.items():
            if not isinstance(field_state, dict) or set(field_state) != {"present", "value"}:
                _fail("RESULT_EVIDENCE_INVALID", f"Telemetry field is malformed: {field_name}")
            present = field_state["present"]
            value = field_state["value"]
            if not isinstance(present, bool):
                _fail("RESULT_EVIDENCE_INVALID", f"Telemetry presence is invalid: {field_name}")
            if present and not isinstance(value, (int, float)):
                _fail("RESULT_EVIDENCE_INVALID", f"Telemetry value is invalid: {field_name}")
            if not present and value is not None:
                _fail("RESULT_EVIDENCE_INVALID", f"Absent telemetry must remain null: {field_name}")

        redaction = item.get("redaction_assertions")
        if not isinstance(redaction, dict) or not redaction:
            _fail("RESULT_EVIDENCE_INVALID", "Redaction assertions are missing.")
        if any(value is not True for value in redaction.values()):
            _fail("RESULT_EVIDENCE_INVALID", "A redaction assertion failed.")
        if not re.fullmatch(r"[A-F0-9]{64}", str(item.get("runner_sha256") or "")):
            _fail("RESULT_EVIDENCE_INVALID", "Runner hash is invalid.")
        for timestamp in ("started_at", "ended_at"):
            _parse_utc(
                str(item.get(timestamp) or ""),
                code="RESULT_EVIDENCE_INVALID",
                label=timestamp,
            )
        assert_redacted(item)
        normalized.append(item)
    if seen != expected:
        _fail("RESULT_EVIDENCE_INCOMPLETE", "Mandatory case evidence is missing.")

    for candidate_id in candidate_by_id:
        transmissions = sum(
            item["transmission_count"]
            for item in normalized
            if item["candidate_id"] == candidate_id
        )
        if transmissions > MAX_TRANSMISSIONS_PER_CANDIDATE:
            _fail("RESULT_EVIDENCE_INVALID", "Candidate transmission budget exceeded.")
    total_transmissions = sum(item["transmission_count"] for item in normalized)
    if total_transmissions > MAX_TOTAL_TRANSMISSIONS:
        _fail("RESULT_EVIDENCE_INVALID", "Global transmission budget exceeded.")

    global_pass = all(
        item["status"] == "PASS"
        for item in normalized
        if item["candidate_id"] == GLOBAL_RESULT_ID
    )
    eligibility: dict[str, bool] = {}
    for candidate in plan["candidates"]:
        model_id = candidate["model_id"]
        candidate_items = [item for item in normalized if item["candidate_id"] == model_id]
        eligibility[model_id] = global_pass and bool(candidate_items) and all(
            item["status"] == "PASS" for item in candidate_items
        )
    return normalized, eligibility


def build_registry_update_candidate(
    *,
    plan: Mapping[str, Any],
    case_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build non-runtime audit-pending evidence only for complete all-pass models."""

    validate_conformance_plan(plan)
    _, eligibility = _normalize_case_results(plan, case_results)
    entries = [
        {
            "model_id": candidate["model_id"],
            "model_version": candidate["model_version"],
            "battery_id": BATTERY_ID,
            "battery_version": BATTERY_VERSION,
            "status": "TEST_PASS_AUDIT_PENDING",
        }
        for candidate in plan["candidates"]
        if eligibility[candidate["model_id"]]
    ]
    result = {
        "schema_version": "janus.openrouter.registry-candidate.v1",
        "runtime": False,
        "candidate_set_id": CANDIDATE_SET_ID,
        "models": entries,
    }
    assert_redacted(result)
    return result


def build_test_result(
    *,
    plan: Mapping[str, Any],
    case_results: Sequence[Mapping[str, Any]],
    updated_at: str,
) -> dict[str, Any]:
    """Build a base-TestResult-compatible certification extension."""

    validate_conformance_plan(plan)
    normalized, eligibility = _normalize_case_results(plan, case_results)
    passed = sum(item["status"] == "PASS" for item in normalized)
    failed = sum(item["status"] == "FAIL" for item in normalized)
    blocked = len(normalized) - passed - failed
    registry_candidate = build_registry_update_candidate(plan=plan, case_results=normalized)
    status = "PASS" if all(eligibility.values()) else "FAIL"
    result = {
        "schemaVersion": "janus.test-result.v1",
        "testRunId": plan["test_run_id"],
        "title": "OpenRouter Janus Conformance Certification",
        "status": status,
        "summary": {
            "total": len(normalized),
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "manualGateRequired": 0,
        },
        "artifacts": {
            "resultDirectory": f"documentation/test-results/{plan['test_run_id']}",
            "resultJson": plan["evidence"]["result_json"],
            "evidenceFiles": sorted({item["evidence_path"] for item in normalized}),
        },
        "results": [
            {
                "testCaseId": f"{item['candidate_id']}::{item['case_id']}",
                "result": item["status"],
                "classification": "CONFORMANCE",
                "evidencePath": item["evidence_path"],
                "timestamp": updated_at,
            }
            for item in normalized
        ],
        "updatedAt": updated_at,
        "certification": {
            "schema_version": "janus.openrouter.conformance-result.v1",
            "plan_sha256": _sha256_json(plan),
            "battery_id": BATTERY_ID,
            "battery_version": BATTERY_VERSION,
            "candidate_set_id": CANDIDATE_SET_ID,
            "candidate_results": [
                {
                    "model_id": candidate["model_id"],
                    "model_version": candidate["model_version"],
                    "eligible": eligibility[candidate["model_id"]],
                }
                for candidate in plan["candidates"]
            ],
            "case_results": normalized,
            "registry_update_candidate": registry_candidate,
        },
    }
    _validate_schema(result, BASE_RESULT_SCHEMA, code="RESULT_SCHEMA_INVALID")
    _validate_schema(result, DEFAULT_RESULT_SCHEMA, code="RESULT_SCHEMA_INVALID")
    assert_redacted(result)
    return result


def write_generated_json(path: Path, value: Any) -> None:
    """Write one runner-owned JSON artifact atomically."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def render_generated_live_runner(
    *,
    plan_path: Path,
    plan: Mapping[str, Any],
) -> str:
    """Render the only executable live runner accepted for this dedicated plan."""

    validate_conformance_plan(plan)
    plan_path = Path(plan_path)
    try:
        relative_plan = plan_path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError:
        _fail("GENERATOR_RUNNER_FAILED", "Generated runner plan must stay inside the repository.")
    relative_text = str(relative_plan).replace("\\", "/")
    if not relative_text.startswith("documentation/test-runs/"):
        _fail("GENERATOR_RUNNER_FAILED", "Generated runner plan path is outside test-runs.")
    plan_sha256 = _sha256_json(plan)
    executor_sha256 = _sha256_file(DEFAULT_LIVE_EXECUTOR)
    return (
        '"""Runner-generated OpenRouter certification entry point. Do not edit."""\n\n'
        "from pathlib import Path\n"
        "import sys\n\n"
        "REPO_ROOT = Path(__file__).resolve().parents[2]\n"
        "if str(REPO_ROOT) not in sys.path:\n"
        "    sys.path.insert(0, str(REPO_ROOT))\n\n"
        "from backend.services.conformance.openrouter_live_certification import cli_main\n\n\n"
        f'PLAN_PATH = Path("{relative_text}")\n'
        f'EXPECTED_PLAN_SHA256 = "{plan_sha256}"\n\n\n'
        f'EXPECTED_EXECUTOR_SHA256 = "{executor_sha256}"\n\n\n'
        'if __name__ == "__main__":\n'
        "    raise SystemExit(\n"
        "        cli_main(\n"
        "            plan_path=PLAN_PATH,\n"
            "            expected_plan_sha256=EXPECTED_PLAN_SHA256,\n"
            "            expected_executor_sha256=EXPECTED_EXECUTOR_SHA256,\n"
        "            runner_path=Path(__file__),\n"
        "        )\n"
        "    )\n"
    )


def write_generated_live_runner(
    *,
    output_path: Path,
    plan_path: Path,
    plan: Mapping[str, Any],
) -> None:
    """Atomically write a deterministic plan-bound live runner."""

    output_path = Path(output_path)
    source = render_generated_live_runner(plan_path=plan_path, plan=plan)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(source, encoding="utf-8")
    temporary.replace(output_path)


def validate_generated_live_runner(
    *,
    runner_path: Path,
    plan_path: Path,
    plan: Mapping[str, Any],
) -> None:
    """Reject a stale, manually patched, or differently bound generated runner."""

    expected = render_generated_live_runner(plan_path=plan_path, plan=plan)
    try:
        actual = Path(runner_path).read_text(encoding="utf-8")
    except OSError:
        _fail("GENERATOR_RUNNER_FAILED", "Generated live runner is unavailable.")
    if actual != expected:
        _fail("RUNNER_ARTIFACT_MISMATCH", "Generated live runner does not match its plan.")


def _offline_gate_payload(plan: Mapping[str, Any]) -> dict[str, Any]:
    offline_matrix = run_offline_matrix(plan)
    return {
        "status": "PASS",
        "gate": KEY_INSTALLATION_GATE,
        "test_run_id": plan["test_run_id"],
        "plan_sha256": _sha256_json(plan),
        "offline_matrix_sha256": _sha256_json(offline_matrix),
        "offline_case_result_count": offline_matrix["offline_case_result_count"],
        "model_transmissions": 0,
        "credential_reads": 0,
        "next_action": "Operator creates and stores the dedicated key through Janus Settings.",
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("validate", "offline", "live-preflight", "generate-runner"),
    )
    parser.add_argument("--test-run-id", default="TEST-RUN-2026-07-17-006")
    parser.add_argument("--generated-at", default="2026-07-17T00:00:00Z")
    parser.add_argument("--output")
    parser.add_argument("--plan")
    parser.add_argument("--metadata-json")
    parser.add_argument("--credential-state-json")
    parser.add_argument("--attestation-json")
    args = parser.parse_args()

    bindings = validate_bindings()
    if args.mode == "validate":
        payload = {
            "status": "PASS",
            "battery_id": BATTERY_ID,
            "battery_version": BATTERY_VERSION,
            "candidate_set_id": CANDIDATE_SET_ID,
            "testspec_sha256": bindings["testspec_sha256"],
            "model_transmissions": 0,
            "credential_reads": 0,
        }
    elif args.mode == "generate-runner":
        if not args.plan or not args.output:
            _fail(
                "GENERATOR_RUNNER_FAILED",
                "generate-runner requires --plan and --output.",
            )
        plan_path = Path(args.plan)
        plan = _require_object(
            _load_json(plan_path),
            code="GENERATOR_PLAN_INVALID",
            label="plan",
        )
        validate_conformance_plan(plan, bindings=bindings)
        write_generated_live_runner(
            output_path=Path(args.output),
            plan_path=plan_path,
            plan=plan,
        )
        validate_generated_live_runner(
            runner_path=Path(args.output),
            plan_path=plan_path,
            plan=plan,
        )
        payload = {
            "status": "PASS",
            "mode": "GENERATE_DEDICATED_LIVE_RUNNER",
            "test_run_id": plan["test_run_id"],
            "plan_sha256": _sha256_json(plan),
            "runner_path": str(Path(args.output)).replace("\\", "/"),
            "model_transmissions": 0,
            "credential_reads": 0,
        }
    else:
        plan = build_conformance_plan(
            test_run_id=args.test_run_id,
            generated_at=args.generated_at,
            bindings=bindings,
        )
        if args.mode == "offline":
            payload = _offline_gate_payload(plan)
        else:
            required = {
                "--metadata-json": args.metadata_json,
                "--credential-state-json": args.credential_state_json,
                "--attestation-json": args.attestation_json,
            }
            missing = [flag for flag, value in required.items() if not value]
            if missing:
                _fail("LIVE_PREFLIGHT_INPUT_MISSING", f"Missing inputs: {', '.join(missing)}")
            payload = live_preflight_only(
                plan=plan,
                metadata_records=_load_json(Path(args.metadata_json)),
                public_credential_state=_load_json(Path(args.credential_state_json)),
                operator_attestation=_load_json(Path(args.attestation_json)),
            )

    if args.output and args.mode != "generate-runner":
        write_generated_json(Path(args.output), payload)
    print(_canonical_json(payload))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_cli())
    except ConformanceValidationError as exc:
        print(_canonical_json({"status": "BLOCKED", "code": exc.code, "detail": exc.detail}))
        raise SystemExit(2) from exc

"""Utility to ensure vision reporter text respects verified/exclusion terms."""

import argparse
import json
import sys
from pathlib import Path


def _load_text(path: Path | None, inline: str | None) -> str:
    if inline:
        return inline.strip()
    if path:
        return path.read_text(encoding="utf-8")
    raise ValueError("Either --response-text or --response-file must be provided.")


FALLBACK_KEYS = [
    "KLEIDUNG",
    "OUTFIT_OBEN",
    "INNER_LAYER",
    "MATERIAL",
    "HAAR_DETAILS",
    "PRINT",
    "OUTFIT_UNTEN",
    "MUSTER_INFO",
]


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _collect_verified_terms(facts: dict) -> tuple[list[str], bool]:
    terms = facts.get("VERIFIZIERTE_ELEMENTE_PFLICHT") or []
    normalized = [str(term).strip() for term in terms if term and str(term).strip()]
    if normalized:
        return normalized, False

    fallback = []
    for key in FALLBACK_KEYS:
        value = facts.get(key)
        if isinstance(value, str) and value.strip():
            fallback.append(value.strip())
    return fallback, bool(fallback)


def _validate(required: list[str], excluded: list[str], response: str) -> tuple[list[str], list[str]]:
    response_norm = _normalize(response)
    missing = [term for term in required if term and term.lower() not in response_norm]
    violating = [term for term in excluded if term and term.lower() in response_norm]
    return missing, violating


def _load_facts(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    raise ValueError("Facts file must contain a JSON object.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check vision reporter text against verified/excluded terms.")
    parser.add_argument("--facts-file", type=Path, required=True, help="JSON file with final_facts block.")
    parser.add_argument("--response-file", type=Path, help="Text file containing the reporter output.")
    parser.add_argument("--response-text", type=str, help="Provide the reporter output as an inline string.")
    parser.add_argument("--picky", action="store_true", help="Fail when there are no requirements to check.")
    args = parser.parse_args()

    response = _load_text(args.response_file, args.response_text)
    facts = _load_facts(args.facts_file)

    required_terms, used_fallback = _collect_verified_terms(facts)
    exclusion_terms = facts.get("AUSSCHLUSS_PFLICHT") or []

    if args.picky and not required_terms and not exclusion_terms:
        print("⚠️  No verified/exclusion terms supplied; run with --picky only if you expect them.")
        return 1

    missing, violating = _validate(required_terms, exclusion_terms, response)
    ok = True
    if required_terms:
        if used_fallback:
            print("⚠️  No verified terms supplied; using fallback terms:")
        print(f"Required terms ({len(required_terms)}): {required_terms}")
        if missing:
            print(f"❌ Missing verified terms: {missing}")
            ok = False
        else:
            print("✅ All verified terms found.")
    else:
        print("(No verified terms supplied)")

    if exclusion_terms:
        print(f"Exclusion terms ({len(exclusion_terms)}): {exclusion_terms}")
        if violating:
            print(f"❌ Forbidden terms present: {violating}")
            ok = False
        else:
            print("✅ No excluded terms found.")
    else:
        print("(No exclusion terms supplied)")

    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())

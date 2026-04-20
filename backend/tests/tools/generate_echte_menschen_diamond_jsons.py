#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.data.database import get_db_context
from backend.services.vision.profiles import gemini_profile
from backend.services.vision.utils import get_mapped_portrait_facts
from backend.services.vision_service import vision_service

MATRIX_DIR = Path(r"c:\KI\Janus-Projekt\backend\tests\vision_matrix\Echte menschen")

REQ_KEYS = [
    "GESCHLECHT",
    "ALTER",
    "HAARFARBE",
    "FRISUR",
    "BART",
    "KOPFBDECKUNG",
    "BRILLE",
    "SCHMUCK",
    "OUTERWEAR",
    "KLEIDUNG",
    "LEGWEAR",
    "SCHUH_SATZ",
    "ZUBEHOER_SATZ",
    "POSE_SATZ",
    "AMBIENTE_SATZ",
    "VERIFIZIERTE_ELEMENTE_PFLICHT",
    "AUSSCHLUSS_PFLICHT",
]

TEXT_DEFAULTS = {
    "GESCHLECHT": "",
    "ALTER": "",
    "HAARFARBE": "nicht sichtbar",
    "FRISUR": "nicht sichtbar",
    "BART": "kein Bart",
    "KOPFBDECKUNG": "keine Kopfbedeckung",
    "BRILLE": "nicht sichtbar",
    "SCHMUCK": "nicht sichtbar",
    "OUTERWEAR": "nicht sichtbar",
    "KLEIDUNG": "nicht sichtbar",
    "LEGWEAR": "nicht sichtbar",
    "SCHUH_SATZ": "nicht sichtbar",
    "ZUBEHOER_SATZ": "nicht sichtbar",
    "POSE_SATZ": "Die Person ist auf dem Bild sichtbar.",
    "AMBIENTE_SATZ": "Innen- oder Außenaufnahme, genauer Ort nicht eindeutig.",
}


def _s(value: Any, default: str) -> str:
    text = str(value or "").strip()
    return text if text else default


def _norm_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    seen = set()
    for item in value:
        text = str(item or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _facts_to_expected(facts: Dict[str, Any]) -> Dict[str, Any]:
    expected: Dict[str, Any] = {
        "GESCHLECHT": _s(facts.get("GESCHLECHT"), TEXT_DEFAULTS["GESCHLECHT"]),
        "ALTER": _s(facts.get("ALTER"), TEXT_DEFAULTS["ALTER"]),
        "HAARFARBE": _s(facts.get("HAARFARBE"), TEXT_DEFAULTS["HAARFARBE"]),
        "FRISUR": _s(facts.get("FRISUR"), TEXT_DEFAULTS["FRISUR"]),
        "BART": _s(facts.get("BART"), TEXT_DEFAULTS["BART"]),
        "KOPFBDECKUNG": _s(
            facts.get("KOPFBDECKUNG") or facts.get("KOPF_BEDECKUNG"),
            TEXT_DEFAULTS["KOPFBDECKUNG"],
        ),
        "BRILLE": _s(facts.get("BRILLE"), TEXT_DEFAULTS["BRILLE"]),
        "SCHMUCK": _s(facts.get("SCHMUCK") or facts.get("HALSKMUCK"), TEXT_DEFAULTS["SCHMUCK"]),
        "OUTERWEAR": _s(facts.get("OUTERWEAR") or facts.get("OUTFIT_OBEN"), TEXT_DEFAULTS["OUTERWEAR"]),
        "KLEIDUNG": _s(facts.get("KLEIDUNG") or facts.get("OUTFIT_UNTEN"), TEXT_DEFAULTS["KLEIDUNG"]),
        "LEGWEAR": _s(facts.get("LEGWEAR"), TEXT_DEFAULTS["LEGWEAR"]),
        "SCHUH_SATZ": _s(facts.get("SCHUH_SATZ"), TEXT_DEFAULTS["SCHUH_SATZ"]),
        "ZUBEHOER_SATZ": _s(facts.get("ZUBEHOER_SATZ"), TEXT_DEFAULTS["ZUBEHOER_SATZ"]),
        "POSE_SATZ": _s(facts.get("POSE_SATZ"), TEXT_DEFAULTS["POSE_SATZ"]),
        "AMBIENTE_SATZ": _s(facts.get("AMBIENTE_SATZ"), TEXT_DEFAULTS["AMBIENTE_SATZ"]),
    }

    verified = _norm_list(facts.get("VERIFIZIERTE_ELEMENTE_PFLICHT"))
    if not verified:
        candidates = [
            expected["OUTERWEAR"],
            expected["KLEIDUNG"],
            expected["LEGWEAR"],
            expected["BRILLE"],
            expected["SCHMUCK"],
            expected["HAARFARBE"],
            expected["FRISUR"],
        ]
        filtered = []
        for c in candidates:
            cl = c.lower()
            if not c or c == "nicht sichtbar":
                continue
            if cl.startswith("kein ") or cl.startswith("keine "):
                continue
            filtered.append(c)
        verified = filtered[:7]

    exclusions = _norm_list(facts.get("AUSSCHLUSS_PFLICHT"))
    if exclusions:
        positives_blob = " ".join(
            [
                expected["BRILLE"],
                expected["SCHUH_SATZ"],
                expected["OUTERWEAR"],
                expected["KLEIDUNG"],
                expected["LEGWEAR"],
            ]
        ).lower()
        exclusions = [term for term in exclusions if term.lower() not in positives_blob]

    expected["VERIFIZIERTE_ELEMENTE_PFLICHT"] = verified
    expected["AUSSCHLUSS_PFLICHT"] = exclusions
    return expected


def _complete_existing(existing: Dict[str, Any], generated_expected: Dict[str, Any], image_idx: int) -> Dict[str, Any]:
    filename = f"{image_idx}.jpg"
    payload = existing if isinstance(existing, dict) else {}
    payload["filename"] = filename

    exp = payload.get("expected") if isinstance(payload.get("expected"), dict) else {}
    if not isinstance(exp, dict):
        exp = {}

    for key in REQ_KEYS:
        if key not in exp:
            exp[key] = generated_expected[key]

    # Replace placeholders generated from template bootstrapping.
    fillable_text_keys = [
        "GESCHLECHT",
        "ALTER",
        "HAARFARBE",
        "FRISUR",
        "BRILLE",
        "SCHMUCK",
        "OUTERWEAR",
        "KLEIDUNG",
        "LEGWEAR",
        "SCHUH_SATZ",
        "ZUBEHOER_SATZ",
        "POSE_SATZ",
        "AMBIENTE_SATZ",
    ]
    for key in fillable_text_keys:
        current = str(exp.get(key, "") or "").strip()
        current_l = current.lower()
        if (
            not current
            or current_l == "todo"
            or current_l.startswith("todo:")
            or current_l == "nicht sichtbar"
        ):
            candidate = str(generated_expected.get(key, "") or "").strip()
            if candidate:
                exp[key] = candidate

    for key, default in TEXT_DEFAULTS.items():
        exp[key] = _s(exp.get(key), generated_expected.get(key, default))

    exp["VERIFIZIERTE_ELEMENTE_PFLICHT"] = _norm_list(exp.get("VERIFIZIERTE_ELEMENTE_PFLICHT"))
    exp["AUSSCHLUSS_PFLICHT"] = _norm_list(exp.get("AUSSCHLUSS_PFLICHT"))

    if not exp["VERIFIZIERTE_ELEMENTE_PFLICHT"]:
        exp["VERIFIZIERTE_ELEMENTE_PFLICHT"] = list(generated_expected.get("VERIFIZIERTE_ELEMENTE_PFLICHT", []))
    if not exp["AUSSCHLUSS_PFLICHT"]:
        exp["AUSSCHLUSS_PFLICHT"] = list(generated_expected.get("AUSSCHLUSS_PFLICHT", []))

    positives_blob = " ".join(
        [
            exp.get("BRILLE", ""),
            exp.get("SCHUH_SATZ", ""),
            exp.get("OUTERWEAR", ""),
            exp.get("KLEIDUNG", ""),
            exp.get("LEGWEAR", ""),
        ]
    ).lower()
    exp["AUSSCHLUSS_PFLICHT"] = [
        term for term in exp["AUSSCHLUSS_PFLICHT"] if term.lower() not in positives_blob
    ]

    payload["expected"] = exp
    return payload


def _generate_facts(image_path: Path, db_session) -> Dict[str, Any]:
    image_bytes = image_path.read_bytes()
    local_result = vision_service.process_image(
        image_bytes,
        db_session,
        profile=gemini_profile,
        image_name=image_path.name,
    )
    return get_mapped_portrait_facts(
        local_result.get("feature_report", {}),
        local_result.get("context", {}),
        vision_mode="eval",
    )


def main() -> int:
    image_files = sorted(
        [p for p in MATRIX_DIR.glob("*.jpg") if p.stem.isdigit()],
        key=lambda p: int(p.stem),
    )

    created = 0
    updated = 0

    with get_db_context() as db:
        for image_path in image_files:
            idx = int(image_path.stem)
            json_path = image_path.with_suffix(".json")

            facts = _generate_facts(image_path, db)
            generated_expected = _facts_to_expected(facts)

            if json_path.exists():
                try:
                    existing = json.loads(json_path.read_text(encoding="utf-8-sig"))
                except Exception:
                    existing = {}
                payload = _complete_existing(existing, generated_expected, idx)
                json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                updated += 1
            else:
                payload = {
                    "filename": f"{idx}.jpg",
                    "expected": generated_expected,
                }
                json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                created += 1

    print(f"updated={updated} created={created} total={len(image_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

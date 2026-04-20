"""Lightweight generator for automated smoke reports on a fixed set of real images."""
import asyncio
import argparse
import base64
import json
import keyring
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.data.database import get_db_context
from backend.services.vision_helper import analyze_image_with_cloud
from backend.services.vision_service import vision_service
from backend.services.vision.utils import fuse_vision_results
from backend.services.chat_orchestrator import (
    _USE_FULL_FACTS_IN_LIVE_REPORTER,
    _apply_plugin_confidence_gates,
    _build_enriched_reporter_facts,
    _build_live_slot_fact_block,
)

logger = logging.getLogger("vision_smoke_check")

DEFAULT_REQUIRED_FACTS = ["GESCHLECHT", "TEINT", "AUGEN", "HAARFARBE", "FRISUR_SATZ"]
LIVE_READY_STRICT_SLOTS = ["ALTER_GESCHLECHT_SATZ", "TEINT", "AUGEN", "HAARFARBE", "FRISUR_SATZ"]
LIVE_READY_CORE_SLOTS = ["AUGEN", "HAARFARBE", "FRISUR_SATZ"]


def _normalize_text(value: Any) -> str:
    text = str(value or "").strip()
    if any(token in text for token in ["Ã", "â", "�"]):
        try:
            text = text.encode("latin1").decode("utf-8")
        except Exception:
            pass
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _stringify_slot(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if str(v).strip())
    return str(value or "")


def _frisur_tags(value: str) -> List[str]:
    text = _normalize_text(value)
    tag_map = {
        "kurz": ["kurz", "pixie", "buzz"],
        "schulterlang": ["schulterlang"],
        "lang": [" lang", "sehr lang", "halblang"],
        "glatt": ["glatt"],
        "lockig": ["lockig", "curly", "gelockt"],
        "wellig": ["wellig", "wavy"],
        "pony": ["pony"],
        "seitenscheitel": ["seitenscheitel", "seitlich gescheitelt"],
        "mittelscheitel": ["mittelscheitel"],
        "dutt": ["dutt"],
        "hochgesteckt": ["hochgesteckt", "hochsteck", "nach hinten gebunden", "zuruckgebunden", "zurückgebunden"],
    }
    tags: List[str] = []
    padded = f" {text} "
    for tag, needles in tag_map.items():
        if any(needle in padded for needle in needles):
            tags.append(tag)
    return tags


def _canonical_slot_value(slot: str, value: Any) -> str:
    text = _normalize_text(_stringify_slot(value))
    if slot == "AUGEN":
        if "nicht erkennbar" in text or "not visible" in text or "occluded" in text:
            return "nicht erkennbar"
        if "geschlossen" in text or "closed" in text:
            return "geschlossen"
        for color in ["blau", "braun", "grun", "grün", "grau", "gruen"]:
            if color in text:
                return "grün" if color in {"grun", "gruen", "grün"} else color
        return ""
    if slot == "HAARFARBE":
        color_map = [
            ("hellbraun", ["hellbraun"]),
            ("blond", ["blond"]),
            ("braun", ["braun"]),
            ("schwarz", ["schwarz"]),
            ("grau", ["grau", "gray", "grey", "silber", "silver", "weiss", "weiß"]),
            ("rot", ["rot", "red"]),
        ]
        for canonical, needles in color_map:
            if any(needle in text for needle in needles):
                return canonical
        return ""
    if slot in {"FRISUR", "FRISUR_SATZ"}:
        return "|".join(sorted(_frisur_tags(text)))
    return text


def _build_live_ready_flags(
    effective_facts: Dict[str, Any],
    plugin_gate: Dict[str, Any],
    maturity_entries: List[Dict[str, Any]],
    truth_matches: Dict[str, bool],
) -> Dict[str, Any]:
    confirmed = set(plugin_gate.get("confirmed", []) or [])
    watch = set(plugin_gate.get("watch", []) or [])
    withheld = set((plugin_gate.get("withheld", {}) or {}).keys())
    maturity_map: Dict[str, str] = {}
    for entry in maturity_entries or []:
        slot = str(entry.get("slot", "") or "").strip()
        state = str(entry.get("maturity", "unknown") or "unknown").strip().lower()
        if slot:
            maturity_map[slot] = state

    slot_flags: Dict[str, Any] = {}
    for slot in LIVE_READY_STRICT_SLOTS:
        has_value = bool(str(effective_facts.get(slot, "") or "").strip())
        gate_ok = slot in confirmed and slot not in watch and slot not in withheld
        maturity_ok = maturity_map.get(slot, "unknown") == "stable"
        truth_ok = True if not truth_matches else bool(truth_matches.get(slot, False))
        slot_flags[slot] = {
            "ready": bool(has_value and gate_ok and maturity_ok and truth_ok),
            "value_present": has_value,
            "gate_confirmed": gate_ok,
            "maturity_stable": maturity_ok,
            "truth_match": truth_ok,
        }

    strict_ready = all(slot_flags.get(slot, {}).get("ready", False) for slot in LIVE_READY_STRICT_SLOTS)
    core_ready = all(slot_flags.get(slot, {}).get("ready", False) for slot in LIVE_READY_CORE_SLOTS)
    return {
        "core_ready": core_ready,
        "strict_ready": strict_ready,
        "slots": slot_flags,
    }


def _extract_length_tag(tags: set[str]) -> str:
    for token in ("kurz", "schulterlang", "lang"):
        if token in tags:
            return token
    return ""


def _compare_with_truth(mapped: Dict[str, Any], truth_entry: Dict[str, Any]) -> (Dict[str, bool], List[Dict[str, Any]]):
    matches: Dict[str, bool] = {}
    mismatches: List[Dict[str, Any]] = []
    for slot, expected in (truth_entry or {}).items():
        expected_text = _canonical_slot_value(slot, expected)
        actual = mapped.get(slot)
        actual_text = _canonical_slot_value(slot, actual)
        if slot in {"FRISUR", "FRISUR_SATZ"}:
            expected_tags = {tag for tag in expected_text.split("|") if tag}
            actual_tags = {tag for tag in actual_text.split("|") if tag}
            overlap = expected_tags.intersection(actual_tags)
            expected_length = _extract_length_tag(expected_tags)
            actual_length = _extract_length_tag(actual_tags)
            length_match = (not expected_length) or (expected_length == actual_length)
            match = bool(expected_tags and actual_tags and length_match and len(overlap) >= 2)
        else:
            match = bool(expected_text and actual_text and expected_text == actual_text)
        matches[slot] = match
        if not match:
            mismatches.append({
                "slot": slot,
                "expected": _stringify_slot(expected),
                "actual": actual,
            })
    return matches, mismatches


def _fetch_cloud_result(image_bytes: bytes, provider: str, api_key: Optional[str]) -> Dict[str, Any]:
    if not api_key:
        return {}
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    try:
        return asyncio.run(analyze_image_with_cloud(image_b64, provider, api_key)) or {}
    except Exception as exc:
        logger.warning("Cloud-Hybrid-Call fehlgeschlagen (%s): %s", provider, exc)
        return {}


def process_image(
    image_path: Path,
    db_session,
    truth_entry: Dict[str, Any] | None,
    *,
    provider: str,
    api_key: Optional[str],
    use_cloud_api: bool,
    use_image_name_hint: bool,
) -> Dict[str, Any]:
    facts = {"image_name": image_path.name}
    image_bytes = image_path.read_bytes()
    image_name = image_path.name if use_image_name_hint else ""
    local_result = vision_service.process_image(
        image_bytes,
        db_session,
        image_name=image_name,
    )
    cloud_result = local_result.get("cloud_vision_result", {}) or {"objects": []}
    if use_cloud_api:
        cloud_api_result = _fetch_cloud_result(image_bytes, provider, api_key)
        if cloud_api_result:
            cloud_result = cloud_api_result

    mapped = fuse_vision_results(local_result, cloud_result, vision_mode="live")

    feature_report = local_result.get("feature_report", {}) or {}
    reporter_facts = _build_enriched_reporter_facts(mapped, feature_report, cloud_result)
    reporter_facts, plugin_gate, maturity_entries = _apply_plugin_confidence_gates(
        reporter_facts,
        feature_report,
        mapped,
        cloud_result,
    )

    effective_facts = (
        reporter_facts if _USE_FULL_FACTS_IN_LIVE_REPORTER else _build_live_slot_fact_block(reporter_facts)
    )

    facts.update({slot: effective_facts.get(slot) for slot in DEFAULT_REQUIRED_FACTS})
    facts["ALTER_GESCHLECHT_SATZ"] = effective_facts.get("ALTER_GESCHLECHT_SATZ")
    facts["validations"] = mapped.get("VALIDATION_FLAGS", [])
    facts["source_of_truth"] = mapped.get("SOURCE_OF_TRUTH", {})
    facts["brief_text"] = effective_facts.get("POSE_SATZ", "") or effective_facts.get("AMBIENTE_SATZ", "")
    facts["mapped_snapshot"] = {slot: mapped.get(slot) for slot in DEFAULT_REQUIRED_FACTS}
    facts["plugin_gate"] = plugin_gate
    facts["plugin_maturity"] = maturity_entries

    truth_matches: Dict[str, bool] = {}
    if truth_entry:
        matches, mismatches = _compare_with_truth(effective_facts, truth_entry)
        truth_matches = matches
        facts["truth_comparison"] = matches
        facts["truth_mismatches"] = mismatches
        facts["truth_match_count"] = sum(1 for matched in matches.values() if matched)
        facts["truth_total_slots"] = len(matches)

    facts["live_ready"] = _build_live_ready_flags(effective_facts, plugin_gate, maturity_entries, truth_matches)
    return facts


def summarize(results: List[Dict[str, str]]) -> None:
    header = "Bildname" + " " * 4 + "Status" + " " * 4 + "Schlüsselwerte"
    print(header)
    print("-" * len(header))
    for entry in results:
        status = "PASS" if all(entry.get(slot) for slot in DEFAULT_REQUIRED_FACTS) else "FAIL"
        values = ", ".join(f"{slot}={entry.get(slot) or '??'}" for slot in DEFAULT_REQUIRED_FACTS)
        print(f"{entry['image_name']:<20} {status:<5} {values}")


def _with_percent(numerator: int, denominator: int) -> Dict[str, Any]:
    pct = (numerator / denominator * 100.0) if denominator else 0.0
    return {
        "count": int(numerator),
        "total": int(denominator),
        "percent": round(pct, 2),
    }


def _build_aggregate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    slot_stats: Dict[str, Dict[str, int]] = {}
    truth_images = 0
    global_mismatches: List[Dict[str, Any]] = []
    slot_maturity: Dict[str, Dict[str, int]] = {}
    gate_state: Dict[str, Dict[str, int]] = {}
    live_ready_core_count = 0
    live_ready_strict_count = 0
    live_ready_core_images: List[str] = []
    live_ready_strict_images: List[str] = []

    for entry in results:
        comparison = entry.get("truth_comparison", {})
        if comparison:
            truth_images += 1
            for slot, matched in comparison.items():
                stats = slot_stats.setdefault(slot, {"matched": 0, "total": 0})
                stats["total"] += 1
                if matched:
                    stats["matched"] += 1

        for mismatch in entry.get("truth_mismatches", []):
            global_mismatches.append({"image": entry["image_name"], **mismatch})

        for maturity in entry.get("plugin_maturity", []) or []:
            slot = str(maturity.get("slot", "") or "").strip()
            if not slot:
                continue
            state = str(maturity.get("maturity", "unknown") or "unknown")
            slot_maturity.setdefault(slot, {}).setdefault(state, 0)
            slot_maturity[slot][state] += 1

        plugin_gate = entry.get("plugin_gate", {}) or {}
        for slot in plugin_gate.get("confirmed", []) or []:
            gate_state.setdefault(slot, {}).setdefault("confirmed", 0)
            gate_state[slot]["confirmed"] += 1
        for slot in plugin_gate.get("watch", []) or []:
            gate_state.setdefault(slot, {}).setdefault("watch", 0)
            gate_state[slot]["watch"] += 1
        for slot in (plugin_gate.get("withheld", {}) or {}).keys():
            gate_state.setdefault(slot, {}).setdefault("withheld", 0)
            gate_state[slot]["withheld"] += 1

        live_ready = entry.get("live_ready", {}) or {}
        if live_ready.get("core_ready"):
            live_ready_core_count += 1
            live_ready_core_images.append(str(entry.get("image_name", "")))
        if live_ready.get("strict_ready"):
            live_ready_strict_count += 1
            live_ready_strict_images.append(str(entry.get("image_name", "")))

    slot_accuracy = {
        slot: _with_percent(stats.get("matched", 0), stats.get("total", 0))
        for slot, stats in slot_stats.items()
    }

    plugin_gate_metrics: Dict[str, Dict[str, Any]] = {}
    plugin_maturity_metrics: Dict[str, Dict[str, Any]] = {}
    total_images = len(results)

    all_metric_slots = sorted(set(slot_maturity.keys()) | set(gate_state.keys()))
    for slot in all_metric_slots:
        gate_counts = gate_state.get(slot, {})
        confirmed = int(gate_counts.get("confirmed", 0))
        watch = int(gate_counts.get("watch", 0))
        withheld = int(gate_counts.get("withheld", 0))
        plugin_gate_metrics[slot] = {
            "confirmed": _with_percent(confirmed, total_images),
            "watch": _with_percent(watch, total_images),
            "withheld": _with_percent(withheld, total_images),
        }

        maturity_counts = slot_maturity.get(slot, {})
        stable = int(maturity_counts.get("stable", 0))
        watch_m = int(maturity_counts.get("watch", 0))
        unstable = int(maturity_counts.get("unstable", 0))
        unknown = int(maturity_counts.get("unknown", 0))
        plugin_maturity_metrics[slot] = {
            "stable": _with_percent(stable, total_images),
            "watch": _with_percent(watch_m, total_images),
            "unstable": _with_percent(unstable, total_images),
            "unknown": _with_percent(unknown, total_images),
        }

    focus_slots = ["ALTER_GESCHLECHT_SATZ", "TEINT", "AUGEN", "HAARFARBE", "FRISUR_SATZ"]
    aggregate_focus = {
        slot: {
            "accuracy": slot_accuracy.get(slot, _with_percent(0, 0)),
            "gate": plugin_gate_metrics.get(
                slot,
                {
                    "confirmed": _with_percent(0, total_images),
                    "watch": _with_percent(0, total_images),
                    "withheld": _with_percent(0, total_images),
                },
            ),
            "maturity": plugin_maturity_metrics.get(
                slot,
                {
                    "stable": _with_percent(0, total_images),
                    "watch": _with_percent(0, total_images),
                    "unstable": _with_percent(0, total_images),
                    "unknown": _with_percent(0, total_images),
                },
            ),
        }
        for slot in focus_slots
    }

    return {
        "total_images": total_images,
        "truth_images": truth_images,
        "slot_accuracy": slot_accuracy,
        "aggregate_focus": aggregate_focus,
        "live_ready": {
            "criteria": {
                "core_slots": LIVE_READY_CORE_SLOTS,
                "strict_slots": LIVE_READY_STRICT_SLOTS,
                "rules": [
                    "slot value present",
                    "plugin gate confirmed (not watch/withheld)",
                    "plugin maturity stable",
                    "truth match required when truth data exists",
                ],
            },
            "core": {
                "ready": _with_percent(live_ready_core_count, total_images),
                "images": live_ready_core_images,
            },
            "strict": {
                "ready": _with_percent(live_ready_strict_count, total_images),
                "images": live_ready_strict_images,
            },
        },
        "mismatches": global_mismatches,
        "plugin_gate": plugin_gate_metrics,
        "plugin_maturity": plugin_maturity_metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check für generische Vision-Erkennung")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "Bilder",
        help="Verzeichnis mit den echten JPG-Bildern",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./vision_smoke_report.json"),
        help="JSON-Datei für das automatisierte Ergebnis"
    )
    parser.add_argument(
        "--required-slots",
        type=str,
        default=",".join(DEFAULT_REQUIRED_FACTS),
        help="Komma-separierte Fakten, die im Smoke-Test vorhanden sein sollten",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximale Anzahl zu prüfender Bilder",
    )
    parser.add_argument(
        "--truth",
        type=Path,
        default=None,
        help="JSON-Datei mit ground-truth Fakten pro Bild (optional)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="gemini",
        help="Provider für Cloud-Hybrid-Parität (gemini/openai)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Optionaler API-Key; ohne Angabe wird keyring genutzt",
    )
    parser.add_argument(
        "--disable-cloud-api",
        action="store_true",
        help="Cloud-Hybrid im Smoke deaktivieren (nur lokal/fallback)",
    )
    parser.add_argument(
        "--use-image-name-hint",
        action="store_true",
        help="Dateinamen als image_name an Vision-Service geben (standardmaessig AUS für Live-Parität)",
    )
    args = parser.parse_args()

    if not args.input_dir.exists():
        logger.error("Input-Verzeichnis %s existiert nicht", args.input_dir)
        return 1

    required_slots = [slot.strip() for slot in args.required_slots.split(",") if slot.strip()]
    results = []
    truth_map: Dict[str, Dict[str, Any]] = {}
    if args.truth:
        try:
            truth_map = json.loads(args.truth.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("Fehler beim Laden der Ground-Truth-Datei: %s", e)
            return 1

    provider = str(args.provider or "gemini").strip().lower()
    api_key = args.api_key or keyring.get_password("Janus-Projekt", provider)
    use_cloud_api = not args.disable_cloud_api
    if use_cloud_api and not api_key:
        logger.warning("Kein API-Key gefunden - Cloud-Hybrid wird fuer Smoke deaktiviert.")
        use_cloud_api = False

    for image_path in sorted(args.input_dir.glob("*.jpg"))[: args.limit]:
        with get_db_context() as db_session:
            entry = process_image(
                image_path,
                db_session,
                truth_map.get(image_path.name),
                provider=provider,
                api_key=api_key,
                use_cloud_api=use_cloud_api,
                use_image_name_hint=bool(args.use_image_name_hint),
            )
            entry["status"] = "PASS" if all(entry.get(slot) for slot in required_slots) else "FAIL"
            results.append(entry)

    summarize(results)
    aggregate = _build_aggregate_summary(results)
    report_payload = {
        "results": results,
        "aggregate": aggregate,
    }
    args.output.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nReport gespeichert: {args.output}")
    if aggregate["truth_images"]:
        print("\n--- Ground-Truth Verification ---")
        print(f"Bilder mit Truth-Data: {aggregate['truth_images']}/{len(results)}")
        for slot, stats in aggregate.get("slot_accuracy", {}).items():
            print(f"{slot}: {stats['count']}/{stats['total']} ({stats['percent']:.0f}%)")
        if aggregate.get("mismatches"):
            print("\nMismatches (max. 10):")
            for mismatch in aggregate["mismatches"][:10]:
                print(
                    f"{mismatch['image']} - {mismatch['slot']}: erwartet='{mismatch['expected']}', gefunden='{mismatch['actual']}'"
                )

    focus_slots = ["ALTER_GESCHLECHT_SATZ", "TEINT", "AUGEN", "HAARFARBE", "FRISUR_SATZ"]
    print("\n--- Plugin Gate/Maturity Summary ---")
    for slot in focus_slots:
        maturity_stats = aggregate.get("plugin_maturity", {}).get(slot, {})
        gate_stats = aggregate.get("plugin_gate", {}).get(slot, {})
        print(
            f"{slot}: maturity={maturity_stats or {'none': 0}}, gate={gate_stats or {'none': 0}}"
        )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())

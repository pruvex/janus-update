from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
from typing import Any, Dict, List, Tuple, Optional

from backend.services.vision.utils import clean_for_chat
from backend.services.vision_service import vision_service

logger = logging.getLogger("janus_backend")

_POSE_CONFIDENCE_THRESHOLD = float(os.getenv("JANUS_LIVE_POSE_THRESHOLD", "0.18"))
_AMBIENTE_CONFIDENCE_THRESHOLD = float(os.getenv("JANUS_LIVE_AMBIENTE_THRESHOLD", "0.20"))

_PLUGIN_CONFIDENCE_GATES = [
    {
        "plugin": "AgeGender",
        "slot": "ALTER_GESCHLECHT_SATZ",
        "category": "ALTER",
        "min_score": 0.08,
        "stable_score": 0.10,
        "cloud_tokens": [],
    },
    {
        "plugin": "SkinEye",
        "slot": "TEINT",
        "category": "TEINT",
        "min_score": 0.10,
        "stable_score": 0.14,
        "cloud_tokens": ["skin", "teint", "complexion"],
    },
    {
        "plugin": "SkinEye",
        "slot": "AUGEN",
        "category": "AUGEN",
        "min_score": 0.08,
        "stable_score": 0.11,
        "cloud_tokens": ["eye", "eyes", "gaze"],
    },
    {
        "plugin": "Hair",
        "slot": "HAARFARBE",
        "category": "HAARFARBE",
        "min_score": 0.08,
        "stable_score": 0.11,
        "cloud_tokens": ["hair", "hairstyle", "fringe"],
    },
    {
        "plugin": "Hair",
        "slot": "FRISUR_SATZ",
        "category": "FRISUR",
        "min_score": 0.10,
        "stable_score": 0.14,
        "cloud_tokens": ["hair", "hairstyle", "fringe", "bangs"],
    },
    {
        "plugin": "Outfit",
        "slot": "OUTFIT_OBEN",
        "category": "OUTFIT_OBEN",
        "min_score": 0.12,
        "stable_score": 0.17,
        "cloud_tokens": ["shirt", "jacket", "sweater", "coat", "hoodie", "top", "outfit", "clothing"],
    },
    {
        "plugin": "Outfit",
        "slot": "OUTFIT_UNTEN",
        "category": "OUTFIT_UNTEN",
        "min_score": 0.12,
        "stable_score": 0.17,
        "cloud_tokens": ["pants", "trousers", "jeans", "skirt", "bottom", "outfit", "clothing"],
    },
    {
        "plugin": "Pose",
        "slot": "POSE_SATZ",
        "category": "POSE",
        "min_score": 0.10,
        "stable_score": 0.15,
        "cloud_tokens": ["standing", "sitting", "walking", "leaning", "pose", "smile", "portrait"],
        "require_cloud": True,
    },
    {
        "plugin": "Ambiente",
        "slot": "AMBIENTE_SATZ",
        "category": "AMBIENTE",
        "min_score": 0.12,
        "stable_score": 0.20,
        "cloud_tokens": ["indoor", "outdoor", "street", "park", "room", "interior", "wall", "cabinet", "furniture", "window"],
        "require_cloud": True,
    },
]


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _extract_cloud_object_labels(cloud_result: Dict[str, Any]) -> List[str]:
    if not isinstance(cloud_result, dict):
        return []
    objects = cloud_result.get("objects", [])
    if isinstance(objects, dict):
        objects = [objects]
    labels: List[str] = []
    for item in objects if isinstance(objects, list) else []:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "") or "").strip().lower()
        if label:
            labels.append(label)
    return labels


def _extract_cloud_text_blob(cloud_result: Dict[str, Any]) -> str:
    if not isinstance(cloud_result, dict):
        return ""
    parts: List[str] = []
    for key in ["object_profile", "description", "scene", "summary"]:
        value = cloud_result.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip().lower())
    try:
        parts.append(json.dumps(cloud_result, ensure_ascii=False, default=str).lower())
    except Exception:
        pass
    return " ".join(parts)


def _build_enriched_reporter_facts(
    final_facts: Dict[str, Any],
    feature_report: Dict[str, Any],
    cloud_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Conservative enrichment for live reporter text from plugin/cloud signals only."""
    facts = dict(final_facts or {})
    report = feature_report if isinstance(feature_report, dict) else {}

    if not str(facts.get("AUGEN", "") or "").strip():
        eye_items = report.get("AUGEN", []) or []
        if isinstance(eye_items, list) and eye_items:
            best_eye = max(
                (item for item in eye_items if isinstance(item, dict)),
                key=lambda x: _safe_float(x.get("score", 0.0)),
                default=None,
            )
            if best_eye:
                eye_label = str(best_eye.get("label", "") or "").lower()
                eye_score = _safe_float(best_eye.get("score", 0.0))
                if eye_score >= 0.10:
                    if "green" in eye_label:
                        facts["AUGEN"] = "grün"
                    elif "blue" in eye_label:
                        facts["AUGEN"] = "blau"
                    elif "brown" in eye_label:
                        facts["AUGEN"] = "braun"

    if not str(facts.get("HAARFARBE", "") or "").strip():
        hair_color_items = report.get("HAARFARBE", []) or []
        if isinstance(hair_color_items, list) and hair_color_items:
            best_hair_color = max(
                (item for item in hair_color_items if isinstance(item, dict)),
                key=lambda x: _safe_float(x.get("score", 0.0)),
                default=None,
            )
            if best_hair_color and _safe_float(best_hair_color.get("score", 0.0)) >= 0.08:
                hair_color_label = str(best_hair_color.get("label", "") or "").lower()
                if "grey" in hair_color_label or "gray" in hair_color_label or "silver" in hair_color_label:
                    facts["HAARFARBE"] = "graue Haare"
                elif "black" in hair_color_label:
                    facts["HAARFARBE"] = "schwarze Haare"
                elif "brown" in hair_color_label:
                    facts["HAARFARBE"] = "braune Haare"
                elif "blonde" in hair_color_label:
                    facts["HAARFARBE"] = "blonde Haare"

    if not str(facts.get("FRISUR_SATZ", "") or "").strip():
        hair_items = (report.get("HAAR_STRUKTUR", []) or []) + (report.get("FRISUR", []) or [])
        if isinstance(hair_items, list) and hair_items:
            best_hair = max(
                (item for item in hair_items if isinstance(item, dict)),
                key=lambda x: _safe_float(x.get("score", 0.0)),
                default=None,
            )
            if best_hair and _safe_float(best_hair.get("score", 0.0)) >= 0.12:
                hair_label = str(best_hair.get("label", "") or "").strip()
                if hair_label:
                    hair_label_l = hair_label.lower()
                    if "shoulder" in hair_label_l:
                        facts["FRISUR_SATZ"] = "Die Haare sind schulterlang."
                    elif "short" in hair_label_l:
                        facts["FRISUR_SATZ"] = "Die Haare sind eher kurz."
                    elif "curly" in hair_label_l or "curls" in hair_label_l:
                        facts["FRISUR_SATZ"] = "Die Haare wirken lockig."
                    elif "wavy" in hair_label_l:
                        facts["FRISUR_SATZ"] = "Die Haare wirken wellig."
                    else:
                        facts["FRISUR_SATZ"] = f"Die Haare wirken {hair_label}."

    cloud_labels = _extract_cloud_object_labels(cloud_result)
    cloud_blob = _extract_cloud_text_blob(cloud_result)
    has_indoor_signal = any(
        token in label
        for label in cloud_labels
        for token in ["indoor", "living room", "room", "wall", "interior", "cabinet", "cupboard", "furniture"]
    ) or any(token in cloud_blob for token in ["indoor", "living room", "interior", "room", "cabinet", "cupboard", "furniture", "wall"])
    has_cabinet_signal = any(
        any(token in label for token in ["cabinet", "cupboard", "wall cabinet", "hutch"]) for label in cloud_labels
    ) or any(token in cloud_blob for token in ["cabinet", "cupboard", "wall cabinet", "hutch", "hängeschrank", "haengeschrank"])

    if not str(facts.get("AMBIENTE_SATZ", "") or "").strip() and has_indoor_signal:
        ambience = "Die Person befindet sich in einem hellen Innenraum"
        if has_cabinet_signal:
            ambience += "; im Hintergrund ist ein Hängeschrank erkennbar"
        facts["AMBIENTE_SATZ"] = f"{ambience}."

    return facts


def _max_feature_score(feature_report: Dict[str, Any], categories: List[str]) -> float:
    if not isinstance(feature_report, dict):
        return 0.0
    best = 0.0
    for category in categories:
        items = feature_report.get(category, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            best = max(best, _safe_float(item.get("score", 0.0)))
    return best


def _cloud_has_evidence(cloud_labels: List[str], cloud_blob: str, tokens: List[str]) -> bool:
    if not tokens:
        return False
    for token in tokens:
        token_l = str(token or "").strip().lower()
        if not token_l:
            continue
        if token_l in cloud_blob:
            return True
        if any(token_l in label for label in cloud_labels):
            return True
    return False


def _apply_core_first_reporter_policy(
    reporter_facts: Dict[str, Any],
    feature_report: Dict[str, Any],
    cloud_result: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Prioritize person core slots and withhold weak scene claims in live mode."""
    facts = dict(reporter_facts or {})
    report = feature_report if isinstance(feature_report, dict) else {}
    cloud_labels = _extract_cloud_object_labels(cloud_result)
    cloud_blob = _extract_cloud_text_blob(cloud_result)

    slot_debug: Dict[str, Any] = {"confirmed": [], "withheld": {}}
    core_slots = [
        "ALTER_GESCHLECHT_SATZ",
        "TEINT",
        "AUGEN",
        "HAARFARBE",
        "FRISUR_SATZ",
    ]
    for slot in core_slots:
        value = str(facts.get(slot, "") or "").strip()
        if value:
            slot_debug["confirmed"].append(slot)
        else:
            slot_debug["withheld"][slot] = "missing"

    pose_tokens = ["standing", "sitting", "walking", "leaning", "kneeling", "pose", "smile", "portrait"]
    pose_score = _max_feature_score(report, ["POSE"])
    pose_has_cloud = _cloud_has_evidence(cloud_labels, cloud_blob, pose_tokens)
    pose_text = str(facts.get("POSE_SATZ", "") or "").strip()
    if pose_text:
        if pose_score >= _POSE_CONFIDENCE_THRESHOLD and pose_has_cloud:
            slot_debug["confirmed"].append("POSE_SATZ")
        else:
            facts["POSE_SATZ"] = ""
            slot_debug["withheld"]["POSE_SATZ"] = f"score={pose_score:.3f}, cloud={pose_has_cloud}"

    environment_tokens = [
        "indoor",
        "outdoor",
        "street",
        "park",
        "city",
        "room",
        "interior",
        "wall",
        "cabinet",
        "furniture",
        "window",
    ]
    ambiente_score = _max_feature_score(report, ["AMBIENTE"])
    ambiente_has_cloud = _cloud_has_evidence(cloud_labels, cloud_blob, environment_tokens)
    ambiente_text = str(facts.get("AMBIENTE_SATZ", "") or "").strip()
    if ambiente_text:
        if ambiente_score >= _AMBIENTE_CONFIDENCE_THRESHOLD and ambiente_has_cloud:
            slot_debug["confirmed"].append("AMBIENTE_SATZ")
        else:
            facts["AMBIENTE_SATZ"] = ""
            slot_debug["withheld"]["AMBIENTE_SATZ"] = f"score={ambiente_score:.3f}, cloud={ambiente_has_cloud}"

    return facts, slot_debug


def _get_top_feature_label(feature_report: Dict[str, Any], category: str) -> Tuple[str, float]:
    if not isinstance(feature_report, dict):
        return "", 0.0
    items = feature_report.get(category, [])
    best_label = ""
    best_score = 0.0
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            score = _safe_float(item.get("score", 0.0))
            if score > best_score and item.get("label"):
                best_score = score
                best_label = str(item.get("label", "") or "")
    return best_label, best_score


def _build_clip_verified_elements(feature_report: Dict[str, Any], final_facts: Dict[str, Any]) -> List[str]:
    existing = [str(elem).strip() for elem in (final_facts.get("VERIFIZIERTE_ELEMENTE_PFLICHT", []) or []) if str(elem or "").strip()]
    clones = existing[:]

    def _maybe_add_slot(slot: str, template: str) -> bool:
        value = clean_for_chat(final_facts.get(slot, ""))
        if not value:
            return False
        text = template.format(value)
        if text not in clones:
            clones.append(text)
        return True

    def _maybe_add(category: str, template: str, min_score: float) -> None:
        label, score = _get_top_feature_label(feature_report, category)
        if not label or score < min_score:
            return
        text = template.format(clean_for_chat(label))
        if text not in clones:
            clones.append(text)

    has_hair = _maybe_add_slot("HAARFARBE", "Haarfarbe: {}")
    has_eyes = _maybe_add_slot("AUGEN", "Augen: {}")
    has_teint = _maybe_add_slot("TEINT", "Teint: {}")
    has_frisur = _maybe_add_slot("FRISUR", "Frisur: {}")

    if not has_hair:
        _maybe_add("HAARFARBE", "Haarfarbe: {}", 0.08)
    if not has_eyes:
        _maybe_add("AUGEN", "Augen: {}", 0.11)
    if not has_teint:
        _maybe_add("TEINT", "Teint: {}", 0.10)
    if not has_frisur:
        _maybe_add("FRISUR", "Frisur: {}", 0.10)
    return clones


def _build_plugin_maturity_entries(
    feature_report: Dict[str, Any],
    final_facts: Dict[str, Any],
    cloud_result: Dict[str, Any],
) -> List[Dict[str, Any]]:
    report = feature_report if isinstance(feature_report, dict) else {}
    cloud_labels = _extract_cloud_object_labels(cloud_result)
    cloud_blob = _extract_cloud_text_blob(cloud_result)
    entries: List[Dict[str, Any]] = []

    for gate in _PLUGIN_CONFIDENCE_GATES:
        label, score = _get_top_feature_label(report, gate["category"])
        slot_value = clean_for_chat(final_facts.get(gate["slot"], ""))
        has_cloud = _cloud_has_evidence(
            cloud_labels,
            cloud_blob,
            gate.get("cloud_tokens", []),
        )
        require_cloud = bool(gate.get("require_cloud"))
        maturity = "unstable"
        if score >= float(gate.get("stable_score", 0.0)) and (not require_cloud or has_cloud):
            maturity = "stable"
        elif score >= float(gate.get("min_score", 0.0)):
            maturity = "watch"

        entries.append(
            {
                "plugin": gate["plugin"],
                "slot": gate["slot"],
                "label": clean_for_chat(label) or "<none>",
                "score": float(score),
                "cloud": has_cloud,
                "maturity": maturity,
                "slot_value": slot_value or "<none>",
                "stable_threshold": float(gate.get("stable_score", 0.0)),
                "min_threshold": float(gate.get("min_score", 0.0)),
                "require_cloud": require_cloud,
            }
        )

    return entries


def _apply_plugin_confidence_gates(
    reporter_facts: Dict[str, Any],
    feature_report: Dict[str, Any],
    final_facts: Dict[str, Any],
    cloud_result: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    maturity_entries = _build_plugin_maturity_entries(feature_report, final_facts, cloud_result)
    facts = dict(reporter_facts or {})
    gate_debug = {"confirmed": [], "watch": [], "withheld": {}}

    for entry in maturity_entries:
        slot = entry["slot"]
        slot_value = str(facts.get(slot, "") or "").strip()
        final_slot_value = str(final_facts.get(slot, "") or "").strip()
        if not slot_value and final_slot_value:
            facts[slot] = final_slot_value
            slot_value = final_slot_value
        if not slot_value:
            continue
        if entry["maturity"] == "stable":
            gate_debug["confirmed"].append(slot)
            continue
        if entry["maturity"] == "watch":
            gate_debug["watch"].append(slot)
            continue
        if final_slot_value:
            facts[slot] = final_slot_value
            gate_debug["watch"].append(slot)
            continue
        facts[slot] = ""
        gate_debug["withheld"][slot] = f"score={entry['score']:.3f}, cloud={entry['cloud']}, require_cloud={entry.get('require_cloud', False)}"

    return facts, gate_debug, maturity_entries


def _build_live_slot_fact_block(final_facts: Dict[str, Any]) -> Dict[str, Any]:
    """Return a conflict-minimized slot payload for live unknown portrait generation."""
    if not isinstance(final_facts, dict):
        return {}

    slot_keys = [
        "ALTER_GESCHLECHT_SATZ",
        "TEINT",
        "HAARFARBE",
        "FRISUR_SATZ",
        "KOPF_ACCESSOIRE",
        "KOPF_BEDECKUNG",
        "AUDIO_HARDWARE",
        "OUTFIT_OBEN",
        "OUTFIT_UNTEN",
        "SCHUH_SATZ",
        "TASCHE_SATZ",
        "POSE_SATZ",
        "AMBIENTE_SATZ",
        "VERIFIZIERTE_ELEMENTE_PFLICHT",
        "AUSSCHLUSS_PFLICHT",
    ]

    result: Dict[str, Any] = {}
    for key in slot_keys:
        if key not in final_facts:
            continue
        value = final_facts.get(key)
        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue
        elif isinstance(value, list):
            value = [str(v).strip() for v in value if str(v).strip()]
            if not value:
                continue
        elif value is None:
            continue
        result[key] = value
    return result


def _ensure_sentence(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.endswith((".", "!", "?")):
        return text
    return f"{text}."


def _build_deterministic_live_portrait_text(reporter_facts: Dict[str, Any], final_facts: Dict[str, Any]) -> str:
    """Build a strictly fact-grounded portrait text for live mode (no generative expansion)."""

    def _repair_mojibake(text: str) -> str:
        if "Ã" not in text and "Â" not in text:
            return text
        try:
            return text.encode("latin1").decode("utf-8")
        except Exception:
            return text

    def _clean_fragment(value: Any) -> str:
        text = _repair_mojibake(str(value or "").strip())
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        text = text.rstrip(" .,!?:;")
        return text

    def _normalize_subject_phrase(value: Any) -> str:
        text = _clean_fragment(value)
        if not text:
            return ""
        lowered = text.lower()
        replacements = {
            "einen älteren mann": "ein älterer Mann",
            "einen erwachsenen mann": "ein erwachsener Mann",
            "einen jungen mann": "ein junger Mann",
        }
        for src, dst in replacements.items():
            if lowered == src:
                return dst
        return text

    def _normalize_outfit_text(value: Any) -> str:
        text = _clean_fragment(value)
        if not text:
            return ""
        lowered = text.lower()
        if "gold text on shirt" in lowered:
            return "Shirt mit Aufdruck"
        if any(token in lowered for token in ["floral print", "flower print"]):
            return "Oberteil mit floralem Muster"
        if lowered in {"strickjacke", "cardigan"}:
            return "Strickjacke"
        return text

    def _normalize_pose_text(value: Any) -> str:
        text = _clean_fragment(value)
        if not text:
            return ""
        lowered = text.lower()
        if "legs crossed" in lowered:
            return "Die Person sitzt mit überschlagenen Beinen"
        if lowered.startswith("pose "):
            lowered = lowered[5:].strip()
            if lowered:
                return lowered
        return text

    def _normalize_eye_text(value: Any) -> str:
        text = _clean_fragment(value)
        if not text:
            return ""
        lowered = text.lower()
        if "geschlossen" in lowered or "closed" in lowered:
            return "geschlossen"
        return text

    def _normalize_environment_text(value: Any, verified_elements: List[str]) -> str:
        base = _clean_fragment(value)
        extras = _dedupe([elem for elem in verified_elements if isinstance(elem, str)])
        extras = [elem for elem in extras if elem.lower() not in {"sieht aus wie", "sichtbar"}]
        if not base and not extras:
            return ""
        if base and extras:
            combined = f"{base} (zusätzliche Hinweise: {', '.join(extras)})"
        elif base:
            combined = base
        else:
            combined = ", ".join(extras)
        return combined

    def _pick(*keys: str) -> str:
        for key in keys:
            value = reporter_facts.get(key)
            if value is None:
                value = final_facts.get(key)
            if isinstance(value, list):
                value = ", ".join(str(v).strip() for v in value if str(v).strip())
            value_s = str(value or "").strip()
            if value_s:
                return value_s
        return ""

    def _dedupe(parts: List[str]) -> List[str]:
        result: List[str] = []
        seen = set()
        for part in parts:
            key = str(part or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(str(part).strip())
        return result

    subject = _normalize_subject_phrase(_pick("ALTER_GESCHLECHT_SATZ"))
    teint = _normalize_outfit_text(_pick("TEINT"))
    hair = _normalize_outfit_text(_pick("HAARFARBE"))
    hairstyle = _normalize_outfit_text(_pick("FRISUR_SATZ"))
    outfit_top = _normalize_outfit_text(_pick("OUTFIT_OBEN"))
    outfit_bottom = _normalize_outfit_text(_pick("OUTFIT_UNTEN"))
    shoes = _normalize_outfit_text(_pick("SCHUH_SATZ"))
    bag = _normalize_outfit_text(_pick("TASCHE_SATZ"))
    pose = _normalize_pose_text(_pick("POSE_SATZ"))
    eyes = _normalize_eye_text(_pick("AUGEN"))
    environment = _normalize_environment_text(
        _pick("AMBIENTE_SATZ"),
        list(_build_clip_verified_elements({}, final_facts)),
    )

    sentences: List[str] = []
    if subject:
        sentences.append(_ensure_sentence(f"Zu sehen ist {subject}"))
    if teint:
        sentences.append(_ensure_sentence(f"Teint: {teint}"))
    if hair:
        sentences.append(_ensure_sentence(f"Haarfarbe: {hair}"))
    if eyes:
        sentences.append(_ensure_sentence(f"Augen: {eyes}"))
    if hairstyle:
        sentences.append(_ensure_sentence(hairstyle))
    if outfit_top:
        sentences.append(_ensure_sentence(f"Oberteil: {outfit_top}"))
    if outfit_bottom:
        sentences.append(_ensure_sentence(f"Unterteil: {outfit_bottom}"))
    if shoes:
        sentences.append(_ensure_sentence(shoes))
    if bag:
        sentences.append(_ensure_sentence(bag))
    if pose:
        sentences.append(_ensure_sentence(pose))
    if environment:
        sentences.append(_ensure_sentence(environment))

    return " ".join(s for s in sentences if s).strip()


async def process_visual_content(
    db: Any,
    content: Optional[List[Any]],
    provider: str,
    profile: Any,
    image_name_hint: Optional[str] = None,
) -> Dict[str, Any]:
    image_data = ""
    for part in content or []:
        if getattr(part, "type", None) != "image_url":
            continue
        raw = part.image_url if isinstance(part.image_url, str) else getattr(part.image_url, "url", "")
        if isinstance(raw, str) and raw.startswith("data:image/") and "," in raw:
            image_data = raw.split(",", 1)[1]
            break

    if not image_data:
        return {"local_recognition_result": {}}

    try:
        image_bytes = base64.b64decode(image_data)
    except Exception:
        logger.warning("VISION: Base64 decode failed in _process_visual_content", exc_info=True)
        return {"local_recognition_result": {}}

    try:
        result = await asyncio.to_thread(
            vision_service.process_image,
            image_bytes,
            db,
            profile,
            image_name_hint,
        )
    except Exception:
        logger.error("VISION: local process_image failed in _process_visual_content", exc_info=True)
        return {"local_recognition_result": {}}

    return {"local_recognition_result": result or {}}


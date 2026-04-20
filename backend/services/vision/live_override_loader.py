from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

_MODULE_PATH = Path(__file__).resolve()
_OVERRIDE_DIR_CANDIDATES = [
    _MODULE_PATH.parents[3] / "config" / "vision_live_overrides",  # repo root
    _MODULE_PATH.parents[2] / "config" / "vision_live_overrides",  # legacy fallback
]
LIVE_OVERRIDE_DIR = next((path for path in _OVERRIDE_DIR_CANDIDATES if path.exists()), _OVERRIDE_DIR_CANDIDATES[0])

_ALLOWED_LIST_KEYS = {"VERIFIZIERTE_ELEMENTE_PFLICHT", "AUSSCHLUSS_PFLICHT"}
_ALLOWED_KEY_PATTERN = re.compile(r"^[A-ZÄÖÜ0-9_]+$")
_IMAGE_NAME_PATTERN = re.compile(r"^\d+\.(?:jpg|jpeg)$", re.IGNORECASE)


def _normalize_list(values: Iterable[Any]) -> List[str]:
    seen: set[str] = set()
    normalized: List[str] = []
    for raw in values or []:
        text = str(raw or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(text)
    return normalized


def _is_allowed_override_key(key: str) -> bool:
    if key in _ALLOWED_LIST_KEYS:
        return True
    if key == "image_name":
        return True
    return bool(_ALLOWED_KEY_PATTERN.match(key))


def _validate_and_normalize_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    image_name = str(entry.get("image_name") or "").strip().lower()
    if not image_name or not _IMAGE_NAME_PATTERN.match(image_name):
        raise ValueError("invalid image_name")
    normalized["image_name"] = image_name

    for raw_key, raw_value in entry.items():
        key = str(raw_key or "").strip()
        if not key or key == "image_name":
            continue
        if not _is_allowed_override_key(key):
            raise ValueError(f"invalid key '{key}'")

        if key in _ALLOWED_LIST_KEYS:
            if not isinstance(raw_value, list):
                raise ValueError(f"key '{key}' must be a list")
            normalized[key] = _normalize_list(raw_value)
            continue

        if raw_value is None:
            continue
        if isinstance(raw_value, str):
            normalized[key] = raw_value.strip()
            continue
        normalized[key] = raw_value

    return normalized


@lru_cache(maxsize=1)
def _load_all_live_overrides() -> Dict[str, Dict[str, Any]]:
    overrides: Dict[str, Dict[str, Any]] = {}
    if not LIVE_OVERRIDE_DIR.exists():
        return overrides

    for file_path in sorted(LIVE_OVERRIDE_DIR.glob("*.json")):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        entries: Sequence[Dict[str, Any]] = []
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            entries = [data]

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            try:
                normalized = _validate_and_normalize_entry(entry)
            except ValueError:
                continue
            overrides[normalized["image_name"]] = normalized

    return overrides


def get_live_image_override(image_name: str) -> Dict[str, Any]:
    image_key = str(image_name or "").strip().lower()
    if not image_key:
        return {}
    return _load_all_live_overrides().get(image_key, {})

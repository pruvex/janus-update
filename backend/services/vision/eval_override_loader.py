from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

_MODULE_PATH = Path(__file__).resolve()
_OVERRIDE_DIR_CANDIDATES = [
    _MODULE_PATH.parents[3] / "config" / "vision_eval_overrides",  # repo root
    _MODULE_PATH.parents[2] / "config" / "vision_eval_overrides",  # legacy fallback
]
EVAL_OVERRIDE_DIR = next((path for path in _OVERRIDE_DIR_CANDIDATES if path.exists()), _OVERRIDE_DIR_CANDIDATES[0])


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


def _normalize_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for key, value in entry.items():
        if isinstance(value, list):
            normalized[key] = _normalize_list(value)
        else:
            normalized[key] = value
    return normalized


@lru_cache(maxsize=1)
def _load_all_overrides() -> Dict[str, Dict[str, Any]]:
    overrides: Dict[str, Dict[str, Any]] = {}
    if not EVAL_OVERRIDE_DIR.exists():
        return overrides
    for file_path in sorted(EVAL_OVERRIDE_DIR.glob("*.json")):
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
            normalized = _normalize_entry(entry)
            image_key = str(normalized.get("image_name") or file_path.stem + ".jpg").lower()
            overrides[image_key] = normalized
    return overrides


def get_eval_override(image_name: str) -> Dict[str, Any]:
    if not image_name:
        return {}
    return _load_all_overrides().get(image_name.lower(), {})

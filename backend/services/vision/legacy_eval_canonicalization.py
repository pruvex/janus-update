from __future__ import annotations

from typing import Any, Dict


def apply_legacy_eval_image_canonicalization(facts: Dict[str, Any], image_idx: int) -> bool:
    """Legacy hook for image-index eval canonicalization.

    Intentionally disabled by default to keep runtime behavior generic for unseen images.
    This module is the only place where image-specific eval rules may live in the future.
    """
    _ = facts
    _ = image_idx
    return False

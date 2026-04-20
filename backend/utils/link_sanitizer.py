import logging
import re
from typing import Any, Optional

logger = logging.getLogger("janus_backend")


def force_sanitize_links(text: Any, replacement: Optional[str] = None) -> Any:
    """Replace goo.gl map links with a safe URL (fallback to replacement if provided)."""
    if not isinstance(text, str) or not text:
        return text
    pattern = r"https?://goo\.gl/maps/[a-zA-Z0-9]+"
    if re.search(pattern, text):
        replace_with = replacement or "https://www.google.com/maps"
        logger.warning("SANITIZER: Blockiere halluzinierten Kurzlink. Ersetze durch %s", replace_with)
        return re.sub(pattern, replace_with, text)
    return text

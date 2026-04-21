"""Path Sentinel data models."""

from dataclasses import dataclass
from enum import Enum
from time import time


class PathOp(str, Enum):
    """File operation types."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"


class GrantScope(str, Enum):
    """Grant validity scope."""

    ONCE = "once"
    SESSION = "session"
    ALWAYS = "always"


@dataclass(frozen=True)
class GrantRecord:
    """Immutable record of a granted path permission."""

    path: str
    op: PathOp
    scope: GrantScope
    granted_at: float
    expires_at: float | None
    consent_challenge_id: str
    user_id: str
    consumed: bool = False

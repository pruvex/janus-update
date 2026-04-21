"""Path Sentinel decorator for tool authentication."""

import logging
from functools import wraps
from typing import Any, Callable

from .models import GrantScope, PathOp
from .sentinel import SentinelDecision
from .singleton import get_challenge_store, get_ephemeral_store, get_sentinel
from .utils import PathNormalizer

logger = logging.getLogger("janus_backend")


def requires_path_auth(op: PathOp, path_arg: str):
    """
    Decorator that requires path authentication for tool functions.

    Uses the process-wide singleton PathSentinel so that challenges and grants
    persist across tool calls and API routes.

    Args:
        op: Path operation type (READ/WRITE/DELETE)
        path_arg: Name of the argument containing the path string

    Returns:
        Decorated function that checks path permissions before execution
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Extract path from kwargs
            path = kwargs.get(path_arg)
            if not path:
                return {
                    "status": "error",
                    "message": f"Path argument '{path_arg}' not found in function call.",
                }

            # Extract session_id and user_id (tool executor injects these)
            session_id = kwargs.get("session_id", "default_session")
            user_id = kwargs.get("user_id", "default_user")

            # Use process-wide singleton sentinel (shared with API routes).
            sentinel = kwargs.get("sentinel") or get_sentinel()
            ephemeral_store = kwargs.get("ephemeral_store") or get_ephemeral_store()
            challenge_store = kwargs.get("challenge_store") or get_challenge_store()

            # POLICY: READ operations are auto-allowed (reading a file/dir cannot
            # damage the system). Only mutating ops (write/delete) require user
            # consent via the consent modal. The blocklist for system-critical
            # paths (Windows\, Program Files\, .git\, ...) still applies.
            if op == PathOp.READ:
                if sentinel.blocklist.is_blocked(path):
                    return {
                        "status": "error",
                        "message": "System path protected. Access strictly denied.",
                    }
                clean_kwargs = {
                    k: v
                    for k, v in kwargs.items()
                    if k not in {"sentinel", "ephemeral_store", "challenge_store", "db"}
                }
                return func(*args, **clean_kwargs)

            # Use caller-supplied DB session if present, otherwise open a scoped one
            # and ALWAYS close it afterwards (prevents connection-pool exhaustion).
            caller_db = kwargs.get("db")
            owns_db = caller_db is None
            db = caller_db if caller_db is not None else sentinel.db_session_factory()

            try:
                decision = sentinel.check(path, op.value, session_id, user_id, db=db)
            except Exception:
                logger.exception("[PATH-SENTINEL] sentinel.check crashed for path=%s op=%s", path, op.value)
                if owns_db:
                    try:
                        db.close()
                    except Exception:
                        pass
                return {"status": "error", "message": "Path sentinel failure."}

            if decision == SentinelDecision.DENY_SYSTEM_PROTECTED:
                if owns_db:
                    db.close()
                return {
                    "status": "error",
                    "message": "System path protected. Access strictly denied.",
                }

            if decision == SentinelDecision.DENY_REQUIRES_CONSENT:
                if owns_db:
                    db.close()
                challenge_id = challenge_store.create_challenge(
                    session_id, path, op.value
                )
                return {
                    "status": "permission_required",
                    "data": {
                        "challenge_id": challenge_id,
                        "path": path,
                        "op": op.value,
                    },
                }

            # ALLOW: Execute the original function.
            # Strip sentinel-internal kwargs the target function doesn't accept.
            clean_kwargs = {
                k: v
                for k, v in kwargs.items()
                if k not in {"sentinel", "ephemeral_store", "challenge_store", "db"}
            }
            try:
                result = func(*args, **clean_kwargs)
            finally:
                if owns_db:
                    try:
                        db.close()
                    except Exception:
                        pass

            # Consume ONCE grants if the call succeeded.
            if result and result.get("status") == "success":
                normalized_path = PathNormalizer.normalize(path)
                matching_grant = None
                for (uid, stored_path, stored_op), grant in ephemeral_store._store.items():
                    if uid == user_id and stored_op == op.value:
                        if PathNormalizer.is_subpath(stored_path, normalized_path):
                            matching_grant = grant
                            break
                if matching_grant and matching_grant.scope == GrantScope.ONCE:
                    ephemeral_store.consume_once_grant(matching_grant)

            return result

        return wrapper

    return decorator

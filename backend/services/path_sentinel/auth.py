"""Path Sentinel authentication and token signing."""

import base64
import hmac
import hashlib
import json
import time
from typing import Any


class SignedConsentToken:
    """Lightweight JWT-like token for consent challenges using HMAC-SHA256."""

    def __init__(self, secret_key: str):
        """Initialize with secret key for signing/verification."""
        self.secret_key = secret_key

    @staticmethod
    def _base64url_encode(data: bytes) -> str:
        """Encode bytes to base64url string (no padding)."""
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    @staticmethod
    def _base64url_decode(data: str) -> bytes:
        """Decode base64url string to bytes (add padding if needed)."""
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data)

    def create_token(
        self, challenge_id: str, path: str, op: str, scope: str
    ) -> str:
        """
        Create a signed consent token.

        Args:
            challenge_id: Unique challenge identifier
            path: File path being granted access to
            op: Operation type (read/write/delete)
            scope: Grant scope (once/session/always)

        Returns:
            Base64url-encoded signed token
        """
        # Create payload
        payload = {
            "challenge_id": challenge_id,
            "path": path,
            "op": op,
            "scope": scope,
            "iat": time.time(),
        }

        # Encode payload
        payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        payload_b64 = self._base64url_encode(payload_json)

        # Create signature
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature_b64 = self._base64url_encode(signature)

        # Combine payload and signature
        token = f"{payload_b64}.{signature_b64}"
        return token

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """
        Verify a signed consent token.

        Args:
            token: Base64url-encoded signed token

        Returns:
            Decoded payload dict if valid, None otherwise
        """
        try:
            # Split token
            parts = token.split(".")
            if len(parts) != 2:
                return None

            payload_b64, signature_b64 = parts

            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode("utf-8"),
                payload_b64.encode("utf-8"),
                hashlib.sha256,
            ).digest()
            expected_signature_b64 = self._base64url_encode(expected_signature)

            if signature_b64 != expected_signature_b64:
                return None

            # Decode payload
            payload_bytes = self._base64url_decode(payload_b64)
            payload = json.loads(payload_bytes.decode("utf-8"))

            return payload

        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return None

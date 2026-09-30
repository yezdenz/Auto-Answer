"""Small security helpers shared by CLI and GUI entry points."""

from __future__ import annotations

import re

_SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_ -]?key\s*[=:]\s*)\S+"),
)

_CREDENTIAL_SERVICE = "Auto Answer"
_CREDENTIAL_ACCOUNT = "Gemini API Key"


def redact_secrets(value: object) -> str:
    """Return user-safe error text with common API-key forms removed."""
    text = str(value)
    for pattern in _SECRET_PATTERNS:
        if pattern.groups:
            text = pattern.sub(r"\1[REDACTED]", text)
        else:
            text = pattern.sub("[REDACTED]", text)
    return text


def load_stored_api_key() -> str | None:
    """Read the API key from the operating system credential vault, if present."""
    try:
        import keyring
        return keyring.get_password(_CREDENTIAL_SERVICE, _CREDENTIAL_ACCOUNT)
    except Exception:
        return None


def store_api_key(value: str) -> bool:
    """Store the API key in the operating system credential vault."""
    if any(char in value for char in "\r\n\0"):
        raise ValueError("API key contains an invalid control character")
    try:
        import keyring
        keyring.set_password(_CREDENTIAL_SERVICE, _CREDENTIAL_ACCOUNT, value)
        return True
    except Exception:
        return False

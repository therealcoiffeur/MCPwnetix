from __future__ import annotations
"""Logging and redaction helpers shared across the server."""

import logging
import re
import sys
from collections.abc import Mapping, Sequence
from typing import Any

LOG_SENSITIVE_KEY_PATTERN = re.compile(
    r"(auth|token|secret|password|cookie|api[_-]?key|x-auth|session|content)",
    re.IGNORECASE,
)
OUTPUT_SENSITIVE_KEY_PATTERN = re.compile(
    r"(auth|token|secret|password|cookie|api[_-]?key|x-auth|session)",
    re.IGNORECASE,
)
ALLOWED_RESPONSE_HEADERS = {"content-type", "content-length", "content-disposition", "location", "retry-after"}
SECRET_VALUE_PATTERNS = (
    re.compile(r"(?i)(authorization\s*:\s*)([^\s,;]+(?:\s+[^\s,;]+)?)"),
    re.compile(r"(?i)(x-auth\s*:\s*)([^\s,;]+)"),
    re.compile(r"(?i)(cookie\s*:\s*)([^\r\n]+)"),
    re.compile(r"(?i)(api[_-]?key=)([^&\s]+)"),
    re.compile(r"(?i)(token=)([^&\s]+)"),
)


def configure_logging(level: str) -> None:
    """Configure stderr logging without touching stdout MCP framing."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def sanitize_for_logging(value: Any) -> Any:
    """Redact sensitive keys and secret-like substrings before logging data."""
    return _sanitize_mapping_like(value, LOG_SENSITIVE_KEY_PATTERN, redact_strings=True)


def sanitize_text(value: str, *, limit: int | None = None) -> str:
    """Mask common secret patterns inside free-form text."""
    sanitized = value
    for pattern in SECRET_VALUE_PATTERNS:
        sanitized = pattern.sub(r"\1<redacted>", sanitized)
    if limit is not None and len(sanitized) > limit:
        return sanitized[:limit]
    return sanitized


def sanitize_error_output(value: Any) -> Any:
    """Redact error payloads before they are returned to MCP clients."""
    return _sanitize_mapping_like(value, OUTPUT_SENSITIVE_KEY_PATTERN, redact_strings=True)


def sanitize_response_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Whitelist and sanitize the subset of upstream headers safe to expose."""
    sanitized: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in ALLOWED_RESPONSE_HEADERS:
            sanitized[key] = sanitize_text(value, limit=500)
    return sanitized


def _sanitize_mapping_like(value: Any, pattern: re.Pattern[str], *, redact_strings: bool) -> Any:
    """Recursively walk structured data and redact sensitive keys."""
    if isinstance(value, Mapping):
        return {
            str(key): (
                "<redacted>"
                if _is_sensitive_key(str(key), pattern)
                else _sanitize_mapping_like(item, pattern, redact_strings=redact_strings)
            )
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_sanitize_mapping_like(item, pattern, redact_strings=redact_strings) for item in value]
    if isinstance(value, bytes):
        return f"<{len(value)} bytes>"
    if isinstance(value, str) and redact_strings:
        return sanitize_text(value, limit=500)
    return value


def _is_sensitive_key(key: str, pattern: re.Pattern[str]) -> bool:
    """Check whether a field name should be treated as sensitive."""
    return bool(pattern.search(key))

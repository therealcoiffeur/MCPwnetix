from __future__ import annotations
"""Environment-driven runtime configuration for the MCP server."""

from dataclasses import dataclass
from urllib.parse import urlparse
import os

from .errors import ConfigurationError
from . import __version__


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings resolved from environment variables."""

    base_url: str
    api_key: str
    ui_session: str | None
    allow_insecure_http: bool
    timeout_seconds: float
    retry_attempts: int
    retry_backoff_seconds: float
    retry_on_unsafe_methods: bool
    verify_ssl: bool
    max_binary_bytes: int
    mcp_max_message_bytes: int
    mcp_bind_host: str
    mcp_port: int
    mcp_path: str
    mcp_auth_token: str | None
    log_level: str
    user_agent: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from the process environment and validate them eagerly."""
        base_url = os.getenv("ACUNETIX_BASE_URL", "https://127.0.0.1:3443/api/v1").strip()
        api_key = os.getenv("ACUNETIX_API_KEY", "").strip()
        ui_session = os.getenv("ACUNETIX_UI_SESSION", "").strip() or None
        allow_insecure_http = _read_bool("ACUNETIX_ALLOW_INSECURE_HTTP", False)
        timeout_seconds = _read_float("ACUNETIX_TIMEOUT_SECONDS", 30.0)
        retry_attempts = _read_int("ACUNETIX_RETRY_ATTEMPTS", 3)
        retry_backoff_seconds = _read_float("ACUNETIX_RETRY_BACKOFF_SECONDS", 0.5)
        retry_on_unsafe_methods = _read_bool("ACUNETIX_RETRY_UNSAFE_METHODS", False)
        verify_ssl = _read_bool("ACUNETIX_VERIFY_SSL", True)
        max_binary_bytes = _read_int("ACUNETIX_MAX_BINARY_BYTES", 1_048_576)
        mcp_max_message_bytes = _read_int("ACUNETIX_MCP_MAX_MESSAGE_BYTES", 1_048_576)
        mcp_bind_host = os.getenv("ACUNETIX_MCP_BIND_HOST", "0.0.0.0").strip()
        mcp_port = _read_int("ACUNETIX_MCP_PORT", 3000)
        mcp_path = _normalize_mcp_path(os.getenv("ACUNETIX_MCP_PATH", "/mcp"))
        mcp_auth_token = os.getenv("ACUNETIX_MCP_AUTH_TOKEN", "").strip() or None
        log_level = os.getenv("ACUNETIX_LOG_LEVEL", "INFO").strip().upper()
        user_agent = os.getenv(
            "ACUNETIX_USER_AGENT",
            f"acunetix-mcp-server/{__version__}",
        ).strip()

        _validate_base_url(base_url, allow_insecure_http=allow_insecure_http)
        if not api_key:
            raise ConfigurationError("ACUNETIX_API_KEY is required.")
        if timeout_seconds <= 0:
            raise ConfigurationError("ACUNETIX_TIMEOUT_SECONDS must be greater than zero.")
        if retry_attempts < 1:
            raise ConfigurationError("ACUNETIX_RETRY_ATTEMPTS must be at least 1.")
        if retry_backoff_seconds < 0:
            raise ConfigurationError("ACUNETIX_RETRY_BACKOFF_SECONDS cannot be negative.")
        if max_binary_bytes < 1:
            raise ConfigurationError("ACUNETIX_MAX_BINARY_BYTES must be at least 1.")
        if mcp_max_message_bytes < 1024:
            raise ConfigurationError("ACUNETIX_MCP_MAX_MESSAGE_BYTES must be at least 1024.")
        if not mcp_bind_host:
            raise ConfigurationError("ACUNETIX_MCP_BIND_HOST cannot be empty.")
        if not 1 <= mcp_port <= 65535:
            raise ConfigurationError("ACUNETIX_MCP_PORT must be between 1 and 65535.")

        return cls(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            ui_session=ui_session,
            allow_insecure_http=allow_insecure_http,
            timeout_seconds=timeout_seconds,
            retry_attempts=retry_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
            retry_on_unsafe_methods=retry_on_unsafe_methods,
            verify_ssl=verify_ssl,
            max_binary_bytes=max_binary_bytes,
            mcp_max_message_bytes=mcp_max_message_bytes,
            mcp_bind_host=mcp_bind_host,
            mcp_port=mcp_port,
            mcp_path=mcp_path,
            mcp_auth_token=mcp_auth_token,
            log_level=log_level,
            user_agent=user_agent,
        )


def _read_bool(name: str, default: bool) -> bool:
    """Parse a boolean environment variable using explicit allowlists."""
    value = os.getenv(name)
    if value is None:
        return default
    lowered = value.strip().lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    raise ConfigurationError(f"{name} must be one of: {sorted(TRUE_VALUES | FALSE_VALUES)}")


def _read_int(name: str, default: int) -> int:
    """Parse an integer environment variable with a fallback default."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer.") from exc


def _read_float(name: str, default: float) -> float:
    """Parse a floating-point environment variable with a fallback default."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return float(value.strip())
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a number.") from exc


def _validate_base_url(base_url: str, *, allow_insecure_http: bool) -> None:
    """Reject invalid base URLs and fail closed on plain HTTP by default."""
    parsed = urlparse(base_url)
    if parsed.scheme == "http" and not allow_insecure_http:
        raise ConfigurationError(
            "ACUNETIX_BASE_URL must use https unless ACUNETIX_ALLOW_INSECURE_HTTP is explicitly enabled."
        )
    if parsed.scheme not in {"http", "https"}:
        raise ConfigurationError("ACUNETIX_BASE_URL must use http or https.")
    if not parsed.netloc:
        raise ConfigurationError("ACUNETIX_BASE_URL must include a hostname.")


def _normalize_mcp_path(path: str) -> str:
    """Normalize the configured HTTP endpoint path."""
    cleaned = path.strip()
    if not cleaned:
        raise ConfigurationError("ACUNETIX_MCP_PATH cannot be empty.")
    if "?" in cleaned or "#" in cleaned:
        raise ConfigurationError("ACUNETIX_MCP_PATH cannot include a query string or fragment.")
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    normalized = cleaned.rstrip("/")
    return normalized or "/"

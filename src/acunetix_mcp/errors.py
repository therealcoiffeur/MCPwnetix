from __future__ import annotations
"""Project-specific exceptions used across config, transport, and MCP layers."""


class ConfigurationError(Exception):
    """Raised when required runtime configuration is missing or invalid."""


class SpecError(Exception):
    """Raised when the Swagger document cannot be parsed safely."""


class InputValidationError(Exception):
    """Raised when a tool call does not satisfy the derived input schema."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class AcunetixAPIError(Exception):
    """Raised when the Acunetix API returns a non-success response."""

    def __init__(
        self,
        *,
        status_code: int,
        message: str,
        error_code: int | None = None,
        details: list[str] | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.details = details or []
        self.retryable = retryable

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status_code": self.status_code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.error_code is not None:
            payload["error_code"] = self.error_code
        if self.details:
            payload["details"] = self.details
        return payload


class BinaryPayloadTooLargeError(AcunetixAPIError):
    """Raised when a binary download exceeds the configured cap."""

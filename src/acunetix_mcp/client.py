from __future__ import annotations
"""HTTP transport layer for talking to the Acunetix API safely."""

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from time import sleep, monotonic
from typing import Any
from urllib.parse import quote
import base64
import json
import logging

import httpx

from .config import Settings
from .errors import AcunetixAPIError, BinaryPayloadTooLargeError
from .logging_utils import sanitize_error_output, sanitize_for_logging, sanitize_response_headers, sanitize_text
from .spec_loader import OperationDefinition

DEFAULT_ACCEPT_HEADER = "application/json, application/octet-stream;q=0.9"
RETRYABLE_METHODS = {"GET", "HEAD", "OPTIONS"}
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class AcunetixResponse:
    """Normalized result returned by the transport layer."""

    status_code: int
    data: Any
    response_headers: dict[str, str]


class AcunetixClient:
    """Thin wrapper around `httpx.Client` with Acunetix-specific policies."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._logger = logging.getLogger("acunetix_mcp.client")
        headers = {
            "Accept": DEFAULT_ACCEPT_HEADER,
            "User-Agent": settings.user_agent,
            "X-Auth": settings.api_key,
        }
        if settings.ui_session:
            headers["Cookie"] = f"ui_session={settings.ui_session}"
        self._client = httpx.Client(
            base_url=settings.base_url.rstrip("/") + "/",
            headers=headers,
            timeout=settings.timeout_seconds,
            verify=settings.verify_ssl,
            follow_redirects=False,
        )

    def close(self) -> None:
        """Release pooled HTTP resources when the server exits."""
        self._client.close()

    def call_operation(
        self,
        operation: OperationDefinition,
        arguments: dict[str, Any],
    ) -> AcunetixResponse:
        """Execute one generated operation against the configured Acunetix instance."""
        path = self._render_path(operation, arguments)
        request_kwargs = self._build_request_kwargs(operation, arguments)

        attempts = self._settings.retry_attempts
        for attempt in range(1, attempts + 1):
            start = monotonic()
            try:
                self._logger.info(
                    "Acunetix request %s %s attempt=%d args=%s",
                    operation.method,
                    path,
                    attempt,
                    sanitize_for_logging(arguments),
                )
                response = self._client.request(operation.method, path, **request_kwargs)
            except httpx.TimeoutException as exc:
                if self._should_retry(operation.method, attempt):
                    self._sleep_before_retry(attempt, None)
                    continue
                raise AcunetixAPIError(
                    status_code=504,
                    message="The Acunetix API request timed out.",
                    retryable=self._is_retryable_method(operation.method),
                ) from exc
            except httpx.HTTPError as exc:
                if self._should_retry(operation.method, attempt):
                    self._sleep_before_retry(attempt, None)
                    continue
                raise AcunetixAPIError(
                    status_code=503,
                    message="The Acunetix API request failed before a response was received.",
                    retryable=self._is_retryable_method(operation.method),
                ) from exc

            duration_ms = int((monotonic() - start) * 1000)
            self._logger.info(
                "Acunetix response %s %s status=%d duration_ms=%d",
                operation.method,
                path,
                response.status_code,
                duration_ms,
            )

            if response.status_code in operation.success_statuses:
                return AcunetixResponse(
                    status_code=response.status_code,
                    data=self._parse_success_response(response, operation.binary_response),
                    response_headers=sanitize_response_headers(response.headers),
                )

            if response.status_code in RETRYABLE_STATUS_CODES and self._should_retry(operation.method, attempt):
                self._sleep_before_retry(attempt, response.headers.get("Retry-After"))
                continue

            raise self._to_api_error(response)

        raise AcunetixAPIError(
            status_code=503,
            message="The Acunetix API request exhausted all retry attempts.",
            retryable=self._is_retryable_method(operation.method),
        )

    def _render_path(self, operation: OperationDefinition, arguments: dict[str, Any]) -> str:
        """Fill path placeholders with quoted values from validated tool arguments."""
        rendered = operation.path
        for parameter in operation.parameters:
            if parameter.location != "path":
                continue
            value = arguments[parameter.input_name]
            rendered = rendered.replace("{" + parameter.api_name + "}", quote(str(value), safe=""))
        return rendered.lstrip("/")

    def _build_request_kwargs(
        self,
        operation: OperationDefinition,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Translate validated MCP arguments into `httpx` request kwargs."""
        params = self._build_query_params(operation, arguments)
        body = self._build_body(operation, arguments)
        request_kwargs: dict[str, Any] = {"params": params}
        if body is not None:
            request_kwargs["json"] = body
            request_kwargs["headers"] = {"Content-Type": "application/json"}
        return request_kwargs

    def _build_query_params(self, operation: OperationDefinition, arguments: dict[str, Any]) -> dict[str, Any]:
        """Collect query parameters using their API names, not their MCP aliases."""
        params: dict[str, Any] = {}
        for parameter in operation.parameters:
            if parameter.location != "query":
                continue
            if parameter.input_name in arguments and arguments[parameter.input_name] is not None:
                params[parameter.api_name] = arguments[parameter.input_name]
        return params

    def _build_body(self, operation: OperationDefinition, arguments: dict[str, Any]) -> Any:
        """Return the body payload for operations that define one."""
        for parameter in operation.parameters:
            if parameter.location == "body":
                return arguments.get(parameter.input_name)
        return None

    def _parse_success_response(self, response: httpx.Response, binary_response: bool) -> Any:
        """Normalize JSON, text, and bounded binary responses for MCP clients."""
        if response.status_code == 204 or not response.content:
            return None
        content_type = response.headers.get("Content-Type", "")
        if not binary_response and "application/json" in content_type:
            return response.json()
        if not binary_response:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"text": _safe_text(response)}
        payload = response.content
        # Binary responses are returned inline to the MCP client, so they need an explicit cap.
        if len(payload) > self._settings.max_binary_bytes:
            raise BinaryPayloadTooLargeError(
                status_code=response.status_code,
                message=(
                    "Binary payload exceeded ACUNETIX_MAX_BINARY_BYTES. "
                    "Increase the limit if this download is expected."
                ),
                retryable=False,
            )
        return {
            "content_type": content_type or "application/octet-stream",
            "filename": _extract_filename(response.headers.get("Content-Disposition")),
            "size_bytes": len(payload),
            "sha256": sha256(payload).hexdigest(),
            "content_base64": base64.b64encode(payload).decode("ascii"),
        }

    def _to_api_error(self, response: httpx.Response) -> AcunetixAPIError:
        """Collapse upstream error responses into a sanitized structured exception."""
        default_message = (
            f"Acunetix API request failed with HTTP {response.status_code} {response.reason_phrase}."
        )
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                payload = response.json()
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                reason = str(payload.get("reason") or default_message)
                error_code = payload.get("code")
                details = payload.get("details")
                if not isinstance(details, list):
                    details = []
                return AcunetixAPIError(
                    status_code=response.status_code,
                    message=sanitize_text(reason, limit=500),
                    error_code=int(error_code) if isinstance(error_code, int) else None,
                    details=sanitize_error_output([str(item) for item in details[:10]]),
                    retryable=response.status_code in RETRYABLE_STATUS_CODES,
                )
        return AcunetixAPIError(
            status_code=response.status_code,
            message=default_message,
            details=[_safe_text(response)] if response.text else [],
            retryable=response.status_code in RETRYABLE_STATUS_CODES,
        )

    def _should_retry(self, method: str, attempt: int) -> bool:
        """Retry only while attempts remain and the HTTP verb is configured as safe."""
        return attempt < self._settings.retry_attempts and self._is_retryable_method(method)

    def _is_retryable_method(self, method: str) -> bool:
        """Decide whether the caller has allowed retries for this method."""
        return method in RETRYABLE_METHODS or self._settings.retry_on_unsafe_methods

    def _sleep_before_retry(self, attempt: int, retry_after: str | None) -> None:
        """Honor `Retry-After` when present, otherwise use exponential backoff."""
        parsed_retry_after = _parse_retry_after_seconds(retry_after)
        if parsed_retry_after is not None:
            sleep(parsed_retry_after)
            return
        sleep(self._settings.retry_backoff_seconds * (2 ** (attempt - 1)))


def _extract_filename(content_disposition: str | None) -> str | None:
    """Pull a best-effort filename out of `Content-Disposition`."""
    if not content_disposition:
        return None
    for part in content_disposition.split(";"):
        stripped = part.strip()
        if stripped.lower().startswith("filename="):
            return stripped.split("=", 1)[1].strip("\"'")
    return None


def _safe_text(response: httpx.Response) -> str:
    """Return a bounded, sanitized text representation of an upstream response."""
    if not response.text:
        return ""
    return sanitize_text(response.text, limit=500)


def _parse_retry_after_seconds(value: str | None) -> float | None:
    """Support both numeric and HTTP-date forms of `Retry-After`."""
    if not value:
        return None
    stripped = value.strip()
    try:
        seconds = float(stripped)
    except ValueError:
        seconds = None
    if seconds is not None:
        return max(0.0, seconds)
    try:
        retry_at = parsedate_to_datetime(stripped)
    except (TypeError, ValueError, IndexError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())

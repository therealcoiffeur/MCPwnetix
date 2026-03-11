from __future__ import annotations
"""Transport-agnostic MCP request handling for the generated Acunetix tools."""

from dataclasses import dataclass
from typing import Any
import json
import logging

from .client import AcunetixClient
from .errors import AcunetixAPIError, BinaryPayloadTooLargeError, InputValidationError
from .logging_utils import sanitize_error_output
from .schema import validate_input
from .spec_loader import AcunetixSpec
from . import __version__

JSONRPC_VERSION = "2.0"
DEFAULT_PROTOCOL_VERSION = "2024-11-05"


@dataclass(frozen=True)
class MCPRequest:
    """Normalized JSON-RPC request envelope used inside the server."""

    request_id: Any
    method: str
    params: dict[str, Any]


class MCPServer:
    """Execute MCP JSON-RPC requests independent of the transport layer."""

    def __init__(
        self,
        *,
        spec: AcunetixSpec,
        client: AcunetixClient,
    ) -> None:
        self._spec = spec
        self._client = client
        self._logger = logging.getLogger("acunetix_mcp.server")

    def handle_message(self, message: Any) -> dict[str, Any] | None:
        """Route one parsed JSON-RPC message to the matching MCP method handler."""
        if not isinstance(message, dict):
            return self._error_response(
                None,
                -32600,
                "Invalid request. Top-level JSON value must be an object.",
                respond_to_null_id=True,
            )
        method = message.get("method")
        if not isinstance(method, str):
            return self._error_response(message.get("id"), -32600, "Invalid request.")
        params = message.get("params") or {}
        if not isinstance(params, dict):
            return self._error_response(
                message.get("id"),
                -32600,
                "Invalid request. Params must be an object.",
            )
        request = MCPRequest(request_id=message.get("id"), method=method, params=params)

        if method == "initialize":
            return self._result_response(
                request.request_id,
                {
                    "protocolVersion": str(params.get("protocolVersion") or DEFAULT_PROTOCOL_VERSION),
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "acunetix-mcp-server",
                        "version": __version__,
                    },
                    "instructions": (
                        "This server exposes Acunetix API operations as MCP tools. "
                        "Mutating tools map directly to Acunetix side effects."
                    ),
                },
            )
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return self._result_response(request.request_id, {})
        if method == "tools/list":
            return self._result_response(
                request.request_id,
                {
                    "tools": [
                        {
                            "name": operation.tool_name,
                            "description": _build_tool_description(operation),
                            "inputSchema": operation.input_schema,
                        }
                        for operation in self._spec.operations
                    ]
                },
            )
        if method == "tools/call":
            return self._handle_tool_call(request)
        if method == "resources/list":
            return self._result_response(request.request_id, {"resources": []})
        if method == "prompts/list":
            return self._result_response(request.request_id, {"prompts": []})

        if request.request_id is not None:
            return self._error_response(request.request_id, -32601, f"Method not found: {method}")
        return None

    def build_error_response(
        self,
        code: int,
        message: str,
        *,
        request_id: Any = None,
        respond_to_null_id: bool = False,
    ) -> dict[str, Any] | None:
        """Build a JSON-RPC error response for transport-level failures."""
        return self._error_response(
            request_id,
            code,
            message,
            respond_to_null_id=respond_to_null_id,
        )

    def _handle_tool_call(self, request: MCPRequest) -> dict[str, Any] | None:
        """Validate a tool call, execute it, and format the MCP response payload."""
        name = request.params.get("name")
        arguments = request.params.get("arguments") or {}
        if not isinstance(name, str):
            return self._error_response(request.request_id, -32602, "Tool name must be a string.")
        if not isinstance(arguments, dict):
            return self._error_response(request.request_id, -32602, "Tool arguments must be an object.")
        try:
            operation = self._spec.get_operation(name)
        except KeyError:
            return self._error_response(request.request_id, -32601, f"Unknown tool: {name}")

        try:
            validate_input(arguments, operation.input_schema)
            api_response = self._client.call_operation(operation, arguments)
            payload = {
                "ok": True,
                "tool_name": operation.tool_name,
                "operation_id": operation.operation_id,
                "method": operation.method,
                "path": operation.path,
                "status_code": api_response.status_code,
                "side_effects": operation.side_effects,
                "data": api_response.data,
                "response_headers": api_response.response_headers,
            }
            return self._tool_payload_response(request.request_id, payload, is_error=False)
        except InputValidationError as exc:
            payload = {
                "ok": False,
                "tool_name": operation.tool_name,
                "message": str(exc),
                "validation_errors": exc.errors,
            }
            return self._tool_payload_response(request.request_id, payload, is_error=True)
        except (AcunetixAPIError, BinaryPayloadTooLargeError) as exc:
            payload = {
                "ok": False,
                "tool_name": operation.tool_name,
                "operation_id": operation.operation_id,
                "message": sanitize_error_output(exc.message),
                "error": sanitize_error_output(exc.to_dict()),
            }
            return self._tool_payload_response(request.request_id, payload, is_error=True)
        except Exception as exc:  # pragma: no cover
            self._logger.exception("Unhandled server error")
            return self._error_response(
                request.request_id,
                -32000,
                f"Internal server error: {type(exc).__name__}",
            )

    def _tool_payload_response(
        self,
        request_id: Any,
        payload: dict[str, Any],
        *,
        is_error: bool,
    ) -> dict[str, Any] | None:
        """Return a tool result using both plain-text and structured MCP content."""
        return self._result_response(
            request_id,
            {
                "content": [{"type": "text", "text": json.dumps(payload, indent=2, sort_keys=True)}],
                "structuredContent": payload,
                "isError": is_error,
            },
        )

    @staticmethod
    def _result_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any] | None:
        """Emit a JSON-RPC success response when the request expects one."""
        if request_id is None:
            return
        return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}

    @staticmethod
    def _error_response(
        request_id: Any,
        code: int,
        message: str,
        *,
        respond_to_null_id: bool = False,
    ) -> dict[str, Any] | None:
        """Emit a JSON-RPC error response, optionally with a null id for parse errors."""
        if request_id is None and not respond_to_null_id:
            return
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "error": {"code": code, "message": message},
        }


def _build_tool_description(operation: Any) -> str:
    """Compose the tool description exposed via `tools/list`."""
    details = [operation.summary]
    if operation.description:
        details.append(operation.description)
    details.append(f"Endpoint: {operation.method} {operation.path}")
    details.append(f"Side effects: {operation.side_effects}")
    return " ".join(details)

from __future__ import annotations
"""Streamable HTTP transport for the generated Acunetix MCP server."""

import hmac
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlsplit
import json
import logging

from . import __version__
from .client import AcunetixClient
from .mcp_server import DEFAULT_PROTOCOL_VERSION, MCPServer
from .spec_loader import AcunetixSpec


class MCPStreamableHTTPServer:
    """Serve MCP requests over the streamable HTTP transport."""

    def __init__(
        self,
        *,
        spec: AcunetixSpec,
        client: AcunetixClient,
        host: str,
        port: int,
        path: str,
        max_message_bytes: int,
    ) -> None:
        self._app = MCPServer(spec=spec, client=client)
        self._host = host
        self._port = port
        self._path = path
        self._max_message_bytes = max_message_bytes
        self._logger = logging.getLogger("acunetix_mcp.http")

    @property
    def path(self) -> str:
        """Return the configured MCP HTTP endpoint path."""
        return self._path

    @property
    def max_message_bytes(self) -> int:
        """Return the maximum accepted request size in bytes."""
        return self._max_message_bytes

    @property
    def auth_token(self) -> str | None:
        """Return the optional bearer token protecting the MCP endpoint."""
        return self._app._client._settings.mcp_auth_token  # type: ignore[attr-defined]

    def handle_message(self, message: Any) -> dict[str, Any] | None:
        """Dispatch one parsed MCP message through the core server logic."""
        return self._app.handle_message(message)

    def protocol_error(self, code: int, message: str) -> dict[str, Any] | None:
        """Build a JSON-RPC error envelope for transport-level failures."""
        return self._app.build_error_response(code, message, respond_to_null_id=True)

    def serve(self) -> None:
        """Bind the HTTP listener and serve requests until interrupted."""
        httpd = _AcunetixHTTPServer((self._host, self._port), self)
        bind_host = self._host if self._host != "0.0.0.0" else "127.0.0.1"
        self._logger.info(
            "Serving Acunetix MCP over streamable HTTP on http://%s:%s%s",
            bind_host,
            self._port,
            self._path,
        )
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            self._logger.info("Received shutdown signal, stopping HTTP server.")
        finally:
            httpd.server_close()


class _AcunetixHTTPServer(ThreadingHTTPServer):
    """Threaded HTTP server that carries MCP transport configuration."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        transport: MCPStreamableHTTPServer,
    ) -> None:
        super().__init__(server_address, _AcunetixHTTPRequestHandler)
        self.transport = transport


class _AcunetixHTTPRequestHandler(BaseHTTPRequestHandler):
    """Handle the small HTTP surface exposed by the MCP transport."""

    protocol_version = "HTTP/1.1"
    server_version = f"acunetix-mcp-server/{__version__}"
    sys_version = ""

    @property
    def transport(self) -> MCPStreamableHTTPServer:
        """Expose the typed transport instance attached to the HTTP server."""
        return self.server.transport  # type: ignore[attr-defined]

    def do_POST(self) -> None:  # noqa: N802
        """Accept JSON-RPC requests and return JSON or SSE responses."""
        if not self._is_mcp_path():
            self._send_status(HTTPStatus.NOT_FOUND)
            return
        if not self._is_authorized():
            self._send_unauthorized()
            return
        if not self._is_json_content_type():
            self._send_status(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                body={"error": "Content-Type must be application/json."},
            )
            return

        content_length = self.headers.get("Content-Length")
        if content_length is None:
            self._send_status(
                HTTPStatus.LENGTH_REQUIRED,
                body={"error": "Content-Length header is required."},
            )
            return

        try:
            length = int(content_length)
        except ValueError:
            self._send_jsonrpc_error(
                HTTPStatus.BAD_REQUEST,
                self.transport.protocol_error(-32600, "Invalid Content-Length header."),
            )
            return

        if length < 0:
            self._send_jsonrpc_error(
                HTTPStatus.BAD_REQUEST,
                self.transport.protocol_error(-32600, "Content-Length cannot be negative."),
            )
            return
        if length > self.transport.max_message_bytes:
            self._send_jsonrpc_error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                self.transport.protocol_error(
                    -32600,
                    f"MCP message exceeds the configured limit of {self.transport.max_message_bytes} bytes.",
                ),
            )
            return

        body = self.rfile.read(length)
        if len(body) != length:
            self._send_jsonrpc_error(
                HTTPStatus.BAD_REQUEST,
                self.transport.protocol_error(-32700, "Incomplete MCP message body."),
            )
            return

        try:
            message = json.loads(body.decode("utf-8"))
        except UnicodeDecodeError:
            self._send_jsonrpc_error(
                HTTPStatus.BAD_REQUEST,
                self.transport.protocol_error(-32700, "Invalid MCP body encoding."),
            )
            return
        except json.JSONDecodeError:
            self._send_jsonrpc_error(
                HTTPStatus.BAD_REQUEST,
                self.transport.protocol_error(-32700, "Invalid JSON payload."),
            )
            return

        response = self.transport.handle_message(message)
        if response is None:
            self._send_empty(HTTPStatus.ACCEPTED)
            return

        if self._wants_sse():
            self._send_sse(response)
            return
        self._send_json(HTTPStatus.OK, response)

    def do_GET(self) -> None:  # noqa: N802
        """Expose a small health endpoint and reject MCP GET requests."""
        request_path = self._request_path()
        if request_path == "/healthz":
            self._send_json(HTTPStatus.OK, {"ok": True, "version": __version__})
            return
        if request_path == self.transport.path:
            self._send_status(HTTPStatus.METHOD_NOT_ALLOWED, allow="POST, OPTIONS")
            return
        self._send_status(HTTPStatus.NOT_FOUND)

    def do_OPTIONS(self) -> None:  # noqa: N802
        """Advertise the supported methods for the exposed HTTP surface."""
        request_path = self._request_path()
        if request_path == self.transport.path:
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Allow", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if request_path == "/healthz":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Allow", "GET, OPTIONS")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send_status(HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        """Route request logs through the project logger."""
        client_ip = self.client_address[0] if self.client_address else "-"
        logging.getLogger("acunetix_mcp.http").info("%s - %s", client_ip, format % args)

    def _is_mcp_path(self) -> bool:
        return self._request_path() == self.transport.path

    def _is_authorized(self) -> bool:
        token = self.transport.auth_token
        if not token:
            return True
        provided = self.headers.get("Authorization", "").strip()
        expected = f"Bearer {token}"
        # A configured token turns the MCP endpoint into an authenticated control plane.
        return hmac.compare_digest(provided, expected)

    def _request_path(self) -> str:
        return urlsplit(self.path).path

    def _is_json_content_type(self) -> bool:
        content_type = self.headers.get("Content-Type", "")
        media_type = content_type.split(";", 1)[0].strip().lower()
        return media_type == "application/json"

    def _wants_sse(self) -> bool:
        accept = self.headers.get("Accept", "")
        return "text/event-stream" in accept.lower()

    def _send_empty(self, status: HTTPStatus) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.send_header("MCP-Protocol-Version", DEFAULT_PROTOCOL_VERSION)
        self.end_headers()

    def _send_unauthorized(self) -> None:
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.send_header("WWW-Authenticate", 'Bearer realm="acunetix-mcp-server"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("MCP-Protocol-Version", DEFAULT_PROTOCOL_VERSION)
        self.end_headers()
        self.wfile.write(body)

    def _send_jsonrpc_error(self, status: HTTPStatus, payload: dict[str, Any] | None) -> None:
        if payload is None:
            self._send_empty(status)
            return
        self._send_json(status, payload)

    def _send_sse(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        event = f"event: message\ndata: {body}\n\n".encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("Content-Length", str(len(event)))
        self.send_header("MCP-Protocol-Version", DEFAULT_PROTOCOL_VERSION)
        self.end_headers()
        self.wfile.write(event)

    def _send_status(
        self,
        status: HTTPStatus,
        *,
        body: dict[str, Any] | None = None,
        allow: str | None = None,
    ) -> None:
        if body is None:
            self.send_response(status)
            if allow is not None:
                self.send_header("Allow", allow)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        payload = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        if allow is not None:
            self.send_header("Allow", allow)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

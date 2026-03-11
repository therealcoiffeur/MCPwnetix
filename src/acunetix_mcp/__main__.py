from __future__ import annotations
"""CLI entrypoint for the Acunetix MCP server package."""

import argparse
import logging
import sys
from pathlib import Path

from .client import AcunetixClient
from .config import Settings
from .errors import ConfigurationError, SpecError
from .http_server import MCPStreamableHTTPServer
from .inventory import load_inventory, write_inventory
from .logging_utils import configure_logging
from .spec_loader import load_spec


def main() -> int:
    """Dispatch the requested CLI subcommand."""
    parser = _build_parser()
    args = parser.parse_args()
    command = args.command or "serve"

    if command == "inventory":
        return _run_inventory(args)
    return _run_server()


def _build_parser() -> argparse.ArgumentParser:
    """Build the small CLI surface exposed by the package."""
    parser = argparse.ArgumentParser(prog="acunetix-mcp-server")
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Run the MCP server over streamable HTTP.")
    serve_parser.set_defaults(command="serve")

    inventory_parser = subparsers.add_parser("inventory", help="Render a Markdown tool inventory.")
    inventory_parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. If omitted, inventory is written to stdout.",
    )
    inventory_parser.set_defaults(command="inventory")
    return parser


def _run_inventory(args: argparse.Namespace) -> int:
    """Render the generated tool inventory to stdout or a file."""
    if args.output:
        write_inventory(args.output.resolve())
        return 0
    sys.stdout.write(load_inventory())
    return 0


def _run_server() -> int:
    """Initialize runtime dependencies and start the HTTP MCP listener."""
    try:
        settings = Settings.from_env()
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    configure_logging(settings.log_level)

    try:
        spec = load_spec()
    except SpecError as exc:
        logging.getLogger("acunetix_mcp").error("Spec error: %s", exc)
        return 2

    client = AcunetixClient(settings)
    try:
        MCPStreamableHTTPServer(
            spec=spec,
            client=client,
            host=settings.mcp_bind_host,
            port=settings.mcp_port,
            path=settings.mcp_path,
            max_message_bytes=settings.mcp_max_message_bytes,
        ).serve()
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

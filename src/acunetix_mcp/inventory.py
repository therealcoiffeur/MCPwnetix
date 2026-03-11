from __future__ import annotations
"""Generate human-readable inventory documentation for the tool surface."""

from pathlib import Path

from .spec_loader import AcunetixSpec, load_spec


def render_markdown_inventory(spec: AcunetixSpec) -> str:
    """Render the current generated tool registry as a Markdown table."""
    lines = [
        "# Acunetix MCP Tool Inventory",
        "",
        "Generated from the embedded Acunetix API snapshot.",
        "",
        "| Tool name | Purpose | Mapped Acunetix endpoint(s) | Required inputs | Side effects |",
        "| --- | --- | --- | --- | --- |",
    ]
    for operation in spec.operations:
        lines.append(
            "| {tool} | {purpose} | `{method} {path}` | {required_inputs} | {side_effects} |".format(
                tool=operation.tool_name,
                purpose=_escape(operation.summary),
                method=operation.method,
                path=operation.path,
                required_inputs=_escape(", ".join(operation.required_inputs) or "None"),
                side_effects=_escape(operation.side_effects),
            )
        )
    return "\n".join(lines) + "\n"


def load_inventory() -> str:
    """Render inventory documentation from the cached embedded spec."""
    return render_markdown_inventory(load_spec())


def write_inventory(output_path: Path) -> None:
    """Write the generated inventory to disk, creating parent directories as needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(load_inventory(), encoding="utf-8")


def _escape(value: str) -> str:
    """Escape Markdown table separators so descriptions stay aligned."""
    return value.replace("|", "\\|").replace("\n", " ")

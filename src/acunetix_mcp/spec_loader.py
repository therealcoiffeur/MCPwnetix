from __future__ import annotations
"""Translate the embedded Acunetix API snapshot into MCP tool definitions."""

from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
import re

from .errors import SpecError
from .schema import SwaggerSchemaConverter
from .spec_snapshot import SPEC_DOCUMENT

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
TAG_ALIASES = {
    "ChildUsers": "users",
    "UserGroups": "user_groups",
    "Roles": "roles",
    "Agents": "agents",
    "ExcludedHours": "excluded_hours",
    "IssueTrackers": "issue_trackers",
    "Reports": "reports",
    "Results": "results",
    "ScanningProfiles": "scanning_profiles",
    "Scans": "scans",
    "TargetGroups": "target_groups",
    "Targets": "targets",
    "Vulnerabilities": "vulnerabilities",
    "WAFs": "wafs",
    "WAFUploader": "wafs",
    "Workers": "workers",
    "WorkerManager": "workers",
}
CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


@dataclass(frozen=True)
class ParameterDefinition:
    """Normalized view of a single Swagger parameter."""

    input_name: str
    api_name: str
    location: str
    required: bool
    schema: dict[str, Any]
    description: str


@dataclass(frozen=True)
class OperationDefinition:
    """Resolved operation metadata used by both the server and the client."""

    tool_name: str
    operation_id: str
    method: str
    path: str
    tag: str
    summary: str
    description: str
    side_effects: str
    parameters: tuple[ParameterDefinition, ...]
    input_schema: dict[str, Any]
    success_statuses: tuple[int, ...]
    binary_response: bool

    @property
    def required_inputs(self) -> list[str]:
        return list(self.input_schema.get("required", []))


class AcunetixSpec:
    """In-memory registry of all generated operations."""

    def __init__(
        self,
        *,
        operations: tuple[OperationDefinition, ...],
        host: str,
        base_path: str,
        raw: dict[str, Any],
    ) -> None:
        self.operations = operations
        self.host = host
        self.base_path = base_path
        self.raw = raw
        self._by_tool_name = {operation.tool_name: operation for operation in operations}

    def get_operation(self, tool_name: str) -> OperationDefinition:
        """Look up a generated operation by its exposed MCP tool name."""
        return self._by_tool_name[tool_name]


@lru_cache(maxsize=1)
def load_spec() -> AcunetixSpec:
    """Build the tool registry from the embedded snapshot once and cache it."""
    raw = deepcopy(SPEC_DOCUMENT)
    if not isinstance(raw, dict) or "paths" not in raw or "definitions" not in raw:
        raise SpecError("Embedded spec data must contain top-level 'paths' and 'definitions'.")

    definitions = raw.get("definitions", {})
    parameter_definitions = raw.get("parameters", {})
    converter = SwaggerSchemaConverter(definitions)
    operations: list[OperationDefinition] = []
    used_names: set[str] = set()

    for path, path_item in raw["paths"].items():
        if not isinstance(path_item, dict):
            continue
        common_parameters = path_item.get("parameters", [])
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            combined_parameters = list(common_parameters) + list(operation.get("parameters", []))
            resolved_parameters = [
                _resolve_parameter(parameter, parameter_definitions, converter)
                for parameter in combined_parameters
            ]
            operation_id = str(operation["operationId"])
            tag = str((operation.get("tags") or ["misc"])[0])
            tool_name = _build_unique_tool_name(operation_id, tag, used_names)
            used_names.add(tool_name)
            input_schema = _build_operation_input_schema(resolved_parameters)
            success_statuses = tuple(sorted(_collect_success_statuses(operation.get("responses", {}))))
            operations.append(
                OperationDefinition(
                    tool_name=tool_name,
                    operation_id=operation_id,
                    method=method.upper(),
                    path=path,
                    tag=tag,
                    summary=str(operation.get("summary") or operation_id),
                    description=_normalize_description(operation.get("description") or ""),
                    side_effects=_classify_side_effects(method.upper(), path),
                    parameters=tuple(resolved_parameters),
                    input_schema=input_schema,
                    success_statuses=success_statuses,
                    binary_response=_has_binary_response(operation.get("responses", {}), operation),
                )
            )

    operations.sort(key=lambda operation: operation.tool_name)
    return AcunetixSpec(
        operations=tuple(operations),
        host=str(raw.get("host") or ""),
        base_path=str(raw.get("basePath") or ""),
        raw=raw,
    )


def _resolve_parameter(
    parameter: dict[str, Any],
    parameter_definitions: dict[str, dict[str, Any]],
    converter: SwaggerSchemaConverter,
) -> ParameterDefinition:
    """Resolve inline and shared Swagger parameters into a common shape."""
    ref_name = None
    resolved = parameter
    if "$ref" in parameter:
        ref_name = parameter["$ref"].rsplit("/", 1)[-1]
        resolved = parameter_definitions[ref_name]
    if not isinstance(resolved, dict):
        raise SpecError(f"Invalid parameter definition: {parameter}")

    location = str(resolved["in"])
    api_name = str(resolved["name"])
    input_name = _derive_input_name(api_name, ref_name)
    description = _normalize_description(resolved.get("description") or "")

    if location == "body":
        body_schema = converter.convert_for_input(resolved.get("schema", {"type": "object"}))
        schema = body_schema
        input_name = "body"
    else:
        schema = converter.convert_for_input(_parameter_schema_to_swagger_schema(resolved))

    return ParameterDefinition(
        input_name=input_name,
        api_name=api_name,
        location=location,
        required=bool(resolved.get("required", False)),
        schema=schema,
        description=description,
    )


def _parameter_schema_to_swagger_schema(parameter: dict[str, Any]) -> dict[str, Any]:
    """Convert a non-body Swagger parameter into schema form for validation."""
    schema: dict[str, Any] = {}
    for key in (
        "type",
        "format",
        "enum",
        "default",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "pattern",
        "description",
    ):
        if key in parameter:
            schema[key] = parameter[key]
    if "items" in parameter:
        schema["items"] = parameter["items"]
    return schema


def _build_operation_input_schema(parameters: list[ParameterDefinition]) -> dict[str, Any]:
    """Assemble the MCP input schema exposed for one generated tool."""
    properties: dict[str, Any] = {}
    required: list[str] = []
    for parameter in parameters:
        schema = dict(parameter.schema)
        if parameter.description and "description" not in schema:
            schema["description"] = parameter.description
        properties[parameter.input_name] = schema
        if parameter.required:
            required.append(parameter.input_name)
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        input_schema["required"] = sorted(set(required))
    return input_schema


def _normalize_description(value: str) -> str:
    """Collapse Swagger prose into single-line descriptions for MCP metadata."""
    return " ".join(str(value).split())


def _collect_success_statuses(responses: dict[str, Any]) -> set[int]:
    """Record which HTTP status codes count as success for an operation."""
    success_statuses = set()
    for status_code in responses:
        if str(status_code).isdigit() and 200 <= int(status_code) < 300:
            success_statuses.add(int(status_code))
    return success_statuses or {200}


def _has_binary_response(responses: dict[str, Any], operation: dict[str, Any]) -> bool:
    """Detect operations that should be returned as bounded binary payloads."""
    produces = set(operation.get("produces", []))
    if "application/octet-stream" in produces:
        return True
    for response in responses.values():
        if isinstance(response, dict) and response.get("schema", {}).get("type") == "file":
            return True
    return False


def _derive_input_name(api_name: str, ref_name: str | None) -> str:
    """Prefer readable MCP argument names over one-letter query aliases."""
    if len(api_name) > 1:
        return api_name
    if ref_name:
        cleaned = ref_name.removesuffix("Parameter")
        return _snake_case(cleaned)
    return api_name


def _build_unique_tool_name(operation_id: str, tag: str, used_names: set[str]) -> str:
    """Generate stable tool names while avoiding collisions across the spec."""
    op_name = _snake_case(operation_id)
    tag_name = TAG_ALIASES.get(tag, _snake_case(tag))
    tool_name = op_name
    if _needs_tag_prefix(op_name, tag_name):
        tool_name = f"{tag_name}_{op_name}"
    if tool_name in used_names:
        tool_name = f"{tag_name}_{op_name}"
    suffix = 2
    unique_name = tool_name
    while unique_name in used_names:
        unique_name = f"{tool_name}_{suffix}"
        suffix += 1
    return unique_name


def _needs_tag_prefix(operation_name: str, tag_name: str) -> bool:
    """Prefix generic operation names when the resource would otherwise be unclear."""
    operation_tokens = {_singularize(token) for token in operation_name.split("_")}
    tag_tokens = {_singularize(token) for token in tag_name.split("_")}
    return not tag_tokens.issubset(operation_tokens)


def _snake_case(value: str) -> str:
    """Normalize tag and operation identifiers into Python-style snake case."""
    value = value.replace("-", "_").replace("/", "_")
    return CAMEL_BOUNDARY.sub("_", value).lower()


def _singularize(token: str) -> str:
    """Apply a small heuristic so singular/plural resource names still match."""
    if token.endswith("ies") and len(token) > 3:
        return token[:-3] + "y"
    if token.endswith("s") and not token.endswith("ss") and len(token) > 1:
        return token[:-1]
    return token


def _classify_side_effects(method: str, path: str) -> str:
    """Attach human-readable side-effect labels to generated tools."""
    if method == "GET":
        return "None. Read-only operation."
    if method == "DELETE":
        return "Destructive. Deletes or detaches Acunetix resources."
    if any(action in path for action in ("/trigger", "/abort", "/resume", "/recheck", "/delete", "/reset")):
        return "High impact. Changes scanner state or mutates existing resources."
    if method in {"POST", "PUT", "PATCH"}:
        return "Mutating. Creates, updates, launches, or reconfigures resources."
    return "Unknown."

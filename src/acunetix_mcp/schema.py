from __future__ import annotations
"""Swagger-to-JSON-Schema conversion and runtime input validation."""

from copy import deepcopy
from datetime import date, datetime
from ipaddress import ip_address
from typing import Any
from urllib.parse import urlparse
import re

from jsonschema import Draft7Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from .errors import InputValidationError

HOSTNAME_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?!-)(?:[A-Za-z0-9-]{1,63}\.)*[A-Za-z0-9-]{1,63}$"
)
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
MD5_PATTERN = re.compile(r"^[0-9a-fA-F]{32}$")
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")

FORMAT_CHECKER = FormatChecker()
SUPPORTED_FORMATS = (
    "uuid",
    "uuid|null",
    "uuid|empty",
    "uuid|empty|null",
    "uuid|null|empty",
    "url",
    "url|null",
    "url|null|empty",
    "url|empty|null",
    "host",
    "host|url",
    "host|url|null",
    "date",
    "date-time",
    "date-time|null",
    "email",
    "filename",
    "sha256",
    "md5",
    "md5|empty|null",
    "rrule",
    "binary",
    "cvss",
    "path_match",
    "search",
    "tag",
    "header",
    "string",
    "generic|null",
    "any|null",
)


class SwaggerSchemaConverter:
    """Convert the Swagger schema subset used by Acunetix into strict input schemas."""

    def __init__(self, definitions: dict[str, dict[str, Any]]) -> None:
        self._definitions = definitions

    def convert_for_input(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Convert a schema fragment into the stricter JSON Schema used by MCP."""
        converted = self._convert(schema, stack=[])
        return converted

    def _convert(self, schema: dict[str, Any], stack: list[str]) -> dict[str, Any]:
        """Recursively inline refs and normalize objects, arrays, and formats."""
        if "$ref" in schema:
            ref_name = schema["$ref"].rsplit("/", 1)[-1]
            if ref_name in stack:
                return {"type": "object", "additionalProperties": False}
            resolved = deepcopy(self._definitions[ref_name])
            return self._convert(resolved, stack + [ref_name])

        if "allOf" in schema:
            return self._merge_all_of(schema, stack)

        converted: dict[str, Any] = {}
        schema_type = schema.get("type")
        if schema_type is None:
            if "properties" in schema or "additionalProperties" in schema:
                schema_type = "object"
            elif "items" in schema:
                schema_type = "array"

        if schema_type is not None:
            converted["type"] = self._json_schema_type(schema_type, schema.get("format"))

        for keyword in (
            "description",
            "enum",
            "default",
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "minLength",
            "maxLength",
            "minItems",
            "maxItems",
            "uniqueItems",
            "pattern",
        ):
            if keyword in schema:
                converted[keyword] = deepcopy(schema[keyword])

        if "format" in schema and schema.get("type") == "string":
            converted["format"] = schema["format"]

        if schema_type == "object" or ("properties" in schema and "type" not in schema):
            properties: dict[str, Any] = {}
            required = []
            for name, property_schema in schema.get("properties", {}).items():
                if property_schema.get("readOnly"):
                    continue
                properties[name] = self._convert(property_schema, stack)
            for required_name in schema.get("required", []):
                if required_name in properties:
                    required.append(required_name)
            converted["type"] = "object"
            converted["properties"] = properties
            converted["additionalProperties"] = self._convert_additional_properties(
                schema.get("additionalProperties", False),
                stack,
            )
            if required:
                converted["required"] = required

        if schema_type == "array":
            converted["items"] = self._convert(schema.get("items", {}), stack)

        return converted

    def _merge_all_of(self, schema: dict[str, Any], stack: list[str]) -> dict[str, Any]:
        """Flatten Swagger `allOf` compositions into a single merged schema."""
        merged: dict[str, Any] = {"type": "object", "properties": {}, "additionalProperties": False}
        required: list[str] = []
        for subschema in schema.get("allOf", []):
            converted = self._convert(subschema, stack)
            if converted.get("type") == "object":
                merged["properties"].update(converted.get("properties", {}))
                if converted.get("additionalProperties", False) is not False:
                    merged["additionalProperties"] = converted["additionalProperties"]
                required.extend(converted.get("required", []))
                if "description" in converted and "description" not in merged:
                    merged["description"] = converted["description"]
            else:
                merged.update(converted)
        if required:
            merged["required"] = sorted(set(required))
        for key, value in schema.items():
            if key in {"allOf", "properties", "required", "additionalProperties", "type"}:
                continue
            if key == "description":
                merged[key] = value
            elif key == "format":
                merged[key] = value
        return merged

    def _convert_additional_properties(self, value: Any, stack: list[str]) -> Any:
        """Preserve object maps while defaulting ordinary objects to closed schemas."""
        if isinstance(value, dict):
            return self._convert(value, stack)
        return bool(value)

    @staticmethod
    def _json_schema_type(schema_type: str, schema_format: str | None) -> str | list[str]:
        if schema_format and "null" in schema_format.split("|"):
            return [schema_type, "null"]
        return schema_type


def validate_input(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate tool arguments and raise a structured error on failure."""
    validator = Draft7Validator(schema, format_checker=FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(payload), key=_validation_sort_key)
    if not errors:
        return
    messages = [_format_validation_error(error) for error in errors]
    raise InputValidationError("Invalid tool arguments.", messages)


def _validation_sort_key(error: JsonSchemaValidationError) -> tuple[int, str]:
    """Keep validation errors stable and readable for clients."""
    return (len(list(error.absolute_path)), ".".join(str(part) for part in error.absolute_path))


def _format_validation_error(error: JsonSchemaValidationError) -> str:
    """Convert jsonschema errors into compact path-prefixed messages."""
    path = ".".join(str(part) for part in error.absolute_path)
    if path:
        return f"{path}: {error.message}"
    return error.message


def _check_multi_format(value: object, primary_format: str) -> bool:
    """Support Acunetix format variants such as `uuid|null` and `url|empty|null`."""
    tokens = primary_format.split("|")
    if value is None:
        return "null" in tokens
    if not isinstance(value, str):
        return False
    if value == "":
        return "empty" in tokens
    if _check_string_format(value, primary_format):
        return True
    for token in tokens:
        if token in {"null", "empty", "generic", "any"}:
            continue
        if _check_string_format(value, token):
            return True
    return False


def _check_string_format(value: str, fmt: str) -> bool:
    """Validate the subset of string formats that matter for tool inputs."""
    if fmt in {"generic", "any", "binary", "cvss", "path_match", "search", "tag", "header", "string", "rrule"}:
        return True
    if fmt == "uuid":
        return bool(UUID_PATTERN.fullmatch(value))
    if fmt == "url":
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    if fmt == "host":
        return _is_valid_host(value)
    if fmt == "host|url":
        return _is_valid_host(value) or _check_string_format(value, "url")
    if fmt == "date":
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False
    if fmt == "date-time":
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False
    if fmt == "email":
        local, _, domain = value.partition("@")
        return bool(local) and _is_valid_host(domain)
    if fmt == "filename":
        return "/" not in value and "\\" not in value and value not in {".", ".."} and bool(value)
    if fmt == "sha256":
        return bool(SHA256_PATTERN.fullmatch(value))
    if fmt == "md5":
        return bool(MD5_PATTERN.fullmatch(value))
    return True


def _is_valid_host(value: str) -> bool:
    """Accept either an IP literal or a hostname-like label sequence."""
    try:
        ip_address(value)
        return True
    except ValueError:
        return bool(HOSTNAME_PATTERN.fullmatch(value))


for supported_format in SUPPORTED_FORMATS:
    FORMAT_CHECKER.checks(supported_format)(
        lambda value, supported_format=supported_format: _check_multi_format(value, supported_format)
    )

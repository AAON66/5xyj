"""Generate Markdown documentation from an OpenAPI schema dict."""
from __future__ import annotations

from typing import Any


def generate_markdown_from_openapi(openapi_schema: dict[str, Any]) -> str:
    """Walk an OpenAPI 3.x JSON schema and produce Markdown documentation.

    Groups endpoints by tag, includes method, path, summary, description,
    parameters, request body schema, and response schema.
    """
    lines: list[str] = []

    info = openapi_schema.get("info", {})
    title = info.get("title", "API Documentation")
    description = info.get("description") or info.get("summary", "")
    version = info.get("version", "")

    lines.append(f"# {title}")
    if version:
        lines.append(f"\n**Version:** {version}")
    if description:
        lines.append(f"\n{description}")
    lines.append("")

    # Collect endpoints grouped by tag
    paths = openapi_schema.get("paths", {})
    tag_groups: dict[str, list[dict[str, Any]]] = {}

    for path, path_item in paths.items():
        for method in ("get", "post", "put", "patch", "delete"):
            operation = path_item.get(method)
            if operation is None:
                continue
            tags = operation.get("tags", ["Other"])
            for tag in tags:
                tag_groups.setdefault(tag, []).append({
                    "method": method.upper(),
                    "path": path,
                    "operation": operation,
                })

    # Render each tag group
    for tag_name, endpoints in tag_groups.items():
        lines.append(f"## {tag_name}")
        lines.append("")
        for ep in endpoints:
            op = ep["operation"]
            summary = op.get("summary", "")
            desc = op.get("description", "")
            lines.append(f"### {ep['method']} `{ep['path']}`")
            if summary:
                lines.append(f"\n**{summary}**")
            if desc:
                lines.append(f"\n{desc}")
            lines.append("")

            # Parameters
            params = op.get("parameters", [])
            if params:
                lines.append("**Parameters:**")
                lines.append("")
                lines.append("| Name | In | Type | Required | Description |")
                lines.append("|------|----|------|----------|-------------|")
                for p in params:
                    schema = p.get("schema", {})
                    ptype = schema.get("type", "-")
                    required = "Yes" if p.get("required") else "No"
                    pdesc = p.get("description", "-")
                    lines.append(f"| {p.get('name', '-')} | {p.get('in', '-')} | {ptype} | {required} | {pdesc} |")
                lines.append("")

            # Request body
            request_body = op.get("requestBody")
            if request_body:
                lines.append("**Request Body:**")
                content = request_body.get("content", {})
                for content_type, media in content.items():
                    lines.append(f"\n- Content-Type: `{content_type}`")
                    schema = media.get("schema", {})
                    _render_schema(lines, schema, openapi_schema)
                lines.append("")

            # Responses
            responses = op.get("responses", {})
            if responses:
                lines.append("**Responses:**")
                lines.append("")
                for status_code, resp in responses.items():
                    resp_desc = resp.get("description", "")
                    lines.append(f"- **{status_code}**: {resp_desc}")
                lines.append("")

    return "\n".join(lines)


def _render_schema(lines: list[str], schema: dict[str, Any], root: dict[str, Any], indent: int = 0) -> None:
    """Render a simplified view of a JSON schema."""
    if "$ref" in schema:
        ref = schema["$ref"]
        resolved = _resolve_ref(ref, root)
        if resolved:
            title = resolved.get("title", ref.split("/")[-1])
            lines.append(f"{'  ' * indent}- Schema: `{title}`")
            props = resolved.get("properties", {})
            required_fields = set(resolved.get("required", []))
            for prop_name, prop_schema in props.items():
                ptype = prop_schema.get("type", "object")
                req_mark = " (required)" if prop_name in required_fields else ""
                lines.append(f"{'  ' * (indent + 1)}- `{prop_name}`: {ptype}{req_mark}")
        return

    schema_type = schema.get("type", "object")
    if schema_type == "array" and "items" in schema:
        lines.append(f"{'  ' * indent}- Type: array")
        _render_schema(lines, schema["items"], root, indent + 1)
    elif "properties" in schema:
        props = schema.get("properties", {})
        for prop_name, prop_schema in props.items():
            ptype = prop_schema.get("type", "object")
            lines.append(f"{'  ' * indent}- `{prop_name}`: {ptype}")


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve a $ref pointer like #/components/schemas/Foo."""
    if not ref.startswith("#/"):
        return None
    parts = ref[2:].split("/")
    current: Any = root
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current if isinstance(current, dict) else None

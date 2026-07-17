"""Canonical skill_id <-> provider tool name adaptation at the transport boundary."""

from __future__ import annotations

import copy
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("janus_backend")

_GEMINI_MANUAL_INBOUND: Dict[str, str] = {
    "system_routing": "system.routing",
    "system_local_business": "system.local_business",
    "system_country_info": "system.country_info",
    "system_websearch": "system.websearch",
    "system_wikipedia_summary": "system.wikipedia_summary",
    "system_price_comparison": "system.price_comparison",
    "system_create_pdf": "system.create_pdf",
    "system_generate_image": "system.generate_image",
    "system_grant_permission": "system.grant_permission",
    "system_revoke_permission": "system.revoke_permission",
    "system_weather": "system.weather",
    "system_scrape_website": "system.scrape_website",
    "system_save_mp3": "system.save_mp3",
    "system_rss_news": "system.rss_news",
}


def get_tool_call_adapter(provider: str) -> "ToolCallAdapter":
    return ToolCallAdapter(provider)


class ToolCallAdapter:
    """Provider-bound adapter for outbound naming, inbound restoration, and schema cleaning."""

    def __init__(self, provider: str):
        self.provider = str(provider or "").strip().lower()

    def outbound_name(self, canonical_skill_id: str) -> str:
        """Map canonical dotted skill_id to provider-safe function name."""
        canonical = str(canonical_skill_id or "").strip()
        if not canonical:
            return canonical
        if self.provider in {"openai", "openrouter", "ollama"}:
            return canonical.replace(".", "_")
        if self.provider == "gemini":
            return self._sanitize_gemini_outbound_name(canonical)
        return canonical

    def inbound_name(self, provider_name: str) -> str:
        """Map provider function name back to canonical dotted skill_id."""
        requested = str(provider_name or "").strip()
        if not requested:
            return requested

        if self.provider == "gemini" and requested in _GEMINI_MANUAL_INBOUND:
            mapped = _GEMINI_MANUAL_INBOUND[requested]
            logger.info("GEMINI-NAME-MAP: manual override '%s' -> '%s'", requested, mapped)
            return mapped

        # A dotted name is already in Janus' canonical internal format.
        if "." in requested:
            return requested

        if "." not in requested and "_" in requested:
            from backend.services.tool_manager import tool_manager

            for skill_id in tool_manager.get_skill_mapping().values():
                sid = str(skill_id or "").strip()
                if sid and sid.replace(".", "_") == requested:
                    return sid

        if self.provider == "gemini":
            try:
                from backend.services.skill_router import skill_router
                from backend.services.tool_manager import tool_manager

                resolved_name = skill_router.resolve_tool_name(requested)
                canonical_name = tool_manager.get_skill_id(resolved_name)
                if canonical_name and canonical_name != requested:
                    logger.info(
                        "GEMINI-NAME-MAP: provider='%s' -> resolved='%s' -> canonical='%s'",
                        requested,
                        resolved_name,
                        canonical_name,
                    )
                return canonical_name or resolved_name or requested
            except Exception as exc:
                logger.warning(
                    "GEMINI-NAME-MAP: could not resolve provider name '%s'; using raw name. reason=%s",
                    requested,
                    exc,
                )
                return requested

        from backend.services.tool_manager import tool_manager

        canonical = str(tool_manager.get_skill_id(requested) or "").strip()
        return canonical or requested

    def outbound_name_for_history(self, tool_name: str) -> str:
        """Resolve a history/tool message name to the provider-safe function name."""
        requested = str(tool_name or "").strip()
        if self.provider != "gemini":
            return self.outbound_name(requested)
        if "." in requested:
            return self.outbound_name(requested)
        try:
            from backend.services.skill_router import skill_router
            from backend.services.tool_manager import tool_manager

            resolved_name = skill_router.resolve_tool_name(requested)
            canonical_name = tool_manager.get_skill_id(resolved_name)
            api_name = self._sanitize_gemini_outbound_name(canonical_name or resolved_name or requested)
            logger.debug(
                "GEMINI-NAME-MAP: history tool='%s' -> resolved='%s' -> api='%s'",
                requested,
                resolved_name,
                api_name,
            )
            return api_name
        except Exception:
            return self._sanitize_gemini_outbound_name(requested or "unknown_function")

    @staticmethod
    def _sanitize_gemini_outbound_name(name: str) -> str:
        if not name or not isinstance(name, str) or name == "None":
            return "unknown_tool"
        safe = name.replace(".", "_").replace("-", "_")
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", safe)
        return safe or "unknown_tool"

    def sanitize_tool_schema(self, schema: Any) -> Dict[str, Any]:
        if self.provider == "gemini":
            return self._sanitize_gemini_tool_schema(schema)
        if self.provider in {"openai", "openrouter", "ollama"}:
            return self._sanitize_openai_tool_schema(schema)
        if isinstance(schema, dict):
            return schema
        return {"type": "object", "properties": {}}

    def remove_additional_properties(self, schema: Any) -> Any:
        if isinstance(schema, dict):
            return {
                key: self.remove_additional_properties(value)
                for key, value in schema.items()
                if key != "additionalProperties"
            }
        if isinstance(schema, list):
            return [self.remove_additional_properties(item) for item in schema]
        return schema

    def convert_tools_to_openai_format(self, tools: List[Any]) -> List[Dict[str, Any]]:
        openai_tools: List[Dict[str, Any]] = []
        seen_names: set[str] = set()
        for tool in tools:
            try:
                name = getattr(tool, "name", tool.get("name") if isinstance(tool, dict) else "unknown")
                desc = getattr(tool, "description", tool.get("description") if isinstance(tool, dict) else "")
                args_schema_model = getattr(tool, "args_schema", None)
                schema: Dict[str, Any] = {"type": "object", "properties": {}}
                if isinstance(tool, dict) and isinstance(tool.get("parameters"), dict):
                    schema = tool.get("parameters")

                if args_schema_model:
                    if hasattr(args_schema_model, "model_json_schema"):
                        schema = args_schema_model.model_json_schema()
                    elif hasattr(args_schema_model, "schema"):
                        schema = args_schema_model.schema()

                raw_name = str(name)
                openai_safe_name = self.outbound_name(raw_name)
                if openai_safe_name in seen_names:
                    logger.debug("OpenAI: Skipping duplicate tool name '%s'", openai_safe_name)
                    continue
                seen_names.add(openai_safe_name)
                safe_schema = self.sanitize_tool_schema(schema)
                openai_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": openai_safe_name,
                            "description": desc,
                            "parameters": safe_schema,
                        },
                    }
                )
            except Exception as exc:
                logger.error(
                    "Überspringe Tool %s wegen Konvertierungsfehler: %s",
                    getattr(tool, "name", "unknown"),
                    exc,
                )
                continue

        if len(openai_tools) > 128:
            logger.warning(
                "[OPENAI_LIMIT] Truncating %s tools to 128 (OpenAI API limit)",
                len(openai_tools),
            )
            openai_tools = openai_tools[:128]
        return openai_tools

    def convert_tools_to_gemini_format(self, tools: List[Any]) -> List[Dict[str, Any]]:
        gemini_tools: List[Dict[str, Any]] = []
        seen_names: set[str] = set()
        for tool in tools:
            try:
                func_def = None
                if isinstance(tool, dict) and "function" in tool and isinstance(tool["function"], dict):
                    func_def = tool["function"]

                if func_def:
                    name = func_def.get("name")
                    desc = func_def.get("description", "")
                    raw_schema = func_def.get("parameters", {"type": "object", "properties": {}})
                else:
                    name = getattr(tool, "name", tool.get("name") if isinstance(tool, dict) else "unknown")
                    desc = getattr(tool, "description", tool.get("description") if isinstance(tool, dict) else "")
                    raw_schema = {"type": "object", "properties": {}}
                    if isinstance(tool, dict) and isinstance(tool.get("parameters"), dict):
                        raw_schema = tool.get("parameters")

                args_schema_model = getattr(tool, "args_schema", None) if not func_def else None
                if args_schema_model:
                    if hasattr(args_schema_model, "model_json_schema"):
                        try:
                            raw_schema = args_schema_model.model_json_schema(mode="serialization")
                        except TypeError:
                            raw_schema = args_schema_model.model_json_schema()
                    elif hasattr(args_schema_model, "schema"):
                        raw_schema = args_schema_model.schema()

                safe_name = self.outbound_name(str(name or ""))
                if name != safe_name:
                    logger.info("[GEMINI-SANITIZE] Tool name '%s' -> '%s'", name, safe_name)

                if not desc or not isinstance(desc, str) or desc == "None":
                    desc = f"Tool {safe_name}"

                if safe_name in seen_names:
                    logger.debug("Gemini: Skipping duplicate tool name '%s'", safe_name)
                    continue
                seen_names.add(safe_name)

                raw_schema_clean = self.remove_additional_properties(raw_schema)
                try:
                    final_schema = self.sanitize_tool_schema(raw_schema_clean)
                except Exception as schema_exc:
                    logger.warning(
                        "Gemini schema sanitization failed for tool '%s': %s. Falling back to empty object schema.",
                        safe_name,
                        schema_exc,
                    )
                    final_schema = {"type": "object", "properties": {}}

                gemini_tools.append(
                    {
                        "function_declarations": [
                            {
                                "name": safe_name,
                                "description": desc,
                                "parameters": final_schema,
                            }
                        ]
                    }
                )
            except Exception as exc:
                logger.error("Gemini Konvertierungs-Fehler: %s", exc)
                continue
        return gemini_tools

    def adapt_openai_stream_params(self, params: Dict[str, Any]) -> None:
        """Normalize tool names and preserve forced-tool behavior for OpenAI stream calls."""
        if "tools" in params:
            for tool in params["tools"]:
                if isinstance(tool, dict) and "function" in tool and "name" in tool["function"]:
                    original_name = tool["function"]["name"]
                    normalized_name = self.outbound_name(original_name)
                    if original_name != normalized_name:
                        logger.debug(
                            "[OPENAI_SHIM] Normalizing tool name from '%s' to '%s'",
                            original_name,
                            normalized_name,
                        )
                        tool["function"]["name"] = normalized_name

        if (
            "tool_choice" in params
            and isinstance(params["tool_choice"], dict)
            and "function" in params["tool_choice"]
            and "name" in params["tool_choice"]["function"]
        ):
            original_name = params["tool_choice"]["function"]["name"]
            normalized_name = self.outbound_name(original_name)
            if original_name != normalized_name:
                logger.debug(
                    "[OPENAI_SHIM] Normalizing tool_choice from '%s' to '%s'",
                    original_name,
                    normalized_name,
                )
                params["tool_choice"]["function"]["name"] = normalized_name

        if (
            "tool_choice" in params
            and isinstance(params["tool_choice"], dict)
            and "function" in params["tool_choice"]
            and "name" in params["tool_choice"]["function"]
        ):
            forced_tool_name = params["tool_choice"]["function"]["name"]
            tool_names = [
                tool.get("function", {}).get("name")
                for tool in params.get("tools", [])
                if isinstance(tool, dict)
            ]
            if forced_tool_name not in tool_names:
                from backend.services.skill_router import skill_router

                try:
                    tool_def = skill_router.get_tool_definition(forced_tool_name)
                    tool_obj = {
                        "type": "function",
                        "function": {
                            "name": forced_tool_name,
                            "description": tool_def.description or "",
                            "parameters": tool_def.parameters.model_dump()
                            if hasattr(tool_def, "parameters")
                            else {},
                        },
                    }
                    if "tools" not in params:
                        params["tools"] = []
                    params["tools"].append(tool_obj)
                    logger.warning(
                        "[OPENAI_SHIM] Re-injecting missing forced tool definition: %s",
                        forced_tool_name,
                    )
                except Exception as exc:
                    logger.error(
                        "[OPENAI_SHIM] Failed to re-inject forced tool %s: %s",
                        forced_tool_name,
                        exc,
                    )

    def _resolve_local_json_ref(self, schema_root: Dict[str, Any], ref: str) -> Dict[str, Any]:
        if not isinstance(ref, str) or not ref.startswith("#/"):
            raise ValueError(f"Unsupported JSON ref: {ref}")

        current: Any = schema_root
        for token in ref[2:].split("/"):
            key = token.replace("~1", "/").replace("~0", "~")
            if not isinstance(current, dict) or key not in current:
                raise ValueError(f"Unresolvable JSON ref: {ref}")
            current = current[key]

        if not isinstance(current, dict):
            raise ValueError(f"Resolved JSON ref is not an object: {ref}")
        return copy.deepcopy(current)

    def _resolve_schema_refs(self, raw_schema: Dict[str, Any]) -> Dict[str, Any]:
        schema_root = copy.deepcopy(raw_schema or {})

        def _walk(node: Any, depth: int = 0, seen_refs: Optional[List[str]] = None) -> Any:
            if depth > 30:
                raise ValueError("Schema reference depth limit exceeded")
            if seen_refs is None:
                seen_refs = []

            if isinstance(node, list):
                return [_walk(item, depth + 1, seen_refs) for item in node]

            if not isinstance(node, dict):
                return node

            if "$ref" in node:
                ref = node.get("$ref")
                if ref in seen_refs:
                    raise ValueError(f"Circular JSON ref detected: {ref}")

                resolved = self._resolve_local_json_ref(schema_root, ref)
                sibling_overrides = {k: v for k, v in node.items() if k != "$ref"}
                merged = {**resolved, **sibling_overrides}
                return _walk(merged, depth + 1, seen_refs + [ref])

            cleaned = {}
            for key, value in node.items():
                if key in {"$defs", "definitions"}:
                    continue
                cleaned[key] = _walk(value, depth + 1, seen_refs)
            return cleaned

        return _walk(schema_root)

    def _clean_gemini_schema(self, obj: Any) -> Any:
        if not isinstance(obj, dict):
            if isinstance(obj, list):
                return [self._clean_gemini_schema(item) for item in obj]
            return obj

        forbidden = [
            "title",
            "default",
            "anyOf",
            "allOf",
            "oneOf",
            "pattern",
            "format",
            "minLength",
            "maxLength",
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "multipleOf",
            "minItems",
            "maxItems",
            "uniqueItems",
            "minProperties",
            "maxProperties",
            "examples",
            "description_internal",
            "$defs",
            "definitions",
            "$ref",
        ]
        new_obj = {k: self._clean_gemini_schema(v) for k, v in obj.items() if k not in forbidden}

        if "anyOf" in obj or "oneOf" in obj:
            options = obj.get("anyOf") or obj.get("oneOf")
            valid_types = [t for t in options if isinstance(t, dict) and t.get("type") != "null"]
            if valid_types:
                new_obj.update(self._clean_gemini_schema(valid_types[0]))
        if "const" in obj:
            new_obj["enum"] = [obj["const"]]
            if "const" in new_obj:
                del new_obj["const"]

        if "properties" in new_obj and "required" in new_obj:
            valid_properties = set(new_obj["properties"].keys())
            synced_required = [req for req in new_obj["required"] if req in valid_properties]
            if synced_required:
                new_obj["required"] = synced_required
            else:
                del new_obj["required"]

        return new_obj

    def _sanitize_gemini_tool_schema(self, raw_schema: Dict[str, Any]) -> Dict[str, Any]:
        resolved_schema = self._resolve_schema_refs(raw_schema)
        final_schema = self._clean_gemini_schema(resolved_schema)

        if not isinstance(final_schema, dict):
            raise ValueError("Sanitized schema is not an object")

        if final_schema.get("type") != "object":
            final_schema["type"] = "object"
        if not isinstance(final_schema.get("properties"), dict):
            final_schema["properties"] = {}

        return final_schema

    def _sanitize_openai_tool_schema(self, schema: Any) -> Dict[str, Any]:
        if not isinstance(schema, dict):
            return {"type": "object", "properties": {}}

        def _sanitize_node(node: Any) -> Any:
            if isinstance(node, dict):
                cleaned = {
                    key: _sanitize_node(value)
                    for key, value in node.items()
                    if key
                    not in {
                        "title",
                        "examples",
                        "example",
                        "default",
                        "$defs",
                        "definitions",
                        "strict",
                    }
                }

                if "anyOf" in cleaned or "oneOf" in cleaned:
                    variants = cleaned.get("anyOf") or cleaned.get("oneOf") or []
                    if isinstance(variants, list):
                        non_null_variants = [
                            variant
                            for variant in variants
                            if not (isinstance(variant, dict) and variant.get("type") == "null")
                        ]
                        if len(non_null_variants) == 1 and isinstance(non_null_variants[0], dict):
                            merged = dict(non_null_variants[0])
                            if "description" in cleaned and "description" not in merged:
                                merged["description"] = cleaned["description"]
                            cleaned = _sanitize_node(merged)
                        else:
                            cleaned = {"type": "string", "description": cleaned.get("description", "")}

                if cleaned.get("type") == "object":
                    props = cleaned.get("properties")
                    if not isinstance(props, dict):
                        cleaned["properties"] = {}
                    req = cleaned.get("required")
                    if not isinstance(req, list):
                        cleaned["required"] = []

                return cleaned
            if isinstance(node, list):
                return [_sanitize_node(item) for item in node]
            return node

        sanitized = _sanitize_node(schema)
        if not isinstance(sanitized, dict):
            return {"type": "object", "properties": {}}
        if sanitized.get("type") != "object":
            sanitized = {"type": "object", "properties": dict(sanitized.get("properties") or {})}
        sanitized.setdefault("properties", {})
        if not isinstance(sanitized.get("properties"), dict):
            sanitized["properties"] = {}
        if "required" in sanitized and not isinstance(sanitized.get("required"), list):
            sanitized["required"] = []
        return sanitized

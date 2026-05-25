from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_dotenv_value(name: str) -> tuple[str | None, str]:
    for env_path in (ROOT / ".env", ROOT / ".env.local", ROOT / "backend" / ".env", ROOT / "backend" / ".env.local"):
        if not env_path.exists():
            continue
        try:
            lines = env_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = env_path.read_text(encoding="utf-8-sig").splitlines()
        for line in lines:
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'") or None, str(env_path)
    return None, ""


def _load_keyring_value(provider: str) -> tuple[str | None, str]:
    try:
        import keyring
    except Exception:
        return None, ""
    try:
        return keyring.get_password("Janus-Projekt", provider) or None, f"Windows keyring: Janus-Projekt/{provider}"
    except Exception:
        return None, ""


def _resolve_gemini_key(explicit: str | None) -> tuple[str, str]:
    if explicit:
        return explicit, "--api-key"
    key, source = _load_keyring_value("gemini")
    if key:
        return key, source
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        key = os.getenv(name)
        if key:
            return key, f"process env: {name}"
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        key, source = _load_dotenv_value(name)
        if key:
            return key, f"{source}:{name}"
    raise RuntimeError("Kein Gemini API-Key gefunden.")


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _to_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump(exclude_none=True)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return {}


def _summarize_response(response: Any) -> dict[str, Any]:
    candidates = _get_attr(response, "candidates", []) or []
    first = candidates[0] if candidates else None
    metadata = _get_attr(first, "grounding_metadata", None) or _get_attr(first, "groundingMetadata", None)
    metadata_dict = _to_dict(metadata)
    chunks = _get_attr(metadata, "grounding_chunks", None) or metadata_dict.get("grounding_chunks") or metadata_dict.get("groundingChunks") or []
    supports = _get_attr(metadata, "grounding_supports", None) or metadata_dict.get("grounding_supports") or metadata_dict.get("groundingSupports") or []
    queries = _get_attr(metadata, "web_search_queries", None) or metadata_dict.get("web_search_queries") or metadata_dict.get("webSearchQueries") or []
    chunk_rows = []
    for chunk in chunks[:8]:
        web = _get_attr(chunk, "web", None)
        web_dict = _to_dict(web)
        chunk_rows.append(
            {
                "title": _get_attr(web, "title", None) or web_dict.get("title", ""),
                "uri": _get_attr(web, "uri", None) or web_dict.get("uri", ""),
            }
        )
    return {
        "text": str(_get_attr(response, "text", "") or "")[:800],
        "candidate_count": len(candidates),
        "finish_reason": str(_get_attr(first, "finish_reason", "") or _get_attr(first, "finishReason", "") or ""),
        "metadata_keys": sorted(metadata_dict.keys()),
        "web_search_queries": queries,
        "grounding_chunks_count": len(chunks),
        "grounding_supports_count": len(supports),
        "grounding_chunks": chunk_rows,
    }


def _safe_raw_shape(response: Any) -> dict[str, Any]:
    response_dict = _to_dict(response)
    candidates = response_dict.get("candidates") if isinstance(response_dict.get("candidates"), list) else []
    first = candidates[0] if candidates and isinstance(candidates[0], dict) else {}
    return {
        "response_keys": sorted(response_dict.keys()),
        "candidate_keys": sorted(first.keys()),
        "candidate_preview": {
            key: first.get(key)
            for key in sorted(first.keys())
            if key not in {"content"}
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Gemini google-genai SDK search grounding.")
    parser.add_argument("--model", default="gemini-3-flash-preview")
    parser.add_argument("--prompt", default="was gibt es neues zu Microsoft?")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--max-output-tokens", type=int, default=1024)
    parser.add_argument("--dict-config", action="store_true", help="Use raw cookbook-style dict config instead of typed config.")
    parser.add_argument("--dump-raw-keys", action="store_true", help="Print safe response/candidate keys for SDK field debugging.")
    parser.add_argument("--api-version", default="", help="Optional google-genai API version, e.g. v1beta.")
    args = parser.parse_args()

    api_key, key_source = _resolve_gemini_key(args.api_key)
    print(f"model: {args.model}")
    print(f"key source: {key_source}")
    print(f"prompt: {args.prompt}")

    from google import genai
    from google.genai import types

    if args.api_version:
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version=args.api_version))
    else:
        client = genai.Client(api_key=api_key)
    if args.dict_config:
        config = {
            "tools": [{"google_search": {}}],
            "temperature": 0.1,
            "max_output_tokens": args.max_output_tokens,
        }
    else:
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        config = types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature=0.1,
            max_output_tokens=args.max_output_tokens,
        )
    response = client.models.generate_content(
        model=args.model,
        contents=args.prompt,
        config=config,
    )

    summary = _summarize_response(response)
    if args.dump_raw_keys:
        summary["raw_shape"] = _safe_raw_shape(response)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

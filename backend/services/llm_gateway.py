from __future__ import annotations

import asyncio
import logging
import threading
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from backend.services.tool_manager import tool_manager
from backend.services.ops_kill_switches import provider_access_decision
from backend.utils.config_loader import load_model_catalog
from backend.llm_providers.shared.utils import _normalize_allowed_skill_ids

if TYPE_CHECKING:
    from backend.services.tool_executor import ToolExecutor

logger = logging.getLogger("janus_backend")


def _guard_llm_provider_silo(provider: str, model_id: str) -> Optional[Dict[str, Any]]:
    """
    BYOK: block cross-cloud LLM calls while a chat silo is active; block obvious
    provider/model catalog mismatches for openai/gemini.
    """
    from backend.services.llm_silo_context import get_active_llm_silo, normalize_llm_silo_provider

    req = normalize_llm_silo_provider(provider)
    raw = str(provider or "").strip().lower()
    if not raw:
        return {
            "content": "",
            "text": "",
            "error": "Unsupported or empty LLM provider",
            "error_code": "UNSUPPORTED_PROVIDER",
        }
    # Unknown / future provider keys: skip openai↔gemini silo rules only.
    if req is None:
        return None

    active = get_active_llm_silo()
    if active in ("openai", "gemini") and req in ("openai", "gemini") and active != req:
        msg = (
            f"PROVIDER-SILO: active chat provider is {active!r}, blocked LLM call for "
            f"provider={req!r} (model={model_id!r})."
        )
        logger.error(msg)
        return {
            "content": "",
            "text": "",
            "error": msg,
            "error_code": "PROVIDER_SILO_VIOLATION",
        }

    if model_id and req in ("openai", "gemini"):
        catalog = get_cached_model_catalog()
        info = catalog.get(str(model_id))
        if isinstance(info, dict):
            mp = normalize_llm_silo_provider(info.get("provider"))
            if mp in ("openai", "gemini") and mp != req:
                msg = (
                    f"PROVIDER-SILO: call_llm provider={req!r} does not match catalog provider={mp!r} "
                    f"for model={model_id!r}."
                )
                logger.error(msg)
                return {
                    "content": "",
                    "text": "",
                    "error": msg,
                    "error_code": "PROVIDER_MODEL_MISMATCH",
                }
    return None

# Provider-Gateway-Silos: schwere Module (Gemini/OpenAI/Ollama Gateway) erst beim ersten Chat-Aufruf laden.
_gateway_silos: Optional[Dict[str, Any]] = None
_gateway_lock = threading.Lock()


def _ensure_gateway_silos() -> Dict[str, Any]:
    global _gateway_silos
    if _gateway_silos is not None:
        return _gateway_silos
    with _gateway_lock:
        if _gateway_silos is not None:
            return _gateway_silos
        from backend.llm_providers.gemini.gateway import GeminiGateway
        from backend.llm_providers.openai.gateway import OpenAIGateway
        from backend.llm_providers.ollama.gateway import OllamaGateway

        _gateway_silos = {
            "gemini": GeminiGateway(),
            "openai": OpenAIGateway(),
            "ollama": OllamaGateway(),
        }
        return _gateway_silos

# --- CACHING FÜR MODELLKATALOG ---
@lru_cache(maxsize=1)
def get_cached_model_catalog():
    """Lädt den Modellkatalog und cacht das Ergebnis in-memory."""
    return load_model_catalog()


async def reason_and_respond(
    provider: str, model: str, api_key: str, chat_history: List[Dict],
    context_manager: Any, db: Any, user_prompt: str, chat_id: int,
    tool_executor: ToolExecutor, tools_override: Optional[List[Dict]] = None,
    disable_tools: bool = False, image_data: Optional[str] = None,
    allowed_skill_ids: Optional[List[str]] = None,
    background_tasks: Any = None, max_tool_rounds: int = 5, bypass_policy: bool = False, **kwargs
) -> Dict[str, Any]:
    """
    Zentraler Einstiegspunkt für die LLM-Orchestrierung.
    Fungiert als Gateway-Router und delegiert an providerspezifische Silos.
    """
    if not tool_manager.get_all_tools():
        from backend import tool_registry as registry
        registry.register_all_tools()

    # 1. Bestimme das Silo
    provider_key = str(provider).lower()
    provider_gate = provider_access_decision(provider_key)
    if provider_gate.disabled:
        logger.warning("OPS-KILL-SWITCH: provider access blocked for provider=%s", provider_key)
        return {
            "content": provider_gate.message,
            "text": provider_gate.message,
            "error": provider_gate.message,
            "error_code": provider_gate.code,
            "metadata": {"ops_kill_switch": True, "switch": provider_gate.switch},
        }
    selected_silo = _ensure_gateway_silos().get(provider_key)
    if not selected_silo:
        logger.error(f"Provider {provider_key} nicht unterstützt.")
        raise ValueError(f"Provider {provider_key} nicht unterstützt.")

    # 2. Bestimme effektive Skills (Router-Logik)
    effective_allowed_skill_ids: Optional[List[str]] = None
    if allowed_skill_ids is not None:
        effective_allowed_skill_ids = _normalize_allowed_skill_ids(allowed_skill_ids)
    elif not disable_tools and str(user_prompt or "").strip():
        from backend.services.skill_selector import SkillSelector

        selector = SkillSelector()
        selected_skills = selector.get_relevant_skills(user_prompt, top_k=10)  # 💎 BACKLOG-034: Erhöhe top_k auf 10 um system.routing nicht zu filtern
        available_skill_ids = {
            str(tool_manager.get_skill_id(getattr(tool, "name", "") or "") or "").strip()
            for tool in tool_manager.get_all_tools().values()
        }
        normalized_selected = [
            skill_id for skill_id in _normalize_allowed_skill_ids(selected_skills)
            if skill_id in available_skill_ids
        ]
        if normalized_selected:
            effective_allowed_skill_ids = normalized_selected[:10]  # 💎 BACKLOG-034: Erhöhe Limit auf 10
            if "system.websearch" in available_skill_ids and "system.websearch" not in effective_allowed_skill_ids and len(effective_allowed_skill_ids) < 10:
                effective_allowed_skill_ids.append("system.websearch")
        else:
            effective_allowed_skill_ids = ["system.websearch"]

    # 3. Delegiere Orchestrierung an das Silo
    logger.info(f"GATEWAY-ROUTER: Delegiere an {provider_key}-Silo.")

    # DIAMOND FIX: Listen-/Ranking-Anfragen benötigen mehr Such-Runden mit Gemini
    normalized_prompt = str(user_prompt or "").lower()
    is_list_heavy_query = any(marker in normalized_prompt for marker in ("liste", "list", "top", "ranking", "beste"))
    if provider_key == "gemini" and is_list_heavy_query:
        if max_tool_rounds < 10:
            logger.info("DIAMOND-RESEARCH: Listen-Anfrage erkannt. Erhöhe max_tool_rounds auf 10 für tiefe Gemini-Suchen.")
        max_tool_rounds = max(max_tool_rounds, 10)
    
    silo_args = {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "chat_history": chat_history,
        "context_manager": context_manager,
        "db": db,
        "user_prompt": user_prompt,
        "chat_id": chat_id,
        "tool_executor": tool_executor,
        "allowed_skill_ids": effective_allowed_skill_ids,
        "max_tool_rounds": max_tool_rounds,
    }

    if tools_override is not None:
        silo_args["tools_override"] = tools_override
    if disable_tools:
        silo_args["disable_tools"] = disable_tools
    if image_data is not None:
        silo_args["image_data"] = image_data
    if background_tasks is not None:
        silo_args["background_tasks"] = background_tasks
    if bypass_policy:
        silo_args["bypass_policy"] = bypass_policy

    tool_results = kwargs.get("tool_results")
    if tool_results is not None:
        silo_args["tool_results"] = tool_results

    trimmed_tool_results = kwargs.get("trimmed_tool_results")
    if trimmed_tool_results is not None:
        silo_args["trimmed_tool_results"] = trimmed_tool_results

    websearch_synthesis_instruction = kwargs.get("websearch_synthesis_instruction")
    if websearch_synthesis_instruction is not None:
        silo_args["websearch_synthesis_instruction"] = websearch_synthesis_instruction

    tool_limit_reached = kwargs.get("tool_limit_reached")
    if tool_limit_reached is not None:
        silo_args["tool_limit_reached"] = tool_limit_reached

    allow_pdf_enrichment = kwargs.get("allow_pdf_enrichment")
    if allow_pdf_enrichment is not None:
        silo_args["allow_pdf_enrichment"] = allow_pdf_enrichment

    request_budget = kwargs.get("request_budget")
    if request_budget is not None:
        silo_args["request_budget"] = request_budget

    validated_tool_definitions = kwargs.get("validated_tool_definitions")
    if validated_tool_definitions is not None:
        silo_args["validated_tool_definitions"] = validated_tool_definitions

    current_round = kwargs.get("current_round")
    if current_round is not None:
        silo_args["current_round"] = current_round

    forced_tool = kwargs.get("forced_tool")
    if forced_tool is not None:
        silo_args["forced_tool"] = forced_tool

    force_tool_name = kwargs.get("force_tool_name")
    if force_tool_name is not None and provider_key in {"openai", "gemini", "google"}:
        silo_args["force_tool_name"] = force_tool_name

    all_tool_definitions = kwargs.get("all_tool_definitions")
    if all_tool_definitions is not None:
        silo_args["all_tool_definitions"] = all_tool_definitions

    if provider_key == "gemini" and kwargs.get("_gemini_engine_owned_tool_loop"):
        silo_args["_gemini_engine_owned_tool_loop"] = True

    return await selected_silo.reason_and_respond(**silo_args)


def get_provider(provider_name: str):
    """
    Gibt eine Instanz des angeforderten Service-Providers zurück.
    Wird primär für Legacy-Kompatibilität (z.B. chat_orchestrator) bereitgestellt.
    """
    provider_key = str(provider_name).lower()
    provider_gate = provider_access_decision(provider_key)
    if provider_gate.disabled:
        raise RuntimeError(provider_gate.message)
    if provider_key == "gemini":
        from backend.llm_providers.gemini.service import GeminiServiceProvider
        return GeminiServiceProvider()
    elif provider_key == "openai":
        from backend.llm_providers.openai.service import OpenAIServiceProvider
        return OpenAIServiceProvider()
    elif provider_key == "ollama":
        from backend.llm_providers.ollama.service import OllamaServiceProvider
        return OllamaServiceProvider()
    else:
        raise ValueError(f"Unbekannter Provider: {provider_name}")


async def call_llm(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """
    Ein-Zug-LLM-Aufruf für Tools und Hilfsdienste (geo_service, Kontakte, Vision, Intent, …).

    Unterstützt:
    - Nur Keyword: ``provider``, ``model_id``/``model``, ``api_key``, ``messages=``, …
    - Positional (Legacy): ``call_llm(provider, model, api_key, messages=[...])``
    - ``chat_history`` als Alias für ``messages`` (context_manager)

    💎 CU-2: #SelfHealingIdentity - API-Key wird frisch aus keyring geladen
    """
    import keyring

    kw = dict(kwargs)
    if len(args) >= 3:
        kw.setdefault("provider", args[0])
        kw.setdefault("model_id", args[1])
        kw.setdefault("api_key", args[2])
        args = args[3:]
    if args:
        raise TypeError(f"call_llm: unexpected positional arguments after provider/model/api_key: {args!r}")

    provider = str(kw.pop("provider", "") or "")
    model_id = str(kw.pop("model_id", None) or kw.pop("model", "") or "")
    api_key = str(kw.pop("api_key", "") or "")

    messages: Optional[List[Dict[str, Any]]] = kw.pop("messages", None)
    chat_history = kw.pop("chat_history", None)
    if messages is None and chat_history is not None:
        messages = chat_history
    prompt = kw.pop("prompt", None)
    if messages is None:
        messages = [{"role": "user", "content": str(prompt or "")}]

    tools = kw.pop("tools", None)
    force_no_tools = bool(kw.pop("force_no_tools", False))

    provider_gate = provider_access_decision(provider)
    if provider_gate.disabled:
        logger.warning("OPS-KILL-SWITCH: call_llm provider blocked provider=%s", provider)
        return {
            "content": provider_gate.message,
            "text": provider_gate.message,
            "error": provider_gate.message,
            "error_code": provider_gate.code,
            "metadata": {"ops_kill_switch": True, "switch": provider_gate.switch},
        }

    if provider:
        blocked = _guard_llm_provider_silo(provider, model_id)
        if blocked is not None:
            return blocked

    # 💎 CU-2: #SelfHealingIdentity - Frischer Key aus keyring wenn nicht übergeben
    if not api_key and provider:
        try:
            fresh_key = keyring.get_password('Janus-Projekt', provider)
            if fresh_key:
                api_key = fresh_key
                logger.debug("[call_llm] Loaded fresh API key from keyring for provider=%s", provider)
        except Exception as ke:
            logger.warning("[call_llm] Failed to load API key from keyring: %s", ke)

    svc = get_provider(provider)

    # 💎 CU-2: Retry-Loop mit Key-Refresh bei API_KEY_EXPIRED
    max_retries = 2
    for attempt in range(max_retries):
        result = await svc.generate_response(
            api_key=api_key,
            model=model_id,
            messages=messages,
            tools=tools,
            force_no_tools=force_no_tools,
            **kw,
        )

        # Prüfe auf API_KEY_EXPIRED und versuche Refresh
        if result.get("error_code") == "API_KEY_EXPIRED" and attempt < max_retries - 1:
            logger.warning("[call_llm] API_KEY_EXPIRED detected, attempting key refresh (attempt %d)", attempt + 1)
            try:
                fresh_key = keyring.get_password('Janus-Projekt', provider)
                if fresh_key and fresh_key != api_key:
                    api_key = fresh_key
                    logger.info("[call_llm] Refreshed API key from keyring, retrying...")
                    continue
                else:
                    logger.error("[call_llm] No new API key available in keyring")
                    break
            except Exception as ke:
                logger.error("[call_llm] Key refresh failed: %s", ke)
                break
        else:
            return result

    return result


async def get_active_image_generation_model(provider: str) -> Optional[str]:
    """
    Ermittelt das aktuell aktive Bildgenerierungsmodell für den Provider.
    """
    from backend.utils.config_loader import load_config_data
    config = await asyncio.to_thread(load_config_data)
    
    last_used_text_model_id = config.get("last_used_model") 
    model_catalog = await asyncio.to_thread(get_cached_model_catalog)
    
    if last_used_text_model_id and last_used_text_model_id in model_catalog:
        text_model_info = model_catalog[last_used_text_model_id]
        if text_model_info.get("provider") == provider:
            image_gen_model_id = text_model_info.get("image_generation_model")
            if image_gen_model_id and image_gen_model_id in model_catalog and model_catalog[image_gen_model_id].get("type") == "image":
                return image_gen_model_id

    # Fallback-Logik
    if provider == "gemini":
        if "gemini-2.5-flash-image-preview" in model_catalog:
            return "gemini-2.5-flash-image-preview"
    elif provider == "openai":
        if "gpt-image-1.5" in model_catalog:
            return "gpt-image-1.5"

    return None


async def simple_llm_generate_content(provider: str, model: str, api_key: str, prompt: str):
    """
    Vereinfachte Generierung (nur für interne Hilfszwecke).
    """
    blocked = _guard_llm_provider_silo(str(provider), str(model))
    if blocked is not None:
        return blocked
    # Da wir call_llm entfernt haben, delegieren wir hier auch an reason_and_respond oder ein Silo
    # Für Einfachheit nutzen wir hier direkt das Silo-Konzept
    provider_key = str(provider).lower()
    if provider_key == "gemini":
        from backend.llm_providers.gemini.service import GeminiServiceProvider
        svc = GeminiServiceProvider()
    elif provider_key == "openai":
        from backend.llm_providers.openai.service import OpenAIServiceProvider
        svc = OpenAIServiceProvider()
    elif provider_key == "ollama":
        from backend.llm_providers.ollama.service import OllamaServiceProvider
        svc = OllamaServiceProvider()
    else:
        raise ValueError(f"Provider {provider} nicht unterstützt.")

    return await svc.generate_response(
        api_key=api_key,
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )


def get_model_details(model_id: str) -> Dict:
    """
    Gibt Details für eine model_id aus dem gecachten Modellkatalog zurück.
    """
    catalog = get_cached_model_catalog()
    return catalog.get(model_id, {})


def get_first_available_text_model() -> str:
    """
    Wählt das erste verfügbare text-Modell aus dem Model-Katalog.
    Robust gegen leere Kataloge: gibt leeren String zurück, wenn kein text-Modell gefunden wird.
    """
    catalog = get_cached_model_catalog()
    for model_id, model_info in catalog.items():
        if model_info.get("type") == "text":
            return str(model_id)
    logger.warning("No text model found in model catalog")
    return ""


def get_first_available_text_model_with_provider() -> Tuple[str, str]:
    """
    Wählt das erste verfügbare text-Modell aus dem Model-Katalog und gibt (provider, model_id) zurück.
    Robust gegen leere Kataloge: gibt ("", "") zurück, wenn kein text-Modell gefunden wird.
    """
    catalog = get_cached_model_catalog()
    for model_id, model_info in catalog.items():
        if model_info.get("type") == "text":
            provider = str(model_info.get("provider") or "").lower()
            return provider, str(model_id)
    logger.warning("No text model found in model catalog")
    return "", ""

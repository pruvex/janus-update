#!/usr/bin/env python
# backend/scripts/benchmark_skill.py
"""
💎 Diamond Universal Skill-Benchmarker

Testet einen Skill aus dem Janus-Katalog gegen alle Modelle einer
Provider-Familie und ermittelt datengestützt das optimale MoA-Tier.

Aufruf:
    python backend/scripts/benchmark_skill.py --skill system.websearch --provider openai
    python backend/scripts/benchmark_skill.py --skill system.weather --provider gemini --runs 2
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Projekt-Root auf sys.path legen ──────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("benchmark")
logger.setLevel(logging.INFO)

# ── Janus-Imports (lazy, nach sys.path fix) ──────────────────────────────
from backend.services.tool_manager import tool_manager, ToolDefinition  # noqa: E402
from backend.tool_registry import register_all_tools  # noqa: E402
from backend.services.prompting.runtime.builder import PromptBuilder  # noqa: E402

# =========================================================================
# Konstanten
# =========================================================================

BENCHMARK_CASES_PATH = Path(__file__).resolve().parent / "benchmark_cases.json"

# Modelle pro Provider (ohne Pro/Advanced – Kosten-Guard)
PROVIDER_MODELS: Dict[str, List[Dict[str, str]]] = {
    "openai": [
        {"id": "gpt-5.4-nano", "tier": "speed"},
        {"id": "gpt-5.4-nano", "tier": "balanced"},
        {"id": "gpt-5.4", "tier": "logic"},
    ],
    "gemini": [
        {"id": "gemini-3-flash-preview", "tier": "speed"},
        {"id": "gemini-3-pro-preview", "tier": "logic"},
    ],
}

# Tier-Empfehlung basierend auf Modell-Position
TIER_RECOMMENDATION = {
    "gpt-5.4-nano": "speed",
    "gpt-5.4-nano": "balanced",
    "gpt-5.4": "logic",
    "gemini-3-flash-preview": "speed",
    "gemini-3-pro-preview": "logic",
}

# Pfad zum Skills-Katalog-Root
_SKILLS_ROOT = PROJECT_ROOT / "backend" / "skills"


# =========================================================================
# Hilfsfunktionen
# =========================================================================

def load_benchmark_cases() -> Dict[str, List[Dict[str, Any]]]:
    """
    Lädt die Test-Cases aus benchmark_cases.json.
    Normalisiert Plain-Strings (altes Format) automatisch zu
    {"prompt": ..., "quality_check": []}.
    """
    if not BENCHMARK_CASES_PATH.exists():
        logger.error("benchmark_cases.json nicht gefunden: %s", BENCHMARK_CASES_PATH)
        sys.exit(1)
    with open(BENCHMARK_CASES_PATH, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    normalized: Dict[str, List[Dict[str, Any]]] = {}
    for skill_id, cases in raw.items():
        norm_cases = []
        for case in cases:
            if isinstance(case, str):
                norm_cases.append({"prompt": case, "quality_check": [], "few_shot_example": None})
            elif isinstance(case, dict):
                # quality_check kann jetzt List[List[str]] (Konzept-Cluster) sein
                raw_qc = case.get("quality_check", [])
                # Normalisiere: alle Keywords zu lowercase, erhalte Cluster-Struktur
                if isinstance(raw_qc, list) and raw_qc and isinstance(raw_qc[0], list):
                    # Konzept-Cluster (neues Format)
                    norm_qc = [[str(k).lower() for k in cluster] for cluster in raw_qc]
                else:
                    # Fallback: flache Liste → jedes Keyword als eigener Cluster
                    norm_qc = [[str(k).lower()] for k in raw_qc]
                
                norm_cases.append({
                    "prompt": case.get("prompt", ""),
                    "quality_check": norm_qc,
                    "few_shot_example": case.get("few_shot_example"),
                })
        normalized[skill_id] = norm_cases
    return normalized


def get_api_key(provider: str) -> str:
    """Holt den API-Key aus dem Keyring (analog zum Janus-Backend)."""
    import keyring
    key = keyring.get_password("Janus-Projekt", provider)
    if not key:
        logger.error(
            "Kein API-Key für Provider '%s' im Keyring gefunden. "
            "Bitte in den Janus-Einstellungen hinterlegen.",
            provider,
        )
        sys.exit(1)
    return key


def find_tool_by_skill_id(skill_id: str) -> Optional[ToolDefinition]:
    """Findet ein registriertes Tool anhand seiner Skill-ID."""
    for tool_name, tool_def in tool_manager.get_all_tools().items():
        resolved_skill = tool_manager.get_skill_id(tool_name)
        if resolved_skill == skill_id:
            return tool_def
    return None


def get_provider_service(provider: str):
    """Instanziiert den passenden Provider-Service."""
    if provider == "openai":
        from backend.llm_providers.openai.service import OpenAIServiceProvider
        return OpenAIServiceProvider()
    elif provider == "gemini":
        from backend.llm_providers.gemini.service import GeminiServiceProvider
        return GeminiServiceProvider()
    else:
        logger.error("Provider '%s' wird nicht unterstützt. Erlaubt: openai, gemini", provider)
        sys.exit(1)


def extract_tool_call_args(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extrahiert die Argumente des ersten Tool-Calls aus der Provider-Response.
    Gibt None zurück wenn kein valider Tool-Call gefunden wurde.
    """
    tool_calls = response.get("tool_calls", [])
    if not tool_calls:
        return None

    first_call = tool_calls[0]

    # OpenAI-Format: {"function": {"name": ..., "arguments": "json_string"}}
    func_data = first_call.get("function", {})
    args_raw = func_data.get("arguments")

    if args_raw is None:
        return None

    if isinstance(args_raw, str):
        try:
            return json.loads(args_raw)
        except json.JSONDecodeError:
            return None
    elif isinstance(args_raw, dict):
        return args_raw

    return None


def validate_args_against_schema(
    args: Dict[str, Any],
    schema_class: Any,
) -> Tuple[bool, Optional[str]]:
    """
    Validiert Tool-Call-Argumente gegen das Pydantic-Schema des Tools.
    Returns: (success, error_message_or_none)
    """
    if schema_class is None:
        return True, None
    try:
        schema_class.model_validate(args)
        return True, None
    except Exception as exc:
        return False, str(exc)[:200]


def _load_skill_directives(skill_id: str) -> Optional[str]:
    """
    Lädt synthesis_directives aus der Skill-Katalog-JSON-Datei.
    Gibt None zurück wenn kein passender Skill-File gefunden wird.
    """
    if not _SKILLS_ROOT.exists():
        return None
    for skill_file in _SKILLS_ROOT.rglob("*.json"):
        try:
            with skill_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                sid = data.get("skill") or data.get("skill_id")
                if sid == skill_id:
                    return data.get("synthesis_directives") or None
        except Exception:
            pass
    return None


def build_system_prompt(
    tool_name: str,
    skill_id: str,
    provider: str,
    model_id: str,
    few_shot_example: Optional[Dict[str, Any]],
) -> str:
    """
    Baut den System-Prompt via PromptBuilder API (Diamond V2).
    Lädt synthesis_directives aus der Skill-JSON und injiziert sie
    modell-spezifisch via SkillDirective (nano/mini erhalten vereinfachte
    XML-Strukturen vom OpenAICompiler, Gemini nutzt grounding_rules).
    """
    synthesis_directives = _load_skill_directives(skill_id)

    builder = PromptBuilder()

    # Block 1: Rolle (required, priority 1 – wird nie wegoptimiert)
    builder.add_block(
        "system_role",
        (
            f"Du bist ein spezialisierter Tool-Call-Agent. Deine einzige Aufgabe: "
            f"Den User-Prompt in einen validen Tool-Call für '{tool_name}' umwandeln. "
            f"Antworte NUR mit dem Tool-Call. Kein Text davor oder danach."
        ),
        priority=1,
        required=True,
    )

    # Block 2: Tool-Regeln mit optionalem Few-Shot-Beispiel (required, priority 2)
    rule_parts = ["Du MUSST das Tool aufrufen. Direkte Antworten sind VERBOTEN."]
    if few_shot_example:
        example_user = few_shot_example.get("user_prompt", "")
        example_args = json.dumps(
            few_shot_example.get("tool_call_arguments", {}), ensure_ascii=False
        )
        rule_parts.append(
            f"BEISPIEL (PERFEKTE AUSFÜHRUNG):\n"
            f"USER-PROMPT: '{example_user}'\n"
            f'TOOL-CALL: {{"name": "{tool_name}", "arguments": {example_args}}}'
        )
    rule_parts.append(
        "TRANSFERIERE das Prinzip auf die neue Aufgabe. Passe Entitäten intelligent an."
    )
    builder.add_block("tool_rules", "\n\n".join(rule_parts), priority=2, required=True)

    # Block 3: Skill-Direktive aus dem Katalog (optional, priority 5)
    # Kleine Modelle (nano/mini) erhalten via OpenAICompiler die nano/mini-Variante;
    # priority >= 8 würde vom Optimizer bei kleinen Modellen entfernt werden.
    if synthesis_directives:
        builder.add_skill_directive(
            skill_id=skill_id,
            instruction_set={
                "standard": synthesis_directives,
                "mini": synthesis_directives,
                "nano": synthesis_directives,
            },
            priority=5,
            required=False,
        )

    return builder.compile(provider, model_id)


def run_quality_check(
    args: Dict[str, Any],
    concept_clusters: List[List[str]],
) -> Tuple[bool, List[str]]:
    """
    Prüft ob aus jedem Konzept-Cluster mindestens ein Keyword in den generierten
    Tool-Call-Argumenten vorkommt (case-insensitive, alle String-Werte des Args-Dicts werden geprüft).
    Returns: (passed, missing_concept_strings)
    """
    if not concept_clusters:
        return True, []

    # Alle String-Werte aus dem Args-Dict rekursiv extrahieren und zusammenführen
    def _collect_strings(obj: Any) -> str:
        if isinstance(obj, str):
            return obj
        if isinstance(obj, dict):
            return " ".join(_collect_strings(v) for v in obj.values())
        if isinstance(obj, list):
            return " ".join(_collect_strings(item) for item in obj)
        return str(obj)

    haystack = _collect_strings(args).lower()
    missing_concepts = []

    for cluster in concept_clusters:
        # Prüfe, ob mindestens ein Keyword aus dem Cluster im haystack vorkommt
        if not any(keyword.lower() in haystack for keyword in cluster):
            # Baue einen lesbaren String für den Fehler
            cluster_repr = " | ".join(cluster)
            missing_concepts.append(f"[{cluster_repr}]")

    return (len(missing_concepts) == 0), missing_concepts


# =========================================================================
# Einzelner Benchmark-Durchlauf
# =========================================================================

async def run_single_benchmark(
    provider_service,
    api_key: str,
    model_id: str,
    provider: str,
    skill_id: str,
    tool_def: ToolDefinition,
    test_case: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Führt einen einzelnen Benchmark-Durchlauf durch.
    Returns: Dict mit latency_s, cost, format_ok, schema_ok,
             quality_ok, quality_missing, generated_query, error_reason
    """
    result: Dict[str, Any] = {
        "latency_s": 0.0,
        "cost": 0.0,
        "format_ok": False,
        "schema_ok": False,
        "quality_ok": False,
        "quality_missing": [],
        "generated_query": "",
        "error_reason": None,
    }

    user_prompt: str = test_case["prompt"]
    concept_clusters: List[List[str]] = test_case.get("quality_check", [])
    few_shot_example: Optional[Dict[str, Any]] = test_case.get("few_shot_example")

    # System-Prompt via PromptBuilder V2 bauen (modell- und provider-spezifisch)
    system_prompt = build_system_prompt(
        tool_def.name, skill_id, provider, model_id, few_shot_example
    )

    # Message-Historie aufbauen
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Tool-Definition für das LLM
    tools = [tool_def.llm_definition]
    force_tool_name = tool_def.name

    # Messung starten
    t0 = time.perf_counter()
    try:
        response = await provider_service.generate_response(
            api_key=api_key,
            model=model_id,
            messages=messages,
            tools=tools,
            force_tool_name=force_tool_name,
        )
    except Exception as exc:
        result["latency_s"] = time.perf_counter() - t0
        result["error_reason"] = f"API-Error: {str(exc)[:150]}"
        return result

    result["latency_s"] = time.perf_counter() - t0

    # Kosten aus der Response extrahieren (Provider-Service liefert sie mit)
    cost_data = response.get("cost", {})
    result["cost"] = float(cost_data.get("total_cost", 0.0))

    # Response-Typ prüfen
    resp_type = response.get("type", "")

    if resp_type == "error":
        result["error_reason"] = f"LLM-Error: {response.get('message', 'unbekannt')[:150]}"
        return result

    if resp_type != "tool_code":
        result["error_reason"] = "FORMAT-FEHLER (kein Tool-Call)"
        return result

    # Format-Erfolg: Tool-Call vorhanden und Args parsebar
    args = extract_tool_call_args(response)
    if args is None:
        result["error_reason"] = "Tool-Call vorhanden, aber Args nicht parsebar"
        return result

    result["format_ok"] = True

    # Generierte Query für Live-Logging festhalten (erster String-Wert oder JSON-Dump)
    query_field = args.get("query") or args.get("location") or args.get("city") or ""
    result["generated_query"] = str(query_field) if query_field else json.dumps(args, ensure_ascii=False)[:120]

    # Schema-Validierung gegen Pydantic
    schema_ok, schema_err = validate_args_against_schema(args, tool_def.args_schema)
    result["schema_ok"] = schema_ok
    if not schema_ok:
        result["error_reason"] = f"Schema: {schema_err}"
        return result

    # Qualitäts-Check: Konzept-Cluster in den generierten Args?
    quality_ok, missing = run_quality_check(args, concept_clusters)
    result["quality_ok"] = quality_ok
    result["quality_missing"] = missing
    if not quality_ok:
        result["error_reason"] = f"Qualität MANGELHAFT (fehlende Konzepte: {', '.join(missing)})"

    return result


# =========================================================================
# Hauptlogik
# =========================================================================

async def run_benchmark(
    skill_id: str,
    provider: str,
    runs: int = 1,
) -> None:
    """Führt den kompletten Benchmark für einen Skill gegen alle Modelle eines Providers durch."""

    # 1. Benchmark-Cases laden
    cases = load_benchmark_cases()
    prompts = cases.get(skill_id)
    if not prompts:
        logger.error(
            "Keine Test-Prompts für Skill '%s' in benchmark_cases.json gefunden.\n"
            "Verfügbare Skills: %s",
            skill_id,
            ", ".join(sorted(cases.keys())),
        )
        sys.exit(1)

    # 2. Tools registrieren & Tool-Definition holen
    register_all_tools()
    tool_def = find_tool_by_skill_id(skill_id)
    if tool_def is None:
        logger.error(
            "Skill '%s' hat kein registriertes Tool im ToolManager.\n"
            "Prüfe, ob register_all_tools() das Tool enthält und das Skill-Mapping korrekt ist.",
            skill_id,
        )
        sys.exit(1)

    logger.info("Tool gefunden: func=%s  schema=%s", tool_def.name, tool_def.args_schema)

    # 3. Provider-Setup
    models = PROVIDER_MODELS.get(provider)
    if not models:
        logger.error(
            "Provider '%s' hat keine definierten Benchmark-Modelle. Erlaubt: %s",
            provider,
            ", ".join(sorted(PROVIDER_MODELS.keys())),
        )
        sys.exit(1)

    api_key = get_api_key(provider)
    service = get_provider_service(provider)

    # 4. Benchmark durchführen
    print()
    print("=" * 72)
    print(f"  💎 DIAMOND SKILL-BENCHMARKER")
    print(f"  Skill:    {skill_id}")
    print(f"  Provider: {provider}")
    print(f"  Modelle:  {', '.join(m['id'] for m in models)}")
    print(f"  Prompts:  {len(prompts)}  ×  {runs} Run(s)  =  {len(prompts) * runs} Calls/Modell")
    print("=" * 72)
    print()

    # Ergebnis-Sammler: model_id → Liste von Einzelergebnissen
    all_results: Dict[str, List[Dict[str, Any]]] = {m["id"]: [] for m in models}

    total_calls = len(models) * len(prompts) * runs
    call_counter = 0

    for model_info in models:
        model_id = model_info["id"]
        print(f"  ── {model_id} ")

        prompt_idx = 0
        for run_idx in range(runs):
            for test_case in prompts:
                prompt_idx += 1
                call_counter += 1
                result = await run_single_benchmark(
                    provider_service=service,
                    api_key=api_key,
                    model_id=model_id,
                    provider=provider,
                    skill_id=skill_id,
                    tool_def=tool_def,
                    test_case=test_case,
                )
                all_results[model_id].append(result)

                # Live-Logging pro Call
                lat = result["latency_s"]
                if result["format_ok"] and result["schema_ok"] and result["quality_ok"]:
                    q = result["generated_query"]
                    print(f"     ✅ Prompt {prompt_idx}: {lat:.2f}s | Query: '{q}'")
                else:
                    reason = result["error_reason"] or "unbekannt"
                    q = result["generated_query"]
                    q_str = f" | Query war: '{q}'" if q else ""
                    print(f"     ❌ Prompt {prompt_idx}: {reason}{q_str}")

        print()

    # 5. Aggregation & Ausgabe
    print()
    print_results_table(all_results, models)
    print_recommendation(all_results, models, skill_id)


# =========================================================================
# Ausgabe
# =========================================================================

def print_results_table(
    all_results: Dict[str, List[Dict[str, Any]]],
    models: List[Dict[str, str]],
) -> None:
    """Druckt die Ergebnis-Tabelle im ASCII-Format."""

    # Spaltenbreiten
    col_model = 28
    col_rate = 18
    col_lat = 12
    col_cost = 14
    col_err = 40

    header = (
        f"{'Modell':<{col_model}}"
        f"{'Success-Rate':<{col_rate}}"
        f"{'Ø Latenz':<{col_lat}}"
        f"{'Ø Kosten':<{col_cost}}"
        f"{'Fehler-Gründe':<{col_err}}"
    )
    separator = "─" * (col_model + col_rate + col_lat + col_cost + col_err)

    print(separator)
    print(header)
    print(separator)

    for model_info in models:
        model_id = model_info["id"]
        results = all_results[model_id]
        n = len(results)

        if n == 0:
            print(f"{model_id:<{col_model}}{'N/A':<{col_rate}}{'N/A':<{col_lat}}{'N/A':<{col_cost}}{'Keine Daten':<{col_err}}")
            continue

        # Erfolg = format_ok UND schema_ok UND quality_ok
        success_count = sum(1 for r in results if r["format_ok"] and r["schema_ok"] and r["quality_ok"])
        success_rate = success_count / n
        avg_latency = sum(r["latency_s"] for r in results) / n
        avg_cost = sum(r["cost"] for r in results) / n

        # Fehler-Gründe sammeln (unique, max 3)
        error_reasons = []
        seen_errors = set()
        for r in results:
            reason = r.get("error_reason")
            if reason and reason not in seen_errors:
                seen_errors.add(reason)
                # Kürzen für Tabellenansicht
                short = reason[:37] + "..." if len(reason) > 40 else reason
                error_reasons.append(short)
            if len(error_reasons) >= 3:
                break
        errors_str = " | ".join(error_reasons) if error_reasons else "—"

        rate_str = f"{success_rate:>6.0%} ({success_count}/{n})"
        lat_str = f"{avg_latency:>7.2f}s"
        cost_str = f"{avg_cost:>9.6f}€"

        # Farbige Markierung über Emoji
        status = "✅" if success_rate >= 1.0 else ("⚠️" if success_rate >= 0.5 else "❌")

        print(
            f"{status} {model_id:<{col_model - 3}}"
            f"{rate_str:<{col_rate}}"
            f"{lat_str:<{col_lat}}"
            f"{cost_str:<{col_cost}}"
            f"{errors_str}"
        )

    print(separator)
    print()


def print_recommendation(
    all_results: Dict[str, List[Dict[str, Any]]],
    models: List[Dict[str, str]],
    skill_id: str,
) -> None:
    """
    Gibt eine datengestützte Empfehlung aus.
    Heuristik: Das BILLIGSTE Modell mit 100% Success-Rate gewinnt.
    """
    candidates = []

    for model_info in models:
        model_id = model_info["id"]
        results = all_results[model_id]
        n = len(results)
        if n == 0:
            continue

        success_count = sum(1 for r in results if r["format_ok"] and r["schema_ok"] and r["quality_ok"])
        success_rate = success_count / n
        avg_cost = sum(r["cost"] for r in results) / n
        avg_latency = sum(r["latency_s"] for r in results) / n

        if success_rate >= 1.0:
            candidates.append({
                "model_id": model_id,
                "tier": model_info.get("tier", "unknown"),
                "avg_cost": avg_cost,
                "avg_latency": avg_latency,
                "success_rate": success_rate,
            })

    print("─" * 72)

    if not candidates:
        print("  ⚠️  EMPFEHLUNG: Kein Modell hat 100% Success-Rate erreicht!")
        print("       → Prüfe die Fehler-Gründe und passe ggf. die Tool-Schemas an.")
        print("       → Kein optimal_model_tier empfohlen für diesen Skill.")
        print()
        return

    # Sortiere: billigstes zuerst, bei Gleichstand schnellstes
    candidates.sort(key=lambda c: (c["avg_cost"], c["avg_latency"]))
    winner = candidates[0]

    recommended_tier = TIER_RECOMMENDATION.get(winner["model_id"], winner["tier"])

    print(f"  🏆 EMPFEHLUNG für '{skill_id}':")
    print(f"     Sieger-Modell: {winner['model_id']}")
    print(f"     Ø Kosten:     {winner['avg_cost']:.6f}€")
    print(f"     Ø Latenz:     {winner['avg_latency']:.2f}s")
    print()
    print(f"     → Empfohlener MoA-Tier:  \"{recommended_tier}\"")
    print()
    print(f"     Zum Anwenden in der Skill-JSON:")
    print(f'       "optimal_model_tier": "{recommended_tier}"')
    print()

    if len(candidates) > 1:
        print(f"  📊 Alle Modelle mit 100% Erfolg (nach Kosten sortiert):")
        for c in candidates:
            print(f"     • {c['model_id']:28s}  {c['avg_cost']:.6f}€  {c['avg_latency']:.2f}s  (Tier: {c['tier']})")
        print()

    print("─" * 72)
    print()


# =========================================================================
# CLI Entry Point
# =========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="💎 Diamond Universal Skill-Benchmarker – Testet Skills gegen Provider-Modelle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skill",
        required=True,
        help="Skill-ID aus dem Janus-Katalog (z.B. system.websearch, system.weather)",
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=sorted(PROVIDER_MODELS.keys()),
        help="Provider-Familie (openai oder gemini)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Anzahl Wiederholungen pro Prompt (Default: 1)",
    )

    args = parser.parse_args()

    asyncio.run(run_benchmark(
        skill_id=args.skill,
        provider=args.provider,
        runs=args.runs,
    ))


if __name__ == "__main__":
    main()

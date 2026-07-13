EXECUTION RESULT
Execution Status: PASS

# BACKLOG-128 - Ollama-Wetteralias canonicalisieren

## Bound Scope

- Backlog: `BACKLOG-128`.
- Root cause: Ollama emitted `system.weather.get_current_weather`, while the Atomic-Agent phase allowlist exposes only `system.weather`.
- Change: normalize that known alias before the provider's normalized tool-call output reaches the allowlist.
- Excluded: gateway policy, tool schemas, fallback behavior, transport-layer activation, and unrelated aliases.

## Changed Files

- `backend/llm_providers/ollama/service.py`
- `backend/tests/llm_providers/test_ollama_service.py`

## Validation

- `python -m pytest backend/tests/llm_providers/test_ollama_service.py backend/tests/test_runtime_llm.py -q`: PASS (`17 passed`).
- `python -m py_compile backend/llm_providers/ollama/service.py backend/llm_providers/runtime_llm.py backend/services/llm_gateway.py backend/tests/llm_providers/test_ollama_service.py backend/tests/test_runtime_llm.py`: PASS.
- `git diff --check`: PASS.
- Manual default-off Ollama smoke, `TRANSPORT_LAYER_ENABLED=false`, Berlin weather prompt at 2026-07-12 23:01: PASS; rendered Open-Meteo weather answer, no raw tool JSON.

## Result

The alias is converted in both non-native payload normalization paths. The canonical `system.weather` call now reaches the existing Atomic-Agent execution chain. No transport resolver or live gateway delegation was enabled.

Next: final audit together with the bounded M6B.4 resolver/registry slice.

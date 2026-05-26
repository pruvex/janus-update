# D11: Debug Compression Engine

## Overview
Production-safe Log-Analysis Engine mit deterministischen Heuristiken und LLM-gestützter Zusammenfassung.

## Endpoint: GET /api/system/debug-summary

**Beschreibung:**
Analysiert die letzten 100 Logs (RAM-Buffer → Supabase → Log-File Fallback) und gibt eine komprimierte Markdown-Diagnose zurück.

**Fallback-Logik:**
1. **RAM-Buffer** (priorität): Schnell, keine DB-Abfrage
2. **Supabase** (fallback): Letzte 10 Minuten aus `logs_raw` Tabelle
3. **Log-File** (fallback): Direkt aus `janus_backend.log` lesen
4. **Empty-State**: Keine Logs → informative Message

**Heuristik-Erkennung:**
- **Hard Errors:** Events mit `status='error'`
- **Model Drift:** Provider/Model Wechsel innerhalb eines Traces
- **Latency Spikes:** Events mit `latency_ms > 5000`

**Provider-Agnostic:**
- Nutzt `get_speed_tier_model()` für dynamische Modell-Auswahl
- Unterstützt OpenAI, Gemini, Anthropic, etc.
- Kein hartcodiertes Modell

**Timeout-Schutz:**
- 5 Sekunden Timeout pro Operation (Fetch + Heuristik)
- Non-blocking via `run_in_executor` für CPU-intensive Heuristik
- Graceful Degradation bei Timeouts

## Dateien
- `backend/services/logging/debug_engine.py` (Core Engine)
- `backend/api/routers/system.py` (Router - nicht geladen, Workaround in main.py)
- `backend/main.py` (Endpoint als standalone @app.get())
- `.windsurf/workflows/debug_log.md` (Windsurf Skill)

## Skill-Nutzung
Tippe `/debug-log` in Windsurf für Debug-Diagnose.

## Status
🥇 SEALED - Operational with Local Log Fallback

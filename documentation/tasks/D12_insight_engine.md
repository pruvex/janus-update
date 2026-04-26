# D12: Janus Insight Engine — Globale Log-Aggregation

**Status:** 🥇 SEALED & COMPLETE (2026-04-26)
**Epic:** D12 Insight Engine
**Version:** V0.4.23-beta.45

## Ziel

Implementierung einer globalen Log-Aggregation Engine für System-Health Monitoring. Trennung von Mikro-Debugging (Session-level, D11) und Makro-Analyse (Global, D12) zur Identifikation systemweiter Architekturschwächen.

## Architektur

### Komponenten

1. **InsightEngine** (`backend/services/logging/insight_engine.py`)
   - **Fetcher**: `fetch_logs()` — Holt Logs aus Supabase für konfigurierbares Zeitfenster (default: 1 Stunde)
   - **Aggregator**: `aggregate_logs()` — Gruppiert Logs nach Skill und Model
   - **Metrics Calculator**: `calculate_metrics()` — Berechnet calls, error_rate, avg_latency_ms
   - **Pattern Detection**: `detect_patterns()` — Detektiert systemische Muster
   - **Confidence Model**: `calculate_confidence()` — Berechnet Confidence-Score basierend auf Volumen und Fehlerquote

2. **POST Endpoint** (`backend/api/routers/system.py`)
   - **Route**: `/api/system/insights`
   - **Request**: `{"hours": 1}` (optional, default: 1 Stunde)
   - **Response**: JSON mit generierten Insights
   - **Storage**: Speichert Ergebnisse in `logs_insights` Tabelle

3. **Schema** (`backend/data/schemas_logging.py`)
   - **InsightCreate**: Schema für logs_insights Tabelle
   - **Insight**: Vollständiges Modell mit ID

### Pattern Detection Rules

Deterministische Muster-Erkennung ohne Physics-Engine oder Reality-Scores:

| Pattern | Bedingung | Beschreibung |
|---------|----------|-------------|
| `high_error_rate` | error_rate > 0.2 | Skill hat hohe Fehlerquote (>20%) |
| `latency_spike` | avg_latency_ms > 2000 | Skill hat hohe Latenz (>2 Sekunden) |
| `stable` | calls > 50 AND error_rate == 0 | Skill ist stabil (>50 Calls, 0 Fehler) |

### Confidence Model

```
base_confidence = min(1.0, calls / 100.0)
if error_rate > 0.5:
    base_confidence *= 0.8  # 20% Reduktion bei hoher Fehlerquote
```

- Calls < 10: Confidence < 0.1
- Calls = 50: Confidence = 0.5
- Calls >= 100: Confidence = 1.0
- Fehlerquote > 50%: Confidence reduziert um 20%

## API Endpoint

### POST /api/system/insights

**Request:**
```json
{
  "hours": 1
}
```

**Response:**
```json
{
  "message": "Generated 3 insights",
  "insights": [
    {
      "id": "uuid",
      "skill": "knowledge.query",
      "model": "gpt-4o-mini",
      "calls": 150,
      "error_rate": 0.05,
      "avg_latency_ms": 850,
      "patterns": ["stable"],
      "confidence": 1.0,
      "generated_at": "2026-04-26T12:00:00",
      "time_window_hours": 1
    }
  ]
}
```

## Test-Suite

**File:** `backend/tests/test_insight_engine.py`

### Test Cases

1. **Faulty Skill — High Error Rate**
   - 10 Calls, 4 Errors (40% error_rate)
   - Pattern: `high_error_rate`
   - Confidence: 0.1 (reduziert nicht, da error_rate < 0.5)

2. **Stable Skill**
   - 60 Calls, 0 Errors
   - Pattern: `stable`
   - Confidence: 0.6 (60/100)

3. **Performance Problem**
   - 5 Calls, avg_latency_ms = 2620
   - Pattern: `latency_spike`
   - Confidence: 0.05 (5/100)

4. **Multiple Skills and Models**
   - 3 Skill/Model-Kombinationen
   - Verifiziert korrekte Aggregation

**Test Results:** 4/4 passed ✅

## Datenbank-Schema

### Tabelle: logs_insights

```sql
CREATE TABLE logs_insights (
  id TEXT PRIMARY KEY,
  skill TEXT NOT NULL,
  model TEXT NOT NULL,
  calls INTEGER NOT NULL,
  error_rate FLOAT NOT NULL,
  avg_latency_ms FLOAT NOT NULL,
  patterns JSONB,
  confidence FLOAT NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  time_window_hours INTEGER NOT NULL
);
```

## Integration mit D11 Debug Compression Engine

| Feature | D11 (Debug) | D12 (Insight) |
|---------|-------------|---------------|
| Scope | Session-level (trace_id) | Global (alle Logs) |
| Time Window | Letzte 10 Minuten | Konfigurierbar (1h, 24h) |
| Output | Markdown für AI Studio | JSON für System-Monitoring |
| Pattern-Regeln | Hard Errors, Model Drift, Latency Spikes | High Error Rate, Latency Spike, Stable |
| Confidence | Heuristik-basiert | Volumen-basiert |
| Storage | Nicht persistent | Persistent (logs_insights) |

## Nutzung

### Curl Beispiel

```bash
curl.exe -X POST http://localhost:8000/api/system/insights -H "Content-Type: application/json" -d "{\"hours\": 1}"
```

### Python Beispiel

```python
import requests

response = requests.post(
    "http://localhost:8000/api/system/insights",
    json={"hours": 1}
)

insights = response.json()["insights"]
for insight in insights:
    print(f"{insight['skill']}/{insight['model']}: {insight['patterns']}")
```

## Files

- `backend/services/logging/insight_engine.py` (neu)
- `backend/api/routers/system.py` (erweitert)
- `backend/data/schemas_logging.py` (erweitert)
- `backend/tests/test_insight_engine.py` (neu)
- `documentation/tasks/D12_insight_engine.md` (dieses Dokument)

## Verifikation

- ✅ InsightEngine implementiert mit allen Komponenten
- ✅ POST Endpoint `/api/system/insights` operational
- ✅ Schema für logs_insights erstellt
- ✅ Test-Suite (4/4 passed)
- ✅ Deterministische Aggregation verifiziert
- ✅ Keine Physics-Engine, keine Reality-Scores (wie gefordert)

## Sign-off

D12 Insight Engine ist vollständig implementiert und produktiv bereit. Die Engine ermöglicht globale System-Health-Analyse durch deterministische Aggregation von Logs nach Skill und Model. Pattern-Detection identifiziert systemische Probleme (hohe Fehlerquote, Latency-Spikes) und stabile Skills. Confidence-Model basiert auf Call-Volumen und Fehlerquote.

**Status:** 🥇 SEALED & COMPLETE
**Version:** V0.4.23-beta.45

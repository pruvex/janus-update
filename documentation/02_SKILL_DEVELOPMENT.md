# 💎 Diamond-Standard Skill-Entwicklung (V2.4)

Dieses Dokument ist das verbindliche Gesetz für Janus. Es nutzt das **Zentralisierungsprinzip**: Komplexe Logik findet im `ToolExecutor` statt. Skills sind global, resilient und nahtlos integriert.

---

## TEIL 1: Die 8 Ebenen der Unzerstörbarkeit

### Ebene 0: Globaler Kontext & Standort
- **Awareness:** Skills passen sich automatisch an Land, Währung und Sprache des Nutzers an.

### Ebene 1: Funktionale Vision & Idempotenz
- **Nutzen:** Klarer Core-Task. Idempotenz garantiert: Gleicher Input + Ort = Gleicher Output.

### Ebene 2: Technischer Kontrakt (Input/Output)
- **Modelle:** Pydantic Input-Schema UND Output-Schema (zur zentralen Validierung).

### Ebene 3: Logik, Resilience & Observability
- **Handler:** Liefert nur Rohdaten. Resilience (Timeout/Retry) wird zentral vom Executor gesteuert.

### Ebene 4: Metadaten & Benchmarking
- **Tiering:** `optimal_model_tier` wird durch Benchmarks (Phase 7) ermittelt.

### Ebene 5: Sprach-Ebene (Grounding & Seamless UX)
- **Striktes Grounding:** Keine Halluzinationen.
- **No Meta-Talk:** Skills fordern den Nutzer niemals auf, andere Tools zu nutzen. Nötige Präzisierungen erfolgen durch interne Skill-Komposition.

### Ebene 6: Präsentations-Ebene (Renderer)
- **Autorität:** Renderer erzeugt Links/Bilder. Source-Awareness wählt Links passend zu LLM-Zitaten.

### Ebene 7: Benchmarking (Qualitätssicherung)
- Verpflichtender Test mit `benchmark_skill.py`. Günstigstes 100%-Modell gewinnt.

### Ebene 8: Agentic Integration (Seamless Orchestration)
- Der Agentic Planner nutzt scharfe Skill-Beschreibungen für proaktive Ketten (z.B. erst Websearch, dann Price-Check).

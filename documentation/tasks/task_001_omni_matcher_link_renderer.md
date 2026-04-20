# Task: 001 - Omni-Matcher Link Renderer

## 1. Ziel & Kontext
- **Ziel:** Implementierung einer robusten 3-Tier-Kaskade für kontextuelles Link-Rendering in Gemini-Antworten. Links werden direkt unter relevante Absätze/Listenelemente injiziert (kein Footer mehr).
- **Kontext:** Bisheriger Link-Renderer nutzte einen "Brute-Force"-Ansatz mit Footer-Links. Dies führte zu schlechter UX und fehlenden Kontext-Verknüpfungen. Die neue Omni-Matcher-Architektur garantiert Link-Injektion durch mehrstufiges Fallback-System.

## 2. Impact-Analyse & Abhängigkeiten (CRITICAL)
- **Basiert auf:** `documentation/ARCHITECTURE.md` (Link-Renderer-Architektur), `backend/llm_providers/gemini/product_map.json` (Idealo-Produkt-Mapping)
- **Beeinflusst:** 
  - `backend/services/chat_orchestrator.py` (verwendet Link-Renderer für finale Response-Verarbeitung)
  - `backend/llm_providers/gemini/gateway.py` (ruft Renderer mit Metadata auf)
  - Alle Skills mit `system.websearch` (empfangen jetzt kontextuelle Links)
- **Risiko-Einschätzung:** Medium – Änderung betrifft zentrale Rendering-Pipeline, aber Fallback-Mechanismen sind defensiv implementiert.

## 3. Betroffene Dateien
- `backend/llm_providers/gemini/link_renderer.py` (Hauptimplementierung – NEU: Omni-Matcher-Kaskade)
- `backend/llm_providers/gemini/service.py` (Metadata-Extraktion für `webSearchQueries`)
- `backend/llm_providers/gemini/product_map.json` (Idealo-Keyword-Mapping – referenziert)

## 4. Umsetzungsschritte (Strikte Anweisung)
1. **Omni-Matcher-Kaskade in `link_renderer.py` implementieren:**
   - Tier 1: Metadata-Query Matching (nutzt `webSearchQueries` aus Gemini grounding_metadata)
   - Tier 2: JSON-Keyword Matching (Fallback auf `product_map.json` Keywords)
   - Tier 3: Context-Extraction (dynamische Idealo-Suche bei Preis-Erkennung)
2. **Listen-Layout-Logik:** Eingerückte Links (`  - 🌐`) für Listenelemente, normale Links für Absätze
3. **Metadata-Extraction in `service.py`:** Methode `_extract_grounding_metadata()` hinzufügen, die `webSearchQueries` sicher aus der Response extrahiert
4. **Hard-Log für Tier-Counts:** Terminal-Output `!!! RENDERER AKTIV: Tier1=X, Tier2=Y, Tier3=Z Links erstellt`
5. **URL-Validierung:** Säubern von Duplikaten, Leerzeichen, falschen Klammern in URLs

## 5. Test-Vorgaben
- **Reale Szenarien:**
  - Test mit Gemini-Produktanfragen (z.B. "WMF Wasserkocher Medium Adult 12,99 €")
  - Verifiziere: Links erscheinen direkt unter dem jeweiligen Produkt-Absatz
  - Verifiziere: Listenelemente haben eingerückte Links
- **Integrations-Tests:**
  - End-to-End via `/api/chat` mit `system.websearch` Skill
  - Prüfe: `grounding_metadata` wird korrekt durch die Pipeline propagiert
  - Prüfe: Wikipedia-Links für Nicht-Preis-Queries (Hauptthemen)

---

*Ab hier wird das Dokument in Phase 4 durch den ausführenden Agenten (Kimi) ausgefüllt:*

## 6. Ergebnis & Audit-Trail
- **Status:** ⚠️ Superseded — Abgelöst durch `UnifiedWebSearchRenderer` (siehe `task_001_gemini_websearch_diamond.md`)
- **Transformation von In-Place-Rendering zu Post-Aggregation-Rendering vollzogen:**
  - **AGGREGATOR FIX (2026-03-25):** Vollständige Architektur-Umstellung
  - Orchestrator sammelt Tool-Resultate in `results_buffer` (execution_engine.py:486,558-562)
  - `ExecutionResponse` erweitert um `all_tool_results` Feld (schemas.py:32)
  - ChatOrchestrator ruft Renderer einmalig nach dem Loop auf (chat_orchestrator.py:4368-4380)
  - Gateway entlastet – jetzt "dummer" Überbringer ohne Rendering (gateway.py:106-116)
- **Was funktioniert jetzt:**
  - Die Omni-Matcher-Kaskade (Tier 1/2/3) in `link_renderer.py` ist **deprecated**
  - `render_aggregated_sources()` wird nicht mehr aufgerufen
  - Stattdessen: `UnifiedWebSearchRenderer` in `backend/renderers/implementations/unified_websearch_renderer.py`
  - Renderer ist **alleinige Link-Autorität** — Provider liefern nur Daten, Renderer formatiert
  - Registrierung via `backend/renderers/registry.py`
- **Aktueller Stand (2026-03-27):**
  - `UnifiedWebSearchRenderer.render()` bereinigt LLM-Text (Markdown-Links, URLs, Citation-Tags)
  - Gemini-Stil: Kein `---` Separator, kein `### 🔗 Quellen` Heading
  - Nur 1 Link wird gerendert (kompakt)
  - Domain-Name als Titel-Fallback statt "Quelle"
  - Orchestrator nutzt Clean-Slate-Zuweisung: `final_text = rendered_output`
- **Architektur-Übergang:**
  - Die Grundidee des Post-Aggregation-Renderings aus diesem Task lebt weiter
  - Aber: Omni-Matcher-Kaskade (Tier 1/2/3) und `GeminiLinkRenderer` sind durch den einfacheren, provider-agnostischen `UnifiedWebSearchRenderer` ersetzt
  - Idealo-Mapping aus `config/idealo_product_map.json` wird weiterhin genutzt
- **Test-Ergebnisse:**
  - `py_compile` auf allen geänderten Dateien: ✅
  - E2E: Manuelle Benutzer-Validierung (Gemini stabil, GPT in Feintuning)

## 7. Debugging-Log (falls zutreffend)
- **Aufgetretene Fehler:** Keine – saubere Implementierung (Omni-Matcher selbst)
- **Architektur-Änderungen:**
  - **Phase 1 (2026-03-25):** Gateway → In-Place-Rendering → Post-Aggregation im Orchestrator
  - **Phase 2 (2026-03-26):** Omni-Matcher/GeminiLinkRenderer → `UnifiedWebSearchRenderer` (provider-agnostisch)
  - **Phase 3 (2026-03-27):** Renderer vereinfacht auf Gemini-Stil (1 Link, kein Heading, kompakt)
  - **Vorteil:** Deterministische, saubere Quellen-Sektion am Ende der Nachricht, identisch für alle Provider

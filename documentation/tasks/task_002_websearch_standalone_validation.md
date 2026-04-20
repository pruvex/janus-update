# Task: 002 - Websearch V2.0 Standalone Validation (Diamond)

## 1. Ziel & Kontext
- **Ziel:** Validierung der isolierten Websearch V2.0 Architektur. Sicherstellung, dass strukturierte Suchergebnisse (`WebSearchOutput`) korrekt extrahiert, gefiltert und gerendert werden.
- **Kontext:** Wir härten die Basis-Recherche (Ebene 6 & 7), bevor wir über Skill-Integrationen nachdenken. Fokus auf Daten-Integrität und Renderer-Sauberkeit.

## 2. Impact-Analyse & Abhängigkeiten (CRITICAL)
- **Basiert auf:** `task_001_gemini_websearch_diamond.md` (Architektur-Grundlage)
- **Beeinflusst:** 
  - `system.websearch` (Kern-Funktionalität)
  - `backend/renderers/implementations/unified_websearch_renderer.py` (Präsentation)
- **Risiko-Einschätzung:** Low — Da wir keine Skill-Kopplungen ("Mixing") zulassen, ist das System stabil und isoliert testbar.

## 3. Betroffene Dateien
- `backend/tests/test_websearch_standalone.py` (Unit-Tests für V2-Schema)
- `backend/tool_registry.py` (Validierung der `_sources_to_items` Logik)
- `backend/renderers/implementations/unified_websearch_renderer.py` (Listen-Design + Anchor-Cleanup + Auto-Source-Footer)
- `backend/services/websearch/openai_provider.py` (GPT-Proaktivitäts-Direktive)
- `documentation/tasks/task_002_websearch_standalone_validation.md` (Dieses Dokument)

## 4. Umsetzungsschritte (Strikte Anweisung)
1. **Isolierte Test-Suite:** Implementiere `backend/tests/test_websearch_standalone.py`. Teste die Konvertierung von `WebSearchResult` (Rohdaten) in `WebSearchOutput` (Pydantic). Verifiziere, dass `items` korrekt befüllt werden.
2. **Global Fallback Check:** Simuliere eine "leere" Suche für ein Tech-Thema im Test. Prüfe im Log, ob die `Global Fallback` Query ("... latest news") ausgelöst wird.
3. **Renderer-Cleanup (Standalone):** Stelle sicher, dass der `UnifiedWebSearchRenderer` die Item-Liste sauber anzeigt (1 Link pro Item, keine Links im Text-Body). 
4. **STRICT NO-MIXING:** Entferne oder deaktiviere jegliche Aufrufe von `system.price_comparison` innerhalb des Websearch-Handlers für diesen Task.
5. **Contract-Validation:** Führe `validate_websearch_result()` für die neuen V2-Strukturen aus.

## 5. Test-Vorgaben (DONE Kriterien)
- [x] `backend/tests/test_websearch_standalone.py` läuft fehlerfrei durch (`pytest`).
- [x] Der Renderer erzeugt eine saubere Markdown-Liste am Ende der Nachricht (verifiziert durch Test-Output).
- [x] Es findet KEINE Skill-Interaktion mit `price_comparison` statt.
- [x] `WebSearchOutput` enthält valide `items` mit `source_url`.

---
*Ab hier wird das Dokument in Phase 5 durch den ausführenden Agenten ausgefüllt:*

## 6. Ergebnis & Audit-Trail
- **Status:** [✅ Done]
- **Was funktioniert jetzt:** 
  - `_sources_to_items()` konvertiert `WebSearchResult.sources` korrekt zu `WebSearchItem[]`
  - `WebSearchOutput` Pydantic-Modell validiert alle Felder (query, items, retrieved_at)
  - `UnifiedWebSearchRenderer` rendert Item-Liste als saubere Markdown mit Item-Level-Links
  - **Anchor-Cleanup:** `[[PRODUCT:...]]` und `[[WIKI:...]]` Tags werden vor Output entfernt
  - **Auto-Source-Footer:** Zeigt immer `**Quelle:** [domain](url)` am Ende an
  - **GPT-Proaktivität:** OpenAI Prompt enthält "PROAKTIVITÄTS-DIREKTIVE (KEINE RÜCKFRAGEN)"
  - Global Fallback Logik erkannt für Tech-Themen mit <2 Ergebnissen
  - STRICT NO-MIXING: `price_comparison` Aufrufe in `websearch_wrapper` auskommentiert
- **Test-Ergebnisse:** 16/16 Tests passed (0.12s)
  - `TestSourcesToItemsConversion`: 4 passed
  - `TestWebSearchOutputSchema`: 3 passed
  - `TestRendererStandalone`: 3 passed
  - `TestGlobalFallbackDetection`: 3 passed
  - `TestNoMixingConstraint`: 1 passed
  - `TestContractValidation`: 2 passed

## 7. Debugging-Log (falls zutreffend)
- **Aufgetretene Fehler:** Keine
- **Lösung:** N/A
- **Phase 5 Finalisierung:** Renderer Diamond-Polish abgeschlossen (Anchor-Cleanup + Auto-Footer + GPT-Proaktivität)

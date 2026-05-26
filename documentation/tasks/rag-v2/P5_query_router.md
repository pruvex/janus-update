# Task P5: Query Router — Regex-Heuristic Classification

**Sektion 1 — Ziel**
Implementiere den Query-Router. Eingehende Nutzeranfragen werden via Regex-Heuristiken klassifiziert (Code-lastig, Prosa-lastig oder Hybrid), um Suchgewichte (Fusion-Weights) und Ziel-Collections deterministisch zu steuern.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/query_router.py` (Regex-Heuristik: Code-Signale (snake_case, camelCase, Dateiendungen, Funktionsklammern), Prosa-Signale (Fragewörter, Satzlänge ≥8 Wörter), Output: RouterDecision)
- NEU `backend/tests/rag/router_fixtures.jsonl` (34 Test-Szenarien, gemischt Code/Prosa/Hybrid)
- NEU `backend/tests/rag_v2/test_query_router.py` (Accuracy-Gate, Latenz-Gate, Regression-Gate, Signal-Tests, Weighted-RRF-Tests)
- MODIFY `backend/services/rag/rrf.py` (P5: `weighted_reciprocal_rank_fusion()` — gewichtete RRF Fusion für Router-basierte Gewichte)
- MODIFY `backend/services/rag/hybrid_retriever.py` (P5: Collection-Routing, `use_router` Flag, `retrieval_mode` Override, `file_type_filter`, gewichtete RRF)

**Sektion 3 — Out-of-Scope**
- Keine LLM-Calls für Routing (Zero-Magic-Gate)
- Keine echte MRR-Validierung (V2 Index leer)
- Keine UI-Integration (P7)

**Sektion 4 — Impact-Analyse**

- `query_router.py`: Pure Regex-Heuristik, ~0ms Latenz, keine externen Abhängigkeiten
- `rrf.py`: Weighted RRF ermöglicht kanal-spezifische Gewichtung (Code: 75% keyword / 25% vector, Prose: 80% vector / 20% keyword)
- `hybrid_retriever.py`: P5 Integration mit `use_router`, `retrieval_mode`, `file_type_filter`. Rückwärtskompatibel (use_router=False = P4 Verhalten)
- Kein Touch an Freeze-List-Files

**Sektion 5 — Acceptance Criteria**

- [x] `python -m backend.tests.rag_v2.test_query_router` läuft grün (20+ Tests)
- [x] `python -m backend.tests.rag_v2.test_rrf` läuft grün (Weighted RRF Tests)
- [x] `python -m backend.tests.rag_v2.test_hybrid_retriever` läuft grün (P5 Router-Integration)
- [x] `python -m backend.tests.rag.test_legacy_filesystem_isolation` → grün (Hash unverändert: 607afb4e...)
- [x] Accuracy-Gate: Router erreicht ≥90% Trefferquote gegen `router_fixtures.jsonl` (34 Szenarien)
- [x] Zero-Magic-Gate: Keine LLM-Imports oder LLM-Calls in query_router.py
- [x] Latenz-Gate: Routing 34 Queries < 5ms Durchschnitt (reine Regex)
- [x] Regression-Gate: Prose-Queries → prose_heavy/hybrid, Code-Queries → code_heavy/hybrid
- [x] Weighted RRF: Produces different scores than uniform RRF when weights differ
- [x] Manual Override: `retrieval_mode="code"` / `"prose"` / `"hybrid"` bypasses router
- [x] File Type Filter: `file_type_filter=[".py"]` filters results by extension

**Sektion 6 — Verifikation**

```powershell
python -m backend.tests.rag_v2.test_query_router
python -m backend.tests.rag_v2.test_rrf
python -m backend.tests.rag_v2.test_hybrid_retriever
python -m backend.tests.rag.test_legacy_filesystem_isolation
```

**Sektion 7 — Rollback**
- Entferne `backend/services/rag/query_router.py`
- Entferne `backend/tests/rag/router_fixtures.jsonl`
- Revert `rrf.py` (entferne `weighted_reciprocal_rank_fusion`)
- Revert `hybrid_retriever.py` auf P4 (entferne P5 Parameter)
- Entferne `test_query_router.py`
- Kein Einfluss auf Legacy-System

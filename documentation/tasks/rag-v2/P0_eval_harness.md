# Task P0: Eval-Harness & Golden Queries

**Sektion 1 — Ziel**
Baseline-Metrik für die aktuelle `knowledge.query`-Pipeline etablieren. Golden-Query-Corpus mit 30 manuell annotierten Queries (Prose / Code / Mixed) + Runner für MRR@10, Recall@5, P@1.

**Sektion 2 — Scope (Files)**

- NEU `backend/tests/rag/__init__.py`
- NEU `backend/tests/rag/golden_queries.jsonl` (30 Einträge)
- NEU `backend/tests/rag/harness.py` (Metric-Runner)
- NEU `backend/tests/rag/test_baseline.py` (pytest-Integration)
- NEU `documentation/tasks/rag-v2/baseline_metrics.md` (Report)

**Sektion 3 — Out-of-Scope**
Keine Änderung an `knowledge.query`, keine neuen Embeddings, keine Chunking-Änderungen.

**Sektion 4 — Impact-Analyse**

- Greift NICHT in Production-Code ein — reiner Test-Layer.
- Risiko: Golden-Queries subjektiv. Mitigation: AI Studio erstellt Queries mit Domain-Wissen, markiert `query_type` + `confidence`.
- Abhängigkeit: Bestehender `chromadb`-Index muss bestückt sein (min. 50 Test-Dokumente).

**Sektion 5 — Acceptance Criteria**

- [ ] `pytest backend/tests/rag/ -v` läuft grün
- [ ] 30 Golden-Queries vorhanden, verteilt: 10 Prose, 10 Code, 10 Mixed
- [ ] Jede Query hat `{query, expected_paths: [≥1], min_rank: 5, query_type, confidence}`
- [ ] Baseline-Report enthält MRR@10, Recall@5, P@1 mit ≥ 3 Nachkommastellen
- [ ] Harness läuft in ≤ 30s auf Referenz-Hardware

**Sektion 6 — Verifikation**

```powershell
pytest backend/tests/rag/ -v --tb=short
python -m backend.tests.rag.harness --report documentation/tasks/rag-v2/baseline_metrics.md
```

**Sektion 7 — Rollback**
Nicht erforderlich — reiner Additive-Layer. Bei Fehlschlag: Task-Files löschen.

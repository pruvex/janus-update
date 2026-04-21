# RAG V2 — Universal Knowledge-Harvester · Master-Plan (Diamantstandard)

**Status:** Spec-v1.1 · ready-to-orchestrate · **regression-proof (Strangler-Fig)**
**Erstellt:** 2026-04-21
**Revision v1.1:** 2026-04-21 — Coexistence-Contract + Freeze-List + physische Isolation
**Orchestrator:** AI Studio (Opus 4.6 Thinking)
**Executors:** SWE 1.6 (Infrastruktur/Glue), Kimi K2.5 (Algorithmen/Logik)
**Ziel:** Lokale, semantische + lexikalische Suche über alle Text-/Dokument-/Code-Formate in Janus-Workspaces
**Integrations-Budget:** 8 atomare Phasen, jede als eigenständiger Task mit Rollback-Pfad

---

## 0 · Executive Summary

Janus bekommt einen Universal Knowledge-Harvester, der **Prosa (PDF/DOCX/MD/TXT)** und **Code (Python/JS/TS/etc.)** mit getrennten, für ihren Inhaltstyp optimierten Embeddings indiziert und via **Hybrid-Retrieval (Dense + FTS5) + RRF + Cross-Encoder-Reranking** auffindbar macht.

**Leitprinzipien:**

- **Zero-Regression-Contract:** V2 ist **strikt additiv**. Keine Modifikation am bestehenden RAG (PDF-Drops, Projekt-Collections, Skill-Index, Memory-Vektoren). Physische Isolation via separatem Chroma-Pfad.
- **Strangler-Fig statt Replace:** V2 läuft parallel. Opt-in über Feature-Flags (alle default `false`). Umschaltung auf V2 als Default ist eine separate, explizite Entscheidung nach grüner Full-Regression.
- **API-Kontrakt unantastbar:** `knowledge.query`-Signatur und -Verhalten bleibt byte-identisch, wenn keine V2-Flags gesetzt sind. V2 ist nur via neuen **optionalen** Params oder neuem separaten Skill erreichbar.
- **Eval-First:** Golden-Query-Set + MRR-Harness vor jeder Code-Änderung. Legacy-Regression-Queries müssen auf Alt- und Neu-System **byte-gleich** sein.
- **Deterministisch vor Magic:** Query-Router = Regex-Heuristik, kein ML. Debuggbar, 0-Latenz.
- **Security-by-Default:** Workspace-Sentinel-Integration; Denylist für Secrets.
- **Single-User-Desktop-fokussiert:** Keine Cluster-Abhängigkeiten, CPU-tauglich, Cold-Start ≤ 3s.

**Abgrenzung (explizit NICHT im Scope):**

- Multi-User-Auth / Tenant-Isolation
- Cloud-Embedding-APIs (alles lokal)
- Echtzeit-Kollaboration
- GPU-Required-Pfad (CPU muss ausreichen)

---

## 1 · Architektur-Entscheidungen

### 1.1 Tech-Stack (final)

| Layer | Komponente | Version/Ref | Begründung |
|---|---|---|---|
| Vector-Store | ChromaDB (bestehend) | ≥ 0.4.22 | Bereits integriert, zwei Collections: `kb_prose`, `kb_code` |
| Prose-Embedding | `sentence-transformers/all-MiniLM-L6-v2` | bereits im Cache | 384 dim, bewährt, migrations-frei |
| Code-Embedding | `jinaai/jina-embeddings-v2-base-code` | HF, Apache-2.0 | 161 MB, 768 dim, explizit code-trainiert |
| Keyword-Index | SQLite FTS5 | stdlib | Neue DB `backend/data/knowledge_fts.db`, WAL-Mode |
| Fusion | Reciprocal Rank Fusion (Cormack et al. 2009) | k=60 | Robust ohne Score-Kalibrierung |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | HF, Apache-2.0 | 90 MB, ~50ms/50 Pairs CPU |
| Code-Chunker | `tree-sitter` + `tree-sitter-python`, `-javascript`, `-typescript`, `-markdown` | ≥ 0.20 | Robust bei kaputtem Code, multi-lang |
| Prose-Parser | PyMuPDF (bestehend), `python-docx` (neu) | ≥ 1.23 / ≥ 1.1 | PyMuPDF schon in Janus |
| MD-Parser | `markdown-it-py` | ≥ 3.0 | Header-Path-Splitter |
| File-Watcher | `watchdog` | ≥ 3.0 | Standard inkrementelles Indexing |
| Query-Router | Regex-Heuristik (eigenes Modul) | — | Deterministisch, keine ML-Abhängigkeit |

### 1.2 Datenfluss

```
┌─────────┐    ┌──────────────┐    ┌─────────────┐
│ File    │───▶│ FormatRouter │───▶│  Adapter    │
│ (*.pdf) │    │  .parse()    │    │ (Txt/Pdf/   │
└─────────┘    └──────────────┘    │  Docx/Code) │
                                   └──────┬──────┘
                                          ▼
                                   ┌──────────────┐
                                   │  RawChunk[]  │
                                   │ (text,meta)  │
                                   └──────┬───────┘
                                          ▼
                                   ┌──────────────┐
                                   │ ChunkEnricher│ (+ header-path, imports)
                                   └──────┬───────┘
                                          ▼
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
                ┌───────────────┐                   ┌──────────────┐
                │ Embedding     │                   │  FTS5 Writer │
                │ Router        │                   │ (WAL)        │
                │ prose|code    │                   └──────┬───────┘
                └───────┬───────┘                          │
                        ▼                                  │
            ┌─────────────────────┐                        │
            │ Chroma Collections  │                        │
            │ kb_prose | kb_code  │                        │
            └──────────┬──────────┘                        │
                       │                                   │
                       └──────────────┬────────────────────┘
                                      ▼
                              ┌───────────────┐
                              │ Query-Router  │◀──── user_query
                              │ (regex-heur)  │
                              └───────┬───────┘
                                      ▼
                              ┌───────────────┐
                              │ HybridRetr.   │
                              │  vec top-50   │
                              │  fts top-50   │
                              │  RRF k=60     │
                              └───────┬───────┘
                                      ▼
                              ┌───────────────┐
                              │ Cross-Encoder │
                              │  rerank top-5 │
                              └───────┬───────┘
                                      ▼
                              ┌───────────────┐
                              │ Context-Exp.  │ (±1 neighbor chunk)
                              └───────┬───────┘
                                      ▼
                              knowledge.query  Response
```

### 1.3 Storage-Layout (physisch isoliert von Legacy)

```
{app_data_dir}/
  rag_chroma_db/                ← LEGACY, V2 NICHT anfassen
    janus_global_documents/     ← PDF-Drops + Memory-Vektoren (bestehend)
    janus_skill_index/          ← Skill-Routing (bestehend)
    <project_collections>/      ← dynamisch via add_text_to_collection (bestehend)

  rag_chroma_db_v2/             ← NEU · V2 exklusiv
    kb_code_v2/                 ← Code-Chunks, jina-embeddings-v2-base-code
    (kb_prose_v2/)              ← optional in P9, nicht Teil des kritischen Pfades

backend/data/
  knowledge_fts_v2.db           ← NEU: SQLite FTS5 (WAL)
  knowledge_index_v2.db         ← NEU: indexed_files (SHA + chunk_ids)
```

**Kritisch:** Der Pfad `rag_chroma_db_v2` ist physisch getrennt. Ein V2-Crash kann den Legacy-Index nicht korrumpieren. Rollback = Verzeichnis löschen.

### 1.4 Dependency-Delta (`requirements.txt`)

```text
# RAG V2 (NEU)
tree-sitter>=0.20.4,<0.22
tree-sitter-python>=0.20.4
tree-sitter-javascript>=0.20.3
tree-sitter-typescript>=0.20.3
tree-sitter-markdown>=0.2.2
python-docx>=1.1.0,<2.0
markdown-it-py>=3.0.0,<4.0
watchdog>=3.0.0,<5.0
# Reranker-Modell wird via sentence-transformers (bereits vorhanden) geladen
```

**Bereits vorhanden (nicht anfassen):** `chromadb`, `sentence-transformers`, `PyMuPDF`, `numpy`.

---

## 1.5 · Coexistence-Inventar & Freeze-Contract

### 1.5.1 Bestehender RAG-Surface (zum Stichtag 2026-04-21)

| Komponente | Collection / Pfad | Write-Pfade | Read-Pfad | V2-Umgang |
|---|---|---|---|---|
| **PDF-Drops** (User dropt PDF in Janus) | `janus_global_documents` in `rag_chroma_db/` | `rag_manager.process_and_index_single_document()` via `api/routers/rag.py` Upload-Endpoint | `rag_manager.query_knowledge_base()` → Skill `knowledge.query` | **HANDS-OFF** |
| **Projekt-URLs** (gescrapte Webseiten) | Pro-Projekt dynamische Collections | `project_service.py` → `add_text_to_collection()` | `rag_manager.query_knowledge_base()` | **HANDS-OFF** |
| **Creative-Writer-Stilproben** | Author-Style-Collections (dynamisch) | manuell/skriptbasiert | `get_all_documents_from_collection`, `query_knowledge_base` | **HANDS-OFF** |
| **Skill-Routing-Index** | `janus_skill_index` | `skill_router.py` beim Start | `skill_selector.py` | **HANDS-OFF** |
| **Memory-Slots (Vektoren)** | `janus_global_documents` (geteilt mit PDF-Drops!) | `vector_service.py` | Memory-Retrieval | **HANDS-OFF** (Read-only via RRF nur bei explizitem Flag) |
| **YouTube-Transcripts** | Heute **KEIN Chroma-Write** — nur Text-Payload in `transcript_service.py` für Playback/Display | — | — | **NICHT-ZIEL** — bleibt außen vor. Optional später separate Task, nicht Teil dieses Plans. |

### 1.5.2 FREEZE-LIST (V2 darf folgende Files/Funktionen NICHT modifizieren)

**Harter Freeze — V2 schreibt/modifiziert nie:**

```
backend/services/rag_manager.py::process_and_index_single_document
backend/services/rag_manager.py::process_and_index_folder
backend/services/rag_manager.py::add_text_to_collection
backend/services/rag_manager.py::_get_or_create_collection
backend/services/rag_manager.py::delete_document_index
backend/services/rag_manager.py::get_all_documents_from_collection
backend/services/rag_manager.py::list_collections
backend/services/vector_service.py::*                          # komplett hands-off
backend/services/skill_router.py::*                            # komplett hands-off
backend/services/skill_selector.py::*                          # komplett hands-off
backend/api/routers/rag.py::*                                  # komplett hands-off
backend/services/project_service.py::*                         # komplett hands-off
backend/services/creative_writer.py::*                         # komplett hands-off

Collections:
  janus_global_documents   ← V2 schreibt NIE, liest nur bei RAG_V2_READ_LEGACY=true
  janus_skill_index        ← V2 ignoriert komplett
  <alle dynamischen Projekt-Collections>

Pfade:
  {app_data_dir}/rag_chroma_db/  ← V2 nutzt EIGENEN Subpfad rag_chroma_db_v2/
```

**Weicher Freeze — nur Signatur-additive Erweiterungen erlaubt (keine Verhaltensänderung bei alten Aufrufen):**

```
backend/services/rag_manager.py::query_knowledge_base
  └─ Neue optionale Params erlaubt:
       retrieval_mode: Literal["legacy", "v2", "hybrid"] = "legacy"
       file_type_filter: list[str] | None = None
     Alle alten Aufrufer (ohne neue Params) müssen byte-identische Ergebnisse bekommen.

backend/skills/knowledge/query.json
  └─ Manifest darf neue optionale Parameter-Felder bekommen, aber KEINE Pflichtfelder,
     KEINE Änderung der description (LLM-Routing-Erhalt).
```

### 1.5.3 Definition of "Zero Regression"

Ein V2-Zustand ist **regression-frei**, gdw. alle folgenden Kriterien gleichzeitig erfüllt sind:

1. Alle Feature-Flags default `false` → System verhält sich byte-identisch zu pre-P0.
2. Legacy-E2E-Tests (siehe § 10) laufen 100% grün, auch mit V2 installiert aber flags-off.
3. Legacy-E2E-Tests laufen ≥ 98% grün, auch mit V2-Flags aktiviert (≤ 2% Abweichung erlaubt für nicht-deterministische Randfälle, jede Abweichung muss dokumentiert sein).
4. `rag_chroma_db/` Verzeichnis wird nach keinem V2-Run in seinem SHA-Summen-Baum verändert (Assertion in CI).
5. Kein neuer Import von V2-Modulen in Freeze-List-Files.

---

## 2 · Phasenplan

> **Gate-Regel:** Jede Phase muss MRR-Acceptance der Vorphase halten. Kein Skip. Rollback-Pfad ist Pflicht.

### Phase-Übersicht (Scope auf Code-First reduziert; Prose bleibt Legacy)

| # | Phase | Executor | Scope | MRR-AC | Rollback |
|---|---|---|---|---|---|
| P0 | Eval-Harness & Golden Queries + **Legacy-Regression-Suite** | SWE 1.6 | Test-Infra | Baseline dokumentiert | N/A (Test-Infra) |
| P1 | Format-Router + Incremental Index + Deletion **(nur Code-Files)** | SWE 1.6 | `.py/.js/.ts/.md` (Code/MD) | Legacy unverändert | Flag off + `rag_chroma_db_v2/` löschen |
| P2 | FTS5 + RRF-Fusion **(auf V2-Collection, nicht Legacy)** | Kimi K2.5 | Code-Queries | Code-Q ≥ Legacy × 1.15 | Flag `RAG_V2_HYBRID=false` |
| P3 | Code-Aware Chunking + Code-Embedding (jina-code) | Kimi K2.5 | Code-Chunking | Code-Q ≥ Legacy × 1.5 | Collection `kb_code_v2` droppable |
| P4 | Cross-Encoder Reranking + Context Expansion | SWE 1.6 | Ranking | ≥ P3 × 1.4 | Flag `RAG_V2_RERANK=false` |
| P5 | Query-Router + Metadata-Filter | Kimi K2.5 | API | Auto ≥ manuell best | Router → "balanced" |
| P6 | Security + Observability | SWE 1.6 | Policy + Logging | Pen-Test grün | N/A (additiv) |
| P7 | Skill-API **additiv** (neuer Skill `knowledge.code_search`, kein Umleiten von `knowledge.query`) | SWE 1.6 | Skill-Layer | Legacy-E2E grün | Skill-Manifest entfernen |
| P8 | Background Watchdog Indexer (optional) | SWE 1.6 | Watcher | p95-Delta ≤ 10% | `RAG_V2_WATCHER=false` |
| **P9** | **Optional · Prose-Migration Alt→V2** — eigenständige Entscheidung, **nicht Teil des kritischen Pfades** | TBD | Prose-Re-Ingest | Full-Regression vor Switch | Legacy-Collection bleibt ≥ 1 Release |

**Scope-Reduktion v1.1:** Prose (PDFs, Projekt-URLs, Creative-Writer) bleibt vollständig beim Legacy-System. V2 fokussiert auf Code/Markdown — dort ist der Mehrwert (Code-aware Chunking, FTS5-Symbol-Match) am größten und das Regression-Risiko minimal (heute schlechte/keine Code-Suche).

---

## 3 · Task-Spezifikationen (Diamond-OS 7-Sektionen-Template)

> Jede Phase wird als eigenes Task-File `documentation/tasks/rag-v2/P{n}_{name}.md` angelegt (via `/task-setup`).
> Die unten stehenden Specs sind **copy-paste-ready** für AI Studio.

---

### P0 — Eval-Harness & Golden Queries

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

---

### P1 — Format-Router + Incremental Index + Deletion (Code-First)

**Sektion 1 — Ziel**
Universeller File-Parser mit SHA-256-basiertem Incremental Indexing und Orphan-Deletion bei gelöschten/umbenannten Files — **initial Scope: Code- und Markdown-Dateien**. Adapter für PDF/DOCX/CSV/JSON werden gebaut, aber ihre Integration in V2-Indexer ist gated hinter Flag `RAG_V2_INCLUDE_PROSE=false` (default). Damit bleibt die Prose-Indizierung vollständig beim Legacy-System.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/__init__.py`
- NEU `backend/services/rag/ingestion.py` (`FormatRouter`, `IngestionRun`)
- NEU `backend/services/rag/adapters/txt.py`
- NEU `backend/services/rag/adapters/markdown.py`
- NEU `backend/services/rag/adapters/pdf.py` (nutzt bestehendes PyMuPDF)
- NEU `backend/services/rag/adapters/docx.py`
- NEU `backend/services/rag/adapters/csv_json.py`
- NEU `backend/services/rag/adapters/code.py` (Platzhalter, P3 füllt tree-sitter)
- NEU `backend/services/rag/index_store.py` (`indexed_files`-Tabelle)
- MODIFY `requirements.txt` (+ python-docx, watchdog)
- NEU `backend/tests/rag/test_ingestion.py`

**Datenmodell `indexed_files`:**

```sql
CREATE TABLE IF NOT EXISTS indexed_files (
  path          TEXT PRIMARY KEY,
  sha256        TEXT NOT NULL,
  mtime         REAL NOT NULL,
  size_bytes    INTEGER NOT NULL,
  last_run_id   INTEGER NOT NULL,
  chunk_ids     TEXT NOT NULL,            -- JSON-Array
  format        TEXT NOT NULL,            -- 'pdf'|'md'|'py'|...
  indexed_at    REAL NOT NULL             -- unix ts
);
CREATE INDEX idx_indexed_files_run ON indexed_files(last_run_id);
```

**Sektion 3 — Out-of-Scope**
Keine neuen Embeddings, kein Reranker, kein Query-Pfad. Nur Ingestion + Delete. **Keine Integration in Prose-Pfad** (Flag `RAG_V2_INCLUDE_PROSE=false`). **Keine Modifikation** von Freeze-List-Files (§ 1.5.2).

**Sektion 4 — Impact-Analyse**

- Neuer Service-Layer — **kein** Eingriff in `rag_manager.py`, `vector_service.py` oder `api/routers/rag.py`.
- V2-Chroma-Pfad: `{app_data_dir}/rag_chroma_db_v2/` (physisch isoliert von Legacy).
- Feature-Flag `RAG_V2_INGESTION=false` (default) → V2-Indexer wird nicht aufgerufen, Legacy-Pipeline komplett unverändert.
- Risiko: Tree-sitter-Wheels für Windows-Python (siehe R1). Pre-Check via `pip install --dry-run` vor Phasenstart.
- Risiko: SHA-256 auf riesigen Files. Mitigation: mtime+size als Vorfilter.
- **Zero-Regression-Check:** CI-Assertion vergleicht SHA-Summen-Baum von `rag_chroma_db/` vor und nach V2-Indexer-Run → muss identisch sein.

**Sektion 5 — Acceptance Criteria**

- [ ] Re-Run der Ingestion ohne File-Änderung → `embedding_calls == 0`
- [ ] File löschen → Vectors aus `kb_code_v2` UND Row aus `indexed_files` weg
- [ ] File umbenennen → alt gelöscht, neu indiziert
- [ ] SHA-Collision-Test: Zwei identische Files an verschiedenen Pfaden → beide indiziert, aber Embedding-Cache greift
- [ ] **Legacy-Regression-Suite (§ 10.1) grün: alle PDF-Drop-Tests, Projekt-Collection-Tests, Skill-Index-Tests, Memory-Retrieval-Tests unverändert grün**
- [ ] **SHA-Baum-Assertion: `rag_chroma_db/` unverändert nach V2-Indexer-Run**
- [ ] Alle Adapter haben Unit-Tests mit je ≥ 3 Sample-Files
- [ ] Fehlerhafte Files (corrupt PDF, invalides JSON) → `ERROR`-Log + Skip, kein Run-Abbruch

**Sektion 6 — Verifikation**

```powershell
# Full-Run
python -m backend.services.rag.ingestion --workspace C:\KI\Janus-Projekt\workspace
# Re-Run (soll 0 embeddings triggern)
python -m backend.services.rag.ingestion --workspace C:\KI\Janus-Projekt\workspace
# Deletion-Test
Remove-Item workspace\test\sample.md
python -m backend.services.rag.ingestion --workspace C:\KI\Janus-Projekt\workspace
pytest backend/tests/rag/test_ingestion.py -v
```

**Sektion 7 — Rollback**

- `RAG_V2_INGESTION=false` in `.env` → V2-Indexer wird nicht aufgerufen.
- Hard-Rollback: `Remove-Item -Recurse {app_data_dir}/rag_chroma_db_v2/` + `backend/data/knowledge_index_v2.db` löschen.
- **Legacy bleibt in JEDEM Fall intakt** (physische Isolation).

---

### P2 — FTS5 + RRF-Fusion

**Sektion 1 — Ziel**
Lexikalischer Index parallel zum Vektor-Store + Fusion der beiden Rankings via Reciprocal Rank Fusion.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/fts_store.py` (SQLite-FTS5 Wrapper, WAL-Mode)
- NEU `backend/services/rag/rrf.py` (pure function `fuse(rankings: List[List[str]], k: int = 60) -> List[Tuple[str, float]]`)
- NEU `backend/services/rag/hybrid_retriever.py` (orchestriert vec + fts + RRF)
- MODIFY `backend/services/rag/ingestion.py` (Hook: parallel in FTS schreiben)
- NEU `backend/tests/rag/test_fts.py`
- NEU `backend/tests/rag/test_rrf.py`
- NEU `backend/tests/rag/test_hybrid.py`

**FTS5-Schema:**

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS kb_fts USING fts5(
  chunk_id UNINDEXED,
  path UNINDEXED,
  content,
  tokenize = "unicode61 remove_diacritics 2"
);
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

**RRF-Formel (canonical):**

```
score(d) = Σ_r 1 / (k + rank_r(d))
```

mit `k=60`, `rank_r(d)` = 1-basierte Position von `d` in Ranking `r` (∞ wenn nicht vorhanden).

**Sektion 3 — Out-of-Scope**
Kein Reranker, kein Query-Router, kein Code-Chunking.

**Sektion 4 — Impact-Analyse**

- Parallel-Index: FTS5-Write nach Chroma-Write, transaktional pro Chunk-Batch.
- SQLite-Lock-Risiko bei Concurrent-Index + Query → WAL-Mode + `busy_timeout=5000`.
- RRF ist pure function → leicht testbar.

**Sektion 5 — Acceptance Criteria**

- [ ] MRR@10 Golden-Set **≥ Baseline × 1.15**
- [ ] Code-Type-Queries (z.B. `"apply_verbosity_control"`) zeigen **MRR-Lift ≥ 30%**
- [ ] RRF-Unit-Tests: `fuse([[a,b,c],[b,a,c]])` → `b > a > c` (bei gleichen Längen)
- [ ] FTS5-Concurrent-Test: 100 parallele Queries während Index-Write → keine `database is locked`-Errors
- [ ] FTS-Store + Chroma enthalten exakt gleiche `chunk_id`-Menge (Konsistenz-Check in `test_hybrid.py`)

**Sektion 6 — Verifikation**

```powershell
pytest backend/tests/rag/test_rrf.py backend/tests/rag/test_fts.py backend/tests/rag/test_hybrid.py -v
python -m backend.tests.rag.harness --mode hybrid --report documentation/tasks/rag-v2/p2_metrics.md
# Concurrent-Stress
python -m backend.tests.rag.stress_hybrid --queries 100 --workers 8
```

**Sektion 7 — Rollback**
`RAG_V2_HYBRID=false` → nur Vektor-Pfad. FTS5-DB bleibt liegen (kostenfrei), kann später re-aktiviert werden.

---

### P3 — Code-Aware Chunking + Code-Embedding (jina-code)

**Sektion 1 — Ziel**
Tree-sitter-basiertes Chunking für Code, Header-Path-Prefix für Markdown, Collection `kb_code_v2` mit `jinaai/jina-embeddings-v2-base-code`. **Kein Prose-Dual-Embedding** in diesem Plan — Prose bleibt beim Legacy-System.

**Sektion 2 — Scope (Files)**

- MODIFY `backend/services/rag/adapters/code.py` (tree-sitter Implementation)
- MODIFY `backend/services/rag/adapters/markdown.py` (Header-Path-Prefix)
- NEU `backend/services/rag/chunking.py` (`chunk_code()`, `chunk_markdown()`, `chunk_prose()`)
- NEU `backend/services/rag/embedding_router.py` (`route(chunk) -> "prose"|"code"`)
- MODIFY `backend/services/rag/ingestion.py` (Dual-Collection-Write)
- MODIFY `backend/services/rag/hybrid_retriever.py` (beide Collections abfragen, RRF über drei Rankings: `kb_prose`, `kb_code`, `fts`)
- NEU `backend/tests/rag/test_chunking.py`
- NEU `backend/tests/rag/test_embedding_router.py`

**Chunking-Regeln:**

| Format | Strategie | Overlap | Max-Tokens |
|---|---|---|---|
| `.py/.js/.ts` | Tree-sitter: `function_definition`, `class_definition`, `method_definition` | 0 | 512 |
| `.md` | `markdown-it-py` Header-Tree (H1→H2→H3) | 0 | 512 |
| `.txt/.pdf/.docx` | Paragraph + 512-Token-Sliding mit 64-Token-Overlap | 64 | 512 |
| `.csv/.json` | Row→Sentence-Flattening | 0 | 512 |

**Code-Chunk-Prefix-Format:**

```
# Module: backend/services/rag/hybrid_retriever.py
# Imports: chromadb, sqlite3, .rrf.fuse, .fts_store.FTSStore

<actual code chunk>
```

**MD-Chunk-Prefix-Format:**

```
# Section: H1 > H2 > H3

<actual markdown>
```

**Sektion 3 — Out-of-Scope**
Kein Reranker (P4), kein Router (P5).

**Sektion 4 — Impact-Analyse**

- Zweite Chroma-Collection → doppelter Storage-Bedarf für Code-Dateien (vertretbar, Code-Corpus meist < 100 MB).
- Tree-sitter-Grammars als Binary-Artifacts (pip-Wheels) → Packaging muss OS-Wheels unterstützen.
- jina-embeddings-v2-base-code Cold-Load: ~2s. Mitigation: Lazy-Load + Singleton.
- Risiko: tree-sitter-Grammars uneinheitliche API-Versionen → Version-Pin in `requirements.txt`.

**Sektion 5 — Acceptance Criteria**

- [ ] MRR@10 Code-Queries **≥ Baseline × 1.5** (erwartet: 1.8–2.2)
- [ ] Kein Code-Chunk beginnt/endet mitten in einer Funktion (Unit-Test: parst jeden Chunk, prüft `tree_sitter.Node.type ∈ {function_definition, class_definition, method_definition, module}`)
- [ ] MD-Chunks enthalten vollständigen Header-Pfad als erste Zeile
- [ ] Prose-Queries keine Regression (≤ 5% MRR-Drop vs. P2)
- [ ] Embedding-Router-Test: 100 annotierte Chunks → ≥ 98% korrekte Route

**Sektion 6 — Verifikation**

```powershell
pytest backend/tests/rag/test_chunking.py backend/tests/rag/test_embedding_router.py -v
python -m backend.tests.rag.harness --mode hybrid --code-aware --report documentation/tasks/rag-v2/p3_metrics.md
```

**Sektion 7 — Rollback**
Collection `kb_code` droppen, `EmbeddingRouter` → immer `"prose"` liefern. Pipeline fällt auf P2-Verhalten zurück.

---

### P4 — Cross-Encoder Reranking + Context Expansion

**Sektion 1 — Ziel**
Nach RRF: Top-20 durch Cross-Encoder auf Top-5 reduzieren; Top-5 mit ±1 Nachbar-Chunk aus derselben Datei anreichern.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/reranker.py` (Singleton-Lazy-Load)
- NEU `backend/services/rag/context_expander.py`
- MODIFY `backend/services/rag/hybrid_retriever.py` (rerank-stage + expand-stage)
- NEU `backend/tests/rag/test_reranker.py`
- NEU `backend/tests/rag/test_context_expansion.py`

**Reranker-Spec:**

- Modell: `cross-encoder/ms-marco-MiniLM-L-6-v2` (sentence-transformers)
- Input: `List[Tuple[query, chunk_text]]`, max 20 Pairs
- Output: `List[float]` Scores
- Warm-Up: Dummy-Pair beim Backend-Boot (reduziert First-Query-Latenz)
- Feature-Flag: `RAG_V2_RERANK=true` (default)

**Context-Expansion-Regel:**

- Für jeden Top-5 Chunk mit `(path, chunk_idx)`:
  - Lese `indexed_files.chunk_ids` → finde `chunk_idx - 1` und `chunk_idx + 1`
  - Hänge beide (falls existent) als `before_context` / `after_context` in Response
- Token-Budget pro Expand: max 256 Tokens/Nachbar

**Sektion 3 — Out-of-Scope**
Kein Router-Change, kein API-Change.

**Sektion 4 — Impact-Analyse**

- Reranker-Latenz: 50ms CPU, ggf. Blocker auf Low-End-Hardware → Flag + Budget-Test.
- Memory-Footprint: +90 MB permanent (Reranker-Model).
- Risiko: Reranker könnte Recall senken (gutes Chunk auf Pos 18 → Top-5 nach Rerank). Mitigation: A/B-Messung via Harness.

**Sektion 5 — Acceptance Criteria**

- [ ] MRR@10 **≥ P3 × 1.4**
- [ ] Median-Retrieval-Latenz bei 10k Dokumenten **≤ 800ms** auf Referenz-CPU
- [ ] p95-Latenz **≤ 1500ms**
- [ ] Reranker-Cold-Start ≤ 3s (First-Query nach Backend-Boot)
- [ ] Context-Expansion: Keine Duplikate, wenn benachbarte Top-5-Chunks überlappen
- [ ] Flag-off-Pfad (`RAG_V2_RERANK=false`) funktioniert und liefert P3-Ergebnisse

**Sektion 6 — Verifikation**

```powershell
pytest backend/tests/rag/test_reranker.py backend/tests/rag/test_context_expansion.py -v
python -m backend.tests.rag.harness --mode full --report documentation/tasks/rag-v2/p4_metrics.md
python -m backend.tests.rag.bench_latency --n 100
```

**Sektion 7 — Rollback**
`RAG_V2_RERANK=false` → P3-Verhalten. Reranker-Modell bleibt im Cache.

---

### P5 — Query-Router + Metadata-Filter

**Sektion 1 — Ziel**
Regex-Heuristik entscheidet Fusion-Gewichte (vec/fts/code-vec) basierend auf Query-Form. API bekommt optionale Metadata-Filter.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/query_router.py`
- MODIFY `backend/services/rag/hybrid_retriever.py` (nutzt Router-Output)
- NEU `backend/tests/rag/test_query_router.py`
- NEU `backend/tests/rag/router_fixtures.jsonl` (20 annotierte Queries)

**Router-Heuristik:**

```python
def route(query: str) -> RouterDecision:
    score_code = 0
    score_prose = 0
    if re.search(r'"[^"]+"', query): score_code += 3                 # Quotes
    if re.search(r'\b[a-z]+_[a-z_]+\b', query): score_code += 2      # snake_case
    if re.search(r'\b[a-z]+[A-Z][a-zA-Z]+\b', query): score_code += 2 # camelCase
    if re.search(r'\.[a-z]{2,4}\b', query): score_code += 1          # .py, .md
    if re.search(r'[a-zA-Z_]\w*\(', query): score_code += 2          # fn()
    if len(query.split()) >= 8: score_prose += 2                     # long prose
    if re.search(r'\b(was|wie|warum|erkläre)\b', query, re.I): score_prose += 2

    if score_code >= 3 and score_code > score_prose:
        return RouterDecision(mode="code_heavy", weights=(0.2, 0.8))   # (prose_vec, fts)
    if score_prose >= 2 and score_prose > score_code:
        return RouterDecision(mode="prose_heavy", weights=(0.8, 0.2))
    return RouterDecision(mode="balanced", weights=(0.5, 0.5))
```

**API-Erweiterung `knowledge.query`:**

```python
def query(
    query_text: str,
    *,
    retrieval_mode: Literal["auto", "vector", "keyword", "hybrid"] = "auto",
    file_type_filter: list[str] | None = None,     # ["py", "md"]
    modified_after: float | None = None,            # unix ts
    path_prefix: str | None = None,
    n_results: int = 10,
) -> QueryResult
```

**Sektion 3 — Out-of-Scope**
Keine LLM-basierte Query-Classification.

**Sektion 4 — Impact-Analyse**

- Router-Entscheidung zusätzlich zu RRF → RRF bekommt ggf. gewichtete Variante (siehe `hybrid_retriever.fuse_weighted`).
- Metadata-Filter auf Chroma-Seite via `where`-Clause, auf FTS-Seite via `WHERE path LIKE ...`.
- Risiko: Router-Fehlklassifikation senkt MRR. Mitigation: Fallback auf `balanced` bei Score-Unsicherheit.

**Sektion 5 — Acceptance Criteria**

- [ ] Router-Unit-Test gegen `router_fixtures.jsonl` **≥ 90% Accuracy**
- [ ] Golden-Query-MRR mit Auto-Router **≥ MRR mit manuell bestem Mode** (beweist: Router-Overhead bringt Nettogewinn)
- [ ] Metadata-Filter funktional: `file_type_filter=["py"]` → nur Python-Chunks in Top-5
- [ ] API backward-compat: Aufrufe ohne neue Params verhalten sich wie P4

**Sektion 6 — Verifikation**

```powershell
pytest backend/tests/rag/test_query_router.py -v
python -m backend.tests.rag.harness --mode full --auto-router --report documentation/tasks/rag-v2/p5_metrics.md
```

**Sektion 7 — Rollback**
`retrieval_mode="hybrid"` (ohne Router) als API-Default. Router-Code bleibt, aber wird nicht mehr aufgerufen.

---

### P6 — Security + Observability

**Sektion 1 — Ziel**
Workspace-Sentinel-Integration, Denylist für Secrets, strukturierte Retrieval-Logs.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/path_policy.py`
- MODIFY `backend/services/rag/ingestion.py` (Policy-Check vor Parse)
- NEU `backend/services/rag/retrieval_logger.py` (JSON-Line Logger)
- MODIFY `backend/services/rag/hybrid_retriever.py` (Log-Call nach jedem Retrieval)
- NEU `backend/tests/rag/test_path_policy.py`
- NEU `backend/tests/rag/test_retrieval_logger.py`

**Denylist-Patterns (default):**

```python
DEFAULT_DENY = [
    "**/.env*",
    "**/*.pem", "**/*.key", "**/*.pfx",
    "**/id_rsa*", "**/id_ed25519*",
    "**/node_modules/**",
    "**/.git/**",
    "**/__pycache__/**",
    "**/venv/**", "**/.venv/**",
    "**/dist/**", "**/build/**",
    "**/*.sqlite", "**/*.db",   # eigene DBs nicht self-indexen
]
```

**Log-Schema (`backend/logs/rag_retrieval.log`, JSON-Line):**

```json
{
  "ts": 1713912345.123,
  "query_id": "uuid",
  "query": "wo liegt gundula1.pdf",
  "router_decision": {"mode": "prose_heavy", "weights": [0.8, 0.2]},
  "filters": {"file_type_filter": null, "path_prefix": null},
  "vec_prose_top5": [{"chunk_id": "...", "score": 0.87}],
  "vec_code_top5": [],
  "fts_top5": [{"chunk_id": "...", "score": 12.4}],
  "rrf_top5": [...],
  "rerank_top5": [...],
  "expanded_paths": [...],
  "latency_ms": {"vec": 42, "fts": 18, "rrf": 3, "rerank": 51, "expand": 8, "total": 122}
}
```

**Sektion 3 — Out-of-Scope**
Kein Audit-UI, kein Log-Shipping.

**Sektion 4 — Impact-Analyse**

- Policy-Check pre-Parse → marginal Overhead (glob-matching).
- Log-File kann wachsen → Rotation via `logging.handlers.RotatingFileHandler` (10 MB, 5 Backups).

**Sektion 5 — Acceptance Criteria**

- [ ] Pen-Test: `.env` in Workspace anlegen → darf NICHT indiziert werden
- [ ] Pen-Test: `id_rsa` in Workspace → darf NICHT indiziert werden
- [ ] Path-Prefix-Traversal (`../../etc/passwd`) wird durch Sentinel blockiert
- [ ] Log-Schema validiert via `jsonschema` in Unit-Test
- [ ] Log-Rotation funktional (10 MB Limit getestet)

**Sektion 6 — Verifikation**

```powershell
pytest backend/tests/rag/test_path_policy.py backend/tests/rag/test_retrieval_logger.py -v
python -m backend.tests.rag.pen_test_secrets
```

**Sektion 7 — Rollback**
Additive Layer — keine Migration. Bei Fehlern: Logger-Flag off, Policy auf "allow-all" (NUR für Debug).

---

### P7 — Skill-API (additiv, NIE Legacy-Umleitung)

**Sektion 1 — Ziel**
**Neuer** Skill `knowledge.code_search` (FTS-bias=0.8) für Code-Symbol-Queries. `knowledge.query` bleibt **verhaltens-identisch** zu heute — lediglich **optional additive** Parameter (`retrieval_mode`, `file_type_filter`) werden ergänzt. Default-Verhalten (ohne diese Params) ist byte-identisch zu pre-P0.

**Sektion 2 — Scope (Files)**

- MODIFY `backend/services/knowledge_service.py` (oder wo `knowledge.query` implementiert ist)
- MODIFY `backend/skills/knowledge/query.json` (neue optionale Params dokumentiert)
- NEU `backend/skills/knowledge/code_search.json`
- NEU `backend/services/rag/code_search.py` (FTS-bias=0.8)
- MODIFY `backend/tests/test_knowledge_skills.py` (bestehend) — Erweiterung
- NEU `backend/tests/rag/test_api_compat.py`

**Neuer Skill `knowledge.code_search`:**

```json
{
  "skill_id": "knowledge.code_search",
  "description": "Durchsucht Code-Dateien lexikalisch und semantisch. Nutze bei 'Wo ist Funktion X definiert?', 'Wo wird Symbol Y verwendet?'.",
  "parameters": {
    "query_text": {"type": "string", "required": true},
    "file_type_filter": {"type": "array", "items": {"type": "string"}},
    "n_results": {"type": "integer", "default": 10}
  },
  "capabilities": ["code_search", "symbol_lookup"],
  "latency": "normal",
  "sandbox_level": "workspace_only"
}
```

**Feature-Flag-Strategie (REVIDIERT v1.1):**

- **Kein** Master-Flag `RAG_V2=true`-Umschaltung in diesem Plan. Stattdessen: V2 ist über den neuen Skill `knowledge.code_search` erreichbar. Der LLM entscheidet via Skill-Routing.
- `knowledge.query` **bleibt verhaltens-default-identisch**. Ein V2-Pfad innerhalb von `knowledge.query` existiert nur, wenn der Aufrufer explizit `retrieval_mode="v2"` setzt.
- Full-Cutover (V2 wird Default für `knowledge.query`) ist **kein P7-Thema**, sondern optionaler P9 (separate Entscheidung nach Full-Regression).

**Sektion 3 — Out-of-Scope**
Keine UI-Änderungen, kein Deprecation-Warning im LLM-Prompt.

**Sektion 4 — Impact-Analyse**

- Alle bestehenden E2E-Tests, die `knowledge.query` nutzen, müssen grün bleiben.
- `CapabilityRegistry` bekommt neuen Eintrag für `knowledge.code_search` — muss in `capability_registry.json` registriert werden.
- Risiko: LLM nutzt bisher `knowledge.query` für Code-Fragen. Neuer Skill muss via Skill-Directive explizit beworben werden.

**Sektion 5 — Acceptance Criteria**

- [ ] **Alle bestehenden `knowledge.query`-E2E-Tests grün — OHNE jede Änderung ihrer Assertions**
- [ ] **Legacy-Regression-Suite (§ 10) 100% grün**
- [ ] Neuer Skill `knowledge.code_search` in `CapabilityRegistry` registriert, keine ORPHAN-Warnings
- [ ] E2E-Test: LLM-Query "wo ist apply_verbosity_control definiert" → wählt `knowledge.code_search` (Skill-Directive geprüft)
- [ ] `knowledge.query` ohne `retrieval_mode`-Param → byte-identisches Verhalten zu pre-P0 (verifiziert via Response-Diff-Test)

**Sektion 6 — Verifikation**

```powershell
pytest backend/tests/rag/ backend/tests/test_knowledge_skills.py -v
pytest backend/tests/test_e2e_diamond_journeys.py -k knowledge -v
```

**Sektion 7 — Rollback**
`knowledge.code_search` Skill-Manifest entfernen + Registry-Eintrag löschen. `knowledge.query`-Signatur-Erweiterung zurücknehmen (rein additive Params — entfernen bricht nichts). Legacy-Pipeline war nie angetastet.

---

### P8 — Background Watchdog Indexer (optional)

**Sektion 1 — Ziel**
File-System-Observer re-indexiert geänderte Files automatisch, ohne User-Query zu blockieren.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/watcher.py` (`watchdog.Observer` + Debounce-Queue)
- MODIFY `backend/main.py` (oder wo Backend-Boot ist): Watcher-Startup pro Workspace
- NEU `backend/tests/rag/test_watcher.py`

**Debounce-Spec:**

- Jeder File-Event (`on_modified`, `on_created`, `on_deleted`, `on_moved`) → Queue mit 2s-Debounce pro Pfad
- Coalesce: Mehrfach-Events pro Pfad in Debounce-Fenster → 1 Re-Index-Call
- Concurrency: Separater Thread, Read-Write-Lock mit Retriever (Read-Priority)

**Sektion 3 — Out-of-Scope**
Keine UI-Feedback, kein Progress-Bar.

**Sektion 4 — Impact-Analyse**

- Hintergrund-CPU-Last während Tipp-Bursts in großen Repos → Debounce entscheidend.
- SQLite WAL + Chroma parallel → muss getestet werden auf "database is locked"-Race.

**Sektion 5 — Acceptance Criteria**

- [ ] File speichern → Index-Update in ≤ 5s
- [ ] p95-Query-Latenz-Delta zwischen "Watcher an" und "Watcher aus" **≤ 10%**
- [ ] 100 File-Events in 1s (Stress-Test) → genau 1 Re-Index pro Pfad (Debounce greift)
- [ ] Watcher-Shutdown clean bei Backend-Stop (keine Zombie-Threads)

**Sektion 6 — Verifikation**

```powershell
pytest backend/tests/rag/test_watcher.py -v
python -m backend.tests.rag.stress_watcher --events 100 --duration 1
```

**Sektion 7 — Rollback**
`RAG_V2_WATCHER=false` → Watcher startet nicht. Manueller Re-Index via CLI bleibt verfügbar.

---

## 4 · Orchestrator-Workflow (AI Studio)

### 4.1 Phasen-Lifecycle

```
┌───────────────────────────────────────────────────────────────┐
│ Für jede Phase P{n}:                                          │
│                                                               │
│  1. AI Studio liest:                                          │
│     - PROJECT_STATE.md                                        │
│     - WHAT_I_LEARNED.md                                       │
│     - documentation/tasks/rag-v2/P{n-1}_metrics.md            │
│                                                               │
│  2. /task-setup → documentation/tasks/rag-v2/P{n}_<name>.md   │
│     (7-Sektionen-Template aus Diamond-OS)                     │
│                                                               │
│  3. AI Studio (Opus Thinking) — Impact-Analyse:               │
│     - Welche bestehenden Files brechen?                       │
│     - Welche Tests existieren? (Sektion 6 Verifikation)       │
│     - Benchmark-Erwartung aus P{n-1}                          │
│     → Fülle Sektion 4 vollständig aus                         │
│                                                               │
│  4. /pre-check → Validierung Sektion 4 complete               │
│                                                               │
│  5. Handover an Executor:                                     │
│     - SWE 1.6 oder Kimi K2.5 (siehe Executor-Matrix)          │
│     - Executor arbeitet mit Task-File als single-source       │
│     - Executor darf NUR Sektion-2-Files anfassen              │
│                                                               │
│  6. Executor: Implementation + Verifikation (Sektion 6)       │
│                                                               │
│  7. /post-impl:                                               │
│     - Audit-Trail (Files/Diffs)                               │
│     - Inventory-Update                                        │
│     - CHANGELOG.md Entry                                      │
│     - PROJECT_STATE.md CURRENT_SESSION_DELTA Update           │
│     - WHAT_I_LEARNED.md Lessons (falls Überraschungen)        │
│     - Harness-Run → Metrics-Report                            │
│                                                               │
│  8. GATE: MRR-AC erfüllt?                                     │
│     ✅ → Markiere Task SEALED, starte P{n+1}                  │
│     ❌ → Iteration oder Rollback                              │
└───────────────────────────────────────────────────────────────┘
```

### 4.2 Executor-Matrix

| Phase | Primary | Begründung |
|---|---|---|
| P0 | **SWE 1.6** | Pytest-Boilerplate, JSON-Fixtures |
| P1 | **SWE 1.6** | Viel Adapter-Code, Library-Glue |
| P2 | **Kimi K2.5** | RRF-Algorithmus + SQL-Schema-Präzision |
| P3 | **Kimi K2.5** | Tree-sitter-Logik, chirurgische Chunk-Grenzen |
| P4 | **SWE 1.6** | Library-Integration, Threading-Basics |
| P5 | **Kimi K2.5** | Heuristik-Scoring, Regex-Präzision |
| P6 | **SWE 1.6** | Policy-Glob, Logging-Setup |
| P7 | **SWE 1.6** | Skill-Manifests, API-Kompat-Shim |
| P8 | **SWE 1.6** | Watchdog-Integration, Debounce-Pattern |

### 4.3 Handover-Template für Executors

```markdown
# RAG-V2 Phase P{n} — Executor Brief

**Executor:** {SWE 1.6 | Kimi K2.5}
**Task-File:** documentation/tasks/rag-v2/P{n}_<name>.md
**Vorphase Metrics:** documentation/tasks/rag-v2/P{n-1}_metrics.md
**Feature-Flag:** {name}={default}

## Do
- Lies Task-File komplett (alle 7 Sektionen).
- Halte dich strikt an Sektion 2 (Files-Liste). Keine weiteren Files.
- Implementiere Sektion 6 Verifikation als erstes (TDD).
- Dokumentiere Überraschungen in `WHAT_I_LEARNED.md`.

## Don't
- Keine Änderungen an bestehenden Files außerhalb Sektion 2.
- Kein Breaking-Change an `knowledge.query`-API (außer in P7, dort additiv).
- Keine `print()`-Debugs — nutze `logger`.
- Keine hart-kodierten Pfade — immer via `config` oder Parameter.

## Definition of Done
- [ ] Alle AC (Sektion 5) erfüllt
- [ ] Verifikation (Sektion 6) grün ausgeführt
- [ ] Metrics-Report in documentation/tasks/rag-v2/P{n}_metrics.md
- [ ] /post-impl abgeschlossen
```

---

## 5 · Risiko-Register

| # | Risiko | Phase | P×I | Mitigation |
|---|---|---|---|---|
| R1 | Tree-sitter-Wheel fehlt für Windows-Python | P3 | H×H | Pre-Check: `pip install tree-sitter-python --dry-run`. Fallback: Python-nur-Pipeline via `ast` |
| R2 | Reranker-Latenz blockiert Low-End-CPU | P4 | M×H | Feature-Flag + Budget-Test. Fallback: RRF-only |
| R3 | SHA-256 auf 500 MB+ Files zu langsam | P1 | M×M | mtime+size-Vorfilter, SHA nur bei Delta |
| R4 | SQLite-Lock bei Concurrent-Index+Query | P2/P8 | M×H | WAL-Mode + busy_timeout=5000 + RW-Lock |
| R5 | jina-code-Modell-Download zu groß für Offline-Setups | P3 | L×M | Lokaler Mirror oder Manual-Bundle für Air-Gapped |
| R6 | Router-Fehlklassifikation senkt MRR | P5 | M×M | Fallback "balanced" bei Score-Unsicherheit |
| R7 | Chroma-Kosten bei Dual-Collection doppelter Speicher | P3 | L×L | Code-Corpus meist < 100 MB — vertretbar |
| R8 | Watchdog-Events-Flood in großen Repos | P8 | M×M | 2s-Debounce + Per-Path-Coalesce + Pattern-Filter |
| R9 | Existierende E2E-Tests brechen in P7 | P7 | M×H | API-Kompat-Suite (test_api_compat.py) vor Merge |
| R10 | Golden-Queries zu subjektiv → MRR-Ziel verfehlt obwohl besser | P0 | M×M | Multi-Annotator-Review (AI Studio + User cross-check) |

---

## 6 · Metriken & Success-Gates

### 6.1 Messpunkte

Alle Metriken werden via `backend/tests/rag/harness.py` reproduzierbar berechnet:

- **MRR@10** (Mean Reciprocal Rank): Kernmetrik für Ranking-Qualität
- **Recall@5**: "Ist das richtige Doc überhaupt in den Top-5?"
- **P@1** (Precision at 1): "Liefert Top-1 einen Treffer?"
- **Latenz**: p50, p95, p99 in ms

### 6.2 Zielwerte (kumulativ)

| Phase | MRR@10 vs Baseline | Recall@5 | p95-Latenz |
|---|---|---|---|
| P0 (Baseline) | 1.00× | X (measure) | Y (measure) |
| P2 | **≥ 1.15×** | ≥ X | ≤ Y × 1.2 |
| P3 | Code-Q ≥ 1.5×, Prose ≥ 0.95× | ≥ X | ≤ Y × 1.3 |
| P4 | ≥ 1.4× vs P3 | ≥ X × 1.1 | ≤ 1500ms |
| P5 | ≥ manuell-best | ≥ X × 1.1 | ≤ 1500ms |
| Final | **Gesamt ≥ 2.0× Baseline** | **≥ 0.85** | **≤ 1200ms** |

---

## 7 · Glossar

- **RRF** — Reciprocal Rank Fusion. Fusions-Algorithmus für mehrere Rankings ohne Score-Kalibrierung.
- **Cross-Encoder** — Modell, das Query+Dokument gemeinsam encodiert und einen Relevanz-Score liefert. Genauer, aber langsamer als Dual-Encoder (Embeddings).
- **FTS5** — Full-Text-Search-Extension 5 in SQLite. Lexikalisch, BM25-ähnlich.
- **MRR@10** — Mean Reciprocal Rank über Top-10: 1/rank_of_first_correct, gemittelt über Queries.
- **Golden Query** — Manuell annotierte Query mit bekanntem "richtigem" Ergebnis; Grundlage jedes Retrieval-Evals.
- **Header-Path-Prefix** — Markdown-Chunk-Präfix, der den Header-Kontext (H1>H2>H3) dem Embedding-Modell explizit gibt.
- **Dual-Embedding** — Zwei getrennte Embedding-Modelle für unterschiedliche Content-Typen (hier: Prose vs Code).

---

## 8 · Quick-Start für AI Studio

```powershell
# 1. Dieses Dokument lesen
Get-Content C:\KI\Janus-Projekt\documentation\RAG_V2_MASTER_PLAN.md

# 2. P0 starten
# In AI Studio: /task-setup
# → erstelle documentation/tasks/rag-v2/P0_eval_harness.md
# → kopiere Sektionen aus § 3 / P0 dieses Dokuments

# 3. Handover an SWE 1.6 mit Executor-Brief (§ 4.3)

# 4. Nach Abschluss: /post-impl, dann P1
```

---

## 9 · Referenzen

- Cormack, Clarke, Buettcher: "Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods" (SIGIR 2009)
- jina-embeddings-v2-base-code: https://huggingface.co/jinaai/jina-embeddings-v2-base-code
- tree-sitter: https://tree-sitter.github.io/
- SQLite FTS5: https://www.sqlite.org/fts5.html
- Cross-Encoder ms-marco: https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2

---

---

### P9 — Optional · Prose-Migration Alt → V2 (NICHT im kritischen Pfad)

**Status:** Optional. Wird **nur** gestartet, wenn nach P0–P8 eine explizite Entscheidung zur Prose-Migration fällt. Plan ist ohne P9 vollständig durchführbar.

**Sektion 1 — Ziel**
Prose-Inhalte (PDFs, DOCX, Projekt-URL-Scrapes) werden zusätzlich in `kb_prose_v2` re-indiziert (Legacy-Collection `janus_global_documents` bleibt parallel befüllt). `knowledge.query` bekommt Default `retrieval_mode="hybrid"` nach grüner Full-Regression.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/prose_migration.py` (One-Shot-Migrator, liest aus `janus_global_documents`, schreibt nach `kb_prose_v2`)
- MODIFY `backend/services/rag/hybrid_retriever.py` (Prose-Collection hinzufügen)
- MODIFY `rag_manager.query_knowledge_base` Default von `retrieval_mode="legacy"` auf `"hybrid"` — **nach** Regression-Gate
- NEU `backend/tests/rag/test_prose_migration.py`
- NEU `backend/tests/rag/test_full_regression.py`

**Sektion 3 — Out-of-Scope**
- Löschung des Legacy-Index `janus_global_documents` — bleibt ≥ 1 Release als Fallback.
- YouTube-Transcripts (separate Entscheidung).

**Sektion 4 — Impact-Analyse**
- **Höchstes Regressions-Risiko aller Phasen** — deshalb optional und separat gated.
- Voraussetzung: P0-Legacy-Regression-Suite muss ≥ 500 Queries umfassen und 100% grün auf V2-Hybrid-Mode laufen.
- Storage-Verdopplung während Übergang (akzeptabel, lokal).

**Sektion 5 — Acceptance Criteria**
- [ ] Re-Ingest aller Prose-Dokumente in `kb_prose_v2` ohne Datenverlust (Count-Assertion)
- [ ] Legacy-Regression-Suite 100% grün mit `retrieval_mode="hybrid"`
- [ ] Full-Regression-Suite (500+ Queries) grün: MRR-Delta ≥ 0, kein Query mit MRR-Drop > 20%
- [ ] Rollback-Drill: `retrieval_mode="legacy"` fällt auf Legacy-Pipeline zurück, byte-identische Antworten wie pre-Migration

**Sektion 6 — Verifikation**
```powershell
python -m backend.services.rag.prose_migration --dry-run
python -m backend.services.rag.prose_migration --execute
pytest backend/tests/rag/test_prose_migration.py backend/tests/rag/test_full_regression.py -v
```

**Sektion 7 — Rollback**
`retrieval_mode` Default auf `"legacy"` zurück. `kb_prose_v2` Collection droppen. Legacy war nie modifiziert.

---

## 10 · Regression-Test-Matrix (Legacy-Grün-Gate)

### 10.1 Pflicht-Suites vor JEDER Phase (P1–P8)

Jede dieser Test-Gruppen MUSS grün sein, **bevor** die jeweilige Phase SEALED wird. Wenn nicht grün → kein Proceed zu P{n+1}.

| Suite | Deckt ab | Befehl |
|---|---|---|
| **PDF-Drop-Regression** | PDF hochladen via `/api/rag/upload`, Indexierung, Retrieval über `knowledge.query` | `pytest backend/tests/test_pdf_status_flow.py backend/tests/test_domain_knowledge.py -v` |
| **E2E-Diamond-Journeys** | End-to-End PDF-Upload + Skill-Execution | `pytest backend/tests/test_e2e_diamond_journeys.py -k knowledge -v` |
| **Routing-Regression** | `knowledge.query`-Skill-Routing | `pytest backend/tests/routing/test_router.py -v` |
| **Skill-Router-Executor** | Skill-Index-Collection unangetastet | `pytest backend/tests/test_skill_router_executor.py -v` |
| **Policy-Bypass-Gateway** | Berechtigungen auf `knowledge.query` unverändert | `pytest backend/tests/test_policy_bypass_gateway.py -v` |
| **Vector-Service** | Memory-Vektoren + `janus_global_documents` unangetastet | `pytest backend/tests/test_vector_service.py -v` |
| **SHA-Baum-Assertion** | `rag_chroma_db/` Verzeichnis-SHA unverändert nach V2-Indexer-Run | `pytest backend/tests/rag/test_legacy_filesystem_isolation.py -v` (NEU in P0) |
| **API-Kompat (ab P7)** | `knowledge.query` ohne neue Params → byte-identisch zu pre-P0 | `pytest backend/tests/rag/test_api_compat.py -v` (NEU in P7) |

### 10.2 Zusätzliche Gates für P9 (Prose-Migration)

| Suite | Deckt ab |
|---|---|
| **Full-Regression (500+ Queries)** | Alle historisch im Produktionsbetrieb vorgekommenen Knowledge-Queries |
| **Memory-Retrieval-Regression** | Memory-Slot-Queries liefern unverändert dieselben Top-K |
| **Creative-Writer-Regression** | Author-Style-Collections liefern unverändert dieselben Stilproben |

### 10.3 Implementierungs-Hinweis für P0

Der Legacy-Regression-Harness wird in P0 als **Voraussetzung** gebaut. Er umfasst:

```
backend/tests/rag/
  test_legacy_regression.py       ← Umbrella-Suite, ruft alle obigen Tests auf
  test_legacy_filesystem_isolation.py ← SHA-Baum-Diff vor/nach V2-Run
  golden_queries.jsonl            ← Retrieval-Qualität (V2-Metrik)
  legacy_regression_queries.jsonl ← 50 Legacy-Queries mit bekannten Alt-Pipeline-Antworten (Byte-Diff-Test)
```

**Keine Phase P{n≥1} darf ohne P0-Abschluss starten.**

---

## 11 · Feature-Flag-Register (zentral, default-safe)

Alle V2-Flags werden in `backend/config.py` (oder äquivalent) registriert. **Default aller Flags: `false`.** Nur explizite Aktivierung schaltet V2-Pfade scharf.

| Flag | Default | Beschreibung | Eingeführt in |
|---|---|---|---|
| `RAG_V2_INGESTION` | `false` | Aktiviert V2-Indexer (Code + MD). Bei `false` läuft nur Legacy. | P1 |
| `RAG_V2_INCLUDE_PROSE` | `false` | Schaltet V2-Indexer auch für Prose-Files frei. **Bleibt `false` bis P9.** | P1 |
| `RAG_V2_HYBRID` | `false` | Fügt FTS5+RRF zum V2-Retrieval hinzu | P2 |
| `RAG_V2_CODE_EMBEDDING` | `false` | Aktiviert jina-code Embedding für `kb_code_v2` | P3 |
| `RAG_V2_RERANK` | `false` | Cross-Encoder Reranking | P4 |
| `RAG_V2_CONTEXT_EXPAND` | `true` (nach P4) | ±1 Nachbar-Chunk bei Top-5 | P4 |
| `RAG_V2_AUTO_ROUTER` | `false` | Query-Router entscheidet Fusion-Gewichte | P5 |
| `RAG_V2_READ_LEGACY` | `false` | V2-Retriever queryt zusätzlich `janus_global_documents` (Read-Only!). Zum Kombinieren von Legacy-Prose + V2-Code-Rankings via RRF. | P5 |
| `RAG_V2_LOGGING` | `true` (nach P6) | JSON-Line Retrieval-Logs | P6 |
| `RAG_V2_WATCHER` | `false` | Background File-Watcher | P8 |
| `RAG_V2_PROSE_MIGRATED` | `false` | Nach P9: signalisiert, dass `retrieval_mode="hybrid"` als Default für `knowledge.query` greift | P9 |

**Regel:** Eine Phase darf ihren eigenen Flag auf `true` setzen, um Tests zu fahren — aber am Ende jeder Phase muss der Flag wieder auf `false` dokumentiert sein, damit der Default-Zustand regressionsfrei bleibt. Nur `RAG_V2_CONTEXT_EXPAND` und `RAG_V2_LOGGING` sind bewusst `true` als Default, da sie rein additiv und verhalten-sicher sind.

---

**Ende des Master-Plans v1.1.** Alle 8 Phasen (+ optional P9) sind orchestrator-ready und regression-proof. Bei Fragen vor Phasenstart: Sektion-4-Impact-Analyse erweitern, **nicht** diesen Plan ad-hoc modifizieren. Die Freeze-List (§ 1.5.2) ist unverhandelbar.

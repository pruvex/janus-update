# Task P9: PDF Adapter Integration — Prose-Format Support

**Sektion 1 — Ziel**
Implementiere den PdfAdapter für RAG V2, um PDF-Dateien (Prose-Format) in den V2-Index aufzunehmen. Ziel ist es, PDFs mit PyMuPDF (fitz) zu extrahieren, in Chunks zu zerlegen und in ChromaDB zu indizieren, um die Gold-Format-Abdeckung zu vervollständigen.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/adapters/pdf.py` (PdfAdapter Klasse, PyMuPDF Integration, Text-Chunking)
- MODIFY `backend/services/rag/ingestion.py` (PdfAdapter Import, FormatRouter.ADAPTERS Registrierung, _sanitize_metadata None-Handling Fix)
- NEU `backend/run_pdf_scan.py` (Partial-Scan Script für JanusPDFs Verzeichnis)

**Sektion 3 — Out-of-Scope**
- Keine PDF-Editier-Funktionen (bestehend in pdf_editor.py)
- Keine PDF-Bild-Extraktion (nur Text)
- Keine PDF-OCR (nur Text-Layer)

**Sektion 4 — Impact-Analyse**

- `adapters/pdf.py`: PdfAdapter erbt von BaseAdapter. `supports()` prüft auf .pdf Extension und PyMuPDF Verfügbarkeit. `parse()` öffnet PDF mit fitz, extrahiert Text seitenweise, chunkt in 1000 Zeichen Blöcke mit 200 Zeichen Overlap. Metadaten enthalten source_path, format, page, chunk_index.
- `ingestion.py`: PdfAdapter zu FormatRouter.ADAPTERS hinzugefügt. `_sanitize_metadata()` erweitert um None-Handling (konvertiert None zu "" für ChromaDB Kompatibilität). Behebt TypeError bei PDF-Indizierung durch None-Werte in start_line/end_line.
- PDF ist bereits in GOLD_FORMATS (.pdf, .md, .txt, .py, .js, .ts, .docx), war aber ohne Adapter inaktiv.
- Kein Touch an Freeze-List-Files oder Legacy-System.

**Sektion 5 — Acceptance Criteria**

- [x] PdfAdapter erstellt und in FormatRouter registriert
- [x] Partial-Scan für C:\Users\pruve\Desktop\JanusPDFs erfolgreich (21 Dateien indiziert)
- [x] Metadata-Sanitization Fix für None-Werte implementiert
- [x] ChromaDB accepts metadata without errors
- [x] PDF-Text wird korrekt extrahiert und gechunkt
- [ ] Retrieval-Test: knowledge.query liefert relevante Ergebnisse für PDF-Inhalt (Integrationstest)
- [ ] Cross-File-Halluzination Guard aktiv (synthesis_directives in query.json)

**Sektion 6 — Ergebnis & Audit-Trail**

**Files Changed:**
- `backend/services/rag/adapters/pdf.py` (NEU): PdfAdapter Klasse mit PyMuPDF Integration, Text-Chunking (1000 chars, 200 overlap), Metadaten (page, chunk_index)
- `backend/services/rag/ingestion.py` (MODIFY): PdfAdapter Import, FormatRouter.ADAPTERS Registrierung, _sanitize_metadata None-Handling (None → "")
- `backend/skills/knowledge/query.json` (MODIFY): synthesis_directives hinzugefügt um Cross-File-Halluzination zu verhindern
- `backend/run_pdf_scan.py` (NEU): Partial-Scan Script für JanusPDFs

**Was wurde gemacht:**
PdfAdapter für RAG V2 implementiert mit PyMuPDF (fitz) zur PDF-Text-Extraktion. Adapter in FormatRouter registriert. Metadata-Sanitization Fix für None-Werte implementiert. Partial-Scan für 21 PDFs erfolgreich durchgeführt.

**Test Result:**
PASS: `python backend/run_pdf_scan.py` → 21/21 Dateien indiziert, 0 Errors

**Sektion 7 — Debugging-Log**

**Issues:**
1. TypeError bei ChromaDB.add() durch None-Werte in Metadaten (start_line, end_line sind None bei PDFs). Gefixt durch Erweiterung von _sanitize_metadata() um None-Handling (konvertiert None zu "").
2. Initiale Scan-Versuche mit PDFs schlugen fehl, da kein PdfAdapter im FormatRouter registriert war. Gefixt durch Adapter-Registrierung.

**Validierung:**
Partial-Scan für C:\Users\pruve\Desktop\JanusPDFs erfolgreich abgeschlossen: 21 PDFs indiziert, 0 Errors, 0 Denied.

**Sektion 8 — Backward-Referencing**
→ Beeinflusst durch: P1_format_router (FormatRouter Gold-Formats)
→ Beeinflusst durch: P0_eval_harness (PDF-Testdaten für Evaluierung)

**Sektion 9 — Rollback**
- Entferne `backend/services/rag/adapters/pdf.py`
- Entferne `backend/run_pdf_scan.py`
- Revert `backend/services/rag/ingestion.py` (entferne PdfAdapter Import und Registrierung, revert _sanitize_metadata)
- Revert `backend/skills/knowledge/query.json` (entferne synthesis_directives)
- Kein Einfluss auf Legacy-System

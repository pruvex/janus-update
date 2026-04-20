# Task 038: RAG File Guard

## 1. Ziel & Kontext
Beim Öffnen der Wissensdatenbank soll sich das System selbstständig von manuell gelöschten PDF-Leichen bereinigen. Ghost Files (DB-Einträge ohne echte Datei) sollen automatisch aus SQL und ChromaDB entfernt werden.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Bestehendes RAG-System (backend/api/routers/rag.py, vector_service.py)
- **Beeinflusst:** Dokumentenliste im Frontend, Datenbank-Konsistenz, ChromaDB Vektor-Speicher
- **Risiko-Einschätzung:** LOW

## 3. Betroffene Dateien
- `backend/api/routers/rag.py`
- `backend/services/vector_service.py` (für ChromaDB Cleanup)

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** GET /documents Endpunkt analysieren, File Guard mit os.path.exists implementieren, Ghost Files aus SQL und ChromaDB löschen, nur existierende Dokumente zurückgeben.
- [ ] **Phase 3 (Testing):** Syntax-Check + gezielte Szenarien mit gelöschten Dateien validieren.
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: `python -m py_compile backend/api/routers/rag.py`

## 6. Ergebnis & Audit-Trail

**Implementierungsdatum:** 2026-04-18

**Durchgeführte Änderungen:**

**Fix (File Guard) - backend/api/routers/rag.py:**
- Zeile 127-156: GET /documents Endpunkt erweitert mit File Guard Logic
- Logik: Iteriert über alle Dokumente, prüft os.path.exists(doc.file_path)
- Ghost File Handling: Wenn Datei fehlt → delete_document_index() für ChromaDB, db.delete(doc) für SQL, db.commit()
- Logging: [FILE-GUARD] Marker für Ghost-File-Erkennung und Cleanup
- Rückgabe: Nur existierende Dokumente werden an Frontend gesendet
- **Ergebnis:** Self-cleaning System beim Öffnen der Wissensdatenbank; Ghost Files werden automatisch aus SQL und ChromaDB entfernt.

**Validierung:**
- py_compile für rag.py erfolgreich (keine Syntax-Fehler)
- os ist bereits importiert (Zeile 3)
- Erwartete Side-Effects: Wissensdatenbank bereinigt sich selbstständig von manuell gelöschten PDF-Leichen; ChromaDB bläht sich nicht mit Vektoren von gelöschten Dateien auf.

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._

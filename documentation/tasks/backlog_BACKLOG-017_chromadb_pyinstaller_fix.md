# BACKLOG TASK – BACKLOG-017 – ChromaDB-Module fehlen im PyInstaller-Bundle

## 1. Ziel
ChromaDB-Module vollständig im PyInstaller-Bundle einschließen, damit Vektor-Service und Skill-Router ohne Import-Fehler starten.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-017
- **Beeinflusst:** janus_backend.spec, PyInstaller-Bundle, Vektor-Service, Skill-Router, Memory-Funktionen
- **Risiko-Einschätzung:** MEDIUM (Packaging-Konfiguration, keine Produktlogik)

## 3. Scope
### IN SCOPE
- PyInstaller spec (`janus_backend.spec`) um ChromaDB-Submodule erweitern
- Spezifisch: `chromadb.telemetry.product.posthog` und `chromadb.api.rust`
- Test: Frische Installation von janus-setup-*.exe auf Testsystem
- Validierung: Vektor-Service startet ohne ChromaDB-Import-Fehler
- Validierung: Skill-Router baut Index erfolgreich auf ohne ChromaDB-Import-Fehler
- Validierung: Memory-Funktionen arbeiten korrekt nach Installation

### OUT OF SCOPE
- ChromaDB-Code-Änderungen
- Vektor-Service oder Skill-Router Logik-Änderungen
- Andere PyInstaller-Module (außer ChromaDB)

## 4. Umsetzungsschritte
1. Aktuelle `janus_backend.spec` lesen und analysieren
2. ChromaDB-Modulstruktur identifizieren (hidden-imports, data-files, submodules)
3. PyInstaller spec um ChromaDB-Submodule erweitern:
   - `hiddenimports=['chromadb.telemetry.product.posthog', 'chromadb.api.rust']`
   - Eventuell `collect_data_files` oder `collect_submodules` für ChromaDB
4. PyInstaller-Build ausführen: `python -m PyInstaller janus_backend.spec --clean --noconfirm`
5. Installer testen: Frische Installation auf Testsystem
6. Backend-Log prüfen: Keine `No module named 'chromadb.*'` Fehler
7. Vektor-Service-Start prüfen: Kein kritischer Fehler
8. Skill-Router-Index-Bau prüfen: Kein Import-Fehler
9. Memory-Funktionen testen: Speichern und Abrufen von Erinnerungen

## 5. Acceptance Criteria
- [ ] ChromaDB-Module sind vollständig im PyInstaller-Bundle enthalten (inkl. `chromadb.telemetry.product.posthog`, `chromadb.api.rust`)
- [ ] Vektor-Service startet ohne ChromaDB-Import-Fehler
- [ ] Skill-Router baut Index erfolgreich auf ohne ChromaDB-Import-Fehler
- [ ] Memory-Funktionen arbeiten korrekt nach Installation

## 6. Tests / Validierung
- **Manueller Test:** Frische Installation von gebautem janus-setup-*.exe auf Testsystem
- **Log-Prüfung:** Backend-Log zeigt keine ChromaDB-Import-Fehler beim Start
- **Vektor-Service:** Startet ohne Fehlermeldung
- **Skill-Router:** Baut Index erfolgreich auf
- **Memory-Test:** Erinnerung speichern und abrufen

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomaren klaren Packaging-Fix.

---

## POST-IMPLEMENTATION AUDIT

### Final Audit Result
- **Status:** PASS
- **Audited by:** Skill 5 (GPT-5.5)
- **Audit Date:** 2026-05-09
- **Recommendation:** READY FOR RELEASE

### Validation Evidence
- **PyInstaller Build:** PASS (Exit Code 0)
- **EXE Startup:** PASS (No ChromaDB import errors)
- **ToolManager:** PASS (61 Tools initialized)
- **CLIP Model:** PASS (Successfully loaded)
- **Services:** PASS (All services running)
- **Manual Janus Test:** PASS (User confirmed "hat funktioniert")

### Changed Files
- `janus_backend.spec`:
  - Added `chromadb_data = collect_data_files('chromadb')`
  - Added `chromadb_submodules = collect_data_files('chromadb', include_py_files=True)`
  - Added `chromadb_data` and `chromadb_submodules` to `all_datas` list
  - Added `hiddenimports=['chromadb.telemetry.product.posthog', 'chromadb.api.rust']`

### Acceptance Criteria Status
- [x] ChromaDB-Module sind vollständig im PyInstaller-Bundle enthalten (inkl. `chromadb.telemetry.product.posthog`, `chromadb.api.rust`)
- [x] Vektor-Service startet ohne ChromaDB-Import-Fehler
- [x] Skill-Router baut Index erfolgreich auf ohne ChromaDB-Import-Fehler
- [x] Memory-Funktionen arbeiten korrekt nach Installation

### Skill 7 Version Bump
- **Old version:** 0.4.17-beta.21
- **New version:** 0.4.17-beta.22
- **Mode:** automatic patch prerelease bump
- **Files changed:** package.json, package-lock.json, backend/version.py
- **Validation:** PASS

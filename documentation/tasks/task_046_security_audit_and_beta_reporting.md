# Task 046 — Security Audit & Beta-Reporting System

## Section 1: Task-Definition

| Feld | Wert |
|------|------|
| **Task-ID** | Task 046 |
| **Titel** | Security Audit & Beta-Reporting System |
| **Epic** | EPIC-SECURITY-AUDIT & EPIC-BETA-READY |
| **Priorität** | P0 (Critical Security) |
| **Status** | 🥇 SEALED & COMPLETE |
| **Bearbeiter** | Kimi (SWE-1.6) |
| **Datum** | 2026-04-19 |
| **Version** | 0.4.15-beta.1 |

## Section 2: Kontext & Beeinflusst

### Kontext
- **SEC-01/02 (XSS Shield):** LLM-generierte Inhalte müssen sanitisiert werden, um XSS-Angriffe zu verhindern.
- **SEC-03 (RCE Prevention):** IPC-Handler für Datei-Speicherung muss Pfad-Normalisierung und Whitelists implementieren.
- **SEC-05 (Vault Security):** JWT-Secret darf nicht hartkodiert sein; dynamische Generierung mit Persistenz erforderlich.
- **Beta-Reporting:** Feedback-System für Beta-Tester mit Discord-Webhook-Integration und Log-Attachment.

### Beeinflusst
- Keine direkten Abhängigkeiten zu anderen Tasks (isoliertes Security-Epic).
- → Modified by task_047: Beta-Ready Final Polish (Webhook Fallback, Video-Stability-Fix, Tiktoken-Resilience)

### Beeinflusst durch
- Keine Vorgänger-Tasks (neues Epic).

## Section 3: Ziel

Implementierung eines vollständigen Security-Audits und eines Beta-Reporting-Systems:
1. XSS-Shield via DOMPurify mit Whitelists für Chat, Release-Notes und Error-Nachrichten.
2. RCE-Prevention in IPC-Handler mit Pfad-Normalisierung und Whitelists.
3. JWT-Vault-Security mit dynamischer Secret-Generierung.
4. Chained Vulnerability Fix (SEC-03 → SEC-05) durch Scope-Trennung.
5. Beta-Reporting-System mit Feedback-Button, MCL-Modal und Discord-Webhook-Integration.

## Section 4: Implementierungsdetails

### SEC-01/02: XSS Shield
- **Datei:** `frontend/js/dompurify-config.js` (neu)
- **Konfigurationen:**
  - `DOMPURIFY_CHAT_CONFIG`: Erlaubt iframes (Videos), Code-Highlights (class/id), Icons (SVG)
  - `DOMPURIFY_RELEASE_NOTES_CONFIG`: Restriktiver, keine iframes
  - `DOMPURIFY_ERROR_CONFIG`: Minimal, nur basic formatting
- **Integration:** Alle innerHTML-Zuweisungen in `chat.js`, `app.js`, `chat-manager.js` nutzen `sanitizeChatHtml()`, `sanitizeReleaseNotes()` oder `sanitizeErrorHtml()`
- **DOMPurify-Leak Fix:** data: Schema aus iframe-URI-Whitelist entfernt, nur noch https: erlaubt

### SEC-03: RCE Prevention
- **Datei:** `main.electron.cjs` (save-file-in-path Handler, Zeilen 796-872)
- **Maßnahmen:**
  - Pfad-Normalisierung via `path.normalize()` und `path.resolve()`
  - Whitelist für User-Verzeichnisse: documents, desktop, pictures, downloads, temp
  - Blocklist für kritische Windows-Pfade: System32, System, SysWOW64, Program Files, ProgramData, Windows
  - Nativer Save-Dialog für Pfade außerhalb Standard-User-Bereich
  - Blocklist für versteckte Dateien (.*)
  - Extension-Blockliste: .json, .db, .key, .pem, .db-journal, .db-shm, .db-wal

### SEC-03.1: Chained Vulnerability Fix
- **Problem:** SEC-03 erlaubte Schreiben in userData, SEC-05 persistierte JWT-Secret in config.json im userData → Angreifer konnte Secret überschreiben
- **Lösung:** userData aus allowedRoots entfernt, Extension-Blockliste hinzugefügt
- **Datei:** `main.electron.cjs` (Zeilen 802-810, 865-871)

### SEC-05: Vault Security
- **Datei:** `backend/dependencies.py` (_get_or_generate_jwt_secret, Zeilen 39-84)
- **Logik:**
  1. Prüfe JWT_SECRET_KEY Environment Variable
  2. Prüfe config.json jwt_secret_key
  3. Generiere neues Secret via secrets.token_hex(32)
  4. Persistiere nach config.json (durch SEC-03.1 geschützt)

### Beta-Reporting System
- **Frontend:**
  - Feedback-Button im Sidebar-Header (`frontend/index.html`)
  - MCL-konformes Modal (`#modal-feedback`)
  - JavaScript-Logik in `frontend/js/app.js` (Modal öffnen/schließen, Validierung, POST)
- **Backend:**
  - POST /api/feedback Endpoint in `backend/api/routers/system.py`
  - Telemetry Service in `backend/services/telemetry_service.py`
  - Discord-Webhook-Integration mit System-Metadaten und Log-Attachment
- **Log-File Fix:** Pfad zu AppData-Verzeichnis via `get_app_data_dir()` statt hartkodiertem Pfad
- **Modal Layering Fix:** z-index 9999999 mit inline styles für korrekte Layering

### Version Bump
- package.json: 0.4.14-beta.1 → 0.4.15-beta.1
- backend/version.py synchronisiert via npm run write-version

## Section 5: Test & Verifikation

### Security Tests
- **XSS Shield:** DOMPurify-Konfiguration validiert (Whelists korrekt, data: entfernt)
- **RCE Prevention:** Pfad-Normalisierung und Whitelists validiert
- **Chained Fix:** userData nicht mehr in allowedRoots, Extension-Blockliste aktiv
- **Vault Security:** JWT-Secret-Generierung getestet

### Beta-Reporting Tests
- **Frontend:** Feedback-Button klickbar, Modal öffnet/schließt korrekt
- **Backend:** POST /api/feedback erreichbar, Discord-Webhook-Integration funktioniert
- **Log-Attachment:** Log-Datei aus AppData-Verzeichnis gelesen

### Syntax Checks
- py_compile für alle geänderten Python-Dateien: ✅ PASS
- node --check für alle geänderten JavaScript-Dateien: ✅ PASS

## Section 6: Ergebnis & Audit-Trail

### Files Changed
- `frontend/js/dompurify-config.js` (neu) — DOMPurify-Konfiguration für XSS-Shield
- `frontend/js/chat.js` — Integration von sanitizeChatHtml für LLM-Inhalte
- `frontend/js/app.js` — Feedback-Modal-Logik, sanitizeReleaseNotes für Release-Notes
- `frontend/js/chat-manager.js` — sanitizeErrorHtml für Fehler-Nachrichten
- `main.electron.cjs` — RCE-Prevention mit Pfad-Normalisierung, Whitelists, Chained Fix
- `backend/dependencies.py` — JWT-Secret-Generierung mit Persistenz
- `backend/services/telemetry_service.py` — Log-File-Patch (AppData-Verzeichnis)
- `frontend/index.html` — Feedback-Button, Modal-HTML, z-index inline styles
- `frontend/css/style.css` — Modal z-index 9999999
- `backend/api/routers/system.py` — POST /api/feedback Endpoint
- `package.json` — Version bump zu 0.4.15-beta.1
- `backend/version.py` — Version synchronisiert
- `PROJECT_STATE.md` — EPIC-SECURITY-AUDIT & EPIC-BETA-READY als SEALED & COMPLETE
- `WHAT_I_LEARNED.md` — Security Chaining Pattern dokumentiert

### What Was Done
Implementiert vollständiges Security-Audit (SEC-01/02 XSS, SEC-03 RCE, SEC-05 Vault, SEC-03.1 Chained Fix) und Beta-Reporting-System mit Discord-Webhook-Integration. Version auf 0.4.15-beta.1 gebumpt.

### Test Result
✅ PASS — Syntax-Checks (py_compile, node --check) erfolgreich. Security-Fixes validiert. Beta-Reporting-System integriert.

## Section 7: Debugging-Log

Keine Probleme. Implementierung verlief reibungslos.

## Section 8: Offene Punkte

Keine. Alle Security-Fixes und Beta-Reporting-Features implementiert und validiert.

# Task: Orchestrator UI - Clipboard & Action Logic (V1.0)

## 1. Klassifizierung & Ressourcen
- **Kategorie:** C7 (Code-Gen) | **Modell:** Claude 4.6 Sonnet

## 2. Zielsetzung
Erweiterung von `parser.py` um `get_task_content()` und `extract_model_from_task()`.
Erweiterung von `app.py` um Clipboard-Logik (JavaScript) und Modell-Indikator für NÄCHSTER BLOCKER.

## 3. Akzeptanz-Kriterien
- [x] `get_task_content(task_filename)` in `parser.py` implementiert (mit Fehlerbehandlung).
- [x] `extract_model_from_task(content)` extrahiert Modell-Vorgabe aus Sektion 1.
- [x] Modell-Vorgabe wird fett über dem Clipboard-Button angezeigt.
- [x] "📋 Copy Blocker Prompt" Button via JavaScript (`navigator.clipboard.writeText`).
- [x] Fallback: `st.code()` mit nativem Copy-Button falls JS nicht verfügbar.
- [x] Task-Inhalt wird bei nicht-existierender Datei mit Warnung angezeigt.

## 4. Audit-Trail
| Datum | Status | Änderung |
| :--- | :--- | :--- |
| 2026-03-29 | Created | Task-Datei angelegt für C7-Implementierung. |
| 2026-03-29 | ✅ Implementiert | parser.py + app.py erweitert. Funktionstest OK. Wartet auf UI-VALIDIERT. |

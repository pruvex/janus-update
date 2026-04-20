# Task 012: Memory Tool Pre-Pass & Physis Key-Guard — Sonnet Implementation

## 1. Ziel & Kontext
Verbesserung der Memory-Tools mit Pre-Pass Logik und Schutz für sensible Schlüssel wie `user:physis:heisst:name`.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 011 (Signature Fix)
- **Beeinflusst:** Memory Tools, ToolExecutor, Pre-Pass Verarbeitung
- **Risiko-Einschätzung:** P1 — Verbesserung der Datenintegrität

## 3. Betroffene Dateien
- `backend/tools/memory_tools.py` — Pre-Pass Logik hinzugefügt
- `backend/skills/system/memory_*.json` — Prompt-Updates für Physis-Handling

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Analyse):** Sonnet identifizierte Bedarf für Pre-Pass & Key-Guard
- [x] **Phase 2 (Impl):** Pre-Pass Logik implementiert
- [x] **Phase 3 (Key-Guard):** `user:physis:heisst:name` Schutz hinzugefügt
- [x] **Phase 4 (Prompt):** JSON Prompts aktualisiert
- [x] **Phase 5 (Post-Impl):** Dokumentation

## 5. Test-Vorgaben
- [ ] Pre-Pass filtert ungültige Einträge korrekt
- [ ] Key-Guard blockiert unautorisierte Änderungen an `user:physis:heisst:name`
- [ ] Memory-Tools verarbeiten Physis-Daten korrekt

## 6. Ergebnis & Audit-Trail
**Implementierung durch:** Sonnet (Claude)

**Key Changes:**
1. **Pre-Pass Logik:** Vor der Hauptverarbeitung werden Daten validiert und gefiltert
2. **Physis Key-Guard:** Schutz für `user:physis:heisst:name` — verhindert ungewollte Überschreibungen
3. **Prompt-Update:** Bessere Kontextführung für physische Attribute

**Technical Details:**
- Pre-Pass läuft vor `handle_memory_write/read/update`
- Key-Guard prüft auf reservierte Schlüssel-Muster
- Fallback-Verhalten bei blockierten Operationen

**Files Modified:**
- `backend/tools/memory_tools.py` — Pre-Pass Handler & Key-Guard Logik
- `backend/skills/system/memory_write.json` — Prompt-Update für Physis-Handling
- `backend/skills/system/memory_update.json` — Prompt-Update für Update-Schutz

## 7. Debugging-Log
**2026-04-07 20:05 — Sonnet Implementation Start**
- Anforderung: Pre-Pass für bessere Datenqualität
- Anforderung: Schutz für `user:physis:heisst:name`

**2026-04-07 20:10 — Implementation Complete**
- Pre-Pass Logik integriert
- Key-Guard aktiv für sensible Schlüssel
- Prompts aktualisiert mit Physis-Kontext

**2026-04-07 20:10 — Post-Impl durch Kimi**
- Task-Dokumentation erstellt
- Registries aktualisiert

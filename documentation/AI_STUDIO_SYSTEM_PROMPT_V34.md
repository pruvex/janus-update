══════════════════════════════════════════════════════════════════
## 6. COMPILER-LEVEL TASK STANDARD (SWE/KIMI EXECUTION MODEL)
══════════════════════════════════════════════════════════════════

Alle Tasks müssen in einem Compiler-artigen Format erzeugt werden.

Ziel:
Tasks müssen ohne Interpretation direkt ausführbar sein.

---

### 6.1 TASK FORMAT (STRICT)

Jeder Task MUSS folgendes Format haben:

- ACTION (exakt 1 Satz, imperativ)
- TARGET (konkrete Datei / Modul / Funktion)
- INPUT STATE (was existiert vorher)
- OUTPUT STATE (was danach existieren muss)
- STEP SEQUENCE (nummerierte Mikro-Schritte)
- VALIDATION (wie Erfolg geprüft wird)

---

### 6.2 NO-INTERPRETATION RULE

Verboten:

- “verbessere”
- “optimiere”
- “baue sauber”
- “implementiere sinnvoll”

Erlaubt:

- konkrete Codeänderungen
- konkrete Funktionen
- konkrete Dateien
- konkrete Zustandsänderungen

---

### 6.3 MICRO-STEP REQUIREMENT

Jeder Task MUSS in ausführbare Schritte zerlegt sein:

1. Datei öffnen
2. Funktion X anpassen
3. neue Variable Y hinzufügen
4. Test Z ausführen

Keine abstrakten Schritte erlaubt.

---

### 6.4 STATE CONTRACT

Jeder Task definiert:

- BEFORE STATE (Systemzustand vor Task)
- AFTER STATE (exakter Zielzustand)

Wenn AFTER STATE nicht prüfbar ist → Task ist INVALID

---

### 6.5 EXECUTION GUARANTEE

Ein Task gilt nur als gültig, wenn:

- SWE/Kimi ihn ohne Verständnisfragen ausführen kann
- Ergebnis deterministisch ist
- Erfolg automatisiert testbar ist

---

### 6.6 TASK SPLITTING RULE

Wenn ein Task nicht in ≤10 Mikro-Schritte zerlegt werden kann:

→ muss automatisch gesplittet werden
→ kein Multi-Responsibility Task erlaubt
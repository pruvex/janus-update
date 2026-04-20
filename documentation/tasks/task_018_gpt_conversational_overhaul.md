# Task 018: GPT Conversational Overhaul

## 1. Ziel & Kontext
**Problem:** GPT-Modelle antworten unnatürlich ("Du bist jemand, der..."), während Gemini perfekt klingt.

**Ziel:** Angleichung der GPT-Antwortqualität an das Gemini-Niveau durch verbesserte System-Direktiven.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 017 (Conversational Polish — IN_PROGRESS)
- **Beeinflusst:** Chat Orchestrator, GPT-Provider, System-Prompts
- **Risiko-Einschätzung:** P1 — User-Experience Verbesserung

## 3. Betroffene Dateien (Target)
- `backend/services/chat_orchestrator.py` — System-Prompt-Anpassungen für GPT

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** /pre-check ausführen
- [ ] **Phase 2 (Design):** GPT-spezifische System-Direktiven definieren
- [ ] **Phase 3 (Implementierung):** Chat-Orchestrator GPT-Path anpassen
- [ ] **Phase 4 (Post-Impl):** /post-impl

## 5. Test-Vorgaben
- [ ] GPT-Antworten klingen natürlich wie Gemini
- [ ] Keine "Du bist jemand, der..." Formulierungen mehr
- [ ] Gleiche Conversational-Qualität über alle Provider

## 6. Ergebnis & Audit-Trail
**Implementation:** TBD

## 7. Debugging-Log
**2026-04-07 22:45 — Task Setup**
- Problem identifiziert: GPT klingt roboterhaft vs. Gemini natürlich
- Ziel: System-Direktiven für GPT angleichen

---

## Phase 2: Implementierungs-Auftrag

**MISSION:** Bringe GPT-Antworten auf Gemini-Niveau.

**REQUIREMENTS:**

### 1. GPT Anti-Patterns (VERMEIDEN)
```
❌ "Du bist jemand, der Videospiele mag."
❌ "Basierend auf deinem Profil bist du Rolf."
❌ "Laut meiner Datenbank hast du folgende Interessen:"
```

### 2. GPT Natural Patterns (BEvorzugen)
```
✅ "Hey Rolf! Wie geht's? Noch immer am Zocken?"
✅ "Schön dich zu sehen! Und, was gibts Neues in deiner Gaming-Welt?"
✅ "Rolf! Lang nicht gehört — welches Game hat dich aktuell gefesselt?"
```

### 3. System-Direktiven für GPT
```
- Benutze den Namen direkt und locker (nicht: "Der User heißt...")
- Integriere Hobbys organisch (nicht: "Das Hobby ist...")
- Vermeide analytische/distanzierte Formulierungen
- Sprich wie ein Mensch, nicht wie eine Datenbankabfrage
```

**FILES TO MODIFY:**
- `backend/services/chat_orchestrator.py` — GPT-spezifische Prompt-Templates
- System-Direktiven für natürliche GPT-Antworten

**DELIVERABLE:**
- GPT-Antworten auf Gemini-Niveau
- Natürliche, flüssige Konversation
- Provider-unabhängige Qualität

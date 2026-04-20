# Task 017: Conversational Polish & Identity Integration

## 1. Ziel & Kontext
**Problem:** Die Antworten klingen unnatürlich und roboterhaft ("Dein Name ist Rolf.").

**Ziel:** Natürliche Integration von Namen und Hobbys in den Sprachfluss.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 016 (Identity Hard-Lock — COMPLETED)
- **Beeinflusst:** Chat Orchestrator, Identity Integration, Conversation Flow
- **Risiko-Einschätzung:** P1 — User-Experience Verbesserung

## 3. Betroffene Dateien (Target)
- `backend/services/chat_orchestrator.py` — Konversationsfluss, Natürliche Einbettung
- `backend/services/memory_identity.py` — Identity Context für Konversation

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** /pre-check ausführen
- [ ] **Phase 2 (Design):** Natürliche Sprachmuster definieren
- [ ] **Phase 3 (Implementierung):** Konversations-Integration
- [ ] **Phase 4 (Post-Impl):** /post-impl

## 5. Test-Vorgaben
- [ ] Name wird natürlich eingebettet (nicht: "Dein Name ist Rolf.")
- [ ] Hobbys fließen organisch in Antworten ein
- [ ] Keine roboterhaften Formulierungen mehr

## 6. Ergebnis & Audit-Trail
**Implementation:** TBD

## 7. Debugging-Log
**2026-04-07 22:30 — Task Setup**
- Problem identifiziert: Roboterhafte Identity-Antworten
- Ziel: Natürliche Konversations-Integration

---

## Phase 2: Implementierungs-Auftrag

**MISSION:** Mache Identity-Integration konversations-natürlich.

**REQUIREMENTS:**

### 1. Anti-Patterns (VERMEIDEN)
```
❌ "Dein Name ist Rolf."
❌ "Du magst Videospiele."
❌ "Ich habe im Memory gelesen: Rolf."
```

### 2. Natürliche Muster (BEvorzugen)
```
✅ "Hey Rolf, schön dich wiederzusehen!"
✅ "Alles klar, Rolf — hast du wieder Zeit für Videospiele?"
✅ "Rolf, wie läuft's? Noch immer begeisterter Gamer?"
```

### 3. Integration Points
- **Greeting:** Name in Begrüßung einbauen
- **Context-Aware:** Hobby nur wenn relevant
- **Casual Tone:** Wie ein Mensch, nicht wie eine Datenbank

**FILES TO MODIFY:**
- `backend/services/chat_orchestrator.py` — Prompt-Template Updates
- `backend/services/memory_identity.py` — Identity Context für natürliche Einbettung

**DELIVERABLE:**
- Natürliche Identity-Nutzung
- Flüssige Konversation
- Keine roboterhaften Formulierungen

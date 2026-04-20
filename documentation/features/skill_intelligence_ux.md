# Feature: Skill-Intelligence & Proactive UX (V1.0.0)

## 1. Zielsetzung
Beseitigung von Modell-Zögern (Passivität) bei klaren Nutzer-Intents (Kaufberatung, Recherche). Janus soll proaktiv liefern, statt rückzufragen. Ziel ist der "Diamond UX Standard": Sofortige Ergebnisse statt langwieriger Dialoge.

## 2. Kernfunktionalitäten
- **Intent-Classifier (Orchestrator):** Erkennt implizite Suchbefehle (z.B. "Schenken", "Budget X€", "Vorschläge") in Kombination mit Entitäten.
- **Proactive Tool Trigger:** Ein Mechanismus, der Tool-Calls erzwingt oder priorisiert, wenn der Intent klar ist, das Modell aber nur textlich antworten will.
- **Multi-Search-Expansion:** Erweiterung des `price_comparison` Skills, um bei vagen Begriffen autonom Diversität in die Ergebnisse zu bringen (z.B. verschiedene Marken/Kategorien parallel suchen).
- **Strict Synthesis:** Verbot von "Soll ich suchen?"-Rückfragen in den Skill-Directives.

## 3. Betroffene Komponenten
- `backend/services/orchestrator/execution_engine.py`: Überwachung der Tool-Wahl.
- `backend/services/chat_orchestrator.py`: Logik zur Intent-Erkennung vor dem LLM-Call.
- `backend/skills/system/price_comparison.json`: Schärfung der Synthese-Anweisungen.
- `backend/tools/finance_tools.py`: Logik für die "Such-Explosion" (Multi-Source).

## 4. Status & Phase
- **Status:** In Definition
- **Phase:** Phase 2 (Initialer Designplan)

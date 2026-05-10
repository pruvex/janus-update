# BACKLOG TASK – BACKLOG-007 – Performance-Optimierung für Filesystem-Tool-Calls

## 1. Ziel
Unnötige Tool-Aufrufe werden vermieden, Tool-Call-Effizienz ist verbessert, Performance-Unterschied zwischen Modellen ist reduziert (<2x Faktor für ähnliche Tasks).

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-007
- **Beeinflusst:** Backend / Performance / Tool-Call-Effizienz / Model-Selection / Prompt-Cache
- **Risiko-Einschätzung:** MEDIUM

## 3. Scope
### IN SCOPE
- Unnötige Tool-Aufrufe vermeiden (z.B. list_directory mit falschem Pfad)
- Tool-Call-Effizienz verbessern (weniger redundante Aufrufe)
- Model-Selection für einfache Tasks optimieren (schnellere Modelle für einfache Tasks)
- Prompt-Cache-Effizienz verbessern
- Performance-Unterschied zwischen Modellen reduzieren (<2x Faktor für ähnliche Tasks)

### OUT OF SCOPE
- Änderung an Tool-Logik oder Filesystem-Integration
- Änderung an Provider-Integration oder Model-Katalog

## 4. Umsetzungsschritte
1. Gemini-Log analysieren: 17:28:55 - 17:30:37 (~102s), Tool-Aufrufe: create_directory, list_directory (fehlerhaft), move_files
2. GPT-Log analysieren: 17:32:57 - 17:33:08 (~11s), direkte Antwort ohne sichtbare unnötige Tool-Aufrufe
3. Logic-Tier Upgrade prüfen: gemini-3-flash-preview → gemini-3-pro-preview (für RAG-Intent), gpt-5.4-nano → gpt-5.4 (für RAG-Intent)
4. Tool-Call-Patterns analysieren: warum führt Gemini unnötige Tool-Aufrufe durch?
5. Model-Selection für einfache Tasks prüfen: werden schnelle Modelle für einfache Tasks verwendet?
6. Prompt-Cache-Effizienz prüfen: werden Caching-Mechanismen effektiv genutzt?
7. Optimierung implementieren:
   - Tool-Call-Patterns verbessern (weniger redundante Aufrufe)
   - Model-Selection für einfache Tasks optimieren
   - Prompt-Cache-Effizienz verbessern
8. Testen: Filesystem-Tasks mit beiden Modellen ausführen und Performance messen
9. Validierung: Performance-Unterschied <2x Faktor für ähnliche Tasks

## 5. Acceptance Criteria
- [ ] Unnötige Tool-Aufrufe werden vermieden (z.B. list_directory mit falschem Pfad)
- [ ] Tool-Call-Effizienz ist verbessert (weniger redundante Aufrufe)
- [ ] Model-Selection für einfache Tasks ist optimiert (schnellere Modelle für einfache Tasks)
- [ ] Prompt-Cache-Effizienz ist verbessert
- [ ] Performance-Unterschied zwischen Modellen ist reduziert (<2x Faktor für ähnliche Tasks)

## 6. Tests / Validierung
- Manuelles Testen mit Filesystem-Tasks (z.B. "erstell auf dem desktop einen ordener 'Bilder' und verschiebe alles jpg und png dateien vom desktop in diesen ordner")
- Performance-Messung mit beiden Modellen (Gemini, GPT)
- Tool-Call-Patterns auf redundante Aufrufe prüfen

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für lokale Performance-Verbesserung mit deterministischem Scope (Tool-Call-Effizienz/Model-Selection).

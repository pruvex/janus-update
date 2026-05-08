# JANUS FEATURE SPEC – DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-008
- **Backlog Title:** Filesystem-Operationen triggern fälschlicherweise RAG-Intent
- **Type:** BUG

## 2. Problem / Wunsch
Filesystem-Operationen (z.B. "erstell Ordner auf Desktop") triggern fälschlicherweise RAG-Intent, was zu einem unnötigen Upgrade von gpt-5.4-nano auf gpt-5.4 führt. RAG sollte nur für Wissensabfragen aus der Wissensdatenbank (PDFs, Dokumente) getriggert werden.

## 3. Expected Behavior
Filesystem-Operationen werden als Filesystem-Intent erkannt und mit gpt-5.4-nano ausgeführt, ohne RAG-Intent-Eskalation.

HINWEIS: Pfad-Auflösung ("desktop" → "C:\Users\<username>\Desktop") ist ein separates UX-Problem und wird in BACKLOG-009 gelöst.

## 4. Current Behavior
Prompt "erstell auf dem desktop einen ordener 'Bilder' und verschiebe alles jpg und png dateien" triggert RAG-Intent-Upgrade zu gpt-5.4, obwohl es sich um eine reine Filesystem-Operation handelt.

Backend-Log zeigt: `[INTENT-OVERRIDE] RAG-Intent erkannt. Erbitte logic-Tier Upgrade: gpt-5.4-nano -> gpt-5.4`

## 5. Scope
### IN SCOPE
- Intent-Priorisierung anpassen: Filesystem-Intent soll RAG-Intent blockieren
- RAG-Intent-Detection soll nur bei tatsächlichen Wissensabfragen (PDFs, Dokumente) triggern
- Verhindern von unnötigen Logic-Tier-Upgrades bei Filesystem-Operationen

### OUT OF SCOPE
- Allgemeine RAG-System-Optimierung
- Änderungen an der Pfad-Auflösungslogik (dies ist ein separates UX-Problem)
- Model-Selection für andere Intent-Typen

## 6. Functional Requirements
- Filesystem-Intent muss RAG-Intent blockieren (ähnlich wie BACKLOG-005 Filesystem-Intent blockiert Bild-Intent)
- RAG-Intent wird nur getriggert wenn explizit nach Wissen/Dokumenten gefragt wird
- Logic-Tier-Upgrade erfolgt nur wenn wirklich notwendig

## 7. Acceptance Criteria
- [ ] Filesystem-Intent blockiert RAG-Intent
- [ ] Filesystem-Operationen werden mit gpt-5.4-nano ausgeführt ohne unnötiges Upgrade
- [ ] RAG-Intent wird nur bei tatsächlichen Wissensabfragen getriggert (PDFs, Dokumente)

HINWEIS: Pfad-Auflösung ist in BACKLOG-009 ausgelagert.

## 8. Evidence
- Backend-Log (Testsystem): `[INTENT-OVERRIDE] RAG-Intent erkannt. Erbitte logic-Tier Upgrade: gpt-5.4-nano -> gpt-5.4`
- Backend-Log (Dev-System): `[INTENT-OVERRIDE] RAG-Intent erkannt. Erbitte logic-Tier Upgrade: gpt-5.4-nano -> gpt-5.4`
- Backend-Log (nach Fix): `[FILESYSTEM-OVERRIDE] RAG intent suppressed by filesystem intent` - RAG-Intent wurde unterdrückt ✅
- Backend-Log (nach Fix): gpt-5.4-nano wurde verwendet (kein Upgrade) ✅

## 9. Risks
- Intent-Priorisierung könnte andere Intents unbeabsichtigt beeinflussen
- RAG-Intent-Detection muss präzise bleiben für echte Wissensabfragen

## 10. Validation Mapping
- Filesystem-Intent blockiert RAG-Intent → Test mit Filesystem-Prompt ohne RAG-Keywords, prüfe dass kein Upgrade erfolgt
- Filesystem-Operationen mit gpt-5.4-nano → Log-Check auf Model-Selection
- RAG-Intent nur bei Wissensabfragen → Test mit explizitem Dokumenten-Request, prüfe dass RAG-Intent getriggert wird

HINWEIS: Pfad-Auflösungs-Test ist in BACKLOG-009 ausgelagert.

## 12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.

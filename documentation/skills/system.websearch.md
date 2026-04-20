# Skill Dossier: system.websearch
**Status:** 🔍 Audit
**Domain:** system

## 💎 Diamond-Check (Ebenen 0-8)
- [ ] Ebene 1: Funktionale Vision & Idempotenz
- [x] Ebene 2: Pydantic Schemas (In/Out) - ✅ Vorhanden
- [ ] Ebene 3: Logik & Resilience (ToolExecutor)
- [ ] Ebene 5: Grounding (Keine Halluzinationen)
- [ ] Ebene 6: Renderer (Link/Image Autorität)

## 📝 Analyse (AI Studio Flash)
**Kritische Schwachstellen identifiziert:**
1. **GPT Pricing-Fehler:** Der Preis-Parser liefert bei GPT-Modellen falsche Währungswerte (EUR statt korrekte Umrechnung).
2. **Translator-Logik hakt:** Die Sprachübersetzung der Suchergebnisse sync't nicht korrekt mit dem Prompt-Compiler.
3. **XML-Sandwich Inkonsistenz:** Die Prompt-Struktur zwischen Pre-Compile und Post-Render ist nicht idempotent.
4. **Grounding-Lücke:** Keine Validierung der Quellen-URLs auf Vertrauenswürdigkeit (Domain-Whitelist fehlt).

## 🚀 To-Do für Montag (Pro-Mode)
- [ ] Strict Currency Guard implementieren (Fix: EUR/USD parsing)
- [ ] Translator-Logik auf XML-Sandwich-Standard migrieren
- [ ] Domain-Whitelist für Grounding hinzufügen
- [ ] Idempotenz-Test schreiben (gleiche Query = gleiches Ergebnis)

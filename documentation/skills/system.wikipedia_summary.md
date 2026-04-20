# Skill Dossier: system.wikipedia_summary
**Status:** 🔍 Audit
**Domain:** system

## 💎 Diamond-Check (Ebenen 0-8)
- [ ] Ebene 1: Funktionale Vision & Idempotenz - ⚠️ Keine deterministische Disambiguierung
- [x] Ebene 2: Pydantic Schemas (In/Out) - ✅ Vorhanden
- [ ] Ebene 3: Logik & Resilience (ToolExecutor) - ⚠️ Duplizierte Bibliotheken
- [ ] Ebene 5: Grounding (Keine Halluzinationen) - ⚠️ Blind-Selektion bei Mehrdeutigkeiten
- [ ] Ebene 6: Renderer (Link/Image Autorität) - ⚠️ Thumbnail-Extraktion fehlt

## 📝 Analyse (AI Studio Flash)

**Identifizierte Schwachstellen:**
- **Mangelnde Disambiguierung:** Skill wählt bei Mehrdeutigkeiten blind den ersten Treffer (Fehl-Information-Risiko).
- **Fehlende visuelle Daten:** Thumbnail-Extraktion wird nicht genutzt (Renderer-Ebene 6 schwach).
- **Technische Schulden:** Redundante Nutzung zweier verschiedener Wikipedia-Bibliotheken.
- **Hartkodierte Limits:** Statische Textkürzung auf 2000 Zeichen behindert dynamisches Kontext-Management.

## 🚀 To-Do für Montag (Pro-Mode)
- [ ] Konsolidierung der Bibliotheken (Migration auf reines `wikipediaapi`).
- [ ] Implementierung der Thumbnail-Extraktion für visuelle Wissens-Karten.
- [ ] Integration einer "Smart-Choice"-Logik bei Begriffsklärungen.
- [ ] Erweiterung des Output-Schemas um strukturierte Sektions-Metadaten.

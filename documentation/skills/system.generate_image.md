# Skill Dossier: system.generate_image
**Status:** 🔍 Audit
**Domain:** system

## 💎 Diamond-Check (Ebenen 0-8)
- [ ] Ebene 1: Funktionale Vision & Idempotenz - ⚠️ Keine deterministische Reproduzierbarkeit
- [x] Ebene 2: Pydantic Schemas (In/Out) - ✅ Vorhanden
- [ ] Ebene 3: Logik & Resilience (ToolExecutor) - ⚠️ Keine Retry-Logik bei Provider-Ausfall
- [ ] Ebene 5: Grounding (Keine Halluzinationen) - ⚠️ Prompt-Injection möglich
- [x] Ebene 6: Renderer (Link/Image Autorität) - ✅ Base64/Image-Renderer vorhanden

## 📝 Analyse (AI Studio Flash)

**Identifizierte Schwachstellen:**
- **Fehlende Prompt-Veredelung:** User-Prompts werden ohne Qualitäts-Optimierung (Expansion) an Provider gesendet.
- **Renderer-Bruch:** Skill generiert Markdown-Code selbst, statt Rohdaten an einen zentralen Renderer zu liefern.
- **Hartkodierte Logik:** Provider-spezifische Modell-IDs sind im Tool-Code verankert (Wartbarkeit).
- **Keine Metadaten:** Wichtige Infos (Seed, echte Auflösung) werden nicht im Output-Contract zurückgegeben.

## 🚀 To-Do für Montag (Pro-Mode)
- [ ] Implementierung eines Prompt-Expansion-Layers für Diamond-Bildqualität.
- [ ] Refactoring: Entfernung des Markdown-Renderings aus dem Tool-Code.
- [ ] Verschiebung der Modell-Logik in den Gateway/Config-Layer.
- [ ] Erweiterung des Output-Schemas um technische Metadaten.

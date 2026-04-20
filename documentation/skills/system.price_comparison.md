# Skill Dossier: system.price_comparison
**Status:** 🔍 Audit
**Domain:** system

## 💎 Diamond-Check (Ebenen 0-8)
- [ ] Ebene 1: Funktionale Vision & Idempotenz - ⚠️ Total Cost Vision verletzt
- [x] Ebene 2: Pydantic Schemas (In/Out) - ✅ Vorhanden
- [ ] Ebene 3: Logik & Resilience (ToolExecutor) - ⚠️ Regex-Parsing instabil
- [ ] Ebene 5: Grounding (Keine Halluzinationen) - ⚠️ Währungsvalidierung fehlt
- [ ] Ebene 6: Renderer (Link/Image Autorität) - ❌ Keine Deep-Links

## 📝 Analyse (AI Studio Flash)

**Identifizierte Schwachstellen:**
- **In-Text Parsing (Regex):** Extrahiert Preise ohne strikte Währungsvalidierung (Gefahr der Umrechnungshalluzination).
- **Versandkosten-Ignoranz:** `includes_shipping` ist hart auf False gesetzt, was die "Total Cost" Vision verletzt.
- **URL-Vakuum:** Skill liefert keine direkt klickbaren Shop-Links.
- **Dubletten-Gefahr:** Caching-Logik unterscheidet nicht zwischen leicht variierenden Produktnamen.

## 🚀 To-Do für Montag (Pro-Mode)
- [ ] Umstellung von Regex-Parsing auf strukturiertes Source-Mapping.
- [ ] Implementierung der Versandkosten-Extraktion.
- [ ] Integration des Deep-Link Renderers für Idealo/Geizhals/Amazon.
- [ ] Härtung des Currency-Guards (Strict Match).

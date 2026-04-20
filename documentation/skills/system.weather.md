# Skill Dossier: system.weather
**Status:** 🔍 Audit
**Domain:** system

## 💎 Diamond-Check (Ebenen 0-8)
- [ ] Ebene 1: Funktionale Vision & Idempotenz - ⚠️ Keine Standort-Persistenz
- [x] Ebene 2: Pydantic Schemas (In/Out) - ✅ Vorhanden
- [ ] Ebene 3: Logik & Resilience (ToolExecutor) - ⚠️ Hartkodierte OpenWeatherMap-Logik
- [ ] Ebene 5: Grounding (Keine Halluzinationen) - ⚠️ Interpolation bei fehlenden Stunden
- [ ] Ebene 6: Renderer (Link/Image Autorität) - ⚠️ Keine visuelle Wetterkarte

## 📝 Analyse (AI Studio Flash)

**Identifizierte Schwachstellen:**
- **Standort-Amnesie:** "Wetter morgen" funktioniert nicht, da der letzte Standort nicht im Memory persistiert wird.
- **Provider-Monokultur:** Vollständig auf OpenWeatherMap hartkodiert (keine Fallback-Option bei Rate-Limits).
- **Halluzinations-Brücke:** Temperatur-Interpolation bei fehlenden Stunden-Daten generiert unrealistische Zwischenwerte.
- **Fehlende Visualisierung:** Keine Einbindung von Wetterkarten oder Radar-Daten im Output.

## 🚀 To-Do für Montag (Pro-Mode)
- [ ] Standort-Persistenz: Speicherung des letzten bekannten Ortes im Core Memory.
- [ ] Provider-Abstraktion: Schaffung einer `WeatherProvider`-Interface-Layer.
- [ ] Interpolations-Entfernung: Wechsel zu "next available hour" statt Halluzination.
- [ ] Renderer-Erweiterung: Einbindung von statischen Wetterkarten-URLs.

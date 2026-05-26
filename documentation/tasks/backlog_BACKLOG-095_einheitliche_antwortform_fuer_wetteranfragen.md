# BACKLOG-095 Task Spec - Einheitliche Antwortform fuer Wetteranfragen

## Source Backlog Item
- `BACKLOG-095 - Einheitliche Antwortform fuer Wetteranfragen`

## Problem / Goal
Wetterantworten von OpenAI/HPZ und Gemini liefern fachlich dieselben Daten, wirken aber unterschiedlich formatiert. Ziel ist eine einheitliche, kurze und gut lesbare Wetterausgabe mit klarer Quellenzeile.

## Scope
- Ein einheitliches Ausgabeformat fuer Wetterantworten definieren und im Wetterpfad anwenden.
- Provider-spezifische Stilunterschiede reduzieren, ohne die fachlichen Inhalte zu verlieren.
- Die Quellenattribution beibehalten.

## Acceptance Criteria
- Wetterantworten von OpenAI/HPZ und Gemini nutzen dieselbe strukturierte Grundform.
- Die Antwort enthaelt Ort, Zeitraum, Wetterlage, Hoechst-/Tiefsttemperatur, Niederschlagswahrscheinlichkeit, Wind und Quelle.
- Die Ausgabe bleibt deutschsprachig, kompakt und gut lesbar.
- Wetterrouting und Fallback-Verhalten bleiben unveraendert funktionsfaehig.

## Verification Plan
- Beispielanfrage fuer Wetter in einer Stadt ueber beide Provider pruefen.
- Antworttext auf gemeinsame Struktur, Quellenzeile und fehlende Stilbrueche vergleichen.
- Sicherstellen, dass die fachlichen Werte weiter korrekt aus der Wetterquelle kommen.

## Out Of Scope
- Neue Wetterdatenquellen.
- Neue Forecast-Funktionalitaet.
- Allgemeine Chat-Umformulierung ausserhalb des Wetterpfads.

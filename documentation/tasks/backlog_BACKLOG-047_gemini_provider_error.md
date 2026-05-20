# BACKLOG-047: Gemini-Provider Fehler bei Calendar Mutation Intent

## Aufgabe
Debug und Fix des Gemini-Provider-Fehlers bei Calendar Mutation Intent.

## Problem
Gemini-Provider (gemini-3-flash-preview) liefert Fehlermeldung "Es ist ein Fehler aufgetreten: Provider: gemini | Modell: gemini-3-flash-preview. Bitte sende die Anfrage direkt noch einmal" statt Kalender-Antwort bei Calendar Mutation Intent.

## Erwartetes Verhalten
Calendar-Intent wird korrekt verarbeitet und Antwort enthält Kalender-Keywords wie "Kalender", "Termin", "verschiebe".

## Tatsächliches Verhalten
Provider-Fehlermeldung statt Kalender-Response. Keine Tool-Ausführung erkennbar.

## Reproduktion
TEST-RUN-2026-05-15-011, TC-002-GEMINI, Prompt "Verschiebe meinen Termin morgen um 30 Minuten".

## Betroffener Bereich
Backend LLM Gateway / Gemini Provider Integration / API-Error-Handling

## Nachweise
documentation/test-results/TEST-RUN-2026-05-15-011/TC-002-GEMINI_evidence.json

## Akzeptanzkriterien
- [ ] Gemini-Provider-Error ist behoben
- [ ] Calendar-Intent wird bei Gemini korrekt verarbeitet
- [ ] Antwort enthält Kalender-Keywords
- [ ] Tool-Ausführung ist erkennbar
- [ ] TC-002-GEMINI im Retest PASS

## Technische Hinweise
Debug in llm_gateway.py oder Gemini-Provider-Config erforderlich. Prüfe API-Error-Handling, Provider-Integration und Request-Forwarding.

## Wichtigkeit
HIGH

## Umsetzungsrisiko
MEDIUM

## Aufwand
M

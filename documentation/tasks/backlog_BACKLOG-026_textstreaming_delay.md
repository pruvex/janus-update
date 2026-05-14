# Task: BACKLOG-026 – Textstreaming-Geschwindigkeit im Chat: GPT vs Gemini

## Backlog Item

- **ID:** BACKLOG-026
- **Typ:** IMPROVEMENT
- **Status:** READY
- **Quelle:** User Intake

## Kurzbeschreibung

GPT-5.4-nano und gemini-3-flash streamen Text im Chat mit sehr unterschiedlicher Geschwindigkeit. GPT streamt so schnell, dass es kaum sichtbar ist (fast wie Block-Antwort). Gemini ist deutlich langsamer, aber immer noch etwas zu schnell. Ziel: Beide etwas langsamer als Gemini aktuell, dann uniform für beide Provider.

## Erwartetes Verhalten

Beide Provider streamen mit gleichmäßiger, etwas langsamerer Geschwindigkeit als Gemini aktuell (nicht so schnell wie GPT aktuell, sondern etwas langsamer als Gemini). Streaming sollte sichtbar und angenehm sein, nicht "block-artig" bei GPT.

## Tatsächliches Verhalten

GPT-5.4-nano streamt so schnell, dass der Text fast in einem Block erscheint (kaum sichtbares Streaming). Gemini-3-flash ist deutlich langsamer als GPT, aber immer noch etwas zu schnell für angenehmes Lesen.

## Reproduktion / Kontext

Chat-Streaming mit gpt-5.4-nano vs gemini-3-flash bei beliebigen Prompts

## Betroffener Bereich

Frontend / Chat Rendering / Streaming / UX

## Nachweise

User-Beobachtung im Live-Chat

## Akzeptanzkriterien

- [ ] GPT-5.4-nano streamt etwas langsamer als aktuell (nicht mehr block-artig)
- [ ] Gemini-3-flash streamt etwas langsamer als aktuell (angenehmes Lesetempo)
- [ ] Beide Provider streamen mit ähnlicher Geschwindigkeit (uniforme UX)
- [ ] Streaming ist sichtbar und angenehm für den User

## Fehlende Informationen

Keine

## Notizen

Es geht nicht um Antwortzeit (response time), sondern um Textstreaming im Chat (wie der Text Zeichen für Zeichen erscheint). Betroffener Bereich ist Frontend/Chat Rendering, nicht Backend-Performance. Lösung könnte ein konfigurierbarer Streaming-Delay oder Token-Rate-Limiter im Frontend sein.

## Routing

- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Kleiner UX-Improvement mit klarem Scope (Frontend Streaming-Delay), LOW-Risk, atomare Änderung
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-05-12
- **Recommended next skill:** SKILL 3

## Bewertung

- **Wichtigkeit:** MEDIUM
- **Umsetzungsrisiko:** LOW
- **Aufwand:** S
- **Umsetzungsreife:** READY
- **Empfehlung:** SCHEDULE

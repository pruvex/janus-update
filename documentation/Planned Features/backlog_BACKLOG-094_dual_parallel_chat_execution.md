# BACKLOG-094 Spec - Zwei Chats parallel mit eigener Modellwahl ausfuehren

## Source Backlog Item

- `BACKLOG-094 - Zwei Chats parallel mit eigener Modellwahl ausfuehren`

## Problem / Goal

Janus soll zwei Chatfenster wirklich parallel bedienen koennen. Ein laufender Request in Chat A darf Chat B nicht blockieren, und umgekehrt.

## Scope

- Pro-Chat isolierte Request-Lifecycle-Verwaltung
- Pro-Chat isolierte Modell- und Provider-Auswahl
- Pro-Chat isoliertes Streaming, Cancel/Stop und Fehlermeldungen
- UI- und State-Handling fuer zwei gleichzeitig aktive Chats

## Acceptance Criteria

- Chat A und Chat B koennen gleichzeitig laufende Requests haben
- Jeder Chat verwendet seine eigene Modell-/Provider-Auswahl
- Streaming und Abbruch verhalten sich pro Chat unabhaengig
- Ein Request in einem Chat veraendert weder Zustand noch Anzeige des anderen Chats

## Verification Plan

- Zwei Chats oeffnen, in beiden unterschiedliche Modelle waehlen
- In Chat A einen laenger laufenden Request starten
- Waehrenddessen in Chat B ebenfalls eine Anfrage senden
- Pruefen, dass beide Antworten gleichzeitig und unabhaengig laufen

## Out Of Scope

- Neue Modelle oder Provider
- Generelle Router- oder Intent-Logik
- Ueber die Parallelitaet hinausgehende UI-Neugestaltung

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 74
- **Risk:** HIGH
- **Recommended Review Model:** 5.5
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-05-25
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

- **Review Notes:** Der Scope ist ausreichend klar und fuers Task-Design bereit. Die spaetere Task-Zerlegung sollte die konkrete Isolation von Request-Lifecycle, Streaming und Cancel-Pfaden noch weiter präzisieren, damit die parallele Ausfuehrung sauber testbar bleibt.

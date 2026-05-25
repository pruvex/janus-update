# BACKLOG-094 Ultra-Low-Cost Smoke (Parallel Chats)

**Ziel:** Parallelitaet + Fenster-Isolation pruefen mit minimalem Tokenverbrauch.  
**Stand:** 2026-05-25  
**Scope:** Nur Smoke, kein Full-Regression-Lauf.

## Kostenprofil (Guardrails)

- Maximal **2 Requests total** (je Chatfenster genau 1).
- Pro Request nur **1 kurzer Satz** (max. ~8-12 Woerter).
- Bevorzugte Modelle: **GPT smallest viable** + **Gemini smallest viable**.
- Keine Follow-up-Fragen im selben Lauf.
- Test sofort stoppen, wenn beide Antworten sichtbar sind.

## Prompt-Vorlagen (sparsam)

- **Fenster A (GPT):** `Antworte mit genau zwei Woertern: "A bereit".`
- **Fenster B (Gemini):** `Antworte mit genau zwei Woertern: "B bereit".`

Hinweis: Diese Prompts erzeugen extrem kurze Completion-Outputs und reichen fuer Parallelitaetsnachweis.

## Testablauf (manuell, 60-90 Sekunden)

1. Janus starten, zwei Chatfenster oeffnen (A/B).
2. In A GPT-Smallest-Viable waehlen, in B Gemini-Smallest-Viable.
3. Prompt A senden.
4. Innerhalb von 1-2 Sekunden Prompt B senden (nicht auf A warten).
5. PASS-Kriterium UI:
   - Beide Chats zeigen eigene laufende Aktivitaet.
   - Beide Chats liefern jeweils kurze Antwort.
   - Kein Fenster blockiert das andere.

## Log-Nachweis (Primary Evidence)

Datei: `C:\KI\Janus-Projekt\documentation\logs\janus_backend.log`

Erwartet:
- `STREAM_AUDIT` Start/Ende fuer **beide** Fenster.
- `TOKEN_AUDIT` Eintraege fuer beide Requests.
- Unterschiedliche `window_id` und jeweils korrekte `provider/model`.
- Zeitliche Ueberlappung der Stream-Events (parallel statt seriell).

## PASS/FAIL Entscheidung

- **PASS:** UI-Kriterien erfuellt + Log zeigt zwei ueberlappende Streams mit sauberer Fenstertrennung.
- **FAIL:** Ein Fenster wartet auf das andere, oder Log zeigt serielle statt parallele Ausfuehrung.

## Optional Mini-Retest (nur bei Unsicherheit)

Nur wenn Nachweis unklar:
- Genau ein zweiter Durchlauf mit denselben 2 Prompts.
- Kein Playwright Full-Suite, keine langen Freitextprompts.

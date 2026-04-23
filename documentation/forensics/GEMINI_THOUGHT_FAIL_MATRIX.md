# GEMINI THOUGHT FAIL MATRIX

**Zweck:** Forensische Dokumentation von Gemini 3 thought_signature Fehlern.
**Status:** 🔴 BLOCKED — Warten auf Opus-Eskalation
**Datum:** 2026-04-24

## Fehlermatrix

| Test-ID | Skill-Kategorie | Prompt | Ergebnis | Fehlermeldung (Log) | Anmerkung (Reasoning-Level) |
|---------|----------------|--------|----------|---------------------|-----------------------------|
| 1 | knowledge.query | "Was steht in aegypten.pdf?" | ✅ OK | - | function_call Part mit thought_signature erfolgreich |
| 2 | knowledge.query | "Was steht in aegypten.pdf?" (zweiter Turn) | ✅ OK | - | function_response Part不需要 thought_signature |
| 3 | RAG (knowledge.query) | RAG-Query mit Tool-Call | ❌ FAIL | `InvalidArgument: 400 Function call is missing a thought_signature` | 🔴 KRITISCHER FEHLERPFAD — RAG-Task ohne thought_signature |
| 4 | filesystem.find_files | "Suche nach Dateien" | ✅ OK | - | function_call Part mit thought_signature erfolgreich |
| 5 | knowledge.read_full_text | "Lese Datei X" | ✅ OK | - | function_call Part mit thought_signature erfolgreich |

## Test-Plan

### Test-Szenarien

1. **Tool-Call mit function_call Part**
   - Skill-Kategorie: knowledge.query
   - Prompt: "Was steht in aegypten.pdf?"
   - Erwartetes Ergebnis: Success mit thought_signature
   - Aktuelles Ergebnis: Fail (400 Error)
   - Fehlermeldung: `InvalidArgument: 400 Function call is missing a thought_signature`

2. **Tool-Call mit function_response Part**
   - Skill-Kategorie: knowledge.query
   - Prompt: "Was steht in aegypten.pdf?" (zweiter Turn nach Tool-Ausführung)
   - Erwartetes Ergebnis: Success
   - Aktuelles Ergebnis: TBD
   - Anmerkung: function_response Parts benötigen KEINE thought_signature

3. **Multi-Tool-Call (Parallel)**
   - Skill-Kategorie: filesystem + knowledge
   - Prompt: "Suche nach Dateien und lese deren Inhalt"
   - Erwartetes Ergebnis: Success mit thought_signature für ersten function_call
   - Aktuelles Ergebnis: TBD
   - Anmerkung: Bei parallelen Calls nur der erste Part braucht thought_signature

## Dokumentation

- **Gemini API Docs:** https://ai.google.dev/gemini-api/docs/thought-signatures
- **Bug-Eintrag:** BUG-GEMINI-API-001 in PROJECT_STATE.md
- **LESSON:** #Gemini #API #ThoughtSignature in WHAT_I_LEARNED.md

## Fix-Empfehlung

Die `thought_signature` muss aus der ursprünglichen Gemini-Antwort extrahiert werden, wenn Tool-Calls verarbeitet werden. Parts sollten nicht neu erstellt, sondern direkt aus der API-Antwort übernommen werden.

**Code-Stelle:** `backend/llm_providers/gemini/service.py:540-545`

```python
# Aktuell (fehlerhaft):
parts_for_raw_assistant.append(
    protos.Part(function_call=protos.FunctionCall(
        name=tc["function"]["name"], 
        args=json.loads(tc["function"]["arguments"])
    ))
)

# Empfohlen (mit thought_signature):
# Original Parts aus API-Antwort übernehmen und wiederverwenden
```

## Status

- **Erstellung:** 2026-04-24
- **Letztes Update:** 2026-04-24
- **Verantwortlich:** SWE-1.6 (Kimi)
- **Eskalation:** Opus (empfohlen)

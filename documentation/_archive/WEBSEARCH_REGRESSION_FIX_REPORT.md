# Websearch Provider Regression Fix – Abschlussbericht

**Datum:** 2026-03-18  
**Status:** ✅ ABGESCHLOSSEN – Alle drei Provider live getestet und bestanden

---

## Zusammenfassung

Alle drei Websearch-Provider (Gemini, OpenAI, DuckDuckGo/Ollama) sind jetzt vollständig funktionsfähig mit nativer Websuche, sauberem Kosten-Tracking und korrekter Quellenanzeige.

---

## Gefundene Regressionen & Fixes

### 1. OpenAI-Provider – Quellen-Extraktion (KRITISCH)

**Problem:** Die Quellen-/URL-Extraktion war fehlerhaft. Der Code suchte `response.web_search_call`, aber die OpenAI Responses API liefert `response.output` als Liste von Items (`web_search_call`, `message`).

**Fix in** `backend/services/websearch/openai_provider.py`:
- Iteration über `response.output` Items
- `web_search_call`-Items: Extraktion von `action.sources` (URL + Titel)
- `message`-Items: Extraktion von `annotations` (`url_citation` Objekte)
- Deduplizierung der URLs aus beiden Quellen
- Text-Aufbau aus Snippets wenn kein message-Text vorhanden

**Ergebnis:** 6 URLs, 7 Annotations, 13 Inline-Markdown-Links im Live-Test.

### 2. DuckDuckGo-Provider – Captcha-Block (KRITISCH)

**Problem:** DuckDuckGo blockiert direkte HTTP-Requests (sowohl Instant Answer API als auch HTML-Scraping) mit Captcha-Challenges. Ollama-Nutzer bekamen keine Suchergebnisse.

**Fix in** `backend/services/websearch/duckduckgo_provider.py`:
- Neue primäre Suchmethode `_search_via_library()` über die `duckduckgo-search` Python-Library
- Die Library nutzt Browser-Fingerprinting (primp) und umgeht Captcha-Blocks
- Bestehender Instant Answer API + HTML-Scraping-Pfad als Fallback erhalten
- Saubere Fehlerbehandlung: Library-Fehler → Fallback → Empty Result

**Ergebnis:** 8 URLs, 8 Inline-Markdown-Links, 2056 Zeichen Text im Live-Test.

### 3. Gemini-Provider – Keine Regression

Der Gemini-Provider war bereits korrekt implementiert (REST API mit `google_search` Tool, Grounding-Metadata-Extraktion, Inline-Zitationen).

### 4. Renderer – Keine Regression

Der WebsearchRenderer gibt Cloud-Text direkt weiter, wenn vorhanden. Nur bei fehlendem Text wird die Executive Summary mit URLs angezeigt.

---

## Live-Test-Ergebnisse (18.03.2026)

| Provider | Text | URLs | Inline-Links | Kosten | Status |
|---|---|---|---|---|---|
| **Gemini** (REST API) | 2052 chars | 5 | 7 | 0.00€ (kostenlos) | ✅ PASS |
| **OpenAI** (Responses API) | 3993 chars | 6 | 13 | 0.009€ | ✅ PASS |
| **DuckDuckGo** (Library) | 2056 chars | 8 | 8 | 0.00€ (kostenlos) | ✅ PASS |

---

## Test-Status

- **Websearch Unit-Tests:** 10/10 bestanden
- **Skill Router/Executor Tests:** 36/36 bestanden
- **Backend-Gesamtsuite:** 556 bestanden, 23 vorbestehende Failures (geo_service, audit, consent – nicht websearch-bezogen)

---

## Geänderte Dateien

| Datei | Änderung |
|---|---|
| `backend/services/websearch/openai_provider.py` | Quellen-Extraktion aus `response.output` Items |
| `backend/services/websearch/duckduckgo_provider.py` | `duckduckgo-search` Library als primäre Suchmethode |
| `backend/tests/tools/test_websearch.py` | Tests für Library-Mock angepasst |

---

## Architektur-Bestätigung

- **Gemini:** REST API → `google_search` Tool → `groundingMetadata` → Inline-Zitationen ✅
- **OpenAI:** Responses API → `web_search` Tool → `response.output` Items → Annotations ✅
- **Ollama:** `duckduckgo-search` Library → Ergebnisse mit URLs und Snippets ✅
- **Kein Fallback** zwischen Providern ✅
- **Kosten-Tracking** über `calculate_cost` für Gemini und OpenAI ✅
- **Renderer** gibt Cloud-Text direkt weiter ✅

# Janus ChatGPT OAuth Provider — Feature-Spec & Umsetzungsplan

**Version:** 1.0.0  
**Datum:** 2026-07-07  
**Zielgruppe:** Codex / Cursor / Janus Diamond Pipeline  
**Status:** READY FOR IMPLEMENTATION (nach Epic 4 Transport Phase B)  
**Epic-ID:** `EPIC-AUTH-CHATGPT-001`  

**Abgrenzung:** Auth/Provider-Epic — nutzt `CodexResponsesTransport` aus Epic 4.  
**Nicht starten vor:** Transport Phase B **oder** explizitem Operator-Go mit dokumentierter technischer Schuld.

---

## 0. Executive Summary

### Problem

Viele potenzielle Janus-Nutzer haben bereits **ChatGPT Plus/Pro**, wollen aber:

- keinen separaten **OpenAI API-Key** besorgen,
- keine **zusätzlichen API-Kosten** neben dem Abo,
- nicht auf `platform.openai.com` Billing einrichten.

### Lösung

Neuer Provider **`openai-codex`** mit **Device-OAuth** (wie Hermes / Codex CLI):

- User meldet sich mit ChatGPT-Konto an
- Janus nutzt **Subscription-Kontingent** statt Pay-per-Token API
- **Bestehender Orchestrator + Tool-Loop bleiben unverändert** — nur Auth/Endpoint wechseln

### Kernentscheidung

```text
✅ codex_responses-Pfad: Janus führt weiterhin eigene Tools aus
❌ codex_app_server-Pfad: NICHT — würde Janus-Tools durch Codex-CLI ersetzen
```

### Aufwand / Risiko

| | Schätzung |
|---|-----------|
| Aufwand MVP | **1,5–2,5 Wochen** |
| Risiko | **Mittel** (OAuth-Lifecycle, OpenAI-Backend-Änderungen) |
| Nutzen | **Sehr hoch** (Onboarding, Conversion) |

---

## 1. Produktziel

### 1.1 User Story

> Als ChatGPT-Plus-Nutzer möchte ich Janus mit meinem bestehenden Abo verbinden, ohne API-Key und ohne Extra-Kosten für GPT-Anfragen.

### 1.2 Settings-UX (Ziel)

```text
Einstellungen → OpenAI

Authentifizierung:
  ○ API-Key (Pay-per-Use, alle OpenAI-Modelle)
  ○ ChatGPT Plus/Pro (OAuth — nutzt dein Abo-Kontingent)

[ Mit ChatGPT anmelden ]   ← Device-OAuth Flow

Hinweis: Verbraucht dein ChatGPT-Codex-Wochenkontingent.
         Gemini und Embeddings benötigen weiterhin separate Keys.
```

### 1.3 Was es löst / was nicht

| User-Frage | Antwort |
|------------|---------|
| „Plus reicht für Janus GPT?“ | **Ja** (dieser Provider) |
| „Kein API-Key mehr nötig?“ | **Für OpenAI-Chat ja** — Embeddings/Gemini evtl. nein |
| „Unbegrenzt?“ | **Nein** — Wochenquota wie Codex CLI |
| „Janus-Tools funktionieren?“ | **Ja** — gleicher Function-Calling-Loop |

---

## 2. Architektur

### 2.1 Ist-Zustand

```text
Settings → Keyring (provider: "openai")
    → OpenAIServiceProvider(api_key=...)
    → Chat Completions / Responses API
    → Tool-Calls → tool_executor → Janus Skills
```

**Relevante Dateien heute:**

| Datei | Rolle |
|-------|-------|
| `backend/api/routers/system.py` | API-Key CRUD via Keyring |
| `backend/llm_providers/openai/service.py` | OpenAI Calls + Tools |
| `frontend/js/settings.js` | API-Key UI |
| `backend/services/chat_orchestrator.py` | `wf.api_key` Weitergabe |

### 2.2 Soll-Zustand

```text
Settings → Auth-Modus wählen
    │
    ├─ api_key  → bestehender Pfad (unverändert)
    │
    └─ oauth    → openai-codex Provider
            → TokenStore (Keyring: openai-codex-oauth)
            → TokenRefresh vor jedem Call / bei 401
            → gleicher Tool-Loop wie heute
```

### 2.3 Komponenten (neu)

```
backend/services/auth/openai_codex_oauth.py      # Device flow, refresh, import
backend/services/auth/token_store.py           # Keyring abstraction
backend/llm_providers/openai_codex/service.py  # Provider mit OAuth-Bearer
backend/llm_providers/openai_codex/gateway.py  # Optional: thin wrapper
backend/api/routers/auth_openai.py             # OAuth start/callback/status
frontend/js/openai-oauth-settings.js           # Login-Button, Status
backend/tests/test_openai_codex_oauth.py
backend/tests/test_openai_codex_provider.py
```

### 2.4 Was NICHT geändert wird

- `tool_executor`, Skill-JSONs, `CapabilityRegistry`
- `IntentEngine`, Memory, Workflows
- Gemini / Ollama / Anthropic Provider
- Orchestrator Tool-Loop Logik

---

## 3. OAuth-Flow (Device Code)

Analog Hermes: `hermes auth add openai-codex --type oauth`

### 3.1 Ablauf

```text
1. User klickt „Mit ChatGPT anmelden“
2. Backend startet Device-Flow → device_code + verification_url
3. UI zeigt: Link + Code (oder öffnet Browser)
4. User loggt sich bei OpenAI ein (ChatGPT-Plus-Konto)
5. Backend pollt Token-Endpoint bis success
6. Tokens in Keyring speichern (refresh_token + access_token)
7. UI: „Verbunden als …“ + Ablauf/Quota-Hinweis
```

### 3.2 Token-Speicherung

| Key | Keyring-Service | Inhalt |
|-----|-----------------|--------|
| `openai-codex-oauth` | `Janus-Projekt` | JSON: access_token, refresh_token, expires_at, account_hint |

**Sicherheit:**

- Nie Tokens in Logs
- Nie in `localStorage` (nur serverseitig Keyring)
- Refresh bei `invalid_grant` → User muss neu anmelden (klare UI-Meldung)

### 3.3 Optional: Codex CLI Import

Wenn `~/.codex/auth.json` existiert (Windows: `%USERPROFILE%\.codex\auth.json`):

- Settings-Button: „Aus Codex CLI importieren“
- Read-only Import, kein Shared-State (eigene Kopie in Janus Keyring)
- Vermeidet doppeltes Login für Power-User

---

## 4. Provider-Implementierung

### 4.1 Neuer Provider-Slug

```python
# config / model catalog
"openai-codex"  # Subscription path
"openai"          # API key path (bestehend)
```

### 4.2 OpenAICodexServiceProvider

Erweitert oder parallel zu `OpenAIServiceProvider`:

```python
class OpenAICodexServiceProvider(BaseLLMProvider):
    """
    ChatGPT-Subscription-Pfad.
    Gleiche Tool-Parameter wie OpenAI API — anderer Auth-Header, ggf. andere base_url.
    """

    async def chat_completion(..., tools, tool_choice, ...):
        token = await token_store.get_valid_access_token("openai-codex")
        # Bearer aus OAuth, NICHT api_key
        # Rest: identisch zu openai/service.py Tool-Normalisierung
```

**Wichtig:** Bestehende Hilfen wiederverwenden:

- `_normalize_tool_names` / OpenAI Shim aus `openai/service.py`
- `iter_openai_chat_completion_stream_events` wo kompatibel

### 4.3 Modell-Mapping

| Janus UI-Name | openai-codex Modell | Anmerkung |
|---------------|---------------------|-----------|
| GPT-5.x / Codex-Modelle | `openai-codex/gpt-5.x` | Subscription-Katalog |
| Legacy API-only Modelle | — | Nur mit API-Key |

Model Catalog erweitern: Provider-Spalte `auth_mode: api_key | oauth | both`

### 4.4 Fehlerbehandlung

| Fehler | User-Meldung | Aktion |
|--------|--------------|--------|
| 401 / invalid_grant | „ChatGPT-Anmeldung abgelaufen — bitte erneut verbinden“ | Re-Auth |
| 429 / quota exceeded | „Wochenlimit erreicht — API-Key nutzen oder bis Reset warten“ | Fallback-Hinweis |
| 403 | „Abo hat keinen Codex-Zugang“ | Link zu Plus-Info |

---

## 5. Integration in Orchestrator

### 5.1 Auth-Auflösung

```python
def resolve_openai_credentials(user_id, provider_mode) -> OpenAICredentials:
    if provider_mode == "oauth":
        return OpenAICredentials(type="oauth", token=...)
    return OpenAICredentials(type="api_key", key=keyring.get("openai"))
```

`wf.api_key` wird zu `wf.auth_credentials` (refactor minimal, abwärtskompatibel).

### 5.2 Nebenaufrufe (Memory, Intent)

| Call | Empfehlung v1 |
|------|----------------|
| Chat Tool-Loop | **openai-codex** wenn OAuth aktiv |
| Memory-Extraktion (Nano) | Gleicher Token wenn `openai` Provider gewählt |
| Intent Classifier (Nano) | Gleicher Token |
| **Embeddings** | **Weiter API-Key** (`openai` separat) — Subscription deckt oft nicht ab |

**UI-Hinweis:** „Für volle Memory-Suche optional OpenAI API-Key für Embeddings hinterlegen.“

---

## 6. Feature-Flags

```python
OPENAI_CODEX_OAUTH_ENABLED = os.getenv("OPENAI_CODEX_OAUTH_ENABLED", "false").lower() == "true"
OPENAI_CODEX_IMPORT_CLI_AUTH = os.getenv("OPENAI_CODEX_IMPORT_CLI_AUTH", "true").lower() == "true"
```

---

## 7. Phasen

### Phase 1 — OAuth Core (4–5 Tage)

- [ ] `openai_codex_oauth.py` — Device flow + refresh
- [ ] `token_store.py` — Keyring
- [ ] API: `POST /api/auth/openai-codex/start`, `GET /api/auth/openai-codex/status`
- [ ] Tests: Token refresh, invalid_grant

### Phase 2 — Provider (3–4 Tage)

- [ ] `OpenAICodexServiceProvider` — Chat + Tools + Stream
- [ ] Orchestrator credential resolution
- [ ] Model catalog Einträge `openai-codex`
- [ ] Tests: Tool-Call roundtrip (mock)

### Phase 3 — UI (2–3 Tage)

- [ ] Settings: Auth-Modus Toggle
- [ ] „Mit ChatGPT anmelden“ + Status
- [ ] Fehlermeldungen (Quota, expired)
- [ ] Optional: Codex CLI import

### Phase 4 — Hardening (2–3 Tage)

- [ ] Live-Test mit Plus-Konto
- [ ] Quota-Error UX
- [ ] Dokumentation / Help-Text
- [ ] `janus-final-audit` Slice

**Gesamt:** ~1,5–2,5 Wochen

---

## 8. Akzeptanzkriterien (MVP)

- [ ] User kann ohne API-Key Janus mit ChatGPT Plus verbinden
- [ ] Chat mit Tool-Calls (z.B. `calendar.list_events`, `memory_read`) funktioniert
- [ ] Bestehender API-Key-Pfad unverändert nutzbar
- [ ] Bei OAuth-Ablauf: klare Re-Auth-Aufforderung, kein Silent-Fail
- [ ] Tokens nie in Logs/Frontend
- [ ] Flag `OPENAI_CODEX_OAUTH_ENABLED=false` → Feature unsichtbar

### Live-Tests

| # | Szenario |
|---|----------|
| L1 | OAuth Login → einfache Chat-Antwort |
| L2 | OAuth → Kalender-Tool-Call |
| L3 | OAuth → Memory write/read |
| L4 | Quota-Limit simulieren → verständliche Meldung |
| L5 | API-Key-Modus parallel → kein Regression |
| L6 | Token abgelaufen → Re-Auth Flow |

---

## 9. Risiken

| Risiko | Schwere | Mitigation |
|--------|---------|------------|
| OpenAI ändert Codex-Auth/API | Hoch | Feature-Flag, schneller Rollback auf API-Key |
| Subscription ohne Embeddings | Mittel | Separater Embedding-Key in UI erklären |
| Wochenlimit Frust | Mittel | Quota-Hinweis + API-Key-Fallback |
| ToS-Grauzone | Mittel | Nur offiziellen Device-Flow (wie Codex CLI) |
| Doppelte Token-Pflege | Niedrig | Kein Shared-State mit Codex CLI |

---

## 10. Abhängigkeiten & Reihenfolge

```text
ROADMAP M0–M4 (Intent + Learn + Memory C)  →  PASS
        ↓
EPIC-AUTH-CHATGPT-001 (dieses Dokument)
```

**Begründung für „später“:**

- Onboarding-Feature profitiert von stabilem Intent (weniger frustige Erstnutzung)
- OAuth-Quota wird durch Memory-Extraktion/Classifier mitverbraucht — sinnvoller wenn diese Pfade stabil sind
- Kein Blocker für Intent/Memory-Entwicklung

**Optional parallel** nach M2 (Intent MVP): Phase 1–2 schon starten, wenn Operator will — aber **nicht vor M0**.

---

## 11. Codex-Startprompt (wenn dran)

```text
Implementiere EPIC-AUTH-CHATGPT-001 Phase 1 + 2 aus:
documentation/Cursor specs/CHATGPT_OAUTH_PROVIDER_SPEC.md

Scope:
- backend/services/auth/openai_codex_oauth.py
- backend/services/auth/token_store.py
- backend/llm_providers/openai_codex/service.py
- backend/api/routers/auth_openai.py
- Orchestrator credential resolution (minimal)
- Tests

Constraints:
- OPENAI_CODEX_OAUTH_ENABLED=false default
- KEIN codex_app_server — Janus Tool-Loop bleibt
- Bestehender openai API-Key Pfad unverändert
- Tokens nur Keyring, nie Logs
- Intent/Memory/Workflow Dateien NICHT anfassen

Validation:
python -m pytest backend/tests/test_openai_codex_oauth.py backend/tests/test_openai_codex_provider.py -v
```

---

## 12. Referenzen

- Hermes Providers: https://hermes-agent.nousresearch.com/docs/integrations/providers
- Hermes Codex Runtime: https://hermes-agent.nousresearch.com/docs/user-guide/features/codex-app-server-runtime
- Janus Keyring heute: `backend/api/routers/system.py` (`add_api_key`)
- Roadmap (Vorgänger): [ROADMAP_EPIC_ORDER.md](./ROADMAP_EPIC_ORDER.md)

---

**END OF SPEC**

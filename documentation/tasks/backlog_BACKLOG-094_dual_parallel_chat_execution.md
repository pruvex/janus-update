# BACKLOG-094 Task Spec - Zwei Chats parallel mit eigener Modellwahl ausfuehren

## Source Spec

- `C:\KI\Janus-Projekt\documentation\Planned Features\backlog_BACKLOG-094_dual_parallel_chat_execution.md`

## Backlog Item

- `BACKLOG-094 - Zwei Chats parallel mit eigener Modellwahl ausfuehren`

## Feature

- Zwei Janus-Chats muessen gleichzeitig Requests senden, streamen, abbrechen und beantworten koennen, ohne sich gegenseitig zu blockieren.

## Generated At

- 2026-05-25

## Generated Tasks

### TASK-094.1 Parallel Chat Execution und State Isolation
- Ziel: Die beiden Chatfenster so entkoppeln, dass jeder Chat seinen eigenen Request-Lifecycle, Stream-Zustand, Cancel-Pfad und Modell-/Provider-Status behaelt.
- Scope: Frontend-Dispatch, Chat-/Window-State, Backend-Request-Handling, Streaming-Rueckkanal, chatlokales Cancel/Stop und UI-Statusanzeige.
- Files:
  - `C:\KI\Janus-Projekt\frontend\js\app.js`
  - `C:\KI\Janus-Projekt\frontend\js\chat.js`
  - `C:\KI\Janus-Projekt\frontend\js\chat-manager.js`
  - `C:\KI\Janus-Projekt\frontend\js\window-state.js`
  - `C:\KI\Janus-Projekt\backend\services\chat_orchestrator.py`
  - `C:\KI\Janus-Projekt\backend\services\orchestrator\chat_request_workflow_state.py`
  - `C:\KI\Janus-Projekt\backend\services\orchestrator\execution_dispatcher.py`
  - `C:\KI\Janus-Projekt\backend\services\orchestrator\status_sync.py`
  - `C:\KI\Janus-Projekt\backend\services\orchestrator\stream_protocol.py`
  - `C:\KI\Janus-Projekt\tests\functional\chat-core.spec.js`
- Steps:
  - Isoliere die Laufzeitdaten pro `chat_id`, damit laufende Requests und Streaming-Events nicht in globale Chat-Zustaende einfliessen.
  - Stelle sicher, dass Cancel/Stop und Statuswechsel immer den richtigen Chat referenzieren.
  - Verhindere, dass ein laufender Request in Chat A den Start oder das Streaming in Chat B blockiert.
  - Passe die Frontend-Event- und Render-Pfade an, damit jede Chat-Instanz ihren eigenen Zustand rendern und aktualisieren kann.
  - Erweitere den vorhandenen funktionalen Chat-Test so, dass zwei unterschiedliche Chats parallel mit verschiedenen Modellen getestet werden.
- Acceptance Criteria:
  - Chat A und Chat B koennen gleichzeitig Requests ausfuehren.
  - Ein Request in Chat A blockiert Chat B nicht und umgekehrt.
  - Modell-/Provider-Auswahl bleibt pro Chat getrennt und konsistent.
  - Streaming, Abort/Cancel und Fehlerzustand sind pro Chat isoliert.
  - Ein Wechsel zwischen beiden Chats waehrend paralleler Antworten verliert weder Inhalt noch Zustand.
- Tests:
  - `node --check C:\KI\Janus-Projekt\frontend\js\app.js`
  - `node --check C:\KI\Janus-Projekt\frontend\js\chat.js`
  - `node --check C:\KI\Janus-Projekt\frontend\js\chat-manager.js`
  - `node --check C:\KI\Janus-Projekt\frontend\js\window-state.js`
  - `python -m py_compile C:\KI\Janus-Projekt\backend\services\chat_orchestrator.py C:\KI\Janus-Projekt\backend\services\orchestrator\chat_request_workflow_state.py C:\KI\Janus-Projekt\backend\services\orchestrator\execution_dispatcher.py C:\KI\Janus-Projekt\backend\services\orchestrator\status_sync.py C:\KI\Janus-Projekt\backend\services\orchestrator\stream_protocol.py`
  - `npx playwright test tests/functional/chat-core.spec.js`
- Model: 5.3 codex
- Reason: Multi-file implementation plus regression test coverage across frontend and backend request orchestration.

# Task 026: Direkte Chat-Zuweisung via Sidebar (A/B Actions)

## Status

**DONE** (2026-04-12)

## Ziel

Chat-Einträge in der Sidebar mit **expliziten A/B-Buttons** in das jeweilige Fenster laden — unabhängig vom „aktiven“ Fenster, mit kurzem **visuellen Feedback** am Ziel-Chatfenster.

## Umsetzung

### HTML / JS (`frontend/js/chat-manager.js`)

- In **`renderChatList`:** Pro Zeile eine Gruppe **`.chat-item-actions`** mit:
  - **`btn-assign-a`** — Zuweisung Fenster A (Lila-Semantik über CSS).
  - **`btn-assign-b`** — Fenster B öffnen + Zuweisung (Cyan-Semantik).
- **Events** (`e.stopPropagation()`):
  - **A:** `loadChat(chatId, { windowId: "A", context: "assistant" })` → `setActiveWindow("A")` → **`flashWindowAssignFeedback("A")`**.
  - **B:** `setWindowOpen("B", true)` → `loadChat(..., { windowId: "B", context: "assistant" })` → `setActiveWindow("B")` → **`flashWindowAssignFeedback("B")`**.
- Hilfsfunktion **`flashWindowAssignFeedback(windowId)`:** setzt temporär **`janus-assign-feedback--a`** bzw. **`--b`** auf `#chat-window-A|B` (Klasse nach ~750 ms entfernt).

### CSS (`frontend/css/style.css`)

- **`.chat-item-actions`:** standardmäßig **`opacity: 0`**, **`visibility: hidden`**, **`pointer-events: none`** (bewusst kein `display: none`, damit **`:focus-within`** / Tastatur nutzbar bleibt).
- Sichtbar bei **`.chat-item:hover`** und **`.chat-item:focus-within`**.
- **`.btn-assign-a` / `.btn-assign-b`:** kompakt (Buchstaben A/B), pane-farbig getönt, **`opacity ~0.45`** bis direkter **`:hover`** auf dem Button (**`opacity: 1`**, leichtes **`scale(1.04)`**).
- **Puls-Animation:** `@keyframes janus-assign-pulse-a|b` verstärkt kurz den **bestehenden** `box-shadow` des **fokussierten** Fensters (nur mit **`.window-active`**, nach Zuweisung gesetzt).

### Eingeklappte Sidebar

- **`.app-container.sidebar-collapsed #chat-list .chat-item-actions`:** ausgeblendet (`display: none` + opacity/visibility).

## Betroffene Dateien

- `frontend/js/chat-manager.js`
- `frontend/css/style.css`

## Kurztest

- [x] Hover auf Chatzeile → A/B sichtbar; Klick A/B lädt Chat im richtigen Fenster; Zielfenster wird fokussiert; kurzer Puls.
- [x] Klick bubbelt nicht zum Titel (kein Doppel-Laden über aktives Fenster).

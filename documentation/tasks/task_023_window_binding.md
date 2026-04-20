# Task 023: Window Binding (Feature 2)

## 1. Ziel & Kontext

**Ziel:** Deterministische Chat-Zuweisung: Ein Klick auf einen Chat in der Sidebar lädt die Konversation in **dem Fenster**, das visuell aktiv ist (`.window-active` / `activeWindowId`), nicht immer in Fenster A.

**Referenzen:** Task 022 (`window-state.js`, `paneId`), `documentation/Planned Features/1Dual Chat Window System.md`

**Status:** **DONE** (verifiziert 2026-04-12)

**Hinweis:** Die Chat-Liste und `loadChat`-Aufrufe liegen in **`frontend/js/chat-manager.js`** (nicht in `sidebar.js` — dort nur statische Nav-Buttons).

---

## 2. Implementation Log

| Datum | Eintrag |
|-------|---------|
| 2026-04-12 | **Post-Impl / Close:** Sidebar-Klicks sind **deterministisch** an **`getActiveWindowId()`** gebunden: `loadChat(chatId, { windowId: getActiveWindowId() })`. Der gewählte Chat erscheint immer im **aktuell aktiven** Fenster (`.window-active`), nicht fest in A. Parallel: `setChatForWindow`, `getActiveChatIdForWindow`, `sendMessage(windowId)` + `getChatIdForPane`-Semantik; Sidebar-Highlight, wenn der Chat in A **oder** B geladen ist. |

---

## 3. Umsetzung (Kurz)

| Bereich | Änderung |
|---------|----------|
| `window-state.js` | `getActiveWindowId()`, `getActiveChatIdForWindow(windowId)` |
| `chat-manager.js` | Sidebar-Klick: `loadChat(chatId, { windowId: getActiveWindowId() })`; `loadChat` rendert Header/Messages für `paneId(..., windowId)`; `setChatForWindow`; Sidebar-Highlight wenn Chat in A **oder** B offen; `getCurrentChatId()` = Chat des aktiven Fensters |
| `chat.js` | Composer/Messages pro Fenster: `sendMessage(windowId)`, `appendMessage(..., { windowId })`, Listener auf A+B; `getChatId` für Senden über `getActiveChatIdForWindow(windowId)` |
| `app.js` | Optional: `user-input`-Listener für beide Panes (autoResize) |

---

## 4. Ergebnis

**Klick links → Chat erscheint im leuchtenden (aktiven) Fenster.** Senden nutzt die `chat_id` des gleichen Fensters.

---

## 5. Test-Vorgaben

- [x] Zwei Fenster: Fenster B aktiv machen → Sidebar-Chat klicken → Inhalt nur in B.
- [x] Fenster A aktiv → gleicher Ablauf → Inhalt in A.
- [x] Nachricht senden: `chat_id` im Request entspricht dem im **jeweiligen** Fenster geladenen Chat (`getActiveChatIdForWindow(windowId)`).

---

## 6. Betroffene Dateien

- `frontend/js/window-state.js`
- `frontend/js/chat-manager.js`
- `frontend/js/chat.js`
- `frontend/js/app.js` (Composer-Resize beide Panes)

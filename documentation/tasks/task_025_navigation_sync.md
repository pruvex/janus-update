# Task 025: Navigation Sync — Active Chat Bar, Clean List & Fenster-B-Sichtbarkeit

## 1. Ziel & Kontext

**Ziel:** Die Sidebar bleibt mit dem **Dual-Window-Workspace** synchron: global sichtbar, welche Chats in A/B aktiv sind; in der Liste **minimal** markiert, welche Chats gerade **in einem Fenster** liegen und welcher Eintrag zum **fokussierten** Fenster gehört — ohne visuelle Überladung (**Clean List Policy**).

**Referenzen (Dossiers):**

| Teil | Dossier |
|------|---------|
| **Active Chat Bar** (Feature 4) | `documentation/Planned Features/4Active Chat Bar.md` |
| **State Indicators** (Feature 5) | `documentation/Planned Features/5Chatlist State Indicators.md` |

**Status:** **DONE** (verifiziert 2026-04-12)

---

## 2. Post-Impl — Active Chat Bar (Lila / Cyan)

**Position:** `#active-chat-bar` oberhalb von **Neuer Chat**, oberhalb der scrollbaren Chatliste (`index.html`).

**Inhalt:**

- Zwei Chips **A** und **B** (`--color-pane-a` ≈ Lila `#9b59b6`, `--color-pane-b` ≈ Cyan `#00f2ff`), konsistent mit Header-Streifen und Fenster-Glow.
- Anzeige der **aktuellen Chat-Titel** pro Fenster (gekürzt/Ellipsis), Live-Update über **`syncActiveChatBar()`** bei `subscribeWindowState`, `loadChat`, `patchChatTitleInUI`.
- **Klick Chip A|B:** `setActiveWindow("A"|"B")`; bei geschlossenem B siehe §4.

**Kein zweiter State:** Die Bar liest nur `getWindowState()` / Titel aus Liste oder Pane-Header.

---

## 3. Post-Impl — Clean List Policy (Listen-Indikatoren)

**Status-only (kein „Bonbon-Look“):**

- **Keine** permanenten A/B-Badge-Buttons für alle Zeilen.
- **Marker:** schmale **vertikale Linie** links (`::before` / `::after`), nur wenn der Chat **tatsächlich** in Fenster A bzw. B geladen ist — **Fenster B zu** → kein B-Marker (`inB` nur wenn `windows.B.isOpen`).
- **Aktiver Fokus:** Zeile des Chats im **aktuell fokussierten** Fenster (`chat-item--active-focus` + `body[data-janus-active-window]`) mit dezentem Highlight und kleinem Punkt vor dem Titel.

**Hover-Actions (Zuweisung):**

- **`chat-item-assign`:** Buttons **A** / **B** nur bei **`:hover`** / **`:focus-within`** (`opacity` + `pointer-events`), laden per `loadChat(id, { windowId })` — reduziert permanente visuelle Last.

**Routing unverändert:** Klick auf den **Titel** lädt in das **aktive** Fenster (Task 023).

---

## 4. Post-Impl — Fenster-B-Sichtbarkeit (Toggle, Content persistent)

**State:** `window-state.js` — `windows.B.isOpen`; **kein** Entfernen des DOM von `#chat-window-B`.

**Sidebar — Chip B:**

- Wenn **`isOpen === false`:** Titeltext **„+ Zweites Fenster“**, Klasse `active-chat-chip--b-closed`.
- **Klick:** `setWindowOpen("B", true)` und `setActiveWindow("B")`.

**Header Fenster B:**

- **`#chat-window-close-btn-B`** (**×**) rechts in der Headerzeile (Reset ⟲ | Titel-Streifen | ×), **`closeSecondWindow()`** → `setWindowOpen("B", false)` + Fokus A.

**CSS / Host:**

- `#chat-window-host-B.chat-window-host--b-closed` → **`display: none`** (nur verstecken; Kinder bleiben im DOM).
- **`applyWindowBHostVisibility()`** in `chat-manager.js` bei jedem Window-State-Update.

**Laden in geschlossenes B:** `loadChat(..., { restoreClosedPane: true })` verhindert automatisches Öffnen von B beim Wiederherstellen aus Persistenz; Inhalt kann trotzdem geladen werden.

---

## 5. Warm Start Persistence (Ergänzung Epic)

Logischer Workspace (`chatA`, `chatB`, `activeWindowId`, `isOpenB`) wird in **`localStorage`** unter `janus_window_workspace_v1` bei jedem `emit()` gesichert; **Position/Größe** der Fenster **nicht** — nach Start **`resetChatWindowLayout("A"|"B")`** in `app.js` für Standard-Andockung.

---

## 6. Abnahme-Checkliste

- [x] Active Chat Bar zeigt Titel/„+ Zweites Fenster“ und aktualisiert live.
- [x] Liste: Marker nur für offene Zuordnung; Hover A/B; Fokus-Zeile konsistent.
- [x] Fenster B per Chip und × steuerbar; Host hidden ohne DOM-Zerstörung.
- [x] Persistenz: Chats + B-Sichtbarkeit; Layout-Reset beim Start.

---

## 7. Betroffene Dateien

- `frontend/js/window-state.js` (Persistenz, `setWindowOpen`, `closeSecondWindow`)
- `frontend/js/chat-manager.js` (`syncSidebarWindowContextUi`, `syncActiveChatBar`, `applyWindowBHostVisibility`, `applyChatListWindowIndicators`, Listen-Rendering, `loadChat`/`restoreClosedPane`)
- `frontend/js/app.js` (`resetChatWindowLayout` nach `loadChats`)
- `frontend/index.html` (Active Bar, Header B mit ×)
- `frontend/css/style.css` (Chips, Liste, Host-B-hidden, Header, Pane-Farben)

---

## 8. Implementation Log

| Datum | Eintrag |
|-------|---------|
| 2026-04-12 | **DONE / Post-Impl:** Active Bar (Lila/Cyan, Chip B Einladetext wenn zu); Clean List (Linien-Marker, Hover A/B, `data-janus-active-window`); Fenster B `isOpen` + Host-`display:none` + × rechts im Header; Persistenz `janus_window_workspace_v1` + Layout-Reset beim Start. |

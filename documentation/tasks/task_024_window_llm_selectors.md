# Task 024: Window-Specific LLM Selectors

**Status:** **DONE** (verifiziert 2026-04-12)

## 1. Ziel

LLM-**Provider** und **Modell** pro Chat-Fenster (A/B) steuerbar; Sidebar bleibt **globaler Standard** (Fallback), wenn das Fenster auf „Sidebar“ (`null`) steht.

## 2. Post-Impl (Design & Routing)

### Zwei-Zeilen-Header

- **Zeile 1:** ⟲-Reset, **Drag-Streifen** mit Titel (`chat-header-title-label`) — unveränderte Bedienlogik.
- **Zeile 2:** CSS **Grid** `grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr)` für kompakte `<select>`-Elemente (`chat-header-provider-A|B`, `chat-header-model-A|B`), damit Controls bei ~600px Fensterbreite nicht mit dem Titel um horizontalen Platz konkurrieren.

### `effectiveProviderModelForWindow(windowId)` (`frontend/js/chat.js`)

- Liest `getWindowState().windows[windowId].provider` / `.modelId`.
- **Override:** Wenn gesetzt (nicht `null`/leer), werden diese Werte für API-Requests (`sendMessage`, Bild-Upload, PDF-Stream, TTS-Provider-Hint) verwendet.
- **Fallback:** Wenn `null`, gelten die Werte aus **`#provider-select`** und **`#model-select`** (Sidebar / globaler Standard).
- Kein zweiter Katalog: Modelllisten für die Header kommen über **`fillModelOptionsIntoSelect`** in `app.js` aus demselben `model_catalog` und derselben Filterlogik wie die Sidebar.

### Sync

- **`syncChatWindowHeaderLlm()`** nach `render()` und bei **`subscribeWindowState`**: Header spiegeln die Sidebar, solange kein Fenster-Override aktiv ist; erste Provider-Option **„↳ Wie Sidebar (…)“** setzt `setWindowProvider(_, null)` bzw. entsprechendes Modell-Override zurück.

## 3. Spezifikation (4 Punkte)

### State (`window-state.js`)

- `windows.A` / `windows.B` erweitern um `provider: null` und `modelId: null` (Default = Sidebar übernehmen).
- `setWindowProvider(windowId, val)` — `val` `null` oder `""` normalisiert zu „kein Override“.
- `setWindowModel(windowId, val)` — analog.

### UI (`index.html` + `style.css`)

- Zwei-Zeilen-Header: Zeile 1 ⟲ + Drag/Titel; Zeile 2 Grid **0.9fr / 1.1fr** für Provider- und Modell-`<select>`.
- IDs: `chat-header-provider-A|B`, `chat-header-model-A|B`.

### Request-Routing (`chat.js`)

- `sendMessage(windowId)` (und gleiche LLM-Nutzung z. B. bei Bild/PDF):  
  `effectiveProvider = windowOverride ?? #provider-select`  
  `effectiveModel = windowModelOverride ?? #model-select`

### Sync (ohne Zirkel)

- Nach `render()` / Katalog-Update: Header spiegeln Sidebar, wenn Override `null`.
- Erste Provider-Option: dynamisches Label „↳ Wie Sidebar (…)“ mit `value=""` → `setWindowProvider(_, null)`.
- Sidebar-`change` → bestehende `render()`-Kette unverändert; danach `syncChatWindowHeaderLlm()` aufrufen.
- `subscribeWindowState`: Header-Anzeige aktualisieren (Fokuswechsel).

## 4. Nicht brechen

- `loadModelCatalog`, `loadUserSelections`, `render()`, `findFirstAvailableModel`, Sidebar-`change`-Handler bleiben die Quelle der Wahrheit für den Katalog; Modelloptionen für Header werden über **dieselbe Filter-/Sortierlogik** wie die Sidebar befüllt (extrahierte Hilfsfunktion in `app.js`).

## 5. Betroffene Dateien

- `frontend/js/window-state.js`
- `frontend/index.html`
- `frontend/css/style.css`
- `frontend/js/app.js`
- `frontend/js/chat.js`

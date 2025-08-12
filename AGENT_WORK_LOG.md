### 2025-08-12 - Chatfenster-Interaktion & Backend-Startfixes

- **Problem:** `interact.js` war nicht definiert, Backend startete nicht automatisch, Chatfenster dockte oben an, nur halber Header als Ziehgriff.
- **Lösung:**
    - `interact.js`-Import in `app.js` korrigiert (`type="module"` in `index.html` hinzugefügt).
    - `package.json` aktualisiert, um Backend (`uvicorn`) automatisch mit `npm run start-dev` zu starten.
    - `styles.css` angepasst (`position: absolute`, `top/left` entfernt, `display: flex` aus Parent entfernt) und `interact.js` so konfiguriert, dass es `top/left` direkt manipuliert.
    - `restrictRect`-Modifikator in `interact.js` entfernt, da er das Andocken verursachte.
    - `chat-header` in `styles.css` feste Höhe und `cursor: grab` gegeben, um den gesamten Bereich als Ziehgriff zu aktivieren.
- **Ergebnis:** Chatfenster ist nun frei beweglich und der gesamte Header dient als Ziehgriff.
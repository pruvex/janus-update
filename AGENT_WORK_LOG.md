

### 2025-08-12 - Mindestgröße Chatfenster

- **Problem:** Chatfenster konnte auf zu kleine Größe skaliert werden, was zu UI-Bruch führte.
- **Lösung:** Mindestgröße für das Chat-Fenster mittels interact.js-Modifier `restrictSize` implementiert (min: width 300px, height 200px).
- **Ergebnis:** Chatfenster kann nicht mehr kleiner als die definierte Mindestgröße gezogen werden.
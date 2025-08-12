

### 2025-08-12 - Dynamische Bewegungsgrenzen Chatfenster (Feinjustierung)

- **Problem:** Chatfenster konnte nicht bis an die Sidebar geschoben werden und hatte keine rechte Begrenzung.
- **Lösung:**
    - Die Klemm-Logik in `dragMoveListener` in `app.js` angepasst.
    - `x`- und `y`-Positionen werden nun relativ zu den Dimensionen des Elternelements (`#chat-view`) geklemmt.
    - `chatView.getBoundingClientRect()` wird verwendet, um die korrekten Dimensionen des Elternelements zu erhalten.
- **Ergebnis:** Chatfenster sollte nun korrekt innerhalb der Grenzen des `#chat-view`-Containers beweglich sein, was die Sidebar-Überlappung und das Herausschieben aus dem Bild verhindert.
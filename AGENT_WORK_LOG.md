### Implementierung des "Sprechblasen"-Layouts abgeschlossen
- Datum: 2025-08-09
- Änderungen:
    - CSS (frontend/css/styles.css): `.chat-message`, `.user-message`, `.bot-message` Klassen hinzugefügt. `#chat-messages` auf Flexbox umgestellt.
    - JavaScript (frontend/js/chat.js): `appendMessage` Funktion angepasst, um die neuen CSS-Klassen basierend auf dem Absender zuzuweisen.
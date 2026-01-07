Testblock 1: Kernfunktionalität des Chats (chat-core.spec.js)
Das ist der wichtigste Test. Wir können ihn den "Happy Path" End-to-End-Test nennen. Er simuliert die grundlegende und wichtigste Aktion, die ein Benutzer ausführt, und stellt sicher, dass die gesamte Kette vom Frontend zum Backend und zurück funktioniert.
Was dieser Test genau prüft (Schritt für Schritt):
Start der App: Öffnet die Startseite und prüft, ob die Anwendung überhaupt lädt.
Neuer Chat: Klickt auf den "Neuer Chat"-Button, um sicherzustellen, dass der Chat-Zustand sauber zurückgesetzt wird.
Texteingabe: Findet das Eingabefeld, tippt die Nachricht "Hallo Janus" ein und prüft, ob der "Senden"-Button aktiv wird.
Nachricht Senden: Sendet die Nachricht durch Drücken der Enter-Taste.
Frontend-Reaktion prüfen:
Stellt sicher, dass das Eingabefeld nach dem Senden leer ist.
Verifiziert, dass die eigene Nachricht ("Hallo Janus") im Chatfenster erscheint.
Backend-Antwort prüfen:
Wartet darauf, dass eine Antwort vom Assistenten in einer neuen Sprechblase (.message.assistant) erscheint.
Stellt sicher, dass diese Antwortblase nicht leer ist.
Zusammenfassend: Wenn dieser Test erfolgreich ist, wissen wir, dass die Kernfunktion deiner Anwendung – eine Konversation zu führen – intakt ist.
Testblock 2: HTML-Struktur-Snapshot (debug-selector.spec.js)
Diesen Test können wir den "Diagnose-Test" oder "Struktur-Snapshot" nennen. Seine einzige Aufgabe ist es, einen "Schnappschuss" des HTML-Codes der Chat-Ansicht zu machen und ihn im Test-Log auszugeben.
Was dieser Test genau prüft:
Er prüft keine Funktionalität. Er macht keine expect-Assertions auf Inhalte oder Verhalten.
Sein einziger Zweck ist es, das HTML zu loggen.
Warum er nützlich ist:
Wenn der chat-core.spec.js Test irgendwann fehlschlägt, weil er ein Element nicht mehr findet (z.B. .message.assistant), können wir im Log dieses "Diagnose-Tests" nachsehen, ob ein Entwickler vielleicht die HTML-Struktur oder die CSS-Klassen geändert hat. Das beschleunigt die Fehlersuche erheblich.
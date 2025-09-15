## Zyklus: Reparatur der Feedback-Schleife

**Stufe 3: Implementierung & Arbeits-Logbuch**

*   **WAS:** `is_confirmation`-Funktion in `backend/main.py` aktualisiert.
*   **WARUM:** Um die Erkennung von Bestätigungen durch den Benutzer robuster zu machen und falsche positive Ergebnisse zu vermeiden.

## Zyklus: Behebung des Datenbank-Schema-Fehlers

**Stufe 3: Implementierung & Arbeits-Logbuch**

*   **WAS:** `init_db()`-Funktion in `backend/database.py` modifiziert, um `sqlite3.OperationalError` (Schema-Mismatch) zu behandeln.
*   **WARUM:** Um sicherzustellen, dass die Anwendung auch bei einer älteren Datenbankversion startet, indem die alte Datenbank gelöscht und eine neue mit dem korrekten Schema erstellt wird. Dies ist eine temporäre Lösung für die Entwicklungsphase.
*   **WAS:** Vollständiger Installer (`Janus Projekt Setup 1.1.0.exe`) neu gebaut, um die Änderungen zu integrieren.
*   **WARUM:** Um die aktualisierte Funktionalität auf Testsystemen bereitzustellen.

## Zyklus: Korrektur des OpenAI Bildgenerierungsmodells

**Stufe 3: Implementierung & Arbeits-Logbuch**

*   **WAS:** `id` des DALL-E 3 (Standard) Bildmodells in `backend/model_catalog.json` von `"dall-e-3-standard"` zu `"dall-e-3"` geändert.
*   **WARUM:** Um den `400 Bad Request` Fehler bei der OpenAI Bildgenerierung auf dem Testsystem zu beheben, da die OpenAI API den Modellnamen `"dall-e-3-standard"` nicht erkennt, aber `"dall-e-3"` unterstützt.
*   **WAS:** Vollständiger Installer (`Janus Projekt Setup 1.1.0.exe`) neu gebaut, um die Änderungen zu integrieren.
*   **WARUM:** Um die aktualisierte Funktionalität auf Testsystemen bereitzustellen.

## Zyklus: Sicherstellung der korrekten Paketierung

**Stufe 3: Implementierung & Arbeits-Logbuch**

*   **WAS:** `janus_backend.spec` auf den ursprünglichen Zustand zurückgesetzt und PyInstaller-Cache aggressiv bereinigt.
*   **WARUM:** Um sicherzustellen, dass die aktualisierte `model_catalog.json` korrekt in den Installer aufgenommen wird, nachdem frühere Versuche fehlgeschlagen sind.
*   **WAS:** Vollständiger Installer (`Janus Projekt Setup 1.1.0.exe`) neu gebaut.
*   **WARUM:** Um die aktualisierte Funktionalität auf Testsystemen bereitzustellen.

## Zyklus: Implementierung der Rechtsklick-Einfügen-Funktion und Behebung von Regressionen

**Stufe 3: Implementierung & Arbeits-Logbuch**

*   **WAS:** Neue Datei `frontend/js/context-menu.js` erstellt, die ein benutzerdefiniertes Rechtsklick-Kontextmenü für `INPUT`- und `TEXTAREA`-Elemente implementiert. Dieses Menü enthält eine "Einfügen"-Option, die den Inhalt der Zwischenablage an der Cursorposition einfügt.
*   **WARUM:** Um die Benutzerfreundlichkeit zu verbessern, indem die "Einfügen"-Funktion per Rechtsklick in Eingabefeldern ermöglicht wird, was zuvor nicht standardmäßig verfügbar war.
*   **WAS:** `frontend/index.html` aktualisiert, um `frontend/js/context-menu.js` als Modul-Skript einzubinden.
*   **WARUM:** Um die neue Kontextmenü-Logik in die Anwendung zu laden.
*   **WAS:** `chatInput` in `frontend/js/chat.js` als `export const` deklariert.
*   **WARUM:** Um den Zugriff auf das `chatInput`-Element von anderen Modulen (insbesondere `chat-manager.js`) zu ermöglichen.
*   **WAS:** `chatInput` in `frontend/js/chat-manager.js` importiert.
*   **WARUM:** Um auf das `chatInput`-Element zugreifen zu können.
*   **WAS:** `chatInput.value = '';` in den Funktionen `createNewChat` und `loadChat` in `frontend/js/chat-manager.js` hinzugefügt.
*   **WARUM:** Um sicherzustellen, dass das Eingabefeld beim Erstellen eines neuen Chats oder beim Laden eines bestehenden Chats geleert wird, wodurch eine Regression behoben wird.
*   **WAS:** Bedingung `if (loadingMessageElement && loadingMessageElement.parentNode === chatMessages)` in `frontend/js/chat.js` an zwei Stellen hinzugefügt, bevor `chatMessages.removeChild(loadingMessageElement)` aufgerufen wird.
*   **WARUM:** Um den Fehler "Failed to execute 'removeChild' on 'Node': The node to be removed is not a child of this node." zu beheben, der auftrat, wenn der Ladeindikator entfernt werden sollte, aber bereits aus dem DOM entfernt war.
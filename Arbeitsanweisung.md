AGENTIC HANDLUNGSPLAN:
Dein Ziel: Implementiere das statische HTML- und CSS-Grundgerüst für das Dashboard, die einklappbare Sidebar und ein Platzhalter-Chatfenster, um die visuelle Grundlage der Anwendung zu schaffen.
Relevante PHASE_X.md: C:\KI\Janus-Projekt\PHASE_2_KERNFUNKTIONALITAET.md
Der Plan:
Stufe 1: Validierung des Ausgangszustands
Führe python health_check.py aus.
Überprüfe die Existenz der relevanten Frontend-Dateien: C:\KI\Janus-Projekt\frontend\index.html und C:\KI\Janus-Projekt\frontend\src\styles.css.
Stufe 3: Implementierung & Arbeits-Logbuch
Implementierung HTML: Ersetze den Inhalt der Datei C:\KI\Janus-Projekt\frontend\index.html mit dem folgenden Code, der die Struktur für Dashboard, Sidebar und Chatfenster definiert:
code
Html
'''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Janus</title>
  <link rel="stylesheet" href="src/styles.css" />
</head>
<body>
  <div id="dashboard">
    <div id="sidebar">
      <h2>Janus</h2>
      <nav>
        <button id="settings-btn">Einstellungen</button>
        <!-- Weitere Nav-Elemente hier -->
      </nav>
    </div>
    <div id="main-content">
      <div id="chat-window">
        <div id="chat-header">Chat</div>
        <div id="chat-messages"></div>
        <div id="chat-input-container">
          <input type="text" id="chat-input" placeholder="Nachricht an Janus senden...">
          <button id="send-btn">Senden</button>
        </div>
      </div>
    </div>
  </div>
  <script src="src/main.js" type="module"></script>
</body>
</html>
'''
Implementierung CSS: Ersetze den Inhalt der Datei C:\KI\Janus-Projekt\frontend\src\styles.css mit grundlegendem CSS für das Layout:
code
Css
'''
:root {
  --background-color: #1e1e1e;
  --sidebar-color: #252526;
  --main-content-color: #1c1c1c;
  --text-color: #cccccc;
  --border-color: #333333;
}

body, html {
  margin: 0;
  padding: 0;
  font-family: sans-serif;
  background-color: var(--background-color);
  color: var(--text-color);
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

#dashboard {
  display: flex;
  height: 100%;
}

#sidebar {
  width: 250px;
  background-color: var(--sidebar-color);
  padding: 1rem;
  border-right: 1px solid var(--border-color);
}

#main-content {
  flex-grow: 1;
  padding: 1rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

#chat-window {
  width: 80%;
  height: 90%;
  background-color: var(--main-content-color);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

#chat-header {
  padding: 0.5rem;
  background-color: var(--sidebar-color);
  border-bottom: 1px solid var(--border-color);
  text-align: center;
}

#chat-messages {
  flex-grow: 1;
  padding: 1rem;
  overflow-y: auto;
}

#chat-input-container {
  display: flex;
  padding: 0.5rem;
  border-top: 1px solid var(--border-color);
}

#chat-input {
  flex-grow: 1;
  background-color: #3c3c3c;
  border: 1px solid var(--border-color);
  color: var(--text-color);
  padding: 0.5rem;
}

#send-btn {
  margin-left: 0.5rem;
}
'''
Stufe 4: Dynamische Verifizierung (Visueller Test durch Supervisor)
Anweisung an den Supervisor: Der agentische Aufbau ist abgeschlossen. Bitte führen Sie den finalen, visuellen Test durch.
Pausiere den Plan: Gib die Meldung aus: Das UI/UX-Grundgerüst wurde implementiert. Bitte starten Sie die Anwendung ('npm run start --prefix ./frontend') und überprüfen Sie das neue Layout visuell. Geben Sie 'test erfolgreich' ein, wenn das Dashboard mit Sidebar und Chatfenster korrekt angezeigt wird.
Stufe 5: Aufräumen & Finale Validierung
Warte auf die Eingabe 'test erfolgreich' vom Supervisor.
Führe python health_check.py erneut aus.
Erfolgs-Kriterien:
Die index.html- und styles.css-Dateien müssen den neuen Inhalt haben.
Der Supervisor muss den visuellen Test als erfolgreich bestätigen.
Der finale Health Check muss erfolgreich sein.
Finale Erfolgsmeldung:
Gib die folgende Meldung aus: Aufgabe erfolgreich abgeschlossen: Das UI/UX-Grundgerüst wurde implementiert und visuell verifiziert.
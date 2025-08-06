Projekt-Manifest: Janus
1. Vision & Leitprinzipien
Vision: Janus ist ein souveräner, lokaler KI-Assistent für den Desktop. Er dient als leistungsstarke und private "Bring Your Own Key" (BYOK) Alternative zu geschlossenen Systemen wie der ChatGPT Desktop App und gibt dem Benutzer die volle Kontrolle über seine Daten, Kosten und KI-Anbieter.
Leitprinzipien:
Souveränität des Benutzers: Der Benutzer hat die alleinige Kontrolle über seine API-Keys, seine Daten und seine Konversationen. Alles wird lokal gespeichert.
Anbieter-Unabhängigkeit: Janus ist agnostisch. Der Benutzer kann jederzeit frei zwischen verschiedenen KI-Anbietern (OpenAI, Google, Anthropic etc.) und deren Modellen wechseln.
Modularität & Erweiterbarkeit: Die Architektur ist von Grund auf so konzipiert, dass neue Fähigkeiten ("Module") und Agenten jederzeit einfach hinzugefügt werden können, ohne das Kernsystem zu gefährden.
Transparenz: Der Benutzer hat jederzeit die volle Kostenkontrolle und Einsicht in die Nutzung seiner API-Keys.
UX als Priorität: Die Benutzeroberfläche ist modern, intuitiv und darauf ausgelegt, komplexe Arbeitsabläufe zu vereinfachen.
2. Kernfunktionalität (Was Janus können wird)
2.1 Agenten-Kern & LLM-Anbindung
Multi-Provider Key Management: Sichere, lokale Speicherung von API-Keys für eine Vielzahl von Anbietern.
Dynamische Modellauswahl: Einfacher Wechsel zwischen Anbietern und spezifischen Modellen (z.B. GPT-4o, Gemini 1.5 Pro) direkt in der Benutzeroberfläche.
Lokale LLM-Integration: Die Fähigkeit, lokale Large Language Models (z.B. über Ollama oder Llama.cpp) zu installieren und zu nutzen. Janus analysiert die Hardware-Leistung des Rechners, fragt den Benutzer nach seinen Zielen (z.B. "kreatives Schreiben", "Codierung") und schlägt basierend darauf passende, lokal installierbare Modelle vor. Auf Wunsch führt Janus die Installation und Einrichtung dieser Modelle durch.
Kosten-Tracking: Ein Dashboard zur Überwachung der API-Nutzung und der damit verbundenen Kosten.
2.2 Das Chat-Erlebnis
ChatGPT-ähnliche Interaktion: Das Verhalten des Chatfensters (Streaming, Formatierung, etc.) orientiert sich am Goldstandard der ChatGPT-App.
Chat-Management: Erstellen, Speichern, Laden und Löschen von einzelnen Konversationen.
Alleinstellungsmerkmal: Chat-übergreifendes Gedächtnis: Janus kann optional auf den Kontext und das Wissen aus allen bisherigen Chats zugreifen, um komplexe, themenübergreifende Projekte zu bearbeiten.
2.3 Agenten-Fähigkeiten
Filesystem-Agent: Vollständiger, sprachgesteuerter Zugriff auf das lokale Dateisystem (lesen, schreiben, erstellen, löschen, umbenennen, verschieben von Dateien und Ordnern), mit einer Sicherheits-Sandbox, die Systemordner schützt.
PDF-Verarbeitung: Fähigkeit, den Inhalt von PDF-Dateien zu lesen, zu analysieren und neue PDF-Dokumente zu erstellen.
Bilderzeugung: Anbindung an Bild-APIs (z.B. DALL-E 3), um Bilder basierend auf Prompts zu generieren.
Tool-Nutzung: Integration der nativen Tool-Fähigkeiten von Modellen (z.B. GPT-4 mit seinen Analyse-Tools).
Sprachein- und -ausgabe: Möglichkeit zur Interaktion mit Janus über gesprochene Sprache.
Coding-Agent: Fähigkeit, Code zu schreiben, zu analysieren und auszuführen, ähnlich der Funktionalität der Gemini CLI.
2.4 Wissensmanagement & Autonomie
Kontext-Gedächtnis: Ein robustes System zur Verwaltung des Kurz- und Langzeitgedächtnisses innerhalb von Konversationen.
Benutzerdefinierte Regeln: Möglichkeit für den Benutzer, dem Agenten permanente Regeln und Anweisungen zu geben.
Selbstlernende Wissensdatenbank: Janus legt automatisch eine interne Wissensdatenbank zu Themen an, die der Benutzer häufig anspricht, und pflegt diese intelligent.
Agenten-Erstellung: Der Benutzer kann durch natürliche Sprache neue, spezialisierte "Mini-Agenten" für wiederkehrende Aufgaben erstellen.
Self-Checks & Self-Heal: Janus verfügt über interne Routinen, um den Zustand seiner Module zu überprüfen und grundlegende Fehler selbstständig zu beheben.
3. Benutzeroberfläche (UI) & Erlebnis (UX)
3.1 Das Dashboard-Konzept
Die Anwendung ist ein zentrales Dashboard, das der Benutzer nach seinen Bedürfnissen anpassen kann.
Alle Elemente auf dem Dashboard (Widgets) sind frei beweglich und in der Größe veränderbar.
3.2 Die Sidebar & Das Einstellungs-Fenster
Am linken Rand befindet sich eine einklappbare Sidebar.
Sie dient als Haupt-Navigationszentrale für:
Einstellungs-Button: Dieser öffnet ein dediziertes Einstellungs-Fenster.
Kostenübersicht
Globale Modellauswahl
Chat-Verwaltung (Öffnen, Neu, Löschen)
**Das Einstellungs-Fenster: Ein modernes Interface mit einer Navigationsleiste auf der linken Seite und den jeweiligen Optionen auf der rechten. Hier kann der Benutzer:
API-Keys hinzufügen, bearbeiten und löschen.
Lokale LLMs installieren und verwalten.
Chats organisieren und durchsuchen.
Dem Modell verschiedene Persönlichkeiten zuweisen (z.B. aus einer Vorlagen-Liste wie "Lehrer", "Coding-Agent", "kreativer Schreibpartner").
Das Gedächtnis des Agenten bearbeiten und verwalten.**
3.3 Das Widget-System
Chat-Fenster: Das primäre Widget. Es können mehrere Chat-Fenster gleichzeitig geöffnet sein.
Dynamische Widgets: Auf Zuruf können neue Widgets für Wetter, Nachrichten etc. erstellt werden.
Datei-Widgets: Per Drag-and-Drop gezogene Dateien (Text, Bild, PDF) öffnen ein dediziertes Widget, das den Inhalt anzeigt und mit einem Chat-Fenster verknüpft ist.
3.4 [RECHERCHE-AUFGABE] UI-Parameter
Vor der Implementierung wird eine Recherche zu modernen UI/UX-Studien durchgeführt, um Parameter für Farbschemata, Schriftarten, Interaktions-Feedback und Layout zu definieren.
4. Nächste Schritte
Abnahme: Sie, der Supervisor, prüfen diesen Entwurf und geben Feedback, bis er zu 100% Ihrer Vision entspricht.
Architektur & Recherche: Sobald das Manifest final ist, werde ich (der Orchestrator) eine tiefgehende technische Analyse durchführen und Ihnen eine detaillierte Blaupause für die Architektur, die Ordnerstruktur und eine exakte, recherchierte Liste der Abhängigkeiten vorlegen.
Roadmap-Erstellung: Basierend auf dieser Blaupause werde ich einen neuen, sauberen und logisch geordneten Phasenplan erstellen.

Roadmap:
PHASE 1: Das Stabile Fundament & "Hello World"
Ziel: Ein leeres, aber startbares Anwendungs-Skelett. Ein Klick auf einen Knopf ruft das Backend auf und zeigt die Antwort an. Das System ist stabil und versioniert.
[INFRASTRUKTUR] "Scorched Earth" & Setup: Das Projektverzeichnis bis auf .git und die .md-Dateien leeren.
[INFRASTRUKTUR] Git-Repository finalisieren: Eine saubere, umfassende .gitignore-Datei erstellen.
[INFRASTRUKTUR] Projektstruktur anlegen: Die leere Goldstandard-Struktur (backend, janus, waechter) erstellen.
[INFRASTRUKTUR] Immunsystem (health_check.py) erstellen: Ein Skript zur Validierung der Struktur und Kern-Abhängigkeiten schmieden.
[INFRASTRUKTUR] Frontend-Setup (Tauri & Vite): Eine saubere package.json (basierend auf der Blaupause) und .nvmrc erstellen, npm install ausführen (um package-lock.json zu erzeugen), tauri init ausführen und vite.config.ts sowie tauri.conf.json sauber konfigurieren.
[INFRASTRUKTUR] Backend-Setup (Python & FastAPI): Die venv erstellen, eine requirements.in erstellen, eine requirements.txt kompilieren und die Abhängigkeiten installieren.
[JANUS] "Hello World"-API-Endpunkt: Im Backend einen /api/health-Endpunkt erstellen.
[WÄCHTER] "Hello World"-Test: Einen Wächter-Test schreiben, der den /api/health-Endpunkt aufruft und verifiziert.
[JANUS] "Hello World"-UI: Im Frontend eine simple index.html mit einem Knopf und einem Ausgabebereich erstellen.
[JANUS] Frontend mit Backend verbinden: Ein Klick auf den Knopf ruft den /api/health-Endpunkt auf und zeigt die Antwort an.
[GIT] Stabilitäts-Commit: Den funktionierenden "Hello World"-Zustand als ersten, goldenen Commit festhalten.

PHASE 2: Der Chat-Kern & Multi-Provider-Fähigkeit
Ziel: Ein funktionierendes Chat-Fenster, das mit verschiedenen, vom Benutzer konfigurierten LLMs kommunizieren kann.
[JANUS] UI/UX-Grundgerüst: Das statische HTML/CSS für das Dashboard, die Sidebar und das (noch nicht funktionale) Einstellungs-Fenster umsetzen.
[JANUS] Key-Management (Backend): Die Logik zur sicheren, verschlüsselten Speicherung von API-Keys (z.B. in einer lokalen config.json) implementieren.
[JANUS] Einstellungs-UI (Frontend): Das UI zum Hinzufügen, Anzeigen (maskiert) und Löschen von API-Keys erstellen.
[JANUS] LLM-Gateway (Backend): Das Kernmodul erstellen, das basierend auf einem Provider-Namen den korrekten API-Key lädt und eine Anfrage an die entsprechende LLM-API sendet.
[JANUS] Chat-API-Endpunkt: Den /api/chat-Endpunkt erstellen, der eine Nachricht und einen Provider entgegennimmt und den LLM-Gateway aufruft.
[WÄCHTER] Chat-Endpunkt testen: Einen Wächter-Test für den Chat-Endpunkt schreiben (ohne echte API-Calls, nur mit Mocks).
[JANUS] Chat-UI-Logik (Frontend): Die Logik implementieren, um Nachrichten aus einem Input-Feld zu senden, den Provider aus einem Dropdown auszuwählen und die gestreamte Antwort im Chatfenster anzuzeigen.
[GIT] Meilenstein-Commit: Den funktionierenden Chat-Kern committen.

PHASE 3: Der Filesystem-Agent & Visuelle Interaktion
Ziel: Der Benutzer kann Dateien per Drag-and-Drop in die App ziehen, deren Inhalt wird in einem Widget angezeigt, und er kann über diese Datei mit dem Agenten chatten.
[JANUS] Drag-and-Drop-Listener (Frontend): Die UI so anpassen, dass sie auf das Ablegen von Dateien reagiert.
[JANUS] Datei-Analyse-Endpunkt (Backend): Den /api/files/analyze-Endpunkt erstellen, der einen Dateipfad empfängt.
[JANUS-AGENT] read_file-Funktion: Die erste Funktion des Filesystem-Agenten implementieren, die den Inhalt einer Textdatei sicher liest.
[WÄCHTER] read_file-Test: Einen Wächter-Test erstellen, der prüft, ob die Funktion den korrekten Inhalt liest und bei nicht existierenden Dateien einen Fehler wirft.
[JANUS] Analyse-Logik (Backend): Den Analyse-Endpunkt mit der read_file-Funktion verbinden und eine einfache Analyse (z.B. Zeilenzahl, Dateityp) zurückgeben.
[JANUS] Datei-Widget (Frontend): Ein neues, dynamisches Widget-Element erstellen, das den Inhalt einer analysierten Datei anzeigen kann.
[JANUS] End-to-End-Verbindung: Den gesamten Flow verbinden: Datei-Drop -> API-Call -> Backend-Analyse -> Anzeige im neuen Datei-Widget.
[JANUS] Kontextuelle Konversation: Die Chat-Logik so anpassen, dass der Inhalt der Datei im Widget automatisch als Kontext für die nächste Chat-Nachricht verwendet wird.
[GIT] Meilenstein-Commit: Das funktionierende Drag-and-Drop-Feature committen.

PHASE 4: Lokale LLMs & Bilderzeugung (MVP)
Ziel: Janus kann unabhängig vom Internet mit lokalen Modellen arbeiten und Bilder generieren. Das Produkt ist nun ein "Minimum Viable Product".
[INFRASTRUKTUR] Ollama-Integration: Eine Wrapper-Klasse im Backend erstellen, die mit der Ollama-API kommunizieren kann, um lokale Modelle aufzulisten und zu verwenden.
[JANUS] Hardware-Analyse: Eine Funktion implementieren, die grundlegende System-Informationen (RAM, GPU) ausliest.
[JANUS] UI für lokale LLMs: Das Einstellungs-Fenster erweitern, um dem Benutzer basierend auf seiner Hardware eine Auswahl an kompatiblen lokalen Modellen vorzuschlagen und einen Installations-Button anzubieten.
[WÄCHTER] Lokale-LLM-Test: Einen Test erstellen, der prüft, ob die Ollama-Integration eine Antwort von einem lokal laufenden Modell erhalten kann.
[JANUS] Bilderzeugungs-Endpunkt (Backend): Einen /api/images/generate-Endpunkt erstellen.
[JANUS-AGENT] generate_image-Funktion: Den Agenten mit der Fähigkeit ausstatten, eine externe Bilderzeugungs-API (z.B. DALL-E 3) anzusprechen.
[JANUS] Bild-Widget (Frontend): Ein Widget-Typ erstellen, der generierte Bilder anzeigen kann.
[GIT] MVP-Commit: Den Zustand als "Minimum Viable Product" committen.

Teilweise abgebildet oder als Grundlage vorbereitet:
Chat-Management & Chat-übergreifendes Gedächtnis: Die Grundlagen werden in Phase 2 geschaffen. Ein ausgefeiltes System ist eine spätere Erweiterung.
PDF-Verarbeitung: Die Architektur in Phase 3 (Datei-Drop -> Analyse -> Widget) ist die perfekte Grundlage, um später einen PDF-Parser anstelle eines Text-Lesers einzubauen.
Einstellungs-Fenster: Die Grundlagen (API-Keys, lokale LLMs) werden in Phase 2 und 4 implementiert. Weitere Optionen (Personas, Gedächtnis bearbeiten) sind spätere Erweiterungen.
Coding-Agent: Die Fähigkeit, mit dem Dateisystem zu interagieren (Phase 3) ist die Grundvoraussetzung für einen Coding-Agenten.
Dynamische Widgets (Wetter, etc.): Die Architektur der Datei-Widgets (Phase 3) schafft die Blaupause für alle zukünftigen Widget-Typen.
Bewusst für später zurückgestellt (aber durch die modulare Architektur ermöglicht):
Sprachein- und -ausgabe: Dies ist ein komplexes Modul, das auf dem funktionierenden Chat-Kern aufbaut.
Selbstlernende Wissensdatenbank & Agenten-Erstellung: Dies sind fortgeschrittene KI-Funktionen, die einen stabilen, datenreichen Kern voraussetzen.
Vollständiger Filesystem-Agent (Schreiben, Löschen, etc.): Diese werden hinzugefügt, sobald ein Feature sie explizit benötigt (z.B. ein "Code-Refactoring"-Feature).
Monetarisierung: Liegt wie besprochen in ferner Zukunft.

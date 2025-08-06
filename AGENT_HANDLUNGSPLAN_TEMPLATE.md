AGENTIC HANDLUNGSPLAN:
Dein Ziel: [Kurze, prägnante Beschreibung des Ziels dieses Handlungsplans.]

Relevante PHASE_X.md: [Pfad zur relevanten PHASE_X.md-Datei, z.B. PHASE_1_FUNDAMENT.md]

Der Plan:
1.  **Stufe 1: Validierung des Ausgangszustands**
    *   Führe `python health_check.py` aus.
    *   [Optional: Zusätzliche proaktive Pfad-Validierungen mit `get_file_info` oder `list_directory` hier einfügen, falls spezifische Pfade vorab geprüft werden müssen.]

2.  **Stufe 2: Planung & Recherche**
    *   [Beschreibe hier die Planungsschritte und notwendige Recherche. Z.B. "Analysiere die Datei X", "Recherchiere die beste Bibliothek für Y mit `google_web_search`".]
    *   [Wenn neue Abhängigkeiten recherchiert werden, dokumentiere die stabile Version im `AGENT_WORK_LOG.md` mit `write_file`.]

3.  **Stufe 3: Implementierung & Arbeits-Logbuch**
    *   [Füge hier die konkreten Implementierungsschritte ein. Nutze Tools wie `write_file`, `replace`, `edit_file`.]
    *   [Dokumentiere jede Aktion und deren Grund im `AGENT_WORK_LOG.md` mit `write_file`.]
    *   [Wenn Pfade dynamisch ermittelt werden (z.B. durch `glob` oder `search_file_content`), dokumentiere die Suchanfrage und die gefundenen Pfade im Logbuch.]

4.  **Stufe 4: Dynamische Verifizierung (Funktionstest)**
    *   [Erstelle hier ein dediziertes Test-Skript (z.B. mit `write_file`).]
    *   [Führe das Test-Skript aus (z.B. mit `run_shell_command`).]
    *   [Beschreibe hier die erwarteten Testergebnisse und wie auf Fehler reagiert werden soll.]

5.  **Stufe 5: Aufräumen & Finale Validierung**
    *   [Lösche temporäre Test-Dateien (z.B. mit `run_shell_command` für `rm`).]
    *   Führe `python health_check.py` erneut aus.

6.  **Stufe 6: Archivierung & Lockfile-Garantie (KRITISCHE STUFE)**
    *   [Überprüfe die Existenz und den Inhalt von `frontend/package-lock.json` und `.gitignore` mit `read_file`.]
    *   Führe `git add .` aus.
    *   [Erstelle einen Commit mit einer aussagekräftigen Nachricht. Beispiel: `run_shell_command` mit `git commit -m "feat: Implementierung der neuen Funktion X"`.]

7.  **Stufe 7: Dokumentation aktualisieren**
    *   [Identifiziere die relevante `PHASE_X.md`-Datei und setze das Häkchen für die erledigte Aufgabe. Nutze `replace` oder `edit_file`.]

8.  **Stufe 8: Vorbereitung für die Zukunft**
    *   [Extrahiere die Beschreibung der nächsten Aufgabe aus der `PHASE_X.md` mit `read_file` und Textverarbeitung.]
    *   [Erstelle einen neuen Git-Branch, der nach dieser nächsten Aufgabe benannt ist. Beispiel: `run_shell_command` mit `git checkout -b "feature/naechste-aufgabe"`.]

Erfolgs-Kriterien:
*   [Liste hier spezifische Kriterien auf, die erfüllt sein müssen, damit der Handlungsplan als erfolgreich gilt.]

Finale Erfolgsmeldung:
[Die finale Erfolgsmeldung, die nur ausgegeben wird, wenn alle Schritte erfolgreich waren.]
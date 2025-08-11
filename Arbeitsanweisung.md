AGENTIC HANDLUNGSPLAN: Tiefenbereinigung & Erstellung des Goldstandard-Meilensteins
Dein Ziel: Das gesamte Projekt von jeglichen Altlasten (veraltete Referenzen, temporäre Dateien, etc.) zu befreien und diesen makellosen Zustand in einem "Goldstandard"-Commit auf dem Haupt-Branch zu verewigen.
Der Plan:
Stufe 1: Branching & Basis-Commit
Ich erstelle einen neuen, isolierten Branch für unsere Aufräumarbeiten: git checkout -b chore/goldstandard-tiefenreinigung.
Auf diesem Branch stage und committe ich zuerst die von Ihnen aktualisierten .md-Dateien, um die neue Planung festzuhalten:
git add .
git commit -m "chore(planning): Projekt-Roadmap neu strukturiert"
Stufe 2: Tiefenanalyse & Bericht (KEINE ÄNDERUNGEN!)
Jetzt führe ich eine umfassende, aber zerstörungsfreie Analyse des gesamten Projektverzeichnisses durch.
a) Keyword-Suche: Ich durchsuche den gesamten Code- und Dokumentationsbestand nach den von Ihnen genannten veralteten Begriffen:
figma server
gpt 3.5
gemini 1.5
b) Suche nach temporären Dateien: Ich werde einen Dry-Run durchführen, um untracked files zu finden, die von der .gitignore erfasst werden sollten. Der Befehl git clean -n -d zeigt an, was gelöscht würde, ohne es tatsächlich zu tun.
c) Analyse auf "tote" Referenzen: Ich werde die package.json und requirements.txt nach Abhängigkeiten durchsuchen, die möglicherweise nicht mehr aktiv im Code importiert oder verwendet werden.
Berichterstattung: Am Ende dieser Stufe präsentiere ich Ihnen einen detaillierten Bericht mit:
Einer Liste aller Fundstellen der Keywords (Datei und Zeilennummer).
Der Ausgabe des git clean -n -d-Befehls.
Einer Liste potenziell ungenutzter Abhängigkeiten.
Ich werde keine einzige Datei ändern oder löschen. Ich warte auf Ihre genauen Anweisungen für jeden einzelnen Fund.
Stufe 3: Kontrollierte Bereinigung (NACH IHRER FREIGABE)
Basierend auf Ihren Anweisungen aus dem Bericht werde ich die Bereinigung durchführen. Beispiele:
Ihre Anweisung: "Entferne die Referenz auf 'gpt 3.5' in Datei X, Zeile Y." -> Meine Aktion: Ich nutze edit_file, um genau das zu tun.
Ihre Anweisung: "Die von git clean gelistete Datei temp_log.txt kann gelöscht werden." -> Meine Aktion: Ich nutze rm temp_log.txt.
Ihre Anweisung: "Lass die Abhängigkeit Z vorerst drin." -> Meine Aktion: Ich rühre sie nicht an.
Stufe 4: Der finale "Goldstandard"-Commit
Nachdem alle von Ihnen genehmigten Änderungen umgesetzt wurden, stage ich diese: git add ..
Ich erstelle den finalen Commit auf unserem Cleanup-Branch mit einer aussagekräftigen Nachricht: chore(project): Goldstandard-Meilenstein nach Tiefenbereinigung.
Stufe 5: Den Haupt-Branch auf den Goldstandard heben
Ich wechsle zum main-Branch: git checkout main.
Ich merge den perfekten Zustand aus unserem Cleanup-Branch hinein: git merge chore/goldstandard-tiefenreinigung.
Ich bitte Sie um Erlaubnis, den nun überflüssigen Cleanup-Branch zu löschen.
Stufe 6: Vorbereitung für die Zukunft
Vom makellosen main-Branch aus erstelle ich den neuen Feature-Branch für unsere erste UI-Aufgabe: git checkout -b feature/interaktives-chatfenster.
Erfolgs-Kriterien:
Das Projekt ist frei von den identifizierten Altlasten.
Keine Änderungen wurden ohne Ihre explizite Freigabe durchgeführt.
Ein klarer "Goldstandard"-Commit existiert auf dem main-Branch.
Wir sind bereit, auf einem sauberen Branch mit der neuen Entwicklung zu starten.
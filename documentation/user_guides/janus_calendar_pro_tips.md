# Janus Calendar Pro Tips

## Time-Blocking in Janus

Time-Blocking ist eine Produktivitätsmethode, bei der du deinen Tag in feste Zeitblöcke unterteilst, die für spezifische Aufgaben reserviert sind. Janus unterstützt dich dabei mit intelligenter KI-Planung.

### Wie es funktioniert

1. **Lücken erkennen**: Die KI analysiert deinen Kalender und findet freie Zeitfenster zwischen deinen bestehenden Terminen.
2. **Fokusblöcke reservieren**: Janus schlägt 2-4 Stunden am Stück für konzentrierte Arbeit ohne Unterbrechungen vor.
3. **Prioritäten abgleichen**: Die KI prüft, ob deine heutigen Termine mit deinen langfristigen Projekten und Zielen übereinstimmen.
4. **Tentative Termine klären**: Janus zeigt Termine an, deren Status noch "tentative" ist oder Klärungsbedarf besteht.

### Deep Work Strategien

- **Morgens blocken**: Reserviere deine produktivsten Stunden (oft 9-12 Uhr) für schwierigste Aufgaben.
- **Meeting-Cluster**: Gruppiere Meetings zu zusammenhängenden Blöcken, um Context-Switching zu minimieren.
- **Pufferzeiten**: Plane 15-30 Minuten zwischen Blöcken für Übergänge und Notfälle.
- **Energie-Management**: Passe Blockgrößen an deine natürlichen Energiezyklen an (z.B. 2h morgens, 1h nachmittags).

## AI-Planung nutzen

### KI-Assistent im Dashboard

Der KI-Assistent im Kalender-Dashboard kann:
- Deinen Tag basierend auf deinen Prioritäten optimieren
- Konflikte erkennen und Lösungsvorschläge machen
- Fokusblöcke automatisch in Lücken einfügen
- Meeting-Cluster vorschlagen, um Fragmentierung zu reduzieren

### Natürliche Sprachbefehle

Frage die KI nach:
- "Optimiere meinen Tag für Deep Work"
- "Gruppiere meine Meetings morgen"
- "Finde einen 3-Stunden-Block für das Projekt X"
- "Zeig mir Konflikte diese Woche"

### Best Practices

- **Bestätige Vorschläge**: Die KI zeigt Änderungen als Diff an. Prüfe sie vor dem Übernehmen.
- **Kontext geben**: Erwähne deine Prioritäten beim Planen (z.B. "Fokus auf Projekt A").
- **Regelmäßig prüfen**: Nutze "Prioritäten prüfen" wöchentlich, um Kurs zu halten.

## Dashboard-Funktionen erklärt

### Prioritäten prüfen
Prüft, ob deine Termine heute mit deinen langfristigen Projekten/Zielen in Janus übereinstimmen.

### Fokusblock schützen
Reserviert 2-4 Stunden am Stück für konzentrierte Arbeit ohne Termine. Die KI erkennt Lücken automatisch.

### Offene Termine bestätigen
Zeigt Termine an, bei denen der Status noch 'tentative' ist oder Klärungsbedarf besteht.

## Installierte App vs. Entwicklungsserver

- **Entwicklung:** Die Oberfläche kommt vom Vite-Server (typisch `http://localhost:5173/`).
- **Installierte / gepackte App:** Die Oberfläche wird aus **`frontend/dist`** geladen (FastAPI mountet dieses Verzeichnis unter `/`; siehe auch Electron-Lade-URL in `main.electron.cjs`).
- Nach Änderungen am HTML/JS/CSS immer **`npm run build`** ausführen, bevor du ein Release oder einen Installer testest — sonst siehst du einen veralteten Stand. Der Build enthält eine kurze Prüfung (`verify-frontend-dist`), dass das Tages-Panel im Bundle steckt.

Details: `documentation/tasks/task_calendar_day_widget_rail_diamond.md`.

## Weiterführende Tipps

- **Wochenplanung**: Nutze die Wochenansicht für strategisches Time-Blocking.
- **Flexibilität**: Plane 80% deiner Zeit, behalte 20% für Unvorhergesehenes frei.
- **Review**: Wöchentliche Reviews helfen, Patterns zu erkennen und zu optimieren.

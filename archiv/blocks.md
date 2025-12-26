# Dokumentation der Refactoring-Blöcke

**Status-Legende:**
- **Erledigt:** Alle Kernaufgaben des Refactorings für diesen Block sind abgeschlossen.
- **Teilweise erledigt:** Die Haupt-Code-Struktur wurde refaktorisiert, aber es fehlen noch Tests, Dokumentation oder Fehlerbehandlung.
- **Offen:** Der Block wurde noch nicht bearbeitet.

---

## Block 1: API Key Management
- **Status:** `Erledigt`

### Zweck
Sicheres und flexibles Management von API-Schlüsseln über Umgebungsvariablen (`.env`), um zu vermeiden, dass sensible Daten im Code stehen.

### Implementierung
Die Kernlogik zur Nutzung von `pydantic-settings` ist implementiert. API-Schlüssel werden aus `.env`-Dateien geladen.

### Offene Punkte

### Definition of Done
- [x] **Settings vorhanden:** Zentrale `Settings` mit `SecretStr` und `.env`-Support.
- [x] **Funktional:** `get_api_key()` nutzt `Settings`.
- [x] **Sicherheit:** `.env` ist in `.gitignore` enthalten.
- [x] **Tests grün & vollständig:** Unit-Tests decken alle Kernpfade ab.
- [x] **Dokumentation aktuell:** Anleitungen sind aktualisiert.

---

## Block 2: Datenbank & Persistenz
- **Status:** `Erledigt`

### Zweck
Kapselung aller Datenbankoperationen (CRUD) und Aufteilung der Verantwortlichkeiten, um die Modularität zu erhöhen.

### Implementierung
Die ehemals monolithische `crud.py` wurde in spezialisierte Manager aufgeteilt:
- `crud.py`: Nur noch für `Chat` und `Message`.
- `image_manager.py`: Für bildbezogene Operationen.
- `memory_manager.py`: Für das Langzeitgedächtnis.

### Offene Punkte

### Definition of Done
- [x] **Trennung:** Zuständigkeiten sind auf `crud.py`, `image_manager.py`, `memory_manager.py` aufgeteilt.
- [x] **Schnittstellen stabil:** Funktionen werden von aufrufenden Schichten korrekt verwendet.
- [x] **Tests grün & vollständig:** Unit-Tests für alle drei Module bestehen und decken die Funktionalität ab.

---

## Block 3: Kostenkontrolle
- **Status:** `Erledigt`

### Zweck
Bereitstellung einer unabhängigen Utility zur Berechnung und Verfolgung von Kosten, die durch die Nutzung von KI-Diensten entstehen.

### Implementierung
- `cost_calculator.py` wurde zu einer reinen Berechnungsfunktion refaktorisiert.
- Die Protokollierung der Kosten wurde in den `llm_gateway.py` verlagert, um die Verantwortlichkeiten klar zu trennen.
- Tests wurden auf `pytest` umgestellt.

### Definition of Done
- [x] **Unabhängigkeit:** `cost_calculator.py` ist eine eigenständige Utility.
- [x] **Zentralisierte Berechnung:** Die Kostenberechnung ist in `calculate_cost` gekapselt.
- [x] **Logging:** Die Kosten werden zentral im `llm_gateway.py` protokolliert.
- [x] **Tests grün:** Unit-Tests für `cost_calculator.py` bestehen.

---

## Block 4: LLM Gateway
- **Status:** `Erledigt`

### Zweck
Abstraktion der Kommunikation mit verschiedenen LLMs (OpenAI, Gemini) und intelligente Delegation von Aufgaben (z.B. Tool-Aufrufe für Bildgenerierung).

### Implementierung
Die Logik in `llm_gateway.py` wurde umfassend refaktorisiert, um Tool-Calls und die spezifische Behandlung von Bildgenerierungs-Anfragen zu unterstützen.
- Die provider-spezifische Logik wurde in das `llm_providers`-Verzeichnis ausgelagert, um die Modularität zu erhöhen.

### Definition of Done
- [x] **Abstraktion:** Einheitliche Schnittstelle `call_llm` für verschiedene Anbieter.
- [x] **Modell-Routing:** Korrekte Auswahl des LLM-Modells.
- [x] **Tool-Delegation:** Erkennung und Delegation von Tool-Aufrufen.
- [x] **Kostenintegration:** Nutzungsdaten werden korrekt an die Kostenkontrolle übergeben.
- [x] **Tests grün:** Unit-Tests für `llm_gateway.py` bestehen.

---

## Block 5: Kontext-Management
- **Status:** `Erledigt`

### Zweck
Verwaltung des Gesprächskontexts, einschließlich Token-Management, Zusammenfassung und Integration von Gedächtnisinhalten.

### Implementierung
Die Logik in `context_manager.py` und die Interaktion mit `memory_extractor.py` wurden angepasst, um flexibler zu sein und auch Kontexte für Bilder zu verarbeiten.

### Definition of Done
- [x] **Kontextverwaltung:** Der Gesprächskontext wird effizient verwaltet.
- [x] **Zusammenfassung:** Ältere Chat-Segmente werden dynamisch zusammengefasst.
- [x] **Gedächtnis-Integration:** Fakten (auch für Bilder) werden im Gedächtnis gespeichert.
- [x] **Tests grün:** Unit-Tests für `context_manager.py` bestehen.

---

## Block 6: Speicher & Wissensmanagement
- **Status:** `Erledigt`

### Zweck
Implementierung des Langzeitgedächtnisses durch Faktenextraktion, Vektorisierung und semantische Suche.

### Implementierung
Die Komponenten `memory_extractor.py`, `vector_service.py` und `chat_summarizer.py` wurden refaktorisiert, um Code-Duplikation zu reduzieren und die Logik zu verbessern.

### Definition of Done
- [x] **Faktenextraktion:** Fakten werden korrekt aus Konversationen extrahiert.
- [x] **Vektorisierung & Suche:** Semantische Suche funktioniert über eine zentrale Hilfsfunktion.
- [x] **Chat-Zusammenfassung:** Funktionalität ist gegeben.
- [x] **Tests grün:** Unit-Tests für die relevanten Module bestehen.

---

## Block 7: Bildgenerierung (Service)
- **Status:** `Erledigt`

### Zweck
Bereitstellung eines einheitlichen Backend-Dienstes für die Bildgenerierung, der sowohl direkte Anfragen als auch delegierte Tool-Aufrufe vom LLM verarbeiten kann.

### Implementierung
Die Logik ist auf mehrere Dateien verteilt, um die Verantwortlichkeiten zu trennen:
- **Endpunkte:** in `backend/main.py`.
- **Service-Logik:** in `backend/image_manager.py`.
- **Daten-Schemas:** in `backend/schemas.py`.
- **Kostenberechnung:** in `backend/cost_calculator.py`.
- **Speicherung:** unter `backend/static/images/`.

### Definition of Done
- [x] **Endpunkte vorhanden:** API-Endpunkte für die Bildgenerierung sind implementiert.
- [x] **Service-Logik gekapselt:** Die Kernlogik befindet sich im `image_manager.py`.
- [x] **Integration:** Kosten, Schemas und Speicherung sind korrekt integriert.

---

## Block 8: Chat-Operationen & Routing (Der "Switch")
- **Status:** `Erledigt`

### Zweck
Implementierung eines robusten, LLM-gesteuerten "Intelligenten Switches", der Benutzeranfragen analysiert und an die korrekten Backend-Dienste (Chat, Tool-Aufruf, etc.) weiterleitet.

### Implementierung
Ein Tool-basiertes Routing-System wurde implementiert.
- **Tool-Definitionen:** in `backend/schemas.py`.
- **Tool-Register:** in `backend/tool_registry.py`.
- **Dispatch-Logik:** in `backend/llm_gateway.py`.
- **API-Endpunkt:** in `backend/main.py`.

### Offene Punkte

### Definition of Done
- [x] **LLM-basiertes Routing:** Intent-Klassifizierung via Tool-Calling ist implementiert.
- [x] **Zentrales Register:** Tools sind zentral in `tool_registry.py` verwaltet.
- [x] **Dynamischer Dispatcher:** Ein Dispatcher für Tool-Aufrufe ist vorhanden.
- [x] **Robuste Fehlerbehandlung:** Umfassende Fehlerbehandlung ist implementiert.
- [x] **Tests grün & vollständig:** Umfassende Integrations-Tests für die Routing-Logik bestehen.

---

## Block 9: Frontend-Interaktion
- **Status:** `Erledigt`

### Zweck
Sicherstellung, dass die Benutzeroberfläche (UI) stabil, konsistent und frei von Bugs ist. Dies umfasst die Interaktion mit dem Backend und die Anzeige von Daten.

### Implementierung
Der bestehende Frontend-Code ist funktional, benötigt aber ein gezieltes Review und Cleanup.
- **Bildgenerierungs-Prompt-Erkennung:** Die Logik zur Erkennung von Bildgenerierungs-Prompts für Gemini wurde im Backend (`backend/main.py`) verfeinert, um flexibler auf verschiedene Formulierungen zu reagieren.

### Offene Punkte
- **Neues Feature (Zurückgestellt):** Die Implementierung eines dedizierten Modals für die Bildgenerierung wurde als neues Feature identifiziert und wird nach Abschluss des Kern-Refactorings behandelt.

### Definition of Done
- [x] **UI-Audit durchgeführt:** Ein manuelles Review der UI-Komponenten ist erfolgt.
- [x] **Code bereinigt:** Identifizierte Probleme im Frontend-Code sind behoben.
- [x] **Stabilität:** Die Interaktion zwischen Frontend und Backend ist verifiziert und stabil.

---

## Block 10: System-Validierung (Health Check)
- **Status:** `Erledigt`

### Zweck
Bereitstellung eines eigenständigen Skripts zur Überprüfung der Systemgesundheit und der Verfügbarkeit kritischer Komponenten.

### Implementierung
Das Skript `health_check.py` ist vorhanden und funktional.

### Definition of Done
- [x] **Skript vorhanden:** `health_check.py` existiert.
- [x] **Funktional:** Das Skript kann ausgeführt werden und prüft die Systemgesundheit.

---

## Block 11: Dateisystem-Operationen
- **Status:** `Erledigt`

### Zweck
Ermöglicht das sichere und kontrollierte Ausführen von Dateisystemoperationen (Erstellen, Löschen, Umbenennen, Verschieben von Dateien und Ordnern) über eine natürliche Sprachschnittstelle, gesteuert durch den LLM-Switch.

### Implementierung
Der Implementierungsplan ist in `PHASE_5_FILESYSTEM_OPERATIONS.md` detailliert beschrieben.

### Definition of Done
- [x] Alle angeforderten Dateisystemoperationen (Erstellen, Löschen, Umbenennen, Verschieben von Dateien/Ordnern) sind in `filesystem_manager.py` implementiert.
- [x] Robuste Pfadvalidierung und Sicherheitsprüfungen (Ausschluss von Systemordnern, Schutz vor Directory Traversal) sind implementiert.
- [x] Pydantic-Modelle für alle Dateisystem-Tools sind in `schemas.py` definiert.
- [x] Alle Dateisystem-Tools sind in `tool_registry.py` registriert.
- [x] Umfassende Unit-Tests für `filesystem_manager.py` sind vorhanden und grün.
- [x] Integrationstests, die die LLM-gesteuerte Ausführung der Dateisystem-Tools verifizieren, sind vorhanden und grün.
- [x] Der Block ist in der Dokumentation (`REFAKTORING_PLANalt.md`, `blocks.md`) als abgeschlossen markiert.
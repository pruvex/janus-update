# Phase 5: Dateisystem-Operationen

## 1. Zweck

Dieser Block ermöglicht das sichere und kontrollierte Ausführen von Dateisystemoperationen (Erstellen, Löschen, Umbenennen, Verschieben von Dateien und Ordnern) über eine natürliche Sprachschnittstelle, gesteuert durch den LLM-Switch. Das Feature soll robust sein und bestehende Funktionen nicht beeinträchtigen.

## 2. Schlüsselkomponenten

*   `backend/filesystem_manager.py`: Neues Modul, das die Kernlogik für Dateisystemoperationen enthält.
*   `backend/schemas.py`: Erweiterung um Pydantic-Modelle für die Argumente der Dateisystem-Tools.
*   `backend/tool_registry.py`: Registrierung der neuen Dateisystem-Tools.

## 3. Implementierungsplan

### Phase 3.1: Tool-Definition und Registrierung

1.  **Pydantic-Modelle in `backend/schemas.py` definieren:**
    *   `CreateFileArgs(path: str, content: str = "")`
    *   `DeleteFileArgs(path: str)`
    *   `RenameFileArgs(old_path: str, new_path: str)`
    *   `MoveFileArgs(source_path: str, destination_path: str)`
    *   `CreateDirectoryArgs(path: str)`
    *   `DeleteDirectoryArgs(path: str)`
    *   `ListDirectoryArgs(path: str)`
    *   `ReadFileArgs(path: str)`

2.  **Tools in `backend/tool_registry.py` registrieren:**
    *   Jedes Tool muss eine klare Beschreibung für das LLM erhalten, die seine Funktion und Parameter erklärt.
    *   Beispiel für `create_file_tool`:
        ```python
        TOOL_REGISTRY.register(
            Tool(
                name="create_file_tool",
                description="Erstellt eine neue Datei mit optionalem Inhalt. Nützlich, um Notizen zu speichern oder neue Skripte zu erstellen.",
                args_schema=CreateFileArgs,
                func=filesystem_manager.create_file
            )
        )
        ```
    *   Die Funktionen `filesystem_manager.create_file` etc. müssen natürlich existieren.

### Phase 3.2: Dateisystem-Manager-Modul (`backend/filesystem_manager.py`)

1.  **Neue Datei `backend/filesystem_manager.py` erstellen.**
2.  **Implementierung der Kernfunktionen:**
    *   `create_file(path: str, content: str = "")`: Erstellt eine Datei.
    *   `delete_file(path: str)`: Löscht eine Datei.
    *   `rename_file(old_path: str, new_path: str)`: Benennt eine Datei um.
    *   `move_file(source_path: str, destination_path: str)`: Verschiebt eine Datei.
    *   `create_directory(path: str)`: Erstellt einen Ordner.
    *   `delete_directory(path: str)`: Löscht einen Ordner (rekursiv).
    *   `list_directory(path: str)`: Listet Inhalte eines Ordners auf.
    *   `read_file(path: str)`: Liest den Inhalt einer Datei.

3.  **Robuste Pfadvalidierung und Sicherheitsprüfungen:**
    *   **Absolute Pfade erzwingen:** Alle Pfade müssen absolut sein.
    *   **Normalisierung:** `pathlib.Path.resolve()` verwenden, um Pfade zu normalisieren und Symlinks aufzulösen.
    *   **Ausschluss von Windows-Systemordnern:**
        *   Eine Liste von zu schützenden Pfaden definieren (z.B. `os.environ.get('WINDIR')`, `os.environ.get('PROGRAMFILES')`, `os.environ.get('PROGRAMFILES(X86)')`, `os.path.expanduser('~\AppData')`).
        *   Vor jeder Operation prüfen, ob der Zielpfad oder ein Teil des Pfades in einem geschützten Ordner liegt. Bei Verstoß `HTTPException` auslösen.
    *   **Berechtigungsprüfung:** `os.access()` verwenden, um vor Operationen zu prüfen, ob die Anwendung die nötigen Berechtigungen hat.
    *   **Fehlerbehandlung:** `try-except`-Blöcke für `FileNotFoundError`, `PermissionError`, `IsADirectoryError`, `NotADirectoryError` etc.

### Phase 3.3: Integration mit LLM Gateway

1.  **Import `filesystem_manager` in `backend/llm_gateway.py`**.
2.  Sicherstellen, dass der LLM Gateway die neuen Tools korrekt an den `filesystem_manager` weiterleitet, wenn das LLM sie vorschlägt. Dies sollte durch die Registrierung in `tool_registry.py` automatisch geschehen.

### Phase 3.4: Testen

1.  **Unit-Tests für `backend/filesystem_manager.py`:**
    *   Umfassende Tests für jede Funktion (`create_file`, `delete_file` etc.).
    *   Tests für Pfadvalidierung und Sicherheitsprüfungen (z.B. Versuch, in Systemordner zu schreiben, ungültige Pfade, fehlende Berechtigungen).
    *   Mocking des Dateisystems (z.B. mit `unittest.mock.mock_open` oder `pyfakefs`) für isolierte Tests.

2.  **Integrationstests (LLM-gesteuert):**
    *   Tests, die überprüfen, ob das LLM die Dateisystem-Tools korrekt erkennt und mit den richtigen Argumenten aufruft.
    *   Szenarien: "Erstelle eine Datei namens 'notiz.txt' mit dem Inhalt 'Hallo Welt'", "Lösche den Ordner 'temp'", "Verschiebe 'bericht.pdf' nach 'archiv'".

## 4. Definition of Done (für diesen Block)

*   [x] Alle angeforderten Dateisystemoperationen (Erstellen, Löschen, Umbenennen, Verschieben von Dateien/Ordnern) sind in `filesystem_manager.py` implementiert.
*   [x] Robuste Pfadvalidierung und Sicherheitsprüfungen (Ausschluss von Systemordnern, Schutz vor Directory Traversal) sind implementiert.
*   [x] Pydantic-Modelle für alle Dateisystem-Tools sind in `schemas.py` definiert.
*   [x] Alle Dateisystem-Tools sind in `tool_registry.py` registriert.
*   [x] Umfassende Unit-Tests für `filesystem_manager.py` sind vorhanden und grün.
*   [x] Integrationstests, die die LLM-gesteuerte Ausführung der Dateisystem-Tools verifizieren, sind vorhanden und grün.
*   [x] Der Block ist in der Dokumentation (`REFAKTORING_PLANalt.md`, `blocks.md`) als abgeschlossen markiert.

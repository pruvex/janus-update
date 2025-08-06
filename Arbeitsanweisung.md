AGENTIC HANDLUNGSPLAN:
Dein Ziel: Erstelle und verifiziere ein Python-Skript (validate_structure.py), das die Goldstandard-Projektstruktur validiert. Du bist für die korrekte Syntax und Implementierung des Python-Codes verantwortlich.
Relevante PHASE_X.md: C:\KI\Janus-Projekt\PHASE_0_PHOENIX_PROTOKOLL.md
# Schritt-für-Schritt-Anweisungen:
Implementierung des Validierungs-Skripts:
Ziel: Erstelle eine neue Python-Datei C:\KI\Janus-Projekt\validate_structure.py.
Funktionale Anforderungen an den Code:
Das Skript muss die Existenz der Verzeichnisse backend, janus und waechter im aktuellen Arbeitsverzeichnis prüfen.
Wenn alle Verzeichnisse existieren, muss es die exakte Zeichenkette VALIDATION PASSED: Die Projektstruktur entspricht dem Goldstandard. auf die Konsole ausgeben und mit dem Exit-Code 0 enden.
Wenn eines oder mehrere Verzeichnisse fehlen, muss es eine Fehlermeldung ausgeben, die die Namen der fehlenden Verzeichnisse enthält (z.B. VALIDATION FAILED: ...), und mit einem Exit-Code ungleich 0 enden.
Implementierung des Test-Wrappers:
Ziel: Erstelle ein temporäres Python-Skript C:\KI\Janus-Projekt\run_validation_test.py.
Funktionale Anforderungen an den Code:
Das Skript muss validate_structure.py als externen Prozess aufrufen.
Es muss einen Erfolgsfall testen (wenn die Ordnerstruktur korrekt ist) und einen Fehlerfall (indem es temporär einen der Ordner löscht oder umbenennt und dann den Validierer aufruft).
Es muss nach dem Fehlerfall-Test den ursprünglichen Zustand wiederherstellen.
Wenn beide Tests (Erfolgs- und Fehlerfall) das erwartete Verhalten zeigen (korrekte Ausgabe und korrekter Exit-Code), muss das Skript die exakte Zeichenkette --- Alle Tests bestanden. Das Validierungs-Skript funktioniert korrekt. --- ausgeben.
Ausführung des Funktionstests: Führe das von dir in Schritt 2 erstellte Test-Wrapper-Skript aus: python C:\KI\Janus-Projekt\run_validation_test.py.
Aufräumen: Lösche das temporäre Test-Wrapper-Skript: rm C:\KI\Janus-Projekt\run_validation_test.py.
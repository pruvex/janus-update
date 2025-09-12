Anweisung 1: Modifiziere die Datei backend/main.py
Aktion: Die Funktion zur Erkennung von Bestätigungen muss erweitert werden, um zuverlässiger zu arbeiten.
Öffnen Sie die Datei: backend/main.py.
Suchen Sie die Funktion is_confirmation(prompt: str) -> bool:.
Ersetzen Sie den gesamten Inhalt dieser Funktion durch den folgenden Codeblock:
code
Python
def is_confirmation(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt eine positive Bestätigung ist."""
    # Liste von Phrasen, die eine exakte Übereinstimmung für eine Bestätigung erfordern.
    # Dies verhindert, dass Sätze, die nur "ja" enthalten, fälschlicherweise als Bestätigung gewertet werden.
    confirm_phrases = [
        "das ist richtig", "das stimmt", "ja genau", "ja das stimmt", "ist korrekt",
        "genau", "richtig", "korrekt", "stimmt", "ja"
    ]
    prompt_lower = prompt.lower().strip().replace('.', '').replace('!', '')
    
    # Prüfe auf exakte Übereinstimmung mit einer der Phrasen in der Liste.
    return prompt_lower in confirm_phrases
Anweisung 2: Modifiziere die Datei backend/memory_extractor.py
Aktion: Die Bedingung zur Überprüfung extrahierter Fakten muss verbessert werden, um das Speichern von irrelevanten "Keine."-Einträgen zu verhindern.
Öffnen Sie die Datei: backend/memory_extractor.py.
Suchen Sie die folgende Code-Zeile:
code
Python
if extracted_text and extracted_text.lower() not in ['none', 'keine']:
Ersetzen Sie diese eine Zeile durch die folgende korrigierte Zeile, die auch Leerzeichen und Punkte am Ende des Strings bereinigt:
code
Python
if extracted_text and extracted_text.lower().strip().rstrip('.') not in ['none', 'keine']:
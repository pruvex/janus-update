Arbeitsanweisung: Wochentag aus Datum berechnen

Ziel: Implementiere eine Funktion, die einen gegebenen Datumsstring (z.B. „10. Oktober 2025“) in ein Datum-Objekt umwandelt und den entsprechenden Wochentag zurückgibt.


Schritte:


Datumsformat definieren:



Wir verwenden das Format „dd. Monat yyyy“ (z.B. „10. Oktober 2025“). 

Es ist wichtig, sicherzustellen, dass der Monat in voller Länge angegeben wird.



Funktion zur Umwandlung:



Erstelle eine Funktion get_weekday_from_date(date_string), die einen Datumsstring entgegennimmt und den Wochentag zurückgibt.



Code-Beispiel:



Verwende Python und die datetime-Bibliothek zur Verarbeitung des Datums. Hier ist ein Beispielcode:


from datetime import datetime

def get_weekday_from_date(date_string: str) -> str:
    # Definiere das Datumsformat
    date_format = "%d. %B %Y"
    
    try:
        # Konvertiere den Datumsstring in ein Datum-Objekt
        date_obj = datetime.strptime(date_string, date_format)
        # Hole den Wochentag als String
        return date_obj.strftime("%A")  # Gibt den Wochentag (z.B. "Donnerstag") zurück
    except ValueError:
        return "Ungültiges Datumsformat. Bitte gebe das Datum im Format 'dd. Monat yyyy' ein."

# Beispielverwendung
date_input = "10. Oktober 2025"
print(get_weekday_from_date(date_input))  # Ausgabe: Donnerstag


Fehlerbehandlung:



Implementiere eine Fehlerbehandlung, die sicherstellt, dass der Benutzer über Eingabefehler informiert wird, wenn das Datumsformat nicht dem erwarteten Muster entspricht.



Integration ins bestehende System:



Füge die Funktion in den relevanten Teil des Codes ein, in dem Datumsverarbeitung stattfindet.

Stelle sicher, dass die Funktion aufgerufen wird, wenn das Datum benötigt wird, und dass der Wochentag korrekt in der Benutzeroberfläche angezeigt wird.





Zusätzliche Hinweise:


Falls die Anwendung internationalisiert werden soll, könnte es sinnvoll sein, auch verschiedene Datumsformate zu unterstützen.

Überlege dir, die Funktion in ein Modul zu packen, damit sie leicht wiederverwendet werden kann.
@echo off
chcp 65001 > nul
echo Debug-Skript fuer Janus Backend wird gestartet...
echo.

REM Setze den Pfad zur Backend-Anwendung.
set "BACKEND_EXE=C:\Program Files\Janus Projekt\resources\dist\janus_backend\janus_backend.exe"

echo Versuche, das Backend unter dem folgenden Pfad zu starten:
echo %BACKEND_EXE%
echo.

REM Pruefe, ob die Datei existiert
if not exist %BACKEND_EXE% (
    echo FEHLER: Die Datei janus_backend.exe wurde unter dem erwarteten Pfad nicht gefunden.
    echo Bitte ueberpruefe den Installationspfad und passe ihn im Skript bei Bedarf an.
    pause
    exit /b
)

echo Erstelle Log-Datei auf dem Desktop...
REM Fuehre die Anwendung aus und leite die Ausgabe in eine Log-Datei auf dem Desktop um.
%BACKEND_EXE% > "%USERPROFILE%\Desktop\backend_crash_log.txt" 2>&1

echo.
echo Fertig.
echo Eine Datei namens "backend_crash_log.txt" sollte jetzt auf deinem Desktop sein.
echo Bitte oeffne diese Datei, kopiere den gesamten Inhalt und fuege ihn in den Chat mit der KI ein.
echo.
pause

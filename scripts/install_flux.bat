@echo off
title Janus Local Image Engine Installer (ComfyUI)
color 0A

echo =======================================================
echo     Janus-Projekt: Local Image Engine Installation
echo =======================================================
echo.

:: 1. Verzeichnis klonen
if exist "C:\KI\Janus-Image-Engine\main.py" goto SKIP_CLONE
echo [1/4] Erstelle Verzeichnis und klone ComfyUI...
mkdir "C:\KI\Janus-Image-Engine"
git clone https://github.com/comfyanonymous/ComfyUI.git "C:\KI\Janus-Image-Engine"
:SKIP_CLONE
echo [1/4] Verzeichnis existiert bereits. Ueberspringe Clone.

cd /d "C:\KI\Janus-Image-Engine"

:: 2. Venv erstellen
if exist "venv\Scripts\python.exe" goto SKIP_VENV
echo [2/4] Erstelle virtuelles Python-Environment (venv)...
python -m venv venv
:SKIP_VENV
echo [2/4] Venv existiert bereits.

:: 3. Pakete installieren
echo [3/4] Installiere Abhaengigkeiten...
call venv\Scripts\activate.bat

echo Installiere PyTorch (CUDA)... Bitte warten!
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo Installiere ComfyUI requirements...
pip install -r requirements.txt

:: 4. Start-Skript bauen
echo [4/4] Erstelle Start-Skript...
echo @echo off > run_engine.bat
echo title Janus Local Image Engine (ComfyUI) >> run_engine.bat
echo cd /d "%%~dp0" >> run_engine.bat
echo call venv\Scripts\activate.bat >> run_engine.bat
echo python main.py --port 8188 >> run_engine.bat
echo pause >> run_engine.bat

echo.
echo =======================================================
echo Installation ABGESCHLOSSEN!
echo Starte nun ComfyUI Test-Server...
echo =======================================================
call run_engine.bat
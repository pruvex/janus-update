@echo off
title Janus CPU Engine Installer (Stable Diffusion 1.5)
color 0A

set "INSTALL_DIR=C:\KI\Janus-Image-Engine-CPU"

if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
)

cd /d "%INSTALL_DIR%"

if not exist "venv" (
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installiere PyTorch (CPU) und Diffusers...
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install diffusers transformers accelerate fastapi uvicorn

echo Erstelle lokale CPU-Engine-Dateien...
(
  echo from fastapi import FastAPI
  echo import uvicorn
  echo.
  echo app = FastAPI^(title="Janus CPU Image Engine"^)
  echo.
  echo @app.get^("/"^)
  echo async def root^(^):
  echo     return {"status": "ok", "engine": "cpu"}
  echo.
  echo if __name__ == "__main__":
  echo     uvicorn.run^(app, host="127.0.0.1", port=8188^)
) > engine_server.py

(
  echo @echo off
  echo title Janus CPU Image Engine
  echo cd /d "%%~dp0"
  echo call venv\Scripts\activate.bat
  echo set PYTHONPATH=%%~dp0\..
  echo python -m backend.services.local_image_server
) > run_engine.bat

echo Stable Diffusion 1.5 CPU-Engine ist installiert.

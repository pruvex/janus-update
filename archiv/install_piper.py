"""
Piper TTS Installation Script
Lädt Piper Binary und deutsche Modelle herunter
"""
import os
import urllib.request
import zipfile
import json
from pathlib import Path

# Verzeichnisse
BASE_DIR = Path(__file__).parent
BIN_DIR = BASE_DIR / "backend" / "bin"
MODELS_DIR = BASE_DIR / "backend" / "models" / "piper" / "de"

BIN_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("Piper TTS Installation\n")

# 1. Piper Binary (Windows)
PIPER_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
PIPER_ZIP = BIN_DIR / "piper.zip"
PIPER_EXE = BIN_DIR / "piper.exe"

if not PIPER_EXE.exists():
    print("Lade Piper Binary herunter...")
    urllib.request.urlretrieve(PIPER_URL, PIPER_ZIP)
    print("Entpacke Piper...")
    with zipfile.ZipFile(PIPER_ZIP, 'r') as zip_ref:
        zip_ref.extractall(BIN_DIR)
    # Move piper.exe from subdirectory to bin/
    for file in BIN_DIR.rglob("piper.exe"):
        file.rename(PIPER_EXE)
        break
    PIPER_ZIP.unlink()
    print(f"Piper installiert: {PIPER_EXE}")
else:
    print(f"Piper bereits vorhanden: {PIPER_EXE}")

# 2. Deutsche Modelle
MODELS = [
    {
        "name": "Thorsten (Hoch)",
        "base_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/high",
        "files": ["de_DE-thorsten-high.onnx", "de_DE-thorsten-high.onnx.json"]
    },
    {
        "name": "Thorsten (Mittel) - Empfohlen",
        "base_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium",
        "files": ["de_DE-thorsten-medium.onnx", "de_DE-thorsten-medium.onnx.json"]
    },
    {
        "name": "Eva K (Niedrig)",
        "base_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/eva_k/x_low",
        "files": ["de_DE-eva_k-x_low.onnx", "de_DE-eva_k-x_low.onnx.json"]
    }
]

for model in MODELS:
    print(f"\nLade Modell: {model['name']}")
    for file in model["files"]:
        target = MODELS_DIR / file
        if target.exists():
            print(f"  {file} bereits vorhanden")
            continue
        
        url = f"{model['base_url']}/{file}"
        print(f"  Lade {file}...")
        try:
            urllib.request.urlretrieve(url, target)
            print(f"  {file} heruntergeladen")
        except Exception as e:
            print(f"  Fehler bei {file}: {e}")

print("\nInstallation abgeschlossen!")
print(f"\nPiper Binary: {PIPER_EXE}")
print(f"Modelle: {MODELS_DIR}")
print("\nStarten Sie den Backend neu, um Piper zu nutzen.")
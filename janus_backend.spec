# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

# --- PFAD-LOGIK ---
# Wir ermitteln den absoluten Pfad zum Projekt-Root (wo die .spec Datei liegt)
SPECPATH = os.path.dirname(os.path.abspath(SPEC))
print(f"DEBUG: Building from Root: {SPECPATH}")

# Definition der Pfade zu den Assets
# Prüfe, ob die Ordner existieren, um Fehler beim Build zu sehen
static_src = os.path.join(SPECPATH, 'backend', 'static')
config_src = os.path.join(SPECPATH, 'backend', 'config')
bin_src    = os.path.join(SPECPATH, 'backend', 'bin')

if not os.path.exists(static_src):
    raise FileNotFoundError(f"CRITICAL: Static folder not found at {static_src}")

# --- DATAS ZUSAMMENBAUEN ---
# Syntax: (Absoluter_Quellpfad, Zielpfad_in_EXE_Ordner)
datas = []
datas += [(static_src, 'backend/static')]
datas += [(config_src, 'backend/config')]
if os.path.exists(bin_src):
    datas += [(bin_src, 'backend/bin')]

# Frontend build directory for PyInstaller
frontend_dist_src = os.path.join(SPECPATH, 'frontend', 'dist')
if os.path.exists(frontend_dist_src):
    datas += [(frontend_dist_src, 'frontend/dist')]
    print(f"DEBUG: Added frontend/dist to PyInstaller data: {frontend_dist_src}")
else:
    print(f"WARNING: Frontend dist directory not found at {frontend_dist_src}. Make sure to run 'npm run build' first.")

# Dateparser Cache (für den Pickle Fehler)
datas += collect_data_files('dateparser')

# Metadaten
datas += copy_metadata('tqdm')
datas += copy_metadata('regex')
datas += copy_metadata('requests')
datas += copy_metadata('packaging')
datas += copy_metadata('filelock')
datas += copy_metadata('numpy')
datas += copy_metadata('huggingface_hub')
datas += copy_metadata('safetensors')
datas += copy_metadata('sentence_transformers')

block_cipher = None

# --- ANALYSIS ---
# ACHTUNG: Hier prüfen wir, wo main.py liegt.
# Wenn main.py im backend-Ordner liegt, müssen wir das angeben.
script_path = os.path.join(SPECPATH, 'backend', 'main.py')
if not os.path.exists(script_path):
    # Fallback: Vielleicht liegt main.py doch im Root?
    script_path = os.path.join(SPECPATH, 'main.py')

print(f"DEBUG: Analyzing script: {script_path}")

a = Analysis(
    [script_path], # Hier nutzen wir den gefundenen Pfad
    pathex=[SPECPATH], # WICHTIG: Root zum Pfad hinzufügen, damit Imports klappen
    binaries=[],
    datas=datas,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan.on',
        'engineio.async_drivers.aiohttp',
        'sklearn.utils._cython_blas',
        'sklearn.neighbors.typedefs',
        'sklearn.neighbors.quad_tree',
        'sklearn.tree._utils',
        'sentence_transformers',
        'watchfiles',
        'websockets',
        'fpdf',
        'pypdf',
        'ebooklib',
        'backend.utils.paths'
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='janus_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='janus_backend',
)

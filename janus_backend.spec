# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files

# WIR DEFINIEREN ALLES HIER OBEN, KLAR UND DEUTLICH
UPX_DIR = 'C:\\tools\\upx-5.1.0-win64'

# 1. Automatische Daten für dateparser
dateparser_data = collect_data_files('dateparser')

# CLIP Daten-Dateien
clip_data = collect_data_files('clip')

# ChromaDB Daten-Dateien und Submodule (BACKLOG-017 Fix)
chromadb_data = collect_data_files('chromadb')
chromadb_submodules = collect_data_files('chromadb', include_py_files=True)

# 2. HIER FÜGEN WIR DEINE BILDER, CONFIGS UND DAS FRONTEND HINZU
my_project_data = [
    ('backend\\config', 'backend\\config'),  # Wichtig für style_profiles.json
    ('backend\\assets', 'backend\\assets'),  # Wichtig für Vorschaubilder
    
    # Frontend Build (Vite kopiert 'public/sounds' automatisch hier rein!)
    ('frontend\\dist', 'frontend\\dist'), 
    
    # Restliche Assets (optional)
    ('frontend\\assets', 'frontend\\dist\\assets'),
    ('backend\\static', 'backend\\static'),  # Wichtig für generierte Bilder

    # CLIP Daten-Dateien manuell hinzufügen
    ('backend\\assets\\bpe_simple_vocab_16e6.txt.gz', 'clip'),
    
    # Capability Registry und Skills für PyInstaller-EXE
    ('backend/data/capability_registry.json', 'backend/data'),
    ('backend/skills', 'backend/skills'),
]

# Security gate: packaged beta builds must never embed local .env files.
# Runtime credentials come from Keyring/AppData or explicit deployment setup.

# 3. Wir kombinieren alle Listen
all_datas = dateparser_data + clip_data + chromadb_data + chromadb_submodules + my_project_data

a = Analysis(
    ['backend\\main.py'],
    pathex=[],
    binaries=[],
    datas=all_datas,  # <--- HIER NEHMEN WIR JETZT ALLES MIT (Bilder + Dateparser + ChromaDB)
    hiddenimports=[
        'chromadb.telemetry.product.posthog',
        'chromadb.api.rust',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 'googleapiclient',  # Wird für Gemini benötigt
        # 'av',  # Wird für faster-whisper benötigt
        'tensorboard',
        # 'torch.testing',  # Wird von torch.autograd benötigt
        # 'torch._inductor',  # Benötigt
        # 'torch._dynamo',    # Benötigt
        # 'torch.distributed',  # Benötigt
        'torch.utils.cpp_extension',
        # 'torchvision',  # Wird von CLIP benötigt
        'torchaudio',
        # 'numpy.testing',  # Benötigt
        'scipy.tests',
        'lib2to3',
        # 'unittest',  # Benötigt
        'tkinter',
        'PyQt5', 'PyQt6', 'wx',
        'IPython', 'jupyter', 'notebook',
        'pandas'
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# WIR MACHEN ALLES IN DER EXE-SEKTION. ES GIBT KEINE COLLECT-SEKTION MEHR.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='janus_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_dir=UPX_DIR,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

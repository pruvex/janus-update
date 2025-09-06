# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['backend/main.py'],
    pathex=[],
    binaries=[],
    datas=(
        ('backend/model_catalog.json', 'backend'),
        ('backend/static', 'backend/static'),
        ('backend/model_cache', 'backend/model_cache'),
        (r'C:\Users\pruve\AppData\Roaming\Python\Python311\site-packages\tiktoken', 'tiktoken'),
        (r'C:\Users\pruve\AppData\Roaming\Python\Python311\site-packages\tiktoken_ext', 'tiktoken_ext')
    ),
    hiddenimports=['uvicorn.workers', 'backend.utils.paths', 'uvicorn', 'watchfiles', 'websockets'],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='janus_backend',
)

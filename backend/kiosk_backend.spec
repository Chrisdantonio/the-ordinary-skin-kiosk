# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the kiosk backend binary.

Build from project root:
  backend/.venv/bin/pyinstaller backend/kiosk_backend.spec --noconfirm

Output: backend/dist/kiosk-backend/  (the whole directory is shipped as a
resource inside the Electron .app via electron-builder extraResources)
"""

import certifi

block_cipher = None

a = Analysis(
    ['server.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Product catalog — regimen agent reads this at runtime
        ('../products/catalog.json', 'products'),
        # SSL certs for httpx (catalog_sync outbound requests)
        (certifi.where(), 'certifi'),
    ],
    hiddenimports=[
        # uvicorn selects its event loop and HTTP protocol at startup via
        # dynamic import — PyInstaller can't see these statically.
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        # anyio asyncio backend (used by starlette / fastapi internally)
        'anyio._backends._asyncio',
        # httptools / websockets (uvicorn optional dependencies)
        'httptools',
        'httptools.parser',
        'websockets',
        'websockets.legacy',
        'websockets.legacy.server',
    ],
    hookspath=[],
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
    name='kiosk-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,        # upx can break macOS binaries; leave off
    console=True,     # keep console so Electron can pipe the logs
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='kiosk-backend',
)

# PyInstaller spec — build with: pyinstaller bot.spec
# Must be run ON Windows (PyInstaller does not cross-compile).

import sys

block_cipher = None

hidden_imports = [
    "telethon",
    "telethon.tl.types",
    "telethon.tl.functions",
    "telethon.crypto",
    "telethon.extensions",
    "yaml",
    "dotenv",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="signal_forwarder",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
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
    upx=False,
    upx_exclude=[],
    name="signal_forwarder",
)

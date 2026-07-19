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
    "eth_account",
    "eth_account.signers.local",
    "eth_keys",
    "eth_utils",
    "coincurve",
    "hyperliquid",
    "hyperliquid.exchange",
    "hyperliquid.info",
    "hyperliquid.api",
    "hyperliquid.utils",
    "hyperliquid.utils.signing",
    "hyperliquid.utils.types",
    "hyperliquid.utils.constants",
    "msgpack",
    "websocket",
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="whale_mirror_bot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

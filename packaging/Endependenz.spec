# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project_root = Path(SPECPATH).resolve().parent
hidden_imports = ["google.genai", "google.genai.types"] + collect_submodules("keyring.backends")

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root / "src"), str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / "assets"), "assets"),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "IPython",
        "jedi",
        "matplotlib",
        "nbformat",
        "numpy",
        "pytest",
        "unittest.mock",
        "zmq",
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Endependenz",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Endependenz",
)

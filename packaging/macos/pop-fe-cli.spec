# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, SPECPATH)
from spec_common import packaging_inputs


ROOT = Path(SPECPATH).parents[1]
GENERATED = ROOT / "build" / "macos" / "generated"
datas, binaries, hiddenimports = packaging_inputs(ROOT)

a = Analysis(
    [str(ROOT / "pop-fe.py")],
    pathex=[str(GENERATED), str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["scipy", "sklearn"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="pop-fe",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
)

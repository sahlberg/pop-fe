# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['pop-fe-ps3.py'],
    pathex=[],
    binaries=[],
    datas=[('PS3LOGO.DAT', '.'), ('pop-fe-ps3.ui', '.')],
    hiddenimports=['pop-fe', 'pygubu.builder.tkstdwidgets', 'pygubu.builder.ttkstdwidgets', 'pygubu.builder.widgets.pathchooserinput'],
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
    name='pop-fe-ps3',
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
    name='pop-fe-ps3',
)

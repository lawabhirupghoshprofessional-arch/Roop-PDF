# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


ROOT_DIR = Path.cwd().resolve()
if not (ROOT_DIR / 'src').exists() and (ROOT_DIR.parent / 'src').exists():
    ROOT_DIR = ROOT_DIR.parent
SRC_DIR = ROOT_DIR / 'src'
ASSETS_DIR = ROOT_DIR / 'assets'
ENTRYPOINT = SRC_DIR / 'roop_pdfmd' / '__main__.py'


a = Analysis(
    [str(ENTRYPOINT)],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=[(str(ASSETS_DIR), 'assets')],
    hiddenimports=['fitz', 'pytesseract', 'PIL'],
    hookspath=[],
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
    a.binaries,
    a.datas,
    [],
    name='roop-pdfmd',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='roop-pdfmd',
)

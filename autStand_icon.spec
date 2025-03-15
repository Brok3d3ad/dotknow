# -*- mode: python ; coding: utf-8 -*-
import os

# Get absolute path to the .ico file
icon_path = os.path.abspath('autStand_ic0n.ico')
logo_path = os.path.abspath('automation_standard_logo.jpg')

a = Analysis(
    ['svg_processor_gui.py'],
    pathex=[],
    binaries=[],
    datas=[(logo_path, '.'), (icon_path, '.')],
    hiddenimports=['numpy', 'PIL', 'PIL._tkinter_finder'],
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
    name='SVG_Processor',
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
    icon=icon_path,
    version='file_version_info.txt',
) 
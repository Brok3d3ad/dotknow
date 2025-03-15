# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.win32 import versioninfo

a = Analysis(
    ['svg_processor_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('automation_standard_logo.jpg', '.'), ('autStand_ic0n.ico', '.')],
    hiddenimports=['numpy', 'PIL', 'PIL._tkinter_finder', 'PIL.ImageDraw'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Create Windows version information
version_file = versioninfo.VSVersionInfo(
    ffi=versioninfo.FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        versioninfo.StringFileInfo(
            [
                versioninfo.StringTable(
                    '040904B0',
                    kids=[
                        versioninfo.StringStruct('CompanyName', 'AutomationStandard'),
                        versioninfo.StringStruct('FileDescription', 'SVG to JSON Converter for Automation Systems'),
                        versioninfo.StringStruct('FileVersion', '1.0.0'),
                        versioninfo.StringStruct('InternalName', 'SVG_Processor'),
                        versioninfo.StringStruct('LegalCopyright', '© 2024 AutomationStandard'),
                        versioninfo.StringStruct('OriginalFilename', 'SVG_Processor.exe'),
                        versioninfo.StringStruct('ProductName', 'SVG Processor'),
                        versioninfo.StringStruct('ProductVersion', '1.0.0')
                    ]
                )
            ]
        ),
        versioninfo.VarFileInfo([versioninfo.VarStruct('Translation', [0x409, 1200])])
    ]
)

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
    icon=['autStand_ic0n.ico'],
    version=version_file,
    uac_admin=False,
)

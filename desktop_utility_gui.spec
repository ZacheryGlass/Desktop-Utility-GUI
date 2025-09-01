# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Desktop Utility GUI
This creates a single executable with all dependencies bundled
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the current directory
SPECPATH = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['main.py'],
    pathex=[SPECPATH],
    binaries=[],
    datas=[
        ('style.qss', '.'),
        ('scripts', 'scripts'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'pywin32',
        'win32com',
        'win32com.client',
        'win32api',
        'win32con',
        'pythoncom',
        'pywintypes',
        'easyocr',
        'torch',
        'torchvision',
        'PIL',
        'Pillow',
        'pyautogui',
        'numpy',
        'cv2',
    ] + collect_submodules('easyocr') + collect_submodules('torch'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'notebook',
        'jupyter',
        'IPython',
        'tkinter',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DesktopUtilityGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
    version='version_info.py' if os.path.exists('version_info.py') else None,
)
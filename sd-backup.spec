# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller sd-backup.spec

import os
import sys

# В namespace PyInstaller передаёт SPEC — путь к spec-файлу
_spec_dir = os.path.dirname(os.path.abspath(SPEC))
try:
    import PyQt6
    pyqt6_root = os.path.dirname(PyQt6.__file__)
    qt_plugins_src = os.path.join(pyqt6_root, 'Qt6', 'plugins')
    qt_lib_src = os.path.join(pyqt6_root, 'Qt6', 'lib')
except Exception:
    qt_plugins_src = ''
    qt_lib_src = ''

def get_qt_datas():
    """Собираем только нужные плагины Qt6: platforms (xcb, wayland), imageformats (обложки)."""
    if not qt_plugins_src or not os.path.isdir(qt_plugins_src):
        return []
    datas = []
    needed = ('platforms', 'platformthemes', 'platforminputcontexts', 'imageformats', 'wayland-decoration-client', 'wayland-shell-integration')
    for name in needed:
        path = os.path.join(qt_plugins_src, name)
        if not os.path.isdir(path):
            continue
        for root, _dirs, files in os.walk(path):
            for f in files:
                if f.endswith('.so'):
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, qt_plugins_src)
                    datas.append((full, os.path.join('PyQt6', 'Qt6', 'plugins', os.path.dirname(rel))))
    return datas

block_cipher = None

a = Analysis(
    [os.path.join(_spec_dir, 'main.py')],
    pathex=[_spec_dir],
    binaries=[],
    datas=get_qt_datas(),
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'src',
        'src.gui',
        'src.gui.main_window',
        'src.gui.dialogs',
        'src.gui.cards',
        'src.core',
        'src.core.devices',
        'src.core.dump',
        'src.core.backups',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='sd-backup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Режим one-file: один исполняемый файл. Для AppImage потом кладём его в AppDir.
# Режим one-dir (раскомментировать ниже и закомментировать EXE выше) — папка с exe и файлами.
# Для AppImage удобнее one-file, чтобы AppRun просто вызывал один бинарник.

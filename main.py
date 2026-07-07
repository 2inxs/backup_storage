#!/usr/bin/env python3
"""
SD Backup — приложение для создания дампов SD-карт и восстановления образов.
Запуск: python main.py  (или ./main.py после chmod +x)
Для доступа к блочным устройствам при создании/восстановлении потребуется ввод пароля (pkexec).
"""
import os
import sys
from pathlib import Path

# При запуске из PyInstaller (AppImage/one-file) — указываем Qt искать плагины в бандле
if getattr(sys, "frozen", False):
    base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    qt_plugin_path = os.path.join(base, "PyQt6", "Qt6", "plugins")
    if os.path.isdir(qt_plugin_path):
        os.environ.setdefault("QT_PLUGIN_PATH", qt_plugin_path)

# Добавляем корень проекта в путь (для запуска из исходников)
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SD Backup")
    app.setApplicationDisplayName("SD Backup")
    app.setStyle("Fusion")

    font = QFont()
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

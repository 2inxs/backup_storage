"""
Диалоги: создание дампа (устройство, имя, обложка), восстановление, прогресс.
"""
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QProgressDialog,
    QGroupBox,
    QFormLayout,
    QDialogButtonBox,
)

from src.core.devices import get_block_devices, BlockDevice
from src.core.dump import create_image, restore_image
from src.core.backups import BackupEntry, add_backup, get_storage_dir, DEFAULT_STORAGE


def _size_of(path: str | Path) -> int:
    try:
        return Path(path).stat().st_size
    except OSError:
        return 0


class DumpWorker(QThread):
    """Поток для создания образа (dd)."""
    progress_line = pyqtSignal(str)
    finished_ok = pyqtSignal(str)
    finished_error = pyqtSignal(str)

    def __init__(self, device_path: str, image_path: str):
        super().__init__()
        self.device_path = device_path
        self.image_path = image_path

    def run(self):
        def on_progress(line: str):
            self.progress_line.emit(line)

        ok, err = create_image(self.device_path, self.image_path, progress_callback=on_progress)
        if ok:
            self.finished_ok.emit(self.image_path)
        else:
            self.finished_error.emit(err or "Ошибка создания образа")


class RestoreWorker(QThread):
    """Поток для восстановления образа на устройство."""
    progress_line = pyqtSignal(str)
    finished_ok = pyqtSignal()
    finished_error = pyqtSignal(str)

    def __init__(self, image_path: str, device_path: str):
        super().__init__()
        self.image_path = image_path
        self.device_path = device_path

    def run(self):
        def on_progress(line: str):
            self.progress_line.emit(line)

        ok, err = restore_image(self.image_path, self.device_path, progress_callback=on_progress)
        if ok:
            self.finished_ok.emit()
        else:
            self.finished_error.emit(err or "Ошибка восстановления")


class CreateDumpDialog(QDialog):
    """Диалог создания нового дампа: выбор устройства, имя, обложка."""

    def __init__(self, storage_dir: Path | None, parent=None):
        super().__init__(parent)
        self.storage_dir = storage_dir or DEFAULT_STORAGE
        self.setWindowTitle("Новый дамп SD-карты")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        group = QGroupBox("Источник")
        form = QFormLayout()
        self.device_combo = QComboBox()
        self._fill_devices()
        form.addRow("Устройство:", self.device_combo)
        group.setLayout(form)
        layout.addWidget(group)

        group2 = QGroupBox("Сохранение")
        form2 = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например: Raspberry Pi 2024")
        form2.addRow("Название дампа:", self.name_edit)
        self.cover_btn = QPushButton("Выбрать картинку обложки...")
        self.cover_btn.clicked.connect(self._pick_cover)
        self.cover_label = QLabel("Не выбрано")
        self.cover_label.setStyleSheet("color: #888;")
        form2.addRow("Обложка:", self.cover_btn)
        form2.addRow("", self.cover_label)
        group2.setLayout(form2)
        layout.addWidget(group2)

        self.cover_path: Path | None = None

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._start)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)

    def _fill_devices(self):
        self.device_combo.clear()
        for dev in get_block_devices(removable_only=True):
            self.device_combo.addItem(dev.display_name, dev.path)
        if self.device_combo.count() == 0:
            self.device_combo.addItem("(Нет съёмных устройств)", "")

    def _pick_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбор обложки",
            str(Path.home()),
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif);;Все файлы (*)",
        )
        if path:
            self.cover_path = Path(path)
            self.cover_label.setText(self.cover_path.name)

    def _start(self):
        device_path = self.device_combo.currentData()
        if not device_path:
            QMessageBox.warning(self, "Ошибка", "Выберите съёмное устройство.")
            return
        name = self.name_edit.text().strip() or "Дамп"
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-")
        if not safe_name:
            safe_name = "backup"
        from datetime import datetime
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = f"{safe_name}_{stamp}.img"
        image_path = self.storage_dir / image_name

        if image_path.exists():
            QMessageBox.warning(self, "Ошибка", f"Файл уже существует: {image_path}")
            return

        self.accept()
        self._run_dump(str(device_path), str(image_path), name)

    def _run_dump(self, device_path: str, image_path: str, name: str):
        prog = QProgressDialog("Создание образа... Это может занять много времени.", None, 0, 0, self.parent())
        prog.setWindowTitle("Дамп")
        prog.setMinimumDuration(0)
        prog.setCancelButton(None)
        status_label = QLabel("")
        prog.setLabel(status_label)

        worker = DumpWorker(device_path, image_path)
        worker.progress_line.connect(lambda line: status_label.setText(line[-80:] if len(line) > 80 else line))
        worker.finished_ok.connect(lambda: self._dump_done(prog, worker, image_path, name))
        worker.finished_error.connect(lambda err: self._dump_error(prog, worker, err))
        worker.finished.connect(prog.close)
        worker.start()
        prog.exec()

    def _dump_done(self, prog: QProgressDialog, worker: DumpWorker, image_path: str, name: str):
        prog.close()
        cover = str(self.cover_path) if self.cover_path else None
        size = _size_of(image_path)
        add_backup(name=name, image_path=image_path, cover_path=cover, size_bytes=size, storage_dir=self.storage_dir)
        QMessageBox.information(self.parent(), "Готово", f"Образ сохранён: {image_path}")
        if hasattr(self.parent(), "refresh_backups"):
            self.parent().refresh_backups()

    def _dump_error(self, prog: QProgressDialog, worker: DumpWorker, err: str):
        prog.close()
        QMessageBox.critical(self.parent(), "Ошибка", f"Не удалось создать образ:\n{err}")


class RestoreDialog(QDialog):
    """Диалог восстановления: выбор целевого устройства."""

    def __init__(self, entry: BackupEntry, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.setWindowTitle("Восстановить образ на SD-карту")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Восстановить образ:\n<b>{entry.name}</b>\n{entry.image_path}"))
        layout.addWidget(QLabel("На устройство:"))

        self.device_combo = QComboBox()
        for dev in get_block_devices(removable_only=True):
            self.device_combo.addItem(dev.display_name, dev.path)
        if self.device_combo.count() == 0:
            self.device_combo.addItem("(Нет съёмных устройств)", "")
        layout.addWidget(self.device_combo)

        warn = QLabel("Внимание: все данные на выбранном устройстве будут уничтожены!")
        warn.setStyleSheet("color: #c00; font-weight: bold;")
        layout.addWidget(warn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._do_restore)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _do_restore(self):
        device_path = self.device_combo.currentData()
        if not device_path:
            QMessageBox.warning(self, "Ошибка", "Выберите устройство.")
            return
        if not Path(self.entry.image_path).exists():
            QMessageBox.critical(self, "Ошибка", f"Файл образа не найден: {self.entry.image_path}")
            return
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Восстановить образ на {device_path}?\nВсе данные на устройстве будут перезаписаны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.accept()
        self._run_restore(device_path)

    def _run_restore(self, device_path: str):
        prog = QProgressDialog("Восстановление образа...", None, 0, 0, self.parent())
        prog.setWindowTitle("Восстановление")
        prog.setMinimumDuration(0)
        prog.setCancelButton(None)
        status_label = QLabel("")
        prog.setLabel(status_label)

        worker = RestoreWorker(self.entry.image_path, device_path)
        worker.progress_line.connect(lambda line: status_label.setText(line[-80:] if len(line) > 80 else line))
        worker.finished_ok.connect(lambda: self._restore_done(prog))
        worker.finished_error.connect(lambda err: self._restore_error(prog, err))
        worker.finished.connect(prog.close)
        worker.start()
        prog.exec()

    def _restore_done(self, prog: QProgressDialog):
        prog.close()
        QMessageBox.information(self.parent(), "Готово", "Образ успешно записан на устройство.")
        prog.close()

    def _restore_error(self, prog: QProgressDialog, err: str):
        prog.close()
        QMessageBox.critical(self.parent(), "Ошибка", f"Ошибка восстановления:\n{err}")

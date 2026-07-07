"""
Главное окно приложения: сетка сохранённых образов, кнопка «Новый дамп».
"""
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QGridLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QFrame,
)

from src.core.backups import load_backups, delete_backup, get_storage_dir, DEFAULT_STORAGE
from src.gui.cards import BackupCard
from src.gui.dialogs import CreateDumpDialog, RestoreDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.storage_dir: Path | None = None
        self.setWindowTitle("SD Backup — дампы и восстановление образов")
        self.setMinimumSize(720, 480)
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Панель инструментов
        toolbar = QHBoxLayout()
        self.new_btn = QPushButton("➕ Новый дамп")
        self.new_btn.clicked.connect(self._on_new_dump)
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.refresh_backups)
        self.folder_btn = QPushButton("Папка бэкапов...")
        self.folder_btn.clicked.connect(self._pick_storage_folder)
        self.storage_label = QLabel("")
        self.storage_label.setStyleSheet("color: #666;")
        toolbar.addWidget(self.new_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.folder_btn)
        toolbar.addWidget(self.storage_label)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Заголовок сетки
        layout.addWidget(QLabel("Сохранённые образы:"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.cards_container = QWidget()
        self.grid = QGridLayout(self.cards_container)
        self.grid.setSpacing(16)
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)

        self._set_storage_label()
        self.refresh_backups()

    def _set_storage_label(self):
        d = self.storage_dir or DEFAULT_STORAGE
        self.storage_label.setText(f"Папка: {d}")

    def _pick_storage_folder(self):
        start = str(self.storage_dir or DEFAULT_STORAGE)
        path = QFileDialog.getExistingDirectory(self, "Выбрать папку для бэкапов", start)
        if path:
            self.storage_dir = Path(path)
            self._set_storage_label()
            self.refresh_backups()

    def _on_new_dump(self):
        dlg = CreateDumpDialog(self.storage_dir, self)
        dlg.exec()

    def refresh_backups(self):
        # Удалить старые карточки
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = load_backups(self.storage_dir)
        cols = 3
        for i, entry in enumerate(entries):
            card = BackupCard(entry)
            card.restore_requested.connect(self._on_restore)
            card.remove_requested.connect(self._on_remove)
            row, col = divmod(i, cols)
            self.grid.addWidget(card, row, col)

        if not entries:
            placeholder = QLabel("Нет сохранённых образов. Нажмите «Новый дамп», чтобы создать образ SD-карты.")
            placeholder.setStyleSheet("color: #888; padding: 24px;")
            self.grid.addWidget(placeholder, 0, 0)

    def _on_restore(self, entry):
        dlg = RestoreDialog(entry, self)
        dlg.exec()

    def _on_remove(self, entry):
        reply = QMessageBox.question(
            self,
            "Удалить из списка?",
            f"Удалить запись «{entry.name}» из списка? Файл образа на диске не удаляется.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_backup(entry.id, self.storage_dir)
            self.refresh_backups()

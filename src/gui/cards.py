"""
Виджет карточки одного сохранённого образа (обложка, название, кнопки).
"""
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QSizePolicy,
    QWidget,
)

from src.core.backups import BackupEntry


def _format_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "—"
    for u, s in [(1e12, "ТБ"), (1e9, "ГБ"), (1e6, "МБ"), (1e3, "КБ")]:
        if size_bytes >= u:
            return f"{size_bytes / u:.1f} {s}"
    return f"{size_bytes} Б"


def _format_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso[:16] if len(iso) > 16 else iso


class BackupCard(QFrame):
    """Одна карточка: обложка, имя, размер/дата, кнопки «Восстановить» и «Удалить из списка»."""

    restore_requested = pyqtSignal(BackupEntry)
    remove_requested = pyqtSignal(BackupEntry)

    CARD_WIDTH = 220
    COVER_HEIGHT = 140

    def __init__(self, entry: BackupEntry, parent: QWidget | None = None):
        super().__init__(parent)
        self.entry = entry
        self.setObjectName("backupCard")
        self.setFixedWidth(self.CARD_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Обложка
        self._cover = QLabel()
        self._cover.setFixedHeight(self.COVER_HEIGHT)
        self._cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover.setStyleSheet("background-color: #2d2d2d; border-radius: 6px;")
        self._cover.setScaledContents(False)
        layout.addWidget(self._cover)
        self._load_cover()

        # Название
        name_label = QLabel(entry.name)
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFont(QFont("Sans", 10, QFont.Weight.DemiBold))
        layout.addWidget(name_label)

        # Размер и дата
        info = QLabel(f"{_format_size(entry.size_bytes)} · {_format_date(entry.created_at)}")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        restore_btn = QPushButton("Восстановить")
        restore_btn.setDefault(True)
        restore_btn.clicked.connect(lambda: self.restore_requested.emit(self.entry))
        remove_btn = QPushButton("Удалить")
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.entry))
        btn_layout.addWidget(restore_btn)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)

    def _load_cover(self):
        cover_path = self.entry.cover_path
        if cover_path and Path(cover_path).exists():
            pix = QPixmap(cover_path)
            if not pix.isNull():
                scaled = pix.scaled(
                    self.CARD_WIDTH - 16,
                    self.COVER_HEIGHT - 8,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._cover.setPixmap(scaled)
                return
        # Плейсхолдер: иконка или текст
        self._cover.setText("📀 Образ SD")
        self._cover.setStyleSheet(
            "background-color: #2d2d2d; border-radius: 6px; color: #666; font-size: 14px;"
        )

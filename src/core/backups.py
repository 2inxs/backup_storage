"""
Хранение метаданных сохранённых образов: имя, обложка, путь к файлу, дата.
"""
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

FILENAME_META = "backups.json"
DEFAULT_STORAGE = Path.home() / "SD-Backups"


@dataclass
class BackupEntry:
    id: str
    name: str
    image_path: str
    cover_path: Optional[str] = None
    created_at: str = ""
    size_bytes: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


def _storage_dir(custom_dir: Path | None) -> Path:
    d = custom_dir or DEFAULT_STORAGE
    d.mkdir(parents=True, exist_ok=True)
    return d


def _meta_path(storage_dir: Path) -> Path:
    return _storage_dir(storage_dir) / FILENAME_META


def load_backups(storage_dir: Path | None = None) -> list[BackupEntry]:
    """Загрузить список бэкапов из backups.json."""
    path = _meta_path(storage_dir or DEFAULT_STORAGE)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [
            BackupEntry(
                id=b.get("id", ""),
                name=b.get("name", "Без имени"),
                image_path=b.get("image_path", ""),
                cover_path=b.get("cover_path"),
                created_at=b.get("created_at", ""),
                size_bytes=int(b.get("size_bytes", 0)),
            )
            for b in data.get("backups", [])
        ]
    except (json.JSONDecodeError, OSError):
        return []


def save_backups(entries: list[BackupEntry], storage_dir: Path | None = None) -> bool:
    """Сохранить список бэкапов в backups.json."""
    path = _meta_path(storage_dir or DEFAULT_STORAGE)
    try:
        data = {
            "backups": [
                {
                    "id": e.id,
                    "name": e.name,
                    "image_path": e.image_path,
                    "cover_path": e.cover_path,
                    "created_at": e.created_at,
                    "size_bytes": e.size_bytes,
                }
                for e in entries
            ]
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def add_backup(
    name: str,
    image_path: str | Path,
    cover_path: str | Path | None = None,
    size_bytes: int = 0,
    storage_dir: Path | None = None,
) -> BackupEntry:
    """Добавить запись о новом бэкапе и сохранить."""
    storage = storage_dir or DEFAULT_STORAGE
    entries = load_backups(storage)
    entry = BackupEntry(
        id=str(uuid.uuid4()),
        name=name,
        image_path=str(image_path),
        cover_path=str(cover_path) if cover_path else None,
        size_bytes=size_bytes,
    )
    entries.append(entry)
    save_backups(entries, storage)
    return entry


def delete_backup(entry_id: str, storage_dir: Path | None = None) -> bool:
    """Удалить запись о бэкапе из метаданных (файл образа не удаляется)."""
    storage = storage_dir or DEFAULT_STORAGE
    entries = [e for e in load_backups(storage) if e.id != entry_id]
    if len(entries) == len(load_backups(storage)):
        return False
    return save_backups(entries, storage)


def get_storage_dir(custom: Path | None = None) -> Path:
    return _storage_dir(custom)

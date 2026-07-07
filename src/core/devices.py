"""
Получение списка блок-устройств (дисков) для дампа и восстановления.
Показываем съёмные диски (SD, USB) и при необходимости все диски.
"""
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BlockDevice:
    name: str
    path: str
    size: str
    model: str
    removable: bool

    @property
    def display_name(self) -> str:
        model = (self.model or "").strip()
        if model:
            return f"/dev/{self.name} — {model} ({self.size})"
        return f"/dev/{self.name} — {self.size}"


def _get_lsblk_json() -> dict | None:
    """Запуск lsblk с выводом в JSON."""
    try:
        out = subprocess.run(
            ["lsblk", "--json", "-o", "NAME,SIZE,TYPE,RM,MODEL"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode != 0:
            return None
        return json.loads(out.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
        return None


def get_block_devices(removable_only: bool = True) -> list[BlockDevice]:
    """
    Список блок-устройств типа «диск».
    Если removable_only=True — только съёмные (SD, USB).
    """
    data = _get_lsblk_json()
    if not data:
        return []

    devices: list[BlockDevice] = []
    for dev in data.get("blockdevices", []):
        if dev.get("type") != "disk":
            continue
        if removable_only and not dev.get("rm"):
            continue
        name = dev.get("name") or ""
        if not name:
            continue
        devices.append(
            BlockDevice(
                name=name,
                path=f"/dev/{name}",
                size=(dev.get("size") or "?"),
                model=(dev.get("model") or "").strip() or None,
                removable=bool(dev.get("rm")),
            )
        )
    return devices

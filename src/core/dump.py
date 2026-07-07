"""
Создание и восстановление образов (dd) с повышенными правами (pkexec).
"""
import subprocess
import shutil
from pathlib import Path
from typing import Callable

# Используем pkexec для запроса прав root без запуска всего приложения под sudo
_SUDO_CMD = "pkexec"
_DD_BS = "4M"


def _run_with_privileges(cmd: list[str], progress_callback: Callable[[str], None] | None = None) -> tuple[bool, str]:
    """
    Запуск команды с правами root через pkexec.
    progress_callback(line) вызывается для каждой строки stderr (для dd status=progress).
    Возвращает (успех, сообщение об ошибке или пустая строка).
    """
    try:
        proc = subprocess.Popen(
            [_SUDO_CMD] + cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        err_lines: list[str] = []
        if proc.stderr:
            for line in iter(proc.stderr.readline, ""):
                err_lines.append(line)
                if progress_callback:
                    progress_callback(line.strip())
        proc.wait()
        if proc.returncode != 0:
            return False, "\n".join(err_lines) or f"Код выхода: {proc.returncode}"
        return True, ""
    except FileNotFoundError:
        return False, "Не найден pkexec. Установите policykit-1."
    except Exception as e:
        return False, str(e)


def create_image(
    device_path: str,
    image_path: str | Path,
    progress_callback: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """
    Создать образ устройства: dd if=<device> of=<image_path>.
    device_path: например /dev/sdb
    image_path: полный путь к файлу образа.
    """
    path = Path(image_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Используем dd с status=progress (пишет в stderr)
    cmd = [
        "dd",
        f"if={device_path}",
        f"of={path}",
        f"bs={_DD_BS}",
        "status=progress",
        "conv=fsync",
    ]
    return _run_with_privileges(cmd, progress_callback)


def restore_image(
    image_path: str | Path,
    device_path: str,
    progress_callback: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """
    Восстановить образ на устройство: dd if=<image_path> of=<device>.
    """
    cmd = [
        "dd",
        f"if={Path(image_path)}",
        f"of={device_path}",
        f"bs={_DD_BS}",
        "status=progress",
        "conv=fsync",
    ]
    return _run_with_privileges(cmd, progress_callback)


def get_dd_path() -> str | None:
    """Путь к dd (для отладки)."""
    return shutil.which("dd")

#!/bin/bash
# Сборка AppImage для SD Backup.
# Запуск из корня проекта: ./build_appimage.sh
# Требуется: venv с PyQt6, pyinstaller (установится при сборке), wget/curl, опционально rsvg-convert или ImageMagick для иконки.

set -e
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"
APP_NAME="SD-Backup"
ARCH="${ARCH:-x86_64}"

echo "=== SD Backup: сборка AppImage ==="

# 1) Виртуальное окружение и PyInstaller
if [ ! -d ".venv" ]; then
    echo "Создайте venv и установите зависимости: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi
.venv/bin/pip install -q pyinstaller
echo "PyInstaller установлен."

# 2) Сборка бинарника
.venv/bin/pyinstaller --noconfirm --clean sd-backup.spec
echo "Бинарник собран: dist/sd-backup"

# 3) Иконка: SVG -> PNG (если есть rsvg-convert или convert)
ICON_SVG="$SCRIPT_DIR/appimage/icon.svg"
ICON_PNG="$SCRIPT_DIR/appimage/sd-backup.png"
if [ -f "$ICON_SVG" ]; then
    if command -v rsvg-convert &>/dev/null; then
        rsvg-convert -w 256 -h 256 "$ICON_SVG" -o "$ICON_PNG"
        echo "Иконка создана: $ICON_PNG (rsvg-convert)"
    elif command -v convert &>/dev/null; then
        convert -background none -resize 256x256 "$ICON_SVG" "$ICON_PNG"
        echo "Иконка создана: $ICON_PNG (ImageMagick)"
    else
        echo "Подсказка: установите librsvg2-bin или imagemagick для PNG-иконки в меню."
        ICON_PNG=""
    fi
fi

# 4) AppDir
APPDIR="$SCRIPT_DIR/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
cp "$SCRIPT_DIR/dist/sd-backup" "$APPDIR/usr/bin/sd-backup"
chmod +x "$APPDIR/usr/bin/sd-backup"

cp "$SCRIPT_DIR/appimage/sd-backup.desktop" "$APPDIR/"
cp "$SCRIPT_DIR/appimage/AppRun" "$APPDIR/"
chmod +x "$APPDIR/AppRun"

if [ -n "$ICON_PNG" ] && [ -f "$ICON_PNG" ]; then
    cp "$ICON_PNG" "$APPDIR/sd-backup.png"
fi
# Копируем SVG в AppDir на случай, если окружение умеет показывать SVG-иконки
[ -f "$ICON_SVG" ] && cp "$ICON_SVG" "$APPDIR/sd-backup.svg"

echo "AppDir собран: $APPDIR"

# 5) appimagetool
TOOL="$SCRIPT_DIR/appimagetool-$ARCH.AppImage"
if [ ! -x "$TOOL" ]; then
    echo "Скачивание appimagetool..."
    URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage"
    if command -v wget &>/dev/null; then
        wget -q -O "$TOOL" "$URL"
    else
        curl -sL -o "$TOOL" "$URL"
    fi
    chmod +x "$TOOL"
fi

# 6) Сборка AppImage
OUTPUT="$SCRIPT_DIR/${APP_NAME}-${ARCH}.AppImage"
rm -f "$OUTPUT"
ARCH=$ARCH "$TOOL" --no-appstream "$APPDIR" "$OUTPUT"
echo ""
echo "Готово: $OUTPUT"
echo "Запуск: $OUTPUT"

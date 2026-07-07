#!/bin/bash
# Запуск приложения с использованием Python из venv
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
    echo "Сначала создайте venv: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi
exec .venv/bin/python main.py "$@"

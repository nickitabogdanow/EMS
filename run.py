#!/usr/bin/env python3
"""Запуск из корня проекта: python run.py

Порт: переменная окружения PORT (по умолчанию 8000). Если занят — берётся следующий
свободный (8001, 8002, …), чтобы не было [Errno 48] Address already in use.
"""

import os
import socket
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def pick_port(host: str, start: int, attempts: int = 30) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
            except OSError:
                continue
            return port
    raise SystemExit(
        f"Не найден свободный порт в диапазоне {start}…{start + attempts - 1}. "
        "Освободите порт или задайте PORT=…"
    )


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    start_port = int(os.environ.get("PORT", "8000"))
    port = pick_port(host, start_port)
    if port != start_port:
        print(f"Порт {start_port} занят, использую {port}.", file=sys.stderr)

    print(f"Откройте в браузере: http://{host}:{port}/", file=sys.stderr)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
    )

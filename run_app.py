"""
One-command launch script for the Brigade Harmony Web Application.
Starts pure Python FastAPI/Uvicorn server and automatically opens the browser.
"""

from __future__ import annotations

import sys
import threading
import time
import webbrowser
from pathlib import Path
import uvicorn

PORT = 8000
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}"


def _open_browser_delayed():
    time.sleep(1.2)
    print(f"\n🌐 Открытие браузера: {URL}\n")
    try:
        webbrowser.open(URL)
    except Exception as e:
        print(f"Не удалось открыть браузер автоматически: {e}")


def main():
    print("=" * 60)
    print("🎵 Бригадное Ядро Гармонизации (Способин / Дубовский) — Web GUI")
    print(f"🚀 Запуск микро-сервера: {URL}")
    print("=" * 60)

    # Launch browser opener thread
    threading.Thread(target=_open_browser_delayed, daemon=True).start()

    # Run Uvicorn server
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()

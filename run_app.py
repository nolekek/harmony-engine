"""
One-command launch script for the Brigade Harmony Web Application.
Starts pure Python FastAPI/Uvicorn server and automatically opens the browser.
Supports custom port/host configuration via CLI flags and environment variables,
with pre-flight port binding validation and graceful shutdown handling.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
import webbrowser
import uvicorn

DEFAULT_PORT = 8000
DEFAULT_HOST = "127.0.0.1"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parses command-line arguments and environment variables for server startup."""
    env_port = os.environ.get("PORT")
    env_host = os.environ.get("HOST", DEFAULT_HOST)
    default_port = int(env_port) if env_port and env_port.isdigit() else DEFAULT_PORT

    parser = argparse.ArgumentParser(
        description="Launch Brigade Harmony Classical Voice-Leading Web Application"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"TCP port to listen on (default: {default_port} or env PORT)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=env_host,
        help=f"Host interface to bind to (default: {env_host} or env HOST)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically launch web browser on server start",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    return parser.parse_args(argv)


def check_port_available(host: str, port: int) -> bool:
    """
    Verifies that the target port is free before starting Uvicorn.
    Raises SystemExit with a clear human-readable error message if the port is bound.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
        except OSError as exc:
            print(
                f"❌ Ошибка запуска: Порт {port} на хосте {host} уже занят другим процессом ({exc}).\n"
                f"Пожалуйста, освободите порт {port} или укажите другой порт: python run_app.py --port <новый_порт>",
                file=sys.stderr,
            )
            return False


def _open_browser_delayed(url: str):
    time.sleep(1.2)
    print(f"\n🌐 Открытие браузера: {url}\n")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Не удалось открыть браузер автоматически: {e}")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    host = args.host
    port = args.port
    url = f"http://{host}:{port}"

    if not check_port_available(host, port):
        sys.exit(1)

    print("=" * 60)
    print("🎵 Бригадное Ядро Гармонизации (Способин / Дубовский) — Web GUI")
    print(f"🚀 Запуск микро-сервера: {url}")
    print("=" * 60)

    if not args.no_browser:
        threading.Thread(target=_open_browser_delayed, args=(url,), daemon=True).start()

    # Run Uvicorn server with native graceful shutdown handling
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        log_level="info",
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

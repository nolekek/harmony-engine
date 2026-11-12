"""
Main entry point and lifecycle manager for Harmony Engine Desktop.
Runs FastAPI/Uvicorn in a daemon thread and hosts the React SPA via pywebview (EdgeChromium).
"""

from __future__ import annotations

import ctypes
import json
import logging
import os
from pathlib import Path
import socket
import sys
import threading
import time
import urllib.error
import urllib.request

import uvicorn
import webview

from backend.main import app as fastapi_app
from desktop.instance import acquire_single_instance, cleanup_instance
from desktop.logging_config import get_app_data_dir, setup_desktop_logging

WINDOW_TITLE = "Brigade Harmony Engine"
DEFAULT_WIDTH = 1440
DEFAULT_HEIGHT = 900
MIN_WIDTH = 1100
MIN_HEIGHT = 700

logger = logging.getLogger("desktop.app")


def apply_dpi_awareness() -> None:
    """Sets per-monitor DPI awareness (V2) to prevent blurry rendering on high-DPI displays."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception as exc:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
        logger.debug("DPI awareness initialization note: %s", exc)


def check_webview2_runtime() -> bool:
    """Verifies that Microsoft Edge WebView2 (Chromium) is available."""
    try:
        import webview.platforms.winforms as wf
        return bool(getattr(wf, "is_chromium", False))
    except Exception:
        pass
    # Fallback path check
    edge_wv_path = r"C:\Program Files (x86)\Microsoft\EdgeWebView\Application"
    return os.path.exists(edge_wv_path)


def show_missing_webview2_dialog() -> None:
    """Shows a native Win32 error dialog if WebView2 Evergreen Runtime is missing."""
    msg = (
        "Для работы приложения Harmony Engine Desktop требуется компонент\n"
        "Microsoft Edge WebView2 Runtime.\n\n"
        "Пожалуйста, загрузите и установите его с официального сайта Microsoft:\n"
        "https://developer.microsoft.com/en-us/microsoft-edge/webview2/\n"
    )
    title = "Harmony Engine — Ошибка запуска"
    try:
        ctypes.windll.user32.MessageBoxW(0, msg, title, 0x10 | 0x0)  # MB_ICONERROR | MB_OK
    except Exception:
        print(msg, file=sys.stderr)


def find_free_port() -> int:
    """Allocates a guaranteed available ephemeral TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_health_check(url: str, timeout_sec: float = 6.0) -> bool:
    """Polls /api/health until the FastAPI backend is ready to serve requests."""
    start = time.perf_counter()
    health_url = f"{url}/api/health"
    while time.perf_counter() - start < timeout_sec:
        try:
            with urllib.request.urlopen(health_url, timeout=0.8) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError, TimeoutError):
            time.sleep(0.08)
    return False


def get_window_state_file() -> Path:
    return get_app_data_dir() / "window_state.json"


def load_window_geometry() -> tuple[int, int, int | None, int | None]:
    """Loads saved window dimensions and coordinates if available."""
    f = get_window_state_file()
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            w = max(MIN_WIDTH, int(data.get("width", DEFAULT_WIDTH)))
            h = max(MIN_HEIGHT, int(data.get("height", DEFAULT_HEIGHT)))
            x = data.get("x")
            y = data.get("y")
            return w, h, (int(x) if x is not None else None), (int(y) if y is not None else None)
        except Exception:
            pass
    return DEFAULT_WIDTH, DEFAULT_HEIGHT, None, None


def save_window_geometry(window: webview.Window | None) -> None:
    """Persists current window dimensions and screen coordinates."""
    if window is None:
        return
    try:
        data = {
            "width": getattr(window, "width", DEFAULT_WIDTH),
            "height": getattr(window, "height", DEFAULT_HEIGHT),
            "x": getattr(window, "x", None),
            "y": getattr(window, "y", None),
        }
        get_window_state_file().write_text(json.dumps(data), encoding="utf-8")
    except Exception as exc:
        logger.debug("Could not save window geometry: %s", exc)


def focus_window(window: webview.Window | None) -> None:
    """
    Brings the main desktop window to the foreground using pure Win32 calls.

    Must NOT call pywebview window methods here: this runs on the IPC listener
    thread, and pywebview window APIs are not thread-safe on the WinForms/Edge
    backend (calling them from a foreign thread destroys the window and kills
    the app when a duplicate instance is launched).
    """
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, WINDOW_TITLE)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception as exc:
        logger.debug("Win32 focus failed: %s", exc)


def run_desktop() -> None:
    """Launches the Harmony Engine Desktop application."""
    log_file, logger = setup_desktop_logging()
    logger.info("Initializing Harmony Engine Desktop...")

    apply_dpi_awareness()

    if not check_webview2_runtime():
        logger.error("Microsoft Edge WebView2 Runtime is not installed.")
        show_missing_webview2_dialog()
        sys.exit(1)

    http_port = find_free_port()
    base_url = f"http://127.0.0.1:{http_port}"
    logger.info("Allocated HTTP port: %d (URL: %s)", http_port, base_url)

    # Active window reference for IPC focus callback
    window_ref: list[webview.Window | None] = [None]

    def _focus_cb():
        focus_window(window_ref[0])

    # Enforce single instance
    is_primary = acquire_single_instance(http_port=http_port, focus_callback=_focus_cb)
    if not is_primary:
        logger.info("Exiting duplicate instance process.")
        sys.exit(0)

    # Configure and start Uvicorn in background daemon thread
    uvicorn_config = uvicorn.Config(
        app=fastapi_app,
        host="127.0.0.1",
        port=http_port,
        log_config=None,
        log_level="warning",
    )
    server = uvicorn.Server(uvicorn_config)
    server_thread = threading.Thread(
        target=server.run,
        daemon=True,
        name="UvicornServerThread",
    )
    server_thread.start()

    # Wait for backend readiness
    if not wait_for_health_check(base_url, timeout_sec=6.0):
        logger.error("Backend health-check timed out on %s/api/health", base_url)
        cleanup_instance()
        sys.exit(1)

    logger.info("Backend health-check passed. Creating desktop window...")

    width, height, x, y = load_window_geometry()

    create_kwargs = {
        "title": WINDOW_TITLE,
        "url": base_url,
        "width": width,
        "height": height,
        "min_size": (MIN_WIDTH, MIN_HEIGHT),
        "text_select": True,
    }
    if x is not None and y is not None:
        create_kwargs["x"] = x
        create_kwargs["y"] = y

    window = webview.create_window(**create_kwargs)
    window_ref[0] = window

    def on_closed():
        logger.info("Window closed event received. Shutting down...")
        save_window_geometry(window)
        cleanup_instance()

        # Signal Uvicorn to exit
        server.should_exit = True
        server_thread.join(timeout=3.0)
        if server_thread.is_alive():
            logger.warning("Uvicorn thread did not exit within 3s. Forcing exit.")
            os._exit(0)

    window.events.closed += on_closed

    try:
        # Start pywebview GUI event loop (blocks main thread until window closed)
        webview.start(gui="edgechromium", debug=False)
    finally:
        on_closed()


def main() -> None:
    run_desktop()


if __name__ == "__main__":
    main()

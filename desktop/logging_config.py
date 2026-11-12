"""
Logging configuration for Harmony Engine Desktop.
Manages log directory in %LOCALAPPDATA%\\HarmonyEngine\\logs and configures
rotating file handlers with stdout/stderr redirection for windowed execution.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys


def get_app_data_dir() -> Path:
    """Returns the base data directory in %LOCALAPPDATA%\\HarmonyEngine."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base = Path(local_app_data)
    else:
        base = Path.home() / "AppData" / "Local"
    app_dir = base / "HarmonyEngine"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def setup_desktop_logging() -> tuple[Path, logging.Logger]:
    """
    Initializes rotating file logging in %LOCALAPPDATA%\\HarmonyEngine\\logs\\desktop.log.
    Safely redirects sys.stdout and sys.stderr when running in windowed (console=False) mode.
    """
    app_dir = get_app_data_dir()
    logs_dir = app_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "desktop.log"

    # In PyInstaller windowed mode (console=False), sys.stdout and sys.stderr are None.
    # Unhandled prints would crash with AttributeError. Redirect to desktop.log.
    if sys.stdout is None:
        try:
            sys.stdout = open(log_file, "a", encoding="utf-8", buffering=1)
        except Exception:
            pass
    if sys.stderr is None:
        try:
            sys.stderr = open(log_file, "a", encoding="utf-8", buffering=1)
        except Exception:
            pass

    logger = logging.getLogger("desktop")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers on re-initialization
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        try:
            handler = RotatingFileHandler(
                str(log_file),
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=3,
                encoding="utf-8",
            )
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        except Exception as exc:
            logging.basicConfig(level=logging.INFO)
            logger.warning("Could not set up RotatingFileHandler: %s", exc)

    return log_file, logger

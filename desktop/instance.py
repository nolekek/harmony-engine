"""
Single-instance enforcement and IPC focus mechanism for Harmony Engine Desktop.

Design note (2026-11-12): a Win32 named mutex is NOT a reliable ownership token
here. WebView2 child processes inherit handles; after a force-killed primary the
orphaned children keep the named mutex alive, so the next launch sees
ERROR_ALREADY_EXISTS and exits without ever showing a window. We therefore use an
exclusive byte-range lock on instance.lock instead: Windows releases it when the
owning process dies (even on TerminateProcess) and Python file descriptors are
non-inheritable by default, so WebView2 children never hold it.

The first process owns instance.lock, writes instance.json (pid/http/ipc ports)
and listens on a local TCP socket. A duplicate process fails to acquire the lock,
reads instance.json, sends FOCUS and exits 0.
"""

from __future__ import annotations

import atexit
import json
import logging
import msvcrt
import os
from pathlib import Path
import socket
import sys
import threading
import time
from typing import Callable

from desktop.logging_config import get_app_data_dir

logger = logging.getLogger("desktop.instance")

_LOCK_FILENAME = "instance.lock"

_lock_fd: int | None = None
_ipc_server_socket: socket.socket | None = None
_instance_file: Path | None = None
# Only the process that created instance.json may remove it on exit. A secondary
# instance must never unlink the primary's discovery file (it would break FOCUS
# delivery for every subsequent launch).
_owns_instance_file = False


def get_instance_file_path() -> Path:
    return get_app_data_dir() / "instance.json"


def _get_lock_path() -> Path:
    return get_app_data_dir() / _LOCK_FILENAME


def cleanup_instance() -> None:
    """Removes discovery files and releases the single-instance lock, IPC socket and mutex resources."""
    global _lock_fd, _ipc_server_socket, _instance_file, _owns_instance_file

    if _ipc_server_socket is not None:
        try:
            _ipc_server_socket.close()
        except Exception:
            pass
        _ipc_server_socket = None

    if _owns_instance_file and _instance_file is not None and _instance_file.exists():
        try:
            _instance_file.unlink(missing_ok=True)
        except Exception:
            pass
    _owns_instance_file = False
    _instance_file = None

    if _lock_fd is not None:
        try:
            msvcrt.locking(_lock_fd, msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
        try:
            os.close(_lock_fd)
        except Exception:
            pass
        _lock_fd = None
        lock_path = _get_lock_path()
        try:
            lock_path.unlink(missing_ok=True)
        except Exception:
            pass


# Automatically clean up on interpreter exit
atexit.register(cleanup_instance)


def _ipc_listener_loop(sock: socket.socket, focus_callback: Callable[[], None]) -> None:
    """Daemon thread loop accepting incoming IPC commands from secondary instances."""
    while True:
        try:
            conn, _ = sock.accept()
            with conn:
                conn.settimeout(2.0)
                data = conn.recv(1024)
                if b"FOCUS" in data:
                    try:
                        focus_callback()
                    except Exception as exc:
                        logger.warning("Error running focus callback: %s", exc)
                conn.sendall(b"OK\n")
        except OSError:
            break
        except Exception as exc:
            logger.debug("IPC listener error: %s", exc)


def _acquire_file_lock() -> int | None:
    """Tries to take the exclusive single-instance lock. Returns the fd or None."""
    lock_path = _get_lock_path()
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    except OSError:
        os.close(fd)
        return None
    return fd


def acquire_single_instance(
    http_port: int,
    focus_callback: Callable[[], None],
) -> bool:
    """
    Attempts to acquire the single-instance file lock.
    If another instance is already running:
        Sends FOCUS to the running instance via local IPC socket and returns False.
    If this is the primary instance:
        Starts IPC listener, records instance.json, and returns True.
    """
    global _lock_fd, _ipc_server_socket, _instance_file, _owns_instance_file

    _instance_file = get_instance_file_path()

    fd = _acquire_file_lock()
    if fd is None:
        logger.info("Secondary instance detected (lock held). Signaling primary instance to focus.")
        notify_existing_instance()
        # Only a real duplicate process (which does not own the file) drops the
        # reference; a same-process probe must not clobber the primary state.
        if not _owns_instance_file:
            _instance_file = None
        return False

    _lock_fd = fd

    # We are the primary instance. Setup IPC server socket.
    try:
        _ipc_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _ipc_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _ipc_server_socket.bind(("127.0.0.1", 0))
        _ipc_server_socket.listen(5)
        ipc_port = _ipc_server_socket.getsockname()[1]

        # Write the discovery file atomically so a waiting secondary never reads half a file.
        instance_data = {
            "pid": os.getpid(),
            "http_port": http_port,
            "ipc_port": ipc_port,
        }
        tmp_path = _instance_file.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(instance_data), encoding="utf-8")
        os.replace(tmp_path, _instance_file)
        _owns_instance_file = True

        t = threading.Thread(
            target=_ipc_listener_loop,
            args=(_ipc_server_socket, focus_callback),
            daemon=True,
            name="IPC-Listener",
        )
        t.start()
        return True
    except Exception as exc:
        logger.error("Failed to initialize primary instance IPC: %s", exc)
        # We still own the lock; the window will open without cross-instance focus.
        return True


def notify_existing_instance() -> None:
    """Connects to the primary instance's IPC port and sends FOCUS command."""
    instance_file = get_instance_file_path()

    data: dict | None = None
    for _ in range(5):
        if instance_file.exists():
            try:
                data = json.loads(instance_file.read_text(encoding="utf-8"))
                break
            except Exception:
                pass
        time.sleep(0.1)

    if not data:
        return

    try:
        ipc_port = int(data.get("ipc_port", 0))
        if ipc_port <= 0:
            return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.5)
            s.connect(("127.0.0.1", ipc_port))
            s.sendall(b"FOCUS\n")
            try:
                s.recv(16)
            except Exception:
                pass
    except Exception:
        # Never raise or show tracebacks on duplicate exit
        pass


# Backwards-compatible alias: older call sites/imports referenced this name.
def get_app_data_directory() -> Path:  # pragma: no cover - trivial alias
    return get_app_data_dir()

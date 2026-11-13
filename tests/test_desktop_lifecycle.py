"""
Unit tests for Harmony Engine Desktop lifecycle, port picking, IPC, and graceful shutdown.
Executed entirely without opening physical Win32 GUI windows.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time

import uvicorn
from fastapi import FastAPI

from backend.main import resolve_frontend_dist
from desktop.app import find_free_port, wait_for_health_check
import desktop.instance as instance_mod


def test_ephemeral_port_allocation():
    """Verifies that find_free_port returns a valid, open TCP port on localhost."""
    port1 = find_free_port()
    port2 = find_free_port()
    assert port1 > 1024
    assert port2 > 1024

    # Verify that the returned port can immediately be bound
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", port1))
        assert sock.getsockname()[1] == port1


def test_health_check_waiter_success_and_timeout():
    """Tests wait_for_health_check on a mock HTTP server and on an unused port."""
    # 1. Unused port -> must return False after timeout
    unused_port = find_free_port()
    assert wait_for_health_check(f"http://127.0.0.1:{unused_port}", timeout_sec=0.2) is False

    # 2. Live test server -> must return True quickly
    app = FastAPI()

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    free_port = find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=free_port, log_config=None, log_level="error")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()

    try:
        ok = wait_for_health_check(f"http://127.0.0.1:{free_port}", timeout_sec=3.0)
        assert ok is True
    finally:
        server.should_exit = True
        t.join(timeout=3.0)


def test_uvicorn_graceful_shutdown():
    """Verifies that Uvicorn stops cleanly within timeout when should_exit is set to True."""
    app = FastAPI()
    free_port = find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=free_port, log_config=None, log_level="error")
    server = uvicorn.Server(config)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    time.sleep(0.3)
    assert server_thread.is_alive() is True

    # Trigger graceful shutdown
    server.should_exit = True
    server_thread.join(timeout=3.0)
    assert server_thread.is_alive() is False


def test_single_instance_ipc_signaling(tmp_path, monkeypatch):
    """
    Simulates primary and secondary instance interaction:
    Primary acquires mutex and starts IPC listener; secondary detects primary and sends FOCUS.
    """
    monkeypatch.setattr(instance_mod, "get_app_data_dir", lambda: tmp_path)

    focus_called = threading.Event()

    def _on_focus():
        focus_called.set()

    # Clean any prior state
    instance_mod.cleanup_instance()

    # 1. Primary instance acquisition
    is_primary = instance_mod.acquire_single_instance(http_port=8080, focus_callback=_on_focus)
    assert is_primary is True

    instance_file = tmp_path / "instance.json"
    assert instance_file.exists()

    # 2. Simulate secondary instance notification
    # When notify_existing_instance is called, it reads instance.json and sends b"FOCUS"
    instance_mod.notify_existing_instance()

    # Wait for listener to invoke callback
    assert focus_called.wait(timeout=2.0) is True

    # 3. Cleanup releases everything cleanly
    instance_mod.cleanup_instance()
    assert not instance_file.exists()


def test_secondary_instance_does_not_delete_primary_discovery_file(tmp_path, monkeypatch):
    """
    Regression: a secondary instance exiting must NOT unlink the primary's instance.json.
    Previously atexit cleanup in the duplicate process removed the file, breaking FOCUS
    delivery for every subsequent launch.
    """
    monkeypatch.setattr(instance_mod, "get_app_data_dir", lambda: tmp_path)
    instance_mod.cleanup_instance()

    focus_called = threading.Event()
    assert instance_mod.acquire_single_instance(http_port=8081, focus_callback=focus_called.set) is True
    instance_file = tmp_path / "instance.json"
    assert instance_file.exists()
    primary_owner_pid = os.getpid()

    # Same-process second acquisition sees the existing mutex -> acts as secondary.
    assert instance_mod.acquire_single_instance(http_port=8082, focus_callback=focus_called.set) is False
    assert instance_file.exists(), "secondary instance must not delete the primary discovery file"
    data = json.loads(instance_file.read_text(encoding="utf-8"))
    assert data["pid"] == primary_owner_pid
    assert data["http_port"] == 8081

    instance_mod.cleanup_instance()
    assert not instance_file.exists()


def test_lock_released_after_cleanup_and_stale_discovery_overwritten(tmp_path, monkeypatch):
    """
    After a hard kill (OS releases the lock) a new launch must become primary even if a
    stale instance.json from the dead process still exists.
    """
    monkeypatch.setattr(instance_mod, "get_app_data_dir", lambda: tmp_path)
    instance_mod.cleanup_instance()

    stale = tmp_path / "instance.json"
    stale.write_text(json.dumps({"pid": 999999, "http_port": 1234, "ipc_port": 1235}), encoding="utf-8")

    assert instance_mod.acquire_single_instance(http_port=8085, focus_callback=lambda: None) is True
    data = json.loads(stale.read_text(encoding="utf-8"))
    assert data["pid"] == os.getpid(), "primary must overwrite a stale discovery file"
    assert data["http_port"] == 8085

    instance_mod.cleanup_instance()

    # Lock must be free again after cleanup (simulates graceful exit).
    assert instance_mod.acquire_single_instance(http_port=8086, focus_callback=lambda: None) is True
    instance_mod.cleanup_instance()


def test_resolve_frontend_dist(tmp_path, monkeypatch):
    """Tests robust resolution order for frontend/dist."""
    # 1. Environment variable override
    fake_dist = tmp_path / "custom_dist"
    fake_dist.mkdir()
    monkeypatch.setenv("FRONTEND_DIST_DIR", str(fake_dist))
    resolved = resolve_frontend_dist()
    assert resolved == fake_dist

    # 2. PyInstaller _MEIPASS override
    monkeypatch.delenv("FRONTEND_DIST_DIR", raising=False)
    fake_meipass = tmp_path / "bundle"
    (fake_meipass / "frontend" / "dist").mkdir(parents=True)
    monkeypatch.setattr(sys, "_MEIPASS", str(fake_meipass), raising=False)
    resolved_mei = resolve_frontend_dist()
    assert resolved_mei == (fake_meipass / "frontend" / "dist")

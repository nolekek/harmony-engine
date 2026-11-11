"""
Tests for API error handling, SPA 404 routing, health checks, and 500 handler.
"""

import uuid
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_api_health_ok():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert "application/json" in res.headers["content-type"]
    assert res.json()["status"] == "ok"


def test_unknown_api_get_route_returns_404_json():
    res = client.get("/api/unknown_route_123")
    assert res.status_code == 404
    assert "application/json" in res.headers["content-type"]
    data = res.json()
    assert "detail" in data
    # Must NOT be an HTML page!
    assert not res.text.strip().startswith("<!DOCTYPE")
    assert not res.text.strip().startswith("<html")


def test_unknown_api_post_route_returns_404_json():
    res = client.post("/api/nested/unknown/route", json={"foo": "bar"})
    assert res.status_code == 404
    assert "application/json" in res.headers["content-type"]
    data = res.json()
    assert "detail" in data


def test_unhandled_exception_returns_500_with_uuid():
    # Patch a service or router call to raise an unexpected runtime error
    with patch("backend.service.HarmonizationService.harmonize", side_effect=RuntimeError("Simulated server crash")):
        res = client.post("/api/harmonize", json={
            "melody": [{"pitch": 60, "duration": "half"}],
            "key": {"tonic": "C", "mode": "Major"},
        })
        assert res.status_code == 500
        assert "application/json" in res.headers["content-type"]
        data = res.json()
        assert data.get("detail") == "Internal Server Error"
        assert "error_id" in data
        # Validate that error_id is a valid UUID
        parsed_uuid = uuid.UUID(data["error_id"])
        assert str(parsed_uuid) == data["error_id"]


def test_run_app_arg_parsing(monkeypatch):
    import run_app

    # Test default
    monkeypatch.delenv("PORT", raising=False)
    args = run_app.parse_args([])
    assert args.port == 8000
    assert args.host == "127.0.0.1"

    # Test CLI flag override
    args_cli = run_app.parse_args(["--port", "9000", "--host", "0.0.0.0"])
    assert args_cli.port == 9000
    assert args_cli.host == "0.0.0.0"

    # Test env var fallback
    monkeypatch.setenv("PORT", "7777")
    args_env = run_app.parse_args([])
    assert args_env.port == 7777


def test_run_app_port_collision_check():
    import socket
    import run_app

    # Bind a socket on a free ephemeral port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
        test_sock.bind(("127.0.0.1", 0))
        _, bound_port = test_sock.getsockname()

        # check_port_available should detect collision and return False
        is_free = run_app.check_port_available("127.0.0.1", bound_port)
        assert is_free is False


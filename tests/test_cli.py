"""
Unit tests for the CLI interface.
"""

from pathlib import Path
import tempfile
import pytest
from src.harmony.cli import parse_melody, main


def test_parse_melody_valid():
    m = parse_melody("64, 65, 67, 62, 60")
    assert len(m) == 5
    assert m[0]["pitch"] == 64
    assert m[0]["is_downbeat"] is True
    assert m[1]["pitch"] == 65
    assert m[1]["is_downbeat"] is False


def test_parse_melody_empty():
    with pytest.raises(ValueError):
        parse_melody("")


def test_cli_execution_with_export(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        xml_path = str(Path(tmpdir) / "test.musicxml")
        mid_path = str(Path(tmpdir) / "test.mid")

        exit_code = main([
            "--melody", "64,65,67,62,60",
            "--tonic", "C",
            "--mode", "Major",
            "--musicxml", xml_path,
            "--midi", mid_path,
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "SATB HARMONY SCORE" in captured.out
        assert Path(xml_path).exists()
        assert Path(mid_path).exists()


def test_cli_execution_with_max_plans(capsys):
    exit_code = main([
        "--melody", "64,65,67,64,62,60",
        "--tonic", "C",
        "--mode", "Major",
        "--max-plans", "60",
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "SATB HARMONY SCORE" in captured.out


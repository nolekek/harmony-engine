# -*- coding: utf-8 -*-
"""Lead verification harness for P2 wave (packaging, replanning, export, frontend).

Run: python .redteam/scratch/lead/verify_p2.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import tomllib
from pathlib import Path

import yaml

sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Key, Voicing  # noqa: E402
from src.harmony.export.midi import export_to_midi  # noqa: E402
from src.harmony.export.musicxml import export_to_musicxml  # noqa: E402
from src.harmony.pipeline import Harmonizer  # noqa: E402

ROOT = Path(r"D:\aitraining")
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'} | {name}" + (f" | {detail}" if detail else ""))


def guard(name: str, fn) -> None:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"EXCEPTION: {exc.__class__.__name__}: {exc}")


# ---------------------------------------------------------------- T22
def t22_deps() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = data.get("project", {}).get("dependencies", [])
    dev = data.get("project", {}).get("optional-dependencies", {}).get("dev", [])
    flat = " ".join(deps + dev).lower()
    needed = ["fastapi", "uvicorn", "pydantic", "pytest", "httpx"]
    missing = [n for n in needed if n not in flat]
    check("T22 pyproject dependencies", not missing, f"missing={missing}")


def t22_ci() -> None:
    p = ROOT / ".github" / "workflows" / "ci.yml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    text = p.read_text(encoding="utf-8")
    ok = bool(data.get("jobs")) and "pytest" in text and "npm run build" in text
    check("T22 CI workflow", ok, f"jobs={list(data.get('jobs', {}).keys())}")


def t22_readme() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    lies = [s for s in ("Bi-GRU", "127 тест", "0 косяков", "<10 ms", "< 10 ms") if s in text]
    check("T22 README without marketing lies", not lies, f"found={lies}")


def t22_ml_honest() -> None:
    text = (ROOT / "src" / "harmony" / "ml" / "model.py").read_text(encoding="utf-8")
    ok = ("n-gram" in text.lower()) and ("bi-gru" not in text.lower()) and (
        "neural network" in text.lower() or "not a neural" in text.lower()
    )
    check("T22 ML module honest docstring", ok, "")


# ---------------------------------------------------------------- T24
def t24_replanning() -> None:
    h = Harmonizer()
    for label, mel in (("A minor asc", [69, 71, 72, 74, 76, 77, 80, 81]),
                       ("A minor desc", [81, 80, 77, 76, 74, 72, 71, 69])):
        r = h.harmonize(mel, key="A MinorHarmonic", allow_replanning=True)
        check(f"T24 replanning [{label}]", r.is_success, f"msg={r.message[:70]}")
    r_off = h.harmonize([81, 80, 77, 76, 74, 72, 71, 69], key="A MinorHarmonic", allow_replanning=False)
    check("T24 explicit opt-out still refuses", not r_off.is_success, f"msg={r_off.message[:70]}")
    a = h.harmonize([69, 71, 72, 74, 76, 77, 80, 81], key="A MinorHarmonic")
    b = h.harmonize([69, 71, 72, 74, 76, 77, 80, 81], key="A MinorHarmonic")
    ok = a.is_success == b.is_success and [
        c.function for c in (a.best_solution.chords if a.best_solution else [])
    ] == [c.function for c in (b.best_solution.chords if b.best_solution else [])]
    check("T24 determinism", ok, "")


def t23_matrix_files() -> None:
    files = ["tests/test_scale_matrix.py", "tests/test_property_invariants.py", "tests/test_replanning.py"]
    missing = [f for f in files if not (ROOT / f).exists()]
    check("T23 matrix/property tests exist", not missing, f"missing={missing}")


# ---------------------------------------------------------------- T25
def t25_musicxml_flats() -> None:
    import xml.etree.ElementTree as ET

    xml = export_to_musicxml(
        voicings=[(70, 65, 58, 46)],  # Bb4 F4 Bb3 Bb2
        chords=["S"],
        key=Key(tonic="F", mode="Major"),
        durations=["whole"],
        time_signature="4/4",
    )
    root = ET.fromstring(xml)
    pitches = []
    for p in root.iter("pitch"):
        step = (p.findtext("step") or "").strip()
        alter = (p.findtext("alter") or "0").strip()
        pitches.append((step, int(float(alter))))
    ok_flat = ("B", -1) in pitches
    no_a_sharp = ("A", 1) not in pitches
    check("T25 MusicXML flats in F-dur", ok_flat and no_a_sharp,
          f"pitches={pitches[:6]} flat={ok_flat} no_a_sharp={no_a_sharp}")


def t25_midi_format() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = export_to_midi(
            voicings=[(64, 60, 55, 48), (62, 59, 55, 43)],
            output_path=os.path.join(td, "test.mid"),
            bpm=80,
            durations=["half", "half"],
            time_signature="4/4",
        )
        data = Path(path).read_bytes()
    ok_header = data[:4] == b"MThd"
    fmt = int.from_bytes(data[8:10], "big")
    ntrks = int.from_bytes(data[10:12], "big")
    has_choir = any(bytes([0xC0 + ch, 52]) in data for ch in range(4))
    check("T25 MIDI format 1 / 4 tracks / Choir Aahs",
          ok_header and fmt == 1 and ntrks == 4 and has_choir,
          f"fmt={fmt} ntrks={ntrks} choir={has_choir}")


def t25_bundle_split() -> None:
    assets = ROOT / "frontend" / "dist" / "assets"
    files = list(assets.glob("*.js")) if assets.exists() else []
    main = [f for f in files if f.name.startswith("index-")]
    osmd = [f for f in files if f.name.startswith("osmd-")]
    main_kb = main[0].stat().st_size // 1024 if main else -1
    osmd_kb = osmd[0].stat().st_size // 1024 if osmd else -1
    ok = bool(main) and bool(osmd) and main_kb < 800 and osmd_kb > 500
    check("T25 bundle split (OSMD lazy chunk)", ok, f"index={main_kb}KB osmd={osmd_kb}KB")
    check("T25 dead App.css removed", not (ROOT / "frontend" / "src" / "App.css").exists(), "")


CHECKS = [
    ("T22 pyproject dependencies", t22_deps),
    ("T22 CI workflow", t22_ci),
    ("T22 README without marketing lies", t22_readme),
    ("T22 ML module honest docstring", t22_ml_honest),
    ("T24 replanning", t24_replanning),
    ("T23 matrix/property tests exist", t23_matrix_files),
    ("T25 MusicXML flats", t25_musicxml_flats),
    ("T25 MIDI format 1", t25_midi_format),
    ("T25 bundle split", t25_bundle_split),
]


def main() -> int:
    for name, fn in CHECKS:
        guard(name, fn)
    failed = [r for r in RESULTS if not r[1]]
    print("\n=== SUMMARY ===")
    print(f"P2: {len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    if failed:
        print("FAILED:")
        for n, _, d in failed:
            print(f"  - {n}: {d}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

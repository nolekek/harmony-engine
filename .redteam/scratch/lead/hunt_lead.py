# -*- coding: utf-8 -*-
"""Lead adversarial hunt: independent fuzz of the harmonizer.

Checks invariants on every successful solution and hunts crashes on edge inputs.
Run: python .redteam/scratch/lead/hunt_lead.py
"""
from __future__ import annotations

import json
import random
import sys
import time

sys.path.insert(0, r"D:\aitraining")

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402
from src.harmony.core.types import to_satb  # noqa: E402
from src.harmony.rules.doubling import get_triad_tones  # noqa: E402

client = TestClient(app)
TONICS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MODES = ["Major", "MinorHarmonic"]
METERS = ["4/4", "3/4", "2/4", "6/8"]
PROBLEMS: list[dict] = []


def report(kind: str, detail: str, **kw) -> None:
    PROBLEMS.append({"kind": kind, "detail": detail, **kw})


def harmonize(melody, tonic="C", mode="Major", ts="4/4", **extra):
    body = {
        "melody": melody,
        "key": {"tonic": tonic, "mode": mode},
        "time_signature": ts,
        **extra,
    }
    t0 = time.perf_counter()
    r = client.post("/api/harmonize", json=body)
    dt = (time.perf_counter() - t0) * 1000
    return r, dt


SEVENTH_SYMS = {"D7", "D65", "D43", "D2", "II7", "II65", "II43", "II2", "VII7", "VII65",
                "VII43", "VII2", "DD7", "DD65", "DD43", "DD2"}


def check_solution(cand: dict, tonic: str, mode: str, label: str) -> None:
    chords = cand.get("chords") or []
    vos = cand.get("voicings") or []
    tonic_pc = {
        "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
        "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11,
    }[tonic]
    engine_mode = "Minor" if "Minor" in mode else "Major"
    n = len(vos)
    if cand.get("cost", 0) < 0:
        report("negative_cost", f"{label}: cost={cand['cost']}")
    for i, v in enumerate(vos):
        s, a, t, b = v["soprano"], v["alto"], v["tenor"], v["bass"]
        sym = chords[i] if i < len(chords) else "?"
        if not (s > a > t > b):
            report("voice_order", f"{label}: [{i} {sym}] S={s} A={a} T={t} B={b}", label=label)
        if sym.upper() == "K64" and (i == 0 or i == n - 1):
            report("k64_position", f"{label}: K64 at {i}", label=label)
        try:
            root, third, fifth = get_triad_tones(sym, tonic_pc, engine_mode)
        except Exception:  # noqa: BLE001
            continue
        pcs = {x % 12 for x in (s, a, t, b)}
        is_seventh = sym.upper() in SEVENTH_SYMS
        if third not in pcs:
            report("third_missing", f"{label}: [{i} {sym}] pcs={sorted(pcs)}", label=label)
        # fifth: omitted in first inversions and incomplete final tonics (canon)
        first_inv = sym.upper().endswith("6") and not sym.upper().endswith("64")
        final_incomplete = i == n - 1 and len(pcs) == 3 and third in pcs
        if fifth not in pcs and not first_inv and not is_seventh and not final_incomplete:
            report("fifth_missing", f"{label}: [{i} {sym}] pcs={sorted(pcs)}", label=label)
        # parallel fifths/octaves between all pairs
        if i > 0:
            prev = vos[i - 1]
            for v1, v2 in (("soprano", "alto"), ("soprano", "tenor"), ("soprano", "bass"),
                           ("alto", "tenor"), ("alto", "bass"), ("tenor", "bass")):
                p1, c1 = prev[v1], v[v1]
                p2, c2 = prev[v2], v[v2]
                d1, d2 = c1 - p1, c2 - p2
                if d1 == 0 or d2 == 0:
                    continue
                if d1 * d2 <= 0:
                    continue
                ip, ic = abs(p1 - p2) % 12, abs(c1 - c2) % 12
                if ip == 7 and ic == 7:
                    report("parallel_fifth", f"{label}: [{i-1}->{i}] {v1}/{v2} {p1},{p2}->{c1},{c2}", label=label)
                if ip == 0 and ic == 0:
                    report("parallel_octave", f"{label}: [{i-1}->{i}] {v1}/{v2} {p1},{p2}->{c1},{c2}", label=label)


def fuzz() -> None:
    random.seed(2026)
    scale = [0, 2, 4, 5, 7, 9, 11]
    solved = 0
    total = 0
    for tonic in TONICS:
        tpc = {
            "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
            "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11,
        }[tonic]
        for mode in MODES:
            for ts in METERS:
                for length in (2, 4, 6, 8):
                    total += 1
                    kind = random.choice(["diath", "diath", "chroma", "repeat"])
                    if kind == "chroma":
                        pcs = [random.randint(0, 11) for _ in range(length)]
                    else:
                        pcs = [scale[random.randrange(7)] for _ in range(length)]
                    pcs[-1] = 0
                    pitches = [60 + ((tpc + pc) % 12) for pc in pcs]
                    notes = [{"pitch": p, "duration": "half"} for p in pitches]
                    label = f"{tonic} {mode} {ts} len{length} {kind} {pitches}"
                    try:
                        r, dt = harmonize(notes, tonic, mode, ts)
                    except Exception as exc:  # noqa: BLE001
                        report("crash", f"{label}: {exc.__class__.__name__}: {exc}", label=label)
                        continue
                    if r.status_code != 200:
                        report("http_error", f"{label}: status={r.status_code} body={r.text[:200]}", label=label)
                        continue
                    data = r.json()
                    if data.get("is_success"):
                        solved += 1
                        for cand in data.get("candidates") or []:
                            check_solution(cand, tonic, mode, label)
                    else:
                        err = data.get("error") or {}
                        if err.get("code") not in ("NO_PLANS", "NO_FEASIBLE_PLAN", "SECONDARY_DOMINANTS_DISABLED"):
                            report("bad_error_code", f"{label}: error={err}", label=label)
                    if dt > 15000:
                        report("slow", f"{label}: {dt:.0f} ms", label=label)


def edge_cases() -> None:
    cases = [
        ("empty", [], "C", "Major", "4/4"),
        ("one_note", [{"pitch": 60, "duration": "whole"}], "C", "Major", "4/4"),
        ("two_notes", [{"pitch": 60, "duration": "half"}, {"pitch": 62, "duration": "half"}], "C", "Major", "4/4"),
        ("pitch_0", [{"pitch": 0, "duration": "half"}, {"pitch": 60, "duration": "half"}], "C", "Major", "4/4"),
        ("pitch_127", [{"pitch": 127, "duration": "half"}, {"pitch": 60, "duration": "half"}], "C", "Major", "4/4"),
        ("weird_meter", [{"pitch": 60, "duration": "half"}, {"pitch": 62, "duration": "half"}], "C", "Major", "7/8"),
        ("weird_duration", [{"pitch": 60, "duration": "banana"}, {"pitch": 62, "duration": "half"}], "C", "Major", "4/4"),
        ("whole_in_3_8", [{"pitch": 60, "duration": "whole"}, {"pitch": 62, "duration": "whole"}], "C", "Major", "3/8"),
        ("all_downbeats", [{"pitch": p, "duration": "half", "is_downbeat": True} for p in (60, 62, 64, 65)], "C", "Major", "4/4"),
    ]
    for name, notes, tonic, mode, ts in cases:
        try:
            r, dt = harmonize(notes, tonic, mode, ts)
            status = r.status_code
            body = r.text[:160].replace("\n", " ")
        except Exception as exc:  # noqa: BLE001
            report("edge_crash", f"{name}: {exc}", label=name)
            continue
        if status >= 500:
            report("edge_500", f"{name}: status={status} {body}", label=name)
        print(f"EDGE {name}: status={status} {dt:.0f}ms {body[:80]}")


def long_melody() -> None:
    notes = [{"pitch": 60 + (i % 12), "duration": "quarter"} for i in range(64)]
    r, dt = harmonize(notes, "C", "Major", "4/4", max_plans=100)
    print(f"LONG 64 notes: status={r.status_code} {dt:.0f}ms success={r.json().get('is_success')}")
    if r.status_code >= 500:
        report("long_500", f"64 notes: {r.status_code} {r.text[:200]}")


def determinism() -> None:
    notes = [{"pitch": p, "duration": "half"} for p in (64, 65, 67, 64, 62, 60)]
    a, _ = harmonize(notes)
    b, _ = harmonize(notes)
    ca = [c["chords"] for c in a.json().get("candidates") or []]
    cb = [c["chords"] for c in b.json().get("candidates") or []]
    if ca != cb:
        report("nondeterministic", f"{ca} != {cb}")


def main() -> int:
    t0 = time.perf_counter()
    fuzz()
    edge_cases()
    long_melody()
    determinism()
    print(f"\nTotal time: {time.perf_counter() - t0:.1f}s")
    print(f"PROBLEMS: {len(PROBLEMS)}")
    for p in PROBLEMS[:40]:
        print(f"  [{p['kind']}] {p['detail']}")
    if PROBLEMS:
        with open(r"D:\aitraining\.redteam\scratch\lead\hunt_lead_findings.json", "w", encoding="utf-8") as fh:
            json.dump(PROBLEMS, fh, ensure_ascii=False, indent=2)
    return 0 if not PROBLEMS else 1


if __name__ == "__main__":
    sys.exit(main())

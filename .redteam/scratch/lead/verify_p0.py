# -*- coding: utf-8 -*-
"""Lead verification harness for P0 wave (redteam-p0 branch).

Run:
    python .redteam/scratch/lead/verify_p0.py --wave 1
    python .redteam/scratch/lead/verify_p0.py --wave 2
    python .redteam/scratch/lead/verify_p0.py --wave all

Exit code 0 => all checks of the requested wave passed.
"""
from __future__ import annotations

import argparse
import sys
import traceback
import xml.etree.ElementTree as ET

sys.path.insert(0, r"D:\aitraining")

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402
from src.harmony.core.types import (  # noqa: E402
    Key,
    Chord,
    Voicing,
    to_satb,
    parse_chord_symbol,
)
from src.harmony.core.chord import ChordDefinition  # noqa: E402
from src.harmony.rules.engine import RuleEngine  # noqa: E402
from src.harmony.solver.state_generator import generate_candidate_voicings  # noqa: E402
from src.harmony.pipeline import Harmonizer  # noqa: E402

client = TestClient(app)
KEY = Key(tonic="C", mode="Major")
TONIC_PC = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
    "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}

RESULTS: list[tuple[str, str, bool, str]] = []


def check(wave: str, name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((wave, name, bool(ok), detail))
    tag = "PASS" if ok else "FAIL"
    print(f"{tag} [{wave}] {name}" + (f" | {detail}" if detail else ""))


def guard(wave: str, name: str, fn) -> None:
    try:
        fn(wave, name)
    except Exception as exc:  # noqa: BLE001
        check(wave, name, False, f"EXCEPTION: {exc.__class__.__name__}: {exc}")


def melody(pitches, durations=None, downbeats=None):
    n = len(pitches)
    durs = durations or ["half"] * n
    db = list(downbeats or []) + [False] * max(0, n - len(downbeats or []))
    return [{"pitch": p, "duration": d, "is_downbeat": bool(b)} for p, d, b in zip(pitches, durs, db)]


def harmonize(notes, tonic="C", mode="Major", ts="4/4", max_plans=50, sec=True, ext=False):
    return client.post("/api/harmonize", json={
        "melody": notes,
        "key": {"tonic": tonic, "mode": mode},
        "time_signature": ts,
        "allow_extended_ranges": ext,
        "allow_secondary_dominants": sec,
        "max_plans": max_plans,
    })


def triads(sym: str):
    from src.harmony.rules.doubling import get_triad_tones
    return get_triad_tones(sym, TONIC_PC["C"], "Major")


# ---------------------------------------------------------------- W1: T1
def w1_t1_generation(wave: str, name: str) -> None:
    vs = generate_candidate_voicings(64, Chord(function="T", is_seventh=False), KEY)
    issues = []
    for v in vs:
        s, a, t, b = to_satb(v)
        if not (s > a > t > b):
            issues.append(f"order/union {(s, a, t, b)}")
        pcs = {x % 12 for x in (s, a, t, b)}
        if 4 not in pcs:
            issues.append(f"no third {(s, a, t, b)}")
        if 7 not in pcs:
            issues.append(f"no fifth {(s, a, t, b)}")
    check(wave, name, len(vs) > 0 and not issues,
          f"{len(vs)} voicings; issues={issues[:5]}")


def w1_t1_unison(wave: str, name: str) -> None:
    r = RuleEngine().validate_voicing(Voicing(soprano=64, alto=60, tenor=48, bass=48),
                                      chord=Chord(function="T"), key=KEY)
    ids = [v.rule_id for v in r.violations]
    check(wave, name, (not r.is_valid) or ("VOICE_UNISON" in ids), f"valid={r.is_valid} ids={ids}")


def w1_t1_third(wave: str, name: str) -> None:
    r = RuleEngine().validate_voicing(Voicing(soprano=60, alto=60, tenor=55, bass=48),
                                      chord=Chord(function="T"), key=KEY)
    ids = [v.rule_id for v in r.violations]
    check(wave, name, (not r.is_valid) or any(i in ids for i in ("CHORD_THIRD_MISSING", "VOICE_UNISON")),
          f"valid={r.is_valid} ids={ids}")


# ---------------------------------------------------------------- W1: T2
def _bass_pcs(sym: str, soprano: int = 74):
    vs = generate_candidate_voicings(soprano, Chord(function=sym), KEY)
    return sorted({to_satb(v)[3] % 12 for v in vs}), len(vs)


def _t2_case(wave: str, name: str, sym: str, want: set[int], soprano: int = 74) -> None:
    pcs, n = _bass_pcs(sym, soprano)
    check(wave, name, pcs == sorted(want), f"{sym}: n={n} bass_pcs={pcs} want={sorted(want)}")


def w1_t2(wave: str, name: str) -> None:
    # Soprano must leave room for root+third+seventh: use G4 (root of D7) for
    # D43/D2 and F4 (third of II7) for II43/II2.
    _t2_case(wave, name + " [D43]", "D43", {2}, soprano=67)
    _t2_case(wave, name + " [D2]", "D2", {5}, soprano=67)
    _t2_case(wave, name + " [II43]", "II43", {9}, soprano=65)
    _t2_case(wave, name + " [II2]", "II2", {0}, soprano=65)


# ---------------------------------------------------------------- W1: T3
def w1_t3_parse(wave: str, name: str) -> None:
    cd = ChordDefinition.from_string("T", KEY)
    sym = parse_chord_symbol(cd)
    check(wave, name, sym == "T", f"parse_chord_symbol -> {sym!r}")


def w1_t3_parity(wave: str, name: str) -> None:
    bad = Voicing(soprano=60, alto=60, tenor=55, bass=48)
    r1 = RuleEngine().validate_voicing(bad, chord=Chord(function="T"), key=KEY)
    r2 = RuleEngine().validate_voicing(bad, chord=ChordDefinition.from_string("T", KEY), key=KEY)
    ids1 = sorted(v.rule_id for v in r1.violations)
    ids2 = sorted(v.rule_id for v in r2.violations)
    check(wave, name, ids1 == ids2 and bool(ids1), f"Chord ids={ids1} ChordDefinition ids={ids2}")


# ---------------------------------------------------------------- W1: API
def w1_cors(wave: str, name: str) -> None:
    r = client.get("/api/health", headers={"Origin": "http://evil.com"})
    acao = r.headers.get("access-control-allow-origin", "")
    check(wave, name, acao != "http://evil.com", f"status={r.status_code} acao={acao!r}")


def w1_validation(wave: str, name: str) -> None:
    cases = [
        ("bad key", {"melody": melody([60]), "key": {"tonic": "Z#", "mode": "AlienMode"}}),
        ("max_plans=0", {"melody": melody([60]), "max_plans": 0}),
        ("max_plans=-10", {"melody": melody([60]), "max_plans": -10}),
        ("pitch=300", {"melody": melody([300])}),
        ("1000 notes", {"melody": melody([60] * 1000)}),
    ]
    bad = []
    for label, body in cases:
        r = client.post("/api/harmonize", json=body)
        if r.status_code != 422:
            bad.append(f"{label}->{r.status_code}")
    check(wave, name, not bad, f"non-422: {bad}")


def w1_secondary(wave: str, name: str) -> None:
    r = harmonize(melody([64, 66, 67, 64, 62, 60]), sec=False)
    data = r.json()
    check(wave, name, data.get("is_success") is False and not data.get("candidates"),
          f"status={r.status_code} is_success={data.get('is_success')} msg={str(data.get('message'))[:80]}")


def w1_parity(wave: str, name: str) -> None:
    notes = melody([60, 64, 67, 72], downbeats=[True, False, True, False])
    api = harmonize(notes, max_plans=50).json()
    core = Harmonizer().harmonize(
        [{"pitch": n["pitch"], "is_downbeat": n["is_downbeat"], "duration": n["duration"]} for n in notes],
        key="C Major", max_plans=50,
    )
    api_chords = [c["chords"] for c in api.get("candidates") or []]
    core_chords = [[ch.function for ch in s.chords] for s in core.solutions]
    ok = bool(api_chords) == bool(core_chords) and api_chords == core_chords
    check(wave, name, ok, f"api={api_chords} core={core_chords}")


# ---------------------------------------------------------------- W2: pipeline
def _candidate_defects(cand) -> list[str]:
    probs = []
    chords = cand.get("chords") or []
    vos = cand.get("voicings") or []
    n = len(vos)
    for i, v in enumerate(vos):
        s, a, t, b = v["soprano"], v["alto"], v["tenor"], v["bass"]
        sym = chords[i] if i < len(chords) else "?"
        if not (s > a > t > b):
            probs.append(f"[{i} {sym}] S={s} A={a} T={t} B={b}")
        try:
            root, third, fifth = triads(sym)
        except Exception:  # noqa: BLE001
            probs.append(f"[{i} {sym}] triad parse error")
            continue
        pcs = {x % 12 for x in (s, a, t, b)}
        if third not in pcs:
            probs.append(f"[{i} {sym}] third {third} missing pcs={sorted(pcs)}")
        if fifth not in pcs and i != n - 1:
            probs.append(f"[{i} {sym}] fifth {fifth} missing (non-final) pcs={sorted(pcs)}")
        if sym.upper() == "K64" and i == 0:
            probs.append("[0 K64] K64 as first chord")
    return probs


def w2_default(wave: str, name: str) -> None:
    r = harmonize(melody([64, 65, 67, 64, 62, 60], durations=["half"] * 5 + ["whole"]))
    data = r.json()
    check(wave, name, data.get("is_success") is True and data.get("candidates"),
          f"status={r.status_code} is_success={data.get('is_success')} msg={str(data.get('message'))[:100]}")


def w2_desc_scale(wave: str, name: str) -> None:
    for label, pitches in [("C5 B4 A4 G4", [72, 71, 69, 67]),
                           ("C5..C4", [72, 71, 69, 67, 65, 64, 62, 60])]:
        data = harmonize(melody(pitches, max_plans=80)).json()
        check(wave, f"{name} [{label}]", data.get("is_success") is True,
              f"is_success={data.get('is_success')} msg={str(data.get('message'))[:80]}")


def w2_k64(wave: str, name: str) -> None:
    data = harmonize(melody([72, 67, 64, 60])).json()
    if not data.get("is_success"):
        check(wave, name, False, "melody C5 G4 E4 C4 did not harmonize")
        return
    chords = data["candidates"][0]["chords"]
    check(wave, name, chords[0].upper() != "K64", f"chords={chords}")


def w2_grade_requires_chords(wave: str, name: str) -> None:
    body = {
        "voicings": [{"soprano": 64, "alto": 60, "tenor": 55, "bass": 48}],
        "key": {"tonic": "C", "mode": "Major"},
    }
    r = client.post("/api/grade", json=body)
    check(wave, name, r.status_code == 422, f"status={r.status_code} body={str(r.text)[:120]}")


def w2_grade_unison(wave: str, name: str) -> None:
    body = {
        "voicings": [{"soprano": 64, "alto": 60, "tenor": 48, "bass": 48}],
        "chords": ["T"],
        "key": {"tonic": "C", "mode": "Major"},
    }
    r = client.post("/api/grade", json=body)
    if r.status_code == 422:
        check(wave, name, True, "422 (strict contract)")
        return
    data = r.json()
    report = data.get("report") or {}
    hard = report.get("hard_violations_count", 0)
    grade = str(report.get("grade", ""))
    check(wave, name, hard >= 1 and not grade.startswith("5"),
          f"status={r.status_code} hard={hard} grade={grade!r}")


def w2_invariants(wave: str, name: str) -> None:
    data = harmonize(melody([64, 65, 67, 64, 62, 60], durations=["half"] * 5 + ["whole"])).json()
    cands = data.get("candidates") or []
    if not cands:
        check(wave, name, False, "no candidates")
        return
    probs = []
    for idx, cand in enumerate(cands):
        probs += [f"cand{idx}: {p}" for p in _candidate_defects(cand)]
    check(wave, name, not probs, f"candidates={len(cands)}; issues={probs[:8]}")


def w2_xml_measures(wave: str, name: str) -> None:
    data = harmonize(melody([64, 65, 67, 64, 62, 60], durations=["half"] * 5 + ["whole"])).json()
    cands = data.get("candidates") or []
    if not cands:
        check(wave, name, False, "no candidates")
        return
    xml_text = cands[0].get("musicxml") or ""
    root = ET.fromstring(xml_text)
    bad = []
    divisions = 4
    for attr in root.iter("divisions"):
        divisions = int(attr.text or 4)
        break
    for measure in root.iter("measure"):
        num = measure.get("number", "?")
        acc = 0
        for child in measure:
            if child.tag == "backup":
                break
            if child.tag == "note" and child.find("duration") is not None:
                acc += int(child.find("duration").text or 0)
        expected = 16  # 4/4 * divisions(4)
        if acc != expected:
            bad.append(f"m{num}:{acc}!={expected}")
    check(wave, name, not bad, f"divisions={divisions} bad={bad[:6]}")


W1 = [
    ("1", "T1 generate T@E4", w1_t1_generation),
    ("1", "T1 unison rejected", w1_t1_unison),
    ("1", "T1 third flagged", w1_t1_third),
    ("1", "T2 D43/D2/II43/II2 bass", w1_t2),
    ("1", "T3 parse_chord_symbol enum", w1_t3_parse),
    ("1", "T3 doubling parity", w1_t3_parity),
    ("1", "T12 CORS", w1_cors),
    ("1", "T12 validation 422", w1_validation),
    ("1", "T6 secondary dominants", w1_secondary),
    ("1", "T5 api==core", w1_parity),
]
W2 = [
    ("2", "T13 default melody", w2_default),
    ("2", "T13 descending scales", w2_desc_scale),
    ("2", "T8 K64 not first", w2_k64),
    ("2", "T7 grade requires chords", w2_grade_requires_chords),
    ("2", "T1/T7 grade catches unison", w2_grade_unison),
    ("2", "T1 invariants on candidates", w2_invariants),
    ("2", "T11 XML measures full", w2_xml_measures),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", choices=["1", "2", "all"], default="all")
    args = parser.parse_args()
    waves = ["1"] if args.wave == "1" else ["2"] if args.wave == "2" else ["1", "2"]
    plan = (W1 if "1" in waves else []) + (W2 if "2" in waves else [])
    for wave, label, fn in plan:
        guard(wave, label, fn)
    failed = [r for r in RESULTS if not r[2] and r[0] in waves]
    print("\n=== SUMMARY ===")
    for w in waves:
        total = [r for r in RESULTS if r[0] == w]
        bad = [r for r in total if not r[2]]
        print(f"wave {w}: {len(total) - len(bad)}/{len(total)} passed")
    if failed:
        print("FAILED:")
        for w, n, _, d in failed:
            print(f"  - [{w}] {n}: {d}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

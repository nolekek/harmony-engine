# -*- coding: utf-8 -*-
"""Lead verification harness for P1 wave (architectural debt).

Run:
    python .redteam/scratch/lead/verify_p1.py --wave A   # dictionary + NCT + key detector + P0 regressions
    python .redteam/scratch/lead/verify_p1.py --wave B   # metric grid, unified rules, service
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"D:\aitraining")

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402
from src.harmony.core.types import Key, Chord, Voicing, to_satb, parse_chord_symbol  # noqa: E402
from src.harmony.rules.engine import RuleEngine  # noqa: E402
from src.harmony.rules.doubling import get_triad_tones  # noqa: E402
from src.harmony.pipeline import Harmonizer  # noqa: E402
from src.harmony.syntax.grammar import HarmonicGrammar  # noqa: E402

client = TestClient(app)
KEY = Key(tonic="C", mode="Major")
TONIC_PC = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
    "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}
RESULTS: list[tuple[str, str, bool, str]] = []


def check(wave: str, name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((wave, name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'} [{wave}] {name}" + (f" | {detail}" if detail else ""))


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


def harmonize(notes, tonic="C", mode="Major", ts="4/4", max_plans=60, sec=True):
    return client.post("/api/harmonize", json={
        "melody": notes, "key": {"tonic": tonic, "mode": mode},
        "time_signature": ts, "allow_extended_ranges": False,
        "allow_secondary_dominants": sec, "max_plans": max_plans,
    })


# ---------------------------------------------------------------- P1-A: T16
def a_dictionary(wave: str, name: str) -> None:
    checks = [
        ("III major", get_triad_tones("III", 0, "Major"), (4, 7, 11)),
        ("III minor", get_triad_tones("III", 9, "MinorHarmonic"), (0, 4, 7)),
        ("VII major", get_triad_tones("VII", 0, "Major"), (11, 2, 5)),
        ("II7 tones", get_triad_tones("II7", 0, "Major"), (2, 5, 9)),
    ]
    bad = [(lbl, got, want) for lbl, got, want in checks if got != want]
    check(wave, name, not bad, f"bad={bad[:3]}")


def a_roman(wave: str, name: str) -> None:
    from src.harmony.core.chord import normalize_roman
    checks = [("I", "T"), ("IV", "S"), ("V", "D")]
    bad = [(sym, normalize_roman(sym)) for sym, want in checks if normalize_roman(sym) != want]
    check(wave, name, not bad, f"bad={bad}")


def a_descending(wave: str, name: str) -> None:
    h = Harmonizer()
    for label, mel in [("C5 B4 A4 G4", [72, 71, 69, 67]),
                       ("8-note scale", [72, 71, 69, 67, 65, 64, 62, 60])]:
        r = h.harmonize(mel, key="C Major")
        check(wave, f"{name} [{label}]", r.is_success, f"msg={r.message[:80]}")


def a_ii7_to_t_forbidden(wave: str, name: str) -> None:
    g = HarmonicGrammar()
    ok = (g.is_valid_syntax_transition("II7", "T") is False
          and g.is_valid_syntax_transition("II7", "D") is True)
    check(wave, name, ok, "II7->T forbidden, II7->D allowed")


# ---------------------------------------------------------------- P1-A: T15
def a_nct(wave: str, name: str) -> None:
    from src.harmony.rules.non_chord_tones import classify_nct
    h = Harmonizer()
    r = h.harmonize([60, 62, 64], key="C Major", chords=["T", "T", "T"])
    check(wave, f"{name} [passing over T]", r.is_success, f"msg={r.message[:80]}")
    phrase = h.harmonize([60, 62, 64, 65, 67, 65, 64, 62, 60], key="C Major")
    check(wave, f"{name} [C-D-E-F-G-F-E-D-C]", phrase.is_success, f"msg={phrase.message[:80]}")
    cls = classify_nct(60, 62, 64, {0, 4, 7}, is_downbeat=False)
    check(wave, f"{name} [classify: passing]", cls == "passing", f"cls={cls!r}")


# ---------------------------------------------------------------- P1-A: T19
def a_detect_key(wave: str, name: str) -> None:
    cases = [
        ("C D E F G", [60, 62, 64, 65, 67], "C", ("Major",)),
        ("A B C D E", [57, 59, 60, 62, 64], "A", ("Minor", "MinorHarmonic")),
    ]
    bad = []
    for label, mel, tonic, modes in cases:
        data = client.post("/api/detect-key", json=[{"pitch": p} for p in mel]).json()
        if data.get("tonic") != tonic or data.get("mode") not in modes:
            bad.append(f"{label}: {data.get('tonic')} {data.get('mode')}")
    check(wave, name, not bad, f"bad={bad}")


# ---------------------------------------------------------------- P0 regressions
def r_default(wave: str, name: str) -> None:
    data = harmonize(melody([64, 65, 67, 64, 62, 60], durations=["half"] * 5 + ["whole"])).json()
    check(wave, name, data.get("is_success") is True and data.get("candidates"),
          f"is_success={data.get('is_success')}")


def r_invariants(wave: str, name: str) -> None:
    data = harmonize(melody([64, 65, 67, 64, 62, 60], durations=["half"] * 5 + ["whole"])).json()
    cands = data.get("candidates") or []
    bad = []
    for cand in cands:
        chords = cand.get("chords") or []
        vos = cand.get("voicings") or []
        n = len(vos)
        for i, v in enumerate(vos):
            s, a, t, b = v["soprano"], v["alto"], v["tenor"], v["bass"]
            sym = chords[i] if i < len(chords) else "?"
            if not (s > a > t > b):
                bad.append(f"[{i} {sym}] order {s}/{a}/{t}/{b}")
            if chords and i < len(chords):
                try:
                    root, third, fifth = get_triad_tones(sym, 0, "Major")
                except Exception:  # noqa: BLE001
                    continue
                pcs = {x % 12 for x in (s, a, t, b)}
                if third not in pcs:
                    bad.append(f"[{i} {sym}] third missing")
                if fifth not in pcs and i != n - 1:
                    bad.append(f"[{i} {sym}] fifth missing")
    check(wave, name, cands and not bad, f"cands={len(cands)} bad={bad[:5]}")


def r_secondary(wave: str, name: str) -> None:
    # With secondary dominants disabled the engine may now legitimately succeed
    # via a diatonic plan + chromatic NCT — as long as NO candidate uses DD*.
    data = harmonize(melody([64, 66, 67, 64, 62, 60]), sec=False).json()
    chords = [c.get("chords") or [] for c in (data.get("candidates") or [])]
    no_dd = all(not any(str(fn).startswith("DD") for fn in ch) for ch in chords)
    if data.get("is_success"):
        ok, detail = no_dd, f"success without DD: {chords[:1]}"
    else:
        code = (data.get("error") or {}).get("code")
        ok, detail = code == "SECONDARY_DOMINANTS_DISABLED", f"refusal code={code!r}"
    check(wave, name, ok, detail)


def r_grade(wave: str, name: str) -> None:
    no_ch = client.post("/api/grade", json={
        "voicings": [{"soprano": 64, "alto": 60, "tenor": 55, "bass": 48}],
        "key": {"tonic": "C", "mode": "Major"}})
    unison = client.post("/api/grade", json={
        "voicings": [{"soprano": 64, "alto": 60, "tenor": 48, "bass": 48}],
        "chords": ["T"], "key": {"tonic": "C", "mode": "Major"}})
    u = unison.json().get("report") or {}
    ok = (no_ch.status_code == 422 and unison.status_code == 200
          and (u.get("hard_violations_count") or 0) >= 1
          and not str(u.get("grade", "")).startswith("5"))
    check(wave, name, ok, f"no_chords={no_ch.status_code} hard={u.get('hard_violations_count')} grade={u.get('grade')!r}")


def r_xml(wave: str, name: str) -> None:
    data = harmonize(melody([64, 65, 67, 64, 62, 60], durations=["half"] * 5 + ["whole"])).json()
    cands = data.get("candidates") or []
    if not cands:
        check(wave, name, False, "no candidates")
        return
    root = ET.fromstring(cands[0].get("musicxml") or "")
    bad = []
    for measure in root.iter("measure"):
        num = measure.get("number", "?")
        acc = 0
        for child in measure:
            if child.tag == "backup":
                break
            if child.tag == "note" and child.find("duration") is not None:
                acc += int(child.find("duration").text or 0)
        if acc != 16:
            bad.append(f"m{num}:{acc}")
    check(wave, name, not bad, f"bad={bad[:6]}")


def r_cors(wave: str, name: str) -> None:
    r = client.get("/api/health", headers={"Origin": "http://evil.com"})
    acao = r.headers.get("access-control-allow-origin", "")
    check(wave, name, acao != "http://evil.com", f"acao={acao!r}")


WAVE_A = [
    ("A", "T16 dictionary tones", a_dictionary),
    ("A", "T16 roman normalization", a_roman),
    ("A", "T16 descending diatonic harmonizes", a_descending),
    ("A", "T16 II7->T forbidden", a_ii7_to_t_forbidden),
    ("A", "T15 NCT passing tones", a_nct),
    ("A", "T19 detect-key half cadence", a_detect_key),
    ("A", "P0 default melody", r_default),
    ("A", "P0 voicing invariants", r_invariants),
    ("A", "P0 secondary dominants", r_secondary),
    ("A", "P0 grade contract", r_grade),
    ("A", "P0 musicxml measures", r_xml),
    ("A", "P0 CORS", r_cors),
]

WAVE_B: list[tuple[str, str, object]] = []


def b_metric_34(wave: str, name: str) -> None:
    data = harmonize(melody([64, 65, 67, 64, 62, 60], durations=["quarter"] * 6), ts="3/4").json()
    cands = data.get("candidates") or []
    if not cands:
        check(wave, name, False, f"no candidates: {str(data.get('message'))[:80]}")
        return
    root = ET.fromstring(cands[0].get("musicxml") or "")
    divisions = 4
    for div in root.iter("divisions"):
        divisions = int(div.text or 4)
        break
    expected = 3 * divisions  # 3/4 in divisions (division == 4 -> 12)
    bad = []
    for measure in root.iter("measure"):
        acc = 0
        for child in measure:
            if child.tag == "backup":
                break
            if child.tag == "note" and child.find("duration") is not None:
                acc += int(child.find("duration").text or 0)
        if acc != expected:
            bad.append(f"m{measure.get('number')}:{acc}!={expected}")
    check(wave, name, not bad, f"divisions={divisions} bad={bad[:6]}")


def b_d_to_s(wave: str, name: str) -> None:
    eng = RuleEngine()
    d = Chord(function="D")
    s = Chord(function="S")
    hard_ban = [v.rule_id for v in eng.check_syntax(d, s, phrase_boundary=False) if v.is_hard]
    at_boundary = [v.rule_id for v in eng.check_syntax(d, s, phrase_boundary=True) if v.is_hard]
    ok = bool([r for r in hard_ban if "D_TO_S" in r.upper() or "D-S" in r.upper()]) and not [
        r for r in at_boundary if "D_TO_S" in r.upper() or "D-S" in r.upper()]
    check(wave, name, ok, f"inside={hard_ban} boundary={at_boundary}")


def b_catalog(wave: str, name: str) -> None:
    eng = RuleEngine()
    desc = eng.get_rule_description("VOICE_UNISON") or eng.get_rule_description("DIRECT_UNISON")
    check(wave, name, bool(desc), f"desc={str(desc)[:80]!r}")


def b_seventh_hold(wave: str, name: str) -> None:
    from src.harmony.rules.resolutions import check_seventh_resolution
    c_d7 = Chord(function="D7")
    c_d65 = Chord(function="D65")
    k = Key(tonic="C", mode="Major")
    v_d7 = Voicing(soprano=67, alto=65, tenor=62, bass=43)   # G F D G -> D7, 7th F in alto
    v_d65 = Voicing(soprano=67, alto=65, tenor=62, bass=47)  # same upper voices, bass B (D65)
    viol = check_seventh_resolution(v_d7, v_d65, c_d7, c_d65, key=k)
    ids = [v.rule_id for v in viol if v.is_hard]
    check(wave, name, not ids, f"hard={ids}")


def b_dim5_to_p5(wave: str, name: str) -> None:
    from src.harmony.rules.voice_leading import check_parallel_fifths_and_octaves
    prev = Voicing(soprano=72, alto=67, tenor=59, bass=54)  # S=C5, B=F#3 -> dim5 (18 % 12 = 6)
    curr = Voicing(soprano=74, alto=69, tenor=62, bass=55)  # S=D5, B=G3  -> P5 (19 % 12 = 7)
    viol = check_parallel_fifths_and_octaves(prev, curr)
    ids = [v.rule_id for v in viol]
    check(wave, name, bool(ids), f"ids={ids}")


def b_costs(wave: str, name: str) -> None:
    data = harmonize(melody([64, 65, 67, 64, 62, 60], durations=["half"] * 5 + ["whole"])).json()
    cands = data.get("candidates") or []
    costs = [c.get("cost") for c in cands]
    check(wave, name, bool(cands) and all(c >= 0 for c in costs), f"costs={costs}")


def b_api_404(wave: str, name: str) -> None:
    r = client.get("/api/definitely-not-a-route")
    ctype = r.headers.get("content-type", "")
    ok = r.status_code == 404 and "application/json" in ctype
    check(wave, name, ok, f"status={r.status_code} ctype={ctype!r}")


def b_deterministic(wave: str, name: str) -> None:
    a = harmonize(melody([64, 65, 67, 64, 62, 60], durations=["half"] * 5 + ["whole"])).json()
    b = harmonize(melody([64, 65, 67, 64, 62, 60], durations=["half"] * 5 + ["whole"])).json()
    ca = [c.get("chords") for c in a.get("candidates") or []]
    cb = [c.get("chords") for c in b.get("candidates") or []]
    check(wave, name, bool(ca) and ca == cb, f"a={ca[:1]} b={cb[:1]}")


WAVE_B.extend([
    ("B", "T14 metric grid 3/4 measures", b_metric_34),
    ("B", "T17 D->S only at phrase boundary", b_d_to_s),
    ("B", "T17 rule catalog is live", b_catalog),
    ("B", "T18 D7->D65 seventh hold allowed", b_seventh_hold),
    ("B", "T18 dim5->P5 parallel caught", b_dim5_to_p5),
    ("B", "T18 non-negative costs", b_costs),
    ("B", "T21 unknown /api route JSON 404", b_api_404),
    ("B", "T21 deterministic results", b_deterministic),
])



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", choices=["A", "B", "all"], default="all")
    args = parser.parse_args()
    waves = ["A"] if args.wave == "A" else ["B"] if args.wave == "B" else ["A", "B"]
    plan = (WAVE_A if "A" in waves else []) + (WAVE_B if "B" in waves else [])
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

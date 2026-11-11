import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import json
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key, parse_key, parse_chord_symbol
from src.harmony.rules.doubling import get_triad_tones

h = Harmonizer()

# 10 representative melodies across different styles and keys
SAMPLE_MELODIES = [
    ("C Major", "4/4", [60, 64, 67, 72, 71, 69, 67, 60], "Diatonic arpeggio & descent"),
    ("G Major", "3/4", [67, 69, 71, 74, 72, 71, 69, 67], "Turn and cadence in G"),
    ("A MinorHarmonic", "4/4", [69, 71, 72, 74, 76, 77, 80, 81], "Ascending scale A minor"),
    ("A MinorHarmonic", "4/4", [81, 80, 77, 76, 74, 72, 71, 69], "Descending scale A minor"),
    ("F Major", "2/4", [65, 69, 72, 70, 69, 67, 65], "F major lyric melody"),
    ("D MinorHarmonic", "6/8", [62, 65, 69, 70, 69, 67, 65, 64, 62], "D minor 6/8 compound"),
    ("E Major", "4/4", [64, 68, 71, 73, 71, 69, 68, 64], "E major chorale tune"),
    ("Bb Major", "3/4", [70, 72, 74, 75, 74, 72, 70], "Bb major arc"),
    ("C Major", "4/4", [60, 62, 64, 65, 67, 69, 71, 72], "C major ascending octave"),
    ("E MinorHarmonic", "4/4", [64, 67, 71, 70, 71, 74, 75, 76], "E minor leaps"),
]

def analyze_musicality(idx, key_str, meter, notes, desc):
    res = h.harmonize(notes, key_str, time_signature=meter)
    if not res.is_success:
        return {"index": idx, "description": desc, "success": False, "msg": res.message}

    sol = res.best_solution
    k = Key.parse(key_str)
    tonic_pc, mode = parse_key(k)
    chords = [c.function for c in sol.chords]
    voicings = sol.voicings
    n = len(chords)

    suspicious = []

    # 1. Start not with T
    if chords[0] not in ("T", "t", "T53", "t53"):
        suspicious.append(f"START_NOT_TONIC: Piece starts with {chords[0]} instead of tonic T/t")

    # 2. Final cadence not via dominant
    if n >= 2:
        penult = chords[-2]
        ult = chords[-1]
        dom_group = ("D", "D7", "D65", "D43", "D2", "d", "d7", "K64", "k64", "VII7", "VII6")
        if ult in ("T", "t") and penult not in dom_group:
            suspicious.append(f"FINAL_NOT_AUTHENTIC_CADENCE: Cadence is {penult} -> {ult} (not dominant preparation)")

    # 3. Patch chords: III, III6, or VI without harmonic necessity
    for step, c in enumerate(chords):
        if c in ("III", "III6", "iii", "iii6"):
            context = chords[max(0, step-1):min(n, step+2)]
            suspicious.append(f"PATCH_III_CHORD at step {step}: '{c}' used in context {context}")
        if c in ("VI", "vi") and step > 0 and chords[step-1] not in ("D", "D7", "d", "d7"):
            context = chords[max(0, step-1):min(n, step+2)]
            suspicious.append(f"UNPREPARED_VI at step {step}: '{c}' without preceding dominant in context {context}")

    # 4. Repeated chords (stagnation)
    for step in range(1, n):
        if chords[step] == chords[step-1]:
            suspicious.append(f"REPEATED_CHORD at step {step}: '{chords[step]}' repeated from previous step")

    # 5. Independent chord tone verification
    mismatched_voicings = []
    for step, (c_fn, v) in enumerate(zip(chords, voicings)):
        root, third, fifth = get_triad_tones(c_fn, tonic_pc, mode)
        expected_pcs = {root, third, fifth}
        # Add 7th if applicable
        if any(x in c_fn for x in ("7", "65", "43", "2")):
            if c_fn.startswith("VII"):
                expected_pcs.add((tonic_pc + 8 if "MINOR" in mode.upper() else tonic_pc + 9) % 12)
            elif c_fn.startswith("II"):
                expected_pcs.add(tonic_pc % 12)
            elif c_fn.startswith("DD"):
                expected_pcs.add(tonic_pc % 12)
            else:
                expected_pcs.add((tonic_pc + 5) % 12)

        actual_pcs = (v.soprano % 12, v.alto % 12, v.tenor % 12, v.bass % 12)
        # Check lower voices
        for v_name, pc in [("A", actual_pcs[1]), ("T", actual_pcs[2]), ("B", actual_pcs[3])]:
            if pc not in expected_pcs:
                mismatched_voicings.append(f"Step {step} ({c_fn}): {v_name} PC {pc} not in chord tones {expected_pcs}")

    return {
        "index": idx,
        "description": desc,
        "key": key_str,
        "meter": meter,
        "notes": notes,
        "chords": chords,
        "cost": sol.cost,
        "suspicious": suspicious,
        "mismatched_voicings": mismatched_voicings,
    }

if __name__ == "__main__":
    results = []
    print("=== MUSICALITY AUDIT FOR 10 REPRESENTATIVE SOLUTIONS ===", flush=True)
    for i, (key, meter, notes, desc) in enumerate(SAMPLE_MELODIES):
        res = analyze_musicality(i+1, key, meter, notes, desc)
        results.append(res)
        print(f"\n[#{i+1}] {desc} ({key}, {meter}):", flush=True)
        print(f"  Chords: {res.get('chords')}", flush=True)
        if res.get("suspicious"):
            for s in res["suspicious"]:
                print(f"  ⚠️  {s}", flush=True)
        else:
            print("  ✅ No suspicious syntactic patterns found.", flush=True)
        if res.get("mismatched_voicings"):
            for m in res["mismatched_voicings"]:
                print(f"  ❌ {m}", flush=True)

    out_p = Path(__file__).parent / "musicality_audit.json"
    out_p.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved report to {out_p}", flush=True)

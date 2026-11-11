import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import random
import time
from collections import Counter
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key, TimeSignature, to_satb, parse_key, parse_chord_symbol
from src.harmony.rules.doubling import get_triad_tones
from src.harmony.rules.voice_leading import VOICE_PAIRS, VOICE_NAMES

# Seed for reproducibility
random.seed(42)

h = Harmonizer()

KEYS = [
    "C Major", "G Major", "D Major", "A Major", "E Major", "F Major", "Bb Major", "Eb Major",
    "A MinorHarmonic", "E MinorHarmonic", "D MinorHarmonic", "C MinorHarmonic",
]

METERS = ["4/4", "3/4", "2/4", "6/8"]

def generate_melodies():
    melodies = []
    # Generate ~360 melodies: 12 keys x 30 variations
    for key_str in KEYS:
        k = Key.parse(key_str)
        t_pc, mode = parse_key(k)
        is_min = "MINOR" in mode.upper()

        scale_intervals = [0, 2, 3, 5, 7, 8, 11] if is_min else [0, 2, 4, 5, 7, 9, 11]
        tonic_pitch = 60 + t_pc
        if tonic_pitch < 60:
            tonic_pitch += 12
        if tonic_pitch > 72:
            tonic_pitch -= 12

        # 30 melodies per key across different lengths 2..12 and meters
        for m_idx in range(30):
            meter = METERS[m_idx % len(METERS)]
            length = 2 + (m_idx % 11)  # lengths 2 to 12

            # Types: 0: diatonic smooth, 1: wide leaps, 2: repeated notes, 3: chromatic passing
            m_type = m_idx % 4

            notes = []
            curr_deg = 0  # tonic
            curr_pitch = tonic_pitch

            for step in range(length):
                if step == length - 1:
                    # Final on tonic or dominant
                    fin_deg = random.choice([0, 4])  # tonic or dominant
                    p = tonic_pitch + scale_intervals[fin_deg]
                    if p > 80:
                        p -= 12
                    if p < 60:
                        p += 12
                    notes.append(p)
                    break

                if m_type == 0:  # diatonic smooth
                    curr_deg = (curr_deg + random.choice([-2, -1, -1, 0, 1, 1, 2])) % 7
                    p = tonic_pitch + scale_intervals[curr_deg]
                    if random.random() < 0.2 and p + 12 <= 80:
                        p += 12
                    while p < 60:
                        p += 12
                    while p > 80:
                        p -= 12
                    notes.append(p)

                elif m_type == 1:  # wide leaps
                    curr_deg = (curr_deg + random.choice([-5, -4, -3, 3, 4, 5])) % 7
                    p = tonic_pitch + scale_intervals[curr_deg]
                    while p < 60:
                        p += 12
                    while p > 80:
                        p -= 12
                    notes.append(p)

                elif m_type == 2:  # repeated notes
                    if step > 0 and random.random() < 0.6:
                        notes.append(notes[-1])
                    else:
                        curr_deg = (curr_deg + random.choice([-1, 1, 2])) % 7
                        p = tonic_pitch + scale_intervals[curr_deg]
                        while p < 60:
                            p += 12
                        while p > 80:
                            p -= 12
                        notes.append(p)

                elif m_type == 3:  # chromatic
                    if random.random() < 0.3:
                        # Non-scale note
                        p = curr_pitch + random.choice([-1, 1])
                    else:
                        curr_deg = (curr_deg + random.choice([-1, 1])) % 7
                        p = tonic_pitch + scale_intervals[curr_deg]
                    while p < 60:
                        p += 12
                    while p > 80:
                        p -= 12
                    curr_pitch = p
                    notes.append(p)

            melodies.append((key_str, meter, notes, f"type_{m_type}_len_{length}"))

    return melodies

def check_invariants(sol, key_str, melody_notes, meter):
    violations = []
    k = Key.parse(key_str)
    tonic_pc, mode = parse_key(k)
    voicings = sol.voicings
    chords = sol.chords
    n = len(voicings)

    # Invariant 5: cost >= 0
    if sol.cost < 0:
        violations.append(f"NEGATIVE_COST: cost={sol.cost} < 0")

    # Invariant 6: Final chord T or D, no K64 first/last
    first_fn = parse_chord_symbol(chords[0])
    last_fn = parse_chord_symbol(chords[-1])
    if first_fn == "K64":
        violations.append(f"K64_FIRST: initial chord is K64")
    if last_fn == "K64":
        violations.append(f"K64_LAST: final chord is K64")
    if last_fn not in ("T", "t", "T6", "t6", "D", "d", "D7"):
        violations.append(f"INVALID_FINAL_CHORD: final chord {last_fn} is not T or D cadence")

    for i, v in enumerate(voicings):
        c = chords[i]
        c_fn = parse_chord_symbol(c)
        is_final = (i == n - 1)

        # Invariant 1: Strict order S > A > T > B (no unisons)
        if not (v.soprano > v.alto > v.tenor > v.bass):
            v_order = f"S={v.soprano}, A={v.alto}, T={v.tenor}, B={v.bass}"
            violations.append(f"VOICE_ORDER_VIOLATION at step {i} ({c_fn}): {v_order}")

        # Invariant 2: Chord 3rd present; 5th present except final chord
        root, third, fifth = get_triad_tones(c_fn, tonic_pc, mode)
        pcs = [p % 12 for p in (v.soprano, v.alto, v.tenor, v.bass)]
        counts = Counter(pcs)

        if counts[third] == 0:
            violations.append(f"CHORD_THIRD_MISSING at step {i} ({c_fn}): third PC {third} not in {pcs}")

        if not is_final:
            # 5th required in non-final chords (except incomplete D7 in root position)
            is_seventh_root = (c_fn in ("D7", "d7", "DD7", "II7", "VII7"))
            if counts[fifth] == 0:
                if is_seventh_root and counts[root] >= 2 and counts[third] >= 1:
                    # Incomplete root-position 7th chord allowed
                    pass
                else:
                    violations.append(f"CHORD_FIFTH_MISSING at step {i} ({c_fn}): fifth PC {fifth} not in {pcs}")

        # Invariant 3: All voices in chord tones, or soprano = NCT only on weak beat
        allowed_pcs = {root, third, fifth}
        # Add 7th if applicable
        if any(x in c_fn for x in ("7", "65", "43", "2")):
            if c_fn.startswith("VII"):
                allowed_pcs.add((tonic_pc + 8 if "MINOR" in mode.upper() else tonic_pc + 9) % 12)
            elif c_fn.startswith("II"):
                allowed_pcs.add(tonic_pc % 12)
            elif c_fn.startswith("DD"):
                allowed_pcs.add(tonic_pc % 12)
            else:
                allowed_pcs.add((tonic_pc + 5) % 12)

        # Check A, T, B are strictly chord tones
        for v_name, p in [("Alto", v.alto), ("Tenor", v.tenor), ("Bass", v.bass)]:
            if (p % 12) not in allowed_pcs:
                violations.append(f"NON_CHORD_TONE in lower voice {v_name} at step {i} ({c_fn}): pitch {p} (PC {p%12}) not in {allowed_pcs}")

        # Check Soprano: if not chord tone, must be on weak beat
        if (v.soprano % 12) not in allowed_pcs:
            is_db = False
            if sol.metric_info and i < len(sol.metric_info):
                is_db = sol.metric_info[i].get("is_downbeat", False)
            if is_db:
                violations.append(f"NCT_ON_DOWNBEAT in Soprano at step {i} ({c_fn}): pitch {v.soprano} (PC {v.soprano%12}) on downbeat")

    # Invariant 4: No parallel / hidden 5ths and 8ves
    for i in range(1, n):
        pv = voicings[i - 1]
        cv = voicings[i]
        p_satb = to_satb(pv)
        c_satb = to_satb(cv)
        pc_fn = parse_chord_symbol(chords[i - 1])
        cc_fn = parse_chord_symbol(chords[i])
        is_same = (pc_fn == cc_fn)

        for v1, v2 in VOICE_PAIRS:
            p1, p2 = p_satb[v1], p_satb[v2]
            c1, c2 = c_satb[v1], c_satb[v2]
            d1, d2 = c1 - p1, c2 - p2

            # Parallel motion (same direction)
            if d1 * d2 > 0:
                raw_prev = abs(p1 - p2)
                raw_curr = abs(c1 - c2)
                # Parallel 5ths
                if raw_prev % 12 == 7 and raw_curr % 12 == 7:
                    if not (is_same and (abs(d1) % 12 == 0 or abs(d2) % 12 == 0)):
                        violations.append(
                            f"PARALLEL_FIFTHS between {VOICE_NAMES[v1]}-{VOICE_NAMES[v2]} steps {i-1}->{i} ({pc_fn}->{cc_fn}): {p1}-{p2} -> {c1}-{c2}"
                        )
                # Parallel octaves / unisons
                if raw_prev % 12 == 0 and raw_curr % 12 == 0:
                    if not (is_same and (abs(d1) % 12 == 0 or abs(d2) % 12 == 0)):
                        violations.append(
                            f"PARALLEL_OCTAVES between {VOICE_NAMES[v1]}-{VOICE_NAMES[v2]} steps {i-1}->{i} ({pc_fn}->{cc_fn}): {p1}-{p2} -> {c1}-{c2}"
                        )

            # Hidden 5ths/8ves in outer voices (S and B)
            if (v1, v2) == (0, 3) and d1 * d2 > 0:
                int_curr = abs(c1 - c2) % 12
                if int_curr in (0, 7) and abs(d1) > 2:
                    iv_name = "8ve" if int_curr == 0 else "5th"
                    violations.append(
                        f"HIDDEN_{iv_name} in outer voices steps {i-1}->{i} ({pc_fn}->{cc_fn}): |dS|={abs(d1)} > 2"
                    )

    return violations

def check_determinism(melody, key_str, meter, sol1):
    sol2_res = h.harmonize(melody, key_str, time_signature=meter)
    if not sol2_res.is_success:
        return ["NON_DETERMINISTIC: first run succeeded, second run failed"]
    sol2 = sol2_res.best_solution
    chords1 = [c.function for c in sol1.chords]
    chords2 = [c.function for c in sol2.chords]
    if chords1 != chords2:
        return [f"NON_DETERMINISTIC_CHORDS: {chords1} != {chords2}"]
    v1 = [(v.soprano, v.alto, v.tenor, v.bass) for v in sol1.voicings]
    v2 = [(v.soprano, v.alto, v.tenor, v.bass) for v in sol2.voicings]
    if v1 != v2:
        return [f"NON_DETERMINISTIC_VOICINGS: {v1} != {v2}"]
    return []

if __name__ == "__main__":
    melodies = generate_melodies()
    print(f"Generated {len(melodies)} melodies for fuzz testing.", flush=True)

    success_count = 0
    fail_count = 0
    all_violations = []
    suspicious_solutions = []

    t_start = time.perf_counter()

    for idx, (key_str, meter, notes, tag) in enumerate(melodies):
        res = h.harmonize(notes, key_str, time_signature=meter)
        if not res.is_success:
            fail_count += 1
            continue

        success_count += 1
        sol = res.best_solution

        # Check invariants
        viols = check_invariants(sol, key_str, notes, meter)
        # Check determinism on every 5th successful melody
        if success_count % 5 == 0:
            det_viols = check_determinism(notes, key_str, meter, sol)
            viols.extend(det_viols)

        if viols:
            all_violations.append({
                "index": idx,
                "key": key_str,
                "meter": meter,
                "notes": notes,
                "chords": [c.function for c in sol.chords],
                "violations": viols,
            })
            print(f"FAILED INVARIANT [#{idx} {key_str} {meter} len {len(notes)}]: {viols}", flush=True)

        if (idx + 1) % 50 == 0:
            print(f"Progress: {idx+1}/{len(melodies)} processed (Success: {success_count}, Solved: {success_count/(idx+1)*100:.1f}%, Viols: {len(all_violations)})", flush=True)

    total_time = time.perf_counter() - t_start
    print("\n=== FUZZ TESTING COMPLETED ===", flush=True)
    print(f"Total melodies tested: {len(melodies)}", flush=True)
    print(f"Successful harmonizations: {success_count}", flush=True)
    print(f"Failed harmonizations: {fail_count}", flush=True)
    print(f"Solutions violating invariants: {len(all_violations)}", flush=True)
    print(f"Elapsed time: {total_time:.2f}s", flush=True)

    # Save summary log for report
    import json
    out_path = Path(__file__).parent / "fuzz_results.json"
    out_path.write_text(json.dumps({
        "total": len(melodies),
        "success": success_count,
        "failed": fail_count,
        "violations": all_violations,
    }, indent=2), encoding="utf-8")
    print(f"Saved results to {out_path}", flush=True)

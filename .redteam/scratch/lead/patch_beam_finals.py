# -*- coding: utf-8 -*-
"""Debug round: beam-width starvation on long melodies + seventh-chord finales."""
from pathlib import Path

root = Path(r"D:\aitraining")

# 1. Beam width: longer melodies need a wider beam, otherwise every surviving
#    partial path dead-ends and generate_plans returns zero plans.
g = root / "src" / "harmony" / "syntax" / "grammar.py"
t = g.read_text(encoding="utf-8")
old = "            beams = new_beams[:max(max_plans * 4, 16)]"
new = (
    "            # Long melodies need a wider beam: with only 4*max_plans partial\n"
    "            # paths every viable prefix can be pruned before the cadence,\n"
    "            # yielding zero plans for perfectly singable diatonic lines.\n"
    "            _beam_width = max(max_plans * 4, 16)\n"
    "            if len(notes) >= 12:\n"
    "                _beam_width = max(max_plans * 16, 640)\n"
    "            beams = new_beams[:_beam_width]"
)
assert old in t, "beam slice not found"
g.write_text(t.replace(old, new, 1), encoding="utf-8")
print("patched grammar beam width")

# 2. Engine: a seventh chord can never be the final chord (D7 half cadence is not a cadence).
e = root / "src" / "harmony" / "rules" / "engine.py"
t = e.read_text(encoding="utf-8")
anchor = "        # Cadential 6/4 must resolve to the dominant: it can never be the"
if anchor not in t:
    raise SystemExit("engine K64 anchor not found")
seventh_rule = '''        # A seventh chord can never end a piece: a half cadence closes on a
        # plain dominant triad, not on a suspended tritone.
        if is_final_chord:
            _final_sym = parse_chord_symbol(curr_chord)
            if _final_sym[-1:] in ("7", "2") or _final_sym[-2:] in ("65", "43"):
                violations.append(
                    RuleViolation(
                        rule_id="CADENCE_FINAL_SEVENTH_FORBIDDEN",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Chord '{_final_sym}' cannot be the final chord: "
                            "a cadence must close on a triad"
                        ),
                    )
                )

''' + anchor
e.write_text(t.replace(anchor, seventh_rule, 1), encoding="utf-8")
print("patched engine seventh finale")

# 3. Pipeline replanning finals: no inversions, no sevenths.
p = root / "src" / "harmony" / "pipeline.py"
t = p.read_text(encoding="utf-8")
t = t.replace(
    'cand_alts = [fn for fn in cand_alts if fn in ("T", "t", "T6", "t6", "K64")]',
    'cand_alts = [fn for fn in cand_alts if fn in ("T", "t")]',
)
t = t.replace(
    'cand_alts = [fn for fn in cand_alts if fn in ("D", "d", "D7", "d7", "VI", "vi")]',
    'cand_alts = [fn for fn in cand_alts if fn in ("D", "d", "VI", "vi")]',
)
t = t.replace(
    'k_cands = [fn for fn in k_cands if fn in ("T", "t", "T6", "t6")]',
    'k_cands = [fn for fn in k_cands if fn in ("T", "t")]',
)
t = t.replace(
    'k_cands = [fn for fn in k_cands if fn in ("D", "d", "D7", "d7", "VI", "vi")]',
    'k_cands = [fn for fn in k_cands if fn in ("D", "d", "VI", "vi")]',
)
p.write_text(t, encoding="utf-8")
print("patched pipeline final candidates")

# -*- coding: utf-8 -*-
"""Second pass: seventh-chord finales, pipeline final list, wider beam for long lines."""
from pathlib import Path

root = Path(r"D:\aitraining")

# 1. Engine: forbid seventh chords as the final chord.
e = root / "src" / "harmony" / "rules" / "engine.py"
t = e.read_text(encoding="utf-8")
anchor = '            elif curr_sym in ("T6", "t6", "D6", "d6", "D65", "d65", "D43", "d43", "D2", "d2", "VII6", "vii6", "VII", "vii", "S6", "s6", "II6", "ii6", "III6", "iii6"):'
if anchor not in t:
    raise SystemExit("engine final inversion anchor not found")
seventh_block = '''            elif curr_sym[-1:] in ("7", "2") or curr_sym[-2:] in ("65", "43"):
                violations.append(
                    RuleViolation(
                        rule_id="CADENCE_FINAL_SEVENTH_FORBIDDEN",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Final chord cannot be a seventh chord ({curr_sym}); "
                            "a cadence closes on a triad (T, D or VI)"
                        ),
                    )
                )
''' + anchor
t = t.replace(anchor, seventh_block, 1)
e.write_text(t, encoding="utf-8")
print("patched engine seventh finale")

# 2. Pipeline replanning finals: root-position triads only.
p = root / "src" / "harmony" / "pipeline.py"
t = p.read_text(encoding="utf-8")
for old, new in (
    ('cand_alts = [fn for fn in cand_alts if fn in ("T", "t", "T6", "t6", "K64")]',
     'cand_alts = [fn for fn in cand_alts if fn in ("T", "t")]'),
    ('cand_alts = [fn for fn in cand_alts if fn in ("D", "d", "D7", "d7", "VI", "vi")]',
     'cand_alts = [fn for fn in cand_alts if fn in ("D", "d", "VI", "vi")]'),
    ('k_cands = [fn for fn in k_cands if fn in ("T", "t", "T6", "t6")]',
     'k_cands = [fn for fn in k_cands if fn in ("T", "t")]'),
    ('k_cands = [fn for fn in k_cands if fn in ("D", "d", "D7", "d7", "VI", "vi")]',
     'k_cands = [fn for fn in k_cands if fn in ("D", "d", "VI", "vi")]'),
):
    if old not in t:
        print(f"  [warn] pipeline pattern missing: {old[:50]}")
    t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("patched pipeline final candidates")

# 3. Wider beam for very long melodies.
g = root / "src" / "harmony" / "syntax" / "grammar.py"
t = g.read_text(encoding="utf-8")
old = '''            if len(notes) >= 12:
                _beam_width = max(max_plans * 16, 640)'''
new = '''            if len(notes) >= 20:
                _beam_width = max(max_plans * 32, 1280)
            elif len(notes) >= 12:
                _beam_width = max(max_plans * 16, 640)'''
assert old in t, "beam width block not found"
g.write_text(t.replace(old, new, 1), encoding="utf-8")
print("patched grammar beam width for long lines")

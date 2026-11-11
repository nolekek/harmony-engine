# -*- coding: utf-8 -*-
"""DD2 must resolve to the dominant, not to the tonic."""
from pathlib import Path

p = Path(r"D:\aitraining\src\harmony\rules\resolutions.py")
t = p.read_text(encoding="utf-8")
old = '''    curr_sym = parse_chord_symbol(curr_chord).strip().upper().replace("/", "")
    violations: list[RuleViolation] = []

    if curr_sym not in ("T6", "T-6", "t6", "t-6"):
        violations.append(
            RuleViolation(
                rule_id="RESOLUTION_D2_TO_T6",
                severity="hard_gate",
                penalty=100000.0,
                description=f"D2 must resolve strictly to T6 (or t6), but got '{curr_sym}'",
                voices=(3,),
            )
        )
'''
new = '''    curr_sym = parse_chord_symbol(curr_chord).strip().upper().replace("/", "")
    violations: list[RuleViolation] = []

    # D2 (V4/2) resolves to T6; DD2 (V4/2 of V) resolves to the dominant
    # (D6/D/D7/D65) or K64 — it must NOT be forced into the tonic.
    is_dd2 = prev_sym == "DD2"
    allowed_targets = ("D6", "D", "D7", "D65", "K64") if is_dd2 else ("T6", "T-6", "t6", "t-6")
    if curr_sym not in allowed_targets:
        violations.append(
            RuleViolation(
                rule_id="RESOLUTION_DD2_TO_D6" if is_dd2 else "RESOLUTION_D2_TO_T6",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"DD2 must resolve to the dominant (D6/D/D7/D65) or K64, but got '{curr_sym}'"
                    if is_dd2
                    else f"D2 must resolve strictly to T6 (or t6), but got '{curr_sym}'"
                ),
                voices=(3,),
            )
        )
'''
assert old in t, "D2 block not found"
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("patched DD2 resolution")

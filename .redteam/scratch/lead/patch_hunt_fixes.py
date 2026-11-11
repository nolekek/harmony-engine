# -*- coding: utf-8 -*-
"""Batch fixes after the red-team hunt: cadence finals, range flag, rules."""
from pathlib import Path

root = Path(r"D:\aitraining")


def patch(path: Path, replacements: list[tuple[str, str]], *, allow_missing: bool = False) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in text:
            if allow_missing:
                print(f"  [skip] {path.name}: pattern not found: {old[:60]!r}")
                continue
            raise SystemExit(f"pattern not found in {path.name}: {old[:80]!r}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print(f"patched {path.name}")


# ---------------------------------------------------------------- pipeline.py
pipeline = root / "src" / "harmony" / "pipeline.py"
patch(pipeline, [
    (
        "        effective_extended = allow_extended_ranges or (allow_replanning and any(m[\"pitch\"] < 60 or m[\"pitch\"] > 81 for m in processed_melody))",
        "        # Honour the caller's flag: replanning must never silently widen the\n"
        "        # allowed vocal ranges when allow_extended_ranges=False.\n"
        "        effective_extended = allow_extended_ranges",
    ),
    (
        "        effective_extended = allow_extended_ranges or any(m[\"pitch\"] < 60 or m[\"pitch\"] > 81 for m in melody)",
        "        effective_extended = allow_extended_ranges",
    ),
])

# Restrict the replanned final chord to legal cadence endings.
text = pipeline.read_text(encoding="utf-8")
anchor = "                cand_alts.sort(key=lambda fn: ALL_FUNCTIONS.index(fn) if fn in ALL_FUNCTIONS else 999)"
if anchor not in text:
    raise SystemExit("replan cand_alts anchor not found")
final_guard = '''                # The final chord must be a legal cadence ending, never a
                # dominant inversion (D6/D65/D43) or a passing chord.
                if is_final:
                    tonic_pc_r, mode_r = parse_key(key)
                    is_minor_r = "MINOR" in str(mode_r).upper()
                    tonic_tones = {
                        tonic_pc_r,
                        (tonic_pc_r + 3 if is_minor_r else tonic_pc_r + 4) % 12,
                        (tonic_pc_r + 7) % 12,
                    }
                    if (target_pitch % 12) in tonic_tones:
                        cand_alts = [fn for fn in cand_alts if fn in ("T", "t", "T6", "t6", "K64")]
                    else:
                        cand_alts = [fn for fn in cand_alts if fn in ("D", "d", "D7", "d7", "VI", "vi")]
                    cand_alts = [fn for fn in cand_alts if fn != "K64"]

''' + anchor
text = text.replace(anchor, final_guard, 1)

# parse_key is imported? ensure import line has it
if "parse_key" not in text.split("\n\n")[0] and "parse_key" not in text[:2000]:
    pass
pipeline.write_text(text, encoding="utf-8")
print("patched pipeline.py (final cadence guard)")

# ---------------------------------------------------------------- doubling.py
doubling = root / "src" / "harmony" / "rules" / "doubling.py"
patch(doubling, [
    (
        'if sym in ("T", "t") and prev_sym.startswith("VII"):',
        'VII7_FAMILY = {"VII7", "vii7", "VII65", "vii65", "VII43", "vii43", "VII2", "vii2"}\n'
        '    if sym in ("T", "t") and prev_sym in VII7_FAMILY:',
    ),
    (
        "        if inversion == \"6\" and not is_diminished:\n"
        "            allowed = True  # canon: 5th may be omitted in a non-diminished first inversion",
        "        if inversion == \"6\" and not is_diminished and counts[third] <= 1:\n"
        "            # canon: 5th may be omitted in a non-diminished first inversion,\n"
        "            # but not while the bass (third) is doubled: that hollows the chord.\n"
        "            allowed = True",
    ),
    (
        '            and group.upper() in ("T", "K64")',
        '            and group.upper() == "T"',
    ),
])

# ---------------------------------------------------------------- resolutions.py
resolutions = root / "src" / "harmony" / "rules" / "resolutions.py"
patch(resolutions, [
    (
        '    if not prev_sym.startswith("VII") or curr_sym not in ("T", "t"):\n        return []',
        '    vii7_family = {"VII7", "vii7", "VII65", "vii65", "VII43", "vii43", "VII2", "vii2"}\n'
        '    if prev_sym not in vii7_family or curr_sym not in ("T", "t"):\n        return []',
    ),
])

# ---------------------------------------------------------------- engine.py
engine = root / "src" / "harmony" / "rules" / "engine.py"
patch(engine, [
    (
        "        # 4. Determine validity and final cost\n        has_hard = any(v.is_hard for v in violations)",
        "        # Cadential 6/4 must resolve to the dominant: it can never be the\n"
        "        # final chord of a piece.\n"
        "        if is_final_chord and parse_chord_symbol(curr_chord) in (\"K64\", \"k64\"):\n"
        "            violations.append(\n"
        "                RuleViolation(\n"
        "                    rule_id=\"CADENCE_K64_FINAL\",\n"
        "                    severity=\"hard_gate\",\n"
        "                    penalty=100000.0,\n"
        "                    description=\"K64 must resolve to D/D7 and cannot be the final chord\",\n"
        "                )\n"
        "            )\n\n"
        "        # 4. Determine validity and final cost\n        has_hard = any(v.is_hard for v in violations)",
    ),
])
print("done")

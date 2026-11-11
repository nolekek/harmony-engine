"""
Tests for Classical Musical Quality and Brigade Canon Rules:
(a) 20 diatonic melodies end on "T" in root position
(b) If melody ends on tonic and penultimate note belongs to dominant, penultimate chord is in (K64, D, D6, D7, D65, D43, D2)
(c) Start in (T, T6) for melodies starting with C/E/G (tonic triad tones)
(d) No two III6 chords in a row
"""

import pytest
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key, parse_key

# 20 diverse diatonic melodies with tonic final note and dominant penultimate note
DIATONIC_MELODIES = [
    # C Major (starts on C, E, or G; ends on C; penultimate in D, B, G, F)
    {"name": "C_maj_scale_asc", "key": "C Major", "ts": "4/4", "melody": [60, 62, 64, 65, 67, 69, 71, 72]},
    {"name": "C_maj_scale_desc", "key": "C Major", "ts": "4/4", "melody": [72, 71, 69, 67, 65, 64, 62, 60]},
    {"name": "C_maj_motif_5", "key": "C Major", "ts": "4/4", "melody": [64, 65, 67, 62, 60]},
    {"name": "C_maj_arch_7", "key": "C Major", "ts": "4/4", "melody": [60, 62, 64, 67, 65, 62, 60]},
    {"name": "C_maj_chorale_opening", "key": "C Major", "ts": "4/4", "melody": [67, 67, 69, 67, 65, 64, 62, 60]},
    {"name": "C_maj_start_third_6", "key": "C Major", "ts": "3/4", "melody": [64, 67, 65, 64, 62, 60]},
    {"name": "C_maj_start_fifth_7", "key": "C Major", "ts": "4/4", "melody": [67, 65, 64, 65, 67, 62, 60]},
    {"name": "C_maj_9_notes", "key": "C Major", "ts": "4/4", "melody": [60, 64, 65, 67, 65, 64, 65, 62, 60]},
    {"name": "C_maj_4_short", "key": "C Major", "ts": "4/4", "melody": [64, 65, 62, 60]},
    {"name": "C_maj_3_4_motif", "key": "C Major", "ts": "3/4", "melody": [60, 64, 67, 65, 62, 60]},

    # G Major (starts on G, B, or D; ends on G; penultimate in A, F#, D, C)
    {"name": "G_maj_scale_asc", "key": "G Major", "ts": "4/4", "melody": [67, 69, 71, 72, 74, 76, 78, 79]},
    {"name": "G_maj_scale_desc", "key": "G Major", "ts": "4/4", "melody": [79, 78, 76, 74, 72, 71, 69, 67]},
    {"name": "G_maj_motif_5", "key": "G Major", "ts": "4/4", "melody": [71, 72, 74, 69, 67]},
    {"name": "G_maj_hymn_7", "key": "G Major", "ts": "4/4", "melody": [67, 69, 71, 72, 71, 69, 67]},
    {"name": "G_maj_4_short", "key": "G Major", "ts": "4/4", "melody": [71, 72, 69, 67]},
    {"name": "G_maj_3_4_melody", "key": "G Major", "ts": "3/4", "melody": [67, 71, 74, 72, 69, 67]},

    # F Major (starts on F, A, or C; ends on F; penultimate in G, E, C, Bb)
    {"name": "F_maj_scale_asc", "key": "F Major", "ts": "4/4", "melody": [65, 67, 69, 70, 72, 74, 76, 77]},
    {"name": "F_maj_scale_desc", "key": "F Major", "ts": "4/4", "melody": [77, 76, 74, 72, 70, 69, 67, 65]},
    {"name": "F_maj_motif_5", "key": "F Major", "ts": "4/4", "melody": [69, 70, 72, 67, 65]},
    {"name": "F_maj_4_short", "key": "F Major", "ts": "4/4", "melody": [69, 70, 67, 65]},
]

DOMINANT_PENULTIMATE_ALLOWED = {"K64", "D", "D6", "D7", "D65", "D43", "D2"}


@pytest.fixture(scope="module")
def harmonizer():
    return Harmonizer()


@pytest.mark.parametrize("item", DIATONIC_MELODIES, ids=[m["name"] for m in DIATONIC_MELODIES])
def test_musical_quality_rules(harmonizer, item):
    """
    Validates musical quality rules for 20 diatonic melodies:
    (a) final = 'T' (root position)
    (b) penultimate chord in (K64, D, D6, D7, D65, D43, D2)
    (c) start in (T, T6)
    (d) no two III6 in a row
    """
    res = harmonizer.harmonize(item["melody"], key=item["key"], time_signature=item["ts"])
    assert res.is_success, f"Harmonization failed for {item['name']}: {res.message}"
    assert res.best_solution is not None, f"No best solution for {item['name']}"

    chords = [c.function for c in res.best_solution.chords]
    assert len(chords) == len(item["melody"])

    # (a) Final chord must be 'T' in root position
    assert chords[-1] == "T", f"{item['name']}: final chord {chords[-1]} != 'T'"

    # (b) Penultimate chord before final tonic must be in dominant family
    k = Key.parse(item["key"])
    tonic_pc, _ = parse_key(k)
    dom_pcs = {(tonic_pc + 7) % 12, (tonic_pc + 11) % 12, (tonic_pc + 2) % 12, (tonic_pc + 5) % 12}
    penult_pitch = item["melody"][-2]
    if (penult_pitch % 12) in dom_pcs:
        assert chords[-2] in DOMINANT_PENULTIMATE_ALLOWED, (
            f"{item['name']}: penultimate chord {chords[-2]} not in {DOMINANT_PENULTIMATE_ALLOWED}"
        )

    # (c) Start in (T, T6) for melodies starting with tonic triad notes (C/E/G in C-dur, etc.)
    tonic_triad_pcs = {tonic_pc, (tonic_pc + 4) % 12, (tonic_pc + 7) % 12}
    if (item["melody"][0] % 12) in tonic_triad_pcs:
        assert chords[0] in ("T", "T6"), f"{item['name']}: start chord {chords[0]} not in ('T', 'T6')"

    # (d) No two III6 in a row
    for i in range(len(chords) - 1):
        assert not (chords[i] in ("III6", "iii6") and chords[i + 1] in ("III6", "iii6")), (
            f"{item['name']}: consecutive III6 at step {i}->{i+1}: {chords}"
        )


def test_no_two_iii6_in_a_row_explicit(harmonizer):
    """Explicit invariant check: grammar never allows consecutive III6 in valid transitions."""
    g = harmonizer.grammar
    assert not g.is_valid_syntax_transition("III6", "III6")
    assert not g.is_valid_syntax_transition("III", "III6")
    assert not g.is_valid_syntax_transition("III6", "III")
    assert not g.is_valid_syntax_transition("iii6", "iii6")


def test_start_chords_for_c_e_g(harmonizer):
    """Explicitly verify that melodies starting with C, E, or G start on T or T6."""
    c_motifs = [
        [60, 64, 67, 62, 60],  # starts with C4
        [64, 67, 65, 62, 60],  # starts with E4
        [67, 65, 64, 62, 60],  # starts with G4
    ]
    for m in c_motifs:
        res = harmonizer.harmonize(m, key="C Major")
        assert res.is_success
        assert res.best_solution.chords[0].function in ("T", "T6")


def test_final_tonic_root_position_invariant(harmonizer):
    """Explicitly verify that final tonic cannot be T6."""
    mel = [64, 65, 67, 62, 60]
    res = harmonizer.harmonize(mel, key="C Major")
    assert res.is_success
    assert res.best_solution.chords[-1].function == "T"

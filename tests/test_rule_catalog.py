"""
Tests for RuleEngine catalog integration and syntax progression rules (T17).
Extended by wave 4 (defect #6): catalog completeness for emitted rule ids and
the grader fallback to catalog descriptions for unmapped ids.
"""
import re
from pathlib import Path

from src.harmony.core.types import Key, Chord, Voicing
from src.harmony.rules.engine import RuleEngine
from src.harmony.syntax.grammar import HarmonicGrammar
from backend.grader import grade_satb_solution


def test_rule_catalog_loaded():
    engine = RuleEngine()
    assert len(engine.rules_registry) > 0
    desc_unison = engine.get_rule_description("VOICE_UNISON")
    assert desc_unison is not None
    assert isinstance(desc_unison, str)
    assert len(desc_unison) > 0

    desc_p5 = engine.get_rule_description("PARALLEL_FIFTHS")
    assert desc_p5 is not None

    desc_missing = engine.get_rule_description("DEFINITELY_NON_EXISTENT_RULE_12345")
    assert desc_missing is None


def test_d_to_s_syntax_rule():
    engine = RuleEngine()
    chord_d = Chord(function="D")
    chord_s = Chord(function="S")

    # Inside phrase (phrase_boundary=False) -> hard violation
    viols_no_boundary = engine.check_syntax(
        chord_d, chord_s, is_downbeat=True, phrase_boundary=False
    )
    assert any(v.rule_id == "SYNTAX_NO_D_TO_S" for v in viols_no_boundary)

    # At phrase boundary (phrase_boundary=True) -> allowed!
    viols_boundary = engine.check_syntax(
        chord_d, chord_s, is_downbeat=True, phrase_boundary=True
    )
    assert not any(v.rule_id == "SYNTAX_NO_D_TO_S" for v in viols_boundary)


def test_grammar_syntax_transition_consistency():
    grammar = HarmonicGrammar(Key("C", "Major"))

    # D -> S inside phrase is forbidden
    assert not grammar.is_valid_syntax_transition("D", "S", is_downbeat=True, phrase_boundary=False)

    # D -> S at phrase boundary is allowed
    assert grammar.is_valid_syntax_transition("D", "S", is_downbeat=True, phrase_boundary=True)

    # K64 on weak beat is forbidden in grammar and engine
    assert not grammar.is_valid_syntax_transition("S", "K64", is_downbeat=False)


def test_catalog_contains_wave4_rule_ids():
    """Defect #6: key rule ids emitted by the code are catalogued with validator severity/penalty."""
    engine = RuleEngine()
    expected = {
        "FALSE_RELATION_PERECHENIE": ("hard_gate", 100000.0),
        "CADENCE_K64_FINAL": ("hard_gate", 100000.0),
        "CHORD_THIRD_MISSING": ("hard_gate", 100000.0),
        "NCT_SUSPENSION_UNRESOLVED": ("hard_gate", 100000.0),
        "NCT_PASSING_ON_DOWNBEAT": ("soft_penalty", 3.0),
        "NCT_ILLEGAL_LEAP_NON_CHORD_TONE": ("hard_gate", 100000.0),
        "RESOLUTION_DD2_TO_D6": ("hard_gate", 100000.0),
        "MELODIC_DIMINISHED_FOURTH_SOFT": ("soft", 5.0),
    }
    for rule_id, (severity, penalty) in expected.items():
        entry = engine.rules_registry.get(rule_id)
        assert entry is not None, f"{rule_id} missing from docs/brigade_rules.json"
        assert entry["severity"] == severity, f"{rule_id} severity mismatch"
        assert float(entry["penalty"]) == penalty, f"{rule_id} penalty mismatch"
        desc = engine.get_rule_description(rule_id)
        assert isinstance(desc, str) and len(desc) > 0


def test_catalog_covers_all_emitted_rule_ids():
    """Every statically emitted rule id in src/harmony must exist in the catalog."""
    src_root = Path(__file__).resolve().parents[1] / "src" / "harmony"
    emitted: set[str] = set()
    for py_file in src_root.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        # rule_id="LITERAL" emissions (including the first branch of ternaries)
        emitted.update(re.findall(r'rule_id="([A-Z0-9_]+)"', text))
        # doubling.py emits via local _add("LITERAL", ...) helpers
        emitted.update(re.findall(r'_add\(\s*"([A-Z0-9_]+)"', text))
    assert emitted, "sanity: the scan must find emitted rule ids"
    engine = RuleEngine()
    missing = emitted - set(engine.rules_registry)
    assert not missing, f"rule ids missing from catalog: {sorted(missing)}"


def test_grader_falls_back_to_catalog_description_for_unmapped_id():
    """Defect #6: grader answers with the Russian catalog description for unmapped rule ids."""
    engine = RuleEngine()
    catalog_desc = engine.get_rule_description("CADENCE_K64_FINAL")
    assert catalog_desc, "precondition: CADENCE_K64_FINAL must be in the catalog"

    # D -> K64(final): CADENCE_K64_FINAL fires on the final chord and has no
    # dedicated Russian formatting branch in backend/grader.py.
    v_d = Voicing(soprano=74, alto=71, tenor=67, bass=55)    # D: D5-B4-G4-G3
    v_k64 = Voicing(soprano=76, alto=72, tenor=67, bass=55)  # K64: E5-C5-G4-G3
    report = grade_satb_solution(
        voicings=[v_d, v_k64],
        key="C Major",
        chords=[Chord("D"), Chord("K64")],
    )
    viols = [v for v in report.violations if v["rule_id"] == "CADENCE_K64_FINAL"]
    assert viols, "K64 as the final chord must trigger CADENCE_K64_FINAL"
    assert viols[0]["message_ru"].endswith(catalog_desc), (
        f"grader must fall back to the catalog description, got: {viols[0]['message_ru']}"
    )

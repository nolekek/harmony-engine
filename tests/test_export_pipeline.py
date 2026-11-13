"""
Tests for MusicXML, MIDI exporters, and the end-to-end Harmonizer pipeline.
"""

from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

from src.harmony.core.types import Voicing, Key
from src.harmony.export.musicxml import export_to_musicxml
from src.harmony.export.midi import export_to_midi
from src.harmony.export.ascii import format_ascii_score
from src.harmony.pipeline import Harmonizer
from tests.corpus.benchmark_tasks import BENCHMARK_TASKS


def test_musicxml_export_validity():
    voicings = [
        Voicing(64, 60, 55, 48),
        Voicing(65, 60, 57, 41),
        Voicing(64, 60, 55, 48),
    ]
    chords = ["T", "S", "T"]
    xml_str = export_to_musicxml(voicings, chords, key="C Major", title="Test Score")

    assert xml_str.startswith("<?xml")
    assert "<work-title>Test Score</work-title>" in xml_str
    # Verify XML can be parsed without error
    root = ET.fromstring(xml_str)
    assert root.tag == "score-partwise"
    measures = root.findall(".//measure")
    assert len(measures) >= 2


def test_midi_export_validity():
    voicings = [
        Voicing(64, 60, 55, 48),
        Voicing(65, 60, 57, 41),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        midi_path = Path(tmpdir) / "output.mid"
        out = export_to_midi(voicings, midi_path)
        assert out.exists()
        assert out.stat().st_size > 30  # Standard MIDI header + track


def test_ascii_score_formatter():
    voicings = [Voicing(64, 60, 55, 48)]
    chords = ["T"]
    txt = format_ascii_score(voicings, chords, key="C Major")
    assert "Soprano" in txt
    assert "Bass" in txt


def test_harmonizer_end_to_end_on_benchmarks():
    harmonizer = Harmonizer()
    for task in BENCHMARK_TASKS:
        res = harmonizer.harmonize(
            melody=task["melody"],
            key=Key(task["key"]["tonic"], task["key"]["mode"]),
            chords=task["ground_truth_functions"],
        )
        assert res.is_success, f"Failed on {task['id']}: {res.message}"
        assert res.best_solution is not None
        assert len(res.best_solution.voicings) == len(task["melody"])
        assert res.best_solution.cost < float("inf")


def test_harmonizer_autonomous_melody_harmonization():
    """
    Tests harmonizing a pure soprano melody without any provided chord plan.
    The grammar must synthesize the plan and Viterbi must find the optimal SATB voicings.
    """
    harmonizer = Harmonizer()
    key = Key(tonic="C", mode="Major")
    # Soprano melody in C-major: E4, F4, G4, D4, C4
    melody = [
        {"pitch": 64, "is_downbeat": True},
        {"pitch": 65, "is_downbeat": False},
        {"pitch": 67, "is_downbeat": True},
        {"pitch": 62, "is_downbeat": False},
        {"pitch": 60, "is_downbeat": True},
    ]

    res = harmonizer.harmonize(melody=melody, key=key)
    assert res.is_success, f"Autonomous harmonization failed: {res.message}"
    assert res.best_solution is not None
    assert len(res.best_solution.voicings) == 5
    # Final chord must be T
    assert res.best_solution.chords[-1].function in ("T", "t")

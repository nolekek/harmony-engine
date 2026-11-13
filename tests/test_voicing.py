"""Unit tests for harmony.core.voicing."""

from harmony.core.chord import ChordDefinition
from harmony.core.key import Key, Mode
from harmony.core.pitch import PitchClass
from harmony.core.voicing import Spacing, Voice, Voicing
from tests.corpus.benchmark_tasks import BENCHMARK_TASKS


class TestVoicing:
    def test_construction_and_access(self):
        v = Voicing.from_midi(64, 60, 52, 48)
        assert v.soprano.midi_number == 64
        assert v.alto.midi_number == 60
        assert v.tenor.midi_number == 52
        assert v.bass.midi_number == 48

        assert v.S == v.soprano
        assert v.A == v.alto
        assert v.T == v.tenor
        assert v.B == v.bass

        assert v[Voice.SOPRANO] == v.soprano
        assert v[0] == v.soprano
        assert v[3] == v.bass
        assert len(v) == 4

    def test_ordering_and_voice_crossing(self):
        # Valid descending SATB
        v_ok = Voicing.from_midi(67, 64, 60, 48)
        assert v_ok.is_ordered
        assert not v_ok.has_voice_crossing

        # Voice crossing: Alto lower than Tenor
        v_cross = Voicing.from_midi(67, 55, 58, 48)
        assert not v_cross.is_ordered
        assert v_cross.has_voice_crossing
        assert not v_cross.is_spacing_valid()

    def test_intervals(self):
        v = Voicing.from_midi(64, 60, 55, 48)
        assert v.interval_sa.semitones == 4  # б3
        assert v.interval_at.semitones == 5  # ч4
        assert v.interval_tb.semitones == 7  # ч5
        assert v.interval_sb.semitones == 16  # б10

    def test_spacing_bounds(self):
        # Upper voice gap > 1 octave (S-A = 13)
        v_gap = Voicing.from_midi(73, 60, 52, 48)
        assert not v_gap.is_spacing_valid()
        assert any("S-A distance exceeds octave" in s for s in v_gap.spacing_violations())

        # Tenor-Bass gap > 2 octaves (T-B = 25)
        v_bass_gap = Voicing.from_midi(67, 64, 60, 35)
        assert not v_bass_gap.is_spacing_valid()
        assert any("T-B distance exceeds two octaves" in s for s in v_bass_gap.spacing_violations())

    def test_voice_ranges(self):
        # Soprano below C4 (60)
        v_low_s = Voicing.from_midi(59, 58, 55, 48)
        assert not v_low_s.in_ranges()
        assert any("Soprano" in s for s in v_low_s.range_violations())

        # Bass below E2 (40)
        v_low_b = Voicing.from_midi(64, 60, 52, 36)
        assert not v_low_b.in_ranges()
        assert any("Bass" in s for s in v_low_b.range_violations())

    def test_determine_spacing(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        t = ChordDefinition.from_string("T", c_dur)

        # Close spacing: S=E4(64), A=C4(60), T=G3(55)
        # S-A = 4, A-T = 5. intermediate chord tones = 0
        v_close = Voicing.from_midi(64, 60, 55, 48)
        assert v_close.determine_spacing(t) == Spacing.CLOSE

        # Wide spacing: S=E4(64), A=G3(55), T=C3(48)
        # Between E4 and G3 there is C4 (1 chord tone).
        # Between G3 and C3 there is E3 (1 chord tone).
        v_wide = Voicing.from_midi(64, 55, 48, 36)
        assert v_wide.determine_spacing(t) == Spacing.WIDE

    def test_benchmark_corpus_voicings(self):
        """Verify that ground truth SATB voicings from the benchmark tasks pass static validation."""
        for task in BENCHMARK_TASKS:
            key_info = task["key"]
            tonic_pc = PitchClass.from_name(key_info["tonic"])
            mode = Mode.from_str(key_info["mode"])
            Key(tonic_pc, mode)

            satb_list = task["ground_truth_satb"]
            for s, a, t, b in satb_list:
                voicing = Voicing.from_midi(s, a, t, b)
                # Voice order must be preserved (no crossing)
                assert voicing.is_ordered, f"Task {task['id']} has voice crossing: {voicing}"
                # Upper voice spacing must not exceed octave
                assert voicing.interval_sa.semitones <= 12
                assert voicing.interval_at.semitones <= 12
                # Bass-tenor gap must not exceed 2 octaves + third
                assert voicing.interval_tb.semitones <= 28

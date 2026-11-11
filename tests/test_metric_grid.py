"""
Tests for unified MetricGrid and metric structure calculations.
Validates 4/4, 3/4, 2/4, 6/8, 3/8 meters, barline crossings, and explicit downbeat overrides.
"""

import pytest
from src.harmony.core.metric import MetricGrid, build_metric_grid
from src.harmony.core.types import calculate_metric_structure, TimeSignature


class TestMetricGrid:
    def test_four_four_meter(self):
        # 4 quarter notes in 4/4 -> beats 0, 1, 2, 3. Downbeats on 0 and 2.
        durations = ["quarter", "quarter", "quarter", "quarter"]
        pitches = [60, 62, 64, 65]
        grid = MetricGrid(time_signature="4/4", durations=durations, pitches=pitches)

        assert len(grid) == 4
        items = list(grid)

        assert items[0]["measure"] == 1
        assert items[0]["beat"] == 0
        assert items[0]["offset"] == 0.0
        assert items[0]["is_downbeat"] is True
        assert items[0]["duration"] == "quarter"

        assert items[1]["measure"] == 1
        assert items[1]["beat"] == 1
        assert items[1]["offset"] == 1.0
        assert items[1]["is_downbeat"] is False

        assert items[2]["measure"] == 1
        assert items[2]["beat"] == 2
        assert items[2]["offset"] == 2.0
        assert items[2]["is_downbeat"] is True

        assert items[3]["measure"] == 1
        assert items[3]["beat"] == 3
        assert items[3]["offset"] == 3.0
        assert items[3]["is_downbeat"] is False

    def test_three_four_meter(self):
        # 3 quarter notes in 3/4 -> beats 0, 1, 2. Downbeat only on 0.
        durations = ["quarter", "quarter", "quarter"]
        grid = MetricGrid(time_signature="3/4", durations=durations)

        assert len(grid) == 3
        assert grid[0]["beat"] == 0 and grid[0]["is_downbeat"] is True
        assert grid[1]["beat"] == 1 and grid[1]["is_downbeat"] is False
        assert grid[2]["beat"] == 2 and grid[2]["is_downbeat"] is False

    def test_two_four_meter(self):
        # 2 quarter notes in 2/4 -> beats 0, 1. Downbeat only on 0.
        durations = ["quarter", "quarter"]
        grid = MetricGrid(time_signature="2/4", durations=durations)

        assert len(grid) == 2
        assert grid[0]["beat"] == 0 and grid[0]["is_downbeat"] is True
        assert grid[1]["beat"] == 1 and grid[1]["is_downbeat"] is False

    def test_six_eight_meter(self):
        # 6 eighth notes in 6/8 -> beats 0, 1, 2, 3, 4, 5 (in eighths).
        # Downbeats on 0 and 3.
        durations = ["eighth"] * 6
        grid = MetricGrid(time_signature="6/8", durations=durations)

        assert len(grid) == 6
        beats = [item["beat"] for item in grid]
        dbs = [item["is_downbeat"] for item in grid]

        assert beats == [0, 1, 2, 3, 4, 5]
        assert dbs == [True, False, False, True, False, False]

    def test_three_eight_meter(self):
        # 3 eighth notes in 3/8 -> beats 0, 1, 2. Downbeat only on 0.
        durations = ["eighth"] * 3
        grid = MetricGrid(time_signature="3/8", durations=durations)

        assert len(grid) == 3
        beats = [item["beat"] for item in grid]
        dbs = [item["is_downbeat"] for item in grid]

        assert beats == [0, 1, 2]
        assert dbs == [True, False, False]

    def test_note_crossing_barline(self):
        # In 4/4:
        # Note 0: half (2.0 quarters) -> starts m1, offset 0.0, beat 0, downbeat True
        # Note 1: dotted_half (3.0 quarters) -> starts m1, offset 2.0, beat 2, downbeat True. Crosses into measure 2!
        # Note 2: quarter (1.0 quarter) -> starts m2, offset 1.0 (since m2 has 1.0 left from note 1), beat 1, downbeat False
        durations = ["half", "dotted_half", "quarter"]
        pitches = [60, 62, 64]
        grid = build_metric_grid(time_signature="4/4", durations=durations, pitches=pitches)

        assert len(grid) == 3

        # Note 0
        assert grid[0]["measure"] == 1
        assert grid[0]["offset"] == 0.0
        assert grid[0]["beat"] == 0
        assert grid[0]["is_downbeat"] is True

        # Note 1 (crosses barline, measure must be measure at start = 1)
        assert grid[1]["measure"] == 1
        assert grid[1]["offset"] == 2.0
        assert grid[1]["beat"] == 2
        assert grid[1]["is_downbeat"] is True

        # Note 2 starts in measure 2 at offset 1.0
        assert grid[2]["measure"] == 2
        assert grid[2]["offset"] == 1.0
        assert grid[2]["beat"] == 1
        assert grid[2]["is_downbeat"] is False

    def test_multi_measure_progression(self):
        # 8 half notes in 4/4 -> 4 measures
        durations = ["half"] * 8
        grid = MetricGrid("4/4", durations=durations)

        assert len(grid) == 8
        for i, item in enumerate(grid):
            expected_measure = (i // 2) + 1
            expected_offset = 0.0 if (i % 2 == 0) else 2.0
            expected_beat = 0 if (i % 2 == 0) else 2
            assert item["measure"] == expected_measure
            assert item["offset"] == expected_offset
            assert item["beat"] == expected_beat
            assert item["is_downbeat"] is True  # In 4/4, beats 0 and 2 are downbeats


class TestCalculateMetricStructureIntegration:
    def test_calculate_metric_structure_backward_compatibility(self):
        notes = [
            {"pitch": 60, "duration": "quarter"},
            {"pitch": 62, "duration": "quarter", "is_downbeat": True},   # Explicit override on weak beat
            {"pitch": 64, "duration": "quarter", "is_downbeat": False},  # Explicit override on strong beat
            {"pitch": 65, "duration": "quarter"},
        ]
        res = calculate_metric_structure(notes, default_time_signature="4/4")

        assert len(res) == 4
        # Note 0: natural beat 0 -> True
        assert res[0]["is_downbeat"] is True
        assert res[0]["measure"] == 1
        assert res[0]["offset_in_measure"] == 0.0
        assert res[0]["offset"] == 0.0
        assert res[0]["beat"] == 0

        # Note 1: beat 1, explicit True -> True
        assert res[1]["is_downbeat"] is True
        assert res[1]["beat"] == 1
        assert res[1]["offset_in_measure"] == 1.0

        # Note 2: beat 2 (normally strong), explicit False -> False
        assert res[2]["is_downbeat"] is False
        assert res[2]["beat"] == 2
        assert res[2]["offset_in_measure"] == 2.0

        # Note 3: beat 3, natural -> False
        assert res[3]["is_downbeat"] is False
        assert res[3]["beat"] == 3
        assert res[3]["offset_in_measure"] == 3.0

"""
Unified Metric Grid Engine for Brigade Classical Harmony.
Provides deterministic, authoritative metric coordinates across 4/4, 3/4, 2/4, 6/8, and 3/8 meters.
"""

from __future__ import annotations

from typing import Any, Sequence

from src.harmony.core.types import (
    TimeSignature,
    parse_duration_quarters,
    quarters_to_xml_type_and_dots,
)


def _is_metric_downbeat(
    time_sig: TimeSignature,
    beat: int,
    offset_in_quarters: float,
    quarter_per_beat: float,
) -> bool:
    """
    Evaluates metric accent per Brigade textbook rules:
    - 4/4: downbeats on beats 0 and 2 (in quarters)
    - 3/4: downbeat on beat 0
    - 2/4: downbeat on beat 0
    - 6/8: downbeats on beats 0 and 3 (in eighths)
    - 3/8: downbeat on beat 0
    Syncopated notes starting off-beat are never downbeats.
    """
    # Verify the note starts exactly on a beat boundary (within tolerance)
    expected_offset = beat * quarter_per_beat
    if abs(offset_in_quarters - expected_offset) > 1e-4:
        return False

    b = time_sig.beats
    bt = time_sig.beat_type

    if b == 4 and bt == 4:
        return beat in (0, 2)
    if b == 3 and bt == 4:
        return beat == 0
    if b == 2 and bt == 4:
        return beat == 0
    if b == 6 and bt == 8:
        return beat in (0, 3)
    if b == 3 and bt == 8:
        return beat == 0

    # General fallback: measure start is always a downbeat
    if beat == 0:
        return True
    # Compound / duple / quadruple meters fallback
    if b == 2 and bt == 2 and beat == 0:
        return True
    if b == 4 and bt == 2 and beat in (0, 2):
        return True
    return False


class MetricGrid:
    """
    Authoritative Metric Grid representation for melody note sequences and chord slices.
    Yields for each note:
    {measure: int, beat: int, offset: float, is_downbeat: bool, duration: str}
    """

    def __init__(
        self,
        time_signature: Any = "4/4",
        durations: Sequence[str | float | int] | None = None,
        pitches: Sequence[int] | None = None,
        notes: Sequence[Any] | None = None,
    ) -> None:
        self.time_signature = TimeSignature.parse(time_signature)
        self._items: list[dict[str, Any]] = []
        self._build(durations=durations, pitches=pitches, notes=notes)

    def _build(
        self,
        durations: Sequence[str | float | int] | None,
        pitches: Sequence[int] | None,
        notes: Sequence[Any] | None,
    ) -> None:
        curr_time_sig = self.time_signature
        curr_measure = 1
        curr_offset = 0.0
        prev_time_sig = None

        raw_items: list[dict[str, Any]] = []

        if notes is not None:
            for item in notes:
                if isinstance(item, dict):
                    raw_items.append(item)
                else:
                    raw_items.append({"pitch": int(item), "duration": "half"})
        elif durations is not None:
            p_list = list(pitches) if pitches is not None else [60] * len(durations)
            for d, p in zip(durations, p_list):
                raw_items.append({"pitch": p, "duration": d})
        elif pitches is not None:
            for p in pitches:
                raw_items.append({"pitch": p, "duration": "half"})

        for item in raw_items:
            note_ts = None
            if "time_signature" in item and item["time_signature"]:
                note_ts = TimeSignature.parse(item["time_signature"])
            dur_raw = item.get("duration", "half")
            pitch = item.get("pitch", 60)
            explicit_db = item.get("is_downbeat")

            if note_ts is not None and note_ts != curr_time_sig:
                if curr_offset > 1e-4:
                    curr_measure += 1
                    curr_offset = 0.0
                curr_time_sig = note_ts

            dur_q = parse_duration_quarters(dur_raw)
            measure_duration = curr_time_sig.measure_duration_quarters
            quarter_per_beat = 4.0 / curr_time_sig.beat_type
            if measure_duration <= 1e-6 or quarter_per_beat <= 1e-6:
                # Defensive: a degenerate meter (0/4, 4/0) must never spin the
                # measure-advance loop forever. Fall back to 4/4.
                curr_time_sig = TimeSignature(4, 4)
                measure_duration = curr_time_sig.measure_duration_quarters
                quarter_per_beat = 4.0 / curr_time_sig.beat_type

            # Advance measure if offset exceeds measure length
            while curr_offset >= measure_duration - 1e-4:
                curr_measure += 1
                curr_offset -= measure_duration
            if abs(curr_offset) < 1e-4:
                curr_offset = 0.0

            time_sig_changed = (curr_time_sig != prev_time_sig)
            prev_time_sig = curr_time_sig

            beat = int(round(curr_offset / quarter_per_beat, 4))

            if explicit_db is not None:
                is_db = bool(explicit_db)
            else:
                is_db = _is_metric_downbeat(
                    curr_time_sig,
                    beat=beat,
                    offset_in_quarters=curr_offset,
                    quarter_per_beat=quarter_per_beat,
                )

            xml_type, dots = quarters_to_xml_type_and_dots(dur_q)
            norm_dur_name = f"dotted_{xml_type}" if dots > 0 else xml_type

            self._items.append({
                "pitch": pitch,
                "duration": norm_dur_name,
                "duration_quarters": dur_q,
                "measure": curr_measure,
                "beat": beat,
                "offset": round(curr_offset, 4),
                "offset_in_measure": round(curr_offset, 4),
                "is_downbeat": is_db,
                "time_signature": curr_time_sig,
                "time_sig_changed": time_sig_changed,
            })

            # Advance offset by duration; notes crossing barline keep measure at their start
            curr_offset += dur_q

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        return self._items[idx]

    def to_list(self) -> list[dict[str, Any]]:
        return list(self._items)


def build_metric_grid(
    time_signature: Any = "4/4",
    durations: Sequence[str | float | int] | None = None,
    pitches: Sequence[int] | None = None,
    notes: Sequence[Any] | None = None,
) -> MetricGrid:
    """Factory helper to construct a MetricGrid instance."""
    return MetricGrid(
        time_signature=time_signature,
        durations=durations,
        pitches=pitches,
        notes=notes,
    )

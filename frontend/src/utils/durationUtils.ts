/**
 * Utility functions and data structures for note durations, metric calculations, and downbeats.
 */

export interface MelodyNote {
  pitch: number;
  name: string;
  duration: string; // "whole" | "dotted_half" | "half" | "dotted_quarter" | "quarter" | "dotted_eighth" | "eighth"
  is_downbeat: boolean;
}

export interface DurationOption {
  id: string;
  label: string;
  hint: string;
  beats: number;
}

export const DURATIONS: DurationOption[] = [
  { id: "whole", label: "1", hint: "Целая", beats: 4 },
  { id: "dotted_half", label: "3/4", hint: "Половинная с точкой", beats: 3 },
  { id: "half", label: "1/2", hint: "Половинная", beats: 2 },
  { id: "dotted_quarter", label: "3/8", hint: "Четверть с точкой", beats: 1.5 },
  { id: "quarter", label: "1/4", hint: "Четверть", beats: 1 },
  { id: "dotted_eighth", label: "3/16", hint: "Восьмая с точкой", beats: 0.75 },
  { id: "eighth", label: "1/8", hint: "Восьмая", beats: 0.5 },
];

export const DURATION_BEATS_MAP: Record<string, number> = {
  whole: 4,
  dotted_half: 3,
  half: 2,
  dotted_quarter: 1.5,
  quarter: 1,
  dotted_eighth: 0.75,
  eighth: 0.5,
};

/**
 * Recalculates downbeats according to current time signature and accumulated beat offsets.
 * Only primary measure boundaries (offset 0.0) are marked as downbeats (accented) for harmonization.
 */
export function recalculateDownbeats(
  notes: MelodyNote[],
  timeSignature: string = "4/4"
): MelodyNote[] {
  const parts = timeSignature.split("/");
  const beats = parseInt(parts[0], 10) || 4;
  const beatType = parseInt(parts[1], 10) || 4;
  const measureQuarters = beats * (4.0 / beatType);

  let currentOffset = 0.0;
  return notes.map((note) => {
    while (currentOffset >= measureQuarters - 1e-4) {
      currentOffset -= measureQuarters;
    }
    if (Math.abs(currentOffset) < 1e-4) {
      currentOffset = 0.0;
    }

    // Only a measure start is a harmonization downbeat; secondary accents
    // stay unaccented so passing tones can serve as NCTs.
    const isDownbeat = Math.abs(currentOffset) < 1e-4;

    const dur = DURATION_BEATS_MAP[note.duration] ?? 2;
    currentOffset += dur;

    return {
      ...note,
      is_downbeat: isDownbeat,
    };
  });
}

const PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

/**
 * Converts a MIDI pitch number (e.g. 60) to a musical note name (e.g. C4).
 */
export function midiToNoteName(pitch: number): string {
  const octave = Math.floor(pitch / 12) - 1;
  const noteIndex = pitch % 12;
  return `${PITCH_NAMES[noteIndex]}${octave}`;
}

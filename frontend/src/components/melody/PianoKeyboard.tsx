import React, { useState } from "react";
import { audioEngine } from "../../audio/synth";
import { midiToNoteName } from "../../utils/durationUtils";

interface PianoKeyboardProps {
  onNoteTrigger: (pitch: number, name: string) => void;
  activePitch?: number | null;
}

/** Piano range C3–C6 (MIDI 48–84), as in the pre-redesign MelodyInput. */
const START_PITCH = 48;
const END_PITCH = 84;

const BLACK_KEY_OFFSETS: Record<number, number> = {
  1: 14, // C#
  3: 42, // D#
  6: 84, // F#
  8: 112, // G#
  10: 140, // A#
};

export const PianoKeyboard: React.FC<PianoKeyboardProps> = ({
  onNoteTrigger,
  activePitch,
}) => {
  const [focusedPitch, setFocusedPitch] = useState<number>(60);

  const handleKeyClick = (pitch: number) => {
    const noteName = midiToNoteName(pitch);
    audioEngine.playNote(0, pitch, 0.4);
    onNoteTrigger(pitch, noteName);
  };

  const focusPitch = (pitch: number) => {
    const clamped = Math.min(END_PITCH, Math.max(START_PITCH, pitch));
    setFocusedPitch(clamped);
    const el = document.querySelector<HTMLButtonElement>(
      `button[data-pitch="${clamped}"]`
    );
    el?.focus();
  };

  // Keyboard navigation: arrows move by semitone, Home/End jump to range edges.
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      focusPitch(focusedPitch + 1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      focusPitch(focusedPitch - 1);
    } else if (e.key === "Home") {
      e.preventDefault();
      focusPitch(START_PITCH);
    } else if (e.key === "End") {
      e.preventDefault();
      focusPitch(END_PITCH);
    }
  };

  const whiteKeyClass = (isPressed: boolean) =>
    `w-7 h-28 border rounded-b-md transition-colors flex flex-col justify-end items-center pb-1 text-[10px] font-mono cursor-pointer focus-ring ${
      isPressed
        ? "bg-brand/30 border-brand text-brand"
        : "bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300"
    }`;

  const blackKeyClass = (isPressed: boolean) =>
    `absolute top-0 w-4 h-16 rounded-b-sm border transition-colors cursor-pointer z-10 focus-ring ${
      isPressed
        ? "bg-brand border-brand shadow-md shadow-brand/50"
        : "bg-slate-900 hover:bg-slate-800 border-slate-950"
    }`;

  const keyProps = (pitch: number) => ({
    "data-pitch": pitch,
    tabIndex: pitch === focusedPitch ? 0 : -1,
    onFocus: () => setFocusedPitch(pitch),
  });

  // Group into octaves for structured rendering (C3, C4, C5 + final C6)
  const octaves = [3, 4, 5];

  return (
    <div
      className="w-full select-none overflow-x-auto pb-2"
      role="group"
      aria-label="Пианино C3–C6: стрелки влево/вправо — выбор клавиши, Enter — добавить ноту"
      onKeyDown={handleKeyDown}
    >
      <div className="flex items-start w-max mx-auto min-w-[580px] bg-surface-panel p-2 rounded-xl border border-border shadow-inner">
        {octaves.map((octave) => {
          const basePitch = (octave + 1) * 12; // C3=48, C4=60, C5=72
          const whiteNotes = [0, 2, 4, 5, 7, 9, 11]; // C, D, E, F, G, A, B
          const blackNotes = [1, 3, 6, 8, 10]; // C#, D#, F#, G#, A#

          return (
            <div key={octave} className="relative flex">
              {/* White keys */}
              {whiteNotes.map((semitone) => {
                const pitch = basePitch + semitone;
                const isPressed = activePitch === pitch;
                const noteName = midiToNoteName(pitch);

                return (
                  <button
                    key={pitch}
                    type="button"
                    aria-label={`Клавиша ${noteName}`}
                    onClick={() => handleKeyClick(pitch)}
                    className={whiteKeyClass(isPressed)}
                    {...keyProps(pitch)}
                  >
                    {semitone === 0 ? `C${octave}` : ""}
                  </button>
                );
              })}

              {/* Black keys */}
              {blackNotes.map((semitone) => {
                const pitch = basePitch + semitone;
                const isPressed = activePitch === pitch;
                const noteName = midiToNoteName(pitch);
                const leftOffset = BLACK_KEY_OFFSETS[semitone] || 0;

                return (
                  <button
                    key={pitch}
                    type="button"
                    aria-label={`Клавиша ${noteName}`}
                    onClick={() => handleKeyClick(pitch)}
                    style={{ left: `${leftOffset}px` }}
                    className={blackKeyClass(isPressed)}
                    {...keyProps(pitch)}
                  />
                );
              })}
            </div>
          );
        })}

        {/* Final C6 key */}
        <button
          type="button"
          aria-label={`Клавиша C6`}
          onClick={() => handleKeyClick(END_PITCH)}
          className={whiteKeyClass(activePitch === END_PITCH)}
          {...keyProps(END_PITCH)}
        >
          C6
        </button>
      </div>
    </div>
  );
};

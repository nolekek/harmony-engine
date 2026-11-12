import React from "react";
import { audioEngine } from "../../audio/synth";
import { midiToNoteName } from "../../utils/durationUtils";

interface PianoKeyboardProps {
  onNoteTrigger: (pitch: number, name: string) => void;
  activePitch?: number | null;
}

const BLACK_KEY_OFFSETS: Record<number, number> = {
  1: 14,  // C#
  3: 42,  // D#
  6: 84,  // F#
  8: 112, // G#
  10: 140,// A#
};

export const PianoKeyboard: React.FC<PianoKeyboardProps> = ({
  onNoteTrigger,
  activePitch,
}) => {
  const handleKeyClick = (pitch: number) => {
    const noteName = midiToNoteName(pitch);
    audioEngine.playSingleTone(pitch, 0.4);
    onNoteTrigger(pitch, noteName);
  };

  // Group into octaves for structured rendering
  const octaves = [3, 4, 5];

  return (
    <div className="w-full select-none overflow-x-auto pb-2">
      <div className="flex items-start justify-center min-w-[580px] bg-slate-950 p-2 rounded-xl border border-slate-800 shadow-inner">
        {octaves.map((octave) => {
          const basePitch = (octave + 1) * 12; // C3=48, C4=60, C5=72
          const whiteNotes = [0, 2, 4, 5, 7, 9, 11]; // C, D, E, F, G, A, B
          const blackNotes = [1, 3, 6, 8, 10];      // C#, D#, F#, G#, A#

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
                    className={`w-7 h-28 border border-slate-300 rounded-b-md transition-colors flex flex-col justify-end items-center pb-1 text-[10px] font-mono cursor-pointer focus-ring ${
                      isPressed
                        ? "bg-indigo-300 text-indigo-950"
                        : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                    }`}
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
                    className={`absolute top-0 w-4 h-16 rounded-b-sm border border-slate-900 transition-colors cursor-pointer z-10 focus-ring ${
                      isPressed
                        ? "bg-indigo-600 shadow-md shadow-indigo-500/50"
                        : "bg-slate-900 hover:bg-slate-800"
                    }`}
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
          className={`w-7 h-28 border border-slate-300 rounded-b-md transition-colors flex flex-col justify-end items-center pb-1 text-[10px] font-mono cursor-pointer focus-ring ${
            activePitch === END_PITCH
              ? "bg-indigo-300 text-indigo-950"
              : "bg-slate-100 hover:bg-slate-200 text-slate-700"
          }`}
        >
          C6
        </button>
      </div>
    </div>
  );
};

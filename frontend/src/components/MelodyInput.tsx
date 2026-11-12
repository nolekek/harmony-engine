import React, { useState, useEffect } from "react";
import { Piano, Clock, Sparkles } from "lucide-react";
import { Card } from "./ui/Card";
import { PianoKeyboard } from "./melody/PianoKeyboard";
import { MidiInputBar } from "./melody/MidiInputBar";
import { NoteList } from "./melody/NoteList";
import { MelodyFileUpload } from "./melody/MelodyFileUpload";
import {
  DURATIONS,
  recalculateDownbeats,
  midiToNoteName,
} from "../utils/durationUtils";
import type { MelodyNote } from "../utils/durationUtils";

export type { MelodyNote };

interface MelodyInputProps {
  melody: MelodyNote[];
  onChange: (newMelody: MelodyNote[]) => void;
  selectedKey: { tonic: string; mode: string };
  onAutoDetectKey: () => void;
  timeSignature?: string;
}

const DEFAULT_SAMPLE_MELODY: MelodyNote[] = [
  { pitch: 64, name: "E4", duration: "half", is_downbeat: true },
  { pitch: 65, name: "F4", duration: "half", is_downbeat: false },
  { pitch: 67, name: "G4", duration: "half", is_downbeat: true },
  { pitch: 64, name: "E4", duration: "half", is_downbeat: false },
  { pitch: 62, name: "D4", duration: "half", is_downbeat: true },
  { pitch: 60, name: "C4", duration: "whole", is_downbeat: false },
];

export const MelodyInput: React.FC<MelodyInputProps> = ({
  melody,
  onChange,
  onAutoDetectKey,
  timeSignature = "4/4",
}) => {
  const [activeDuration, setActiveDuration] = useState<string>("half");
  const [recentPitch, setRecentPitch] = useState<number | null>(null);

  // Recalculate downbeats whenever meter changes
  useEffect(() => {
    if (melody.length > 0) {
      const recalculated = recalculateDownbeats(melody, timeSignature);
      const isChanged = recalculated.some(
        (n, i) => n.is_downbeat !== melody[i]?.is_downbeat
      );
      if (isChanged) {
        onChange(recalculated);
      }
    }
  }, [timeSignature, melody, onChange]);

  const handleAddNote = (pitch: number, name?: string) => {
    const noteName = name || midiToNoteName(pitch);
    setRecentPitch(pitch);
    setTimeout(() => setRecentPitch(null), 250);

    const newNote: MelodyNote = {
      pitch,
      name: noteName,
      duration: activeDuration,
      is_downbeat: false, // will be recalculated
    };

    const nextMelody = [...melody, newNote];
    onChange(recalculateDownbeats(nextMelody, timeSignature));
  };

  const handleLoadSample = () => {
    onChange(recalculateDownbeats(DEFAULT_SAMPLE_MELODY, timeSignature));
  };

  const handleClear = () => {
    onChange([]);
  };

  const handleLoadedFromFile = (
    loadedNotes: MelodyNote[],
    loadedTs?: string
  ) => {
    const targetTs = loadedTs || timeSignature;
    onChange(recalculateDownbeats(loadedNotes, targetTs));
    if (onAutoDetectKey) {
      setTimeout(onAutoDetectKey, 100);
    }
  };

  return (
    <Card
      title="Ввод мелодии (Soprano)"
      subtitle="Интерактивная клавиатура, MIDI-контроллер или файлы партитур"
      badge={
        <div className="w-8 h-8 rounded-lg bg-indigo-950 border border-indigo-700/60 flex items-center justify-center text-indigo-400">
          <Piano className="w-4 h-4" />
        </div>
      }
      className="border-slate-800"
    >
      <div className="space-y-4">
        {/* WebMIDI device status */}
        <MidiInputBar onNoteReceived={(pitch) => handleAddNote(pitch)} />

        {/* Duration selector for subsequent note input */}
        <div className="flex flex-wrap items-center gap-1.5 p-2 bg-slate-950/70 border border-slate-800 rounded-lg">
          <div className="flex items-center gap-1 text-xs text-slate-400 mr-1">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            <span className="font-medium">Длительность:</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {DURATIONS.map((dur) => (
              <button
                key={dur.id}
                type="button"
                onClick={() => setActiveDuration(dur.id)}
                className={`px-2 py-0.5 rounded text-xs font-mono font-medium border transition-colors cursor-pointer focus-ring ${
                  activeDuration === dur.id
                    ? "bg-indigo-600 border-indigo-500 text-white shadow-sm shadow-indigo-600/30"
                    : "bg-slate-900 border-slate-800 text-slate-300 hover:text-white hover:border-slate-700"
                }`}
                title={dur.hint}
              >
                {dur.label}
              </button>
            ))}
          </div>
        </div>

        {/* Visual Piano Keyboard */}
        <PianoKeyboard
          onNoteTrigger={(pitch, name) => handleAddNote(pitch, name)}
          activePitch={recentPitch}
        />

        {/* Note List / Chips */}
        <NoteList
          melody={melody}
          onChange={onChange}
          onClear={handleClear}
          onSelectSample={handleLoadSample}
        />

        {/* File and text upload options */}
        <MelodyFileUpload onMelodyLoaded={handleLoadedFromFile} />
      </div>
    </Card>
  );
};

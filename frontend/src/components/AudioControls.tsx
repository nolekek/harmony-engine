import React, { useState } from "react";
import {
  Play,
  Square,
  Volume2,
  VolumeX,
  Headphones,
  SlidersHorizontal,
} from "lucide-react";
import { audioEngine } from "../audio/synth";
import type { InstrumentPreset, SATBVoicing } from "../audio/synth";

interface AudioControlsProps {
  voicings: SATBVoicing[];
  currentChordIndex: number;
  onStepChange: (index: number) => void;
}

const VOICES = [
  { index: 0, label: "Сопрано (S)", color: "border-blue-500 text-blue-400 bg-blue-950/40" },
  { index: 1, label: "Альт (A)", color: "border-green-500 text-green-400 bg-green-950/40" },
  { index: 2, label: "Тенор (T)", color: "border-orange-500 text-orange-400 bg-orange-950/40" },
  { index: 3, label: "Бас (B)", color: "border-red-500 text-red-400 bg-red-950/40" },
];

export const AudioControls: React.FC<AudioControlsProps> = ({
  voicings,
  currentChordIndex: _currentChordIndex,
  onStepChange,
}) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [bpm, setBpm] = useState<number>(76);
  const [preset, setPreset] = useState<InstrumentPreset>("piano");
  const [mutes, setMutes] = useState<[boolean, boolean, boolean, boolean]>([
    false,
    false,
    false,
    false,
  ]);
  const [solos, setSolos] = useState<[boolean, boolean, boolean, boolean]>([
    false,
    false,
    false,
    false,
  ]);

  const handlePlayToggle = () => {
    if (isPlaying) {
      audioEngine.stop();
      setIsPlaying(false);
      onStepChange(-1);
    } else {
      if (!voicings || voicings.length === 0) return;
      setIsPlaying(true);
      audioEngine.playSequence(
        voicings,
        bpm,
        (idx) => {
          onStepChange(idx);
        },
        () => {
          setIsPlaying(false);
          onStepChange(-1);
        }
      );
    }
  };

  const handlePresetChange = (newPreset: InstrumentPreset) => {
    setPreset(newPreset);
    audioEngine.setPreset(newPreset);
  };

  const toggleMute = (idx: number) => {
    const nextMutes = [...mutes] as [boolean, boolean, boolean, boolean];
    nextMutes[idx] = !nextMutes[idx];
    setMutes(nextMutes);
    audioEngine.setMute(idx, nextMutes[idx]);
  };

  const toggleSolo = (idx: number) => {
    const nextSolos = [...solos] as [boolean, boolean, boolean, boolean];
    nextSolos[idx] = !nextSolos[idx];
    setSolos(nextSolos);
    audioEngine.setSolo(idx, nextSolos[idx]);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg space-y-4">
      {/* Playback & Instrument bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Play/Stop + BPM */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handlePlayToggle}
            disabled={!voicings || voicings.length === 0}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all shadow-md active:scale-95 ${
              isPlaying
                ? "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/30"
                : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30 disabled:opacity-40 disabled:pointer-events-none"
            }`}
          >
            {isPlaying ? (
              <>
                <Square className="w-4 h-4 fill-white" />
                <span>Стоп</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Слушать 4 голоса</span>
              </>
            )}
          </button>

          {/* BPM */}
          <div className="flex items-center gap-2 bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700">
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs text-slate-300 font-mono">BPM:</span>
            <input
              type="number"
              min="40"
              max="180"
              value={bpm}
              onChange={(e) => setBpm(Number(e.target.value) || 76)}
              className="w-12 bg-slate-900 text-xs font-mono font-bold text-center text-slate-100 rounded border border-slate-700 py-0.5"
            />
          </div>
        </div>

        {/* Preset Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Звучание:</span>
          <div className="inline-flex rounded-lg bg-slate-800 p-0.5 border border-slate-700">
            {(["piano", "choir", "organ"] as InstrumentPreset[]).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => handlePresetChange(p)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                  preset === p
                    ? "bg-indigo-600 text-white shadow"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {p === "piano" && "Фортепиано"}
                {p === "choir" && "Хоровой пад"}
                {p === "organ" && "Орган"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Voice Strips: Solo / Mute per Voice */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
        {VOICES.map((v) => {
          const isMuted = mutes[v.index];
          const isSoloed = solos[v.index];
          return (
            <div
              key={v.index}
              className={`p-2.5 rounded-lg border flex flex-col justify-between gap-2 ${v.color} ${
                isMuted ? "opacity-40 grayscale" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold">{v.label}</span>
                {isSoloed && (
                  <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded bg-amber-500 text-slate-950">
                    Solo
                  </span>
                )}
              </div>

              <div className="flex items-center gap-1.5 pt-1">
                <button
                  type="button"
                  onClick={() => toggleMute(v.index)}
                  className={`flex-1 flex items-center justify-center gap-1 py-1 rounded text-[11px] font-semibold border transition-colors ${
                    isMuted
                      ? "bg-rose-900/60 border-rose-700 text-rose-200"
                      : "bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-300"
                  }`}
                  title="Заглушить голос"
                >
                  {isMuted ? (
                    <VolumeX className="w-3 h-3 text-rose-400" />
                  ) : (
                    <Volume2 className="w-3 h-3 text-slate-400" />
                  )}
                  <span>Mute</span>
                </button>

                <button
                  type="button"
                  onClick={() => toggleSolo(v.index)}
                  className={`flex-1 flex items-center justify-center gap-1 py-1 rounded text-[11px] font-semibold border transition-colors ${
                    isSoloed
                      ? "bg-amber-600 border-amber-500 text-slate-950 font-bold"
                      : "bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-300"
                  }`}
                  title="Солировать голос"
                >
                  <Headphones className="w-3 h-3" />
                  <span>Solo</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

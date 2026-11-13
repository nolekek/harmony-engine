import React, { useEffect, useState } from "react";
import {
  Play,
  Square,
  Volume2,
  VolumeX,
  Headphones,
  SlidersHorizontal,
  SkipBack,
  SkipForward,
} from "lucide-react";
import { audioEngine } from "../audio/synth";
import type { InstrumentPreset, SATBVoicing } from "../audio/synth";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";

interface AudioControlsProps {
  voicings: SATBVoicing[];
  currentChordIndex: number;
  onStepChange: (index: number) => void;
}

/* SATB voice identity colors (kept recognizable in both themes). */
const VOICES = [
  { index: 0, label: "Сопрано (S)", color: "border-blue-500/60 text-blue-700 dark:text-blue-400 bg-blue-500/10" },
  { index: 1, label: "Альт (A)", color: "border-green-500/60 text-green-700 dark:text-green-400 bg-green-500/10" },
  { index: 2, label: "Тенор (T)", color: "border-orange-500/60 text-orange-700 dark:text-orange-400 bg-orange-500/10" },
  { index: 3, label: "Бас (B)", color: "border-red-500/60 text-red-700 dark:text-red-400 bg-red-500/10" },
];

export const AudioControls: React.FC<AudioControlsProps> = ({
  voicings,
  currentChordIndex,
  onStepChange,
}) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [bpm, setBpm] = useState<number>(76);
  const [preset, setPreset] = useState<InstrumentPreset>("piano");
  const [mutes, setMutes] = useState<[boolean, boolean, boolean, boolean]>([
    false, false, false, false,
  ]);
  const [solos, setSolos] = useState<[boolean, boolean, boolean, boolean]>([
    false, false, false, false,
  ]);

  // Unmount (tab switch) must silence playback: the engine is a module singleton.
  useEffect(() => {
    return () => {
      audioEngine.stop();
    };
  }, []);

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

  // Manual transport: step back/forward through chord slices with cursor sync.
  const handleStep = (dir: -1 | 1) => {
    if (!voicings || voicings.length === 0) return;
    audioEngine.stop();
    setIsPlaying(false);
    const base = currentChordIndex >= 0 ? currentChordIndex : dir > 0 ? -1 : 0;
    const next = Math.min(voicings.length - 1, Math.max(0, base + dir));
    audioEngine.playChord(voicings[next], 1.0);
    onStepChange(next);
  };

  const handleBpmChange = (value: number) => {
    setBpm(Math.min(200, Math.max(40, value || 76)));
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

  const hasVoicings = !!voicings && voicings.length > 0;

  return (
    <div className="bg-surface-card border border-border rounded-xl p-4 shadow-lg space-y-4">
      {/* Playback & Instrument bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Play/Stop + Step transport + BPM */}
        <div className="flex items-center gap-3 flex-wrap">
          <Button
            variant={isPlaying ? "danger" : "success"}
            size="md"
            onClick={handlePlayToggle}
            disabled={!hasVoicings}
            icon={
              isPlaying ? (
                <Square className="w-4 h-4 fill-white" />
              ) : (
                <Play className="w-4 h-4 fill-white" />
              )
            }
          >
            {isPlaying ? "Стоп" : "Слушать 4 голоса"}
          </Button>

          <div className="flex items-center gap-1" role="group" aria-label="Пошаговый транспорт">
            <Button
              variant="secondary"
              size="xs"
              onClick={() => handleStep(-1)}
              disabled={!hasVoicings}
              aria-label="Шаг назад (предыдущий аккорд)"
              title="Шаг назад"
              icon={<SkipBack className="w-3.5 h-3.5" />}
            />
            <Button
              variant="secondary"
              size="xs"
              onClick={() => handleStep(1)}
              disabled={!hasVoicings}
              aria-label="Шаг вперёд (следующий аккорд)"
              title="Шаг вперёд"
              icon={<SkipForward className="w-3.5 h-3.5" />}
            />
          </div>

          {/* BPM 40–200 */}
          <div className="flex items-center gap-2 bg-surface-elevated px-3 py-1.5 rounded-lg border border-border">
            <SlidersHorizontal className="w-3.5 h-3.5 text-text-muted" />
            <label htmlFor="audio-bpm" className="text-xs text-text-secondary font-mono">
              BPM:
            </label>
            <div className="w-16 shrink-0">
              <Input
                id="audio-bpm"
                type="number"
                min={40}
                max={200}
                value={bpm}
                onChange={(e) => handleBpmChange(Number(e.target.value))}
                inputSize="sm"
                className="w-full text-center font-mono font-bold"
              />
            </div>
          </div>
        </div>

        {/* Preset Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted font-medium">Звучание:</span>
          <div className="inline-flex rounded-lg bg-surface-elevated p-0.5 border border-border" role="group" aria-label="Инструментальный пресет">
            {(["piano", "choir", "organ"] as InstrumentPreset[]).map((p) => (
              <Button
                key={p}
                variant="ghost"
                size="xs"
                onClick={() => handlePresetChange(p)}
                aria-pressed={preset === p}
                selected={preset === p}
                selectedClass="border border-transparent bg-brand text-white shadow-sm"
              >
                {p === "piano" && "Фортепиано"}
                {p === "choir" && "Хоровой пад"}
                {p === "organ" && "Орган"}
              </Button>
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
                <Button
                  variant="secondary"
                  size="xs"
                  onClick={() => toggleMute(v.index)}
                  aria-pressed={isMuted}
                  selected={isMuted}
                  selectedClass="border border-rose-600/60 bg-rose-600/20 text-rose-700 dark:text-rose-200"
                  className="flex-1"
                  title="Заглушить голос"
                  icon={
                    isMuted ? (
                      <VolumeX className="w-3 h-3 text-rose-600 dark:text-rose-400" />
                    ) : (
                      <Volume2 className="w-3 h-3 text-text-muted" />
                    )
                  }
                >
                  Mute
                </Button>

                <Button
                  variant="secondary"
                  size="xs"
                  onClick={() => toggleSolo(v.index)}
                  aria-pressed={isSoloed}
                  selected={isSoloed}
                  selectedClass="border border-amber-400 bg-amber-500 text-slate-950"
                  className="flex-1"
                  title="Солировать голос"
                  icon={<Headphones className="w-3 h-3" />}
                >
                  Solo
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

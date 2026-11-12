import React from "react";
import { Trash2, Volume2, Sparkles } from "lucide-react";
import { Button } from "../ui/Button";
import { audioEngine } from "../../audio/synth";
import { DURATIONS } from "../../utils/durationUtils";
import type { MelodyNote } from "../../utils/durationUtils";

interface NoteListProps {
  melody: MelodyNote[];
  onChange: (newMelody: MelodyNote[]) => void;
  onClear: () => void;
  onSelectSample: () => void;
}

export const NoteList: React.FC<NoteListProps> = ({
  melody,
  onChange,
  onClear,
  onSelectSample,
}) => {
  const handleDurationChange = (index: number, newDur: string) => {
    const next = [...melody];
    next[index] = { ...next[index], duration: newDur };
    onChange(next);
  };

  const handleToggleDownbeat = (index: number) => {
    const next = [...melody];
    next[index] = { ...next[index], is_downbeat: !next[index].is_downbeat };
    onChange(next);
  };

  const handleDelete = (index: number) => {
    const next = melody.filter((_, i) => i !== index);
    onChange(next);
  };

  const handlePlaySingle = (pitch: number) => {
    audioEngine.playSingleTone(pitch, 0.4);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-slate-400 pb-1 border-b border-slate-800">
        <span className="font-semibold uppercase tracking-wider text-slate-300">
          Мелодия ({melody.length} {melody.length === 1 ? "нота" : melody.length < 5 ? "ноты" : "нот"})
        </span>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="xs"
            onClick={onSelectSample}
            icon={<Sparkles className="w-3 h-3 text-indigo-400" />}
          >
            Пример
          </Button>
          {melody.length > 0 && (
            <Button
              variant="ghost"
              size="xs"
              onClick={onClear}
              className="text-rose-400 hover:text-rose-300"
              icon={<Trash2 className="w-3 h-3" />}
            >
              Очистить
            </Button>
          )}
        </div>
      </div>

      {melody.length === 0 ? (
        <div className="py-6 text-center text-xs text-slate-500 italic bg-slate-950/40 rounded-lg border border-dashed border-slate-800">
          Мелодия пуста. Нажимайте клавиши на пианино выше или загрузите файл.
        </div>
      ) : (
        <div className="max-h-56 overflow-y-auto space-y-1 pr-1">
          {melody.map((note, idx) => (
            <div
              key={`${idx}-${note.pitch}`}
              className="flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-lg bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition-colors text-xs"
            >
              {/* Note name & play button */}
              <div className="flex items-center gap-2">
                <span className="w-5 font-mono text-[11px] text-slate-500 text-right">
                  {idx + 1}.
                </span>
                <button
                  type="button"
                  onClick={() => handlePlaySingle(note.pitch)}
                  aria-label={`Воспроизвести ${note.name}`}
                  className="font-mono font-bold text-indigo-300 hover:text-indigo-200 flex items-center gap-1 focus-ring"
                >
                  <Volume2 className="w-3 h-3 text-indigo-400" />
                  <span>{note.name}</span>
                </button>
                <span className="text-[10px] text-slate-500 font-mono">
                  ({note.pitch})
                </span>
              </div>

              {/* Duration selector & Downbeat switch */}
              <div className="flex items-center gap-1.5">
                <select
                  value={note.duration}
                  aria-label={`Длительность ноты ${note.name}`}
                  onChange={(e) => handleDurationChange(idx, e.target.value)}
                  className="bg-slate-900 border border-slate-700 text-slate-200 px-1.5 py-0.5 rounded text-[11px] font-mono focus-ring"
                >
                  {DURATIONS.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.label} ({d.hint})
                    </option>
                  ))}
                </select>

                <button
                  type="button"
                  aria-label={note.is_downbeat ? "Сильная доля" : "Слабая доля"}
                  onClick={() => handleToggleDownbeat(idx)}
                  className={`px-1.5 py-0.5 rounded text-[10px] font-mono border transition-colors cursor-pointer focus-ring ${
                    note.is_downbeat
                      ? "bg-amber-950/80 border-amber-600 text-amber-300 font-bold"
                      : "bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-400"
                  }`}
                  title={note.is_downbeat ? "Сильная доля (акцент)" : "Слабая доля"}
                >
                  {note.is_downbeat ? "СД" : "сл"}
                </button>

                <button
                  type="button"
                  aria-label={`Удалить ноту ${note.name}`}
                  onClick={() => handleDelete(idx)}
                  className="p-1 rounded text-slate-500 hover:text-rose-400 transition-colors focus-ring cursor-pointer"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

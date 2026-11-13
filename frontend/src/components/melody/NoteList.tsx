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
    audioEngine.playNote(0, pitch, 0.4);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-text-muted pb-1 border-b border-border-subtle">
        <span className="font-semibold uppercase tracking-wider text-text-secondary">
          Мелодия ({melody.length} {melody.length === 1 ? "нота" : melody.length < 5 ? "ноты" : "нот"})
        </span>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="xs"
            onClick={onSelectSample}
            icon={<Sparkles className="w-3 h-3 text-brand" />}
          >
            Пример
          </Button>
          {melody.length > 0 && (
            <Button
              variant="ghost"
              size="xs"
              onClick={onClear}
              className="text-rose-600 dark:text-rose-400 hover:text-rose-500 dark:hover:text-rose-300"
              icon={<Trash2 className="w-3 h-3" />}
            >
              Очистить
            </Button>
          )}
        </div>
      </div>

      {melody.length === 0 ? (
        <div className="py-6 text-center text-xs text-text-muted italic bg-surface-subtle/40 rounded-lg border border-dashed border-border">
          Мелодия пуста. Нажимайте клавиши на пианино выше или загрузите файл.
        </div>
      ) : (
        /* No nested vertical scrollbox: the whole left panel scrolls as one. */
        <div className="space-y-1">
          {melody.map((note, idx) => (
            <div
              key={`${idx}-${note.pitch}`}
              className="flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-lg bg-surface-panel/70 border border-border-subtle hover:border-border transition-colors text-xs"
            >
              {/* Note name & play button */}
              <div className="flex items-center gap-2">
                <span className="w-5 font-mono text-[11px] text-text-muted text-right">
                  {idx + 1}.
                </span>
                <button
                  type="button"
                  onClick={() => handlePlaySingle(note.pitch)}
                  aria-label={`Воспроизвести ${note.name}`}
                  className="font-mono font-bold text-brand hover:text-brand-hover flex items-center gap-1 focus-ring rounded cursor-pointer"
                >
                  <Volume2 className="w-3 h-3 text-brand" />
                  <span>{note.name}</span>
                </button>
                <span className="text-[10px] text-text-muted font-mono">
                  ({note.pitch})
                </span>
              </div>

              {/* Duration selector & Downbeat switch */}
              <div className="flex items-center gap-1.5">
                <select
                  value={note.duration}
                  aria-label={`Длительность ноты ${note.name}`}
                  onChange={(e) => handleDurationChange(idx, e.target.value)}
                  className="bg-surface-panel border border-border text-text-primary px-1.5 py-0.5 rounded text-[11px] font-mono focus-ring cursor-pointer"
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
                      ? "bg-amber-500/15 border-amber-600/60 text-amber-700 dark:text-amber-300 font-bold"
                      : "bg-surface-panel border-border text-text-muted hover:text-text-secondary"
                  }`}
                  title={note.is_downbeat ? "Сильная доля (акцент)" : "Слабая доля"}
                >
                  {note.is_downbeat ? "СД" : "сл"}
                </button>

                <button
                  type="button"
                  aria-label={`Удалить ноту ${note.name}`}
                  onClick={() => handleDelete(idx)}
                  className="p-1 rounded text-text-muted hover:text-rose-500 dark:hover:text-rose-400 transition-colors focus-ring cursor-pointer"
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

import React from "react";
import type { SATBVoicing } from "../../audio/synth";
import { Button } from "../ui/Button";

interface GraderScoreMatrixProps {
  voicings: SATBVoicing[];
  onVoicePitchChange: (
    chordIdx: number,
    voice: "soprano" | "alto" | "tenor" | "bass",
    val: number
  ) => void;
  onAddChord: () => void;
  onRemoveChord: () => void;
}

/* SATB identity colors, AA-readable in both themes. */
const VOICE_ROWS: Array<{
  key: "soprano" | "alto" | "tenor" | "bass";
  label: string;
  badgeClass: string;
  textClass: string;
}> = [
  { key: "soprano", label: "Сопрано (S)", badgeClass: "bg-blue-500/10", textClass: "text-blue-700 dark:text-blue-300" },
  { key: "alto", label: "Альт (A)", badgeClass: "bg-emerald-500/10", textClass: "text-emerald-700 dark:text-emerald-300" },
  { key: "tenor", label: "Тенор (T)", badgeClass: "bg-amber-500/10", textClass: "text-amber-700 dark:text-amber-300" },
  { key: "bass", label: "Бас (B)", badgeClass: "bg-rose-500/10", textClass: "text-rose-700 dark:text-rose-300" },
];

export const GraderScoreMatrix: React.FC<GraderScoreMatrixProps> = ({
  voicings,
  onVoicePitchChange,
  onAddChord,
  onRemoveChord,
}) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-text-secondary">
          Сетка аккордов (MIDI-ноты 4 голосов):
        </span>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="xs" onClick={onAddChord}>
            + Добавить аккорд
          </Button>
          {voicings.length > 2 && (
            <Button
              variant="secondary"
              size="xs"
              onClick={onRemoveChord}
              className="text-rose-600 dark:text-rose-400 hover:text-rose-500 dark:hover:text-rose-300"
            >
              - Удалить последний
            </Button>
          )}
        </div>
      </div>

      <div className="overflow-x-auto border border-border rounded-lg">
        <table className="w-full text-xs text-left">
          <thead className="bg-surface-elevated text-text-secondary font-mono">
            <tr>
              <th className="p-2 border-r border-border">Голос</th>
              {voicings.map((_, idx) => (
                <th key={idx} className="p-2 text-center border-r border-border-subtle min-w-[54px]">
                  #{idx + 1}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle font-mono">
            {VOICE_ROWS.map(({ key, label, badgeClass, textClass }) => (
              <tr key={key} className={badgeClass}>
                <td className={`p-2 font-bold border-r border-border-subtle shrink-0 ${textClass}`}>
                  {label}
                </td>
                {voicings.map((v, i) => (
                  <td key={i} className="p-1 border-r border-border-subtle">
                    <input
                      type="number"
                      aria-label={`${label}, аккорд #${i + 1}`}
                      value={v[key]}
                      onChange={(e) =>
                        onVoicePitchChange(i, key, Number(e.target.value))
                      }
                      className={`w-full text-center bg-surface-panel border border-border rounded px-1 py-1 ${textClass} font-bold focus-ring`}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

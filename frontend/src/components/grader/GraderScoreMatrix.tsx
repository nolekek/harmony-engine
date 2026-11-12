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

const VOICE_ROWS: Array<{
  key: "soprano" | "alto" | "tenor" | "bass";
  label: string;
  badgeClass: string;
  textClass: string;
}> = [
  { key: "soprano", label: "Сопрано (S)", badgeClass: "bg-blue-950/40 text-blue-400", textClass: "text-blue-300" },
  { key: "alto", label: "Альт (A)", badgeClass: "bg-emerald-950/40 text-emerald-400", textClass: "text-emerald-300" },
  { key: "tenor", label: "Тенор (T)", badgeClass: "bg-amber-950/40 text-amber-400", textClass: "text-amber-300" },
  { key: "bass", label: "Бас (B)", badgeClass: "bg-rose-950/40 text-rose-400", textClass: "text-rose-300" },
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
        <span className="text-xs font-semibold text-slate-300">
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
              className="text-rose-400 hover:text-rose-300"
            >
              - Удалить последний
            </Button>
          )}
        </div>
      </div>

      <div className="overflow-x-auto border border-slate-800 rounded-lg">
        <table className="w-full text-xs text-left">
          <thead className="bg-slate-800/80 text-slate-400 font-mono">
            <tr>
              <th className="p-2 border-r border-slate-700">Голос</th>
              {voicings.map((_, idx) => (
                <th key={idx} className="p-2 text-center border-r border-slate-700/60 min-w-[54px]">
                  #{idx + 1}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/70 font-mono">
            {VOICE_ROWS.map(({ key, label, badgeClass, textClass }) => (
              <tr key={key} className={badgeClass}>
                <td className="p-2 font-bold border-r border-slate-800 shrink-0">
                  {label}
                </td>
                {voicings.map((v, i) => (
                  <td key={i} className="p-1 border-r border-slate-800">
                    <input
                      type="number"
                      aria-label={`${label}, аккорд #${i + 1}`}
                      value={v[key]}
                      onChange={(e) =>
                        onVoicePitchChange(i, key, Number(e.target.value))
                      }
                      className={`w-full text-center bg-slate-900 border border-slate-700 rounded px-1 py-1 ${textClass} font-bold focus-ring`}
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

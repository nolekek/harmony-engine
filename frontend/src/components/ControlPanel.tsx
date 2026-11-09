import React from "react";
import {
  Wand2,
  Sparkles,
  Sliders,
  CheckCircle2,
  Layers,
  Clock,
  ArrowRight,
} from "lucide-react";

export interface CandidateSolution {
  id: string;
  rank: number;
  cost: number;
  chords: string[];
  progression_preview: string;
  description: string;
  voicings: Array<{ soprano: number; alto: number; tenor: number; bass: number }>;
  musicxml: string;
  ascii_score: string;
}

interface ControlPanelProps {
  keys: Array<{ tonic: string; mode: string; fifths: number; title: string }>;
  selectedKey: { tonic: string; mode: string };
  onKeyChange: (key: { tonic: string; mode: string }) => void;
  onAutoDetectKey: () => void;
  allowExtendedRanges: boolean;
  onToggleExtendedRanges: (val: boolean) => void;
  allowSecondaryDominants: boolean;
  onToggleSecondaryDominants: (val: boolean) => void;
  onHarmonize: () => void;
  isHarmonizing: boolean;
  latencyMs: number | null;
  candidates: CandidateSolution[];
  selectedCandidateId: string | null;
  onSelectCandidate: (candidate: CandidateSolution) => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  keys,
  selectedKey,
  onKeyChange,
  onAutoDetectKey,
  allowExtendedRanges,
  onToggleExtendedRanges,
  allowSecondaryDominants,
  onToggleSecondaryDominants,
  onHarmonize,
  isHarmonizing,
  latencyMs,
  candidates,
  selectedCandidateId,
  onSelectCandidate,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-indigo-400" />
          <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-200">
            Панель управления гармонизацией
          </h2>
        </div>
        {latencyMs !== null && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/80 text-emerald-400 text-xs font-mono">
            <Clock className="w-3.5 h-3.5" />
            <span>{latencyMs} мс</span>
            <span className="text-emerald-500 text-[10px]">(&lt; 500 мс)</span>
          </div>
        )}
      </div>

      {/* Row 1: Key selection + Auto detect */}
      <div className="space-y-2">
        <label className="block text-xs font-medium text-slate-300">
          Тональность (24 канонических лада)
        </label>
        <div className="flex items-center gap-2">
          <select
            className="flex-1 bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={`${selectedKey.tonic}:${selectedKey.mode}`}
            onChange={(e) => {
              const [tonic, mode] = e.target.value.split(":");
              onKeyChange({ tonic, mode });
            }}
          >
            {keys.map((k) => (
              <option key={`${k.tonic}:${k.mode}`} value={`${k.tonic}:${k.mode}`}>
                {k.title} ({k.tonic} {k.mode === "Major" ? "мажор" : "гарм. минор"})
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={onAutoDetectKey}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs font-medium text-slate-200 transition-colors"
            title="Автоопределить тональность по первой/последней ноте сопрано"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Авто</span>
          </button>
        </div>
      </div>

      {/* Row 2: Strictness Toggles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
        <label className="flex items-start gap-3 p-3 bg-slate-800/50 hover:bg-slate-800 border border-slate-700/60 rounded-lg cursor-pointer transition-colors">
          <input
            type="checkbox"
            className="mt-1 rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500"
            checked={allowExtendedRanges}
            onChange={(e) => onToggleExtendedRanges(e.target.checked)}
          />
          <div>
            <div className="text-xs font-semibold text-slate-200">
              Расширенный диапазон
            </div>
            <div className="text-[11px] text-slate-400 leading-tight">
              {allowExtendedRanges
                ? "Инструментальный диапазон (C2-C6)"
                : "Строгий классический хор SATB"}
            </div>
          </div>
        </label>

        <label className="flex items-start gap-3 p-3 bg-slate-800/50 hover:bg-slate-800 border border-slate-700/60 rounded-lg cursor-pointer transition-colors">
          <input
            type="checkbox"
            className="mt-1 rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500"
            checked={allowSecondaryDominants}
            onChange={(e) => onToggleSecondaryDominants(e.target.checked)}
          />
          <div>
            <div className="text-xs font-semibold text-slate-200">
              Побочные доминанты
            </div>
            <div className="text-[11px] text-slate-400 leading-tight">
              Разрешить альтерированные DD, D7/x
            </div>
          </div>
        </label>
      </div>

      {/* Harmonize Action Button */}
      <button
        type="button"
        onClick={onHarmonize}
        disabled={isHarmonizing}
        className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white font-medium text-sm rounded-xl shadow-lg shadow-indigo-500/20 active:scale-[0.99] transition-all disabled:opacity-50 disabled:pointer-events-none"
      >
        <Wand2 className={`w-4 h-4 ${isHarmonizing ? "animate-spin" : ""}`} />
        <span>
          {isHarmonizing ? "Математический синтез (Viterbi)..." : "Гармонизовать мелодию"}
        </span>
      </button>

      {/* Candidate Selector (Carousel / Cards) */}
      {candidates.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Пул гармонических планов (Топ-{candidates.length})</span>
            </div>
            <span className="text-[11px] text-slate-400">1 клик для переключения</span>
          </div>

          <div className="grid grid-cols-1 gap-2.5">
            {candidates.map((cand) => {
              const isSelected = cand.id === selectedCandidateId;
              return (
                <div
                  key={cand.id}
                  onClick={() => onSelectCandidate(cand)}
                  className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                    isSelected
                      ? "bg-indigo-950/40 border-indigo-500 ring-1 ring-indigo-500 shadow-md"
                      : "bg-slate-800/60 border-slate-700/70 hover:bg-slate-800 hover:border-slate-600"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-bold ${
                          cand.rank === 1
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                            : "bg-slate-700 text-slate-300"
                        }`}
                      >
                        #{cand.rank} {cand.rank === 1 ? "Оптимум" : "Вариант"}
                      </span>
                      <span className="text-xs font-medium text-slate-200">
                        {cand.description}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400">
                      <span>Стоимость:</span>
                      <span
                        className={`font-semibold ${
                          cand.cost <= 0 ? "text-emerald-400" : "text-amber-400"
                        }`}
                      >
                        {cand.cost}
                      </span>
                    </div>
                  </div>

                  {/* Chord progression preview */}
                  <div className="flex items-center gap-1.5 flex-wrap text-xs font-mono font-semibold text-indigo-300">
                    {cand.chords.map((chord, idx) => (
                      <React.Fragment key={idx}>
                        <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700">
                          {chord}
                        </span>
                        {idx < cand.chords.length - 1 && (
                          <ArrowRight className="w-3 h-3 text-slate-500" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>

                  {isSelected && (
                    <div className="mt-2 flex items-center gap-1 text-[11px] text-indigo-400">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Активное решение в партитуре и плеере</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

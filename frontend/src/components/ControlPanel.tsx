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
import { Button } from "./ui/Button";
import { Select } from "./ui/Select";

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
  keys: Array<{ tonic: string; mode: string; fifths: number; title?: string; name?: string }>;
  selectedKey: { tonic: string; mode: string };
  onKeyChange: (key: { tonic: string; mode: string }) => void;
  onAutoDetectKey: () => void;
  timeSignature: string;
  onTimeSignatureChange: (val: string) => void;
  allowExtendedRanges: boolean;
  onToggleExtendedRanges: (val: boolean) => void;
  allowSecondaryDominants: boolean;
  onToggleSecondaryDominants: (val: boolean) => void;
  allowAdjacentUnisons: boolean;
  onToggleAdjacentUnisons: (val: boolean) => void;
  relaxHardGates: boolean;
  onToggleRelaxHardGates: (val: boolean) => void;
  onHarmonize: () => void;
  isHarmonizing: boolean;
  isMelodyEmpty?: boolean;
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
  timeSignature,
  onTimeSignatureChange,
  allowExtendedRanges,
  onToggleExtendedRanges,
  allowSecondaryDominants,
  onToggleSecondaryDominants,
  allowAdjacentUnisons,
  onToggleAdjacentUnisons,
  relaxHardGates,
  onToggleRelaxHardGates,
  onHarmonize,
  isHarmonizing,
  isMelodyEmpty = false,
  latencyMs,
  candidates,
  selectedCandidateId,
  onSelectCandidate,
}) => {
  return (
    <div className="bg-surface-card border border-border rounded-xl p-5 shadow-lg space-y-6">
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-brand" />
          <h2 className="text-sm font-semibold tracking-wider uppercase text-text-secondary">
            Панель управления гармонизацией
          </h2>
        </div>
        {latencyMs !== null && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-600/50 text-emerald-700 dark:text-emerald-400 text-xs font-mono">
            <Clock className="w-3.5 h-3.5" />
            <span>{latencyMs} мс</span>
          </div>
        )}
      </div>

      {/* Row 1: Key selection + Auto detect */}
      <div className="flex items-end gap-2">
        <Select
          label="Тональность (24 тональности)"
          value={`${selectedKey.tonic}:${selectedKey.mode}`}
          onChange={(e) => {
            const [tonic, mode] = e.target.value.split(":");
            onKeyChange({ tonic, mode });
          }}
        >
          {keys.map((k) => (
            <option key={`${k.tonic}:${k.mode}`} value={`${k.tonic}:${k.mode}`}>
              {k.name ?? k.title} ({k.tonic} {k.mode === "Major" ? "мажор" : "гарм. минор"})
            </option>
          ))}
        </Select>
        <Button
          variant="secondary"
          size="md"
          onClick={onAutoDetectKey}
          className="shrink-0"
          title="Автоопределить тональность по первой/последней ноте сопрано"
          icon={<Sparkles className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />}
        >
          Авто
        </Button>
      </div>

      {/* Time Signature (Meter) Selector */}
      <div className="space-y-1.5">
        <span className="block text-xs font-medium text-text-secondary">Размер (Метр)</span>
        <div className="flex gap-2" role="group" aria-label="Размер (метр)">
          {["4/4", "3/4", "2/4", "6/8", "3/8"].map((ts) => (
            <button
              key={ts}
              type="button"
              onClick={() => onTimeSignatureChange(ts)}
              aria-pressed={timeSignature === ts}
              className={`flex-1 py-1.5 text-xs font-medium rounded-lg border transition-all cursor-pointer focus-ring ${
                timeSignature === ts
                  ? "bg-brand border-brand text-white shadow-sm shadow-brand/30"
                  : "bg-surface-elevated/80 hover:bg-surface-elevated border-border text-text-secondary"
              }`}
            >
              {ts}
            </button>
          ))}
        </div>
      </div>

      {/* Row 2: Strictness Toggles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
        <label className="flex items-start gap-3 p-3 bg-surface-elevated/50 hover:bg-surface-elevated border border-border rounded-lg cursor-pointer transition-colors">
          <input
            type="checkbox"
            className="mt-1 rounded accent-[var(--app-brand-primary)] focus-ring"
            checked={allowExtendedRanges}
            onChange={(e) => onToggleExtendedRanges(e.target.checked)}
          />
          <div>
            <div className="text-xs font-semibold text-text-primary">Расширенный диапазон</div>
            <div className="text-[11px] text-text-muted leading-tight">
              {allowExtendedRanges
                ? "Инструментальный диапазон (C2-C6)"
                : "Строгий классический хор SATB"}
            </div>
          </div>
        </label>

        <label className="flex items-start gap-3 p-3 bg-surface-elevated/50 hover:bg-surface-elevated border border-border rounded-lg cursor-pointer transition-colors">
          <input
            type="checkbox"
            className="mt-1 rounded accent-[var(--app-brand-primary)] focus-ring"
            checked={allowSecondaryDominants}
            onChange={(e) => onToggleSecondaryDominants(e.target.checked)}
          />
          <div>
            <div className="text-xs font-semibold text-text-primary">Побочные доминанты</div>
            <div className="text-[11px] text-text-muted leading-tight">
              Разрешить альтерированные DD, D7/x
            </div>
          </div>
        </label>

        <label
          className="flex items-start gap-3 p-3 bg-surface-elevated/50 hover:bg-surface-elevated border border-border rounded-lg cursor-pointer transition-colors"
          title="Опциональное послабление: разрешить унисоны соседних голосов (S=A, A=T, T=B). По умолчанию строгий классический запрет."
        >
          <input
            type="checkbox"
            className="mt-1 rounded accent-[var(--app-brand-primary)] focus-ring"
            checked={allowAdjacentUnisons}
            onChange={(e) => onToggleAdjacentUnisons(e.target.checked)}
          />
          <div>
            <div className="text-xs font-semibold text-text-primary">Унисоны соседних голосов</div>
            <div className="text-[11px] text-text-muted leading-tight">
              Разрешить S=A, A=T, T=B (по умолчанию запрещено)
            </div>
          </div>
        </label>

        <label
          className="flex items-start gap-3 p-3 bg-surface-elevated/50 hover:bg-surface-elevated border border-border rounded-lg cursor-pointer transition-colors"
          title="Last-resort режим: нарушения жёстких правил получают большой штраф вместо отбраковки плана. Строгое решение всегда приоритетнее релаксации."
        >
          <input
            type="checkbox"
            className="mt-1 rounded accent-[var(--app-brand-primary)] focus-ring"
            checked={relaxHardGates}
            onChange={(e) => onToggleRelaxHardGates(e.target.checked)}
          />
          <div>
            <div className="text-xs font-semibold text-text-primary">Смягчение hard-правил</div>
            <div className="text-[11px] text-text-muted leading-tight">
              Last-resort: штраф вместо отказа (строгое решение в приоритете)
            </div>
          </div>
        </label>
      </div>

      {/* Harmonize Action Button */}
      <Button
        variant="primary"
        size="lg"
        onClick={onHarmonize}
        disabled={isHarmonizing || isMelodyEmpty}
        className="w-full shadow-lg shadow-brand/20"
        icon={<Wand2 className={`w-4 h-4 ${isHarmonizing ? "animate-spin" : ""}`} />}
      >
        {isHarmonizing ? "Математический синтез (Viterbi)..." : "Гармонизовать мелодию"}
      </Button>

      {/* Candidate Selector (Top-3 pool) */}
      {candidates.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-border-subtle">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary">
              <Layers className="w-4 h-4 text-brand" />
              <span>Пул гармонических планов (Топ-{candidates.length})</span>
            </div>
            <span className="text-[11px] text-text-muted">1 клик для переключения</span>
          </div>

          <div className="grid grid-cols-1 gap-2.5">
            {candidates.map((cand) => {
              const isSelected = cand.id === selectedCandidateId;
              return (
                <div
                  key={cand.id}
                  role="button"
                  tabIndex={0}
                  aria-label={`Выбрать решение #${cand.rank}: ${cand.description}`}
                  aria-pressed={isSelected}
                  onClick={() => onSelectCandidate(cand)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSelectCandidate(cand);
                    }
                  }}
                  className={`p-3 rounded-lg border text-left cursor-pointer transition-all focus-ring ${
                    isSelected
                      ? "bg-brand-light border-brand ring-1 ring-brand shadow-md"
                      : "bg-surface-elevated/60 border-border hover:bg-surface-elevated hover:border-border-strong"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-bold border ${
                          cand.rank === 1
                            ? "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-600/40"
                            : "bg-surface-elevated text-text-secondary border-border"
                        }`}
                      >
                        #{cand.rank} {cand.rank === 1 ? "Оптимум" : "Вариант"}
                      </span>
                      <span className="text-xs font-medium text-text-primary">
                        {cand.description}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-[11px] font-mono text-text-muted">
                      <span>Штраф:</span>
                      <span
                        className={`font-semibold ${
                          cand.cost === 0
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-amber-600 dark:text-amber-400"
                        }`}
                      >
                        {Math.abs(cand.cost)}
                      </span>
                    </div>
                  </div>

                  {/* Chord progression preview */}
                  <div className="flex items-center gap-1.5 flex-wrap text-xs font-mono font-semibold text-brand">
                    {cand.chords.map((chord, idx) => (
                      <React.Fragment key={idx}>
                        <span className="px-1.5 py-0.5 rounded bg-surface-panel border border-border">
                          {chord}
                        </span>
                        {idx < cand.chords.length - 1 && (
                          <ArrowRight className="w-3 h-3 text-text-muted" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>

                  {isSelected && (
                    <div className="mt-2 flex items-center gap-1 text-[11px] text-brand">
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

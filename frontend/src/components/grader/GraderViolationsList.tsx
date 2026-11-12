import React from "react";
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";

export interface GraderViolationItem {
  measure: number;
  chord_index: number;
  rule_id: string;
  severity: "hard_gate" | "soft_penalty";
  message_ru: string;
  voices: string[];
  notes: string[];
}

export interface GraderReportData {
  is_valid: boolean;
  total_violations: number;
  hard_violations_count: number;
  soft_violations_count: number;
  violations: GraderViolationItem[];
  problem_measures: number[];
  summary_verdict: string;
  grade: string;
}

interface GraderViolationsListProps {
  report: GraderReportData;
  onHighlightMeasure: (measure: number) => void;
}

export const GraderViolationsList: React.FC<GraderViolationsListProps> = ({
  report,
  onHighlightMeasure,
}) => {
  const isExcellent = report.grade.startsWith("5");
  const isGood = report.grade.startsWith("4");
  const isSatisfactory = report.grade.startsWith("3");

  const gradeBannerClass = isExcellent
    ? "bg-emerald-950/40 border-emerald-600 text-emerald-200"
    : isGood
    ? "bg-blue-950/40 border-blue-600 text-blue-200"
    : isSatisfactory
    ? "bg-amber-950/40 border-amber-600 text-amber-200"
    : "bg-rose-950/40 border-rose-600 text-rose-200";

  return (
    <div className="space-y-4 pt-3 border-t border-slate-800">
      {/* Grade banner */}
      <div className={`p-4 rounded-xl border flex items-center justify-between gap-4 ${gradeBannerClass}`}>
        <div className="space-y-1">
          <div className="text-xs uppercase font-semibold tracking-wider opacity-80">
            Оценка инспектора
          </div>
          <div className="text-2xl font-black">{report.grade}</div>
          <div className="text-xs opacity-90">{report.summary_verdict}</div>
        </div>

        <div className="text-right space-y-1 font-mono text-xs">
          <div className="text-rose-400 font-semibold">
            Критических ошибок: {report.hard_violations_count}
          </div>
          <div className="text-amber-400">
            Предупреждений: {report.soft_violations_count}
          </div>
          <div className="text-slate-400">
            Проблемных тактов: {report.problem_measures.length}
          </div>
        </div>
      </div>

      {/* List of Rule Violations with pedagogical critique */}
      {report.violations.length > 0 ? (
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Детальный разбор ошибок по тактам:
          </h3>
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {report.violations.map((v, idx) => (
              <div
                key={idx}
                role="button"
                tabIndex={0}
                aria-label={`Подсветить ошибку в такте ${v.measure}: ${v.message_ru}`}
                onClick={() => onHighlightMeasure(v.measure)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onHighlightMeasure(v.measure);
                  }
                }}
                className={`p-3 rounded-lg border text-left cursor-pointer transition-colors focus-ring ${
                  v.severity === "hard_gate"
                    ? "bg-rose-950/30 border-rose-800/80 hover:bg-rose-950/50"
                    : "bg-amber-950/30 border-amber-800/80 hover:bg-amber-950/50"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    {v.severity === "hard_gate" ? (
                      <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                    )}
                    <span className="text-xs font-bold font-mono text-slate-200">
                      {v.message_ru}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold uppercase ${
                      v.severity === "hard_gate"
                        ? "bg-rose-900 text-rose-200"
                        : "bg-amber-900 text-amber-200"
                    }`}
                  >
                    {v.severity === "hard_gate" ? "Запрет" : "Штраф"}
                  </span>
                </div>

                {v.notes.length > 0 && (
                  <div className="text-[11px] font-mono text-slate-400 mt-1 pl-6">
                    Движение: {v.notes.join(", ")}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-lg bg-emerald-950/30 border border-emerald-800 text-emerald-300 flex items-center gap-3 text-xs">
          <CheckCircle className="w-5 h-5 text-emerald-400" />
          <div>
            <strong>Идеальное голосоведение!</strong> Ни одной параллельной квинты,
            октавы, перекрещивания или недопустимого удвоения не обнаружено.
          </div>
        </div>
      )}
    </div>
  );
};

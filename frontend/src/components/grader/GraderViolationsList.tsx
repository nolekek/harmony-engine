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
    ? "bg-emerald-500/10 border-emerald-600 text-emerald-800 dark:text-emerald-200"
    : isGood
    ? "bg-blue-500/10 border-blue-600 text-blue-800 dark:text-blue-200"
    : isSatisfactory
    ? "bg-amber-500/10 border-amber-600 text-amber-800 dark:text-amber-200"
    : "bg-rose-500/10 border-rose-600 text-rose-800 dark:text-rose-200";

  return (
    <div className="space-y-4 pt-3 border-t border-border-subtle">
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
          <div className="text-rose-700 dark:text-rose-300 font-semibold">
            Критических ошибок: {report.hard_violations_count}
          </div>
          <div className="text-amber-700 dark:text-amber-300">
            Предупреждений: {report.soft_violations_count}
          </div>
          <div className="text-text-muted">
            Проблемных тактов: {report.problem_measures.length}
          </div>
        </div>
      </div>

      {/* List of Rule Violations with pedagogical critique */}
      {report.violations.length > 0 ? (
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted">
            Детальный разбор ошибок по тактам:
          </h3>
          {/* No nested scrollbox: the page/panel scrolls as one. */}
          <div className="space-y-2">
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
                    ? "bg-rose-500/10 border-rose-600/50 hover:bg-rose-500/20"
                    : "bg-amber-500/10 border-amber-600/50 hover:bg-amber-500/20"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    {v.severity === "hard_gate" ? (
                      <XCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                    )}
                    <span className="text-xs font-bold font-mono text-text-primary">
                      {v.message_ru}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold uppercase ${
                      v.severity === "hard_gate"
                        ? "bg-rose-600 text-white"
                        : "bg-amber-500 text-slate-950"
                    }`}
                  >
                    {v.severity === "hard_gate" ? "Запрет" : "Штраф"}
                  </span>
                </div>

                {v.notes.length > 0 && (
                  <div className="text-[11px] font-mono text-text-muted mt-1 pl-6">
                    Движение: {v.notes.join(", ")}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-600/50 text-emerald-800 dark:text-emerald-300 flex items-center gap-3 text-xs">
          <CheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          <div>
            <strong>Идеальное голосоведение!</strong> Ни одной параллельной квинты,
            октавы, перекрещивания или недопустимого удвоения не обнаружено.
          </div>
        </div>
      )}
    </div>
  );
};

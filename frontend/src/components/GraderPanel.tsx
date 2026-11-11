import React, { useState } from "react";
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Upload,
  Award,
  BookOpen,
  Sparkles,
} from "lucide-react";
import type { SATBVoicing } from "../audio/synth";

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

export interface GraderMeta {
  key: { tonic: string; mode: string };
  timeSignature: string;
  chords: string[];
  durations: string[];
  asciiScore?: string;
}

interface GraderPanelProps {
  selectedKey: { tonic: string; mode: string };
  timeSignature?: string;
  allowExtendedRanges: boolean;
  onGradeComplete: (
    report: GraderReportData,
    musicxml: string,
    voicings: SATBVoicing[],
    meta?: GraderMeta
  ) => void;
  onHighlightMeasure: (measure: number) => void;
}

// Preset examples for students to try
const SAMPLE_TESTS = [
  {
    name: "Задача с грубыми ошибками (Параллельные квинты/октавы)",
    key: { tonic: "C", mode: "Major" },
    timeSignature: "4/4",
    voicings: [
      { soprano: 67, alto: 60, tenor: 55, bass: 48 }, // G4, C4, G3, C3 (T)
      { soprano: 69, alto: 62, tenor: 57, bass: 50 }, // A4, D4, A3, D3 (Parallel 5ths & 8ves!)
      { soprano: 67, alto: 64, tenor: 55, bass: 48 }, // G4, E4, G3, C3
    ],
    chords: ["T", "II", "T"],
    durations: ["half", "half", "half"],
  },
  {
    name: "Эталонное решение (Способин, без ошибок)",
    key: { tonic: "C", mode: "Major" },
    timeSignature: "4/4",
    voicings: [
      { soprano: 64, alto: 60, tenor: 55, bass: 48 }, // E4, C4, G3, C3 (T)
      { soprano: 65, alto: 60, tenor: 57, bass: 45 }, // F4, C4, A3, A2 (VI)
      { soprano: 65, alto: 60, tenor: 57, bass: 41 }, // F4, C4, A3, F2 (S)
      { soprano: 64, alto: 60, tenor: 55, bass: 48 }, // E4, C4, G3, C3 (T)
      { soprano: 62, alto: 59, tenor: 55, bass: 43 }, // D4, B3, G3, G2 (D)
      { soprano: 60, alto: 60, tenor: 55, bass: 48 }, // C4, C4, G3, C3 (T)
    ],
    chords: ["T", "VI", "S", "T", "D", "T"],
    durations: ["half", "half", "half", "half", "half", "half"],
  },
];

export const GraderPanel: React.FC<GraderPanelProps> = ({
  selectedKey,
  timeSignature = "4/4",
  allowExtendedRanges,
  onGradeComplete,
  onHighlightMeasure,
}) => {
  const [voicings, setVoicings] = useState<SATBVoicing[]>(SAMPLE_TESTS[0].voicings);
  const [chordsInput, setChordsInput] = useState<string>("T, II, T");
  const [currentKey, setCurrentKey] = useState<{ tonic: string; mode: string }>(selectedKey);
  const [currentTimeSignature, setCurrentTimeSignature] = useState<string>(
    SAMPLE_TESTS[0].timeSignature || timeSignature
  );
  const [currentDurations, setCurrentDurations] = useState<string[]>(
    SAMPLE_TESTS[0].durations || ["half", "half", "half"]
  );
  const [isGrading, setIsGrading] = useState<boolean>(false);
  const [report, setReport] = useState<GraderReportData | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const runGrading = async (
    targetVoicings = voicings,
    targetChordsInput = chordsInput,
    targetKey = currentKey,
    targetTimeSig = currentTimeSignature,
    targetDurations = currentDurations
  ) => {
    const targetChords = targetChordsInput
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);

    if (targetChords.length === 0) {
      setErrorMessage("Укажите гармонические функции (аккорды), например: T, S, D, T. Поле не может быть пустым.");
      return;
    }

    setIsGrading(true);
    setErrorMessage(null);

    const durs =
      targetDurations && targetDurations.length === targetVoicings.length
        ? targetDurations
        : targetVoicings.map((v) => v.duration || "half");

    try {
      const resp = await fetch("/api/grade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          voicings: targetVoicings,
          key: targetKey,
          chords: targetChords,
          time_signature: targetTimeSig || "4/4",
          durations: durs,
          allow_extended_ranges: allowExtendedRanges,
        }),
      });

      if (!resp.ok) {
        let detailMsg = `Ошибка сервера (${resp.status})`;
        try {
          const errData = await resp.json();
          if (errData.detail) {
            if (typeof errData.detail === "string") {
              detailMsg = errData.detail;
            } else if (Array.isArray(errData.detail)) {
              detailMsg = errData.detail
                .map((d: any) =>
                  d.msg ? `${d.loc ? d.loc.join(".") + ": " : ""}${d.msg}` : JSON.stringify(d)
                )
                .join("; ");
            }
          }
        } catch {
          // ignore json parse error
        }
        throw new Error(detailMsg);
      }

      const data = await resp.json();
      setReport(data.report);
      onGradeComplete(data.report, data.musicxml, targetVoicings, {
        key: targetKey,
        timeSignature: targetTimeSig || "4/4",
        chords: targetChords,
        durations: durs,
        asciiScore: data.ascii_score,
      });
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setIsGrading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      setIsGrading(true);
      const res = await fetch("/api/import-file", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Не удалось прочитать файл");
      }

      const data = await res.json();
      if (data.satb_voicings && data.satb_voicings.length > 0) {
        setVoicings(data.satb_voicings);
        const chordsList = data.chords && data.chords.length > 0 ? data.chords : [];
        const chordsStr = chordsList.join(", ");
        setChordsInput(chordsStr);

        const fKey = data.key || currentKey;
        const fTime = data.time_signature || currentTimeSignature;
        const fDurs =
          data.durations ||
          data.satb_voicings.map((v: SATBVoicing) => v.duration || "half");

        if (data.key) setCurrentKey(fKey);
        if (data.time_signature) setCurrentTimeSignature(fTime);
        setCurrentDurations(fDurs);

        await runGrading(data.satb_voicings, chordsStr, fKey, fTime, fDurs);
      } else {
        throw new Error("В файле не найдено 4 голоса SATB");
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setIsGrading(false);
    }
  };

  const loadSample = (sample: (typeof SAMPLE_TESTS)[0]) => {
    setVoicings(sample.voicings);
    const chordsStr = sample.chords.join(", ");
    setChordsInput(chordsStr);
    setCurrentKey(sample.key);
    const ts = sample.timeSignature || "4/4";
    setCurrentTimeSignature(ts);
    const durs = sample.durations || sample.voicings.map(() => "half");
    setCurrentDurations(durs);
    runGrading(sample.voicings, chordsStr, sample.key, ts, durs);
  };

  // Matrix cell change helper
  const updateVoicePitch = (
    chordIdx: number,
    voice: "soprano" | "alto" | "tenor" | "bass",
    val: number
  ) => {
    const updated = [...voicings];
    updated[chordIdx] = { ...updated[chordIdx], [voice]: val };
    setVoicings(updated);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-400" />
            <h2 className="text-base font-bold text-slate-100">
              Режим «Консерваторский инспектор»
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Строгая академическая проверка голосоведения по правилам бригадного учебника
          </p>
        </div>

        {/* File upload shortcut */}
        <label className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs font-medium text-slate-200 cursor-pointer transition-colors">
          <Upload className="w-4 h-4 text-indigo-400" />
          <span>Загрузить MusicXML студента</span>
          <input
            type="file"
            accept=".xml,.musicxml,.mid"
            className="hidden"
            onChange={handleFileUpload}
          />
        </label>
      </div>

      {/* Preset Pickers */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs font-semibold text-slate-400 flex items-center gap-1">
          <BookOpen className="w-3.5 h-3.5" />
          Примеры для проверки:
        </span>
        {SAMPLE_TESTS.map((sample, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => loadSample(sample)}
            className="text-xs px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors"
          >
            {sample.name}
          </button>
        ))}
      </div>

      {/* Harmonic Functions (Chords) Input & Meta Indicator */}
      <div className="space-y-1.5 bg-slate-950/40 p-3 rounded-lg border border-slate-800">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-slate-300">
            Гармонические функции (аккорды через запятую):
          </label>
          <span className="text-[11px] text-slate-400 font-mono">
            Тональность: <strong className="text-amber-300">{currentKey.tonic} {currentKey.mode === "Major" ? "мажор" : "гарм. минор"}</strong> · Размер: <strong className="text-indigo-300">{currentTimeSignature}</strong>
          </span>
        </div>
        <input
          type="text"
          value={chordsInput}
          onChange={(e) => setChordsInput(e.target.value)}
          placeholder="Например: T, S, D, T или T, II, T"
          className="w-full text-xs bg-slate-900 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 font-mono focus:border-amber-500 focus:outline-none"
        />
      </div>

      {/* Matrix Editor for SATB Voicings */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300">
            Сетка аккордов (MIDI-ноты 4 голосов):
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                const last = voicings[voicings.length - 1] || {
                  soprano: 60,
                  alto: 55,
                  tenor: 52,
                  bass: 48,
                };
                setVoicings([...voicings, { ...last }]);
                setCurrentDurations([...currentDurations, "half"]);
              }}
              className="text-xs px-2 py-0.5 bg-slate-800 hover:bg-slate-700 rounded border border-slate-700 text-slate-200"
            >
              + Добавить аккорд
            </button>
            {voicings.length > 2 && (
              <button
                type="button"
                onClick={() => {
                  setVoicings(voicings.slice(0, -1));
                  setCurrentDurations(currentDurations.slice(0, -1));
                }}
                className="text-xs px-2 py-0.5 bg-slate-800 hover:bg-slate-700 rounded border border-slate-700 text-rose-300"
              >
                - Удалить последний
              </button>
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
              {/* Soprano */}
              <tr className="bg-blue-950/20">
                <td className="p-2 font-bold text-blue-400 border-r border-slate-800">
                  Сопрано (S)
                </td>
                {voicings.map((v, i) => (
                  <td key={i} className="p-1 border-r border-slate-800">
                    <input
                      type="number"
                      aria-label={`Сопрано, аккорд #${i + 1}`}
                      value={v.soprano}
                      onChange={(e) =>
                        updateVoicePitch(i, "soprano", Number(e.target.value))
                      }
                      className="w-full text-center bg-slate-900 border border-slate-700 rounded px-1 py-1 text-blue-300 font-bold focus:border-blue-500 focus:outline-none"
                    />
                  </td>
                ))}
              </tr>

              {/* Alto */}
              <tr className="bg-green-950/20">
                <td className="p-2 font-bold text-green-400 border-r border-slate-800">
                  Альт (A)
                </td>
                {voicings.map((v, i) => (
                  <td key={i} className="p-1 border-r border-slate-800">
                    <input
                      type="number"
                      aria-label={`Альт, аккорд #${i + 1}`}
                      value={v.alto}
                      onChange={(e) => updateVoicePitch(i, "alto", Number(e.target.value))}
                      className="w-full text-center bg-slate-900 border border-slate-700 rounded px-1 py-1 text-green-300 font-bold focus:border-green-500 focus:outline-none"
                    />
                  </td>
                ))}
              </tr>

              {/* Tenor */}
              <tr className="bg-orange-950/20">
                <td className="p-2 font-bold text-orange-400 border-r border-slate-800">
                  Тенор (T)
                </td>
                {voicings.map((v, i) => (
                  <td key={i} className="p-1 border-r border-slate-800">
                    <input
                      type="number"
                      aria-label={`Тенор, аккорд #${i + 1}`}
                      value={v.tenor}
                      onChange={(e) => updateVoicePitch(i, "tenor", Number(e.target.value))}
                      className="w-full text-center bg-slate-900 border border-slate-700 rounded px-1 py-1 text-orange-300 font-bold focus:border-orange-500 focus:outline-none"
                    />
                  </td>
                ))}
              </tr>

              {/* Bass */}
              <tr className="bg-red-950/20">
                <td className="p-2 font-bold text-red-400 border-r border-slate-800">
                  Бас (B)
                </td>
                {voicings.map((v, i) => (
                  <td key={i} className="p-1 border-r border-slate-800">
                    <input
                      type="number"
                      aria-label={`Бас, аккорд #${i + 1}`}
                      value={v.bass}
                      onChange={(e) => updateVoicePitch(i, "bass", Number(e.target.value))}
                      className="w-full text-center bg-slate-900 border border-slate-700 rounded px-1 py-1 text-red-300 font-bold focus:border-red-500 focus:outline-none"
                    />
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Action check button */}
      <button
        type="button"
        onClick={() => runGrading()}
        disabled={isGrading}
        className="w-full py-3 px-4 bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white font-bold text-sm rounded-xl shadow-lg shadow-amber-600/20 active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <Sparkles className={`w-4 h-4 ${isGrading ? "animate-spin" : ""}`} />
        <span>
          {isGrading ? "Проверка по канонам гармонии..." : "Проверить моё голосоведение"}
        </span>
      </button>

      {errorMessage && (
        <div className="p-3 bg-red-950/40 border border-red-800 rounded-lg text-xs text-red-300">
          {errorMessage}
        </div>
      )}

      {/* Grader Verdict & Detailed Errors Report */}
      {report && (
        <div className="space-y-4 pt-3 border-t border-slate-800">
          {/* Grade banner */}
          <div
            className={`p-4 rounded-xl border flex items-center justify-between gap-4 ${
              report.grade.startsWith("5")
                ? "bg-emerald-950/40 border-emerald-600 text-emerald-200"
                : report.grade.startsWith("4")
                ? "bg-blue-950/40 border-blue-600 text-blue-200"
                : report.grade.startsWith("3")
                ? "bg-amber-950/40 border-amber-600 text-amber-200"
                : "bg-rose-950/40 border-rose-600 text-rose-200"
            }`}
          >
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
                    className={`p-3 rounded-lg border text-left cursor-pointer transition-colors ${
                      v.severity === "hard_gate"
                        ? "bg-rose-950/30 border-rose-800/80 hover:bg-rose-950/50"
                        : "bg-amber-950/30 border-amber-800/80 hover:bg-amber-950/50"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        {v.severity === "hard_gate" ? (
                          <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                        ) : (
                          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
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
      )}
    </div>
  );
};

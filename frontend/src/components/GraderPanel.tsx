import React, { useState } from "react";
import { Award, Upload, BookOpen, Sparkles } from "lucide-react";
import type { SATBVoicing } from "../audio/synth";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";
import { GraderScoreMatrix } from "./grader/GraderScoreMatrix";
import { GraderViolationsList } from "./grader/GraderViolationsList";
import type { GraderReportData, GraderViolationItem } from "./grader/GraderViolationsList";
import { SAMPLE_TESTS } from "./grader/sampleTests";
import type { GraderSampleTest } from "./grader/sampleTests";

export type { GraderReportData, GraderViolationItem };

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
      setErrorMessage("Укажите гармонические функции (аккорды), например: T, S, D, T.");
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
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || errData.message || `Ошибка сервера (${resp.status})`);
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
      if (!res.ok) throw new Error("Не удалось прочитать файл");

      const data = await res.json();
      if (data.satb_voicings && data.satb_voicings.length > 0) {
        setVoicings(data.satb_voicings);
        const chordsStr = (data.chords || []).join(", ");
        setChordsInput(chordsStr);
        const fKey = data.key || currentKey;
        const fTime = data.time_signature || currentTimeSignature;
        const fDurs = data.durations || data.satb_voicings.map((v: SATBVoicing) => v.duration || "half");

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

  const loadSample = (sample: GraderSampleTest) => {
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
    <div className="bg-surface-card border border-border rounded-xl p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-3">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-500 dark:text-amber-400" />
            <h2 className="text-base font-bold text-text-primary">
              Режим «Консерваторский инспектор»
            </h2>
          </div>
          <p className="text-xs text-text-muted mt-0.5">
            Строгая академическая проверка голосоведения по правилам бригадного учебника
          </p>
        </div>

        <label className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-elevated hover:bg-surface-panel border border-border rounded-lg text-xs font-medium text-text-primary cursor-pointer transition-colors focus-ring">
          <Upload className="w-3.5 h-3.5 text-brand" />
          <span>Загрузить партитуру</span>
          <input type="file" accept=".xml,.musicxml,.mid" className="hidden" onChange={handleFileUpload} />
        </label>
      </div>

      {/* Preset Pickers */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs font-semibold text-text-muted flex items-center gap-1">
          <BookOpen className="w-3.5 h-3.5" /> Примеры:
        </span>
        {SAMPLE_TESTS.map((sample, idx) => (
          <Button
            key={idx}
            variant="secondary"
            size="xs"
            onClick={() => loadSample(sample)}
          >
            {sample.name}
          </Button>
        ))}
      </div>

      {/* Harmonic Functions */}
      <div className="space-y-1.5 bg-surface-subtle/40 p-3 rounded-lg border border-border-subtle">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-text-secondary">
            Гармонические функции:
          </span>
          <span className="text-[11px] text-text-muted font-mono">
            {currentKey.tonic} {currentKey.mode === "Major" ? "мажор" : "гарм. минор"} · {currentTimeSignature}
          </span>
        </div>
        <Input
          type="text"
          inputSize="sm"
          value={chordsInput}
          onChange={(e) => setChordsInput(e.target.value)}
          placeholder="Например: T, S, D, T или T, II, T"
          aria-label="Гармонические функции"
          className="font-mono"
        />
      </div>

      {/* SATB Matrix */}
      <GraderScoreMatrix
        voicings={voicings}
        onVoicePitchChange={updateVoicePitch}
        onAddChord={() => {
          const last = voicings[voicings.length - 1] || { soprano: 60, alto: 55, tenor: 52, bass: 48 };
          setVoicings([...voicings, { ...last }]);
          setCurrentDurations([...currentDurations, "half"]);
        }}
        onRemoveChord={() => {
          setVoicings(voicings.slice(0, -1));
          setCurrentDurations(currentDurations.slice(0, -1));
        }}
      />

      {/* Submit button */}
      <Button
        variant="primary"
        size="md"
        onClick={() => runGrading()}
        disabled={isGrading}
        className="w-full font-bold bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 shadow-md shadow-amber-600/20"
        icon={<Sparkles className={`w-4 h-4 ${isGrading ? "animate-spin" : ""}`} />}
      >
        {isGrading ? "Проверка по канонам гармонии..." : "Проверить моё голосоведение"}
      </Button>

      {errorMessage && (
        <div role="alert" aria-live="assertive" className="p-3 bg-rose-500/10 border border-rose-600/50 rounded-lg text-xs text-rose-700 dark:text-rose-300">
          {errorMessage}
        </div>
      )}

      {/* Violations report */}
      {report && (
        <GraderViolationsList report={report} onHighlightMeasure={onHighlightMeasure} />
      )}
    </div>
  );
};

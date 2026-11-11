import { useState, useEffect, useRef } from "react";
import {
  Music,
  Award,
  FileMusic,
  AlertCircle,
} from "lucide-react";

import { MelodyInput } from "./components/MelodyInput";
import type { MelodyNote } from "./components/MelodyInput";
import { ControlPanel } from "./components/ControlPanel";
import type { CandidateSolution } from "./components/ControlPanel";
import { ScoreDisplay } from "./components/ScoreDisplay";
import { AudioControls } from "./components/AudioControls";
import { GraderPanel } from "./components/GraderPanel";
import type { GraderReportData, GraderMeta } from "./components/GraderPanel";
import { ExportBar } from "./components/ExportBar";
import type { SATBVoicing } from "./audio/synth";

// Initial classic melody: E4, F4, G4, E4, D4, C4 in C Major
const INITIAL_MELODY: MelodyNote[] = [
  { pitch: 64, name: "E4", duration: "half", is_downbeat: true },
  { pitch: 65, name: "F4", duration: "half", is_downbeat: false },
  { pitch: 67, name: "G4", duration: "half", is_downbeat: true },
  { pitch: 64, name: "E4", duration: "half", is_downbeat: false },
  { pitch: 62, name: "D4", duration: "half", is_downbeat: true },
  { pitch: 60, name: "C4", duration: "whole", is_downbeat: false },
];

export interface TabScoreState {
  musicxml: string;
  voicings: SATBVoicing[];
  chords: string[];
  asciiScore: string;
  title: string;
  problemMeasures: number[];
  durations: string[];
  key: { tonic: string; mode: string };
  timeSignature: string;
  currentPlaybackIndex: number;
}

const INITIAL_HARMONIZER_STATE: TabScoreState = {
  musicxml: "",
  voicings: [],
  chords: [],
  asciiScore: "",
  title: "Гармонизация мелодии",
  problemMeasures: [],
  durations: INITIAL_MELODY.map((m) => m.duration),
  key: { tonic: "C", mode: "Major" },
  timeSignature: "4/4",
  currentPlaybackIndex: -1,
};

const INITIAL_GRADER_STATE: TabScoreState = {
  musicxml: "",
  voicings: [],
  chords: [],
  asciiScore: "",
  title: "Консерваторский инспектор",
  problemMeasures: [],
  durations: [],
  key: { tonic: "C", mode: "Major" },
  timeSignature: "4/4",
  currentPlaybackIndex: -1,
};

export function App() {
  const [activeTab, setActiveTab] = useState<"harmonizer" | "grader">("harmonizer");

  // Melody & Keys
  const [melody, setMelody] = useState<MelodyNote[]>(INITIAL_MELODY);
  const [canonicalKeys, setCanonicalKeys] = useState<
    Array<{ tonic: string; mode: string; fifths: number; title?: string; name?: string }>
  >([]);
  const [selectedKey, setSelectedKey] = useState<{ tonic: string; mode: string }>({
    tonic: "C",
    mode: "Major",
  });

  // Strictness settings
  const [allowExtendedRanges, setAllowExtendedRanges] = useState<boolean>(false);
  const [allowSecondaryDominants, setAllowSecondaryDominants] = useState<boolean>(true);
  const [timeSignature, setTimeSignature] = useState<string>("4/4");

  // Harmonization state
  const [isHarmonizing, setIsHarmonizing] = useState<boolean>(false);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [candidates, setCandidates] = useState<CandidateSolution[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateSolution | null>(
    null
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorDiagnostics, setErrorDiagnostics] = useState<string[]>([]);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Independent tab score states: Harmonizer vs Grader
  const [harmonizerScore, setHarmonizerScore] = useState<TabScoreState>(INITIAL_HARMONIZER_STATE);
  const [graderScore, setGraderScore] = useState<TabScoreState>(INITIAL_GRADER_STATE);

  // Active state for score rendering and export
  const activeScoreState = activeTab === "harmonizer" ? harmonizerScore : graderScore;

  const setPlaybackIndex = (tab: "harmonizer" | "grader", idx: number) => {
    if (tab === "harmonizer") {
      setHarmonizerScore((prev) => ({ ...prev, currentPlaybackIndex: idx }));
    } else {
      setGraderScore((prev) => ({ ...prev, currentPlaybackIndex: idx }));
    }
  };

  // Load canonical keys on mount
  useEffect(() => {
    fetch("/api/keys")
      .then((res) => res.json())
      .then((data) => {
        setCanonicalKeys(data);
      })
      .catch((err) => console.error("Failed to load keys:", err));
  }, []);

  // Harmonize function
  const handleHarmonize = async () => {
    if (!melody || melody.length === 0) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsHarmonizing(true);
    setErrorMessage(null);
    setErrorDiagnostics([]);

    try {
      const resp = await fetch("/api/harmonize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          melody: melody.map((m) => ({
            pitch: m.pitch,
            name: m.name,
            duration: m.duration,
            is_downbeat: m.is_downbeat,
          })),
          key: selectedKey,
          time_signature: timeSignature,
          allow_extended_ranges: allowExtendedRanges,
          allow_secondary_dominants: allowSecondaryDominants,
          max_plans: 50,
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
                .map((d: any) => {
                  const loc = Array.isArray(d.loc)
                    ? d.loc.filter((l: any) => l !== "body").join(".")
                    : "";
                  return loc ? `${loc}: ${d.msg}` : d.msg;
                })
                .join("; ");
            } else if (typeof errData.detail === "object") {
              detailMsg = JSON.stringify(errData.detail);
            }
          } else if (errData.message) {
            detailMsg = errData.message;
          }
        } catch {
          // ignore json parse error
        }

        setCandidates([]);
        setSelectedCandidate(null);
        setLatencyMs(null);
        setErrorMessage(detailMsg);
        setErrorDiagnostics([]);
        setHarmonizerScore((prev) => ({
          ...prev,
          musicxml: "",
          voicings: [],
          chords: [],
          asciiScore: "",
          problemMeasures: [],
        }));
        return;
      }

      const data = await resp.json();
      setLatencyMs(data.latency_ms ?? null);

      if (data.is_success && data.candidates && data.candidates.length > 0) {
        setErrorMessage(null);
        setErrorDiagnostics([]);
        setCandidates(data.candidates);
        const best = data.best_candidate || data.candidates[0];
        setSelectedCandidate(best);
        const bestDurs = best.durations || melody.map((m) => m.duration);
        const bestCost = Math.abs(best.cost);

        setHarmonizerScore((prev) => ({
          ...prev,
          musicxml: best.musicxml,
          voicings: best.voicings,
          chords: best.chords,
          asciiScore: best.ascii_score,
          durations: bestDurs,
          problemMeasures: [],
          key: selectedKey,
          timeSignature: timeSignature,
          currentPlaybackIndex: -1,
          title: `Решение #${best.rank} · ${best.description} (Штраф: ${bestCost})`,
        }));
      } else {
        setCandidates([]);
        setSelectedCandidate(null);
        setLatencyMs(null);
        const msg =
          data.error?.message ??
          data.message ??
          "Не удалось построить гармонизацию";
        setErrorMessage(msg);

        setHarmonizerScore((prev) => ({
          ...prev,
          musicxml: "",
          voicings: [],
          chords: [],
          asciiScore: "",
          problemMeasures: [],
        }));

        if (data.error?.diagnostics && Array.isArray(data.error.diagnostics)) {
          setErrorDiagnostics(
            data.error.diagnostics.map((d: any) => {
              if (typeof d === "string") return d;
              if (typeof d === "object" && d !== null) {
                const parts: string[] = [];
                if (d.step !== undefined) parts.push(`Шаг ${d.step}`);
                if (d.chord) parts.push(`аккорд ${d.chord}`);
                if (d.blocked !== undefined) parts.push(`заблокировано: ${d.blocked}`);
                if (d.blocked_by && Array.isArray(d.blocked_by))
                  parts.push(`правила: ${d.blocked_by.join(", ")}`);
                return parts.length > 0 ? parts.join(" | ") : JSON.stringify(d);
              }
              return String(d);
            })
          );
        } else {
          setErrorDiagnostics([]);
        }
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name === "AbortError") {
        return;
      }
      console.error("Harmonize request error:", e);
      setCandidates([]);
      setSelectedCandidate(null);
      setLatencyMs(null);
      setErrorMessage(
        e instanceof Error ? e.message : "Не удалось построить гармонизацию"
      );
      setErrorDiagnostics([]);
      setHarmonizerScore((prev) => ({
        ...prev,
        musicxml: "",
        voicings: [],
        chords: [],
        asciiScore: "",
        problemMeasures: [],
      }));
    } finally {
      if (abortControllerRef.current === controller) {
        setIsHarmonizing(false);
      }
    }
  };

  // Run initial harmonization automatically on first render, abort on unmount
  useEffect(() => {
    handleHarmonize();
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Key Auto-detection
  const handleAutoDetectKey = async () => {
    if (!melody || melody.length === 0) return;
    try {
      const resp = await fetch("/api/detect-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          melody.map((m) => ({ pitch: m.pitch, name: m.name }))
        ),
      });
      const data = await resp.json();
      if (data && data.tonic && data.mode) {
        const detectedKey = { tonic: data.tonic, mode: data.mode };
        setSelectedKey(detectedKey);
        setHarmonizerScore((prev) => ({
          ...prev,
          key: detectedKey,
        }));
      }
    } catch (e) {
      console.error("Key detection error:", e);
    }
  };

  // Candidate selection
  const handleSelectCandidate = (cand: CandidateSolution) => {
    setSelectedCandidate(cand);
    const candCost = Math.abs(cand.cost);
    const candDurs =
      (cand as unknown as { durations?: string[] }).durations ||
      melody.map((m) => m.duration);

    setHarmonizerScore((prev) => ({
      ...prev,
      musicxml: cand.musicxml,
      voicings: cand.voicings,
      chords: cand.chords,
      asciiScore: cand.ascii_score,
      durations: candDurs,
      problemMeasures: [],
      key: selectedKey,
      timeSignature: timeSignature,
      currentPlaybackIndex: -1,
      title: `Решение #${cand.rank} · ${cand.description} (Штраф: ${candCost})`,
    }));
  };

  // Melody change handler
  const handleMelodyChange = (newMelody: MelodyNote[]) => {
    setMelody(newMelody);
    setHarmonizerScore((prev) => ({
      ...prev,
      durations: newMelody.map((m) => m.duration),
    }));
  };

  // Time signature change handler for Harmonizer
  const handleTimeSignatureChange = (newTs: string) => {
    setTimeSignature(newTs);
    setHarmonizerScore((prev) => ({
      ...prev,
      timeSignature: newTs,
    }));
  };

  // Key change handler for Harmonizer
  const handleKeyChange = (newKey: { tonic: string; mode: string }) => {
    setSelectedKey(newKey);
    setHarmonizerScore((prev) => ({
      ...prev,
      key: newKey,
    }));
  };

  // Grader complete handler — isolated to graderScore
  const handleGradeComplete = (
    report: GraderReportData,
    musicxml: string,
    voicings: SATBVoicing[],
    meta?: GraderMeta
  ) => {
    setGraderScore((prev) => ({
      ...prev,
      musicxml,
      voicings,
      chords: meta?.chords ?? prev.chords,
      asciiScore: meta?.asciiScore ?? prev.asciiScore,
      problemMeasures: report.problem_measures,
      title: `Инспектор: ${report.grade}`,
      key: meta?.key ?? selectedKey,
      timeSignature: meta?.timeSignature ?? timeSignature,
      durations: meta?.durations ?? voicings.map((v) => v.duration || "half"),
      currentPlaybackIndex: -1,
    }));
  };

  // Grader measure highlight handler
  const handleHighlightMeasure = (m: number) => {
    setGraderScore((prev) => ({
      ...prev,
      problemMeasures: [m],
    }));
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/70 backdrop-blur sticky top-0 z-50 px-4 lg:px-8 py-3.5">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          {/* Logo & Subtitle */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-500 flex items-center justify-center shadow-lg shadow-indigo-600/30">
              <FileMusic className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-tight text-white m-0">
                  Бригадное Ядро Гармонизации
                </h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-950 border border-indigo-700/60 text-indigo-300">
                  Способин / Дубовский
                </span>
              </div>
              <p className="text-xs text-slate-400 m-0">
                Математический Viterbi-синтез & Консерваторский инспектор голосоведения
              </p>
            </div>
          </div>

          {/* Mode Navigation Tabs */}
          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-1 rounded-xl">
            <button
              type="button"
              onClick={() => setActiveTab("harmonizer")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "harmonizer"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Music className="w-3.5 h-3.5" />
              <span>Гармонизация мелодии</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("grader")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "grader"
                  ? "bg-gradient-to-r from-amber-600 to-rose-600 text-white shadow-md shadow-amber-600/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span>Консерваторский инспектор</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-6 space-y-4">
        {/* Inline Error Banner */}
        {errorMessage && (
          <div
            role="alert"
            className="rounded-xl border border-rose-500/50 bg-rose-950/40 p-4 text-rose-200 shadow-lg backdrop-blur"
          >
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold text-rose-300">
                    Ошибка гармонизации
                  </h3>
                  <button
                    type="button"
                    onClick={() => {
                      setErrorMessage(null);
                      setErrorDiagnostics([]);
                    }}
                    className="text-xs text-rose-400 hover:text-rose-200 transition-colors"
                  >
                    ✕ Закрыть
                  </button>
                </div>
                <p className="mt-1 text-sm text-rose-200 break-words">{errorMessage}</p>
                {errorDiagnostics.length > 0 && (
                  <div className="mt-3 border-t border-rose-900/60 pt-2.5">
                    <span className="text-xs font-semibold uppercase tracking-wider text-rose-400">
                      Диагностика голосоведения:
                    </span>
                    <ul className="mt-1.5 space-y-1 list-disc list-inside text-xs text-rose-300/90 font-mono">
                      {errorDiagnostics.map((diag, idx) => (
                        <li key={idx}>{diag}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "harmonizer" ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column (Input & Controls) */}
            <div className="lg:col-span-5 space-y-6">
              <MelodyInput
                melody={melody}
                onChange={handleMelodyChange}
                selectedKey={selectedKey}
                onAutoDetectKey={handleAutoDetectKey}
                timeSignature={timeSignature}
              />

              <ControlPanel
                keys={canonicalKeys}
                selectedKey={selectedKey}
                onKeyChange={handleKeyChange}
                onAutoDetectKey={handleAutoDetectKey}
                timeSignature={timeSignature}
                onTimeSignatureChange={handleTimeSignatureChange}
                allowExtendedRanges={allowExtendedRanges}
                onToggleExtendedRanges={setAllowExtendedRanges}
                allowSecondaryDominants={allowSecondaryDominants}
                onToggleSecondaryDominants={setAllowSecondaryDominants}
                onHarmonize={handleHarmonize}
                isHarmonizing={isHarmonizing}
                isMelodyEmpty={melody.length === 0}
                latencyMs={latencyMs}
                candidates={candidates}
                selectedCandidateId={selectedCandidate?.id || null}
                onSelectCandidate={handleSelectCandidate}
              />
            </div>

            {/* Right Column (Score Display, Playback & Export for Harmonizer) */}
            <div className="lg:col-span-7 space-y-5">
              {/* Score Display (OSMD) */}
              <ScoreDisplay
                musicxml={activeScoreState.musicxml}
                currentChordIndex={activeScoreState.currentPlaybackIndex}
                problemMeasures={activeScoreState.problemMeasures}
                title={activeScoreState.title}
              />

              {/* Audio Playback Controls */}
              <AudioControls
                voicings={activeScoreState.voicings}
                currentChordIndex={activeScoreState.currentPlaybackIndex}
                onStepChange={(idx) => setPlaybackIndex("harmonizer", idx)}
              />

              {/* One-Click Export from Active Harmonizer State */}
              <ExportBar
                voicings={activeScoreState.voicings}
                chords={activeScoreState.chords}
                keyObj={activeScoreState.key}
                timeSignature={activeScoreState.timeSignature}
                asciiScore={activeScoreState.asciiScore}
                durations={activeScoreState.durations}
              />
            </div>
          </div>
        ) : (
          /* Student Homework Grader Mode */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left: Grader Matrix & Verification */}
            <div className="lg:col-span-6 space-y-6">
              <GraderPanel
                selectedKey={selectedKey}
                timeSignature={timeSignature}
                allowExtendedRanges={allowExtendedRanges}
                onGradeComplete={handleGradeComplete}
                onHighlightMeasure={handleHighlightMeasure}
              />
            </div>

            {/* Right: Real-time Score with error highlighting & audio playback for Grader */}
            <div className="lg:col-span-6 space-y-5">
              <ScoreDisplay
                musicxml={activeScoreState.musicxml}
                currentChordIndex={activeScoreState.currentPlaybackIndex}
                problemMeasures={activeScoreState.problemMeasures}
                title={activeScoreState.title}
              />

              <AudioControls
                voicings={activeScoreState.voicings}
                currentChordIndex={activeScoreState.currentPlaybackIndex}
                onStepChange={(idx) => setPlaybackIndex("grader", idx)}
              />

              {/* One-Click Export from Active Grader State */}
              <ExportBar
                voicings={activeScoreState.voicings}
                chords={activeScoreState.chords}
                keyObj={activeScoreState.key}
                timeSignature={activeScoreState.timeSignature}
                asciiScore={activeScoreState.asciiScore}
                durations={activeScoreState.durations}
              />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500">
        Бригадный Гармонизатор · Строгое соблюдение канонов гармонии (И. И. Способин, И. В. Способин, В. В. Хвостенко, В. А. Вахромеев) · Viterbi Algorithm & Pure Python
      </footer>
    </div>
  );
}

export default App;

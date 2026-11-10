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
import type { GraderReportData } from "./components/GraderPanel";
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

export function App() {
  const [activeTab, setActiveTab] = useState<"harmonizer" | "grader">("harmonizer");

  // Melody & Keys
  const [melody, setMelody] = useState<MelodyNote[]>(INITIAL_MELODY);
  const [canonicalKeys, setCanonicalKeys] = useState<
    Array<{ tonic: string; mode: string; fifths: number; title: string }>
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
  const [activeDurations, setActiveDurations] = useState<string[]>(
    INITIAL_MELODY.map((m) => m.duration)
  );

  const abortControllerRef = useRef<AbortController | null>(null);

  // Score & Playback state
  const [activeMusicXml, setActiveMusicXml] = useState<string>("");
  const [activeVoicings, setActiveVoicings] = useState<SATBVoicing[]>([]);
  const [activeChords, setActiveChords] = useState<string[]>([]);
  const [asciiScore, setAsciiScore] = useState<string>("");
  const [currentPlaybackIndex, setCurrentPlaybackIndex] = useState<number>(-1);
  const [problemMeasures, setProblemMeasures] = useState<number[]>([]);
  const [scoreTitle, setScoreTitle] = useState<string>("Гармонизация мелодии");

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
    setProblemMeasures([]);

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
        setActiveMusicXml("");
        setLatencyMs(null);
        setErrorMessage(detailMsg);
        setErrorDiagnostics([]);
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
        setActiveMusicXml(best.musicxml);
        setActiveVoicings(best.voicings);
        setActiveChords(best.chords);
        setAsciiScore(best.ascii_score);
        setActiveDurations(
          best.durations || melody.map((m) => m.duration)
        );
        setScoreTitle(
          `Решение #${best.rank} · ${best.description} (Стоимость: ${best.cost})`
        );
      } else {
        setCandidates([]);
        setSelectedCandidate(null);
        setActiveMusicXml("");
        setLatencyMs(null);
        const msg =
          data.error?.message ??
          data.message ??
          "Не удалось построить гармонизацию";
        setErrorMessage(msg);

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
      setActiveMusicXml("");
      setLatencyMs(null);
      setErrorMessage(
        e instanceof Error ? e.message : "Не удалось построить гармонизацию"
      );
      setErrorDiagnostics([]);
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
        setSelectedKey({ tonic: data.tonic, mode: data.mode });
      }
    } catch (e) {
      console.error("Key detection error:", e);
    }
  };

  // Candidate selection
  const handleSelectCandidate = (cand: CandidateSolution) => {
    setSelectedCandidate(cand);
    setActiveMusicXml(cand.musicxml);
    setActiveVoicings(cand.voicings);
    setActiveChords(cand.chords);
    setAsciiScore(cand.ascii_score);
    setActiveDurations(
      (cand as unknown as { durations?: string[] }).durations ||
        melody.map((m) => m.duration)
    );
    setScoreTitle(
      `Решение #${cand.rank} · ${cand.description} (Стоимость: ${cand.cost})`
    );
  };

  // Melody change handler
  const handleMelodyChange = (newMelody: MelodyNote[]) => {
    setMelody(newMelody);
    setActiveDurations(newMelody.map((m) => m.duration));
  };

  // Grader complete handler
  const handleGradeComplete = (
    report: GraderReportData,
    musicxml: string,
    voicings: SATBVoicing[]
  ) => {
    setActiveMusicXml(musicxml);
    setActiveVoicings(voicings);
    setProblemMeasures(report.problem_measures);
    setScoreTitle(`Инспектор: ${report.grade}`);
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
              />

              <ControlPanel
                keys={canonicalKeys}
                selectedKey={selectedKey}
                onKeyChange={setSelectedKey}
                onAutoDetectKey={handleAutoDetectKey}
                timeSignature={timeSignature}
                onTimeSignatureChange={setTimeSignature}
                allowExtendedRanges={allowExtendedRanges}
                onToggleExtendedRanges={setAllowExtendedRanges}
                allowSecondaryDominants={allowSecondaryDominants}
                onToggleSecondaryDominants={setAllowSecondaryDominants}
                onHarmonize={handleHarmonize}
                isHarmonizing={isHarmonizing}
                latencyMs={latencyMs}
                candidates={candidates}
                selectedCandidateId={selectedCandidate?.id || null}
                onSelectCandidate={handleSelectCandidate}
              />
            </div>

            {/* Right Column (Score Display, Playback & Export) */}
            <div className="lg:col-span-7 space-y-5">
              {/* Score Display (OSMD) */}
              <ScoreDisplay
                musicxml={activeMusicXml}
                currentChordIndex={currentPlaybackIndex}
                problemMeasures={problemMeasures}
                title={scoreTitle}
              />

              {/* Audio Playback Controls */}
              <AudioControls
                voicings={activeVoicings}
                currentChordIndex={currentPlaybackIndex}
                onStepChange={setCurrentPlaybackIndex}
              />

              {/* One-Click Export */}
              <ExportBar
                voicings={activeVoicings}
                chords={activeChords}
                keyObj={selectedKey}
                timeSignature={timeSignature}
                asciiScore={asciiScore}
                durations={activeDurations}
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
                allowExtendedRanges={allowExtendedRanges}
                onGradeComplete={handleGradeComplete}
                onHighlightMeasure={(m) => setProblemMeasures([m])}
              />
            </div>

            {/* Right: Real-time Score with error highlighting & audio playback */}
            <div className="lg:col-span-6 space-y-5">
              <ScoreDisplay
                musicxml={activeMusicXml}
                currentChordIndex={currentPlaybackIndex}
                problemMeasures={problemMeasures}
                title={scoreTitle}
              />

              <AudioControls
                voicings={activeVoicings}
                currentChordIndex={currentPlaybackIndex}
                onStepChange={setCurrentPlaybackIndex}
              />

              <ExportBar
                voicings={activeVoicings}
                chords={activeChords}
                keyObj={selectedKey}
                timeSignature={timeSignature}
                asciiScore={asciiScore}
                durations={activeDurations}
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

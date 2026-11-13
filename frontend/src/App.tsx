import { useState, useRef, useEffect, lazy, Suspense } from "react";
import { AlertCircle } from "lucide-react";
import { Header } from "./components/layout/Header";
import { MelodyInput } from "./components/MelodyInput";
import { ControlPanel } from "./components/ControlPanel";
import { AudioControls } from "./components/AudioControls";
import { GraderPanel } from "./components/GraderPanel";
import type { GraderReportData, GraderMeta } from "./components/GraderPanel";
import { ExportBar } from "./components/ExportBar";
import { useHarmonizer } from "./hooks/useHarmonizer";
import type { TabScoreState } from "./types/harmony";
import type { MelodyNote } from "./utils/durationUtils";
import type { SATBVoicing } from "./audio/synth";

const ScoreDisplay = lazy(() =>
  import("./components/ScoreDisplay").then((m) => ({ default: m.ScoreDisplay }))
);

const ScoreFallback = (
  <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-surface-elevated p-6 text-text-muted">
    <div className="flex items-center gap-2 text-sm">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand border-t-transparent" />
      <span>Загрузка партитуры (OSMD)...</span>
    </div>
  </div>
);

const INITIAL_MELODY: MelodyNote[] = [
  { pitch: 64, name: "E4", duration: "half", is_downbeat: true },
  { pitch: 65, name: "F4", duration: "half", is_downbeat: false },
  { pitch: 67, name: "G4", duration: "half", is_downbeat: true },
  { pitch: 64, name: "E4", duration: "half", is_downbeat: false },
  { pitch: 62, name: "D4", duration: "half", is_downbeat: true },
  { pitch: 60, name: "C4", duration: "whole", is_downbeat: false },
];

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

  const {
    melody,
    setMelody,
    canonicalKeys,
    selectedKey,
    setSelectedKey,
    timeSignature,
    setTimeSignature,
    allowExtendedRanges,
    setAllowExtendedRanges,
    allowSecondaryDominants,
    setAllowSecondaryDominants,
    isHarmonizing,
    latencyMs,
    candidates,
    selectedCandidate,
    errorMessage,
    setErrorMessage,
    errorDiagnostics,
    setErrorDiagnostics,
    harmonizerScore,
    setHarmonizerScore,
    handleHarmonize,
    handleAutoDetectKey,
    handleSelectCandidate,
    abortControllerRef,
  } = useHarmonizer(INITIAL_MELODY);

  const [graderScore, setGraderScore] = useState<TabScoreState>(INITIAL_GRADER_STATE);

  const initialHarmonizeRef = useRef(false);
  useEffect(() => {
    if (!initialHarmonizeRef.current) {
      initialHarmonizeRef.current = true;
      handleHarmonize();
    }
    // Capture the ref value in the effect body (react-hooks/exhaustive-deps):
    // handleHarmonize sets abortControllerRef.current synchronously before its
    // first await, so this snapshot is the in-flight request to abort on cleanup.
    const controller = abortControllerRef.current;
    return () => {
      if (controller) {
        controller.abort();
      }
    };
  }, [handleHarmonize, abortControllerRef]);

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

  const handleHighlightMeasure = (m: number) => {
    setGraderScore((prev) => ({
      ...prev,
      problemMeasures: [m],
    }));
  };

  return (
    <div className="min-h-screen bg-surface-subtle text-text-primary flex flex-col font-sans transition-colors">
      <Header activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-6 space-y-4">
        {errorMessage && (
          <div
            role="alert"
            className="rounded-xl border border-rose-500/50 bg-rose-950/40 p-4 text-rose-200 shadow-lg backdrop-blur"
          >
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold text-rose-300">Ошибка гармонизации</h3>
                  <button
                    type="button"
                    onClick={() => {
                      setErrorMessage(null);
                      setErrorDiagnostics([]);
                    }}
                    className="text-xs text-rose-400 hover:text-rose-200 transition-colors focus-ring rounded"
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
          <div
            id="panel-harmonizer"
            role="tabpanel"
            aria-labelledby="tab-harmonizer"
            className="flex flex-col lg:flex-row gap-6 items-start"
          >
            <div className="w-full lg:w-[420px] shrink-0 space-y-6 max-h-[calc(100vh-6rem)] overflow-y-auto pr-1">
              <MelodyInput
                melody={melody}
                onChange={setMelody}
                onAutoDetectKey={handleAutoDetectKey}
                timeSignature={timeSignature}
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
                isMelodyEmpty={melody.length === 0}
                latencyMs={latencyMs}
                candidates={candidates}
                selectedCandidateId={selectedCandidate?.id || null}
                onSelectCandidate={handleSelectCandidate}
              />
            </div>

            <div className="flex-1 min-w-0 space-y-5">
              <Suspense fallback={ScoreFallback}>
                <ScoreDisplay
                  musicxml={harmonizerScore.musicxml}
                  currentChordIndex={harmonizerScore.currentPlaybackIndex}
                  problemMeasures={harmonizerScore.problemMeasures}
                  title={harmonizerScore.title}
                />
              </Suspense>

              <AudioControls
                voicings={harmonizerScore.voicings}
                currentChordIndex={harmonizerScore.currentPlaybackIndex}
                onStepChange={(idx) =>
                  setHarmonizerScore((prev) => ({ ...prev, currentPlaybackIndex: idx }))
                }
              />

              <ExportBar
                voicings={harmonizerScore.voicings}
                chords={harmonizerScore.chords}
                keyObj={harmonizerScore.key}
                timeSignature={harmonizerScore.timeSignature}
                asciiScore={harmonizerScore.asciiScore}
                durations={harmonizerScore.durations}
              />
            </div>
          </div>
        ) : (
          <div
            id="panel-grader"
            role="tabpanel"
            aria-labelledby="tab-grader"
            className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start"
          >
            <div className="lg:col-span-6 space-y-6">
              <GraderPanel
                selectedKey={selectedKey}
                timeSignature={timeSignature}
                allowExtendedRanges={allowExtendedRanges}
                onGradeComplete={handleGradeComplete}
                onHighlightMeasure={handleHighlightMeasure}
              />
            </div>

            <div className="lg:col-span-6 space-y-5">
              <Suspense fallback={ScoreFallback}>
                <ScoreDisplay
                  musicxml={graderScore.musicxml}
                  currentChordIndex={graderScore.currentPlaybackIndex}
                  problemMeasures={graderScore.problemMeasures}
                  title={graderScore.title}
                />
              </Suspense>

              <AudioControls
                voicings={graderScore.voicings}
                currentChordIndex={graderScore.currentPlaybackIndex}
                onStepChange={(idx) =>
                  setGraderScore((prev) => ({ ...prev, currentPlaybackIndex: idx }))
                }
              />

              <ExportBar
                voicings={graderScore.voicings}
                chords={graderScore.chords}
                keyObj={graderScore.key}
                timeSignature={graderScore.timeSignature}
                asciiScore={graderScore.asciiScore}
                durations={graderScore.durations}
              />
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-border bg-surface py-4 px-6 text-center text-xs text-text-muted">
        Бригадный Гармонизатор · Строгое соблюдение канонов гармонии (И. Дубовский, С. Евсеев, И. В. Способин, В. Соколов) · Viterbi Algorithm &amp; Pure Python
      </footer>
    </div>
  );
}

export default App;

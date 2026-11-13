import { useState, useEffect, useRef, useCallback } from "react";
import { recalculateDownbeats } from "../utils/durationUtils";
import type { MelodyNote } from "../utils/durationUtils";
import type { CandidateSolution } from "../components/ControlPanel";
import type { TabScoreState } from "../types/harmony";

export interface CanonicalKey {
  tonic: string;
  mode: string;
  fifths: number;
  title?: string;
  name?: string;
}

export function useHarmonizer(initialMelody: MelodyNote[]) {
  const [melody, setMelody] = useState<MelodyNote[]>(initialMelody);
  const [canonicalKeys, setCanonicalKeys] = useState<CanonicalKey[]>([]);
  const [selectedKey, setSelectedKey] = useState<{ tonic: string; mode: string }>({
    tonic: "C",
    mode: "Major",
  });
  const [timeSignature, setTimeSignatureState] = useState<string>("4/4");
  // Event-driven meter change: recalculate downbeats here (not in an effect),
  // keeping the auto-strong-beats feature without setState-in-effect.
  const setTimeSignature = useCallback((next: string) => {
    setTimeSignatureState(next);
    setMelody((prev) => (prev.length > 0 ? recalculateDownbeats(prev, next) : prev));
  }, []);
  const [allowExtendedRanges, setAllowExtendedRanges] = useState<boolean>(false);
  const [allowSecondaryDominants, setAllowSecondaryDominants] = useState<boolean>(true);

  const [isHarmonizing, setIsHarmonizing] = useState<boolean>(false);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [candidates, setCandidates] = useState<CandidateSolution[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateSolution | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorDiagnostics, setErrorDiagnostics] = useState<string[]>([]);

  const [harmonizerScore, setHarmonizerScore] = useState<TabScoreState>({
    musicxml: "",
    voicings: [],
    chords: [],
    asciiScore: "",
    title: "Гармонизация мелодии",
    problemMeasures: [],
    durations: initialMelody.map((m) => m.duration),
    key: { tonic: "C", mode: "Major" },
    timeSignature: "4/4",
    currentPlaybackIndex: -1,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  // Load canonical keys on mount
  useEffect(() => {
    fetch("/api/keys")
      .then((res) => res.json())
      .then((data) => setCanonicalKeys(data))
      .catch((err) => console.error("Failed to load keys:", err));
  }, []);

  // Harmonize function
  const handleHarmonize = useCallback(async () => {
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
        const errData = await resp.json().catch(() => ({}));
        let detailMsg = `Ошибка сервера (${resp.status})`;
        if (errData.detail) {
          detailMsg = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
        } else if (errData.message) {
          detailMsg = errData.message;
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
      setLatencyMs(data.latency_ms || null);

      const candidateList = data.candidates || data.solutions || [];
      if (data.is_success && candidateList.length > 0) {
        setCandidates(candidateList);
        const best = data.best_candidate || candidateList[0];
        setSelectedCandidate(best);
        setErrorMessage(null);
        setErrorDiagnostics([]);

        const bestDurs = best.durations || melody.map((m) => m.duration);
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
          title: `Решение #${best.rank} · ${best.description} (Штраф: ${Math.abs(best.cost)})`,
        }));
      } else {
        setCandidates([]);
        setSelectedCandidate(null);
        const msg = data.error?.message ?? data.message ?? "Не найдено допустимого решения голосоведения.";
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
        setHarmonizerScore((prev) => ({
          ...prev,
          musicxml: "",
          voicings: [],
          chords: [],
          asciiScore: "",
          problemMeasures: [],
        }));
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      setErrorMessage(err instanceof Error ? err.message : "Ошибка связи с сервером гармонизации.");
    } finally {
      if (abortControllerRef.current === controller) {
        setIsHarmonizing(false);
      }
    }
  }, [melody, selectedKey, timeSignature, allowExtendedRanges, allowSecondaryDominants]);

  // Key Auto-detection
  const handleAutoDetectKey = useCallback(async () => {
    if (!melody || melody.length === 0) return;
    try {
      const resp = await fetch("/api/detect-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(melody.map((m) => ({ pitch: m.pitch, name: m.name }))),
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
  }, [melody]);

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

  return {
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
  };
}

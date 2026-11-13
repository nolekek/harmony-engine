import type { SATBVoicing } from "../audio/synth";

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

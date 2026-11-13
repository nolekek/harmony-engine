import type { SATBVoicing } from "../../audio/synth";

export interface GraderSampleTest {
  name: string;
  key: { tonic: string; mode: string };
  timeSignature: string;
  voicings: SATBVoicing[];
  chords: string[];
  durations: string[];
}

export const SAMPLE_TESTS: GraderSampleTest[] = [
  {
    name: "Задача с грубыми ошибками (Параллельные квинты/октавы)",
    key: { tonic: "C", mode: "Major" },
    timeSignature: "4/4",
    voicings: [
      { soprano: 67, alto: 60, tenor: 55, bass: 48 },
      { soprano: 69, alto: 62, tenor: 57, bass: 50 },
      { soprano: 67, alto: 64, tenor: 55, bass: 48 },
    ],
    chords: ["T", "II", "T"],
    durations: ["half", "half", "half"],
  },
  {
    name: "Эталонное решение (Способин, без ошибок)",
    key: { tonic: "C", mode: "Major" },
    timeSignature: "4/4",
    voicings: [
      { soprano: 64, alto: 60, tenor: 55, bass: 48 },
      { soprano: 65, alto: 60, tenor: 57, bass: 45 },
      { soprano: 65, alto: 60, tenor: 57, bass: 41 },
      { soprano: 64, alto: 60, tenor: 55, bass: 48 },
      { soprano: 62, alto: 59, tenor: 55, bass: 43 },
      { soprano: 60, alto: 60, tenor: 55, bass: 48 },
    ],
    chords: ["T", "VI", "S", "T", "D", "T"],
    durations: ["half", "half", "half", "half", "half", "half"],
  },
];

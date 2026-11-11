/**
 * Polyphonic WebAudio Synthesizer for 4-part SATB harmony.
 * Features 3 instrument presets (Piano, Choir Pad, Church Organ),
 * individual Solo/Mute controls per voice (S, A, T, B), and timed score cursor playback.
 */

export type InstrumentPreset = "piano" | "choir" | "organ";

export interface SATBVoicing {
  soprano: number;
  alto: number;
  tenor: number;
  bass: number;
  measure?: number;
  is_downbeat?: boolean;
  duration?: string;
}

export class AudioEngine {
  private ctx: AudioContext | null = null;
  private voiceGains: GainNode[] = [];
  private masterGain: GainNode | null = null;
  private preset: InstrumentPreset = "piano";
  private isPlaying: boolean = false;
  private playbackTimer: number | null = null;

  public mutes: [boolean, boolean, boolean, boolean] = [false, false, false, false];
  public solos: [boolean, boolean, boolean, boolean] = [false, false, false, false];

  constructor() {
    // Lazy initialized on first user gesture
  }

  private initCtx() {
    if (!this.ctx) {
      const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AudioCtxClass();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(0.7, this.ctx.currentTime);
      this.masterGain.connect(this.ctx.destination);

      this.voiceGains = [0, 1, 2, 3].map(() => {
        const g = this.ctx!.createGain();
        g.connect(this.masterGain!);
        return g;
      });
    }
    if (this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  public setPreset(preset: InstrumentPreset) {
    this.preset = preset;
  }

  public setMute(voiceIdx: number, muted: boolean) {
    this.mutes[voiceIdx] = muted;
    this.updateGains();
  }

  public setSolo(voiceIdx: number, soloed: boolean) {
    this.solos[voiceIdx] = soloed;
    this.updateGains();
  }

  private updateGains() {
    if (!this.ctx || this.voiceGains.length < 4) return;
    const hasSolo = this.solos.some((s) => s);

    for (let i = 0; i < 4; i++) {
      let active = true;
      if (hasSolo) {
        active = this.solos[i];
      } else if (this.mutes[i]) {
        active = false;
      }
      this.voiceGains[i].gain.setValueAtTime(active ? 1.0 : 0.0, this.ctx.currentTime);
    }
  }

  private midiToFreq(midi: number): number {
    return 440 * Math.pow(2, (midi - 69) / 12);
  }

  /**
   * Triggers a single voice note according to the selected instrument preset.
   */
  public playNote(voiceIdx: number, midiPitch: number, durationSec: number = 1.0) {
    this.initCtx();
    if (!this.ctx) return;

    this.updateGains();
    const dest = this.voiceGains[voiceIdx];
    const freq = this.midiToFreq(midiPitch);
    const now = this.ctx.currentTime;

    if (this.preset === "piano") {
      // Piano: warm percussive attack, rich harmonics
      const osc1 = this.ctx.createOscillator();
      const osc2 = this.ctx.createOscillator();
      const noteGain = this.ctx.createGain();
      const filter = this.ctx.createBiquadFilter();

      filter.type = "lowpass";
      filter.frequency.setValueAtTime(freq * 5, now);
      filter.frequency.exponentialRampToValueAtTime(Math.max(freq * 1.2, 100), now + durationSec);

      osc1.type = "triangle";
      osc1.frequency.setValueAtTime(freq, now);

      osc2.type = "sine";
      osc2.frequency.setValueAtTime(freq, now);

      // Attack / Decay envelope
      noteGain.gain.setValueAtTime(0.001, now);
      noteGain.gain.linearRampToValueAtTime(0.35, now + 0.015);
      noteGain.gain.exponentialRampToValueAtTime(0.0001, now + durationSec);

      osc1.connect(filter);
      osc2.connect(filter);
      filter.connect(noteGain);
      noteGain.connect(dest);

      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + durationSec + 0.05);
      osc2.stop(now + durationSec + 0.05);
    } else if (this.preset === "choir") {
      // Choir Pad: lush detuned triangle/saw with slow vocal formant envelope
      const oscA = this.ctx.createOscillator();
      const oscB = this.ctx.createOscillator();
      const noteGain = this.ctx.createGain();
      const filter = this.ctx.createBiquadFilter();

      filter.type = "bandpass";
      filter.frequency.setValueAtTime(Math.min(freq * 2, 2500), now);
      filter.Q.setValueAtTime(3.0, now);

      oscA.type = "sawtooth";
      oscA.frequency.setValueAtTime(freq, now);
      oscA.detune.setValueAtTime(-6, now);

      oscB.type = "triangle";
      oscB.frequency.setValueAtTime(freq, now);
      oscB.detune.setValueAtTime(6, now);

      noteGain.gain.setValueAtTime(0.001, now);
      noteGain.gain.linearRampToValueAtTime(0.22, now + 0.12);
      noteGain.gain.setValueAtTime(0.2, now + durationSec - 0.1);
      noteGain.gain.exponentialRampToValueAtTime(0.0001, now + durationSec + 0.2);

      oscA.connect(filter);
      oscB.connect(filter);
      filter.connect(noteGain);
      noteGain.connect(dest);

      oscA.start(now);
      oscB.start(now);
      oscA.stop(now + durationSec + 0.25);
      oscB.stop(now + durationSec + 0.25);
    } else if (this.preset === "organ") {
      // Church Organ: additive drawbars (8', 4', 2 2/3', 2')
      const freqs = [freq, freq * 2, freq * 3, freq * 4];
      const weights = [0.2, 0.12, 0.08, 0.05];

      const noteGain = this.ctx.createGain();
      noteGain.gain.setValueAtTime(0.001, now);
      noteGain.gain.linearRampToValueAtTime(0.25, now + 0.04);
      noteGain.gain.setValueAtTime(0.25, now + durationSec - 0.03);
      noteGain.gain.linearRampToValueAtTime(0.001, now + durationSec);

      freqs.forEach((f, i) => {
        const osc = this.ctx!.createOscillator();
        const g = this.ctx!.createGain();
        osc.type = i === 0 ? "triangle" : "sine";
        osc.frequency.setValueAtTime(f, now);
        g.gain.setValueAtTime(weights[i], now);

        osc.connect(g);
        g.connect(noteGain);

        osc.start(now);
        osc.stop(now + durationSec + 0.05);
      });

      noteGain.connect(dest);
    }
  }

  /**
   * Plays full SATB vertical chord slice.
   */
  public playChord(voicing: SATBVoicing, durationSec: number = 1.2) {
    this.playNote(0, voicing.soprano, durationSec);
    this.playNote(1, voicing.alto, durationSec);
    this.playNote(2, voicing.tenor, durationSec);
    this.playNote(3, voicing.bass, durationSec);
  }

  /**
   * Sequentially plays through voicings with cursor synchronization.
   */
  public playSequence(
    voicings: SATBVoicing[],
    bpm: number,
    onStep: (index: number) => void,
    onFinish: () => void
  ) {
    this.stop();
    if (!voicings.length) return;

    this.initCtx();
    this.isPlaying = true;

    const beatDurationSec = 60 / bpm;
    // Each chord in Brigade textbook is default half note = 2 beats
    const chordDurationSec = beatDurationSec * 2;
    const intervalMs = chordDurationSec * 1000;

    let currentIndex = 0;

    const playNext = () => {
      if (!this.isPlaying) return;

      if (currentIndex >= voicings.length) {
        this.stop();
        onFinish();
        return;
      }

      const v = voicings[currentIndex];
      this.playChord(v, chordDurationSec * 0.95);
      onStep(currentIndex);

      currentIndex++;
      this.playbackTimer = window.setTimeout(playNext, intervalMs);
    };

    playNext();
  }

  public stop() {
    this.isPlaying = false;
    if (this.playbackTimer !== null) {
      clearTimeout(this.playbackTimer);
      this.playbackTimer = null;
    }
  }

  public getIsPlaying(): boolean {
    return this.isPlaying;
  }
}

export const audioEngine = new AudioEngine();

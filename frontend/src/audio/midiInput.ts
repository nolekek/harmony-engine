/**
 * Web MIDI API Manager with live metronome recording for soprano melody input.
 */

export interface MidiDevice {
  id: string;
  name: string;
  manufacturer: string;
}

export type MidiNoteCallback = (pitch: number, isDownbeat: boolean) => void;

interface LocalMidiMessageEvent {
  data: Uint8Array | number[];
}

interface LocalMidiInput {
  id: string;
  name?: string;
  manufacturer?: string;
  onmidimessage: ((event: LocalMidiMessageEvent) => void) | null;
}

interface LocalMidiAccess {
  inputs: {
    forEach: (callback: (input: LocalMidiInput) => void) => void;
    get: (id: string) => LocalMidiInput | undefined;
  };
}

export class WebMidiManager {
  private midiAccess: LocalMidiAccess | null = null;
  private currentInput: LocalMidiInput | null = null;
  private isRecording: boolean = false;
  private metronomeTimer: number | null = null;
  private beatCounter: number = 0;
  private onNoteCallback: MidiNoteCallback | null = null;

  public async requestAccess(): Promise<MidiDevice[]> {
    const nav = navigator as unknown as {
      requestMIDIAccess?: (opts?: { sysex?: boolean }) => Promise<LocalMidiAccess>;
    };
    if (!nav.requestMIDIAccess) {
      throw new Error("Web MIDI API не поддерживается в этом браузере.");
    }
    this.midiAccess = await nav.requestMIDIAccess({ sysex: false });
    return this.getAvailableDevices();
  }

  public getAvailableDevices(): MidiDevice[] {
    if (!this.midiAccess) return [];
    const devices: MidiDevice[] = [];
    this.midiAccess.inputs.forEach((input: LocalMidiInput) => {
      devices.push({
        id: input.id,
        name: input.name || "MIDI Keyboard",
        manufacturer: input.manufacturer || "Generic",
      });
    });
    return devices;
  }

  public connectDevice(deviceId: string) {
    if (!this.midiAccess) return;
    this.currentInput = this.midiAccess.inputs.get(deviceId) || null;
    if (this.currentInput) {
      this.currentInput.onmidimessage = this.handleMidiMessage.bind(this);
    }
  }

  public startRecording(
    bpm: number,
    onNote: MidiNoteCallback,
    onMetronomeTick?: (beat: number) => void
  ) {
    this.isRecording = true;
    this.onNoteCallback = onNote;
    this.beatCounter = 0;

    const intervalMs = (60 / bpm) * 1000;

    // Start metronome click
    const playTick = () => {
      if (!this.isRecording) return;
      this.beatCounter++;
      const measureBeat = ((this.beatCounter - 1) % 4) + 1;
      this.playClick(measureBeat === 1);
      if (onMetronomeTick) onMetronomeTick(measureBeat);
      this.metronomeTimer = window.setTimeout(playTick, intervalMs);
    };

    playTick();
  }

  public stopRecording() {
    this.isRecording = false;
    this.onNoteCallback = null;
    if (this.metronomeTimer !== null) {
      clearTimeout(this.metronomeTimer);
      this.metronomeTimer = null;
    }
  }

  private handleMidiMessage(event: LocalMidiMessageEvent) {
    if (!this.isRecording || !this.onNoteCallback) return;
    const data = event.data;
    const status = data[0];
    const note = data[1];
    const velocity = data[2];
    const command = status >> 4;

    // Note On with velocity > 0
    if (command === 9 && velocity > 0) {
      // Metric check: if current beat in 4/4 is 1 or 3 -> downbeat
      const beatInMeasure = ((this.beatCounter - 1) % 4) + 1;
      const isDownbeat = beatInMeasure === 1 || beatInMeasure === 3;
      this.onNoteCallback(note, isDownbeat);
    }
  }

  private playClick(isDownbeat: boolean) {
    try {
      const AudioCtxClass =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtxClass();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.frequency.setValueAtTime(isDownbeat ? 1200 : 800, ctx.currentTime);
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.09);
    } catch {
      // Ignore audio click error
    }
  }
}

export const webMidiManager = new WebMidiManager();

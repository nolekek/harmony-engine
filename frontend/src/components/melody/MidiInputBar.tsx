import React, { useEffect, useRef, useState } from "react";
import { Radio, AlertCircle, Circle, Square } from "lucide-react";
import { webMidiManager } from "../../audio/midiInput";
import type { MidiDevice } from "../../audio/midiInput";
import { Button } from "../ui/Button";

interface MidiInputBarProps {
  onNoteReceived: (pitch: number, isDownbeat: boolean) => void;
  timeSignature: string;
}

/**
 * Web MIDI input bar built on the REAL WebMidiManager API:
 * requestAccess() → MidiDevice[], connectDevice(id), startRecording(bpm,
 * onNote(pitch, isDownbeat), onMetronomeTick, timeSignature), stopRecording().
 * Notes only arrive while recording is active (metronome-driven downbeats).
 */
export const MidiInputBar: React.FC<MidiInputBarProps> = ({
  onNoteReceived,
  timeSignature,
}) => {
  const [devices, setDevices] = useState<MidiDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>("");
  const [isRecording, setIsRecording] = useState(false);
  const [metronomeBpm, setMetronomeBpm] = useState<number>(80);
  const [activeBeat, setActiveBeat] = useState<number>(0);
  const [lastNote, setLastNote] = useState<number | null>(null);
  const [accessError, setAccessError] = useState<string | null>(null);

  const supported = webMidiManager.isSupported();
  const onNoteRef = useRef(onNoteReceived);
  useEffect(() => {
    onNoteRef.current = onNoteReceived;
  }, [onNoteReceived]);

  useEffect(() => {
    if (!supported) return;
    let cancelled = false;

    webMidiManager
      .requestAccess()
      .then((devs) => {
        if (cancelled) return;
        setDevices(devs);
        if (devs.length > 0) {
          setSelectedDevice(devs[0].id);
          webMidiManager.connectDevice(devs[0].id);
        }
      })
      .catch(() => {
        if (!cancelled) setAccessError("Доступ к Web MIDI не получен.");
      });

    return () => {
      cancelled = true;
      webMidiManager.stopRecording();
      webMidiManager.disconnectDevice();
    };
  }, [supported]);

  const beginRecording = (bpm: number) => {
    if (selectedDevice) webMidiManager.connectDevice(selectedDevice);
    webMidiManager.startRecording(
      bpm,
      (pitch: number, isDownbeat: boolean) => {
        setLastNote(pitch);
        onNoteRef.current(pitch, isDownbeat);
        window.setTimeout(() => setLastNote(null), 300);
      },
      (beat: number) => setActiveBeat(beat),
      timeSignature
    );
    setIsRecording(true);
  };

  const handleToggleRecording = () => {
    if (isRecording) {
      webMidiManager.stopRecording();
      setIsRecording(false);
      setActiveBeat(0);
    } else {
      beginRecording(metronomeBpm);
    }
  };

  const handleBpmChange = (value: number) => {
    const clamped = Math.min(200, Math.max(40, value || 80));
    setMetronomeBpm(clamped);
    if (isRecording) {
      webMidiManager.stopRecording();
      beginRecording(clamped);
    }
  };

  const handleDeviceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const devId = e.target.value;
    setSelectedDevice(devId);
    webMidiManager.connectDevice(devId);
  };

  if (!supported) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-surface-subtle border border-border rounded-lg text-xs text-text-muted">
        <AlertCircle className="w-3.5 h-3.5 shrink-0" />
        <span>Web MIDI не поддерживается в этом браузере — используйте пианино ниже.</span>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-3 py-2 bg-surface-subtle border border-border rounded-lg text-xs">
      <div className="flex items-center gap-2">
        <Radio
          className={`w-3.5 h-3.5 ${devices.length > 0 ? "text-brand" : "text-text-muted"}`}
        />
        <span className="text-text-secondary font-medium">MIDI клавиатура:</span>
      </div>

      {accessError ? (
        <span className="text-text-muted italic flex items-center gap-1">
          <AlertCircle className="w-3 h-3" /> {accessError}
        </span>
      ) : devices.length === 0 ? (
        <span className="text-text-muted italic flex items-center gap-1">
          <AlertCircle className="w-3 h-3" /> Устройства не подключены
        </span>
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={selectedDevice}
            onChange={handleDeviceChange}
            aria-label="Выбор MIDI устройства"
            className="bg-surface-panel border border-border text-text-primary px-2 py-1 rounded text-xs focus-ring cursor-pointer max-w-40"
          >
            {devices.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>

          <label className="flex items-center gap-1 text-text-muted">
            <span className="font-mono">BPM</span>
            <input
              type="number"
              min={40}
              max={200}
              value={metronomeBpm}
              onChange={(e) => handleBpmChange(Number(e.target.value))}
              aria-label="Темп метронома MIDI-записи"
              className="w-14 bg-surface-panel border border-border text-text-primary px-1.5 py-0.5 rounded text-xs font-mono text-center focus-ring"
            />
          </label>

          <Button
            variant={isRecording ? "danger" : "primary"}
            size="xs"
            onClick={handleToggleRecording}
            aria-label={isRecording ? "Остановить MIDI-запись" : "Начать MIDI-запись"}
            icon={
              isRecording ? <Square className="w-3 h-3" /> : <Circle className="w-3 h-3" />
            }
          >
            {isRecording ? "Стоп" : "Запись"}
          </Button>

          {isRecording && (
            <span
              className="font-mono text-text-muted"
              aria-live="polite"
              aria-label={`Доля ${activeBeat}`}
            >
              ♩ {activeBeat}
            </span>
          )}

          {lastNote !== null && (
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block" />
          )}
        </div>
      )}
    </div>
  );
};

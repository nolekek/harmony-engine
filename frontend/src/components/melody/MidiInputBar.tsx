import React, { useEffect, useState } from "react";
import { Radio, AlertCircle } from "lucide-react";
import { webMidiManager } from "../../audio/midiInput";
import type { MidiDevice } from "../../audio/midiInput";

interface MidiInputBarProps {
  onNoteReceived: (pitch: number) => void;
}

export const MidiInputBar: React.FC<MidiInputBarProps> = ({ onNoteReceived }) => {
  const [isSupported, setIsSupported] = useState(false);
  const [devices, setDevices] = useState<MidiDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>("");
  const [lastNote, setLastNote] = useState<number | null>(null);

  useEffect(() => {
    const supported = webMidiManager.isSupported();
    setIsSupported(supported);
    if (!supported) return;

    webMidiManager
      .requestAccess()
      .then((ok) => {
        if (ok) {
          const devs = webMidiManager.getDevices();
          setDevices(devs);
          if (devs.length > 0) {
            setSelectedDevice(devs[0].id);
            webMidiManager.selectDevice(devs[0].id);
          }
        }
      })
      .catch((e) => console.debug("WebMIDI access not granted:", e));

    const unsub = webMidiManager.onNoteOn((note) => {
      setLastNote(note);
      onNoteReceived(note);
      setTimeout(() => setLastNote(null), 300);
    });

    return () => unsub();
  }, [onNoteReceived]);

  const handleDeviceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const devId = e.target.value;
    setSelectedDevice(devId);
    webMidiManager.selectDevice(devId);
  };

  if (!isSupported) {
    return null;
  }

  return (
    <div className="flex items-center justify-between gap-3 px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs">
      <div className="flex items-center gap-2">
        <Radio className={`w-3.5 h-3.5 ${devices.length > 0 ? "text-indigo-400" : "text-slate-500"}`} />
        <span className="text-slate-300 font-medium">MIDI клавиатура:</span>
      </div>

      {devices.length === 0 ? (
        <span className="text-slate-500 italic flex items-center gap-1">
          <AlertCircle className="w-3 h-3" /> Устройства не подключены
        </span>
      ) : (
        <div className="flex items-center gap-2">
          <select
            value={selectedDevice}
            onChange={handleDeviceChange}
            aria-label="Выбор MIDI устройства"
            className="bg-slate-950 border border-slate-700 text-slate-200 px-2 py-1 rounded text-xs focus-ring"
          >
            {devices.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          {lastNote !== null && (
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block" />
          )}
        </div>
      )}
    </div>
  );
};

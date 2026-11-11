import React, { useState, useEffect, useRef } from "react";
import {
  Music,
  Piano,
  Upload,
  FileCode,
  Radio,
  Play,
  Square,
  Trash2,
  Clock,
  Sparkles,
} from "lucide-react";
import { audioEngine } from "../audio/synth";
import { webMidiManager } from "../audio/midiInput";
import type { MidiDevice } from "../audio/midiInput";

export interface MelodyNote {
  pitch: number;
  name: string;
  duration: string; // "whole" | "half" | "quarter" | "eighth"
  is_downbeat: boolean;
}

interface MelodyInputProps {
  melody: MelodyNote[];
  onChange: (newMelody: MelodyNote[]) => void;
  selectedKey: { tonic: string; mode: string };
  onAutoDetectKey: () => void;
  timeSignature?: string;
}

const DURATIONS = [
  { id: "whole", label: "1", hint: "Целая", beats: 4 },
  { id: "dotted_half", label: "3/4", hint: "Половинная с точкой", beats: 3 },
  { id: "half", label: "1/2", hint: "Половинная", beats: 2 },
  { id: "dotted_quarter", label: "3/8", hint: "Четверть с точкой", beats: 1.5 },
  { id: "quarter", label: "1/4", hint: "Четверть", beats: 1 },
  { id: "dotted_eighth", label: "3/16", hint: "Восьмая с точкой", beats: 0.75 },
  { id: "eighth", label: "1/8", hint: "Восьмая", beats: 0.5 },
];

const DURATION_BEATS_MAP: Record<string, number> = {
  whole: 4,
  dotted_half: 3,
  half: 2,
  dotted_quarter: 1.5,
  quarter: 1,
  dotted_eighth: 0.75,
  eighth: 0.5,
};

export function recalculateDownbeats(
  notes: MelodyNote[],
  timeSignature: string = "4/4"
): MelodyNote[] {
  const parts = timeSignature.split("/");
  const beats = parseInt(parts[0], 10) || 4;
  const beatType = parseInt(parts[1], 10) || 4;
  const measureQuarters = beats * (4.0 / beatType);

  let currentOffset = 0.0;
  return notes.map((note) => {
    while (currentOffset >= measureQuarters - 1e-4) {
      currentOffset -= measureQuarters;
    }
    if (Math.abs(currentOffset) < 1e-4) {
      currentOffset = 0.0;
    }

    // Only a measure start is a harmonization downbeat; secondary accents
    // (beat 3 in 4/4, beat 4 in 6/8) stay weak so passing tones can be NCTs.
    const isDownbeat = Math.abs(currentOffset) < 1e-4;

    const dur = DURATION_BEATS_MAP[note.duration] ?? 2;
    currentOffset += dur;

    return {
      ...note,
      is_downbeat: isDownbeat,
    };
  });
}

// C4 to A5 natural and accidental notes
const STAFF_PITCHES = [
  { pitch: 81, name: "A5", staffPos: 11, accidental: "" },
  { pitch: 80, name: "G#5", staffPos: 10, accidental: "#" },
  { pitch: 79, name: "G5", staffPos: 10, accidental: "" },
  { pitch: 78, name: "F#5", staffPos: 9, accidental: "#" },
  { pitch: 77, name: "F5", staffPos: 9, accidental: "" },
  { pitch: 76, name: "E5", staffPos: 8, accidental: "" },
  { pitch: 75, name: "D#5", staffPos: 7, accidental: "#" },
  { pitch: 74, name: "D5", staffPos: 7, accidental: "" },
  { pitch: 73, name: "C#5", staffPos: 6, accidental: "#" },
  { pitch: 72, name: "C5", staffPos: 6, accidental: "" },
  { pitch: 71, name: "B4", staffPos: 5, accidental: "" },
  { pitch: 70, name: "A#4", staffPos: 4, accidental: "#" },
  { pitch: 69, name: "A4", staffPos: 4, accidental: "" },
  { pitch: 68, name: "G#4", staffPos: 3, accidental: "#" },
  { pitch: 67, name: "G4", staffPos: 3, accidental: "" },
  { pitch: 66, name: "F#4", staffPos: 2, accidental: "#" },
  { pitch: 65, name: "F4", staffPos: 2, accidental: "" },
  { pitch: 64, name: "E4", staffPos: 1, accidental: "" },
  { pitch: 63, name: "D#4", staffPos: 0, accidental: "#" },
  { pitch: 62, name: "D4", staffPos: 0, accidental: "" },
  { pitch: 61, name: "C#4", staffPos: -1, accidental: "#" },
  { pitch: 60, name: "C4", staffPos: -1, accidental: "" },
];

export const MelodyInput: React.FC<MelodyInputProps> = ({
  melody,
  onChange,
  selectedKey,
  onAutoDetectKey,
  timeSignature = "4/4",
}) => {
  const [activeTab, setActiveTab] = useState<"staff" | "midi" | "file" | "text">("staff");
  const [selectedDuration, setSelectedDuration] = useState<string>("half");

  // MIDI state
  const [midiDevices, setMidiDevices] = useState<MidiDevice[]>([]);
  const [selectedMidiId, setSelectedMidiId] = useState<string>("");
  const [isMidiRecording, setIsMidiRecording] = useState<boolean>(false);
  const [metronomeBpm, setMetronomeBpm] = useState<number>(80);
  const [activeBeat, setActiveBeat] = useState<number>(0);
  const [midiStatus, setMidiStatus] = useState<string>("");

  // Text input state
  const [textInput, setTextInput] = useState<string>("E4 F4 G4 D4 C4");

  // Drag and drop state
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [importStatus, setImportStatus] = useState<string>("");

  const melodyRef = useRef<MelodyNote[]>(melody);
  useEffect(() => {
    melodyRef.current = melody;
  }, [melody]);

  // Recalculate downbeats automatically whenever timeSignature changes
  useEffect(() => {
    if (melody && melody.length > 0) {
      const recalculated = recalculateDownbeats(melody, timeSignature);
      const isChanged = recalculated.some(
        (n, i) => n.is_downbeat !== melody[i]?.is_downbeat
      );
      if (isChanged) {
        onChange(recalculated);
      }
    }
  }, [timeSignature]);

  // Stop the MIDI metronome and detach the device listener when the input
  // unmounts (tab switch): otherwise the click keeps ticking forever.
  useEffect(() => {
    return () => {
      webMidiManager.cleanup();
    };
  }, []);

  const addNote = (pitch: number, name: string) => {
    audioEngine.playNote(0, pitch, 0.4);
    const newNote: MelodyNote = {
      pitch,
      name,
      duration: selectedDuration,
      is_downbeat: false,
    };
    const updated = recalculateDownbeats([...melody, newNote], timeSignature);
    onChange(updated);
  };

  const removeNote = (idx: number) => {
    const updated = melody.filter((_, i) => i !== idx);
    onChange(recalculateDownbeats(updated, timeSignature));
  };

  const toggleDownbeat = (idx: number) => {
    const updated = [...melody];
    updated[idx] = { ...updated[idx], is_downbeat: !updated[idx].is_downbeat };
    onChange(updated);
  };

  const clearAllNotes = () => {
    onChange([]);
  };

  // Web MIDI setup
  const initMidi = async () => {
    try {
      const devices = await webMidiManager.requestAccess();
      setMidiDevices(devices);
      if (devices.length > 0) {
        setSelectedMidiId(devices[0].id);
        webMidiManager.connectDevice(devices[0].id);
        setMidiStatus(`Подключено: ${devices[0].name}`);
      } else {
        setMidiStatus("MIDI устройства не найдены. Подключите USB-клавиатуру.");
      }
    } catch (err) {
      setMidiStatus(`Ошибка Web MIDI: ${String(err)}`);
    }
  };

  const toggleMidiRecording = () => {
    if (isMidiRecording) {
      webMidiManager.stopRecording();
      setIsMidiRecording(false);
      setActiveBeat(0);
    } else {
      if (selectedMidiId) webMidiManager.connectDevice(selectedMidiId);
      setIsMidiRecording(true);
      webMidiManager.startRecording(
        metronomeBpm,
        (pitch, isDownbeat) => {
          const noteObj = STAFF_PITCHES.find((p) => p.pitch === pitch) || {
            pitch,
            name: `Note ${pitch}`,
          };
          audioEngine.playNote(0, pitch, 0.4);
          const newNote: MelodyNote = {
            pitch,
            name: noteObj.name,
            duration: "half",
            is_downbeat: isDownbeat,
          };
          const updated = recalculateDownbeats(
            [...melodyRef.current, newNote],
            timeSignature
          );
          onChange(updated);
        },
        (beat) => {
          setActiveBeat(beat);
        },
        timeSignature
      );
    }
  };

  // Text import
  const applyTextInput = async () => {
    try {
      const resp = await fetch("/api/parse-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: textInput,
          key: { tonic: selectedKey.tonic, mode: selectedKey.mode },
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        if (Array.isArray(data) && data.length > 0) {
          onChange(data);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  // File import (drag and drop)
  const handleFileUpload = async (file: File) => {
    setImportStatus(`Импорт файла ${file.name}...`);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const resp = await fetch("/api/import-file", {
        method: "POST",
        body: formData,
      });

      if (resp.ok) {
        const data = await resp.json();
        if (data.soprano_melody && data.soprano_melody.length > 0) {
          onChange(data.soprano_melody);
          setImportStatus(`Успешно импортировано ${data.soprano_melody.length} нот из ${file.name}`);
        } else {
          setImportStatus("В файле не найдена мелодия сопрано.");
        }
      } else {
        const errJson = await resp.json();
        setImportStatus(`Ошибка импорта: ${errJson.detail || "сбой сервера"}`);
      }
    } catch (e) {
      setImportStatus(`Ошибка отправки файла: ${String(e)}`);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex flex-col gap-4">
      {/* Header & Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Music className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h2 className="text-sm font-bold uppercase tracking-wide text-slate-800 dark:text-slate-100">
            Ввод Мелодии Сопрано
          </h2>
          <span className="text-xs bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded-full font-mono">
            {melody.length} нот
          </span>
        </div>

        {/* Input Mode Tabs */}
        <div className="flex items-center bg-slate-100 dark:bg-slate-800/80 p-1 rounded-lg text-xs font-medium">
          <button
            onClick={() => setActiveTab("staff")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
              activeTab === "staff"
                ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-300 shadow-sm font-semibold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            <Piano className="w-3.5 h-3.5" />
            Нотный стан / Клавиши
          </button>
          <button
            onClick={() => {
              setActiveTab("midi");
              if (!midiDevices.length) initMidi();
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
              activeTab === "midi"
                ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-300 shadow-sm font-semibold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            Web MIDI
          </button>
          <button
            onClick={() => setActiveTab("file")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
              activeTab === "file"
                ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-300 shadow-sm font-semibold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            Файл (.mid / .xml)
          </button>
          <button
            onClick={() => setActiveTab("text")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition ${
              activeTab === "text"
                ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-300 shadow-sm font-semibold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            <FileCode className="w-3.5 h-3.5" />
            Текстовый ввод
          </button>
        </div>
      </div>

      {/* Tab 1: Interactive Staff / Piano Roll (Click to Add) */}
      {activeTab === "staff" && (
        <div className="flex flex-col gap-3">
          {/* Duration Selector */}
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
              <Clock className="w-4 h-4 text-slate-400" />
              <span>Длительность:</span>
              <div className="flex flex-wrap items-center gap-1 bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg">
                {DURATIONS.map((dur) => (
                  <button
                    key={dur.id}
                    onClick={() => setSelectedDuration(dur.id)}
                    title={dur.hint}
                    className={`px-2 py-1 rounded text-[11px] font-mono min-w-[2rem] text-center transition ${
                      selectedDuration === dur.id
                        ? "bg-indigo-600 text-white font-semibold shadow-sm"
                        : "text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                    }`}
                  >
                    {dur.label}
                  </button>
                ))}
              </div>
            </div>

            <span className="text-xs text-slate-400">
              Диапазон сопрано: C4 (до 1-й октавы) — A5 (ля 2-й октавы)
            </span>
          </div>

          {/* Interactive Keyboard / Staff Roll */}
          <div className="bg-slate-50 dark:bg-slate-950/60 p-3 rounded-lg border border-slate-200 dark:border-slate-800 flex flex-col gap-2">
            <div className="text-xs font-semibold text-slate-600 dark:text-slate-400 flex items-center justify-between">
              <span>Кликните по ноте для добавления в мелодию:</span>
              <span className="text-[11px] text-indigo-500">Звуковой предпросмотр активен</span>
            </div>

            {/* Note buttons arranged in a clean chromatic piano ladder */}
            <div className="grid grid-cols-6 sm:grid-cols-11 gap-1.5">
              {STAFF_PITCHES.slice().reverse().map((item) => {
                const isAccidental = item.accidental !== "";
                return (
                  <button
                    key={item.pitch}
                    onClick={() => addNote(item.pitch, item.name)}
                    className={`px-2 py-2 rounded text-xs font-mono font-semibold transition flex flex-col items-center justify-center border shadow-xs active:scale-95 ${
                      isAccidental
                        ? "bg-slate-800 text-amber-300 border-slate-700 hover:bg-slate-700"
                        : "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-300 dark:border-slate-700 hover:border-indigo-500 hover:text-indigo-600 dark:hover:text-indigo-400"
                    }`}
                  >
                    <span className="text-sm font-bold">{item.name}</span>
                    <span className="text-[10px] opacity-60">MIDI {item.pitch}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Web MIDI API with Metronome */}
      {activeTab === "midi" && (
        <div className="flex flex-col gap-3 p-3 bg-slate-50 dark:bg-slate-950/60 rounded-lg border border-slate-200 dark:border-slate-800">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                MIDI-клавиатура:
              </label>
              {midiDevices.length > 0 ? (
                <select
                  value={selectedMidiId}
                  onChange={(e) => {
                    setSelectedMidiId(e.target.value);
                    webMidiManager.connectDevice(e.target.value);
                  }}
                  className="text-xs bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded px-2.5 py-1"
                >
                  {midiDevices.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.manufacturer})
                    </option>
                  ))}
                </select>
              ) : (
                <button
                  onClick={initMidi}
                  className="px-3 py-1 bg-indigo-600 text-white rounded text-xs font-medium hover:bg-indigo-700"
                >
                  Обнаружить MIDI
                </button>
              )}
            </div>

            {/* Metronome BPM */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                Темп метронома:
              </span>
              <input
                type="number"
                min="40"
                max="180"
                value={metronomeBpm}
                onChange={(e) => setMetronomeBpm(Number(e.target.value))}
                className="w-16 text-xs bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded px-2 py-1 text-center font-mono font-bold"
              />
              <span className="text-xs text-slate-400">BPM</span>
            </div>
          </div>

          {/* Record Control & Beat Indicator */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-slate-800">
            <button
              onClick={toggleMidiRecording}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition shadow-sm ${
                isMidiRecording
                  ? "bg-red-600 text-white hover:bg-red-700 animate-pulse"
                  : "bg-emerald-600 text-white hover:bg-emerald-700"
              }`}
            >
              {isMidiRecording ? (
                <>
                  <Square className="w-4 h-4 fill-current" /> Остановить запись
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" /> Запись под метроном
                </>
              )}
            </button>

            {/* Meter Beat Indicator */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Тактовая доля:</span>
              <div className="flex items-center gap-1.5">
                {Array.from(
                  { length: Math.max(1, parseInt((timeSignature || "4/4").split("/")[0], 10) || 4) },
                  (_, i) => i + 1
                ).map((beat) => (
                  <div
                    key={beat}
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold font-mono transition ${
                      activeBeat === beat
                        ? beat === 1
                          ? "bg-red-600 text-white scale-110 shadow-md"
                          : "bg-indigo-600 text-white scale-105"
                        : "bg-slate-200 dark:bg-slate-800 text-slate-500"
                    }`}
                  >
                    {beat}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {midiStatus && (
            <p className="text-xs text-indigo-600 dark:text-indigo-400 mt-1">{midiStatus}</p>
          )}
        </div>
      )}

      {/* Tab 3: File Import (Drag & Drop .mid / .musicxml) */}
      {activeTab === "file" && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
              handleFileUpload(e.dataTransfer.files[0]);
            }
          }}
          className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center text-center transition ${
            isDragging
              ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20"
              : "border-slate-300 dark:border-slate-700 hover:border-slate-400"
          }`}
        >
          <Upload className="w-8 h-8 text-slate-400 mb-2" />
          <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Перетащите сюда файл <span className="text-indigo-600 font-mono">.mid</span> или{" "}
            <span className="text-indigo-600 font-mono">.musicxml</span>
          </p>
          <p className="text-[11px] text-slate-500 mt-1">
            Бэкенд автоматически выделит верхний голос (сопрано) и определит тональность.
          </p>
          <label className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-xs font-medium cursor-pointer transition">
            <span>Выбрать файл на диске</span>
            <input
              type="file"
              accept=".mid,.midi,.musicxml,.xml"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileUpload(e.target.files[0]);
                }
              }}
            />
          </label>
          {importStatus && (
            <p className="text-xs text-indigo-600 dark:text-indigo-400 mt-3 font-medium">
              {importStatus}
            </p>
          )}
        </div>
      )}

      {/* Tab 4: Text Input (Shortcuts / Scale Degrees) */}
      {activeTab === "text" && (
        <div className="flex flex-col gap-2 p-3 bg-slate-50 dark:bg-slate-950/60 rounded-lg border border-slate-200 dark:border-slate-800">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center justify-between">
            <span>Быстрый ввод нот или ступеней лада:</span>
            <span className="text-[11px] text-slate-400">
              Примеры: <code className="text-indigo-600">C4 E4 F4 G4 E4 D4 C4</code> или{" "}
              <code className="text-indigo-600">1 3 4 5 3 2 1</code>
            </span>
          </label>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Например: E4 F4 G4 D4 C4 или 3 4 5 2 1"
              className="flex-1 text-xs bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded px-3 py-2 font-mono"
            />
            <button
              onClick={applyTextInput}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs font-bold transition shadow-xs"
            >
              Применить
            </button>
          </div>
        </div>
      )}

      {/* Melody Sequence Ribbon (Active Notes) */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Текущая последовательность нот:
            </span>
            <button
              onClick={onAutoDetectKey}
              className="inline-flex items-center gap-1 text-[11px] text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
            >
              <Sparkles className="w-3 h-3" /> Определить тональность по мелодии
            </button>
          </div>
          {melody.length > 0 && (
            <button
              onClick={clearAllNotes}
              className="inline-flex items-center gap-1 text-xs text-red-500 hover:text-red-700 font-medium transition"
            >
              <Trash2 className="w-3.5 h-3.5" /> Очистить всё
            </button>
          )}
        </div>

        {melody.length === 0 ? (
          <div className="p-4 border border-dashed rounded-lg text-center text-xs text-slate-400">
            Мелодия пуста. Добавьте ноты кликом по клавиатуре, наберите текстом или загрузите файл.
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-1.5 p-2 bg-slate-50 dark:bg-slate-950/40 rounded-lg border border-slate-200 dark:border-slate-800 min-h-[50px]">
            {melody.map((note, idx) => (
              <div
                key={idx}
                className={`group flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-mono font-medium border shadow-xs transition ${
                  note.is_downbeat
                    ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-900 dark:text-indigo-200 border-indigo-300 dark:border-indigo-800"
                    : "bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border-slate-200 dark:border-slate-700"
                }`}
              >
                <button
                  onClick={() => audioEngine.playNote(0, note.pitch, 0.4)}
                  className="font-bold hover:text-indigo-600 cursor-pointer"
                  title="Прослушать ноту"
                >
                  {note.name || `MIDI ${note.pitch}`}
                </button>

                <button
                  onClick={() => toggleDownbeat(idx)}
                  className={`text-[9px] px-1 py-0.2 rounded font-sans transition ${
                    note.is_downbeat
                      ? "bg-indigo-600 text-white font-bold"
                      : "bg-transparent text-slate-400 dark:text-slate-500"
                  }`}
                  title={
                    note.is_downbeat
                      ? "Сильная доля (такт). Клик — сделать слабой"
                      : "Слабая доля. Клик — сделать сильной"
                  }
                >
                  {note.is_downbeat ? "сильная" : "·"}
                </button>

                <button
                  onClick={() => removeNote(idx)}
                  className="text-slate-400 hover:text-red-500 transition ml-0.5"
                  title="Удалить ноту"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

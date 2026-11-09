import React, { useState } from "react";
import { Download, FileText, Check, Music } from "lucide-react";
import type { SATBVoicing } from "../audio/synth";

interface ExportBarProps {
  voicings: SATBVoicing[];
  chords?: string[];
  keyObj: { tonic: string; mode: string };
  asciiScore?: string;
}

export const ExportBar: React.FC<ExportBarProps> = ({
  voicings,
  chords = [],
  keyObj,
  asciiScore = "",
}) => {
  const [copied, setCopied] = useState(false);
  const [downloadingMidi, setDownloadingMidi] = useState(false);
  const [downloadingXml, setDownloadingXml] = useState(false);

  const handleDownloadMidi = async () => {
    if (!voicings.length) return;
    setDownloadingMidi(true);
    try {
      const resp = await fetch("/api/export/midi", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voicings, bpm: 80 }),
      });
      if (!resp.ok) throw new Error("Failed to export MIDI");

      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `harmonization_${keyObj.tonic}_${keyObj.mode}.mid`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error("MIDI download error:", e);
    } finally {
      setDownloadingMidi(false);
    }
  };

  const handleDownloadMusicXml = async () => {
    if (!voicings.length) return;
    setDownloadingXml(true);
    try {
      const resp = await fetch("/api/export/musicxml", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          voicings,
          chords,
          key: keyObj,
          title: `Гармонизация в ${keyObj.tonic} ${keyObj.mode}`,
        }),
      });
      if (!resp.ok) throw new Error("Failed to export MusicXML");

      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `harmonization_${keyObj.tonic}_${keyObj.mode}.musicxml`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error("MusicXML download error:", e);
    } finally {
      setDownloadingXml(false);
    }
  };

  const handleCopyAscii = async () => {
    if (!asciiScore) return;
    try {
      await navigator.clipboard.writeText(asciiScore);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback
      const ta = document.createElement("textarea");
      ta.value = asciiScore;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-2">
        <Download className="w-4 h-4 text-indigo-400" />
        <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
          Экспорт решения (One-Click Export):
        </span>
      </div>

      <div className="flex items-center gap-2.5 flex-wrap">
        <button
          type="button"
          onClick={handleDownloadMidi}
          disabled={!voicings.length || downloadingMidi}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors disabled:opacity-40"
          title="Скачать многодорожечный MIDI файл (SATB)"
        >
          <Music className="w-3.5 h-3.5 text-blue-400" />
          <span>{downloadingMidi ? "Загрузка..." : "Скачать MIDI"}</span>
        </button>

        <button
          type="button"
          onClick={handleDownloadMusicXml}
          disabled={!voicings.length || downloadingXml}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition-colors disabled:opacity-40"
          title="Скачать MusicXML для MuseScore, Sibelius, Dorico"
        >
          <FileText className="w-3.5 h-3.5 text-emerald-400" />
          <span>{downloadingXml ? "Загрузка..." : "Скачать MusicXML"}</span>
        </button>

        <button
          type="button"
          onClick={handleCopyAscii}
          disabled={!asciiScore}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-colors ${
            copied
              ? "bg-emerald-950/80 border-emerald-500 text-emerald-300"
              : "bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-200"
          } disabled:opacity-40`}
          title="Скопировать текстовую ASCII-таблицу партитуры"
        >
          {copied ? (
            <Check className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <FileText className="w-3.5 h-3.5 text-amber-400" />
          )}
          <span>{copied ? "Скопировано в буфер!" : "Копировать ASCII-таблицу"}</span>
        </button>
      </div>
    </div>
  );
};

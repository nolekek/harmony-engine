import React, { useState } from "react";
import { Download, FileText, Check, Music } from "lucide-react";
import { Button } from "./ui/Button";
import type { SATBVoicing } from "../audio/synth";

interface ExportBarProps {
  voicings: SATBVoicing[];
  chords?: string[];
  keyObj: { tonic: string; mode: string };
  timeSignature?: string;
  asciiScore?: string;
  durations?: string[];
}

export const ExportBar: React.FC<ExportBarProps> = ({
  voicings,
  chords = [],
  keyObj,
  timeSignature = "4/4",
  asciiScore = "",
  durations,
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
        body: JSON.stringify({
          voicings,
          bpm: 80,
          time_signature: timeSignature,
          ...(durations && durations.length > 0 ? { durations } : {}),
        }),
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
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
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
          time_signature: timeSignature,
          ...(durations && durations.length > 0 ? { durations } : {}),
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
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
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
    <div className="bg-surface-card border border-border rounded-xl p-4 shadow-lg flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-2">
        <Download className="w-4 h-4 text-brand" />
        <span className="text-xs font-bold uppercase tracking-wider text-text-secondary">
          Экспорт решения (One-Click Export):
        </span>
      </div>

      <div className="flex items-center gap-2.5 flex-wrap">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleDownloadMidi}
          disabled={!voicings.length || downloadingMidi}
          title="Скачать многодорожечный MIDI файл (SATB)"
          icon={<Music className="w-3.5 h-3.5 text-blue-500 dark:text-blue-400" />}
        >
          {downloadingMidi ? "Загрузка..." : "Скачать MIDI"}
        </Button>

        <Button
          variant="secondary"
          size="sm"
          onClick={handleDownloadMusicXml}
          disabled={!voicings.length || downloadingXml}
          title="Скачать MusicXML для MuseScore, Sibelius, Dorico"
          icon={<FileText className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />}
        >
          {downloadingXml ? "Загрузка..." : "Скачать MusicXML"}
        </Button>

        <Button
          variant={copied ? "primary" : "secondary"}
          size="sm"
          onClick={handleCopyAscii}
          disabled={!asciiScore}
          className={copied ? "bg-emerald-600 hover:bg-emerald-500 border-emerald-500" : ""}
          title="Скопировать текстовую ASCII-таблицу партитуры"
          icon={
            copied ? (
              <Check className="w-3.5 h-3.5" />
            ) : (
              <FileText className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
            )
          }
        >
          {copied ? "Скопировано в буфер!" : "Копировать ASCII-таблицу"}
        </Button>
      </div>
    </div>
  );
};

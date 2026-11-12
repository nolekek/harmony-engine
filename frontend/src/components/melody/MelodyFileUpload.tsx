import React, { useState, useRef } from "react";
import { Upload, FileCode, Check, AlertCircle } from "lucide-react";
import { Button } from "../ui/Button";
import type { MelodyNote } from "../../utils/durationUtils";

interface MelodyFileUploadProps {
  onMelodyLoaded: (melody: MelodyNote[], timeSignature?: string, key?: { tonic: string; mode: string }) => void;
}

export const MelodyFileUpload: React.FC<MelodyFileUploadProps> = ({ onMelodyLoaded }) => {
  const [textInput, setTextInput] = useState("");
  const [isParsingText, setIsParsingText] = useState(false);
  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isError, setIsError] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleParseText = async () => {
    if (!textInput.trim()) return;
    setIsParsingText(true);
    setStatusMessage(null);
    setIsError(false);

    try {
      const resp = await fetch("/api/parse-text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textInput }),
      });
      const data = await resp.json();
      if (resp.ok && data.melody) {
        onMelodyLoaded(data.melody, data.time_signature, data.key);
        setStatusMessage(`Загружено нот: ${data.melody.length}`);
        setTextInput("");
      } else {
        setIsError(true);
        setStatusMessage(data.detail || "Не удалось распознать нотный текст.");
      }
    } catch (e) {
      setIsError(true);
      setStatusMessage("Ошибка запроса к серверу парсинга текста.");
    } finally {
      setIsParsingText(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    setIsUploadingFile(true);
    setStatusMessage(null);
    setIsError(false);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const resp = await fetch("/api/import-file", {
        method: "POST",
        body: formData,
      });
      const data = await resp.json();
      if (resp.ok && data.melody) {
        onMelodyLoaded(data.melody, data.time_signature, data.key);
        setStatusMessage(`Файл "${file.name}" загружен (${data.melody.length} нот).`);
      } else {
        setIsError(true);
        setStatusMessage(data.detail || "Ошибка при чтении файла MusicXML/MIDI.");
      }
    } catch (e) {
      setIsError(true);
      setStatusMessage("Ошибка при загрузке файла на сервер.");
    } finally {
      setIsUploadingFile(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-3 pt-2">
      {/* Text string input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Ввод строкой: E4/2, F4/2, G4/2, C4/1 или 64, 65, 67, 60..."
          aria-label="Ввод нот строкой"
          className="flex-1 bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus-ring"
          onKeyDown={(e) => {
            if (e.key === "Enter") handleParseText();
          }}
        />
        <Button
          variant="secondary"
          size="sm"
          onClick={handleParseText}
          disabled={isParsingText || !textInput.trim()}
          icon={<FileCode className="w-3.5 h-3.5" />}
        >
          {isParsingText ? "..." : "Распознать"}
        </Button>
      </div>

      {/* File Upload / Dropzone */}
      <div className="flex items-center gap-3">
        <input
          ref={fileInputRef}
          type="file"
          accept=".mid,.midi,.xml,.musicxml"
          aria-label="Выбор файла MusicXML или MIDI"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFileUpload(f);
          }}
        />
        <Button
          variant="outline"
          size="sm"
          className="w-full border-dashed"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploadingFile}
          icon={<Upload className="w-3.5 h-3.5" />}
        >
          {isUploadingFile ? "Загрузка партитуры..." : "Импорт файла (.musicxml / .mid)"}
        </Button>
      </div>

      {statusMessage && (
        <div
          role="status"
          className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded border ${
            isError
              ? "bg-rose-950/40 border-rose-800 text-rose-300"
              : "bg-emerald-950/40 border-emerald-800 text-emerald-300"
          }`}
        >
          {isError ? <AlertCircle className="w-3.5 h-3.5 shrink-0" /> : <Check className="w-3.5 h-3.5 shrink-0" />}
          <span>{statusMessage}</span>
        </div>
      )}
    </div>
  );
};

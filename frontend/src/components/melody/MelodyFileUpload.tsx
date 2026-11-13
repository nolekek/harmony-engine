import React, { useState, useRef } from "react";
import { Upload, FileCode, Check, AlertCircle } from "lucide-react";
import { Button } from "../ui/Button";
import type { MelodyNote } from "../../utils/durationUtils";

interface MelodyFileUploadProps {
  onMelodyLoaded: (melody: MelodyNote[], timeSignature?: string, key?: { tonic: string; mode: string }) => void;
  /** Current UI meter — sent to /api/parse-text (backend contract m1). */
  timeSignature: string;
}

export const MelodyFileUpload: React.FC<MelodyFileUploadProps> = ({
  onMelodyLoaded,
  timeSignature,
}) => {
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
        body: JSON.stringify({ text: textInput, time_signature: timeSignature }),
      });
      const data = await resp.json();
      // Backend contract: /api/parse-text returns a bare list of notes;
      // accept both shapes (array or {melody: [...]}) defensively.
      const notes = Array.isArray(data) ? data : data?.melody;
      if (resp.ok && Array.isArray(notes) && notes.length > 0) {
        const loadedTs =
          !Array.isArray(data) && typeof data?.time_signature === "string"
            ? data.time_signature
            : timeSignature;
        onMelodyLoaded(notes, loadedTs, !Array.isArray(data) ? data?.key : undefined);
        setStatusMessage(`Загружено нот: ${notes.length}`);
        setTextInput("");
      } else {
        setIsError(true);
        setStatusMessage(
          (!Array.isArray(data) && data?.detail) || "Не удалось распознать нотный текст."
        );
      }
    } catch {
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
      // Backend contract: /api/import-file returns soprano_melody (api.py);
      // keep data.melody as a defensive fallback.
      const notes = data?.soprano_melody ?? data?.melody;
      if (resp.ok && Array.isArray(notes) && notes.length > 0) {
        onMelodyLoaded(notes, data.time_signature, data.key);
        setStatusMessage(`Файл "${file.name}" загружен (${notes.length} нот).`);
      } else if (resp.ok && Array.isArray(notes) && notes.length === 0) {
        setIsError(true);
        setStatusMessage("В файле не найдено нот.");
      } else {
        setIsError(true);
        setStatusMessage(data?.detail || "Ошибка при чтении файла MusicXML/MIDI.");
      }
    } catch {
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
      <div className="flex gap-2 items-start">
        <input
          type="text"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Ввод строкой: C4:half, D4:quarter, E4:dotted_half или 64, 65, 67, 60..."
          aria-label="Ввод нот строкой"
          className="flex-1 bg-surface-panel border border-border rounded-lg px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus-ring transition-colors hover:border-border-strong"
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
          aria-live="polite"
          className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded border ${
            isError
              ? "bg-rose-500/10 border-rose-600/50 text-rose-700 dark:text-rose-300"
              : "bg-emerald-500/10 border-emerald-600/50 text-emerald-700 dark:text-emerald-300"
          }`}
        >
          {isError ? <AlertCircle className="w-3.5 h-3.5 shrink-0" /> : <Check className="w-3.5 h-3.5 shrink-0" />}
          <span>{statusMessage}</span>
        </div>
      )}
    </div>
  );
};

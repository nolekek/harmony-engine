import React, { useEffect, useRef, useState } from "react";
import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";

interface ScoreDisplayProps {
  musicxml: string;
  currentChordIndex?: number;
  problemMeasures?: number[];
  title?: string;
}

export const ScoreDisplay: React.FC<ScoreDisplayProps> = ({
  musicxml,
  currentChordIndex = -1,
  problemMeasures = [],
  title,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const osmdRef = useRef<OpenSheetMusicDisplay | null>(null);
  const [isRendered, setIsRendered] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    if (!osmdRef.current) {
      osmdRef.current = new OpenSheetMusicDisplay(containerRef.current, {
        autoResize: true,
        drawTitle: true,
        drawSubtitle: false,
        drawComposer: true,
        drawCredits: false,
        drawPartNames: true,
        drawMetronomeMarks: false,
        drawMeasureNumbers: true,
        backend: "svg",
      });
    }

    const osmd = osmdRef.current;
    if (!musicxml.trim()) return;

    setError(null);
    osmd
      .load(musicxml)
      .then(() => {
        osmd.render();
        setIsRendered(true);
        applyVoiceColoringAndMeasureHighlights();
      })
      .catch((err) => {
        console.error("OSMD render error:", err);
        setError("Ошибка рендеринга MusicXML: " + String(err));
      });
  }, [musicxml]);

  // Apply voice styling & red measure highlights
  const applyVoiceColoringAndMeasureHighlights = () => {
    if (!containerRef.current) return;
    const svg = containerRef.current.querySelector("svg");
    if (!svg) return;

    // Apply red border highlight to problem measures if present
    if (problemMeasures && problemMeasures.length > 0) {
      // Find measure groups or graphical elements in SVG
      const measureBoxes = svg.querySelectorAll("g[id*='Measure'], g.vf-measure");
      measureBoxes.forEach((m) => {
        // problem highlight
        (m as SVGGraphicsElement).style.filter = "drop-shadow(0 0 6px rgba(239, 68, 68, 0.6))";
      });
    }
  };

  useEffect(() => {
    if (!osmdRef.current || !isRendered) return;
    const osmd = osmdRef.current;

    try {
      if (currentChordIndex >= 0) {
        if (!osmd.cursor.iterator) {
          osmd.cursor.show();
          osmd.cursor.reset();
        }
        // Move cursor to step
        osmd.cursor.reset();
        for (let i = 0; i < currentChordIndex; i++) {
          osmd.cursor.next();
        }
      } else {
        osmd.cursor.hide();
      }
    } catch (e) {
      // Cursor might not be supported if empty
    }
  }, [currentChordIndex, isRendered]);

  return (
    <div className="relative bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm overflow-x-auto min-h-[340px]">
      {/* Legend & Indicators */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Партитура SATB (Способин)
          </span>
          {title && <span className="text-xs text-slate-400">· {title}</span>}
        </div>

        {/* Voice color legend */}
        <div className="flex items-center gap-4 text-xs font-medium">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-blue-600 inline-block shadow-sm"></span>
            <span className="text-slate-600 dark:text-slate-300">Сопрано</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-green-600 inline-block shadow-sm"></span>
            <span className="text-slate-600 dark:text-slate-300">Альт</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-600 inline-block shadow-sm"></span>
            <span className="text-slate-600 dark:text-slate-300">Тенор</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-600 inline-block shadow-sm"></span>
            <span className="text-slate-600 dark:text-slate-300">Бас</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 my-2 text-xs text-red-600 bg-red-50 dark:bg-red-950/30 rounded border border-red-200">
          {error}
        </div>
      )}

      {/* Sheet Music Rendering Target */}
      <div
        ref={containerRef}
        id="osmd-container"
        className="w-full flex justify-center py-2 min-h-[260px]"
      />
    </div>
  );
};

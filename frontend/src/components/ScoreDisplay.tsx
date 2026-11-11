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
  const loadSequenceRef = useRef<number>(0);
  const [isRendered, setIsRendered] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize OSMD and load/render MusicXML with race condition guard
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

    // Empty musicxml clears score
    if (!musicxml || !musicxml.trim()) {
      try {
        osmd.clear();
      } catch {
        // ignore
      }
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }
      setIsRendered(false);
      setError(null);
      return;
    }

    const currentLoadId = ++loadSequenceRef.current;
    let isMounted = true;
    setError(null);

    osmd
      .load(musicxml)
      .then(() => {
        if (!isMounted || currentLoadId !== loadSequenceRef.current) return;
        osmd.render();
        setIsRendered(true);
      })
      .catch((err) => {
        if (!isMounted || currentLoadId !== loadSequenceRef.current) return;
        console.error("OSMD render error:", err);
        setError("Ошибка рендеринга MusicXML: " + String(err));
      });

    return () => {
      isMounted = false;
    };
  }, [musicxml]);

  // Apply red measure highlights matching ONLY problemMeasures
  const applyMeasureHighlights = (measuresToHighlight: number[]) => {
    if (!containerRef.current) return;
    const svg = containerRef.current.querySelector("svg");
    if (!svg) return;

    // 1. Clear any existing measure highlights
    const allHighlighted = svg.querySelectorAll<SVGGraphicsElement>(
      "g[data-measure-highlight='true'], g[id^='osmd-m'], g[id*='Measure'], g.vf-measure"
    );
    allHighlighted.forEach((el) => {
      if (
        el.style.filter.includes("drop-shadow") ||
        el.getAttribute("data-measure-highlight") === "true"
      ) {
        el.style.filter = "";
        el.removeAttribute("data-measure-highlight");
      }
    });

    if (!measuresToHighlight || measuresToHighlight.length === 0) {
      return;
    }

    const targetSet = new Set(measuresToHighlight);

    // 2. Try highlighting via OSMD GraphicSheet if available
    const osmd = osmdRef.current;
    if (osmd && (osmd as any).GraphicSheet?.MeasureList) {
      const measureList: any[][] = (osmd as any).GraphicSheet.MeasureList;
      measureList.forEach((measuresInStaff, measureListIdx) => {
        // Measure numbers are 1-based, measureListIdx is 0-based
        const measureNum =
          measuresInStaff[0]?.parentSourceMeasure?.MeasureNumber ??
          measuresInStaff[0]?.MeasureNumber ??
          measureListIdx + 1;

        if (targetSet.has(measureNum)) {
          measuresInStaff.forEach((gm) => {
            const el: SVGGraphicsElement | null =
              gm?.getSVGGElement?.() || gm?.svgGElement || null;
            if (el) {
              el.style.filter = "drop-shadow(0 0 6px rgba(239, 68, 68, 0.75))";
              el.setAttribute("data-measure-highlight", "true");
            }
          });
        }
      });
    }

    // 3. Highlight via SVG element IDs / classes matching specific measure number
    measuresToHighlight.forEach((mNum) => {
      const mIdx = mNum - 1; // 0-based index used in OSMD element ids: osmd-m{idx}-{staff}
      const selectors = [
        `g[id^='osmd-m${mIdx}-']`,
        `g[id^='osmd-m${mIdx}x-']`,
        `g[id='vf-measure-${mIdx}']`,
        `g[id='vf-measure-${mNum}']`,
      ];
      const matching = svg.querySelectorAll<SVGGraphicsElement>(selectors.join(", "));
      matching.forEach((el) => {
        el.style.filter = "drop-shadow(0 0 6px rgba(239, 68, 68, 0.75))";
        el.setAttribute("data-measure-highlight", "true");
      });
    });
  };

  // Dedicated effect for problem measure highlights
  useEffect(() => {
    if (!isRendered || !osmdRef.current || !containerRef.current) return;
    applyMeasureHighlights(problemMeasures);
  }, [problemMeasures, isRendered, musicxml]);

  // Cursor playback effect
  useEffect(() => {
    if (!osmdRef.current || !isRendered) return;
    const osmd = osmdRef.current;

    try {
      if (currentChordIndex >= 0) {
        if (!osmd.cursor.iterator) {
          osmd.cursor.show();
          osmd.cursor.reset();
        }
        osmd.cursor.reset();
        for (let i = 0; i < currentChordIndex; i++) {
          osmd.cursor.next();
        }
      } else {
        osmd.cursor.hide();
      }
    } catch {
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

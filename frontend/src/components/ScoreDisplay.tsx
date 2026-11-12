import React, { useEffect, useRef, useState, useCallback } from "react";
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
        drawTitle: false,
        drawSubtitle: false,
        drawComposer: false,
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
      return;
    }

    const currentLoadId = ++loadSequenceRef.current;
    let isMounted = true;

    osmd
      .load(musicxml)
      .then(() => {
        if (!isMounted || currentLoadId !== loadSequenceRef.current) return;
        osmd.render();
        setIsRendered(true);
        setError(null);
      })
      .catch((err) => {
        if (!isMounted || currentLoadId !== loadSequenceRef.current) return;
        console.error("OSMD render error:", err);
        setError("Ошибка рендеринга MusicXML: " + String(err));
        setIsRendered(false);
      });

    return () => {
      isMounted = false;
    };
  }, [musicxml]);

  // Apply red measure highlights matching ONLY problemMeasures
  const applyMeasureHighlights = useCallback((measuresToHighlight: number[]) => {
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
        const measureNum =
          measuresInStaff[0]?.parentSourceMeasure?.MeasureNumber ??
          measuresInStaff[0]?.MeasureNumber ??
          measureListIdx + 1;

        if (targetSet.has(measureNum)) {
          measuresInStaff.forEach((gm) => {
            const el: SVGGraphicsElement | null =
              gm?.getSVGGElement?.() || gm?.svgGElement || null;
            if (el) {
              el.style.filter = "drop-shadow(0 0 6px rgba(239, 68, 68, 0.85))";
              el.setAttribute("data-measure-highlight", "true");
            }
          });
        }
      });
    }

    // 3. Highlight via SVG element IDs / classes matching specific measure number
    measuresToHighlight.forEach((mNum) => {
      const mIdx = mNum - 1;
      const selectors = [
        `g[id^='osmd-m${mIdx}-']`,
        `g[id^='osmd-m${mIdx}x-']`,
        `g[id='vf-measure-${mIdx}']`,
        `g[id='vf-measure-${mNum}']`,
      ];
      const matching = svg.querySelectorAll<SVGGraphicsElement>(selectors.join(", "));
      matching.forEach((el) => {
        el.style.filter = "drop-shadow(0 0 6px rgba(239, 68, 68, 0.85))";
        el.setAttribute("data-measure-highlight", "true");
      });
    });
  }, []);

  // Dedicated effect for problem measure highlights
  useEffect(() => {
    if (!isRendered || !osmdRef.current || !containerRef.current) return;
    applyMeasureHighlights(problemMeasures);
  }, [problemMeasures, isRendered, applyMeasureHighlights]);

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
    <div className="relative bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl overflow-hidden">
      {/* Legend & Indicators */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Партитура SATB
          </span>
          {title && <span className="text-xs text-slate-400 font-mono">· {title}</span>}
        </div>

        {/* Voice color legend */}
        <div className="flex items-center gap-3 text-xs font-medium">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block shadow-sm"></span>
            <span className="text-slate-300">Сопрано</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block shadow-sm"></span>
            <span className="text-slate-300">Альт</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block shadow-sm"></span>
            <span className="text-slate-300">Тенор</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block shadow-sm"></span>
            <span className="text-slate-300">Бас</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 my-2 text-xs text-rose-300 bg-rose-950/40 rounded border border-rose-800">
          {error}
        </div>
      )}

      {/* Sheet Music Rendering Target: Warm matte manuscript paper frame */}
      <div className="w-full overflow-x-auto rounded-lg bg-[#fbf9f4] border border-amber-900/20 shadow-inner py-3 px-2 flex justify-center min-h-[300px]">
        <div
          ref={containerRef}
          id="osmd-container"
          className="w-full flex justify-center"
        />
      </div>
    </div>
  );
};

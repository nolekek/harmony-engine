import { Music, Award, FileMusic, Sun, Moon } from "lucide-react";
import { useTheme } from "../../hooks/useTheme";

interface HeaderProps {
  activeTab: "harmonizer" | "grader";
  onTabChange: (tab: "harmonizer" | "grader") => void;
}

export function Header({ activeTab, onTabChange }: HeaderProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="border-b border-border bg-surface-elevated/80 backdrop-blur sticky top-0 z-50 px-4 lg:px-8 py-3.5 transition-colors">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Brand & Subtitle */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand to-indigo-500 flex items-center justify-center shadow-lg shadow-brand/20">
            <FileMusic className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-text-primary m-0">
                Бригадное Ядро Гармонизации
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-surface-subtle border border-border text-brand">
                Способин / Дубовский
              </span>
            </div>
            <p className="text-xs text-text-muted m-0">
              Математический Viterbi-синтез &amp; Консерваторский инспектор голосоведения
            </p>
          </div>
        </div>

        {/* Right Section: Mode Tabs + Theme Toggle */}
        <div className="flex items-center gap-3">
          {/* Navigation Tabs */}
          <nav
            role="tablist"
            aria-label="Режимы работы"
            className="flex items-center gap-1 bg-surface-subtle border border-border p-1 rounded-xl"
          >
            <button
              id="tab-harmonizer"
              role="tab"
              type="button"
              aria-selected={activeTab === "harmonizer"}
              aria-controls="panel-harmonizer"
              onClick={() => onTabChange("harmonizer")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all focus-ring ${
                activeTab === "harmonizer"
                  ? "bg-brand text-white shadow-md shadow-brand/20"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              <Music className="w-3.5 h-3.5" />
              <span>Гармонизация</span>
            </button>

            <button
              id="tab-grader"
              role="tab"
              type="button"
              aria-selected={activeTab === "grader"}
              aria-controls="panel-grader"
              onClick={() => onTabChange("grader")}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all focus-ring ${
                activeTab === "grader"
                  ? "bg-gradient-to-r from-amber-600 to-rose-600 text-white shadow-md shadow-amber-600/20"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span>Инспектор</span>
            </button>
          </nav>

          {/* Theme Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "Переключить на светлую тему" : "Переключить на тёмную тему"}
            title={theme === "dark" ? "Светлая тема" : "Тёмная тема"}
            className="p-2 rounded-xl border border-border bg-surface-subtle hover:bg-surface-elevated text-text-muted hover:text-text-primary transition-all focus-ring"
          >
            {theme === "dark" ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-brand" />}
          </button>
        </div>
      </div>
    </header>
  );
}

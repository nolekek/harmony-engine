import React, { useRef } from "react";

export interface TabItem {
  id: string;
  label: React.ReactNode;
  icon?: React.ReactNode;
  /** Override the active-tab visual (e.g. grader amber/rose identity). */
  activeClass?: string;
}

interface TabsProps {
  items: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  ariaLabel: string;
  className?: string;
}

/**
 * Accessible tablist: role=tablist/tab, aria-selected, roving tabindex,
 * ArrowLeft/ArrowRight/Home/End keyboard navigation.
 * Renders ids `tab-<id>` / aria-controls `panel-<id>` (App panels match).
 */
export const Tabs: React.FC<TabsProps> = ({
  items,
  activeId,
  onChange,
  ariaLabel,
  className = "",
}) => {
  const tabRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  const focusTab = (id: string) => {
    onChange(id);
    tabRefs.current.get(id)?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let target: number | null = null;
    if (e.key === "ArrowRight") target = (index + 1) % items.length;
    else if (e.key === "ArrowLeft") target = (index - 1 + items.length) % items.length;
    else if (e.key === "Home") target = 0;
    else if (e.key === "End") target = items.length - 1;
    if (target !== null) {
      e.preventDefault();
      focusTab(items[target].id);
    }
  };

  return (
    <nav
      role="tablist"
      aria-label={ariaLabel}
      className={`flex items-center gap-1 bg-surface-subtle border border-border p-1 rounded-xl ${className}`}
    >
      {items.map((item, index) => {
        const isActive = item.id === activeId;
        return (
          <button
            key={item.id}
            id={`tab-${item.id}`}
            role="tab"
            type="button"
            aria-selected={isActive}
            aria-controls={`panel-${item.id}`}
            tabIndex={isActive ? 0 : -1}
            ref={(el) => {
              if (el) tabRefs.current.set(item.id, el);
              else tabRefs.current.delete(item.id);
            }}
            onClick={() => onChange(item.id)}
            onKeyDown={(e) => handleKeyDown(e, index)}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all focus-ring cursor-pointer ${
              isActive
                ? item.activeClass ?? "bg-brand text-white shadow-md shadow-brand/20"
                : "text-text-muted hover:text-text-primary"
            }`}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
};

import React from "react";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "brand" | "success" | "warning" | "error" | "voice";
  voice?: "soprano" | "alto" | "tenor" | "bass";
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "default",
  voice,
  children,
  className = "",
  ...props
}) => {
  let styleClasses = "bg-surface-elevated text-text-secondary border-border";

  if (variant === "brand") {
    styleClasses = "bg-brand-light text-brand border-brand/40";
  } else if (variant === "success") {
    styleClasses =
      "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-600/40 dark:border-emerald-700/60";
  } else if (variant === "warning") {
    styleClasses =
      "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-600/40 dark:border-amber-700/60";
  } else if (variant === "error") {
    styleClasses =
      "bg-rose-500/15 text-rose-700 dark:text-rose-300 border-rose-600/40 dark:border-rose-700/60";
  } else if (variant === "voice") {
    if (voice === "soprano")
      styleClasses = "bg-blue-500/15 text-blue-700 dark:text-blue-300 border-blue-600/40 dark:border-blue-700/60";
    else if (voice === "alto")
      styleClasses = "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-600/40 dark:border-emerald-700/60";
    else if (voice === "tenor")
      styleClasses = "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-600/40 dark:border-amber-700/60";
    else if (voice === "bass")
      styleClasses = "bg-red-500/15 text-red-700 dark:text-red-300 border-red-600/40 dark:border-red-700/60";
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono border tracking-tight ${styleClasses} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};

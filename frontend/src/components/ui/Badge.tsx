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
  let styleClasses = "bg-slate-800 text-slate-300 border-slate-700";

  if (variant === "brand") {
    styleClasses = "bg-indigo-950/80 text-indigo-300 border-indigo-700/60";
  } else if (variant === "success") {
    styleClasses = "bg-emerald-950/80 text-emerald-300 border-emerald-700/60";
  } else if (variant === "warning") {
    styleClasses = "bg-amber-950/80 text-amber-300 border-amber-700/60";
  } else if (variant === "error") {
    styleClasses = "bg-rose-950/80 text-rose-300 border-rose-700/60";
  } else if (variant === "voice") {
    if (voice === "soprano") styleClasses = "bg-blue-950/80 text-blue-300 border-blue-700/60";
    else if (voice === "alto") styleClasses = "bg-emerald-950/80 text-emerald-300 border-emerald-700/60";
    else if (voice === "tenor") styleClasses = "bg-amber-950/80 text-amber-300 border-amber-700/60";
    else if (voice === "bass") styleClasses = "bg-red-950/80 text-red-300 border-red-700/60";
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

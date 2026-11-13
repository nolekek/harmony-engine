import React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "success";
  size?: "xs" | "sm" | "md" | "lg";
  icon?: React.ReactNode;
  /** Toggle state, paired with `selectedClass` (mirrors Tabs.TabItem.activeClass). */
  selected?: boolean;
  /**
   * Color classes used instead of the variant's when `selected` is true.
   * Replaces (not merges with) the variant classes, so include `border` width
   * yourself if the selected look needs a border.
   */
  selectedClass?: string;
}

export const Button: React.FC<ButtonProps> = ({
  variant = "secondary",
  size = "sm",
  icon,
  selected = false,
  selectedClass,
  children,
  className = "",
  disabled,
  type = "button",
  ...props
}) => {
  const base =
    "inline-flex items-center justify-center gap-1.5 font-medium rounded-lg transition-all select-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-ring";

  const sizeClasses = {
    xs: "px-2 py-1 text-xs",
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-5 py-2.5 text-base font-semibold",
  }[size];

  const variantClasses = {
    primary:
      "bg-brand hover:bg-brand-hover text-white shadow-sm shadow-brand/30 active:scale-[0.98]",
    secondary:
      "bg-surface-elevated hover:border-border-strong text-text-primary border border-border active:scale-[0.98]",
    outline:
      "bg-transparent hover:bg-surface-elevated/60 text-text-secondary border border-border active:scale-[0.98]",
    ghost:
      "bg-transparent hover:bg-surface-elevated/60 text-text-muted hover:text-text-primary active:scale-[0.98]",
    danger:
      "bg-rose-600 hover:bg-rose-500 text-white shadow-sm shadow-rose-600/30 active:scale-[0.98]",
    success:
      "bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm shadow-emerald-600/30 active:scale-[0.98]",
  }[variant];

  const colorClasses = selected && selectedClass ? selectedClass : variantClasses;

  return (
    <button
      type={type}
      disabled={disabled}
      className={`${base} ${sizeClasses} ${colorClasses} ${className}`}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </button>
  );
};

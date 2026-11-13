import React, { useId } from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  inputSize?: "sm" | "md";
}

/** Token-styled text/number input with label association and error state. */
export const Input: React.FC<InputProps> = ({
  label,
  error,
  inputSize = "md",
  className = "",
  id,
  ...props
}) => {
  const autoId = useId();
  const inputId = id || autoId;
  const sizeClasses = inputSize === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-sm";

  return (
    <div className="flex flex-col gap-1 w-full">
      {label && (
        <label htmlFor={inputId} className="text-xs font-medium text-text-secondary">
          {label}
        </label>
      )}
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${inputId}-error` : undefined}
        className={`w-full rounded-lg border bg-surface-panel text-text-primary placeholder:text-text-muted focus-ring transition-colors disabled:opacity-50 ${
          error ? "border-rose-500" : "border-border hover:border-border-strong"
        } ${sizeClasses} ${className}`}
        {...props}
      />
      {error && (
        <span id={`${inputId}-error`} role="alert" className="text-[11px] text-rose-700 dark:text-rose-300">
          {error}
        </span>
      )}
    </div>
  );
};

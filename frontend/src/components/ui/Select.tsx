import React, { useId } from "react";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  selectSize?: "sm" | "md";
}

/** Token-styled native select with label association (a11y-safe option list). */
export const Select: React.FC<SelectProps> = ({
  label,
  selectSize = "md",
  className = "",
  id,
  children,
  ...props
}) => {
  const autoId = useId();
  const selectId = id || autoId;
  const sizeClasses = selectSize === "sm" ? "px-2 py-1 text-xs" : "px-3 py-2 text-sm";

  return (
    <div className="flex flex-col gap-1 w-full">
      {label && (
        <label htmlFor={selectId} className="text-xs font-medium text-text-secondary">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`w-full rounded-lg border border-border bg-surface-panel text-text-primary focus-ring transition-colors hover:border-border-strong cursor-pointer disabled:opacity-50 ${sizeClasses} ${className}`}
        {...props}
      >
        {children}
      </select>
    </div>
  );
};

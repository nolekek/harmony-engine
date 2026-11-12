import React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  headerAction?: React.ReactNode;
  badge?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  headerAction,
  badge,
  children,
  className = "",
  ...props
}) => {
  const hasHeader = title || subtitle || headerAction || badge;

  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/80 shadow-md backdrop-blur transition-all ${className}`}
      {...props}
    >
      {hasHeader && (
        <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-b border-slate-800/80">
          <div className="flex items-center gap-2 min-w-0">
            {badge}
            <div>
              {title && (
                <h3 className="text-sm font-semibold text-slate-100 tracking-tight m-0">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-xs text-slate-400 m-0 mt-0.5">{subtitle}</p>
              )}
            </div>
          </div>
          {headerAction && <div className="shrink-0">{headerAction}</div>}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
};

import React from 'react';

export function TableSkeleton({ rows = 5, cols = 6 }) {
  return (
    <div className="w-full space-y-3 animate-pulse">
      {/* Header Skeleton */}
      <div className="h-10 bg-slate-900/80 rounded-lg border border-slate-800 flex items-center px-4 gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <div
            key={`th-${i}`}
            className="h-3.5 bg-slate-800 rounded"
            style={{ width: `${Math.max(12, 100 / cols - 4)}%` }}
          />
        ))}
      </div>
      {/* Rows Skeleton */}
      {Array.from({ length: rows }).map((_, r) => (
        <div
          key={`tr-${r}`}
          className="h-14 bg-slate-900/40 rounded-lg border border-slate-800/60 flex items-center px-4 gap-4"
        >
          {Array.from({ length: cols }).map((_, c) => (
            <div
              key={`td-${r}-${c}`}
              className="h-3 bg-slate-800/80 rounded"
              style={{
                width: c === 0 ? '8%' : c === 1 ? '30%' : `${Math.max(10, 80 / (cols - 2))}%`,
              }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton({ count = 4 }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-3"
        >
          <div className="flex justify-between items-center">
            <div className="h-3 w-24 bg-slate-800 rounded" />
            <div className="w-8 h-8 rounded-xl bg-slate-800" />
          </div>
          <div className="h-7 w-20 bg-slate-800 rounded" />
          <div className="h-3 w-32 bg-slate-850 rounded" />
        </div>
      ))}
    </div>
  );
}

export default { TableSkeleton, CardSkeleton };

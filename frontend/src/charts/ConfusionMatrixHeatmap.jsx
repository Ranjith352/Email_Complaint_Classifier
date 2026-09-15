import React from 'react';

export default function ConfusionMatrixHeatmap({ matrix = [], classNames = [], title = 'Confusion Matrix' }) {
  if (!matrix || matrix.length === 0) {
    return (
      <div className="p-4 text-center text-slate-500 text-sm">
        No confusion matrix data available.
      </div>
    );
  }

  // Calculate max value for color intensity
  const maxVal = Math.max(...matrix.flat(), 1);

  return (
    <div className="overflow-x-auto bg-slate-900 border border-slate-800 rounded-xl p-4">
      <div className="text-sm font-semibold text-slate-200 mb-3 flex items-center justify-between">
        <span>{title}</span>
        <span className="text-xs text-slate-400 font-normal">Real Test Set Evaluation</span>
      </div>

      <div className="inline-block min-w-full align-middle">
        <table className="min-w-full text-xs text-center border-collapse">
          <thead>
            <tr>
              <th className="p-2 text-left font-semibold text-slate-400 border-b border-slate-800">
                Actual \ Predicted
              </th>
              {classNames.map((c, i) => (
                <th key={i} className="p-2 font-medium text-slate-300 border-b border-slate-800 max-w-[90px] truncate" title={c}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, rIdx) => (
              <tr key={rIdx} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                <td className="p-2 text-left font-semibold text-slate-300 max-w-[120px] truncate" title={classNames[rIdx]}>
                  {classNames[rIdx]}
                </td>
                {row.map((cell, cIdx) => {
                  const intensity = Math.min(cell / maxVal, 1);
                  const isDiagonal = rIdx === cIdx;
                  // Green for diagonal hits, reddish/slate for off-diagonal
                  const bgColor = isDiagonal
                    ? `rgba(16, 185, 129, ${0.15 + intensity * 0.75})`
                    : cell > 0
                    ? `rgba(239, 68, 68, ${0.1 + intensity * 0.5})`
                    : 'transparent';

                  return (
                    <td
                      key={cIdx}
                      className="p-2 font-mono font-medium transition-colors"
                      style={{ backgroundColor: bgColor }}
                    >
                      <span className={cell > 0 ? (isDiagonal ? 'text-emerald-200' : 'text-rose-200') : 'text-slate-600'}>
                        {cell}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import React from 'react';

const priorityConfig = {
  P1: { bg: 'bg-rose-500/15', text: 'text-rose-400', border: 'border-rose-500/30', label: 'P1 - Critical' },
  P2: { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30', label: 'P2 - High' },
  P3: { bg: 'bg-sky-500/15', text: 'text-sky-400', border: 'border-sky-500/30', label: 'P3 - Medium' },
  P4: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30', label: 'P4 - Low' },
};

export default function PriorityBadge({ priority = 'P3' }) {
  const config = priorityConfig[priority] || priorityConfig.P3;
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${config.bg} ${config.text} ${config.border}`}>
      {config.label}
    </span>
  );
}

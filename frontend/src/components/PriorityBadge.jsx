import React from 'react';

// Priority indicators should be visually clear: LOW, MEDIUM, HIGH, CRITICAL
export default function PriorityBadge({ priority = 'MEDIUM', showBeacon = true }) {
  const norm = String(priority || '').toUpperCase().trim();

  let config = {
    label: 'MEDIUM',
    bg: 'bg-sky-500/15',
    text: 'text-sky-400',
    border: 'border-sky-500/30',
    dot: 'bg-sky-400',
    pulse: false,
  };

  if (norm === 'CRITICAL' || norm === 'P1') {
    config = {
      label: 'CRITICAL',
      bg: 'bg-rose-500/15',
      text: 'text-rose-300 font-bold',
      border: 'border-rose-500/40 shadow-sm shadow-rose-950/40',
      dot: 'bg-rose-500',
      pulse: true,
    };
  } else if (norm === 'HIGH' || norm === 'P2') {
    config = {
      label: 'HIGH',
      bg: 'bg-amber-500/15',
      text: 'text-amber-300 font-semibold',
      border: 'border-amber-500/40',
      dot: 'bg-amber-400',
      pulse: false,
    };
  } else if (norm === 'MEDIUM' || norm === 'P3') {
    config = {
      label: 'MEDIUM',
      bg: 'bg-sky-500/15',
      text: 'text-sky-300',
      border: 'border-sky-500/30',
      dot: 'bg-sky-400',
      pulse: false,
    };
  } else if (norm === 'LOW' || norm === 'P4') {
    config = {
      label: 'LOW',
      bg: 'bg-emerald-500/15',
      text: 'text-emerald-300',
      border: 'border-emerald-500/30',
      dot: 'bg-emerald-400',
      pulse: false,
    };
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide uppercase border transition-all ${config.bg} ${config.text} ${config.border}`}
    >
      {showBeacon && (
        <span className="relative flex h-2 w-2">
          {config.pulse && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
          )}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${config.dot}`}></span>
        </span>
      )}
      {config.label}
    </span>
  );
}

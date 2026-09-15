import React from 'react';
import { Clock, CheckCircle2, AlertOctagon, Flame, Archive } from 'lucide-react';

export default function StatusBadge({ status = 'OPEN' }) {
  const norm = String(status || '').toUpperCase().trim();

  let config = {
    label: 'Open',
    icon: Clock,
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/25',
  };

  switch (norm) {
    case 'IN_PROGRESS':
    case 'IN PROGRESS':
      config = {
        label: 'In Progress',
        icon: Clock,
        bg: 'bg-purple-500/10',
        text: 'text-purple-300',
        border: 'border-purple-500/30',
      };
      break;
    case 'RESOLVED':
      config = {
        label: 'Resolved',
        icon: CheckCircle2,
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-300',
        border: 'border-emerald-500/30',
      };
      break;
    case 'ESCALATED':
      config = {
        label: 'Escalated',
        icon: Flame,
        bg: 'bg-rose-500/15',
        text: 'text-rose-300 font-bold',
        border: 'border-rose-500/35',
      };
      break;
    case 'CLOSED':
      config = {
        label: 'Closed',
        icon: Archive,
        bg: 'bg-slate-700/20',
        text: 'text-slate-400',
        border: 'border-slate-750',
      };
      break;
    case 'OPEN':
    default:
      config = {
        label: 'Open',
        icon: AlertOctagon,
        bg: 'bg-cyan-500/10',
        text: 'text-cyan-300',
        border: 'border-cyan-500/25',
      };
      break;
  }

  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-medium border ${config.bg} ${config.text} ${config.border}`}
    >
      <Icon className="w-3 h-3" />
      <span>{config.label}</span>
    </span>
  );
}

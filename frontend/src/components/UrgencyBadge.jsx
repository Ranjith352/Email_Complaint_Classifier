import React from 'react';
import { AlertCircle, AlertTriangle, Clock, CheckCircle } from 'lucide-react';

export default function UrgencyBadge({ urgency }) {
  switch (urgency) {
    case 'Critical':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30 animate-pulse">
          <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
          Critical
        </span>
      );
    case 'High':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          High
        </span>
      );
    case 'Medium':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-sky-500/15 text-sky-400 border border-sky-500/30">
          <Clock className="w-3.5 h-3.5 text-sky-400" />
          Medium
        </span>
      );
    case 'Low':
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
          Low
        </span>
      );
  }
}

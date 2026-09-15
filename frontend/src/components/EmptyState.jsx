import React from 'react';
import { Inbox, RefreshCcw } from 'lucide-react';

export default function EmptyState({
  icon: Icon = Inbox,
  title = 'No records found',
  description = 'There are currently no items matching your criteria or filters.',
  actionLabel,
  onAction,
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center rounded-2xl border border-dashed border-slate-850 bg-slate-900/30">
      <div className="w-14 h-14 rounded-2xl bg-slate-850/80 border border-slate-750 flex items-center justify-center text-slate-400 mb-4 shadow-inner">
        <Icon className="w-7 h-7 text-slate-400" />
      </div>
      <h3 className="text-base font-bold text-slate-200 tracking-tight">{title}</h3>
      <p className="mt-1.5 text-xs text-slate-400 max-w-sm leading-relaxed">{description}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-5 inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-brand-500/10 hover:bg-brand-500/20 text-brand-300 border border-brand-500/30 transition-all shadow-sm"
        >
          <RefreshCcw className="w-3.5 h-3.5" />
          <span>{actionLabel}</span>
        </button>
      )}
    </div>
  );
}

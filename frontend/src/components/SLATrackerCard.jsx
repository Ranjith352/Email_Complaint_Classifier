import React, { useState } from 'react';
import { Clock, AlertTriangle, AlertOctagon, CheckCircle2, ArrowUpRight, Flame } from 'lucide-react';

export default function SLATrackerCard({ slaMetrics, isEscalated, onEscalate, loadingEscalate }) {
  const [showEscalateModal, setShowEscalateModal] = useState(false);
  const [escalateReason, setEscalateReason] = useState('');

  if (!slaMetrics) {
    return (
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-400 text-xs flex items-center gap-2">
        <Clock className="w-4 h-4 text-slate-500" />
        <span>SLA tracking initialized upon triage.</span>
      </div>
    );
  }

  const {
    target_hours = 0,
    deadline,
    time_remaining_str = 'N/A',
    is_breached = false,
    percent_elapsed = 0,
    warning_level = 'ON_TRACK'
  } = slaMetrics;

  const getStatusBadge = () => {
    if (is_breached || warning_level === 'BREACHED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
          <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
          SLA BREACHED
        </span>
      );
    }
    if (warning_level === 'CRITICAL_WARNING') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-orange-500/20 text-orange-300 border border-orange-500/40 animate-pulse">
          <Flame className="w-3.5 h-3.5 text-orange-400" />
          Critical Warning (90% Elapsed)
        </span>
      );
    }
    if (warning_level === 'WARNING') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          Warning (75% Elapsed)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
        On Track
      </span>
    );
  };

  const getProgressColor = () => {
    if (is_breached || warning_level === 'BREACHED') return 'bg-rose-500';
    if (warning_level === 'CRITICAL_WARNING') return 'bg-orange-500';
    if (warning_level === 'WARNING') return 'bg-amber-400';
    return 'bg-emerald-500';
  };

  const formattedDeadline = deadline
    ? new Date(deadline).toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : 'Not Assigned';

  const handleEscalateSubmit = (e) => {
    e.preventDefault();
    if (!escalateReason.trim()) return;
    if (onEscalate) {
      onEscalate(escalateReason);
    }
    setShowEscalateModal(false);
    setEscalateReason('');
  };

  return (
    <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-sm space-y-4 shadow-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-brand-400" />
          <h4 className="text-sm font-bold text-white tracking-wide">SLA Tracking & Governance</h4>
        </div>
        <div>{getStatusBadge()}</div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
          <span className="text-slate-400 block text-[11px]">SLA Target</span>
          <span className="font-bold text-slate-100 text-sm">{target_hours} Hours</span>
        </div>
        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
          <span className="text-slate-400 block text-[11px]">SLA Deadline</span>
          <span className="font-semibold text-slate-200 text-xs">{formattedDeadline}</span>
        </div>
        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 col-span-2 sm:col-span-1">
          <span className="text-slate-400 block text-[11px]">Time Remaining</span>
          <span className={`font-bold text-sm ${is_breached ? 'text-rose-400' : 'text-slate-100'}`}>
            {time_remaining_str}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span>Elapsed Time</span>
          <span className="font-bold text-slate-200">{Math.min(100, Math.round(percent_elapsed))}%</span>
        </div>
        <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 rounded-full ${getProgressColor()}`}
            style={{ width: `${Math.min(100, Math.max(3, percent_elapsed))}%` }}
          />
        </div>
      </div>

      {/* Escalation Controls */}
      <div className="pt-1 flex items-center justify-between border-t border-slate-800/80">
        <div className="text-[11px] text-slate-400">
          {isEscalated ? (
            <span className="inline-flex items-center gap-1 font-semibold text-amber-400">
              <ArrowUpRight className="w-3.5 h-3.5" /> Ticket Escalated
            </span>
          ) : (
            <span>High risk or delay? Escalate to supervisors.</span>
          )}
        </div>

        {!isEscalated && onEscalate && (
          <button
            type="button"
            onClick={() => setShowEscalateModal(true)}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1.5 transition-colors"
          >
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>Escalate SLA</span>
          </button>
        )}
      </div>

      {/* Escalate Modal */}
      {showEscalateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-2xl p-5 space-y-4 shadow-2xl">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <ArrowUpRight className="w-4 h-4 text-amber-400" />
              Escalate Complaint to Leadership
            </h4>
            <p className="text-xs text-slate-300">
              Provide the justification for escalating this complaint. This will notify team leads and record an audit event.
            </p>
            <form onSubmit={handleEscalateSubmit} className="space-y-3">
              <textarea
                required
                rows={3}
                value={escalateReason}
                onChange={(e) => setEscalateReason(e.target.value)}
                placeholder="Reason for escalation (e.g. Critical customer impact, approaching SLA deadline, high refund threshold)..."
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-amber-400"
              />
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowEscalateModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loadingEscalate}
                  className="px-4 py-1.5 rounded-lg text-xs font-bold bg-amber-600 hover:bg-amber-500 text-white shadow-lg disabled:opacity-50"
                >
                  {loadingEscalate ? 'Escalating...' : 'Confirm Escalation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

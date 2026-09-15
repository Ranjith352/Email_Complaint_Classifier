import React from 'react';
import {
  Sparkles, AlertCircle, AlertTriangle, TrendingUp, TrendingDown,
  ShieldAlert, CheckCircle, Flame, ArrowRight, ExternalLink
} from 'lucide-react';

export default function AIInsightsSection({ insights = [], onInspectInsight, title = "Operational AI Insights" }) {
  if (!insights || insights.length === 0) {
    return null;
  }

  const getSeverityStyle = (severity) => {
    switch ((severity || '').toUpperCase()) {
      case 'CRITICAL':
        return {
          card: 'bg-rose-950/20 border-rose-500/40 hover:border-rose-500/60 shadow-rose-950/20',
          badge: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
          icon: <ShieldAlert className="w-4 h-4 text-rose-400" />
        };
      case 'WARNING':
        return {
          card: 'bg-amber-950/20 border-amber-500/40 hover:border-amber-500/60 shadow-amber-950/20',
          badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />
        };
      case 'SUCCESS':
        return {
          card: 'bg-emerald-950/20 border-emerald-500/40 hover:border-emerald-500/60 shadow-emerald-950/20',
          badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          icon: <CheckCircle className="w-4 h-4 text-emerald-400" />
        };
      default:
        return {
          card: 'bg-brand-950/20 border-brand-500/30 hover:border-brand-500/50 shadow-brand-950/10',
          badge: 'bg-brand-500/20 text-brand-300 border-brand-500/40',
          icon: <Sparkles className="w-4 h-4 text-brand-400" />
        };
    }
  };

  return (
    <div className="glass-panel p-5 rounded-2xl border border-purple-500/30 bg-gradient-to-br from-purple-950/20 via-slate-900/60 to-slate-950/80 space-y-4 shadow-xl">
      <div className="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-purple-500/20">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-purple-500/20 border border-purple-500/40 text-purple-300">
            <Sparkles className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-black text-white tracking-wide uppercase flex items-center gap-2">
              <span>{title}</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                Live Data-Grounded
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Deterministic operational intelligence derived directly from database telemetry with zero fabrication.
            </p>
          </div>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          {insights.length} active {insights.length === 1 ? 'signal' : 'signals'}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {insights.map((item, idx) => {
          const style = getSeverityStyle(item.severity);
          return (
            <div
              key={item.id || idx}
              className={`p-4 rounded-xl border transition-all duration-200 flex flex-col justify-between space-y-3 ${style.card} hover:-translate-y-0.5 shadow-lg`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${style.badge}`}>
                    {style.icon}
                    <span>{item.category || item.type || 'INSIGHT'}</span>
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {item.severity}
                  </span>
                </div>

                <p className="text-xs font-semibold text-white leading-relaxed">
                  "{item.message}"
                </p>
              </div>

              {item.data_point && (
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                  <span className="truncate">
                    {Object.entries(item.data_point).slice(0, 2).map(([k, v]) => `${k.replace('_', ' ')}: ${v}`).join(' · ')}
                  </span>
                  {onInspectInsight && (
                    <button
                      onClick={() => onInspectInsight(item)}
                      className="text-brand-400 hover:text-brand-300 font-medium inline-flex items-center gap-1 shrink-0 ml-2"
                    >
                      <span>Filter</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

import React from 'react';

export default function StatCard({ title, value, subtitle, icon: Icon, change, isCritical, accentColor = 'blue' }) {
  const getGradient = () => {
    switch (accentColor) {
      case 'rose':
        return 'from-rose-500/20 to-transparent text-rose-400 border-rose-500/30';
      case 'emerald':
        return 'from-emerald-500/20 to-transparent text-emerald-400 border-emerald-500/30';
      case 'amber':
        return 'from-amber-500/20 to-transparent text-amber-400 border-amber-500/30';
      case 'purple':
        return 'from-purple-500/20 to-transparent text-purple-400 border-purple-500/30';
      default:
        return 'from-blue-500/20 to-transparent text-blue-400 border-blue-500/30';
    }
  };

  return (
    <div className={`relative overflow-hidden rounded-xl border p-5 glass-panel glass-panel-hover transition-all duration-300 ${isCritical ? 'ring-1 ring-rose-500/40' : ''}`}>
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl ${getGradient()} opacity-40 blur-2xl pointer-events-none`} />
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</p>
          <h3 className="mt-2 text-3xl font-extrabold text-white tracking-tight">{value}</h3>
        </div>
        <div className={`p-3 rounded-xl border bg-slate-900/80 ${getGradient()}`}>
          {Icon && <Icon className="w-6 h-6" />}
        </div>
      </div>
      {(subtitle || change) && (
        <div className="mt-4 flex items-center gap-2 text-xs font-medium">
          {change && (
            <span className={`px-1.5 py-0.5 rounded font-bold ${change.startsWith('+') ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-400 bg-slate-800'}`}>
              {change}
            </span>
          )}
          <span className="text-slate-400">{subtitle}</span>
        </div>
      )}
    </div>
  );
}

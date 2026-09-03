import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Legend, Cell
} from 'recharts';
import { BarChart3, PieChart as PieIcon, ShieldAlert, Sparkles, Clock, HeartHandshake } from 'lucide-react';
import { getDashboardAnalytics } from '../api/analytics';

const URGENCY_COLORS = {
  Critical: '#f43f5e',
  High: '#f59e0b',
  Medium: '#38bdf8',
  Low: '#10b981',
};

const EMOTION_COLORS = {
  Anger: '#ef4444',
  Frustration: '#f97316',
  Anxiety: '#eab308',
  Disappointment: '#a855f7',
  Neutral: '#64748b',
  Gratitude: '#10b981',
};

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const data = await getDashboardAnalytics();
      setAnalytics(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const sentimentData = analytics?.sentiment_breakdown
    ? Object.entries(analytics.sentiment_breakdown).map(([key, val]) => ({ name: key, count: val }))
    : [];

  const categoryData = analytics?.category_counts
    ? Object.entries(analytics.category_counts).map(([key, val]) => ({ name: key, count: val }))
    : [];

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">Enterprise Visual Analytics & Intelligence</h2>
        <p className="text-xs text-slate-400 mt-1">
          Deep analytics on department routing efficiency, SLA performance, and customer sentiment distribution.
        </p>
      </div>

      {/* Row 1: Department Workload (Open vs Resolved) */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-brand-400" /> Department Workload: Active vs Resolved Cases
            </h3>
            <p className="text-[11px] text-slate-400">Resolution velocity comparing open backlog against completed tickets</p>
          </div>
        </div>

        <div className="h-72">
          {analytics?.department_volumes && analytics.department_volumes.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.department_volumes} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <XAxis dataKey="department" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Bar dataKey="open" name="Active Backlog" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="resolved" name="Resolved Tickets" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">No volume data</div>
          )}
        </div>
      </div>

      {/* Row 2: Urgency Distribution & Customer Sentiment */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Urgency Breakdown */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-1">
              <ShieldAlert className="w-4 h-4 text-rose-400" /> Urgency Severity Classification
            </h3>
            <p className="text-[11px] text-slate-400 mb-4">NLP multi-factor priority weighting</p>
          </div>

          <div className="space-y-3">
            {analytics?.urgency_distributions?.map((item) => (
              <div key={item.urgency} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-300 flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: URGENCY_COLORS[item.urgency] || '#64748b' }}
                    />
                    {item.urgency} Urgency
                  </span>
                  <span className="font-mono text-slate-400">
                    {item.count} tickets ({item.percentage}%)
                  </span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${item.percentage}%`,
                      backgroundColor: URGENCY_COLORS[item.urgency] || '#64748b'
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800/60 text-[11px] text-slate-400">
            Critical tickets trigger 4-hour SLA timers and instant escalations.
          </div>
        </div>

        {/* Emotion / Sentiment Breakdown */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-1">
              <HeartHandshake className="w-4 h-4 text-purple-400" /> Customer Emotion & Sentiment Index
            </h3>
            <p className="text-[11px] text-slate-400 mb-4">Linguistic emotion detection for tone calibration</p>
          </div>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sentimentData} layout="vertical" margin={{ left: 20, right: 20 }}>
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={11} width={90} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                />
                <Bar dataKey="count" fill="#a855f7" radius={[0, 4, 4, 0]}>
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={EMOTION_COLORS[entry.name] || '#a855f7'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/60 text-[11px] text-slate-400">
            Detected emotions directly instruct the Generative AI response drafter's empathy level.
          </div>
        </div>

      </div>

      {/* Row 3: Category Volume Rankings */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800/80">
        <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-1">
          <Sparkles className="w-4 h-4 text-blue-400" /> Top Complaint Categories
        </h3>
        <p className="text-[11px] text-slate-400 mb-4">Semantic clustering volume across taxonomy classifications</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          {categoryData.map((c) => (
            <div key={c.name} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
              <span className="text-xs font-semibold text-slate-300 leading-tight">{c.name}</span>
              <span className="text-2xl font-mono font-black text-brand-400 mt-2">{c.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

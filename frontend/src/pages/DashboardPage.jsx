import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Inbox, AlertCircle, CheckCircle2, Clock, Zap, Plus, ArrowUpRight, TrendingUp, ShieldCheck,
  ShieldAlert, Sparkles, RefreshCw, AlertTriangle, Copy, Users, BrainCircuit, BarChart3,
  PieChart as PieIcon, Activity
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, PieChart, Pie, Legend
} from 'recharts';
import StatCard from '../components/StatCard';
import UrgencyBadge from '../components/UrgencyBadge';
import PriorityBadge from '../components/PriorityBadge';
import DepartmentBadge from '../components/DepartmentBadge';
import AIInsightsSection from '../components/AIInsightsSection';
import ComplaintDetailModal from '../components/ComplaintDetailModal';
import NewComplaintModal from '../components/NewComplaintModal';
import { getDashboardAnalytics } from '../api/analytics';
import { getComplaints } from '../api/complaints';
import { getActiveIncidents, detectIncidents, acknowledgeIncident, resolveIncident } from '../api/incidents';

const PALETTE = ['#3b82f6', '#10b981', '#a855f7', '#f59e0b', '#ec4899', '#06b6d4', '#f43f5e', '#8b5cf6'];
const SENTIMENT_COLORS = {
  Positive: '#10b981',
  Neutral: '#64748b',
  Negative: '#ef4444'
};
const PRIORITY_COLORS = {
  P1: '#ef4444',
  P2: '#f97316',
  P3: '#3b82f6',
  P4: '#64748b'
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [criticalComplaints, setCriticalComplaints] = useState([]);
  const [activeIncidents, setActiveIncidents] = useState([]);
  const [scanningIncidents, setScanningIncidents] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [showNewModal, setShowNewModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [anRes, compRes, incRes] = await Promise.all([
        getDashboardAnalytics(),
        getComplaints({ urgency: 'Critical', limit: 5 }),
        getActiveIncidents().catch(() => [])
      ]);
      setAnalytics(anRes);
      setCriticalComplaints(compRes || []);
      setActiveIncidents(incRes || []);
    } catch (err) {
      console.error('Failed to load dashboard analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleScanIncidents = async () => {
    setScanningIncidents(true);
    try {
      await detectIncidents({ window_hours: 24, min_complaints: 3, similarity_threshold: 0.60 });
      const updated = await getActiveIncidents();
      setActiveIncidents(updated || []);
      loadData();
    } catch (err) {
      console.error('Failed to scan incidents:', err);
    } finally {
      setScanningIncidents(false);
    }
  };

  const handleAcknowledgeIncident = async (id) => {
    try {
      await acknowledgeIncident(id, 'Operations Manager', 'Acknowledged and analyzing root cause.');
      const updated = await getActiveIncidents();
      setActiveIncidents(updated || []);
    } catch (err) {
      console.error('Failed to acknowledge incident:', err);
    }
  };

  const handleResolveIncident = async (id) => {
    const notes = prompt('Enter resolution summary:', 'Incident root cause mitigated and services restored.');
    if (!notes) return;
    try {
      await resolveIncident(id, 'Operations Manager', notes);
      const updated = await getActiveIncidents();
      setActiveIncidents(updated || []);
      loadData();
    } catch (err) {
      console.error('Failed to resolve incident:', err);
    }
  };

  const kpis = analytics?.kpis || {};
  const charts = analytics?.charts || {};
  const insights = analytics?.insights || [];

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      {/* Top Banner & Action Controls */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-black text-white tracking-tight">Main Executive Command Center</h2>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              Live Database Telemetry
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Global operational overview, real-time SLA metrics, non-fabricated AI insights, and multi-dimensional chart telemetry.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadData}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh All Analytics"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleScanIncidents}
            disabled={scanningIncidents}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-rose-300 border border-rose-500/30 shadow-sm transition-all disabled:opacity-50"
          >
            <ShieldAlert className={`w-3.5 h-3.5 ${scanningIncidents ? 'animate-spin' : ''}`} />
            <span>{scanningIncidents ? 'Scanning Clusters...' : 'Detect Incidents'}</span>
          </button>
          <button
            onClick={() => setShowNewModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/20 transition-all hover:scale-[1.02]"
          >
            <Plus className="w-4 h-4" />
            <span>New Complaint</span>
          </button>
        </div>
      </div>

      {/* 10. AI INSIGHTS SECTION (Live, Non-Fabricated Insights Grounded in DB Data) */}
      <AIInsightsSection
        insights={insights}
        title="Live Database AI Insights & Signals"
        onInspectInsight={(ins) => {
          if (ins.action_url) {
            navigate(ins.action_url);
          }
        }}
      />

      {/* Active Incidents Banner if detected */}
      {activeIncidents.length > 0 && (
        <div className="space-y-3">
          {activeIncidents.map((inc) => (
            <div
              key={inc.id}
              className="p-5 rounded-2xl bg-gradient-to-r from-rose-950/40 via-purple-950/25 to-slate-900 border border-rose-500/50 shadow-xl relative overflow-hidden"
            >
              <div className="flex items-start justify-between flex-wrap gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-black uppercase tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/50 animate-pulse">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      Active Incident Detected
                    </span>
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800">
                      {inc.incident_number}
                    </span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-rose-500/30 text-rose-200 border border-rose-500/60">
                      Severity: {inc.severity}
                    </span>
                    <DepartmentBadge department={inc.department_name} />
                  </div>
                  <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                    <span className="text-rose-300">{inc.title}</span>
                  </h3>
                  <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                    {inc.description}
                  </p>
                  <div className="flex items-center gap-4 text-xs pt-1">
                    <span className="text-slate-400">
                      Affected Tickets: <strong className="text-rose-400 font-mono text-sm">{inc.affected_count}</strong>
                    </span>
                    <span className="text-slate-400">
                      Detected: <strong className="text-slate-200">{new Date(inc.detected_at).toLocaleTimeString()}</strong>
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {inc.status === 'DETECTED' && (
                    <button
                      onClick={() => handleAcknowledgeIncident(inc.id)}
                      className="px-3 py-1.5 rounded-xl text-xs font-bold bg-amber-600 hover:bg-amber-500 text-white flex items-center gap-1.5 shadow"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Acknowledge</span>
                    </button>
                  )}
                  <button
                    onClick={() => handleResolveIncident(inc.id)}
                    className="px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-1.5 shadow"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Resolve Incident</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 9. THE 10 MAIN DASHBOARD KPIS */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-brand-400" />
            Core Enterprise Operational KPIs (10 Metrics)
          </h3>
          <span className="text-[11px] text-slate-500">Real-time DB aggregate</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {/* KPI 1: Total Complaints */}
          <StatCard
            title="Total Complaints"
            value={kpis.total_complaints ?? 0}
            subtitle="All logged tickets"
            icon={Inbox}
            accentColor="blue"
          />

          {/* KPI 2: Open Complaints */}
          <StatCard
            title="Open Complaints"
            value={kpis.open_complaints ?? 0}
            subtitle="Pending active triage"
            icon={Clock}
            accentColor="amber"
          />

          {/* KPI 3: Critical Complaints */}
          <StatCard
            title="Critical Complaints"
            value={kpis.critical_complaints ?? 0}
            subtitle="Immediate escalation"
            icon={AlertCircle}
            accentColor="rose"
            isCritical={Boolean(kpis.critical_complaints && kpis.critical_complaints > 0)}
          />

          {/* KPI 4: Resolved Complaints */}
          <StatCard
            title="Resolved Complaints"
            value={kpis.resolved_complaints ?? 0}
            subtitle={`Closed cases (${kpis.resolution_rate ?? 0}%)`}
            icon={CheckCircle2}
            accentColor="emerald"
          />

          {/* KPI 5: SLA Breaches */}
          <StatCard
            title="SLA Breaches"
            value={kpis.sla_breaches ?? 0}
            subtitle="Past SLA resolution deadline"
            icon={ShieldAlert}
            accentColor="rose"
            isCritical={Boolean(kpis.sla_breaches && kpis.sla_breaches > 0)}
          />

          {/* KPI 6: Average Resolution Time */}
          <StatCard
            title="Avg Resolution Time"
            value={`${kpis.avg_resolution_hours ?? 0}h`}
            subtitle="Average hours to close"
            icon={Clock}
            accentColor="blue"
          />

          {/* KPI 7: AI Auto-routing Rate */}
          <StatCard
            title="AI Auto-Routing"
            value={`${kpis.ai_auto_routing_rate ?? 0}%`}
            subtitle="Routed without manual touch"
            icon={Zap}
            accentColor="purple"
          />

          {/* KPI 8: AI Confidence */}
          <StatCard
            title="AI Confidence"
            value={`${kpis.ai_confidence ?? 0}%`}
            subtitle="Mean NLP classification score"
            icon={Sparkles}
            accentColor="indigo"
          />

          {/* KPI 9: Duplicate Complaints */}
          <StatCard
            title="Duplicate Tickets"
            value={kpis.duplicate_complaints ?? 0}
            subtitle="Identified duplicate cases"
            icon={Copy}
            accentColor="amber"
          />

          {/* KPI 10: Human Review Required */}
          <StatCard
            title="Human Review Req."
            value={kpis.human_review_required ?? 0}
            subtitle="Flagged for manual audit"
            icon={AlertTriangle}
            accentColor="orange"
          />
        </div>
      </div>

      {/* 9. NINE RESPONSIVE VISUAL CHARTS */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <BarChart3 className="w-3.5 h-3.5 text-brand-400" />
            Operational & Triage Visual Analytics (9 Telemetry Charts)
          </h3>
          <span className="text-[11px] text-slate-500">Interactive charts</span>
        </div>

        {/* ROW 1: Chart 1 (Complaints Over Time) & Chart 2 (Complaints by Department) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart 1: Complaints over time */}
          <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-800/80">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-brand-400" />
                  1. Complaints Over Time
                </h4>
                <p className="text-[11px] text-slate-400">Daily ticket ingestion, resolution, and critical surges (Last 7 Days)</p>
              </div>
            </div>
            <div className="h-64">
              {charts?.complaints_over_time?.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={charts.complaints_over_time}>
                    <defs>
                      <linearGradient id="colorCreated" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorResolved" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorCritical" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                    />
                    <Area type="monotone" dataKey="created" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorCreated)" name="Ingested" />
                    <Area type="monotone" dataKey="resolved" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorResolved)" name="Resolved" />
                    <Area type="monotone" dataKey="critical" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorCritical)" name="Critical" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">No time series data</div>
              )}
            </div>
          </div>

          {/* Chart 2: Complaints by department */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
            <div>
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-purple-400" />
                2. Complaints by Department
              </h4>
              <p className="text-[11px] text-slate-400">Distribution of workload across organizational units</p>
            </div>
            <div className="h-60 my-2">
              {charts?.complaints_by_department?.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={charts.complaints_by_department} layout="vertical" margin={{ left: 10, right: 10 }}>
                    <XAxis type="number" stroke="#64748b" fontSize={10} allowDecimals={false} />
                    <YAxis dataKey="department" type="category" stroke="#94a3b8" fontSize={10} width={90} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                    />
                    <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} name="Total Complaints" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">No department data</div>
              )}
            </div>
          </div>
        </div>

        {/* ROW 2: Chart 3 (By Category), Chart 4 (Priority Distribution), Chart 5 (Sentiment Distribution) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Chart 3: Complaints by category */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80">
            <h4 className="text-sm font-bold text-white mb-1">3. Complaints by Category</h4>
            <p className="text-[11px] text-slate-400 mb-4">Volume per functional inquiry domain</p>
            <div className="h-56">
              {charts?.complaints_by_category?.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={charts.complaints_by_category} margin={{ top: 5, right: 5, bottom: 25, left: -10 }}>
                    <XAxis dataKey="category" stroke="#64748b" fontSize={10} angle={-30} textAnchor="end" interval={0} />
                    <YAxis stroke="#64748b" fontSize={10} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                    />
                    <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]} name="Tickets" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">No category data</div>
              )}
            </div>
          </div>

          {/* Chart 4: Priority distribution */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80">
            <h4 className="text-sm font-bold text-white mb-1">4. Priority Distribution</h4>
            <p className="text-[11px] text-slate-400 mb-4">Severity tiers from P1 (Critical) to P4 (Low)</p>
            <div className="h-56">
              {charts?.priority_distribution?.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={charts.priority_distribution} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
                    <XAxis dataKey="priority" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]} name="Tickets">
                      {charts.priority_distribution.map((entry) => (
                        <Cell key={entry.priority} fill={PRIORITY_COLORS[entry.priority] || '#3b82f6'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">No priority data</div>
              )}
            </div>
          </div>

          {/* Chart 5: Sentiment distribution */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
            <div>
              <h4 className="text-sm font-bold text-white mb-1">5. Sentiment Distribution</h4>
              <p className="text-[11px] text-slate-400">NLP customer tone analysis</p>
            </div>
            <div className="h-44 my-2">
              {charts?.sentiment_distribution?.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={charts.sentiment_distribution}
                      dataKey="count"
                      nameKey="sentiment"
                      cx="50%"
                      cy="50%"
                      innerRadius={35}
                      outerRadius={65}
                      paddingAngle={4}
                    >
                      {charts.sentiment_distribution.map((entry) => (
                        <Cell key={entry.sentiment} fill={SENTIMENT_COLORS[entry.sentiment] || '#64748b'} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">No sentiment data</div>
              )}
            </div>
            <div className="grid grid-cols-3 gap-1 text-[11px] text-center pt-1 border-t border-slate-800">
              {charts?.sentiment_distribution?.map((s) => (
                <div key={s.sentiment}>
                  <p className="font-bold text-white">{s.count}</p>
                  <p className="text-slate-400 text-[10px]">{s.sentiment}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ROW 3: Chart 6 (Emotion), Chart 7 (Resolution Time), Chart 8 (SLA Compliance) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Chart 6: Emotion distribution */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80">
            <h4 className="text-sm font-bold text-white mb-1">6. Emotion Distribution</h4>
            <p className="text-[11px] text-slate-400 mb-4">Granular emotional state extracted by AI</p>
            <div className="h-56">
              {charts?.emotion_distribution?.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={charts.emotion_distribution} margin={{ top: 5, right: 5, bottom: 25, left: -10 }}>
                    <XAxis dataKey="emotion" stroke="#64748b" fontSize={10} angle={-30} textAnchor="end" interval={0} />
                    <YAxis stroke="#64748b" fontSize={10} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                    />
                    <Bar dataKey="count" fill="#ec4899" radius={[4, 4, 0, 0]} name="Occurrences" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">No emotion data</div>
              )}
            </div>
          </div>

          {/* Chart 7: Resolution time */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80">
            <h4 className="text-sm font-bold text-white mb-1">7. Resolution Time</h4>
            <p className="text-[11px] text-slate-400 mb-4">Turnaround duration duration brackets</p>
            <div className="h-56">
              {charts?.resolution_time?.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={charts.resolution_time} margin={{ top: 5, right: 5, bottom: 20, left: -10 }}>
                    <XAxis dataKey="bucket" stroke="#64748b" fontSize={10} angle={-25} textAnchor="end" interval={0} />
                    <YAxis stroke="#64748b" fontSize={10} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                    />
                    <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Resolved Cases" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">No resolution data</div>
              )}
            </div>
          </div>

          {/* Chart 8: SLA compliance */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
            <div>
              <h4 className="text-sm font-bold text-white mb-1">8. SLA Compliance</h4>
              <p className="text-[11px] text-slate-400">Compliance vs approaching breach vs breached</p>
            </div>
            <div className="h-44 my-2">
              {charts?.sla_compliance?.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={charts.sla_compliance}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={35}
                      outerRadius={65}
                      paddingAngle={4}
                    >
                      {charts.sla_compliance.map((entry) => (
                        <Cell key={entry.name} fill={entry.color || '#3b82f6'} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">No SLA data</div>
              )}
            </div>
            <div className="grid grid-cols-3 gap-1 text-[11px] text-center pt-1 border-t border-slate-800">
              {charts?.sla_compliance?.map((item) => (
                <div key={item.name}>
                  <p className="font-bold text-white">{item.value}</p>
                  <p className="text-slate-400 text-[10px] truncate">{item.name}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ROW 4: Chart 9 (Agent Workload) */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-emerald-400" />
                9. Agent Workload & Utilization
              </h4>
              <p className="text-[11px] text-slate-400">Current assigned active ticket capacity across support agents</p>
            </div>
          </div>

          <div className="h-64">
            {charts?.agent_workload?.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.agent_workload} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
                  <XAxis dataKey="agent_name" stroke="#64748b" fontSize={11} angle={-20} textAnchor="end" interval={0} />
                  <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                    formatter={(value, name) => [value, name === 'current_workload' ? 'Active Complaints' : name]}
                  />
                  <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: '10px', fontSize: '12px' }} />
                  <Bar dataKey="current_workload" fill="#10b981" radius={[4, 4, 0, 0]} name="Current Active Tickets" />
                  <Bar dataKey="max_workload" fill="#334155" radius={[4, 4, 0, 0]} name="Max Workload Capacity" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No active agent assignments recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Critical Attention Queue Table */}
      <div className="glass-panel rounded-2xl border border-slate-800/80 p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400" />
              Critical Attention & P1 Triage Queue
            </h3>
            <p className="text-[11px] text-slate-400">Complaints flagged with highest business risk, shortest SLA, and critical urgency</p>
          </div>
          <button
            onClick={() => navigate('/complaints')}
            className="text-xs font-bold text-brand-400 hover:text-brand-300 flex items-center gap-1"
          >
            <span>Open All Complaints</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="pb-3 font-semibold">Ticket</th>
                <th className="pb-3 font-semibold">Subject & Customer</th>
                <th className="pb-3 font-semibold">Department</th>
                <th className="pb-3 font-semibold">Priority</th>
                <th className="pb-3 font-semibold">Urgency</th>
                <th className="pb-3 font-semibold">Status</th>
                <th className="pb-3 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {criticalComplaints.map((c) => (
                <tr key={c.id} className="hover:bg-slate-900/50 transition-colors">
                  <td className="py-3 font-mono font-bold text-slate-300">{c.ticket_number}</td>
                  <td className="py-3 max-w-sm">
                    <p className="font-semibold text-white truncate">{c.subject || c.title}</p>
                    <p className="text-[11px] text-slate-400 truncate">{c.customer_name || c.customer_email || c.sender_email}</p>
                  </td>
                  <td className="py-3"><DepartmentBadge department={c.department_name || c.department || c.category} /></td>
                  <td className="py-3"><PriorityBadge priority={c.priority || 'P1'} /></td>
                  <td className="py-3"><UrgencyBadge urgency={c.urgency || 'Critical'} /></td>
                  <td className="py-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                      {c.status || 'OPEN'}
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => setSelectedComplaint(c)}
                      className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-300 text-xs font-semibold border border-slate-700 transition-colors"
                    >
                      <span>Triage</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
              {criticalComplaints.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No critical tickets in the queue! System SLA compliance is healthy.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modals */}
      {selectedComplaint && (
        <ComplaintDetailModal
          complaint={selectedComplaint}
          onClose={() => setSelectedComplaint(null)}
          onUpdated={() => {
            loadData();
            setSelectedComplaint(null);
          }}
        />
      )}

      {showNewModal && (
        <NewComplaintModal
          onClose={() => setShowNewModal(false)}
          onCreated={() => {
            loadData();
            setShowNewModal(false);
          }}
        />
      )}
    </div>
  );
}

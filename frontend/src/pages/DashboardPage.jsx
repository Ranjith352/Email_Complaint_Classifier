import React, { useState, useEffect } from 'react';
import {
  Inbox, AlertCircle, CheckCircle2, Clock, Zap, Plus, ArrowUpRight, TrendingUp, ShieldCheck
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, PieChart, Pie
} from 'recharts';
import StatCard from '../components/StatCard';
import UrgencyBadge from '../components/UrgencyBadge';
import DepartmentBadge from '../components/DepartmentBadge';
import ComplaintDetailModal from '../components/ComplaintDetailModal';
import NewComplaintModal from '../components/NewComplaintModal';
import { getDashboardAnalytics } from '../api/analytics';
import { getComplaints } from '../api/complaints';

const COLORS = ['#3b82f6', '#10b981', '#a855f7', '#f59e0b', '#ec4899'];

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState(null);
  const [criticalComplaints, setCriticalComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [showNewModal, setShowNewModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [anRes, compRes] = await Promise.all([
        getDashboardAnalytics(),
        getComplaints({ urgency: 'Critical', limit: 5 }),
      ]);
      setAnalytics(anRes);
      setCriticalComplaints(compRes);
    } catch (err) {
      console.error('Failed to load dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  const kpis = analytics?.kpis;

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header banner */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-black text-white tracking-tight">Executive Triage Command Center</h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-channel complaint classification, pgvector semantic routing, and SLA compliance telemetry.
          </p>
        </div>
        <button
          onClick={() => setShowNewModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/20 transition-all hover:scale-[1.02]"
        >
          <Plus className="w-4 h-4" />
          <span>New Complaint Triage</span>
        </button>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Ingested"
          value={kpis?.total_complaints ?? 0}
          subtitle="All recorded tickets"
          icon={Inbox}
          accentColor="blue"
        />
        <StatCard
          title="Critical Urgency"
          value={kpis?.critical_cases ?? 0}
          subtitle="Immediate action required"
          icon={AlertCircle}
          accentColor="rose"
          isCritical={Boolean(kpis?.critical_cases && kpis.critical_cases > 0)}
        />
        <StatCard
          title="Resolution Rate"
          value={`${kpis?.resolution_rate ?? 0}%`}
          subtitle="Successfully closed tickets"
          icon={CheckCircle2}
          accentColor="emerald"
        />
        <StatCard
          title="SLA Compliance"
          value={`${kpis?.sla_compliance_rate ?? 100}%`}
          subtitle="Resolved within deadline"
          icon={ShieldCheck}
          accentColor="purple"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ingestion & Resolution Trend */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-800/80">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-brand-400" /> Ingestion & Resolution Timeline
              </h3>
              <p className="text-[11px] text-slate-400">Incoming email tickets vs closed resolutions</p>
            </div>
          </div>
          <div className="h-64">
            {analytics?.trends && analytics.trends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analytics.trends}>
                  <defs>
                    <linearGradient id="colorCreated" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorResolved" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="created" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorCreated)" name="Ingested" />
                  <Area type="monotone" dataKey="resolved" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorResolved)" name="Resolved" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">No trend history available yet.</div>
            )}
          </div>
        </div>

        {/* Department Distribution */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" /> Department Routing Volume
            </h3>
            <p className="text-[11px] text-slate-400">Triage allocation across teams</p>
          </div>
          <div className="h-52 my-2">
            {analytics?.department_volumes && analytics.department_volumes.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={analytics.department_volumes}
                    dataKey="count"
                    nameKey="department"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={3}
                  >
                    {analytics.department_volumes.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">No data</div>
            )}
          </div>
          <div className="space-y-1 text-xs">
            {analytics?.department_volumes?.slice(0, 4).map((d, i) => (
              <div key={d.department} className="flex items-center justify-between text-slate-300">
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  {d.department}
                </span>
                <span className="font-mono text-slate-400 font-bold">{d.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Critical Queue Table */}
      <div className="glass-panel rounded-2xl border border-slate-800/80 p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400" /> Critical & High Priority Attention Queue
            </h3>
            <p className="text-[11px] text-slate-400">Complaints flagged by NLP with highest business risk and shortest SLA</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="pb-3 font-semibold">Ticket</th>
                <th className="pb-3 font-semibold">Subject & Customer</th>
                <th className="pb-3 font-semibold">Department</th>
                <th className="pb-3 font-semibold">Urgency</th>
                <th className="pb-3 font-semibold">Status</th>
                <th className="pb-3 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {criticalComplaints.map((c) => (
                <tr key={c.id} className="hover:bg-slate-900/50 transition-colors">
                  <td className="py-3 font-mono font-bold text-slate-300">{c.ticket_number}</td>
                  <td className="py-3">
                    <p className="font-medium text-white max-w-xs md:max-w-md truncate">{c.title}</p>
                    <p className="text-[11px] text-slate-400">{c.sender_email}</p>
                  </td>
                  <td className="py-3"><DepartmentBadge department={c.department} /></td>
                  <td className="py-3"><UrgencyBadge urgency={c.urgency} /></td>
                  <td className="py-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-300">
                      {c.status}
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => setSelectedComplaint(c)}
                      className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-300 text-xs font-semibold transition-colors"
                    >
                      <span>Triage</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
              {criticalComplaints.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
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

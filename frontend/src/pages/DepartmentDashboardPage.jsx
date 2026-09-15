import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Building2, Users, AlertCircle, Clock, CheckCircle2, ShieldAlert,
  TrendingUp, Sparkles, RefreshCw, Lock, ArrowUpRight, ChevronRight,
  ShieldCheck, AlertTriangle, Layers, UserCheck
} from 'lucide-react';
import {
  BarChart, Bar, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend, PieChart, Pie
} from 'recharts';
import StatCard from '../components/StatCard';
import UrgencyBadge from '../components/UrgencyBadge';
import PriorityBadge from '../components/PriorityBadge';
import StatusBadge from '../components/StatusBadge';
import AIInsightsSection from '../components/AIInsightsSection';
import ComplaintDetailModal from '../components/ComplaintDetailModal';
import { CardSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import EmptyState from '../components/EmptyState';
import { getDepartmentDashboard, getDepartments } from '../api/departments';
import { getComplaints } from '../api/complaints';
import { getCurrentUser } from '../api/auth';
import { useAuth } from '../context/AuthContext';

const CATEGORY_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'];

export default function DepartmentDashboardPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const auth = useAuth();
  const user = auth?.user || getCurrentUser() || {};

  const [departments, setDepartments] = useState([]);
  const [selectedDeptId, setSelectedDeptId] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [deptComplaints, setDeptComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [permissionError, setPermissionError] = useState(null);
  const [selectedComplaint, setSelectedComplaint] = useState(null);

  const isAdmin = (user?.role || '').toUpperCase() === 'ADMIN';
  const isManager = (user?.role || '').toUpperCase() === 'MANAGER';

  // 1. Initial Load of Departments list
  useEffect(() => {
    loadDepartmentsList();
  }, [id, user?.id]);

  const loadDepartmentsList = async () => {
    try {
      const depts = await getDepartments();
      const validDepts = Array.isArray(depts) ? depts : depts?.departments || [];
      setDepartments(validDepts);

      // Determine default department ID
      let targetId = id ? parseInt(id, 10) : null;

      if (!targetId) {
        if (isManager && user?.department_id) {
          targetId = user.department_id;
        } else if (validDepts && validDepts.length > 0) {
          const finance = validDepts.find((d) => (d.name || '').toLowerCase().includes('finance'));
          targetId = finance ? finance.id : validDepts[0].id;
        }
      }

      if (targetId) {
        setSelectedDeptId(targetId);
        fetchDepartmentData(targetId);
      } else {
        setLoading(false);
      }
    } catch (err) {
      console.error('Failed to load departments list:', err);
      setLoading(false);
    }
  };

  // 2. Fetch specific department dashboard
  const fetchDepartmentData = async (deptId) => {
    setLoading(true);
    setPermissionError(null);
    try {
      const [dashRes, compRes] = await Promise.all([
        getDepartmentDashboard(deptId),
        getComplaints({ department_id: deptId, limit: 15 }).catch(() => [])
      ]);
      setDashboardData(dashRes);
      setDeptComplaints(Array.isArray(compRes) ? compRes : compRes?.items || []);
    } catch (err) {
      console.error('Department dashboard load error:', err);
      if (err.response?.status === 403) {
        setPermissionError(
          err.response?.data?.message ||
          err.response?.data?.detail ||
          'Managers can only access their assigned department dashboard unless granted ADMIN permissions.'
        );
      } else {
        setPermissionError('Unable to load department dashboard data. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDepartmentChange = (newId) => {
    const numId = parseInt(newId, 10);
    setSelectedDeptId(numId);
    navigate(`/departments/${numId}/dashboard`);
    fetchDepartmentData(numId);
  };

  const currentDept = dashboardData?.department || departments.find((d) => d.id === selectedDeptId);
  const metrics = dashboardData?.metrics || {};
  const agentWorkload = dashboardData?.agent_workload || [];
  const topCategories = dashboardData?.top_complaint_categories || [];
  const insights = dashboardData?.insights || [];

  return (
    <div className="space-y-8 animate-fade-in pb-16">
      {/* Top Header & Department Selector */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-black text-white tracking-tight">
              {currentDept?.name ? `${currentDept.name} Operations Hub` : 'Department Dedicated Dashboard'}
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-brand-500/10 text-brand-400 border border-brand-500/30">
              {currentDept?.code || 'DEPT'}
            </span>
            {isManager && !isAdmin && (
              <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-purple-500/10 text-purple-300 border border-purple-500/30">
                <Lock className="w-3 h-3" /> Manager Isolation
              </span>
            )}
            {isAdmin && (
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Admin Global Access
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Departmental telemetry, category surging, SLA risks, and agent capacity tracking.
          </p>
        </div>

        {/* Action Controls & Department Switcher */}
        <div className="flex items-center gap-3">
          {isAdmin || !isManager ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-semibold">Switch Department:</span>
              <select
                value={selectedDeptId || ''}
                onChange={(e) => handleDepartmentChange(e.target.value)}
                className="bg-slate-900 border border-slate-700 text-white rounded-xl px-3 py-2 text-xs font-semibold focus:outline-none focus:border-brand-500"
              >
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.code})
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 font-semibold flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5 text-brand-400" />
              <span>Assigned: {currentDept?.name || 'Your Department'}</span>
            </div>
          )}

          <button
            onClick={() => selectedDeptId && fetchDepartmentData(selectedDeptId)}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh Department Telemetry"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Loading Skeleton View */}
      {loading && (
        <div className="space-y-6">
          <CardSkeleton count={5} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CardSkeleton count={2} />
            <CardSkeleton count={2} />
          </div>
          <TableSkeleton rows={5} cols={7} />
        </div>
      )}

      {/* RBAC 403 Permission Banner if Manager is restricted */}
      {!loading && permissionError && (
        <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-500/40 text-rose-300 space-y-3">
          <div className="flex items-center gap-2 font-bold text-sm text-rose-200">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span>Department Manager Isolation Enforced (HTTP 403)</span>
          </div>
          <p className="text-xs text-rose-300 leading-relaxed">
            {permissionError}
          </p>
          {user?.department_id && (
            <button
              onClick={() => handleDepartmentChange(user.department_id)}
              className="px-4 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white shadow transition-all"
            >
              Return to My Assigned Department
            </button>
          )}
        </div>
      )}

      {/* Loaded Dashboard Content */}
      {!loading && !permissionError && (
        <>
          {/* Department-Specific AI Insights */}
          {insights.length > 0 && (
            <AIInsightsSection
              insights={insights}
              title={`${currentDept?.name || 'Department'} AI Intelligence & Risk Signals`}
            />
          )}

          {/* 5 Core Department Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {/* 1. Open Complaints */}
            <StatCard
              title="Open Complaints"
              value={metrics.open_complaints ?? 0}
              subtitle="Pending in department"
              icon={Clock}
              accentColor="amber"
            />

            {/* 2. Critical Complaints */}
            <StatCard
              title="Critical Complaints"
              value={metrics.critical_complaints ?? 0}
              subtitle="P1 / Urgent severity"
              icon={AlertCircle}
              accentColor="rose"
              isCritical={Boolean(metrics.critical_complaints && metrics.critical_complaints > 0)}
            />

            {/* 3. SLA Risks */}
            <StatCard
              title="SLA Risks"
              value={metrics.sla_risks ?? 0}
              subtitle="Past 75% SLA or breached"
              icon={ShieldAlert}
              accentColor="rose"
              isCritical={Boolean(metrics.sla_risks && metrics.sla_risks > 0)}
            />

            {/* 4. Resolved Complaints */}
            <StatCard
              title="Resolved"
              value={metrics.resolved_complaints ?? 0}
              subtitle={`Total closed tickets (${metrics.sla_compliance_rate ?? 100}% SLA)`}
              icon={CheckCircle2}
              accentColor="emerald"
            />

            {/* 5. Average Resolution Time */}
            <StatCard
              title="Avg Resolution"
              value={`${metrics.average_resolution_time_hours ?? 0}h`}
              subtitle="Hours from open to close"
              icon={TrendingUp}
              accentColor="blue"
            />
          </div>

          {/* Top Complaint Categories & Agent Workload Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Complaint Categories */}
            <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-brand-400" />
                    Top Complaint Categories
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Primary root cause categories (e.g. Billing, Payments, Refunds, Invoices)
                  </p>
                </div>
                <span className="text-xs font-mono font-bold text-slate-400">
                  {topCategories.reduce((acc, c) => acc + (c.count || 0), 0)} Total Tickets
                </span>
              </div>

              {topCategories.length > 0 ? (
                <div className="space-y-4 pt-2">
                  {topCategories.map((cat, idx) => (
                    <div key={cat.category || idx} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2 font-semibold text-white">
                          <span
                            className="w-2.5 h-2.5 rounded-full"
                            style={{ backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
                          />
                          <span>{cat.category || 'General'}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-slate-400">{cat.count} tickets</span>
                          <span className="font-mono font-bold text-brand-300 w-12 text-right">
                            {cat.percentage}%
                          </span>
                        </div>
                      </div>
                      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(100, Math.max(8, cat.percentage))}%`,
                            backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length]
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-slate-500">
                  No category records logged for this department yet.
                </div>
              )}
            </div>

            {/* Agent Workload Distribution */}
            <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Users className="w-4 h-4 text-emerald-400" />
                    Agent Workload & Team Capacity
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Active assigned ticket utilization across department agents
                  </p>
                </div>
                <span className="text-xs font-mono font-bold text-emerald-400">
                  {agentWorkload.length} Active Agents
                </span>
              </div>

              {agentWorkload.length > 0 ? (
                <div className="space-y-3 pt-2 max-h-80 overflow-y-auto pr-1">
                  {agentWorkload.map((agent) => {
                    const currentLoad = agent.current_workload ?? 0;
                    const maxLoad = agent.max_workload || 10;
                    const util = agent.utilization_rate || Math.round((currentLoad / Math.max(1, maxLoad)) * 100);
                    const isOverloaded = util >= 90;
                    return (
                      <div
                        key={agent.agent_id}
                        className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors"
                      >
                        <div className="flex items-center justify-between text-xs mb-2">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-300 font-bold flex items-center justify-center text-[11px] border border-emerald-500/20">
                              {(agent.agent_name || 'AG').slice(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <p className="font-bold text-white">{agent.agent_name || 'Agent'}</p>
                              <p className="text-[10px] text-slate-400">
                                Rating: {agent.performance_score || '4.8'}/5.0
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              isOverloaded
                                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                                : 'bg-slate-800 text-slate-300'
                            }`}>
                              {currentLoad} / {maxLoad} Active
                            </span>
                            <p className="text-[10px] font-mono text-slate-400 mt-0.5">{util}% Utilized</p>
                          </div>
                        </div>

                        {/* Utilization Bar */}
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              isOverloaded ? 'bg-rose-500' : util > 70 ? 'bg-amber-500' : 'bg-emerald-500'
                            }`}
                            style={{ width: `${Math.min(100, Math.max(5, util))}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-slate-500">
                  No active agents currently assigned to this department.
                </div>
              )}
            </div>
          </div>

          {/* Department Complaints Table Queue */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Clock className="w-4 h-4 text-brand-400" />
                  Recent {currentDept?.name || ''} Complaints
                </h3>
                <p className="text-[11px] text-slate-400">
                  Queue of tickets actively being handled by this department
                </p>
              </div>
              <button
                onClick={() => navigate('/complaints')}
                className="text-xs font-bold text-brand-400 hover:text-brand-300 flex items-center gap-1"
              >
                <span>Full Explorer</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="pb-3 font-semibold">Ticket</th>
                    <th className="pb-3 font-semibold">Subject & Customer</th>
                    <th className="pb-3 font-semibold">Category</th>
                    <th className="pb-3 font-semibold">Priority</th>
                    <th className="pb-3 font-semibold">Urgency</th>
                    <th className="pb-3 font-semibold">Status</th>
                    <th className="pb-3 font-semibold text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {deptComplaints.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-900/50 transition-colors">
                      <td className="py-3 font-mono font-bold text-slate-300">{c.ticket_number || c.complaint_number || `CMP-${c.id}`}</td>
                      <td className="py-3 max-w-sm">
                        <p className="font-medium text-white truncate">{c.subject || c.title || 'Support Ticket'}</p>
                        <p className="text-[11px] text-slate-400 truncate">{c.customer_name || c.customer_email || c.sender_email || 'Customer'}</p>
                      </td>
                      <td className="py-3 font-medium text-slate-300">{c.category || 'General'}</td>
                      <td className="py-3"><PriorityBadge priority={c.priority || 'P3'} /></td>
                      <td className="py-3"><UrgencyBadge urgency={c.urgency || 'Medium'} /></td>
                      <td className="py-3">
                        <StatusBadge status={c.status || 'OPEN'} />
                      </td>
                      <td className="py-3 text-right">
                        <button
                          onClick={() => setSelectedComplaint(c)}
                          className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-300 text-xs font-semibold transition-colors cursor-pointer"
                        >
                          <span>Triage</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {deptComplaints.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-500">
                        No active complaints currently routed to this department.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Complaint Detail Modal if triage clicked */}
      {selectedComplaint && (
        <ComplaintDetailModal
          complaint={selectedComplaint}
          onClose={() => setSelectedComplaint(null)}
          onUpdated={() => {
            if (selectedDeptId) fetchDepartmentData(selectedDeptId);
            setSelectedComplaint(null);
          }}
        />
      )}
    </div>
  );
}

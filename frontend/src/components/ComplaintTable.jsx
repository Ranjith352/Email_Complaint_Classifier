import React, { useState, useMemo } from 'react';
import {
  Search, Filter, ArrowUpDown, ChevronDown, ChevronUp, ChevronLeft,
  ChevronRight, Calendar, User, Clock, AlertTriangle, ShieldAlert,
  CheckCircle2, Sparkles, X, Eye, ArrowUpRight
} from 'lucide-react';
import PriorityBadge from './PriorityBadge';
import UrgencyBadge from './UrgencyBadge';
import DepartmentBadge from './DepartmentBadge';
import StatusBadge from './StatusBadge';
import { TableSkeleton } from './LoadingSkeleton';
import EmptyState from './EmptyState';

export default function ComplaintTable({
  complaints = [],
  loading = false,
  selectedComplaintId = null,
  onSelectComplaint,
  departments = [],
  teams = [],
  onRefresh
}) {
  // Search & Filter States
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedTeam, setSelectedTeam] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedPriority, setSelectedPriority] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedSentiment, setSelectedSentiment] = useState('');
  const [selectedUrgency, setSelectedUrgency] = useState('');
  const [selectedDateRange, setSelectedDateRange] = useState('ALL'); // ALL, TODAY, 7D, 30D

  // Sort State
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Extract unique categories from current complaints dataset
  const uniqueCategories = useMemo(() => {
    const cats = new Set();
    complaints.forEach((c) => {
      if (c.category) cats.add(c.category);
    });
    return Array.from(cats);
  }, [complaints]);

  // Handle Sort Toggle
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // Reset Filters
  const handleResetFilters = () => {
    setSearchTerm('');
    setSelectedDept('');
    setSelectedTeam('');
    setSelectedCategory('');
    setSelectedPriority('');
    setSelectedStatus('');
    setSelectedSentiment('');
    setSelectedUrgency('');
    setSelectedDateRange('ALL');
    setCurrentPage(1);
  };

  const hasActiveFilters = Boolean(
    searchTerm || selectedDept || selectedTeam || selectedCategory ||
    selectedPriority || selectedStatus || selectedSentiment || selectedUrgency || selectedDateRange !== 'ALL'
  );

  // Filtering Logic
  const filteredComplaints = useMemo(() => {
    const now = new Date();

    return complaints.filter((c) => {
      // Search term
      if (searchTerm) {
        const s = searchTerm.toLowerCase();
        const idMatch = (c.complaint_number || c.ticket_number || '').toLowerCase().includes(s);
        const subjMatch = (c.subject || '').toLowerCase().includes(s);
        const nameMatch = (c.customer_name || '').toLowerCase().includes(s);
        const emailMatch = (c.customer_email || '').toLowerCase().includes(s);
        const descMatch = (c.description || c.body || '').toLowerCase().includes(s);
        if (!idMatch && !subjMatch && !nameMatch && !emailMatch && !descMatch) return false;
      }

      // Department
      if (selectedDept) {
        const deptName = c.department_name || c.department?.name || c.department;
        if (String(c.department_id) !== String(selectedDept) && deptName !== selectedDept) {
          return false;
        }
      }

      // Team
      if (selectedTeam) {
        const teamName = c.team_name || c.team?.name || c.team;
        if (String(c.team_id) !== String(selectedTeam) && teamName !== selectedTeam) {
          return false;
        }
      }

      // Category
      if (selectedCategory && c.category !== selectedCategory) {
        return false;
      }

      // Priority
      if (selectedPriority && (c.priority || '').toUpperCase() !== selectedPriority.toUpperCase()) {
        return false;
      }

      // Status
      if (selectedStatus && (c.status || '').toUpperCase() !== selectedStatus.toUpperCase()) {
        return false;
      }

      // Sentiment
      if (selectedSentiment && (c.sentiment || '').toUpperCase() !== selectedSentiment.toUpperCase()) {
        return false;
      }

      // Urgency
      if (selectedUrgency && (c.urgency || '').toUpperCase() !== selectedUrgency.toUpperCase()) {
        return false;
      }

      // Date Range Filter
      if (selectedDateRange !== 'ALL' && c.created_at) {
        const created = new Date(c.created_at);
        const diffMs = now - created;
        const diffDays = diffMs / (1000 * 60 * 60 * 24);

        if (selectedDateRange === 'TODAY' && diffDays > 1) return false;
        if (selectedDateRange === '7D' && diffDays > 7) return false;
        if (selectedDateRange === '30D' && diffDays > 30) return false;
      }

      return true;
    });
  }, [
    complaints, searchTerm, selectedDept, selectedTeam, selectedCategory,
    selectedPriority, selectedStatus, selectedSentiment, selectedUrgency, selectedDateRange
  ]);

  // Sorting Logic
  const sortedComplaints = useMemo(() => {
    return [...filteredComplaints].sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      // Handle custom accessors
      if (sortField === 'customer') {
        aVal = a.customer_name || a.customer_email || '';
        bVal = b.customer_name || b.customer_email || '';
      } else if (sortField === 'department') {
        aVal = a.department_name || a.department?.name || '';
        bVal = b.department_name || b.department?.name || '';
      } else if (sortField === 'sla') {
        aVal = a.sla_deadline ? new Date(a.sla_deadline).getTime() : 0;
        bVal = b.sla_deadline ? new Date(b.sla_deadline).getTime() : 0;
      } else if (sortField === 'created_at') {
        aVal = a.created_at ? new Date(a.created_at).getTime() : 0;
        bVal = b.created_at ? new Date(b.created_at).getTime() : 0;
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredComplaints, sortField, sortDirection]);

  // Pagination Slice
  const totalItems = sortedComplaints.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const paginatedComplaints = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedComplaints.slice(start, start + pageSize);
  }, [sortedComplaints, currentPage, pageSize]);

  const renderSortIndicator = (field) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 text-slate-600 opacity-60 group-hover:opacity-100" />;
    }
    return sortDirection === 'asc' ? (
      <ChevronUp className="w-3.5 h-3.5 text-brand-400 font-bold" />
    ) : (
      <ChevronDown className="w-3.5 h-3.5 text-brand-400 font-bold" />
    );
  };

  const getSentimentStyle = (sentiment) => {
    const s = (sentiment || '').toUpperCase();
    if (s === 'POSITIVE') {
      return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
    }
    if (s === 'NEGATIVE') {
      return 'bg-rose-500/10 text-rose-300 border-rose-500/30';
    }
    return 'bg-slate-800/80 text-slate-300 border-slate-700';
  };

  const getStatusStyle = (status) => {
    const st = (status || '').toUpperCase();
    switch (st) {
      case 'NEW':
        return 'bg-blue-500/10 text-blue-300 border-blue-500/30';
      case 'ASSIGNED':
        return 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30';
      case 'IN_PROGRESS':
        return 'bg-amber-500/10 text-amber-300 border-amber-500/30';
      case 'WAITING_FOR_CUSTOMER':
        return 'bg-purple-500/10 text-purple-300 border-purple-500/30';
      case 'ESCALATED':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/50 font-bold animate-pulse';
      case 'RESOLVED':
        return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
      case 'CLOSED':
        return 'bg-slate-800 text-slate-400 border-slate-700';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const renderSLAMiniBadge = (complaint) => {
    const metrics = complaint.sla_metrics;
    if (!metrics) {
      return <span className="text-[11px] text-slate-500 font-mono">--</span>;
    }

    if (metrics.is_breached) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
          <ShieldAlert className="w-3 h-3 text-rose-400" />
          <span>BREACHED</span>
        </span>
      );
    }

    if (metrics.warning_level === 'CRITICAL_WARNING') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30">
          <AlertTriangle className="w-3 h-3 text-rose-400" />
          <span>{metrics.time_remaining || 'Critical'}</span>
        </span>
      );
    }

    if (metrics.warning_level === 'WARNING') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
          <Clock className="w-3 h-3 text-amber-400" />
          <span>{metrics.time_remaining || 'At Risk'}</span>
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-mono">
        <Clock className="w-3 h-3 text-emerald-400" />
        <span>{metrics.time_remaining || 'On Track'}</span>
      </span>
    );
  };

  return (
    <div className="space-y-4">
      {/* 8 Filters & Search Bar Toolbar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800/80 space-y-3.5 shadow-xl">
        {/* Search Bar Row */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search complaints by ID, subject, customer, keyword, or description..."
              className="w-full bg-slate-950/80 border border-slate-800 focus:border-brand-500 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-brand-500/30 transition-all"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {hasActiveFilters && (
            <button
              onClick={handleResetFilters}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-slate-900 text-slate-300 border border-slate-800 hover:text-white transition-colors"
            >
              <X className="w-3.5 h-3.5 text-rose-400" />
              <span>Clear Filters</span>
            </button>
          )}
        </div>

        {/* 8 Filters Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 text-xs">
          {/* 1. Department Filter */}
          <div>
            <label className="text-[10px] text-slate-400 font-semibold block mb-1">Department</label>
            <select
              value={selectedDept}
              onChange={(e) => {
                setSelectedDept(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Depts</option>
              {departments.map((d) => (
                <option key={d.id} value={d.name}>{d.name}</option>
              ))}
            </select>
          </div>

          {/* 2. Team Filter */}
          <div>
            <label className="text-[10px] text-slate-400 font-semibold block mb-1">Team</label>
            <select
              value={selectedTeam}
              onChange={(e) => {
                setSelectedTeam(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Teams</option>
              {teams.map((t) => (
                <option key={t.id} value={t.name}>{t.name}</option>
              ))}
            </select>
          </div>

          {/* 3. Category Filter */}
          <div>
            <label className="text-[10px] text-slate-400 font-semibold block mb-1">Category</label>
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Categories</option>
              {uniqueCategories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* 4. Priority Filter */}
          <div>
            <label className="text-[10px] text-slate-400 font-semibold block mb-1">Priority</label>
            <select
              value={selectedPriority}
              onChange={(e) => {
                setSelectedPriority(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Priorities</option>
              <option value="P1">P1 (Critical)</option>
              <option value="P2">P2 (High)</option>
              <option value="P3">P3 (Medium)</option>
              <option value="P4">P4 (Low)</option>
            </select>
          </div>

          {/* 5. Status Filter */}
          <div>
            <label className="text-[10px] text-slate-400 font-semibold block mb-1">Status</label>
            <select
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Statuses</option>
              <option value="NEW">New</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="WAITING_FOR_CUSTOMER">Waiting Customer</option>
              <option value="ESCALATED">Escalated</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>

          {/* 6. Sentiment Filter */}
          <div>
            <label className="text-[10px] text-slate-400 font-semibold block mb-1">Sentiment</label>
            <select
              value={selectedSentiment}
              onChange={(e) => {
                setSelectedSentiment(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Sentiments</option>
              <option value="POSITIVE">Positive</option>
              <option value="NEUTRAL">Neutral</option>
              <option value="NEGATIVE">Negative</option>
            </select>
          </div>

          {/* 7. Urgency Filter */}
          <div>
            <label className="text-[10px] text-slate-400 font-semibold block mb-1">Urgency</label>
            <select
              value={selectedUrgency}
              onChange={(e) => {
                setSelectedUrgency(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Urgencies</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          {/* 8. Date Range Filter */}
          <div>
            <label className="text-[10px] text-slate-400 font-semibold block mb-1">Date</label>
            <select
              value={selectedDateRange}
              onChange={(e) => {
                setSelectedDateRange(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="ALL">All Time</option>
              <option value="TODAY">Today</option>
              <option value="7D">Last 7 Days</option>
              <option value="30D">Last 30 Days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Professional Complaint Table */}
      <div className="glass-panel rounded-2xl border border-slate-800/80 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 select-none">
                {/* 1. Complaint ID */}
                <th
                  onClick={() => handleSort('complaint_number')}
                  className="py-3 px-3.5 font-bold cursor-pointer group hover:text-white"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Complaint ID</span>
                    {renderSortIndicator('complaint_number')}
                  </div>
                </th>

                {/* 2. Subject */}
                <th
                  onClick={() => handleSort('subject')}
                  className="py-3 px-3.5 font-bold cursor-pointer group hover:text-white min-w-[200px]"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Subject</span>
                    {renderSortIndicator('subject')}
                  </div>
                </th>

                {/* 3. Customer */}
                <th
                  onClick={() => handleSort('customer')}
                  className="py-3 px-3.5 font-bold cursor-pointer group hover:text-white min-w-[140px]"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Customer</span>
                    {renderSortIndicator('customer')}
                  </div>
                </th>

                {/* 4. Department */}
                <th
                  onClick={() => handleSort('department')}
                  className="py-3 px-3.5 font-bold cursor-pointer group hover:text-white"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Department</span>
                    {renderSortIndicator('department')}
                  </div>
                </th>

                {/* 5. Team */}
                <th className="py-3 px-3.5 font-bold">Team</th>

                {/* 6. Category */}
                <th
                  onClick={() => handleSort('category')}
                  className="py-3 px-3.5 font-bold cursor-pointer group hover:text-white"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Category</span>
                    {renderSortIndicator('category')}
                  </div>
                </th>

                {/* 7. Priority */}
                <th
                  onClick={() => handleSort('priority')}
                  className="py-3 px-3.5 font-bold cursor-pointer group hover:text-white"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Priority</span>
                    {renderSortIndicator('priority')}
                  </div>
                </th>

                {/* 8. Sentiment */}
                <th className="py-3 px-3.5 font-bold">Sentiment</th>

                {/* 9. Status */}
                <th
                  onClick={() => handleSort('status')}
                  className="py-3 px-3.5 font-bold cursor-pointer group hover:text-white"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Status</span>
                    {renderSortIndicator('status')}
                  </div>
                </th>

                {/* 10. Assigned Agent */}
                <th className="py-3 px-3.5 font-bold">Assigned Agent</th>

                {/* 11. SLA */}
                <th
                  onClick={() => handleSort('sla')}
                  className="py-3 px-3.5 font-bold cursor-pointer group hover:text-white"
                >
                  <div className="flex items-center gap-1.5">
                    <span>SLA</span>
                    {renderSortIndicator('sla')}
                  </div>
                </th>

                {/* 12. Created At */}
                <th
                  onClick={() => handleSort('created_at')}
                  className="py-3 px-3.5 font-bold cursor-pointer group hover:text-white min-w-[110px]"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Created At</span>
                    {renderSortIndicator('created_at')}
                  </div>
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-800/60">
              {paginatedComplaints.map((c) => {
                const isSelected = selectedComplaintId === c.id;
                const deptName = c.department_name || c.department?.name || c.category || 'General';
                const teamName = c.team_name || c.team?.name || 'Triage';
                const agentName = c.assigned_agent_name || c.assigned_agent?.name || 'Unassigned';

                return (
                  <tr
                    key={c.id}
                    onClick={() => onSelectComplaint && onSelectComplaint(c)}
                    className={`cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-brand-950/40 border-l-4 border-l-brand-500 shadow-inner'
                        : 'hover:bg-slate-900/60'
                    }`}
                  >
                    {/* 1. Complaint ID */}
                    <td className="py-3 px-3.5 font-mono font-bold text-white whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                        {c.complaint_number || c.ticket_number || `CMP-${c.id}`}
                      </span>
                    </td>

                    {/* 2. Subject */}
                    <td className="py-3 px-3.5 max-w-xs">
                      <p className="font-semibold text-white truncate">{c.subject || 'Complaint'}</p>
                      <p className="text-[11px] text-slate-400 truncate mt-0.5">
                        {c.description || c.body || 'No description provided.'}
                      </p>
                    </td>

                    {/* 3. Customer */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <p className="font-medium text-slate-200 truncate">{c.customer_name || 'Customer'}</p>
                      <p className="text-[11px] text-slate-500 font-mono truncate">{c.customer_email}</p>
                    </td>

                    {/* 4. Department */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <DepartmentBadge department={deptName} />
                    </td>

                    {/* 5. Team */}
                    <td className="py-3 px-3.5 whitespace-nowrap text-slate-300 font-medium">
                      <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 text-[11px]">
                        {teamName}
                      </span>
                    </td>

                    {/* 6. Category */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <span className="text-[11px] text-slate-300 font-medium truncate block max-w-[120px]">
                        {c.category || 'General'}
                      </span>
                    </td>

                    {/* 7. Priority */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <PriorityBadge priority={c.priority || c.priority_level || 'P3'} />
                    </td>

                    {/* 8. Sentiment */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getSentimentStyle(c.sentiment)}`}>
                        {c.sentiment || 'Neutral'}
                      </span>
                    </td>

                    {/* 9. Status */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <StatusBadge status={c.status} />
                    </td>

                    {/* 10. Assigned Agent */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <div className="w-5 h-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-[10px] font-bold">
                          {agentName.charAt(0)}
                        </div>
                        <span className={`text-[11px] truncate max-w-[100px] ${agentName === 'Unassigned' ? 'text-slate-500 italic' : 'text-slate-200'}`}>
                          {agentName}
                        </span>
                      </div>
                    </td>

                    {/* 11. SLA */}
                    <td className="py-3 px-3.5 whitespace-nowrap">
                      {renderSLAMiniBadge(c)}
                    </td>

                    {/* 12. Created At */}
                    <td className="py-3 px-3.5 whitespace-nowrap text-[11px] font-mono text-slate-400">
                      {c.created_at ? new Date(c.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '--'}
                    </td>
                  </tr>
                );
              })}

              {loading ? (
                <tr>
                  <td colSpan={12} className="p-6">
                    <TableSkeleton rows={pageSize || 8} cols={12} />
                  </td>
                </tr>
              ) : paginatedComplaints.length === 0 ? (
                <tr>
                  <td colSpan={12} className="p-8">
                    <EmptyState
                      title="No complaints matched your filter"
                      description="Try adjusting your search terms, selecting different departments, or resetting filters."
                      actionLabel={hasActiveFilters ? "Reset All Filters" : undefined}
                      onAction={hasActiveFilters ? handleResetFilters : undefined}
                    />
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 bg-slate-950/60 border-t border-slate-800/80 flex items-center justify-between flex-wrap gap-3 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:outline-none"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
            </select>
            <span className="text-slate-500">
              Showing {Math.min(totalItems, (currentPage - 1) * pageSize + 1)} - {Math.min(totalItems, currentPage * pageSize)} of {totalItems}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 disabled:opacity-40 hover:text-white"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-mono text-slate-300">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 disabled:opacity-40 hover:text-white"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

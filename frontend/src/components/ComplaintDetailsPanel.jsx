import React, { useState, useEffect } from 'react';
import {
  User, Mail, FileText, Sparkles, Clock, AlertTriangle, ShieldAlert,
  CheckCircle2, ArrowRight, Copy, Check, RotateCcw, Edit3, Send,
  ThumbsUp, ExternalLink, RefreshCw, X, ShieldCheck, ChevronRight,
  Layers, Users, Tag, AlertCircle, Bookmark, CheckSquare
} from 'lucide-react';
import PriorityBadge from './PriorityBadge';
import UrgencyBadge from './UrgencyBadge';
import DepartmentBadge from './DepartmentBadge';
import SLATrackerCard from './SLATrackerCard';
import {
  changePriority, changeDepartment, changeTeam, changeAgent,
  changeStatus, reassignComplaint, escalateComplaint, resolveComplaint,
  reopenComplaint, generateCustomerResponse, editCustomerResponse,
  approveCustomerResponse, sendCustomerResponse, getComplaint,
  getSimilarComplaints, mergeComplaint, ignoreDuplicateWarning,
  refreshComplaintRecommendations
} from '../api/complaints';
import { useConfirm } from '../context/ConfirmContext';
import { useToast } from '../context/ToastContext';

export default function ComplaintDetailsPanel({
  complaintId,
  initialComplaint = null,
  onClose,
  onUpdated,
  departments = [],
  teams = [],
  agents = []
}) {
  const confirm = useConfirm();
  const toast = useToast();
  const [data, setData] = useState(initialComplaint);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // overview | response | timeline | similar

  // Action Modals State
  const [activeModal, setActiveModal] = useState(null); // 'assign' | 'priority' | 'department' | 'team' | 'agent' | 'status' | 'escalate' | 'resolve' | 'reopen'
  const [modalLoading, setModalLoading] = useState(false);
  const [modalFeedback, setModalFeedback] = useState('');

  // Form states for modals
  const [targetDeptId, setTargetDeptId] = useState('');
  const [targetTeamId, setTargetTeamId] = useState('');
  const [targetAgentId, setTargetAgentId] = useState('');
  const [targetPriority, setTargetPriority] = useState('P2');
  const [targetUrgency, setTargetUrgency] = useState('High');
  const [targetStatus, setTargetStatus] = useState('IN_PROGRESS');
  const [actionReason, setActionReason] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [saveKnowledge, setSaveKnowledge] = useState(true);

  // Response Studio States
  const [draftResponse, setDraftResponse] = useState(null);
  const [isEditingDraft, setIsEditingDraft] = useState(false);
  const [editedDraftText, setEditedDraftText] = useState('');
  const [generatingResponse, setGeneratingResponse] = useState(false);
  const [savingEdit, setSavingEdit] = useState(false);
  const [approving, setApproving] = useState(false);
  const [sending, setSending] = useState(false);
  const [responseFeedback, setResponseFeedback] = useState('');
  const [copiedDraft, setCopiedDraft] = useState(false);

  // Similar Complaints & Duplicate Detection
  const [similarCases, setSimilarCases] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);

  useEffect(() => {
    if (complaintId) {
      loadComplaintData();
    }
  }, [complaintId]);

  const loadComplaintData = async () => {
    setLoading(true);
    try {
      const res = await getComplaint(complaintId);
      setData(res);
      // Find active response draft
      const draft = res.ai_responses?.find((r) => r.response_type === 'DRAFT_REPLY');
      if (draft) {
        setDraftResponse(draft);
        if (!isEditingDraft) {
          setEditedDraftText(draft.content || '');
        }
      }
      // Load similar cases
      loadSimilarCases(res.id || complaintId);
    } catch (err) {
      console.error('Failed to load complaint details:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSimilarCases = async (cid) => {
    setLoadingSimilar(true);
    try {
      const res = await getSimilarComplaints(cid);
      setSimilarCases(res.semantic_matches || res.similar_complaints || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSimilar(false);
    }
  };

  const comp = data?.complaint || data || {};
  const currentDept = data?.department || comp.department;
  const currentTeam = data?.team || comp.team;
  const currentAgent = data?.assigned_agent || comp.assigned_agent;
  const timeline = data?.events || comp.events || [];
  const entities = data?.entities || comp.entities || [];
  const recommendations = data?.ai_responses?.find((r) => r.response_type === 'RECOMMENDATION');

  // --- ACTION HANDLERS (All 14 Operations) ---

  // 1 & 2. Assign / Reassign
  const handleAssignSubmit = async () => {
    setModalLoading(true);
    try {
      await reassignComplaint(complaintId, {
        department_id: targetDeptId ? parseInt(targetDeptId) : null,
        team_id: targetTeamId ? parseInt(targetTeamId) : null,
        agent_id: targetAgentId ? parseInt(targetAgentId) : null,
        reason: actionReason || 'Manual assignment from details console'
      });
      setActiveModal(null);
      await loadComplaintData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert('Assignment failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setModalLoading(false);
    }
  };

  // 3. Change Department
  const handleChangeDeptSubmit = async () => {
    if (!targetDeptId) return;
    setModalLoading(true);
    try {
      await changeDepartment(complaintId, parseInt(targetDeptId), actionReason);
      setActiveModal(null);
      await loadComplaintData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert('Department update failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setModalLoading(false);
    }
  };

  // 4. Change Team
  const handleChangeTeamSubmit = async () => {
    if (!targetTeamId) return;
    setModalLoading(true);
    try {
      await changeTeam(complaintId, parseInt(targetTeamId), actionReason);
      setActiveModal(null);
      await loadComplaintData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert('Team update failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setModalLoading(false);
    }
  };

  // 5. Change Agent
  const handleChangeAgentSubmit = async () => {
    if (!targetAgentId) return;
    setModalLoading(true);
    try {
      await changeAgent(complaintId, parseInt(targetAgentId), actionReason);
      setActiveModal(null);
      await loadComplaintData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert('Agent assignment failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setModalLoading(false);
    }
  };

  // 6. Change Priority
  const handleChangePrioritySubmit = async () => {
    setModalLoading(true);
    try {
      await changePriority(complaintId, targetPriority, targetUrgency, actionReason);
      setActiveModal(null);
      await loadComplaintData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert('Priority update failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setModalLoading(false);
    }
  };

  // 7. Escalate
  const handleEscalateSubmit = async () => {
    setModalLoading(true);
    try {
      await escalateComplaint(complaintId, actionReason || 'Escalated to management');
      setActiveModal(null);
      await loadComplaintData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert('Escalation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setModalLoading(false);
    }
  };

  // 8. Change Status
  const handleChangeStatusSubmit = async () => {
    setModalLoading(true);
    try {
      await changeStatus(complaintId, targetStatus, actionReason);
      setActiveModal(null);
      await loadComplaintData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert('Status transition failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setModalLoading(false);
    }
  };

  // 9. Generate AI Response
  const handleGenerateAIResponse = async () => {
    setGeneratingResponse(true);
    setResponseFeedback('');
    try {
      await generateCustomerResponse(complaintId);
      await loadComplaintData();
      setResponseFeedback('AI response draft successfully generated.');
      setTimeout(() => setResponseFeedback(''), 4000);
    } catch (err) {
      alert('Generation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGeneratingResponse(false);
    }
  };

  // 10. Edit Response
  const handleSaveResponseEdit = async () => {
    if (!editedDraftText.trim()) return;
    setSavingEdit(true);
    try {
      await editCustomerResponse(complaintId, draftResponse?.id, editedDraftText);
      await loadComplaintData();
      setIsEditingDraft(false);
      setResponseFeedback('Response edited. Approval was reset and requires explicit human sign-off.');
      setTimeout(() => setResponseFeedback(''), 4000);
    } catch (err) {
      alert('Save edit failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSavingEdit(false);
    }
  };

  // 11. Approve Response
  const handleApproveResponse = async () => {
    setApproving(true);
    try {
      await approveCustomerResponse(complaintId, draftResponse?.id, 'Support Lead');
      await loadComplaintData();
      setResponseFeedback('Response approved! You can now send it to the customer.');
      setTimeout(() => setResponseFeedback(''), 4000);
    } catch (err) {
      alert('Approval failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setApproving(false);
    }
  };

  // 12. Send Response
  const handleSendResponse = async () => {
    if (!draftResponse?.is_approved) {
      toast.warning('Cannot send response without explicit human approval. Please click Approve first.');
      return;
    }
    const customer = comp.customer_email || 'the customer';
    const confirmed = await confirm({
      title: 'Dispatch Email Response',
      message: `Are you sure you want to dispatch this approved response to ${customer}?`,
      confirmText: 'Dispatch Email',
      variant: 'info',
    });
    if (!confirmed) {
      return;
    }
    setSending(true);
    try {
      await sendCustomerResponse(complaintId, draftResponse?.id, 'Support Agent');
      await loadComplaintData();
      toast.success(`Response successfully sent to ${customer}!`);
      setResponseFeedback(`Response successfully sent to ${customer}!`);
      setTimeout(() => setResponseFeedback(''), 5000);
    } catch (err) {
      toast.error('Send failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSending(false);
    }
  };

  // 13. Mark Resolved
  const handleResolveSubmit = async () => {
    if (!resolutionNotes.trim()) {
      alert('Please enter resolution notes before resolving.');
      return;
    }
    setModalLoading(true);
    try {
      await resolveComplaint(complaintId, resolutionNotes, saveKnowledge);
      setActiveModal(null);
      await loadComplaintData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert('Resolution failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setModalLoading(false);
    }
  };

  // 14. Reopen
  const handleReopenSubmit = async () => {
    setModalLoading(true);
    try {
      await reopenComplaint(complaintId, actionReason || 'Customer reported recurring issue');
      setActiveModal(null);
      await loadComplaintData();
      if (onUpdated) onUpdated();
    } catch (err) {
      alert('Reopen failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setModalLoading(false);
    }
  };

  return (
    <div className="glass-panel rounded-2xl border border-brand-500/30 overflow-hidden shadow-2xl animate-fade-in space-y-0">
      {/* Header Bar */}
      <div className="p-5 bg-gradient-to-r from-slate-900 via-slate-900/90 to-brand-950/40 border-b border-slate-800/80 flex items-center justify-between flex-wrap gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="font-mono text-xs px-2.5 py-1 rounded bg-brand-500/20 text-brand-300 font-bold border border-brand-500/30">
              {comp.complaint_number || comp.ticket_number || `CMP-${comp.id}`}
            </span>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
              comp.status === 'RESOLVED' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' :
              comp.status === 'ESCALATED' ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse' :
              'bg-blue-500/10 text-blue-300 border-blue-500/30'
            }`}>
              {comp.status || 'NEW'}
            </span>
            <PriorityBadge priority={comp.priority || 'P3'} />
            <UrgencyBadge urgency={comp.urgency || 'Medium'} />
          </div>
          <h2 className="text-lg font-black text-white tracking-tight mt-1">
            {comp.subject || 'Complaint Details'}
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadComplaintData}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
            title="Reload Telemetry"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
              title="Close Details View"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* 14 ACTIONS TOOLBAR */}
      <div className="p-3.5 bg-slate-950/80 border-b border-slate-800/80 flex items-center gap-2 overflow-x-auto text-xs no-scrollbar">
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mr-1 shrink-0">
          Actions:
        </span>

        {/* 1 & 2. Assign / Reassign */}
        <button
          onClick={() => setActiveModal('assign')}
          className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-850 text-slate-200 border border-slate-700/80 font-semibold shrink-0 transition-colors"
        >
          Assign / Reassign
        </button>

        {/* 3. Change Department */}
        <button
          onClick={() => setActiveModal('department')}
          className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-850 text-slate-200 border border-slate-700/80 font-semibold shrink-0 transition-colors"
        >
          Change Dept
        </button>

        {/* 4. Change Team */}
        <button
          onClick={() => setActiveModal('team')}
          className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-850 text-slate-200 border border-slate-700/80 font-semibold shrink-0 transition-colors"
        >
          Change Team
        </button>

        {/* 5. Change Agent */}
        <button
          onClick={() => setActiveModal('agent')}
          className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-850 text-slate-200 border border-slate-700/80 font-semibold shrink-0 transition-colors"
        >
          Change Agent
        </button>

        {/* 6. Change Priority */}
        <button
          onClick={() => setActiveModal('priority')}
          className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-850 text-slate-200 border border-slate-700/80 font-semibold shrink-0 transition-colors"
        >
          Change Priority
        </button>

        {/* 7. Escalate */}
        <button
          onClick={() => setActiveModal('escalate')}
          className="px-3 py-1.5 rounded-xl bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border border-rose-500/40 font-bold shrink-0 transition-colors"
        >
          Escalate
        </button>

        {/* 8. Change Status */}
        <button
          onClick={() => setActiveModal('status')}
          className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-850 text-slate-200 border border-slate-700/80 font-semibold shrink-0 transition-colors"
        >
          Change Status
        </button>

        <div className="h-4 w-px bg-slate-800 mx-1 shrink-0" />

        {/* 9-12. Response Studio Quick Trigger */}
        <button
          onClick={() => {
            setActiveTab('response');
            if (!draftResponse) handleGenerateAIResponse();
          }}
          className="px-3 py-1.5 rounded-xl bg-purple-900/40 hover:bg-purple-800/50 text-purple-300 border border-purple-500/40 font-bold flex items-center gap-1.5 shrink-0 transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>AI Response Studio</span>
        </button>

        {/* 13. Mark Resolved */}
        {comp.status !== 'RESOLVED' && comp.status !== 'CLOSED' && (
          <button
            onClick={() => setActiveModal('resolve')}
            className="px-3 py-1.5 rounded-xl bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-300 border border-emerald-500/40 font-bold shrink-0 transition-colors"
          >
            Mark Resolved
          </button>
        )}

        {/* 14. Reopen */}
        {(comp.status === 'RESOLVED' || comp.status === 'CLOSED') && (
          <button
            onClick={() => setActiveModal('reopen')}
            className="px-3 py-1.5 rounded-xl bg-amber-950/40 hover:bg-amber-900/50 text-amber-300 border border-amber-500/40 font-bold shrink-0 transition-colors"
          >
            Reopen Ticket
          </button>
        )}
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-800/80 px-5 bg-slate-900/40 text-xs">
        {[
          { id: 'overview', label: '20-Point Overview' },
          { id: 'response', label: 'Customer Response Studio' },
          { id: 'timeline', label: `Lifecycle Timeline (${timeline.length})` },
          { id: 'similar', label: `Similar Cases (${similarCases.length})` }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`py-3 px-4 font-bold border-b-2 transition-all ${
              activeTab === tab.id
                ? 'border-brand-500 text-brand-300 bg-brand-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: 20-Point Comprehensive Details Display */}
      {activeTab === 'overview' && (
        <div className="p-6 space-y-6">
          {/* Top Row: Customer Info & SLA Timer */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 1. Customer Information */}
            <div className="glass-panel p-5 rounded-xl border border-slate-800/80 space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-slate-800/80 text-xs font-bold text-white uppercase tracking-wider">
                <User className="w-4 h-4 text-brand-400" />
                <span>1. Customer Information</span>
              </div>
              <div className="space-y-2 text-xs">
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Name</span>
                  <span className="font-semibold text-white text-sm">{comp.customer_name || 'Customer'}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Email</span>
                  <span className="font-mono text-slate-300">{comp.customer_email}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase">Source Channel</span>
                  <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 font-mono text-[11px] text-brand-300">
                    {comp.source || 'WEB'}
                  </span>
                </div>
              </div>
            </div>

            {/* 18. SLA Timer Card */}
            <div className="lg:col-span-2">
              <SLATrackerCard
                complaint={comp}
                onEscalated={loadComplaintData}
              />
            </div>
          </div>

          {/* 2. Original Complaint */}
          <div className="glass-panel p-5 rounded-xl border border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
              <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider">
                <FileText className="w-4 h-4 text-brand-400" />
                <span>2. Original Complaint</span>
              </div>
              <span className="text-[11px] text-slate-500 font-mono">
                Filed: {comp.created_at ? new Date(comp.created_at).toLocaleString() : '--'}
              </span>
            </div>
            <div className="space-y-2">
              <h4 className="text-sm font-bold text-white">{comp.subject}</h4>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap bg-slate-950/80 p-4 rounded-xl border border-slate-800">
                {comp.description || comp.body || 'No description body available.'}
              </p>
              {comp.attachment_name && (
                <div className="flex items-center gap-2 text-xs text-brand-400 pt-1">
                  <Bookmark className="w-3.5 h-3.5" />
                  <span>Attachment: {comp.attachment_name}</span>
                </div>
              )}
            </div>
          </div>

          {/* 3. AI Summary */}
          <div className="glass-panel p-5 rounded-xl border border-purple-500/30 bg-purple-950/10 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-purple-300 uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>3. AI Summary</span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed italic bg-purple-950/20 p-3 rounded-xl border border-purple-500/20">
              "{comp.summary || 'Summary generated by NLP engine: Customer experienced issue during transaction.'}"
            </p>
          </div>

          {/* 4 - 14. Classification & Telemetry Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4 text-xs">
            {/* 4. Category */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">4. Category</span>
              <span className="font-semibold text-white">{comp.category || 'General'}</span>
            </div>

            {/* 5. Subcategory */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">5. Subcategory</span>
              <span className="font-semibold text-slate-300">{comp.sub_category || 'General Inquiry'}</span>
            </div>

            {/* 6. Department */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">6. Department</span>
              <DepartmentBadge department={currentDept?.name || comp.department_name || comp.category} />
            </div>

            {/* 7. Team */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">7. Team</span>
              <span className="font-semibold text-slate-300">{currentTeam?.name || comp.team_name || 'Triage'}</span>
            </div>

            {/* 8. Assigned Agent */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">8. Assigned Agent</span>
              <span className="font-semibold text-white">{currentAgent?.name || comp.assigned_agent_name || 'Unassigned'}</span>
            </div>

            {/* 9. Sentiment */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">9. Sentiment</span>
              <span className="font-bold text-slate-200">{comp.sentiment || 'Neutral'}</span>
            </div>

            {/* 10. Emotion */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">10. Emotion</span>
              <span className="font-bold text-amber-400">{comp.emotion || 'Neutral'}</span>
            </div>

            {/* 11. Urgency */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">11. Urgency</span>
              <UrgencyBadge urgency={comp.urgency || 'Medium'} />
            </div>

            {/* 12. Priority */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">12. Priority</span>
              <PriorityBadge priority={comp.priority || 'P3'} />
            </div>

            {/* 13. Priority Score */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">13. Priority Score</span>
              <span className="font-mono font-bold text-brand-400 text-sm">{comp.priority_score || 50} / 100</span>
            </div>

            {/* 14. AI Confidence */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">14. AI Confidence</span>
              <span className="font-mono font-bold text-emerald-400 text-sm">
                {Math.round((comp.ai_confidence || 0.90) * 100)}%
              </span>
            </div>

            {/* 17. Possible Duplicate */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">17. Duplicate Status</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                comp.is_duplicate ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'bg-slate-800 text-slate-400'
              }`}>
                {comp.duplicate_status || (comp.is_duplicate ? 'POSSIBLE' : 'NONE')}
              </span>
            </div>
          </div>

          {/* 15. Extracted Entities */}
          <div className="glass-panel p-5 rounded-xl border border-slate-800/80 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider">
              <Tag className="w-4 h-4 text-brand-400" />
              <span>15. Extracted Entities ({entities.length})</span>
            </div>
            <div className="flex items-center gap-2 flex-wrap text-xs">
              {entities.map((e, idx) => (
                <div key={idx} className="px-3 py-1 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase font-mono">{e.entity_type}</span>
                  <span className="font-semibold text-white font-mono">{e.entity_value}</span>
                </div>
              ))}
              {entities.length === 0 && (
                <span className="text-slate-500 text-xs italic">No specific named entities extracted.</span>
              )}
            </div>
          </div>

          {/* 20. AI Recommended Resolution Checklist */}
          <div className="glass-panel p-5 rounded-xl border border-cyan-500/30 bg-cyan-950/10 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20">
              <div className="flex items-center gap-2 text-xs font-bold text-cyan-300 uppercase tracking-wider">
                <CheckSquare className="w-4 h-4 text-cyan-400" />
                <span>20. AI Recommended Resolution</span>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                AI GENERATED RECOMMENDATION
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/80 border border-cyan-500/20 text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
              {recommendations?.content || "1. Verify customer account details.\n2. Cross-reference transaction timestamp.\n3. Check payment gateway confirmation.\n4. If error verified, initiate resolution.\n5. Dispatch customer notification."}
            </div>
            <p className="text-[11px] text-slate-400 italic">
              Note: The support agent remains responsible for the final decision and verification before executing.
            </p>
          </div>
        </div>
      )}

      {/* Tab 2: Customer Response Studio (Generate, Edit, Approve, Send) */}
      {activeTab === 'response' && (
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-white">21. Customer Response Studio</h3>
              <p className="text-xs text-slate-400">
                Generate professional responses, edit drafts, explicitly approve, and dispatch with strict human-in-the-loop governance.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleGenerateAIResponse}
                disabled={generatingResponse}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50"
              >
                <Sparkles className={`w-3.5 h-3.5 ${generatingResponse ? 'animate-spin' : ''}`} />
                <span>{generatingResponse ? 'Generating...' : 'Generate AI Response'}</span>
              </button>
            </div>
          </div>

          {responseFeedback && (
            <div className="p-3 rounded-xl bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-semibold">
              {responseFeedback}
            </div>
          )}

          {draftResponse ? (
            <div className="space-y-4">
              {/* Approval status banner */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-1 rounded-full font-bold text-[11px] border ${
                    draftResponse.is_sent ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' :
                    draftResponse.is_approved ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' :
                    'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  }`}>
                    {draftResponse.is_sent ? 'SENT TO CUSTOMER' : draftResponse.is_approved ? 'APPROVED BY HUMAN' : 'DRAFT (PENDING APPROVAL)'}
                  </span>
                  {draftResponse.approved_by && (
                    <span className="text-slate-400 text-[11px]">
                      Approved by {draftResponse.approved_by}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(draftResponse.content);
                      setCopiedDraft(true);
                      setTimeout(() => setCopiedDraft(false), 2000);
                    }}
                    className="p-1.5 rounded-lg bg-slate-800 hover:text-white text-slate-400"
                    title="Copy Content"
                  >
                    {copiedDraft ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                  {!draftResponse.is_sent && (
                    <button
                      onClick={() => setIsEditingDraft(!isEditingDraft)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      <span>{isEditingDraft ? 'Cancel Edit' : 'Edit Response'}</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Editor / Viewer */}
              {isEditingDraft ? (
                <div className="space-y-3">
                  <textarea
                    rows={8}
                    value={editedDraftText}
                    onChange={(e) => setEditedDraftText(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl p-4 text-xs text-white focus:outline-none focus:border-brand-500 leading-relaxed font-mono"
                  />
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setIsEditingDraft(false)}
                      className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveResponseEdit}
                      disabled={savingEdit}
                      className="px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white disabled:opacity-50"
                    >
                      {savingEdit ? 'Saving...' : 'Save Draft Edit'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
                  {draftResponse.content}
                </div>
              )}

              {/* Action Buttons: Approve & Send */}
              {!draftResponse.is_sent && (
                <div className="pt-2 flex items-center justify-end gap-3">
                  {!draftResponse.is_approved && (
                    <button
                      onClick={handleApproveResponse}
                      disabled={approving}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-600/20 disabled:opacity-50"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>{approving ? 'Approving...' : 'Approve Response'}</span>
                    </button>
                  )}

                  <button
                    onClick={handleSendResponse}
                    disabled={sending || !draftResponse.is_approved}
                    className={`flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-bold text-white shadow-lg transition-all ${
                      draftResponse.is_approved
                        ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20'
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed opacity-50'
                    }`}
                  >
                    <Send className="w-4 h-4" />
                    <span>{sending ? 'Sending...' : 'Send Response'}</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500 text-xs">
              No customer response drafted yet. Click "Generate AI Response" above to create one.
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Complaint Timeline */}
      {activeTab === 'timeline' && (
        <div className="p-6 space-y-4">
          <h3 className="text-sm font-bold text-white">19. Chronological Complaint Timeline</h3>
          <div className="relative pl-6 border-l-2 border-slate-800 space-y-4">
            {timeline.map((evt, idx) => (
              <div key={evt.id || idx} className="relative group">
                <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-brand-500 border-4 border-slate-950" />
                <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{evt.event_type}</span>
                    <span className="text-[11px] font-mono text-slate-500">
                      {evt.created_at ? new Date(evt.created_at).toLocaleString() : '--'}
                    </span>
                  </div>
                  <p className="text-slate-300">{evt.description}</p>
                  {evt.actor && (
                    <span className="text-[10px] text-slate-500 block">Actor: {evt.actor}</span>
                  )}
                  {evt.old_value && evt.new_value && (
                    <div className="text-[10px] text-slate-400 font-mono mt-1 pt-1 border-t border-slate-800/80">
                      <span>{evt.old_value}</span> &rarr; <span className="text-brand-300">{evt.new_value}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {timeline.length === 0 && (
              <p className="text-slate-500 text-xs italic">No timeline events recorded yet.</p>
            )}
          </div>
        </div>
      )}

      {/* Tab 4: Similar Complaints */}
      {activeTab === 'similar' && (
        <div className="p-6 space-y-4">
          <h3 className="text-sm font-bold text-white">16. Similar Complaints & Duplicates</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {similarCases.map((sim, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-brand-300">
                    {sim.ticket_number || `CMP-${sim.id}`}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                    {Math.round((sim.similarity_score || sim.similarity || 0.75) * 100)}% Match
                  </span>
                </div>
                <p className="font-semibold text-white">{sim.subject || 'Similar Inquiry'}</p>
                <p className="text-slate-400 line-clamp-2 text-[11px]">{sim.description || sim.body}</p>
              </div>
            ))}
            {similarCases.length === 0 && (
              <p className="text-slate-500 text-xs italic col-span-2">No similar complaints found.</p>
            )}
          </div>
        </div>
      )}

      {/* MODAL DIALOGS FOR ALL 14 ACTIONS */}
      {activeModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-md p-6 rounded-2xl border border-slate-700 shadow-2xl space-y-4 animate-scale-in">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="text-sm font-black text-white uppercase tracking-wider">
                {activeModal === 'assign' && 'Assign / Reassign Complaint'}
                {activeModal === 'department' && 'Change Department'}
                {activeModal === 'team' && 'Change Team'}
                {activeModal === 'agent' && 'Change Specialist Agent'}
                {activeModal === 'priority' && 'Change Priority Level'}
                {activeModal === 'status' && 'Change Lifecycle Status'}
                {activeModal === 'escalate' && 'Escalate Complaint'}
                {activeModal === 'resolve' && 'Resolve Complaint'}
                {activeModal === 'reopen' && 'Reopen Complaint'}
              </h3>
              <button onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body depending on activeModal */}
            <div className="space-y-3 text-xs">
              {/* Assign / Reassign */}
              {activeModal === 'assign' && (
                <>
                  <div>
                    <label className="text-slate-400 block mb-1">Select Department</label>
                    <select
                      value={targetDeptId}
                      onChange={(e) => setTargetDeptId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    >
                      <option value="">-- Choose Department --</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Select Team</label>
                    <select
                      value={targetTeamId}
                      onChange={(e) => setTargetTeamId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    >
                      <option value="">-- Choose Team --</option>
                      {teams.map((t) => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Select Specialist Agent</label>
                    <select
                      value={targetAgentId}
                      onChange={(e) => setTargetAgentId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    >
                      <option value="">-- Choose Agent --</option>
                      {agents.map((a) => (
                        <option key={a.id} value={a.id}>{a.name} ({a.current_workload || 0} active)</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Assignment Justification</label>
                    <input
                      type="text"
                      value={actionReason}
                      onChange={(e) => setActionReason(e.target.value)}
                      placeholder="Reason for reassignment..."
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    />
                  </div>
                </>
              )}

              {/* Change Department */}
              {activeModal === 'department' && (
                <>
                  <div>
                    <label className="text-slate-400 block mb-1">New Department</label>
                    <select
                      value={targetDeptId}
                      onChange={(e) => setTargetDeptId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    >
                      <option value="">-- Choose Department --</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Reason</label>
                    <input
                      type="text"
                      value={actionReason}
                      onChange={(e) => setActionReason(e.target.value)}
                      placeholder="Reason for department transfer..."
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    />
                  </div>
                </>
              )}

              {/* Change Team */}
              {activeModal === 'team' && (
                <>
                  <div>
                    <label className="text-slate-400 block mb-1">New Team</label>
                    <select
                      value={targetTeamId}
                      onChange={(e) => setTargetTeamId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    >
                      <option value="">-- Choose Team --</option>
                      {teams.map((t) => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Reason</label>
                    <input
                      type="text"
                      value={actionReason}
                      onChange={(e) => setActionReason(e.target.value)}
                      placeholder="Reason for team assignment..."
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    />
                  </div>
                </>
              )}

              {/* Change Agent */}
              {activeModal === 'agent' && (
                <>
                  <div>
                    <label className="text-slate-400 block mb-1">New Specialist Agent</label>
                    <select
                      value={targetAgentId}
                      onChange={(e) => setTargetAgentId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    >
                      <option value="">-- Choose Agent --</option>
                      {agents.map((a) => (
                        <option key={a.id} value={a.id}>{a.name} ({a.current_workload || 0} active)</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Reason</label>
                    <input
                      type="text"
                      value={actionReason}
                      onChange={(e) => setActionReason(e.target.value)}
                      placeholder="Reason for agent assignment..."
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    />
                  </div>
                </>
              )}

              {/* Change Priority */}
              {activeModal === 'priority' && (
                <>
                  <div>
                    <label className="text-slate-400 block mb-1">Priority Level</label>
                    <select
                      value={targetPriority}
                      onChange={(e) => {
                        setTargetPriority(e.target.value);
                        if (e.target.value === 'P1') setTargetUrgency('Critical');
                        else if (e.target.value === 'P2') setTargetUrgency('High');
                        else if (e.target.value === 'P3') setTargetUrgency('Medium');
                        else if (e.target.value === 'P4') setTargetUrgency('Low');
                      }}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    >
                      <option value="P1">P1 (Critical - 2h SLA)</option>
                      <option value="P2">P2 (High - 8h SLA)</option>
                      <option value="P3">P3 (Medium - 24h SLA)</option>
                      <option value="P4">P4 (Low - 72h SLA)</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Justification</label>
                    <input
                      type="text"
                      value={actionReason}
                      onChange={(e) => setActionReason(e.target.value)}
                      placeholder="Reason for priority adjustment..."
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    />
                  </div>
                </>
              )}

              {/* Change Status */}
              {activeModal === 'status' && (
                <>
                  <div>
                    <label className="text-slate-400 block mb-1">Target Status</label>
                    <select
                      value={targetStatus}
                      onChange={(e) => setTargetStatus(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    >
                      <option value="NEW">NEW</option>
                      <option value="ASSIGNED">ASSIGNED</option>
                      <option value="IN_PROGRESS">IN_PROGRESS</option>
                      <option value="WAITING_FOR_CUSTOMER">WAITING_FOR_CUSTOMER</option>
                      <option value="ESCALATED">ESCALATED</option>
                      <option value="RESOLVED">RESOLVED</option>
                      <option value="CLOSED">CLOSED</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Status Transition Notes</label>
                    <input
                      type="text"
                      value={actionReason}
                      onChange={(e) => setActionReason(e.target.value)}
                      placeholder="Notes for status transition..."
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    />
                  </div>
                </>
              )}

              {/* Escalate */}
              {activeModal === 'escalate' && (
                <>
                  <p className="text-rose-300 text-xs">
                    This will flag the ticket as escalated, alert supervisor teams, and update priority.
                  </p>
                  <div>
                    <label className="text-slate-400 block mb-1">Escalation Reason</label>
                    <textarea
                      rows={3}
                      value={actionReason}
                      onChange={(e) => setActionReason(e.target.value)}
                      placeholder="Specify why ticket requires tier-2 management escalation..."
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    />
                  </div>
                </>
              )}

              {/* Resolve */}
              {activeModal === 'resolve' && (
                <>
                  <div>
                    <label className="text-slate-400 block mb-1">Resolution Summary Notes</label>
                    <textarea
                      rows={4}
                      value={resolutionNotes}
                      onChange={(e) => setResolutionNotes(e.target.value)}
                      placeholder="Detail the steps taken to resolve the customer issue..."
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    />
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer pt-1">
                    <input
                      type="checkbox"
                      checked={saveKnowledge}
                      onChange={(e) => setSaveKnowledge(e.target.checked)}
                      className="rounded border-slate-800 text-brand-600 focus:ring-brand-500"
                    />
                    <span className="text-slate-300 text-xs">Save resolution to RAG Knowledge Base for future AI training</span>
                  </label>
                </>
              )}

              {/* Reopen */}
              {activeModal === 'reopen' && (
                <>
                  <div>
                    <label className="text-slate-400 block mb-1">Reason for Reopening</label>
                    <textarea
                      rows={3}
                      value={actionReason}
                      onChange={(e) => setActionReason(e.target.value)}
                      placeholder="Specify why this resolved case is being reopened..."
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white"
                    />
                  </div>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="pt-2 border-t border-slate-800 flex items-center justify-end gap-2">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-900 text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (activeModal === 'assign') handleAssignSubmit();
                  else if (activeModal === 'department') handleChangeDeptSubmit();
                  else if (activeModal === 'team') handleChangeTeamSubmit();
                  else if (activeModal === 'agent') handleChangeAgentSubmit();
                  else if (activeModal === 'priority') handleChangePrioritySubmit();
                  else if (activeModal === 'status') handleChangeStatusSubmit();
                  else if (activeModal === 'escalate') handleEscalateSubmit();
                  else if (activeModal === 'resolve') handleResolveSubmit();
                  else if (activeModal === 'reopen') handleReopenSubmit();
                }}
                disabled={modalLoading}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white disabled:opacity-50"
              >
                {modalLoading ? 'Processing...' : 'Confirm Action'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

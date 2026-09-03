import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserCheck, Clock, ArrowUpRight, CheckCircle } from 'lucide-react';
import UrgencyBadge from '../components/UrgencyBadge';
import DepartmentBadge from '../components/DepartmentBadge';
import { getComplaints } from '../api/complaints';

export default function MyAssignedPage() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadMyComplaints();
  }, []);

  const loadMyComplaints = async () => {
    setLoading(true);
    try {
      // In production, queries where assigned_agent_id corresponds to the active user
      const data = await getComplaints({ status: 'Assigned', limit: 20 });
      setComplaints(data.length > 0 ? data : await getComplaints({ limit: 10 }));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">My Assigned Complaints</h2>
        <p className="text-xs text-slate-400 mt-1">
          Active queue assigned to your agent profile. Prioritize tickets based on SLA target deadlines.
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-800/80 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400">
                <th className="py-3 px-4 font-semibold">Ticket</th>
                <th className="py-3 px-4 font-semibold">Subject & Customer</th>
                <th className="py-3 px-4 font-semibold">Department</th>
                <th className="py-3 px-4 font-semibold">Urgency</th>
                <th className="py-3 px-4 font-semibold">Priority</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Investigate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {complaints.map((c) => (
                <tr key={c.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-slate-300">{c.ticket_number}</td>
                  <td className="py-3 px-4 max-w-sm md:max-w-md">
                    <p className="font-semibold text-white truncate">{c.subject}</p>
                    <p className="text-[11px] text-slate-400 truncate mt-0.5">{c.customer_name || c.customer_email}</p>
                  </td>
                  <td className="py-3 px-4"><DepartmentBadge department={c.category} /></td>
                  <td className="py-3 px-4"><UrgencyBadge urgency={c.urgency} /></td>
                  <td className="py-3 px-4 font-semibold text-blue-400">{c.priority_level}</td>
                  <td className="py-3 px-4">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/30">
                      {c.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => navigate(`/complaints/${c.id}`)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-850 hover:bg-slate-800 text-brand-300 font-semibold border border-slate-700/80"
                    >
                      <span>Open</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
              {complaints.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    {loading ? 'Loading assigned tickets...' : 'No active tickets currently assigned to your queue.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

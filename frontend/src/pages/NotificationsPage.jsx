import React, { useState, useEffect } from 'react';
import { Bell, CheckCircle2, AlertTriangle, Info, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/notifications');
      setNotifications(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      await apiClient.post(`/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      <div>
        <h2 className="text-2xl font-black text-white tracking-tight">System Alerts & Notifications</h2>
        <p className="text-xs text-slate-400 mt-1">
          Automated escalation alerts, critical priority dispatches, and SLA breach warnings.
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-800/80 p-5 space-y-3">
        {notifications.map((n) => (
          <div
            key={n.id}
            className={`p-4 rounded-xl border flex items-start justify-between gap-4 transition-colors ${
              n.is_read
                ? 'bg-slate-900/40 border-slate-800/60 opacity-70'
                : 'bg-slate-900 border-slate-700/80'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg mt-0.5 ${
                n.notification_type === 'CRITICAL_TICKET' ? 'bg-rose-500/15 text-rose-400' : 'bg-blue-500/15 text-blue-400'
              }`}>
                {n.notification_type === 'CRITICAL_TICKET' ? <AlertTriangle className="w-4 h-4" /> : <Info className="w-4 h-4" />}
              </div>
              <div className="space-y-1">
                <h4 className="text-xs font-bold text-white">{n.title}</h4>
                <p className="text-xs text-slate-300 leading-relaxed">{n.message}</p>
                <span className="text-[10px] text-slate-500 block">
                  {new Date(n.created_at).toLocaleString()}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {n.link_url && (
                <button
                  onClick={() => navigate(n.link_url)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-300 text-xs font-semibold flex items-center gap-1"
                >
                  <span>View</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
              {!n.is_read && (
                <button
                  onClick={() => markAsRead(n.id)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Dismiss
                </button>
              )}
            </div>
          </div>
        ))}

        {notifications.length === 0 && (
          <div className="py-12 text-center text-xs text-slate-500">
            {loading ? 'Loading notifications...' : 'No notifications active.'}
          </div>
        )}
      </div>
    </div>
  );
}

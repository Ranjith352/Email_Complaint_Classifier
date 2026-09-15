import React, { useState, useEffect } from 'react';
import { Bell, CheckCircle2, AlertTriangle, Info, ArrowRight, CheckCheck, Filter, ShieldAlert } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterUnread, setFilterUnread] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadNotifications();
  }, [filterUnread]);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/notifications', {
        params: filterUnread ? { unread_only: true } : {}
      });
      setNotifications(res.data);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
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

  const markAllAsRead = async () => {
    try {
      await apiClient.post('/notifications/mark-all-read');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (err) {
      console.error(err);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="space-y-6 pb-12 animate-fade-in max-w-5xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-black text-white tracking-tight">In-App Notification Center</h2>
            {unreadCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                {unreadCount} Unread
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time department routing alerts, team dispatch notifications, and SLA warnings.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilterUnread(!filterUnread)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold border flex items-center gap-1.5 transition-colors ${
              filterUnread
                ? 'bg-brand-600 text-white border-brand-500'
                : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800'
            }`}
          >
            <Filter className="w-3.5 h-3.5" />
            <span>{filterUnread ? 'Showing Unread Only' : 'All Notifications'}</span>
          </button>

          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 flex items-center gap-1.5 transition-colors"
            >
              <CheckCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Mark All as Read</span>
            </button>
          )}
        </div>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-800/80 p-5 space-y-3 shadow-xl">
        {notifications.map((n) => {
          const isCritical = n.notification_type === 'CRITICAL_TICKET' || n.title?.toLowerCase().includes('critical');
          return (
            <div
              key={n.id}
              className={`p-4 rounded-xl border flex items-start justify-between gap-4 transition-all ${
                n.is_read
                  ? 'bg-slate-900/40 border-slate-800/50 opacity-75 hover:opacity-100'
                  : 'bg-slate-900/90 border-slate-700/80 shadow-md'
              } ${isCritical && !n.is_read ? 'border-l-4 border-l-rose-500' : ''}`}
            >
              <div className="flex items-start gap-3.5 flex-1 min-w-0">
                <div className={`p-2.5 rounded-xl mt-0.5 shrink-0 ${
                  isCritical ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                }`}>
                  {isCritical ? <ShieldAlert className="w-4 h-4" /> : <Bell className="w-4 h-4" />}
                </div>

                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="text-xs font-bold text-white tracking-wide">{n.title}</h4>
                    {!n.is_read && (
                      <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
                    )}
                  </div>

                  {/* Formatted multi-line notification content */}
                  <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs text-slate-200 font-mono whitespace-pre-wrap leading-relaxed">
                    {n.message}
                  </div>

                  <span className="text-[11px] text-slate-500 block pt-0.5">
                    {new Date(n.created_at).toLocaleString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit'
                    })}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0 pt-1">
                {n.link_url && (
                  <button
                    onClick={() => navigate(n.link_url)}
                    className="px-3 py-1.5 rounded-lg bg-brand-600/20 hover:bg-brand-600/30 text-brand-300 border border-brand-500/30 text-xs font-semibold flex items-center gap-1 transition-colors"
                  >
                    <span>View Ticket</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                )}
                {!n.is_read && (
                  <button
                    onClick={() => markAsRead(n.id)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
                  >
                    Dismiss
                  </button>
                )}
              </div>
            </div>
          );
        })}

        {notifications.length === 0 && (
          <div className="py-16 text-center text-xs text-slate-500 space-y-2">
            <Bell className="w-8 h-8 text-slate-700 mx-auto" />
            <p>{loading ? 'Loading notification history...' : 'No notifications in history.'}</p>
          </div>
        )}
      </div>
    </div>
  );
}

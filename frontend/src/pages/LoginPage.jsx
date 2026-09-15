import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Lock, Mail, ArrowRight, ShieldCheck, Zap } from 'lucide-react';
import { login, getCurrentUser } from '../api/auth';
import { useToast } from '../context/ToastContext';

export default function LoginPage({ onLoginSuccess }) {
  const navigate = useNavigate();
  const toast = useToast();
  const [email, setEmail] = useState('admin@complaints.io');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // If already authenticated with token, auto-redirect to dashboard
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/', { replace: true });
    }
  }, [navigate]);

  const performLogin = async (targetEmail, targetPassword) => {
    setLoading(true);
    setError(null);
    try {
      const res = await login(targetEmail, targetPassword);
      toast.success(`Welcome back, ${res.user?.name || 'Administrator'}!`);
      if (onLoginSuccess) onLoginSuccess(res.user);
      navigate('/', { replace: true });
    } catch (err) {
      console.error('Login error:', err);
      const msg = err.response?.data?.message || err.response?.data?.detail || 'Authentication failed. Please verify credentials.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    performLogin(email, password);
  };

  const handleQuickDemoLogin = (role = 'admin') => {
    if (role === 'admin') {
      setEmail('admin@complaints.io');
      setPassword('admin123');
      performLogin('admin@complaints.io', 'admin123');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-950 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black">
      <div className="w-full max-w-md p-8 rounded-3xl glass-modal border border-slate-800 space-y-6 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-emerald-400 text-slate-950 shadow-xl shadow-brand-500/20 mb-2">
            <Sparkles className="w-6 h-6 text-slate-950" />
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight">AutoTriage AI</h2>
          <p className="text-xs text-slate-400">Enterprise Complaint Management & Department Routing Portal</p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs text-center font-medium animate-fade-in">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-600/25 transition-all hover:scale-[1.01] disabled:opacity-50 mt-2 cursor-pointer"
          >
            <span>{loading ? 'Authenticating...' : 'Sign In with JWT'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* 1-Click Instant Demo Login Button */}
        <div className="pt-2">
          <button
            type="button"
            onClick={() => handleQuickDemoLogin('admin')}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-semibold bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 transition-all hover:border-emerald-500/50 cursor-pointer shadow-sm"
          >
            <Zap className="w-3.5 h-3.5 text-emerald-400" />
            <span>One-Click Instant Demo Access (Admin)</span>
          </button>
        </div>

        <div className="pt-3 border-t border-slate-800/80 text-center">
          <p className="text-[11px] text-slate-400">
            Pre-seeded Admin credentials: <span className="font-mono text-slate-300">admin@complaints.io / admin123</span>
          </p>
        </div>
      </div>
    </div>
  );
}

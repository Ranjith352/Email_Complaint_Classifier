import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(({ title, message, type = 'info', duration = 4000 }) => {
    const id = Date.now() + Math.random().toString(36).substring(2, 7);
    const newToast = { id, title, message, type, duration };
    setToasts((prev) => [...prev, newToast]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
    return id;
  }, [removeToast]);

  const toast = {
    success: (message, title = 'Success') => addToast({ message, title, type: 'success' }),
    error: (message, title = 'Error') => addToast({ message, title, type: 'error' }),
    warning: (message, title = 'Warning') => addToast({ message, title, type: 'warning' }),
    info: (message, title = 'Info') => addToast({ message, title, type: 'info' }),
    custom: addToast,
    dismiss: removeToast,
  };

  const getToastStyles = (type) => {
    switch (type) {
      case 'success':
        return {
          border: 'border-emerald-500/40',
          bg: 'bg-slate-900/95 text-emerald-300',
          iconBg: 'bg-emerald-500/20 text-emerald-400',
          progress: 'bg-emerald-500',
          icon: CheckCircle2,
        };
      case 'error':
        return {
          border: 'border-rose-500/40',
          bg: 'bg-slate-900/95 text-rose-300',
          iconBg: 'bg-rose-500/20 text-rose-400',
          progress: 'bg-rose-500',
          icon: AlertCircle,
        };
      case 'warning':
        return {
          border: 'border-amber-500/40',
          bg: 'bg-slate-900/95 text-amber-300',
          iconBg: 'bg-amber-500/20 text-amber-400',
          progress: 'bg-amber-500',
          icon: AlertTriangle,
        };
      case 'info':
      default:
        return {
          border: 'border-cyan-500/40',
          bg: 'bg-slate-900/95 text-cyan-300',
          iconBg: 'bg-cyan-500/20 text-cyan-400',
          progress: 'bg-cyan-500',
          icon: Info,
        };
    }
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      {/* Toast Render Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
        {toasts.map((t) => {
          const style = getToastStyles(t.type);
          const Icon = style.icon;
          return (
            <div
              key={t.id}
              role="alert"
              className={`pointer-events-auto relative overflow-hidden rounded-xl border p-4 shadow-2xl backdrop-blur-md transition-all duration-300 transform translate-y-0 ${style.bg} ${style.border}`}
            >
              <div className="flex items-start gap-3">
                <div className={`p-1.5 rounded-lg shrink-0 ${style.iconBg}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 pr-2">
                  {t.title && <h4 className="text-xs font-bold text-slate-100 mb-0.5">{t.title}</h4>}
                  <p className="text-xs text-slate-300 leading-relaxed">{t.message}</p>
                </div>
                <button
                  onClick={() => removeToast(t.id)}
                  className="shrink-0 p-1 text-slate-400 hover:text-slate-100 rounded-md transition-colors"
                  aria-label="Dismiss notification"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

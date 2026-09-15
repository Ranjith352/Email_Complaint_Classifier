import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import { AlertTriangle, HelpCircle, ShieldAlert, X } from 'lucide-react';

const ConfirmContext = createContext(null);

export function ConfirmProvider({ children }) {
  const [dialog, setDialog] = useState(null);
  const resolveRef = useRef(null);

  const confirm = useCallback(
    ({
      title = 'Confirm Action',
      message = 'Are you sure you want to proceed?',
      confirmText = 'Confirm',
      cancelText = 'Cancel',
      variant = 'danger', // 'danger' | 'warning' | 'info'
    }) => {
      return new Promise((resolve) => {
        resolveRef.current = resolve;
        setDialog({
          title,
          message,
          confirmText,
          cancelText,
          variant,
        });
      });
    },
    []
  );

  const handleClose = (confirmed) => {
    if (resolveRef.current) {
      resolveRef.current(confirmed);
      resolveRef.current = null;
    }
    setDialog(null);
  };

  const getVariantStyles = (variant) => {
    switch (variant) {
      case 'danger':
        return {
          icon: ShieldAlert,
          iconBg: 'bg-rose-500/20 text-rose-400 border border-rose-500/30',
          btnBg: 'bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/30',
        };
      case 'warning':
        return {
          icon: AlertTriangle,
          iconBg: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
          btnBg: 'bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold shadow-lg shadow-amber-900/30',
        };
      case 'info':
      default:
        return {
          icon: HelpCircle,
          iconBg: 'bg-brand-500/20 text-brand-400 border border-brand-500/30',
          btnBg: 'bg-brand-600 hover:bg-brand-500 text-slate-950 font-bold shadow-lg shadow-brand-900/30',
        };
    }
  };

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {dialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden p-6">
            {/* Close button */}
            <button
              onClick={() => handleClose(false)}
              className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition"
              aria-label="Close dialog"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex gap-4">
              {(() => {
                const styles = getVariantStyles(dialog.variant);
                const Icon = styles.icon;
                return (
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${styles.iconBg}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                );
              })()}

              <div className="flex-1">
                <h3 className="text-base font-bold text-slate-100">{dialog.title}</h3>
                <p className="mt-1.5 text-xs text-slate-300 leading-relaxed">{dialog.message}</p>

                <div className="mt-6 flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => handleClose(false)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700/80 border border-slate-700 transition"
                  >
                    {dialog.cancelText}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleClose(true)}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold transition ${getVariantStyles(dialog.variant).btnBg}`}
                  >
                    {dialog.confirmText}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const context = useContext(ConfirmContext);
  if (!context) {
    throw new Error('useConfirm must be used within a ConfirmProvider');
  }
  return context;
}

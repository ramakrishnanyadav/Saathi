import React from 'react';
import { AlertCircle, X, RefreshCw } from 'lucide-react';
import { ErrorState } from '../types';

interface ErrorModalProps {
  errorState: ErrorState | null;
  onRetry: () => void;
  onDismiss: () => void;
}

export const ErrorModal: React.FC<ErrorModalProps> = ({
  errorState,
  onRetry,
  onDismiss,
}) => {
  if (!errorState) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
      <div className="glass-panel w-full max-w-md rounded-2xl p-5 flex flex-col gap-4 border-red-500/40 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <h3 className="text-sm font-bold uppercase tracking-wider">
              {errorState.title} {errorState.status > 0 ? `(HTTP ${errorState.status})` : ''}
            </h3>
          </div>
          <button onClick={onDismiss} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
          {errorState.message}
        </p>

        <div className="flex items-center gap-2 pt-1">
          {errorState.retryable && (
            <button
              onClick={onRetry}
              className="flex-1 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-lg shadow-amber-500/20 flex items-center justify-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Submission</span>
            </button>
          )}
          <button
            onClick={onDismiss}
            className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
          >
            Dismiss & Edit Input
          </button>
        </div>
      </div>
    </div>
  );
};

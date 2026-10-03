import React from 'react';
import { Sparkles, CheckCircle2 } from 'lucide-react';

interface OnboardingModalProps {
  isOpen: boolean;
  onComplete: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  isOpen,
  onComplete,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex items-center justify-center p-4 animate-fadeIn">
      <div className="glass-panel w-full max-w-md rounded-2xl p-6 flex flex-col gap-5 border-amber-500/40 shadow-2xl text-center">
        <div className="flex flex-col items-center gap-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-500 to-amber-300 flex items-center justify-center font-black text-slate-950 text-xl shadow-lg shadow-amber-500/30">
            S
          </div>
          <h2 className="text-xl font-extrabold text-white tracking-tight">Welcome to SAATH</h2>
          <p className="text-xs text-amber-300 font-semibold">Calm Household Memory & Follow-Through</p>
        </div>

        <div className="flex flex-col gap-3 text-left text-xs bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-white font-bold">Remember Promises & To-Dos</strong>
              <p className="text-slate-400 text-[11px]">Tell SAATH what members agreed to handle.</p>
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-white font-bold">Track Unresolved Issues</strong>
              <p className="text-slate-400 text-[11px]">Keep repairs like leaks or Wi-Fi fixes visible.</p>
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <strong className="text-white font-bold">Prepared WhatsApp Follow-ups</strong>
              <p className="text-slate-400 text-[11px]">SAATH drafts reminders when things become overdue.</p>
            </div>
          </div>
        </div>

        <button
          onClick={onComplete}
          className="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2"
        >
          <Sparkles className="w-4 h-4" />
          <span>Start Using SAATH</span>
        </button>
      </div>
    </div>
  );
};

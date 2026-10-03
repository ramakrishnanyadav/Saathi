import React from 'react';
import { Sparkles, X } from 'lucide-react';
import { ConfirmationCardState } from '../types';

interface ConfirmationModalProps {
  card: ConfirmationCardState | null;
  onConfirm: () => void;
  onDismiss: () => void;
  getMemberName: (id: string) => string;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  card,
  onConfirm,
  onDismiss,
  getMemberName,
}) => {
  if (!card) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
      <div className="glass-panel w-full max-w-md rounded-2xl p-5 flex flex-col gap-4 border-amber-500/40 shadow-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-amber-400">
            <Sparkles className="w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider">SAATH Understood</h3>
          </div>
          <button onClick={onDismiss} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-200 italic font-mono leading-relaxed">
          "{card.rawText}"
        </div>

        <div className="flex flex-col gap-2 text-xs">
          <span className="font-bold text-white uppercase tracking-wider text-[11px]">Extracted Household Memory:</span>
          <div className="glass-card rounded-xl p-3.5 flex flex-col gap-2 border-amber-500/20">
            {card.eventsCreated && card.eventsCreated.length > 0 ? (
              card.eventsCreated.map((ev: any, idx: number) => (
                <div key={idx} className="flex flex-col gap-1 border-b border-slate-800/60 pb-2 last:border-0 last:pb-0">
                  <span className="text-amber-300 font-bold text-xs">
                    • {ev.payload?.title || ev.payload?.text || ev.type || 'Household Memory Saved'}
                  </span>
                  {ev.payload?.responsible_party && (
                    <span className="text-slate-300 text-[11px]">
                      Responsible: <strong className="text-white">{getMemberName(ev.payload.responsible_party)}</strong>
                    </span>
                  )}
                  {ev.payload?.due_at && (
                    <span className="text-slate-400 text-[10px]">
                      Due: {new Date(ev.payload.due_at).toLocaleString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' })}
                    </span>
                  )}
                </div>
              ))
            ) : (
              <span className="text-amber-300 font-semibold">• Saved safely into household memory</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 pt-2">
          <button
            onClick={onConfirm}
            className="flex-1 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-lg shadow-amber-500/20"
          >
            Confirm & Save
          </button>
          <button
            onClick={onDismiss}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
};

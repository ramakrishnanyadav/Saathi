import React, { useEffect } from 'react';
import { Search, DollarSign, AlertTriangle, BookOpen, MessageCircle, X } from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectAction: (action: string) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectAction,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else onSelectAction('open');
      } else if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, onSelectAction]);

  if (!isOpen) return null;

  const commands = [
    { id: 'memory', label: 'Search household memory', icon: Search },
    { id: 'money', label: 'Record household expense', icon: DollarSign },
    { id: 'issues', label: 'View household issues & repairs', icon: AlertTriangle },
    { id: 'todos', label: 'View overdue promises & to-dos', icon: BookOpen },
    { id: 'followups', label: 'View prepared WhatsApp follow-ups', icon: MessageCircle },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-start justify-center pt-24 p-4 animate-fadeIn">
      <div className="glass-panel w-full max-w-lg rounded-2xl p-4 flex flex-col gap-3 border-amber-500/40 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
          <div className="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider">
            <Search className="w-4 h-4" />
            <span>SAATH Quick Actions (Ctrl + K)</span>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex flex-col gap-1.5">
          {commands.map((cmd) => {
            const Icon = cmd.icon;
            return (
              <button
                key={cmd.id}
                onClick={() => {
                  onSelectAction(cmd.id);
                  onClose();
                }}
                className="p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800 border border-slate-800 flex items-center justify-between text-xs text-slate-200 hover:text-white transition group"
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
                  <span className="font-semibold">{cmd.label}</span>
                </div>
                <span className="text-[10px] font-mono text-slate-500 uppercase">↵ Select</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

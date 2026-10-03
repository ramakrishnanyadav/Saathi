import { useEffect } from 'react';
import { Command } from 'cmdk';
import { useUIStore } from '../../lib/store';
import { useNavigate } from 'react-router-dom';
import { Home, Clock, Users, ReceiptText, BarChart2, Shield, FastForward } from 'lucide-react';

export function CommandPalette() {
  const open = useUIStore((s) => s.commandPaletteOpen);
  const setOpen = useUIStore((s) => s.setCommandPaletteOpen);
  const advanceClock = useUIStore((s) => s.advanceClock);
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen(!open);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, setOpen]);

  if (!open) return null;

  const runCommand = (action: () => void) => {
    action();
    setOpen(false);
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        background: 'rgba(15, 23, 42, 0.4)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '15vh',
      }}
      onClick={() => setOpen(false)}
    >
      <div
        style={{ width: '90%', maxWidth: 600 }}
        onClick={(e) => e.stopPropagation()}
      >
        <Command
          style={{
            background: '#FFFFFF',
            border: '2px solid var(--brand-saffron)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: '0 20px 50px rgba(15, 23, 42, 0.15)',
            overflow: 'hidden',
            color: 'var(--ink-900)',
          }}
        >
          <div style={{ padding: '14px 18px', borderBottom: '1.5px solid var(--border-light)' }}>
            <Command.Input
              placeholder="Type a command or search..."
              style={{
                width: '100%',
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'var(--ink-900)',
                fontSize: 16,
              }}
              autoFocus
            />
          </div>

          <Command.List style={{ maxHeight: 320, overflowY: 'auto', padding: 8 }}>
            <Command.Empty style={{ padding: 16, color: 'var(--ink-500)', fontSize: 14 }}>
              No results found.
            </Command.Empty>

            <Command.Group heading="Navigation" style={{ fontSize: 12, fontWeight: 700, color: 'var(--ink-500)', padding: '6px 12px' }}>
              <Item icon={Home} label="Needs Attention (Home)" onSelect={() => runCommand(() => navigate('/app/today'))} />
              <Item icon={Clock} label="Household History" onSelect={() => runCommand(() => navigate('/app/history'))} />
              <Item icon={Users} label="People & Household" onSelect={() => runCommand(() => navigate('/app/house'))} />
              <Item icon={ReceiptText} label="Expenses" onSelect={() => runCommand(() => navigate('/app/money'))} />
              <Item icon={BarChart2} label="Weekly Summary" onSelect={() => runCommand(() => navigate('/app/week'))} />
              <Item icon={Shield} label="Local Proof (Privacy)" onSelect={() => runCommand(() => navigate('/app/privacy'))} />
              <Item icon={FastForward} label="Time Machine (Lab)" onSelect={() => runCommand(() => navigate('/app/lab'))} />
            </Command.Group>

            <Command.Group heading="Demo Actions" style={{ fontSize: 12, fontWeight: 700, color: 'var(--ink-500)', padding: '6px 12px' }}>
              <Item icon={FastForward} label="Advance Clock by 24 Hours" onSelect={() => runCommand(() => advanceClock(24))} />
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}

function Item({ icon: Icon, label, onSelect }: { icon: any; label: string; onSelect: () => void }) {
  return (
    <Command.Item
      onSelect={onSelect}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '10px 14px',
        borderRadius: 'var(--radius-sm)',
        cursor: 'pointer',
        fontSize: 14,
        color: 'var(--ink-900)',
        transition: 'background 120ms',
      }}
    >
      <Icon size={16} color="var(--brand-saffron)" />
      <span>{label}</span>
    </Command.Item>
  );
}

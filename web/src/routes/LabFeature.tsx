import { useUIStore } from '../lib/store';
import { advanceDemoClock } from '../lib/api';
import { FastForward, RotateCcw } from 'lucide-react';

export function LabFeature() {
  const clockOffsetHours = useUIStore((s) => s.clockOffsetHours);
  const simulatedTimeMs = useUIStore((s) => s.simulatedTimeMs);
  const advanceClock = useUIStore((s) => s.advanceClock);
  const resetClock = useUIStore((s) => s.resetClock);

  const handleAdvance = async (hours: number) => {
    advanceClock(hours);
    try {
      await advanceDemoClock(hours);
    } catch {
      /* Handled */
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      <div>
        <h1 className="font-serif" style={{ fontSize: 32, fontWeight: 400, color: 'var(--text-hi)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <FastForward size={24} color="var(--diya)" />
          Time Machine ("Ghadi Dial")
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text-md)', marginTop: 4 }}>
          Advance the simulated clock to see overdue items flicker and sky palettes shift
        </p>
      </div>

      <div className="glass-card" style={{ padding: 36, textAlign: 'center' }}>
        <div style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--diya)', fontWeight: 700, letterSpacing: '0.08em', marginBottom: 12 }}>
          Simulated Clock Time
        </div>
        <div className="font-serif" style={{ fontSize: 42, color: 'var(--text-hi)', marginBottom: 8 }}>
          {new Date(simulatedTimeMs).toLocaleString('en-IN', { weekday: 'long', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
        </div>
        <div style={{ fontSize: 14, color: 'var(--text-lo)', marginBottom: 32 }}>
          Offset from real time: <strong>+{clockOffsetHours} hours</strong>
        </div>

        {/* Quick Jump Preset Buttons */}
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => handleAdvance(1)}
            style={{ padding: '12px 20px', borderRadius: 'var(--radius-sm)', background: 'var(--glass-2)', border: '1px solid var(--glass-edge)', color: '#FFF', fontWeight: 600, cursor: 'pointer' }}
          >
            +1 Hour
          </button>
          <button
            onClick={() => handleAdvance(24)}
            style={{ padding: '12px 20px', borderRadius: 'var(--radius-sm)', background: 'var(--diya)', color: '#FFF', border: 'none', fontWeight: 600, cursor: 'pointer' }}
          >
            +24 Hours (+1 Day)
          </button>
          <button
            onClick={() => handleAdvance(72)}
            style={{ padding: '12px 20px', borderRadius: 'var(--radius-sm)', background: 'var(--dusk)', color: '#FFF', border: 'none', fontWeight: 600, cursor: 'pointer' }}
          >
            +72 Hours (+3 Days)
          </button>
          <button
            onClick={resetClock}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '12px 20px', borderRadius: 'var(--radius-sm)', background: 'var(--ember)', color: '#FFF', border: 'none', fontWeight: 600, cursor: 'pointer' }}
          >
            <RotateCcw size={15} />
            Reset Clock
          </button>
        </div>
      </div>
    </div>
  );
}

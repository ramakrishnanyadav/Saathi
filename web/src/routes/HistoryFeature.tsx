import { useState, useEffect, useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { getHistory, undoEvent, timeAgo } from '../lib/api';
import { Clock, RotateCcw } from 'lucide-react';
import type { HistoryEvent } from '../types';

export function HistoryFeature() {
  const [events, setEvents] = useState<HistoryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const parentRef = useRef<HTMLDivElement>(null);

  const fetchHistoryData = () => {
    setLoading(true);
    getHistory()
      .then((data) => setEvents(Array.isArray(data) ? data : data.events ?? []))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchHistoryData();
  }, []);

  const rowVirtualizer = useVirtualizer({
    count: events.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 82,
    overscan: 5,
  });

  const handleUndo = async (eventId: string) => {
    try {
      const res = await undoEvent(eventId);
      if (res.ok) fetchHistoryData();
    } catch {
      /* Handled */
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      <div>
        <h1 className="font-sora" style={{ fontSize: 32, fontWeight: 800, color: 'var(--ink-900)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <Clock size={26} color="var(--brand-saffron)" />
          Household History
        </h1>
        <p style={{ fontSize: 14, color: 'var(--ink-500)', marginTop: 4 }}>
          Virtualized audit trail of every recorded event in order
        </p>
      </div>

      {loading ? (
        <div className="glass-fake" style={{ padding: 40, textAlign: 'center' }}>Loading timeline...</div>
      ) : events.length === 0 ? (
        <div className="glass-fake" style={{ padding: 40, textAlign: 'center', color: 'var(--ink-500)' }}>
          No events recorded yet.
        </div>
      ) : (
        <div
          ref={parentRef}
          style={{
            height: '600px',
            overflow: 'auto',
            position: 'relative',
          }}
        >
          <div
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const e = events[virtualRow.index];
              return (
                <div
                  key={virtualRow.key}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: `${virtualRow.size}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                    paddingBottom: '12px',
                  }}
                >
                  <div className="glass-fake card-domain-waiting" style={{ padding: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--ink-900)' }}>
                        {e.payload?.title || e.payload?.text || e.type}
                      </div>
                      <div style={{ fontSize: 13, color: 'var(--ink-500)', marginTop: 2 }}>
                        Type: {e.type} · {timeAgo(e.occurred_at)}
                      </div>
                    </div>

                    <button
                      onClick={() => handleUndo(e.id)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '6px 12px',
                        borderRadius: 'var(--radius-sm)',
                        background: '#FFFFFF',
                        border: '1.5px solid var(--border-light)',
                        color: 'var(--ink-700)',
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      <RotateCcw size={13} />
                      Undo
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

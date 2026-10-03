import { motion } from 'framer-motion';
import { timeAgo, eventTypeToHuman } from '../api';
import type { HistoryEvent } from '../types';

interface Props {
  events: HistoryEvent[];
  loading: boolean;
  error?: string;
}

export function HistoryTimeline({ events, loading, error }: Props) {
  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {[1, 2, 3, 4].map(i => (
          <div key={i} style={{ display: 'flex', gap: 12 }}>
            <div className="skeleton" style={{ width: 10, height: 10, borderRadius: '50%', marginTop: 5 }} />
            <div className="skeleton" style={{ flex: 1, height: 56 }} />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        padding: '16px 20px',
        background: 'var(--danger-light)',
        borderRadius: 'var(--radius-md)',
        fontSize: 14, color: '#991B1B',
      }}>
        {error}
      </div>
    );
  }

  if (!events?.length) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '48px 24px',
        color: 'var(--text-secondary)',
        fontSize: 14,
      }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>📋</div>
        Nothing recorded yet. Tell SAATH what happened to get started.
      </div>
    );
  }

  // Group by day
  const groups = groupByDay(events);

  return (
    <div>
      {groups.map(([day, dayEvents], gi) => (
        <div key={day} style={{ marginBottom: 28 }}>
          <div style={{
            fontSize: 12,
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--text-tertiary)',
            marginBottom: 14,
          }}>
            {day}
          </div>

          <div style={{ position: 'relative', paddingLeft: 22 }}>
            {/* Vertical line */}
            <div style={{
              position: 'absolute',
              left: 4,
              top: 0,
              bottom: 0,
              width: 2,
              background: 'var(--border)',
            }} />

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {dayEvents.map((event, idx) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: (gi * dayEvents.length + idx) * 0.03 }}
                  style={{ position: 'relative' }}
                >
                  {/* Dot */}
                  <div style={{
                    position: 'absolute',
                    left: -18,
                    top: 8,
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: eventTypeToColor(event.type),
                    border: '2px solid var(--surface)',
                    boxShadow: '0 0 0 1px var(--border)',
                  }} />

                  {/* Card */}
                  <div
                    className="card"
                    style={{ padding: '12px 16px', cursor: 'default' }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--text)' }}>
                          {eventTypeToHuman(event.type)}
                        </div>
                        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 3 }}>
                          {eventSummary(event)}
                        </div>
                      </div>
                      <span style={{ fontSize: 12, color: 'var(--text-tertiary)', whiteSpace: 'nowrap', marginTop: 1 }}>
                        {timeAgo(event.occurred_at)}
                      </span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function eventTypeToColor(type: string): string {
  const map: Record<string, string> = {
    commitment_created: '#6366F1',
    commitment_updated: '#8B5CF6',
    issue_reported:     '#EF4444',
    expense_created:    '#F59E0B',
    expense_confirmed:  '#10B981',
    supply_depleted:    '#F97316',
    supply_restocked:   '#10B981',
    followup_sent:      '#06B6D4',
    note_recorded:      '#6B7280',
  };
  return map[type] ?? '#9CA3AF';
}

function eventSummary(event: HistoryEvent): string {
  const p = event.payload ?? {};
  if (p.title) return p.title;
  if (p.text) return p.text.slice(0, 80) + (p.text.length > 80 ? '…' : '');
  if (p.item_name) return p.item_name;
  return '';
}

function groupByDay(events: HistoryEvent[]): [string, HistoryEvent[]][] {
  const map: Record<string, HistoryEvent[]> = {};
  for (const e of events) {
    const d = new Date(e.occurred_at);
    const now = new Date();
    let label: string;
    if (isSameDay(d, now)) label = 'Today';
    else if (isSameDay(d, new Date(now.getTime() - 86400000))) label = 'Yesterday';
    else label = d.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'short' });
    if (!map[label]) map[label] = [];
    map[label].push(e);
  }
  return Object.entries(map);
}

function isSameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate();
}

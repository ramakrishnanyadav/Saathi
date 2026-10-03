import { useState, useEffect } from 'react';
import { getReflection, getMembers } from '../lib/api';
import { BarChart2, ShieldCheck, HeartHandshake, Table, LayoutGrid } from 'lucide-react';

export function WeekFeature() {
  const [reflection, setReflection] = useState<any>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showTable, setShowTable] = useState(false);

  useEffect(() => {
    Promise.all([getReflection(), getMembers()])
      .then(([refData, memData]) => {
        setReflection(refData);
        setMembers(Array.isArray(memData) ? memData : memData.members ?? []);
      })
      .finally(() => setLoading(false));
  }, []);

  const getMemberName = (id: string) => members.find((m) => m.id === id)?.name ?? id;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 className="font-serif" style={{ fontSize: 32, fontWeight: 400, color: 'var(--text-hi)', display: 'flex', alignItems: 'center', gap: 10 }}>
            <BarChart2 size={24} color="var(--diya)" />
            This Week's Household Summary
          </h1>
          <p style={{ fontSize: 14, color: 'var(--text-md)', marginTop: 4 }}>
            Invisible coordination & physical care work keeping the home running
          </p>
        </div>

        <button
          onClick={() => setShowTable(!showTable)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 14px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--glass-2)',
            border: '1px solid var(--glass-edge)',
            color: 'var(--text-hi)',
            fontSize: 13,
            cursor: 'pointer',
          }}
        >
          {showTable ? <LayoutGrid size={15} /> : <Table size={15} />}
          <span>{showTable ? 'Card View' : 'Table View'}</span>
        </button>
      </div>

      {/* No Scoreboard Policy Notice */}
      <div
        className="glass-card"
        style={{
          padding: '14px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          background: 'rgba(99, 102, 241, 0.08)',
          borderColor: 'rgba(99, 102, 241, 0.2)',
        }}
      >
        <ShieldCheck size={20} color="var(--sky)" />
        <span style={{ fontSize: 13, color: 'var(--text-md)' }}>
          <strong>SAATH Principle:</strong> No competitive rankings or leaderboards. All household care & coordination efforts are valued equally.
        </span>
      </div>

      {loading ? (
        <div className="glass-card" style={{ padding: 40, textAlign: 'center' }}>Loading summary...</div>
      ) : reflection ? (
        showTable ? (
          /* Table View Alternative */
          <div className="glass-card" style={{ padding: 24, overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--glass-edge)', color: 'var(--text-lo)' }}>
                  <th style={{ padding: 12 }}>Member</th>
                  <th style={{ padding: 12 }}>Coordination Actions</th>
                  <th style={{ padding: 12 }}>Physical Tasks</th>
                </tr>
              </thead>
              <tbody>
                {(reflection.members ?? reflection.member_contributions ?? []).map((m: any) => (
                  <tr key={m.member_id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <td style={{ padding: 12, fontWeight: 600 }}>{m.name || getMemberName(m.member_id)}</td>
                    <td style={{ padding: 12 }}>{m.coordination_count} tasks</td>
                    <td style={{ padding: 12 }}>{m.physical_count} tasks</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          /* Invisible Work Weave Cards */
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
            {(reflection.members ?? reflection.member_contributions ?? []).map((m: any) => (
              <div key={m.member_id} className="glass-fake card-domain-coord" style={{ padding: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                  <HeartHandshake size={20} color="var(--domain-coord)" />
                  <div style={{ fontWeight: 700, fontSize: 18, color: 'var(--ink-900)' }}>
                    {m.name || getMemberName(m.member_id)}
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ background: '#FFFFFF', padding: 14, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)' }}>
                    <div style={{ fontSize: 12, color: 'var(--ink-500)', fontWeight: 600 }}>Coordination & Calls</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--brand-saffron)' }}>
                      {m.coordination_count} follow-up{m.coordination_count !== 1 ? 's' : ''} & update{m.coordination_count !== 1 ? 's' : ''}
                    </div>
                  </div>

                  <div style={{ background: '#FFFFFF', padding: 14, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)' }}>
                    <div style={{ fontSize: 12, color: 'var(--ink-500)', fontWeight: 600 }}>Physical Home Tasks</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--domain-money)' }}>
                      {m.physical_count} restock{m.physical_count !== 1 ? 's' : ''} & repair{m.physical_count !== 1 ? 's' : ''}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      ) : null}
    </div>
  );
}

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAttention, draftFollowup, markFollowupSent } from '../lib/api';
import { ArrowLeft, Send, MessageSquare } from 'lucide-react';
import type { AttentionItem } from '../types';

export function ThreadDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [item, setItem] = useState<AttentionItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [whatsappUrl, setWhatsappUrl] = useState<string | null>(null);
  const [tone, setTone] = useState<'polite' | 'firm'>('polite');

  useEffect(() => {
    if (!id) return;
    getAttention().then((data) => {
      const items: AttentionItem[] = Array.isArray(data) ? data : data.items ?? [];
      const found = items.find((i) => i.id === id);
      if (found) {
        setItem(found);
        draftFollowup(found.id).then((r) => r.ok && r.json()).then((d) => {
          if (d?.whatsapp_url) setWhatsappUrl(d.whatsapp_url);
        });
      }
    }).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="glass-card" style={{ padding: 40, textAlign: 'center' }}>Loading thread...</div>;
  if (!item) return <div className="glass-card" style={{ padding: 40, textAlign: 'center' }}>Thread not found. <button onClick={() => navigate('/app/today')}>Go Back</button></div>;

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <button
        onClick={() => navigate('/app/today')}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          background: 'none',
          border: 'none',
          color: 'var(--text-md)',
          cursor: 'pointer',
          fontSize: 14,
        }}
      >
        <ArrowLeft size={16} />
        Back to Attention
      </button>

      {/* Hero Header */}
      <div className="glass-card" style={{ padding: 24 }}>
        <div style={{ fontSize: 13, color: 'var(--diya)', fontWeight: 600, marginBottom: 6 }}>
          THREAD #{item.id.slice(0, 8)}
        </div>
        <h1 className="font-serif" style={{ fontSize: 28, marginBottom: 12 }}>{item.title}</h1>
        <div style={{ display: 'flex', gap: 16, fontSize: 14, color: 'var(--text-md)' }}>
          {item.responsible_party && <span>👤 Responsible: {item.responsible_party}</span>}
          {item.tracked_by && <span>Following up: {item.tracked_by}</span>}
        </div>
      </div>

      {/* Thread Timeline */}
      <div className="glass-card" style={{ padding: 24 }}>
        <h2 className="font-serif" style={{ fontSize: 20, marginBottom: 20 }}>Event Beads & Timeline</h2>
        <div style={{ position: 'relative', paddingLeft: 24, borderLeft: '2px solid var(--glass-edge)' }}>
          <TimelineBead title="Promise Created" time="Yesterday" desc={`Added: "${item.title}"`} color="var(--diya)" />
          {item.is_overdue && <TimelineBead title="Deadline Passed (Overdue)" time="Today" desc="Overdue notification triggered." color="var(--ember)" />}
        </div>
      </div>

      {/* Follow-up Composer Sheet */}
      <div className="glass-card" style={{ padding: 24, background: 'var(--glass-3)' }}>
        <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
          <MessageSquare size={18} color="var(--diya)" />
          WhatsApp Check-in Composer
        </div>

        <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
          <button
            onClick={() => setTone('polite')}
            style={{
              padding: '4px 12px',
              borderRadius: 'var(--radius-pill)',
              border: '1px solid var(--glass-edge)',
              background: tone === 'polite' ? 'var(--diya)' : 'transparent',
              color: '#FFF',
              fontSize: 12,
              cursor: 'pointer',
            }}
          >
            Polite Tone
          </button>
          <button
            onClick={() => setTone('firm')}
            style={{
              padding: '4px 12px',
              borderRadius: 'var(--radius-pill)',
              border: '1px solid var(--glass-edge)',
              background: tone === 'firm' ? 'var(--ember)' : 'transparent',
              color: '#FFF',
              fontSize: 12,
              cursor: 'pointer',
            }}
          >
            Firm Tone
          </button>
        </div>

        {/* Quick Reply Bar Chips */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
          {['Nahi aaya', 'Kal aayega', 'Aa gaya', 'Cancel'].map((chip) => (
            <span
              key={chip}
              style={{
                fontSize: 12,
                padding: '4px 10px',
                borderRadius: 'var(--radius-pill)',
                background: 'var(--glass-2)',
                border: '1px solid var(--glass-edge)',
                color: 'var(--text-hi)',
                cursor: 'pointer',
              }}
            >
              {chip}
            </span>
          ))}
        </div>

        {whatsappUrl ? (
          <a
            href={whatsappUrl}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => markFollowupSent(item.id)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '12px 24px',
              borderRadius: 'var(--radius-sm)',
              background: '#25D366',
              color: '#FFF',
              textDecoration: 'none',
              fontWeight: 600,
            }}
          >
            <Send size={16} />
            Open in WhatsApp
          </a>
        ) : (
          <div style={{ fontSize: 13, color: 'var(--text-lo)' }}>Preparing WhatsApp link...</div>
        )}
      </div>
    </div>
  );
}

function TimelineBead({ title, time, desc, color }: { title: string; time: string; desc: string; color: string }) {
  return (
    <div style={{ position: 'relative', marginBottom: 20 }}>
      <div
        style={{
          position: 'absolute',
          left: -31,
          top: 2,
          width: 12,
          height: 12,
          borderRadius: '50%',
          background: color,
          border: '2px solid var(--ink-0)',
        }}
      />
      <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-hi)' }}>{title}</div>
      <div style={{ fontSize: 13, color: 'var(--text-lo)' }}>{time}</div>
      <div style={{ fontSize: 14, color: 'var(--text-md)', marginTop: 4 }}>{desc}</div>
    </div>
  );
}

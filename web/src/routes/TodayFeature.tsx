import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '../lib/store';
import { getAttention, draftFollowup, markFollowupSent } from '../lib/api';
import { DiyaBadge } from '../components/glass/DiyaBadge';
import { BellRing, List, Grid, RefreshCw, ArrowRight, CheckCircle } from 'lucide-react';
import type { AttentionItem } from '../types';

export function TodayFeature() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [items, setItems] = useState<AttentionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [followupLoading, setFollowupLoading] = useState<Set<string>>(new Set());

  const listViewOnly = useUIStore((s) => s.listViewOnly);
  const setListViewOnly = useUIStore((s) => s.setListViewOnly);

  const fetchItems = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getAttention();
      setItems(Array.isArray(data) ? data : data.items ?? []);
    } catch {
      setError('Could not load attention items.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const handleFollowup = async (item: AttentionItem) => {
    setFollowupLoading((prev) => new Set([...prev, item.id]));
    try {
      const res = await draftFollowup(item.id);
      if (res.ok) {
        const data = await res.json();
        if (data.whatsapp_url) {
          window.open(data.whatsapp_url, '_blank');
          await markFollowupSent(item.id);
          fetchItems();
        }
      }
    } catch {
      /* Handled */
    } finally {
      setFollowupLoading((prev) => {
        const next = new Set(prev);
        next.delete(item.id);
        return next;
      });
    }
  };

  const overdueItems = items.filter((i) => i.is_overdue);
  const actionItems = items.filter((i) => !i.is_overdue && i.next_action);
  const waitingItems = items.filter((i) => !i.is_overdue && !i.next_action);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 className="font-sora" style={{ fontSize: 32, fontWeight: 800, color: 'var(--ink-900)', display: 'flex', alignItems: 'center', gap: 10 }}>
            <BellRing size={26} color={items.length > 0 ? 'var(--brand-coral)' : 'var(--domain-done)'} />
            {t('attention.title')}
          </h1>
          <p style={{ fontSize: 14, color: 'var(--ink-500)', marginTop: 4 }}>
            {t('attention.sub')}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* List View Toggle (Accessibility First) */}
          <button
            onClick={() => setListViewOnly(!listViewOnly)}
            aria-label={listViewOnly ? 'Switch to Constellation Board' : 'Switch to List View'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 14px',
              borderRadius: 'var(--radius-sm)',
              background: '#FFFFFF',
              border: '1.5px solid var(--border-light)',
              color: 'var(--ink-700)',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {listViewOnly ? <Grid size={15} /> : <List size={15} />}
            <span>{listViewOnly ? 'Board' : 'List'}</span>
          </button>

          <button
            onClick={fetchItems}
            aria-label="Refresh"
            style={{
              padding: 9,
              borderRadius: 'var(--radius-sm)',
              background: '#FFFFFF',
              border: '1.5px solid var(--border-light)',
              color: 'var(--ink-700)',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-fake" style={{ height: 90, opacity: 0.5 }} />
          ))}
        </div>
      ) : error ? (
        <div className="glass-fake card-domain-issue" style={{ padding: 20, color: 'var(--domain-issue)' }}>{error}</div>
      ) : items.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-fake card-domain-done"
          style={{ padding: '60px 24px', textAlign: 'center' }}
        >
          <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--domain-done-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <CheckCircle size={32} color="var(--domain-done)" />
          </div>
          <h2 className="font-serif" style={{ fontSize: 26, marginBottom: 8, color: 'var(--ink-900)' }}>{t('attention.allClearTitle')}</h2>
          <p style={{ fontSize: 14, color: 'var(--ink-500)', maxWidth: 400, margin: '0 auto' }}>
            {t('attention.allClearSub')}
          </p>
        </motion.div>
      ) : (
        /* Constellation Zone Board / List */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {/* Overdue Zone */}
          {overdueItems.length > 0 && (
            <ZoneSection title="🔴 Overdue & Action Needed" color="var(--domain-issue)">
              {overdueItems.map((item) => (
                <DiyaCard key={item.id} item={item} domainClass="card-domain-issue" onFollowup={handleFollowup} isLoading={followupLoading.has(item.id)} onSelect={() => navigate(`/app/threads/${item.id}`)} />
              ))}
            </ZoneSection>
          )}

          {/* Action Zone */}
          {actionItems.length > 0 && (
            <ZoneSection title="🟡 Needs Follow-up" color="var(--domain-waiting)">
              {actionItems.map((item) => (
                <DiyaCard key={item.id} item={item} domainClass="card-domain-waiting" onFollowup={handleFollowup} isLoading={followupLoading.has(item.id)} onSelect={() => navigate(`/app/threads/${item.id}`)} />
              ))}
            </ZoneSection>
          )}

          {/* Waiting Zone */}
          {waitingItems.length > 0 && (
            <ZoneSection title="🟣 Waiting on others" color="var(--domain-coord)">
              {waitingItems.map((item) => (
                <DiyaCard key={item.id} item={item} domainClass="card-domain-coord" onFollowup={handleFollowup} isLoading={followupLoading.has(item.id)} onSelect={() => navigate(`/app/threads/${item.id}`)} />
              ))}
            </ZoneSection>
          )}
        </div>
      )}
    </div>
  );
}

function ZoneSection({ title, color, children }: { title: string; color: string; children: React.ReactNode }) {
  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color, marginBottom: 14 }}>
        {title}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
        {children}
      </div>
    </div>
  );
}

function DiyaCard({ item, domainClass, onFollowup, isLoading, onSelect }: { item: AttentionItem; domainClass: string; onFollowup: (i: AttentionItem) => void; isLoading: boolean; onSelect: () => void }) {
  return (
    <motion.div
      layout
      onClick={onSelect}
      className={`glass-fake ${domainClass} ${item.is_overdue ? 'animate-coral-pulse' : ''}`}
      style={{
        padding: 22,
        cursor: 'pointer',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--ink-900)' }}>{item.title}</div>
        <DiyaBadge status={item.is_overdue ? 'needs_action' : 'waiting'} isOverdue={item.is_overdue} />
      </div>

      <div style={{ fontSize: 13, color: 'var(--ink-500)', marginBottom: 16, display: 'flex', flexWrap: 'wrap', gap: 12 }}>
        {item.responsible_party && <span>👤 {item.responsible_party}</span>}
        {item.due_at && <span>📅 {new Date(item.due_at).toLocaleDateString('en-IN')}</span>}
      </div>

      <div style={{ display: 'flex', gap: 8 }} onClick={(e) => e.stopPropagation()}>
        {item.next_action && (
          <button
            onClick={() => onFollowup(item)}
            disabled={isLoading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 16px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--brand-gradient)',
              color: '#FFF',
              border: 'none',
              fontSize: 13,
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(255, 93, 93, 0.3)',
            }}
          >
            <span>{isLoading ? 'Preparing...' : 'Send check-in'}</span>
            <ArrowRight size={14} />
          </button>
        )}
      </div>
    </motion.div>
  );
}

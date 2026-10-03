import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Edit2, X } from 'lucide-react';
import { formatRupees, formatDate } from '../api';

interface Props {
  open: boolean;
  data: {
    applied_events?: any[];
    pending_confirmations?: any[];
    reply_resolution?: any;
    commitments?: any[];
  } | null;
  originalText: string;
  members: { id: string; name: string }[];
  onConfirmExpense: (payload: any) => void;
  onDismiss: () => void;
}

export function UnderstandingCard({ open, data, originalText, members, onConfirmExpense, onDismiss }: Props) {
  if (!open || !data) return null;

  const memberName = (id: string) => members.find(m => m.id === id)?.name ?? id;

  const pendingExpense = data.pending_confirmations?.[0];
  const commitment = data.applied_events?.find(e => e.event_type === 'commitment_created');
  const issue = data.applied_events?.find(e => e.event_type === 'issue_reported');
  const notes = data.applied_events?.filter(e =>
    e.event_type === 'note_recorded' || e.event_type === 'supply_depleted'
  ) || [];

  const hasContent = pendingExpense || commitment || issue || notes.length > 0;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        style={{
          background: 'var(--surface)',
          border: '1.5px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-md)',
          overflow: 'hidden',
          marginTop: 12,
        }}
        role="region"
        aria-label="What SAATH understood"
      >
        {/* Header */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '16px 20px',
          borderBottom: '1px solid var(--border)',
          background: 'var(--surface-muted)',
        }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text)' }}>
              {pendingExpense ? '💰 Check this expense' : '✓ Here\'s what I understood'}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>
              "{originalText.slice(0, 60)}{originalText.length > 60 ? '…' : ''}"
            </div>
          </div>
          <button
            onClick={onDismiss}
            aria-label="Dismiss"
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: 4 }}
          >
            <X size={18} />
          </button>
        </div>

        <div style={{ padding: '20px' }}>
          {!hasContent && (
            <div style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
              Noted — SAATH has remembered this.
            </div>
          )}

          {/* Commitment card */}
          {commitment && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              style={{ marginBottom: 16 }}
            >
              <div style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)', marginBottom: 10 }}>
                Promise tracked
              </div>
              <div className="card" style={{ padding: '16px' }}>
                <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text)', marginBottom: 10 }}>
                  {commitment.payload?.title}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <Row label="Who's handling it?" value={commitment.payload?.responsible_party} />
                  {commitment.payload?.due_at && (
                    <Row label="When?" value={formatDate(commitment.payload.due_at)} />
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {/* Issue */}
          {issue && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              style={{ marginBottom: 16 }}
            >
              <div style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)', marginBottom: 10 }}>
                Problem noted
              </div>
              <div className="card" style={{ padding: '16px' }}>
                <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text)' }}>
                  {issue.payload?.title}
                </div>
                {issue.payload?.description && (
                  <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 6 }}>
                    {issue.payload.description}
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Expense confirmation */}
          {pendingExpense && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              style={{ marginBottom: 16 }}
            >
              <div style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)', marginBottom: 10 }}>
                Expense — please confirm before saving
              </div>
              <div className="card" style={{ padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <div style={{ fontWeight: 600, fontSize: 18, color: 'var(--text)' }}>
                    {formatRupees(pendingExpense.amount_paise || pendingExpense.payload?.amount_paise || 0)}
                  </div>
                  <span className="badge badge-warning">Not saved yet</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
                  <Row label="Paid by" value={memberName(pendingExpense.paid_by || pendingExpense.payload?.paid_by)} />
                  {pendingExpense.payload?.title && (
                    <Row label="For" value={pendingExpense.payload.title} />
                  )}
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <button
                    className="btn btn-primary"
                    style={{ flex: 1 }}
                    onClick={() => onConfirmExpense(pendingExpense.payload || pendingExpense)}
                  >
                    <CheckCircle size={15} /> Yes, save this
                  </button>
                  <button className="btn btn-secondary btn-sm" onClick={onDismiss}>
                    <Edit2 size={14} /> Change
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* Notes */}
          {notes.map((n: any, i: number) => (
            <motion.div
              key={n.id || i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + i * 0.05 }}
              className="card"
              style={{ padding: '14px 16px', marginBottom: 10 }}
            >
              <div style={{ fontSize: 14, color: 'var(--text)' }}>
                {n.payload?.text || n.payload?.item_name}
              </div>
            </motion.div>
          ))}

          {/* Dismiss if no expense */}
          {!pendingExpense && hasContent && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              style={{ display: 'flex', gap: 10, marginTop: 8 }}
            >
              <button className="btn btn-primary" onClick={onDismiss} style={{ flex: 1 }}>
                <CheckCircle size={15} /> Got it
              </button>
            </motion.div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

function Row({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div style={{ display: 'flex', gap: 8, fontSize: 14 }}>
      <span style={{ color: 'var(--text-secondary)', minWidth: 120 }}>{label}</span>
      <span style={{ fontWeight: 500, color: 'var(--text)' }}>{value}</span>
    </div>
  );
}

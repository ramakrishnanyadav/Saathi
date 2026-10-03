import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Clock, CheckCircle, ArrowRight, Loader2 } from 'lucide-react';
import { formatDate } from '../api';
import type { AttentionItem } from '../types';

interface Props {
  items: AttentionItem[];
  loading: boolean;
  error?: string;
  onFollowup: (item: AttentionItem) => void;
  followupLoading: Set<string>;
}

export function AttentionPanel({ items, loading, error, onFollowup, followupLoading }: Props) {
  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {[1, 2, 3].map(i => (
          <div key={i} className="skeleton" style={{ height: 80, width: '100%' }} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        background: 'var(--danger-light)',
        borderRadius: 'var(--radius-md)',
        padding: '16px 20px',
        color: '#991B1B',
        fontSize: 14,
      }}>
        {error}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '48px 24px',
          textAlign: 'center',
          gap: 12,
        }}
      >
        <div style={{
          width: 56, height: 56,
          borderRadius: '50%',
          background: 'var(--success-light)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <CheckCircle size={24} color="var(--success)" />
        </div>
        <div style={{ fontWeight: 600, fontSize: 16, color: 'var(--text)' }}>
          All clear!
        </div>
        <div style={{ fontSize: 14, color: 'var(--text-secondary)', maxWidth: 280 }}>
          Nothing needs your attention right now. SAATH is watching everything.
        </div>
      </motion.div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <AnimatePresence initial={false}>
        {items.map((item, idx) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ type: 'spring', stiffness: 350, damping: 30, delay: idx * 0.04 }}
          >
            <AttentionCard
              item={item}
              onFollowup={onFollowup}
              isLoadingFollowup={followupLoading.has(item.id)}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

function AttentionCard({
  item,
  onFollowup,
  isLoadingFollowup,
}: {
  item: AttentionItem;
  onFollowup: (item: AttentionItem) => void;
  isLoadingFollowup: boolean;
}) {
  const isOverdue = item.is_overdue;
  const hasFollowup = item.next_action?.kind === 'send_followup';
  const hasWhatsApp = !!item.next_action?.whatsapp_url;

  const urgencyColor = isOverdue ? 'var(--danger)' : 'var(--warning)';
  const urgencyBg   = isOverdue ? 'var(--danger-light)' : 'var(--warning-light)';

  return (
    <div
      className="card"
      style={{
        padding: '16px 20px',
        borderLeft: `3px solid ${urgencyColor}`,
        background: 'var(--surface)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
        {/* Icon */}
        <div style={{
          width: 36, height: 36,
          borderRadius: 'var(--radius-sm)',
          background: urgencyBg,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, marginTop: 2,
        }}>
          {isOverdue
            ? <AlertTriangle size={17} color={urgencyColor} />
            : <Clock size={17} color={urgencyColor} />
          }
        </div>

        {/* Content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--text)', marginBottom: 4 }}>
            {item.title}
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 16px', marginBottom: 12 }}>
            {item.responsible_party && (
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                👤 {item.responsible_party}
              </span>
            )}
            {item.tracked_by && item.tracked_by !== item.responsible_party && (
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                Following up: {item.tracked_by}
              </span>
            )}
            {item.due_at && (
              <span style={{ fontSize: 13, color: isOverdue ? 'var(--danger)' : 'var(--text-secondary)', fontWeight: isOverdue ? 600 : 400 }}>
                📅 {formatDate(item.due_at)} {isOverdue ? '(overdue!)' : ''}
              </span>
            )}
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {hasFollowup && (
              <button
                className="btn btn-primary btn-sm"
                onClick={() => onFollowup(item)}
                disabled={isLoadingFollowup}
                aria-label={`Send check-in for ${item.title}`}
              >
                {isLoadingFollowup ? (
                  <><Loader2 size={13} className="animate-spin-slow" /> Preparing…</>
                ) : (
                  <>Send check-in <ArrowRight size={13} /></>
                )}
              </button>
            )}

            {hasWhatsApp && item.next_action?.whatsapp_url && (
              <a
                href={item.next_action.whatsapp_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-sm"
                style={{
                  background: '#25D366',
                  color: '#fff',
                  border: 'none',
                  textDecoration: 'none',
                }}
                aria-label={`WhatsApp ${item.responsible_party}`}
              >
                <WhatsAppIcon />
                WhatsApp
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function WhatsAppIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
    </svg>
  );
}

import { AlertCircle, Clock, CheckCircle } from 'lucide-react';

interface Props {
  status: 'needs_action' | 'waiting' | 'done';
  isOverdue?: boolean;
}

export function DiyaBadge({ status, isOverdue }: Props) {
  if (isOverdue) {
    return (
      <span
        className="animate-coral-pulse"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          fontSize: 12,
          fontWeight: 700,
          padding: '4px 12px',
          borderRadius: 'var(--radius-pill)',
          background: 'rgba(255, 93, 93, 0.12)',
          color: '#D92D2D', // WCAG 4.5:1 on light
          border: '1px solid rgba(255, 93, 93, 0.35)',
        }}
      >
        <AlertCircle size={13} />
        Overdue
      </span>
    );
  }

  if (status === 'needs_action') {
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          fontSize: 12,
          fontWeight: 700,
          padding: '4px 12px',
          borderRadius: 'var(--radius-pill)',
          background: 'rgba(255, 159, 28, 0.12)',
          color: '#B45309', // WCAG 4.5:1 on light
          border: '1px solid rgba(255, 159, 28, 0.35)',
        }}
      >
        <AlertCircle size={13} />
        Needs action
      </span>
    );
  }

  if (status === 'waiting') {
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          fontSize: 12,
          fontWeight: 700,
          padding: '4px 12px',
          borderRadius: 'var(--radius-pill)',
          background: 'rgba(122, 90, 248, 0.12)',
          color: '#5B21B6', // WCAG 4.5:1 on light
          border: '1px solid rgba(122, 90, 248, 0.35)',
        }}
      >
        <Clock size={13} />
        Waiting
      </span>
    );
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        fontSize: 12,
        fontWeight: 700,
        padding: '4px 12px',
        borderRadius: 'var(--radius-pill)',
        background: 'rgba(43, 196, 138, 0.12)',
        color: '#065F46', // WCAG 4.5:1 on light
        border: '1px solid rgba(43, 196, 138, 0.35)',
      }}
    >
      <CheckCircle size={13} />
      Done
    </span>
  );
}

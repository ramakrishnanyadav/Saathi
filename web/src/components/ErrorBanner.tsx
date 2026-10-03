import { motion } from 'framer-motion';
import { X } from 'lucide-react';

interface Props {
  error: string | null;
  onClose: () => void;
}

export function ErrorBanner({ error, onClose }: Props) {
  if (!error) return null;
  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      style={{
        background: 'var(--danger-light)',
        borderRadius: 'var(--radius-md)',
        padding: '12px 16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 12,
        marginBottom: 12,
        fontSize: 14,
        color: '#991B1B',
        border: '1px solid #FECACA',
      }}
      role="alert"
      aria-live="assertive"
    >
      <span>{error}</span>
      <button
        onClick={onClose}
        aria-label="Dismiss error"
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#991B1B', flexShrink: 0 }}
      >
        <X size={16} />
      </button>
    </motion.div>
  );
}

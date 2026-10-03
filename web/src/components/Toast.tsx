import { motion } from 'framer-motion';
import { AnimatePresence } from 'framer-motion';
import { CheckCircle, Bell, AlertTriangle } from 'lucide-react';

interface Toast {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

interface Props {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

export function ToastStack({ toasts, onRemove }: Props) {
  return (
    <div
      style={{
        position: 'fixed',
        bottom: 88,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 200,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        alignItems: 'center',
        pointerEvents: 'none',
      }}
      aria-live="polite"
      aria-atomic="true"
    >
      <AnimatePresence>
        {toasts.map(t => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            onClick={() => onRemove(t.id)}
            role="status"
            style={{
              background: t.type === 'error' ? '#111827' : '#111827',
              color: '#fff',
              padding: '11px 18px',
              borderRadius: 'var(--radius-lg)',
              fontSize: 14,
              fontWeight: 500,
              boxShadow: 'var(--shadow-lg)',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              pointerEvents: 'auto',
              cursor: 'pointer',
              maxWidth: '90vw',
              userSelect: 'none',
              whiteSpace: 'nowrap',
              borderLeft: `3px solid ${
                t.type === 'success' ? '#10B981' :
                t.type === 'error'   ? '#EF4444' : '#6366F1'
              }`,
            }}
          >
            {t.type === 'success' && <CheckCircle size={15} color="#10B981" />}
            {t.type === 'error'   && <AlertTriangle size={15} color="#EF4444" />}
            {t.type === 'info'    && <Bell size={15} color="#6366F1" />}
            {t.message}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

// Hook to manage toasts
import { useState, useCallback } from 'react';

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, type: Toast['type'] = 'success', durationMs = 3500) => {
    const id = Math.random().toString(36).slice(2);
    setToasts(prev => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, durationMs);
    return id;
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return { toasts, addToast, removeToast };
}

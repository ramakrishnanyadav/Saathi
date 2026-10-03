import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, ArrowRight, Loader2 } from 'lucide-react';

interface UniversalComposerProps {
  onSend: (text: string) => Promise<void>;
  loading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

const PLACEHOLDERS = [
  'What happened?',
  "The landlord said he'll come tomorrow...",
  'I paid ₹1,450 for electricity...',
  'Rahul called the plumber...',
  'The milk is almost finished...',
  'The Wi-Fi is acting up again...',
];

export function UniversalComposer({ onSend, loading, disabled }: UniversalComposerProps) {
  const [text, setText] = useState('');
  const [focused, setFocused] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Rotate placeholder
  useEffect(() => {
    if (focused || text) return;
    const t = setInterval(() => {
      setPlaceholderIndex(i => (i + 1) % PLACEHOLDERS.length);
    }, 3500);
    return () => clearInterval(t);
  }, [focused, text]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
  }, [text]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = useCallback(async () => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    // Do NOT clear text before backend confirmation
    await onSend(trimmed);
    // Text cleared by parent on success only
  }, [text, loading, onSend]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mr = new MediaRecorder(stream);
      mediaRecorderRef.current = mr;
      mr.ondataavailable = e => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        if (audioChunksRef.current.length > 0) {
          const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const fd = new FormData();
          fd.append('audio', blob, 'recording.webm');
          fd.append('author_id', 'm-1');
          try {
            const res = await fetch('/api/v1/voice/ingest', {
              method: 'POST',
              headers: { 'X-House-Id': 'h-demo', 'X-Member-Id': 'm-1' },
              body: fd,
            });
            if (res.ok) {
              const data = await res.json();
              if (data.transcript) setText(data.transcript);
            }
          } catch { /* handled by onSend */ }
        }
        setIsRecording(false);
      };
      mr.start();
      setIsRecording(true);
    } catch {
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
  };

  const canSend = text.trim().length > 0 && !loading;

  return (
    <div
      className="composer-wrap"
      role="form"
      aria-label="Tell SAATH what happened"
    >
      <textarea
        ref={textareaRef}
        className="composer-input"
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder={PLACEHOLDERS[placeholderIndex]}
        rows={1}
        aria-label="What happened?"
        disabled={loading || disabled}
        style={{ overflow: 'hidden' }}
        id="composer-input"
      />

      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px 14px',
      }}>
        <span style={{
          fontSize: '12px',
          color: 'var(--text-tertiary)',
          userSelect: 'none',
        }}>
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--primary)' }}>
              <Loader2 size={13} className="animate-spin-slow" />
              Understanding...
            </span>
          ) : (
            'Enter to send · Shift+Enter for new line'
          )}
        </span>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Mic button */}
          <button
            type="button"
            onClick={isRecording ? stopRecording : startRecording}
            disabled={loading}
            aria-label={isRecording ? 'Stop recording' : 'Start voice recording'}
            style={{
              width: 36, height: 36,
              borderRadius: '50%',
              border: '1px solid var(--border)',
              background: isRecording ? '#FEE2E2' : 'var(--surface-muted)',
              color: isRecording ? 'var(--danger)' : 'var(--text-secondary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 150ms',
            }}
          >
            {isRecording ? <MicOff size={15} /> : <Mic size={15} />}
          </button>

          {/* Send button */}
          <motion.button
            type="button"
            onClick={handleSubmit}
            disabled={!canSend}
            aria-label="Send message"
            whileTap={canSend ? { scale: 0.93 } : {}}
            style={{
              width: 36, height: 36,
              borderRadius: '50%',
              border: 'none',
              background: canSend ? 'var(--primary)' : 'var(--border)',
              color: canSend ? '#fff' : 'var(--text-tertiary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: canSend ? 'pointer' : 'not-allowed',
              transition: 'all 200ms var(--ease-spring)',
              boxShadow: canSend ? '0 2px 8px rgba(99,102,241,0.3)' : 'none',
            }}
          >
            <ArrowRight size={16} />
          </motion.button>
        </div>
      </div>

      {/* Recording indicator */}
      <AnimatePresence>
        {isRecording && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{
              padding: '8px 16px',
              background: '#FEF2F2',
              display: 'flex', alignItems: 'center', gap: 8,
              fontSize: 13, color: 'var(--danger)',
            }}
          >
            <span className="animate-pulse-subtle" style={{
              width: 8, height: 8, borderRadius: '50%',
              background: 'var(--danger)', display: 'inline-block',
            }} />
            Recording... tap the mic icon to stop
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

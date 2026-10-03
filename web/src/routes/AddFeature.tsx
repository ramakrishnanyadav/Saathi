import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { MicOrb } from '../components/ui/MicOrb';
import { sendMessage, confirmExpense, formatRupees } from '../lib/api';
import { ArrowLeft, Send, CheckCircle } from 'lucide-react';

export function AddFeature() {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async () => {
    if (!text.trim() || loading) return;
    setLoading(true);
    try {
      const res = await sendMessage(text.trim(), `msg-${Date.now()}`);
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch {
      /* Handled */
    } finally {
      setLoading(false);
    }
  };

  const pendingExpense = result?.pending_confirmations?.[0];

  return (
    <div style={{ maxWidth: 640, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24, paddingTop: 20 }}>
      <button
        onClick={() => navigate('/app/today')}
        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', color: 'var(--text-md)', cursor: 'pointer', fontSize: 14 }}
      >
        <ArrowLeft size={16} />
        Back
      </button>

      <div className="glass-card" style={{ padding: 32, textAlign: 'center' }}>
        <h1 className="font-serif" style={{ fontSize: 28, marginBottom: 8 }}>Tell SAATH what happened</h1>
        <p style={{ fontSize: 14, color: 'var(--text-md)', marginBottom: 28 }}>
          Hold the mic to speak, or type plain Hinglish text below.
        </p>

        {/* Audio Reactive Mic Orb */}
        <div style={{ marginBottom: 32 }}>
          <MicOrb onTranscript={(transcript) => setText(transcript)} disabled={loading} />
        </div>

        {/* Input Textarea */}
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. Rahul paid ₹1,450 for electricity bill..."
          rows={3}
          style={{
            width: '100%',
            background: 'var(--ink-1)',
            border: '1.5px solid var(--glass-edge)',
            borderRadius: 'var(--radius-md)',
            padding: 16,
            color: 'var(--text-hi)',
            fontSize: 15,
            outline: 'none',
            resize: 'none',
            marginBottom: 16,
          }}
        />

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={handleSubmit}
            disabled={!text.trim() || loading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '12px 28px',
              borderRadius: 'var(--radius-md)',
              background: text.trim() ? 'var(--diya)' : 'var(--glass-2)',
              color: text.trim() ? '#FFF' : 'var(--text-lo)',
              border: 'none',
              fontWeight: 600,
              fontSize: 15,
              cursor: text.trim() ? 'pointer' : 'not-allowed',
            }}
          >
            <span>{loading ? 'Understanding...' : 'Submit Update'}</span>
            <Send size={16} />
          </button>
        </div>
      </div>

      {/* Entity Chips & Confirmation Result */}
      {result && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h2 className="font-serif" style={{ fontSize: 20, color: 'var(--meadow)', margin: 0 }}>
              ✓ Structured Result
            </h2>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 12, background: result.parser === 'llm' ? 'rgba(34, 197, 94, 0.12)' : 'rgba(245, 158, 11, 0.12)', fontSize: 12, fontWeight: 600, color: result.parser === 'llm' ? '#166534' : '#92400e' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: result.parser === 'llm' ? '#22c55e' : '#f59e0b' }} />
              {result.parser === 'llm' ? `Parsed by ${result.model || 'Gemma'} (${Math.round(result.latency_ms || 0)}ms)` : `Parsed by Rules (${result.fallback_reason || 'Offline'})`}
            </div>
          </div>


          {pendingExpense ? (
            /* Money Confirmation Card */
            <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: 20, borderRadius: 'var(--radius-md)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
              <div style={{ fontWeight: 700, fontSize: 22, color: 'var(--diya)', marginBottom: 8 }}>
                Confirm {formatRupees(pendingExpense.amount_paise || pendingExpense.payload?.amount_paise || 0)}
              </div>
              <div style={{ fontSize: 14, color: 'var(--text-hi)', marginBottom: 16 }}>
                Paid by {pendingExpense.paid_by || pendingExpense.payload?.paid_by} · Expense Title: {pendingExpense.payload?.title || 'Bill'}
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  onClick={async () => {
                    await confirmExpense(pendingExpense.payload || pendingExpense);
                    navigate('/app/today');
                  }}
                  style={{ padding: '10px 20px', borderRadius: 'var(--radius-sm)', background: 'var(--meadow)', color: '#FFF', border: 'none', fontWeight: 600, cursor: 'pointer' }}
                >
                  <CheckCircle size={15} style={{ verticalAlign: 'middle', marginRight: 6 }} />
                  Confirm & Save Expense
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div style={{ fontSize: 14, color: 'var(--text-hi)', marginBottom: 16 }}>
                SAATH has remembered this update durably.
              </div>
              <button
                onClick={() => navigate('/app/today')}
                style={{ padding: '10px 20px', borderRadius: 'var(--radius-sm)', background: 'var(--diya)', color: '#FFF', border: 'none', fontWeight: 600, cursor: 'pointer' }}
              >
                Go to Dashboard
              </button>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}

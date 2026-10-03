import { useState, useEffect } from 'react';
import { getExpenses, formatRupees, timeAgo } from '../lib/api';
import { ReceiptText } from 'lucide-react';

export function MoneyFeature() {
  const [expenses, setExpenses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getExpenses()
      .then((data) => setExpenses(Array.isArray(data) ? data : data.expenses ?? []))
      .finally(() => setLoading(false));
  }, []);

  const total = expenses.reduce((sum, e) => sum + (e.amount_paise ?? 0), 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="font-serif" style={{ fontSize: 32, fontWeight: 400, color: 'var(--text-hi)', display: 'flex', alignItems: 'center', gap: 10 }}>
            <ReceiptText size={24} color="var(--diya)" />
            Household Expenses
          </h1>
          <p style={{ fontSize: 14, color: 'var(--text-md)', marginTop: 4 }}>
            Shared household payments & bills
          </p>
        </div>
      </div>

      {total > 0 && (
        <div className="glass-card" style={{ padding: 28, background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(16, 185, 129, 0.12) 100%)' }}>
          <div style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--text-lo)', letterSpacing: '0.08em', marginBottom: 6 }}>
            Total Recorded
          </div>
          <div className="font-serif" style={{ fontSize: 36, fontWeight: 600, color: 'var(--text-hi)', fontVariantNumeric: 'tabular-nums' }}>
            {formatRupees(total)}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-md)', marginTop: 4 }}>
            across {expenses.length} confirmed payment{expenses.length !== 1 ? 's' : ''}
          </div>
        </div>
      )}

      {loading ? (
        <div className="glass-card" style={{ padding: 40, textAlign: 'center' }}>Loading expenses...</div>
      ) : expenses.length === 0 ? (
        <div className="glass-card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-md)' }}>
          No expenses recorded yet. Tell SAATH about a payment to get started.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {expenses.map((exp, idx) => (
            <div key={exp.id || idx} className="glass-card" style={{ padding: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 16, color: 'var(--text-hi)' }}>
                  {exp.title || exp.payload?.title || 'Expense'}
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-md)', marginTop: 2 }}>
                  Paid by {exp.paid_by || exp.payload?.paid_by} · {timeAgo(exp.occurred_at || Date.now())}
                </div>
              </div>

              <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-hi)', fontVariantNumeric: 'tabular-nums' }}>
                {formatRupees(exp.amount_paise || exp.payload?.amount_paise || 0)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

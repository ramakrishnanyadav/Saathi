import { useNavigate } from 'react-router-dom';

export function NotFound() {
  const navigate = useNavigate();
  return (
    <div style={{ padding: 60, textAlign: 'center' }}>
      <h1 className="font-serif" style={{ fontSize: 36, marginBottom: 12 }}>404 — Page Not Found</h1>
      <p style={{ color: 'var(--text-md)', marginBottom: 24 }}>This page does not exist in SAATH.</p>
      <button
        onClick={() => navigate('/app/today')}
        style={{ padding: '10px 20px', borderRadius: 'var(--radius-sm)', background: 'var(--diya)', color: '#FFF', border: 'none', cursor: 'pointer' }}
      >
        Go to Home
      </button>
    </div>
  );
}

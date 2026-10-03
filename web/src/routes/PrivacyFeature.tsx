import { useState, useEffect } from 'react';
import { getHealthz } from '../lib/api';
import { flushOutbox, getQueuedItems } from '../lib/outbox';
import { Shield, Wifi, Cpu, Database, RefreshCw } from 'lucide-react';

export function PrivacyFeature() {
  const [healthStatus, setHealthStatus] = useState<boolean | null>(null);
  const [queuedCount, setQueuedCount] = useState(0);
  const [syncing, setSyncing] = useState(false);
  const [simulatedOffline, setSimulatedOffline] = useState(false);

  useEffect(() => {
    getHealthz().then((h) => setHealthStatus(h)).catch(() => setHealthStatus(false));
    getQueuedItems().then((items: any[]) => setQueuedCount(items.length));
  }, []);

  const handleManualSync = async () => {
    setSyncing(true);
    await flushOutbox();
    const items = await getQueuedItems();
    setQueuedCount(items.length);
    setSyncing(false);
  };


  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      <div>
        <h1 className="font-serif" style={{ fontSize: 32, fontWeight: 400, color: 'var(--text-hi)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <Shield size={24} color="var(--meadow)" />
          Local Proof & Privacy Diagnostics
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text-md)', marginTop: 4 }}>
          Verify that your household memory operates locally inside your flat
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
        <DiagCard icon={Cpu} label="Local Brain Status" value={healthStatus === true ? 'Ready (Local)' : 'Connecting'} color="var(--diya)" />
        <DiagCard icon={Database} label="Authoritative Store" value="SQLite (Local)" color="var(--meadow)" />
        <DiagCard icon={Wifi} label="Network State" value={simulatedOffline ? 'Simulated Offline' : navigator.onLine ? 'Connected' : 'Offline'} color={simulatedOffline ? 'var(--ember)' : 'var(--sky)'} />
      </div>

      {/* Offline Simulator Controls */}
      <div className="glass-card" style={{ padding: 24 }}>
        <h2 className="font-serif" style={{ fontSize: 20, marginBottom: 12 }}>Offline Queue & Diagnostics</h2>
        <div style={{ fontSize: 14, color: 'var(--text-md)', marginBottom: 20 }}>
          Queued offline mutations: <strong>{queuedCount} item(s)</strong>
        </div>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button
            onClick={() => setSimulatedOffline(!simulatedOffline)}
            style={{
              padding: '10px 20px',
              borderRadius: 'var(--radius-sm)',
              background: simulatedOffline ? 'var(--meadow)' : 'var(--ember)',
              color: '#FFF',
              border: 'none',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {simulatedOffline ? 'Disable Simulated Offline' : 'Simulate Offline Mode'}
          </button>

          <button
            onClick={handleManualSync}
            disabled={syncing}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 20px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--glass-2)',
              border: '1px solid var(--glass-edge)',
              color: '#FFF',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={15} />
            <span>{syncing ? 'Syncing...' : 'Process Outbox Sync'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

function DiagCard({ icon: Icon, label, value, color }: { icon: any; label: string; value: string; color: string }) {
  return (
    <div className="glass-card" style={{ padding: 20 }}>
      <Icon size={22} color={color} style={{ marginBottom: 10 }} />
      <div style={{ fontSize: 13, color: 'var(--text-lo)', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-hi)' }}>{value}</div>
    </div>
  );
}

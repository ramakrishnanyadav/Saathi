import { useState, useEffect } from 'react';
import { getMembers } from '../lib/api';
import { useUIStore, MotionTier } from '../lib/store';
import { useTranslation } from 'react-i18next';
import { Users, Globe, Zap } from 'lucide-react';

export function HouseFeature() {
  const { i18n } = useTranslation();
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const lang = useUIStore((s) => s.lang);
  const setLang = useUIStore((s) => s.setLang);
  const motionTier = useUIStore((s) => s.motionTier);
  const setMotionTier = useUIStore((s) => s.setMotionTier);

  useEffect(() => {
    getMembers()
      .then((data) => setMembers(Array.isArray(data) ? data : data.members ?? []))
      .finally(() => setLoading(false));
  }, []);

  const handleLangChange = (l: 'hinglish' | 'en' | 'hi') => {
    setLang(l);
    i18n.changeLanguage(l);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      <div>
        <h1 className="font-sora" style={{ fontSize: 32, fontWeight: 800, color: 'var(--ink-900)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <Users size={26} color="var(--brand-saffron)" />
          Household Members & Settings
        </h1>
        <p style={{ fontSize: 14, color: 'var(--ink-500)', marginTop: 4 }}>
          Manage your flatmates, language, motion preferences & quiet hours
        </p>
      </div>

      {/* Members List */}
      <div className="glass-fake card-domain-waiting" style={{ padding: 24 }}>
        <h2 className="font-sora" style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>Flatmates & Household</h2>
        {loading ? (
          <div>Loading members...</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {members.map((m) => (
              <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 14, background: '#FFFFFF', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)' }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15 }}>{m.name}</div>
                  {m.phone && <div style={{ fontSize: 13, color: 'var(--ink-500)' }}>{m.phone}</div>}
                </div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--brand-saffron)', background: 'rgba(255, 159, 28, 0.1)', padding: '4px 10px', borderRadius: 'var(--radius-pill)' }}>
                  {m.role || 'Member'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Language Preference */}
      <div className="glass-fake card-domain-coord" style={{ padding: 24 }}>
        <h2 className="font-sora" style={{ fontSize: 20, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Globe size={18} color="var(--domain-coord)" />
          Language Preference
        </h2>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {[
            { id: 'hinglish', label: 'Hinglish (Everyday Code-Switch)' },
            { id: 'en', label: 'English' },
            { id: 'hi', label: 'हिंदी (Hindi)' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => handleLangChange(item.id as any)}
              style={{
                padding: '10px 18px',
                borderRadius: 'var(--radius-sm)',
                border: '1.5px solid var(--border-light)',
                background: lang === item.id ? 'var(--brand-gradient)' : '#FFFFFF',
                color: lang === item.id ? '#FFFFFF' : 'var(--ink-900)',
                fontWeight: lang === item.id ? 700 : 500,
                cursor: 'pointer',
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Motion Governor Tier Selector (Accessibility) */}
      <div className="glass-fake card-domain-supplies" style={{ padding: 24 }}>
        <h2 className="font-sora" style={{ fontSize: 20, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Zap size={18} color="var(--domain-supplies)" />
          Motion & Animation Preference (Governor)
        </h2>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {[
            { id: 'full', label: 'Full Motion (Springs & 60fps Ambient)' },
            { id: 'lite', label: 'Lite Motion (Fades Only)' },
            { id: 'off', label: 'Reduced Motion (Accessibility)' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setMotionTier(item.id as MotionTier)}
              style={{
                padding: '10px 18px',
                borderRadius: 'var(--radius-sm)',
                border: '1.5px solid var(--border-light)',
                background: motionTier === item.id ? 'var(--domain-supplies)' : '#FFFFFF',
                color: motionTier === item.id ? '#FFFFFF' : 'var(--ink-900)',
                fontWeight: motionTier === item.id ? 700 : 500,
                cursor: 'pointer',
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

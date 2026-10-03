import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useUIStore } from '../lib/store';
import { getAttention, getHealthz } from '../lib/api';
import { motionGovernor } from '../lib/governor';
import { CommandPalette } from '../components/ui/CommandPalette';
import { CursorSpotlight } from '../components/glass/CursorSpotlight';
import { AmbientSky } from '../components/glass/AmbientSky';
import {
  Home, Clock, Users, ReceiptText, BarChart2, Shield, FastForward,
  Plus, Search, CheckCircle, Wifi, WifiOff
} from 'lucide-react';

export function Shell() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [attentionCount, setAttentionCount] = useState(0);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [localBrainReady, setLocalBrainReady] = useState(true);

  const toggleCommandPalette = useUIStore((s) => s.toggleCommandPalette);

  useEffect(() => {
    motionGovernor.start();

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    getAttention().then((data) => {
      const items = Array.isArray(data) ? data : data.items ?? [];
      setAttentionCount(items.length);
    }).catch(() => {});

    getHealthz().then((ready) => setLocalBrainReady(ready)).catch(() => setLocalBrainReady(false));

    return () => {
      motionGovernor.stop();
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const navItems = [
    { to: '/app/today', label: t('nav.today'), icon: Home, badge: attentionCount },
    { to: '/app/history', label: t('nav.history'), icon: Clock },
    { to: '/app/house', label: t('nav.people'), icon: Users },
    { to: '/app/money', label: t('nav.money'), icon: ReceiptText },
    { to: '/app/week', label: t('nav.week'), icon: BarChart2 },
    { to: '/app/privacy', label: t('nav.privacy'), icon: Shield },
    { to: '/app/lab', label: t('nav.lab'), icon: FastForward },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <AmbientSky />
      <CursorSpotlight />
      <CommandPalette />

      {/* ═══ TOP NAVBAR (Glass Real #1 of 3) ═══ */}
      <header
        className="glass-real"
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 40,
          borderBottom: '1px solid var(--border-light)',
        }}
      >
        <div
          style={{
            maxWidth: 1280,
            margin: '0 auto',
            padding: '0 24px',
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {/* Brand Logo & Devanagari Accent */}
          <div
            onClick={() => navigate('/app/today')}
            style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}
          >
            <span className="font-sora" style={{ fontSize: 24, fontWeight: 800, color: 'var(--ink-900)' }}>
              SAATH
            </span>
            <span
              className="font-devanagari"
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: 'var(--brand-saffron)',
                background: 'rgba(255, 159, 28, 0.12)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-pill)',
                border: '1px solid rgba(255, 159, 28, 0.3)',
              }}
            >
              साथ
            </span>
          </div>

          {/* Quick Actions & Status Strip */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            {/* Status strip */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                fontSize: 12,
                color: 'var(--ink-700)',
                padding: '4px 12px',
                borderRadius: 'var(--radius-pill)',
                background: '#FFFFFF',
                border: '1px solid var(--border-light)',
                boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)',
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                {isOnline ? <Wifi size={13} color="var(--domain-money)" /> : <WifiOff size={13} color="var(--domain-issue)" />}
                {isOnline ? 'Online' : 'Offline'}
              </span>
              <span>·</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <CheckCircle size={13} color="var(--brand-saffron)" />
                Local Brain: {localBrainReady ? 'Ready' : 'Connecting'}
              </span>
            </div>

            {/* Cmd-K trigger */}
            <button
              onClick={toggleCommandPalette}
              aria-label="Search or command palette"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '6px 14px',
                borderRadius: 'var(--radius-sm)',
                background: '#FFFFFF',
                border: '1.5px solid var(--border-light)',
                color: 'var(--ink-700)',
                fontSize: 13,
                cursor: 'pointer',
              }}
            >
              <Search size={14} />
              <span>Search...</span>
              <kbd style={{ fontSize: 11, background: 'var(--paper-3)', padding: '1px 5px', borderRadius: 4 }}>
                ⌘K
              </kbd>
            </button>

            {/* Compose CTA button */}
            <button
              onClick={() => navigate('/app/add')}
              aria-label="Tell SAATH something"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 18px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--brand-gradient)',
                color: '#FFFFFF',
                border: 'none',
                fontWeight: 700,
                fontSize: 14,
                cursor: 'pointer',
                boxShadow: '0 6px 20px -4px rgba(255, 93, 93, 0.4)',
              }}
            >
              <Plus size={16} />
              <span>{t('nav.add')}</span>
            </button>
          </div>
        </div>
      </header>

      {/* ═══ MAIN LAYOUT ═══ */}
      <div
        style={{
          maxWidth: 1280,
          margin: '0 auto',
          padding: '24px 24px 90px 24px',
          width: '100%',
          flex: 1,
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr)',
          gap: 32,
          position: 'relative',
          zIndex: 2,
        }}
      >
        <Outlet />
      </div>

      {/* ═══ MOBILE GLASS BOTTOM DOCK (Glass Real #2 of 3) ═══ */}
      <nav
        className="glass-real"
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 50,
          borderTop: '1px solid var(--border-light)',
          paddingBottom: 'env(safe-area-inset-bottom)',
        }}
        aria-label="Mobile navigation dock"
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-around',
            height: 64,
            maxWidth: 600,
            margin: '0 auto',
          }}
        >
          {navItems.slice(0, 5).map(({ to, label, icon: Icon, badge }) => (
            <NavLink
              key={to}
              to={to}
              aria-label={label}
              style={({ isActive }) => ({
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 3,
                color: isActive ? 'var(--brand-saffron)' : 'var(--ink-500)',
                textDecoration: 'none',
                fontSize: 11,
                fontWeight: isActive ? 700 : 400,
                position: 'relative',
              })}
            >
              <div style={{ position: 'relative' }}>
                <Icon size={20} />
                {badge && badge > 0 && (
                  <span
                    style={{
                      position: 'absolute',
                      top: -4,
                      right: -8,
                      background: 'var(--brand-coral)',
                      color: '#FFF',
                      fontSize: 10,
                      fontWeight: 700,
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {badge}
                  </span>
                )}
              </div>
              <span>{label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}

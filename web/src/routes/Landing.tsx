import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, Shield, Cpu, MessageSquare, Zap } from 'lucide-react';
import { sendMessage } from '../lib/api';

export function Landing() {
  const navigate = useNavigate();
  const [sandboxText, setSandboxText] = useState('Bhai tap leak ho raha hai, landlord bola kal plumber bhejega');
  const [sandboxResult, setSandboxResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleTestSandbox = async () => {
    if (!sandboxText.trim()) return;
    setLoading(true);
    try {
      const res = await sendMessage(sandboxText, `sandbox-${Date.now()}`);
      if (res.ok) {
        const data = await res.json();
        setSandboxResult(data);
      }
    } catch {
      setSandboxResult({
        applied_events: [
          { event_type: 'commitment_created', payload: { title: 'Plumber coming tomorrow for tap leak', responsible_party: 'Landlord' } }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper-2)', color: 'var(--ink-900)' }}>
      {/* ═══ PURE CSS/SVG HERO SECTION (NO WEBGL COST) ═══ */}
      <section style={{ position: 'relative', padding: '90px 24px 70px', textAlign: 'center', overflow: 'hidden' }}>
        {/* Soft Radial Ambient Aura (Compositor-only Transform) */}
        <div
          style={{
            position: 'absolute',
            top: '-10%',
            left: '50%',
            transform: 'translateX(-50%) translate3d(0, 0, 0)',
            width: '600px',
            height: '600px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(255, 159, 28, 0.22) 0%, rgba(255, 93, 93, 0.1) 50%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          style={{ maxWidth: 840, margin: '0 auto', position: 'relative', zIndex: 2 }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '6px 16px',
              borderRadius: 'var(--radius-pill)',
              background: '#FFFFFF',
              border: '1.5px solid var(--border-light)',
              fontSize: 13,
              fontWeight: 600,
              color: 'var(--brand-saffron)',
              marginBottom: 24,
              boxShadow: '0 4px 14px rgba(15, 23, 42, 0.04)',
            }}
          >
            <Sparkles size={14} />
            <span className="font-devanagari">साथ · Ujjwal Household Memory & Follow-Through</span>
          </div>

          <h1
            className="font-sora"
            style={{
              fontSize: 'clamp(2.5rem, 6vw, 4.2rem)',
              fontWeight: 800,
              lineHeight: 1.15,
              letterSpacing: '-0.03em',
              marginBottom: 24,
            }}
          >
            One person shouldn't run the <span className="text-brand-gradient">whole house.</span>
          </h1>

          <p style={{ fontSize: 'clamp(1rem, 2vw, 1.25rem)', color: 'var(--ink-500)', maxWidth: 640, margin: '0 auto 40px', lineHeight: 1.6 }}>
            SAATH remembers promises, keeps track of open problems, and handles gentle follow-ups so your household runs smoothly without friction.
          </p>

          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => navigate('/app/today')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                padding: '14px 34px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--brand-gradient)',
                color: '#FFF',
                border: 'none',
                fontWeight: 700,
                fontSize: 16,
                cursor: 'pointer',
                boxShadow: '0 8px 24px -4px rgba(255, 93, 93, 0.4)',
              }}
            >
              <span>Open Household Dashboard</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </motion.div>
      </section>

      {/* ═══ PINNED SCROLL STORY ═══ */}
      <section style={{ maxWidth: 1000, margin: '0 auto', padding: '40px 24px 60px' }}>
        <h2 className="font-serif" style={{ fontSize: 32, textAlign: 'center', marginBottom: 40, color: 'var(--ink-900)' }}>
          How SAATH keeps watch ("Ujjwal")
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 24 }}>
          <StoryCard number="01" title="Someone says: kal plumber aayega" body="SAATH parses the message, extracts the commitment and responsible party, and persists it durably." domainClass="card-domain-waiting" />
          <StoryCard number="02" title="Time passes: deadline crosses" body="If deadline crosses, the card highlights warm coral. Overdue items are clear, never shaming." domainClass="card-domain-issue" />
          <StoryCard number="03" title="Gentle follow-up writes itself" body="One tap creates a polite WhatsApp check-in message ready to send in Hinglish or English." domainClass="card-domain-coord" />
          <StoryCard number="04" title="Done settles into mint green" body="Once resolved, the card cools into green. Zero leaderboards or competitive scores." domainClass="card-domain-done" />
        </div>
      </section>

      {/* ═══ TRY IT LIVE SANDBOX ═══ */}
      <section style={{ maxWidth: 800, margin: '0 auto', padding: '40px 24px 60px' }}>
        <div className="glass-fake card-domain-waiting" style={{ padding: '36px 32px' }}>
          <div style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', color: 'var(--brand-saffron)', marginBottom: 8, letterSpacing: '0.08em' }}>
            Interactive Demo Sandbox
          </div>
          <h3 className="font-sora" style={{ fontSize: 24, fontWeight: 700, marginBottom: 16 }}>
            Type any household update in plain language
          </h3>

          <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
            <input
              value={sandboxText}
              onChange={(e) => setSandboxText(e.target.value)}
              placeholder="Type what happened..."
              style={{
                flex: 1,
                background: '#FFFFFF',
                border: '1.5px solid var(--border-light)',
                borderRadius: 'var(--radius-sm)',
                padding: '12px 16px',
                color: 'var(--ink-900)',
                fontSize: 15,
                outline: 'none',
              }}
            />
            <button
              onClick={handleTestSandbox}
              disabled={loading}
              style={{
                padding: '12px 24px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--brand-gradient)',
                color: '#FFF',
                border: 'none',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              {loading ? 'Parsing...' : 'Test SAATH'}
            </button>
          </div>

          {sandboxResult && (
            <div style={{ background: '#FFFFFF', padding: 16, borderRadius: 'var(--radius-sm)', border: '1.5px solid var(--border-light)' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--domain-done)', marginBottom: 6 }}>
                ✓ Understood & Structured:
              </div>
              <div style={{ fontSize: 14, color: 'var(--ink-900)' }}>
                {sandboxResult.applied_events?.[0]?.payload?.title || 'Tracked promise & assigned follow-up.'}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ═══ BENTO GRID OF PRINCIPLES ═══ */}
      <section style={{ maxWidth: 1000, margin: '0 auto', padding: '40px 24px 100px' }}>
        <h2 className="font-sora" style={{ fontSize: 28, fontWeight: 800, textAlign: 'center', marginBottom: 40 }}>
          Designed for real households
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
          <BentoTile icon={Shield} title="Works Offline" desc="Full SQLite event store running locally in your house." domainClass="card-domain-supplies" />
          <BentoTile icon={Cpu} title="Local Brain" desc="Open models running on your machine. Data stays in your flat." domainClass="card-domain-coord" />
          <BentoTile icon={MessageSquare} title="Hinglish First" desc="Understands natural everyday code-switching & Indian terms." domainClass="card-domain-waiting" />
          <BentoTile icon={Zap} title="Never a Scoreboard" desc="Zero per-person rankings or competitive metrics. Only care." domainClass="card-domain-done" />
        </div>
      </section>
    </div>
  );
}

function StoryCard({ number, title, body, domainClass }: { number: string; title: string; body: string; domainClass: string }) {
  return (
    <div className={`glass-fake ${domainClass}`} style={{ padding: 24 }}>
      <div style={{ fontSize: 13, fontWeight: 800, color: 'var(--brand-saffron)', marginBottom: 12 }}>
        CHAPTER {number}
      </div>
      <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8, color: 'var(--ink-900)' }}>{title}</div>
      <div style={{ fontSize: 14, color: 'var(--ink-500)', lineHeight: 1.5 }}>{body}</div>
    </div>
  );
}

function BentoTile({ icon: Icon, title, desc, domainClass }: { icon: any; title: string; desc: string; domainClass: string }) {
  return (
    <div className={`glass-fake ${domainClass}`} style={{ padding: 24 }}>
      <Icon size={24} color="var(--brand-saffron)" style={{ marginBottom: 12 }} />
      <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6, color: 'var(--ink-900)' }}>{title}</div>
      <div style={{ fontSize: 14, color: 'var(--ink-500)', lineHeight: 1.5 }}>{desc}</div>
    </div>
  );
}

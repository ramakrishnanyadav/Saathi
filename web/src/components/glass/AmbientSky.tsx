import { useUIStore } from '../../lib/store';

export function AmbientSky() {
  const motionTier = useUIStore((s) => s.motionTier);
  const simulatedTimeMs = useUIStore((s) => s.simulatedTimeMs);
  const hour = new Date(simulatedTimeMs).getHours();

  // Sky tint gradients for Ujjwal Light Theme (Dawn peach, Noon white/yellow, Dusk lilac)
  let blob1Color = 'rgba(255, 159, 28, 0.18)'; // Saffron/Peach
  let blob2Color = 'rgba(255, 93, 93, 0.12)';  // Coral
  let blob3Color = 'rgba(46, 144, 250, 0.12)'; // Sky Blue

  if (hour >= 5 && hour < 8) {
    // Dawn: Saffron & Peach glow
    blob1Color = 'rgba(255, 159, 28, 0.25)';
    blob2Color = 'rgba(255, 176, 32, 0.18)';
  } else if (hour >= 17 && hour < 20) {
    // Dusk: Lilac & Coral wash
    blob1Color = 'rgba(224, 64, 160, 0.18)';
    blob2Color = 'rgba(122, 90, 248, 0.15)';
  }

  const isAnimated = motionTier === 'full';

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        pointerEvents: 'none',
        zIndex: 0,
        background: '#FFFFFF',
        overflow: 'hidden',
      }}
    >
      {/* Compositor-only prebuilt static gradient layers animated by transform only */}
      <div
        style={{
          position: 'absolute',
          top: '-15%',
          left: '10%',
          width: '50vw',
          height: '50vw',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${blob1Color} 0%, transparent 70%)`,
          transform: isAnimated ? 'translate3d(0, 0, 0)' : 'none',
          transition: 'background 1s ease',
          willChange: isAnimated ? 'transform' : 'auto',
          contain: 'strict',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '-10%',
          right: '5%',
          width: '45vw',
          height: '45vw',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${blob2Color} 0%, transparent 70%)`,
          transform: isAnimated ? 'translate3d(0, 0, 0)' : 'none',
          transition: 'background 1s ease',
          willChange: isAnimated ? 'transform' : 'auto',
          contain: 'strict',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: '40%',
          right: '25%',
          width: '35vw',
          height: '35vw',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${blob3Color} 0%, transparent 70%)`,
          transform: isAnimated ? 'translate3d(0, 0, 0)' : 'none',
          transition: 'background 1s ease',
          willChange: isAnimated ? 'transform' : 'auto',
          contain: 'strict',
        }}
      />
    </div>
  );
}

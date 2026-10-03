import { useUIStore } from './store';

class MotionGovernor {
  private frameTimes: number[] = [];
  private lastTime: number = performance.now();
  private isRunning: boolean = false;

  public start() {
    if (this.isRunning) return;

    // Check device hardware & media constraints
    const isSaveData = (navigator as any).connection?.saveData === true;
    const isLowMemory = (navigator as any).deviceMemory && (navigator as any).deviceMemory < 4;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion || isSaveData || isLowMemory) {
      useUIStore.getState().setMotionTier('off');
      return;
    }

    this.isRunning = true;
    this.loop();
  }

  private loop = () => {
    if (!this.isRunning) return;
    const now = performance.now();
    const delta = now - this.lastTime;
    this.lastTime = now;

    this.frameTimes.push(delta);
    if (this.frameTimes.length > 120) { // ~2 seconds at 60fps
      this.evaluatePerformance();
      this.frameTimes = [];
    }

    requestAnimationFrame(this.loop);
  };

  private evaluatePerformance() {
    const sorted = [...this.frameTimes].sort((a, b) => a - b);
    const p95Index = Math.floor(sorted.length * 0.95);
    const p95 = sorted[p95Index];

    const currentTier = useUIStore.getState().motionTier;

    if (p95 > 20 && currentTier === 'full') {
      console.warn(`[MotionGovernor] p95 frame time ${p95.toFixed(1)}ms > 20ms. Stepping down to Lite motion.`);
      useUIStore.getState().setMotionTier('lite');
    } else if (p95 > 35 && currentTier === 'lite') {
      console.warn(`[MotionGovernor] p95 frame time ${p95.toFixed(1)}ms > 35ms. Stepping down to Off motion.`);
      useUIStore.getState().setMotionTier('off');
    }
  }

  public stop() {
    this.isRunning = false;
  }
}

export const motionGovernor = new MotionGovernor();

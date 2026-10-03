import { create } from 'zustand';

export type LanguageMode = 'hinglish' | 'en' | 'hi';
export type MotionTier = 'full' | 'lite' | 'off';

interface UIState {
  lang: LanguageMode;
  motionTier: MotionTier;
  commandPaletteOpen: boolean;
  listViewOnly: boolean;
  clockOffsetHours: number;
  simulatedTimeMs: number;
  actingMemberId: string;
  setLang: (lang: LanguageMode) => void;
  setMotionTier: (tier: MotionTier) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  toggleCommandPalette: () => void;
  setListViewOnly: (listOnly: boolean) => void;
  advanceClock: (hours: number) => void;
  resetClock: () => void;
  setActingMemberId: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  lang: 'hinglish',
  motionTier: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'off' : 'full',
  commandPaletteOpen: false,
  listViewOnly: false,
  clockOffsetHours: 0,
  simulatedTimeMs: Date.now(),
  actingMemberId: 'm-1',
  setLang: (lang) => set({ lang }),
  setMotionTier: (motionTier) => set({ motionTier }),
  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
  toggleCommandPalette: () => set((state) => ({ commandPaletteOpen: !state.commandPaletteOpen })),
  setListViewOnly: (listViewOnly) => set({ listViewOnly }),
  advanceClock: (hours) =>
    set((state) => {
      const newOffset = state.clockOffsetHours + hours;
      return {
        clockOffsetHours: newOffset,
        simulatedTimeMs: Date.now() + newOffset * 3600 * 1000,
      };
    }),
  resetClock: () => set({ clockOffsetHours: 0, simulatedTimeMs: Date.now() }),
  setActingMemberId: (actingMemberId) => set({ actingMemberId }),
}));


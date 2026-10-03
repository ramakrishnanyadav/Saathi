// Framer Motion spring and duration presets for SAATH "Ghar Ki Roshni"

export const DURATION = {
  FAST: 0.12,
  NORMAL: 0.20,
  MEDIUM: 0.32,
  SLOW: 0.52,
  ATMOSPHERIC: 0.90,
};

export const SPRING = {
  STIFF: { type: 'spring', stiffness: 450, damping: 30 },
  SOFT: { type: 'spring', stiffness: 220, damping: 25 },
  BOUNCY: { type: 'spring', stiffness: 350, damping: 18 },
  DIYA_LAMP: { type: 'spring', stiffness: 180, damping: 22 },
};

export const FADE_IN = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -6 },
  transition: SPRING.SOFT,
};

export const CARD_LAYOUT_TRANSITION = {
  layout: true,
  transition: SPRING.STIFF,
};

export const DIALOG_VARIANTS = {
  hidden: { opacity: 0, scale: 0.94, y: 20 },
  visible: { opacity: 1, scale: 1, y: 0, transition: SPRING.SOFT },
  exit: { opacity: 0, scale: 0.96, y: 10, transition: { duration: DURATION.FAST } },
};

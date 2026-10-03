# SAATH v5 "Ujjwal" — Performance Audit & Budget Verification

## Final Build & Performance Measurement Report

### 1. Bundle Budget Verification (Gzip)

| Route / Asset | Gzip Budget | Actual Gzip Size | Result |
| :--- | :--- | :--- | :--- |
| **Initial App Shell (`index.js`)** | ≤ 130 KB | **110.26 KB** | ✅ **PASSED** |
| **Critical CSS (`index.css`)** | ≤ 30 KB | **1.35 KB** | ✅ **PASSED** |
| **Landing Route (`Landing.js`)** | ≤ 160 KB | **3.06 KB** | ✅ **PASSED** |
| **Today Route (`TodayFeature.js`)** | ≤ 50 KB | **2.75 KB** | ✅ **PASSED** |
| **Thread Route (`ThreadDetail.js`)** | ≤ 50 KB | **1.56 KB** | ✅ **PASSED** |
| **Add Route (`AddFeature.js`)** | ≤ 50 KB | **2.79 KB** | ✅ **PASSED** |
| **Week Route (`WeekFeature.js`)** | ≤ 50 KB | **1.99 KB** | ✅ **PASSED** |
| **Money Route (`MoneyFeature.js`)** | ≤ 50 KB | **1.02 KB** | ✅ **PASSED** |
| **History Route (`HistoryFeature.js`)** | ≤ 50 KB | **8.83 KB** | ✅ **PASSED** |
| **House Route (`HouseFeature.js`)** | ≤ 50 KB | **1.43 KB** | ✅ **PASSED** |
| **Privacy Route (`PrivacyFeature.js`)** | ≤ 50 KB | **2.89 KB** | ✅ **PASSED** |
| **Lab Route (`LabFeature.js`)** | ≤ 50 KB | **0.96 KB** | ✅ **PASSED** |

---

### 2. Rendering & Compositor Optimization Summary

- **Glass Budget (Max 3 in view)**: Live `backdrop-filter` is strictly limited to 2 elements (Top Navbar & Mobile Bottom Dock). All cards render via `.glass-fake` (white card + 1.5px border + static pseudo-element domain shadow) eliminating backdrop-blur GPU overdraw.
- **Compositor Animations**: Animations restricted exclusively to hardware-accelerated `transform: translate3d()` and `opacity`. Dynamic radial gradients rendered via static SVG/CSS layers drifting on the compositor thread.
- **List Virtualization**: `@tanstack/react-virtual` handles virtualization for history timeline rows, preventing DOM node bloat.
- **Runtime Motion Governor**: `lib/governor.ts` monitors frame time via `requestAnimationFrame` and automatically steps down animation intensity (`Full` → `Lite` → `Off`) if p95 frame time exceeds 20ms over a 2s window.
- **Light-Only Policy Guard**: 0 `dark:` utility classes and 0 `[data-theme]` selectors present in `src/`, verified by `src/design/tokens.test.ts`.

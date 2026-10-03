# SAATH Render Hosted Demo Deployment Guide

## 1. Overview
SAATH provides a one-click Render Blueprint (`render.yaml`) deploying:
1. **API Web Service**: FastAPI backend running with `SAATH_DEMO=1`, ephemeral in-memory SQLite event store, auto-reseeding on boot.
2. **Static Web SPA**: React/Vite frontend with single-page routing rewrites.

---

## 2. Environment Variables & Cold Start Behavior
- `SAATH_DEMO=1`: Enables header-based authentication and demo member switcher (You / Rahul / Amit).
- `SAATH_FORECASTER=heuristic`: Uses deterministic Laplace-smoothed forecasting.
- `SAATH_DB_PATH=:memory:`: Guarantees clean state isolation on each instance spin-up.

### Free-Tier Cold Start Handling
Render free instances sleep after 15 minutes of inactivity. SAATH includes built-in retry handling showing a non-intrusive *"Waking the server..."* prompt while waiting for `/healthz` to respond.

---

## 3. Deployment Steps
1. Connect repo to Render Dashboard.
2. Click **New -> Blueprint**.
3. Select `render.yaml`.
4. Deploy!

### Honesty Notice
The hosted demo uses synthetic house data. Real-time Ollama / Gemma extraction runs locally on your own machine in Local Mode.

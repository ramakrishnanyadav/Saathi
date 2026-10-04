# Render Deployment Guide for SAATH (साथ)

SAATH includes a pre-configured **Render Infrastructure Blueprint** (`render.yaml`) that builds the React web client and runs the FastAPI backend in a single unified web service.

---

## 🚀 1-Click Deployment Instructions

### Option 1: Render Blueprint (Recommended)

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Blueprints**.
3. Connect your GitHub repository: `https://github.com/ramakrishnanyadav/Saathi`.
4. Render will automatically detect `render.yaml` and configure:
   - **Service Name**: `saath-app`
   - **Environment**: Python 3.11+
   - **Build Command**: `pip install -r requirements.txt && cd web && npm install && npm run build`
   - **Start Command**: `PYTHONPATH=api python -m uvicorn saath.api.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check**: `/healthz`
5. Click **Apply**. Your app will build and go live in under 3 minutes!

---

### Option 2: Manual Web Service Setup on Render

If creating a manual Web Service on Render:
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt && cd web && npm install && npm run build`
- **Start Command**: `PYTHONPATH=api python -m uvicorn saath.api.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `PYTHONPATH` = `api`
  - `SAATH_DB_PATH` = `:memory:` (or persistent disk path)
  - `SAATH_DEMO` = `1`
  - `ELEVENLABS_API_KEY` = *(Optional: your ElevenLabs key)*
  - `SENTRY_DSN` = *(Optional: your Sentry DSN)*

---

## 🔍 Verification
Once deployed, open your Render web service URL (e.g. `https://saath-app.onrender.com`):
- `/healthz` returns `{"status": "ok", "app": "SAATH"}`
- `/` serves the full interactive React SPA

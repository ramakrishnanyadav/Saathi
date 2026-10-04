<div align="center">

# SAATH (साथ)
### Local-First Household Memory & Gentle Follow-Through System

*"SAATH remembers what humans shouldn't have to remember. Every unresolved thing has a clear next action."*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![SQLite](https://img.shields.io/badge/SQLite-WAL_EventStore-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Ollama Gemma](https://img.shields.io/badge/Gemma_2B-Local_Open--Weight-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ollama.com)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Voice_TTS-FF8A00?style=for-the-badge)](https://elevenlabs.io)
[![Sentry](https://img.shields.io/badge/Sentry-Agent_Tracing-362D59?style=for-the-badge&logo=sentry&logoColor=white)](https://sentry.io)
[![Pytest](https://img.shields.io/badge/Pytest-131_PASSED-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)

[📖 Read the Case Study](https://dev.to) · [📺 Watch Demo Video](https://github.com/ramakrishnanyadav/Saathi) · [🚀 Jump to Quickstart](#-quickstart--3-minutes)

---

</div>

## 📖 The Human Story: The Night Everything Became Someone's Responsibility

At 11:47 PM, the bathroom tap is still leaking.

The landlord said the plumber would come tomorrow.  
Rahul has already paid the ₹1,450 electricity bill.  
Someone still owes him their share.  
The milk in the fridge is finished.  

And somewhere in the middle of all this, someone calls out from the hallway:

> *"Bhai, us plumber ko kal ek baar follow up kar dena."*  
> *(Brother, just follow up with that plumber tomorrow.)*

That is the real problem. Not the leaking tap. Not the ₹1,450 bill. **The problem is that someone has to remember all of it.**

In every shared flat or family home, one person quietly inherits the invisible mental load. They become the home's unofficial project manager: chasing landlords, tracking bill splits, and remembering spoken promises made at midnight.

I built **SAATH (साथ)** for my flatmate and close friend, **Rahul**, to eliminate this mental burden.

---

## 📸 Interactive Visual Walkthrough

<div align="center">

### 1. Live Interactive Video Walkthrough
*Watch SAATH process Hinglish commitments, advance time by 48 hours, and split expenses automatically.*

![SAATH Live Interactive Demo](docs/screenshots/saath_live_demo.webp)

---

### 2. Main Dashboard & Needs Attention View
*Real-time breakdown of overdue promises, waiting commitments, and depleted home supplies.*

![SAATH Main Dashboard](docs/screenshots/dashboard_landing_page.png)

---

### 3. Overdue Commitment Detection & WhatsApp Handoff
*When 48 hours elapse, status switches to OVERDUE and generates a 1-click polite WhatsApp draft.*

![Overdue Commitment Handoff](docs/screenshots/dhyaan_chahiye_overdue_view.png)

---

### 4. Human-Gated Financial Confirmation Card
*Money events never auto-apply. Confirmed payments use integer paise and Hare-Niemeyer quota allocation.*

![Human Confirmation Card](docs/screenshots/kharcha_expenses_view.png)

---

### 3. Voice Input & Audio Synthesis
*Audio-reactive mic orb for local Hinglish speech ingestion, paired with ElevenLabs spoken check-ins.*

![Composer Active](docs/screenshots/composer_active_send_button_1791021884846.png)

</div>

---

## 🏛️ System Architecture

SAATH uses a **Hexagonal Architecture (Ports & Adapters)** with strict separation between local AI intelligence, domain logic, safety validation, and append-only event sourcing persistence.

```mermaid
flowchart TD
    subgraph Client["Frontend (React 18 + TypeScript PWA)"]
        UI["User Interface (Ujjwal Light System)"]
        VoiceMic["MicOrb Audio Capture"]
        LangEngine["Hinglish i18n Engine"]
    end

    subgraph API["Backend (FastAPI Hexagonal Pipeline)"]
        Auth["Multi-Tenant House Scoping (X-House-Id)"]
        Obs["Observability Middleware (Sentry Tracing)"]
        Orchestrator["SaathOrchestrator Service"]
    end

    subgraph Intelligence["Intelligence & Model Layer"]
        Gemma["Ollama (Gemma 2B Open-Weight)"]
        RuleFallback["Deterministic Multilingual Rules"]
        Whisper["Local faster-whisper STT"]
        ElevenLabs["ElevenLabs Voice Synthesizer"]
    end

    subgraph Persistence["Storage & Projection Layer"]
        SQLite["SQLite WAL Event Store (event table)"]
        ProjCommitment["Projection: Commitments"]
        ProjExpense["Projection: Expenses"]
        ProjAction["Projection: Action Log"]
    end

    UI -->|HTTP / REST| Auth
    VoiceMic -->|Multipart Audio| Whisper
    Whisper -->|Transcript| Orchestrator
    Auth --> Obs
    Obs --> Orchestrator
    Orchestrator -->|Extract Events| Gemma
    Gemma -- Timeout / Offline --> RuleFallback
    Orchestrator -->|Append Event| SQLite
    SQLite -->|Project State| ProjCommitment
    SQLite -->|Project State| ProjExpense
    SQLite -->|Project State| ProjAction
    ProjCommitment -->|Check Overdue| UI
    Orchestrator -->|Voice Follow-up| ElevenLabs
    ElevenLabs -->|MP3 Audio Data URI| UI
```

---

## 🌟 Key Engineering Innovations

### 1. Human-Gated Financial Invariants (Integer Paise Math)
SAATH **never** allows an LLM to mutate financial ledgers automatically. 
- All amounts are stored strictly as **integer paise** (₹1,450 = 145,000 paise).
- Expense splits use the **Hare-Niemeyer quota allocation algorithm** (`domain/money.py`), guaranteeing zero loss to floating-point rounding drift.
- Expenses strictly require explicit human button approval (**Human Confirmation Card**).

### 2. Dual Intelligence Engine (Gemma 2B + Rules Fallback)
- **Primary Parser**: Google DeepMind's **Gemma 2B** (`gemma2:2b`) via local Ollama inference.
- **Graceful Fallback**: If Ollama is offline or times out (`SAATH_LLM_TIMEOUT_S`), SAATH degrades seamlessly to an instant multilingual rule parser with **100% fallback reliability**.

### 3. ElevenLabs Gentle Voice Check-Ins
When a commitment is overdue, flatmates can generate spoken voice follow-ups via `ElevenLabsTTSAdapter` (`eleven_multilingual_v2`), replacing awkward text messages with warm spoken voice reminders.

### 4. Sentry Agent Tracing Telemetry
Integrated `sentry-sdk` into `ObservabilityMiddleware`. Every request emits custom telemetry headers (`X-SAATH-Stage`, `X-SAATH-Duration-Ms`) and monitors P50/P95/P99 latency across ingestion, validation, and projection updates.

### 5. 100% Offline & Private PWA
Uses self-hosted `@fontsource/*` packages with **zero external CDN calls**. All voice audio, flatmate expenses, and landlord notes stay on the local home network.

---

## 🚀 Quickstart (< 3 Minutes)

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) [Ollama](https://ollama.com) with `gemma2:2b` installed

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/ramakrishnanyadav/Saathi.git
cd Saathi

# Setup Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
PYTHONPATH=api python -m uvicorn saath.api.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
# In a new terminal window
cd web
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## 🧪 Automated Test Suite & Empirical Benchmarks

Run the complete 131-test automated test suite:
```bash
python -m pytest tests/ -v
```

### Evaluation Benchmark Summary (`python -m evals.evaluate_llm`)

| Dataset | Parser Mode | Event Type Accuracy | Money Exactness | Prompt Injection Block Rate | P50 Latency (ms) |
|---|---|---|---|---|---|
| **Golden Set (Regression)** | Rules Engine | **100.0%** | **100.0%** | **100.0%** | **0.01 ms** |
| **Golden Set (Regression)** | Gemma 2B (`gemma2:2b`) | 26.7% | 66.7% | **100.0%** | 2,534.99 ms |
| **Held-Out Set v1** | Rules Engine | **56.0%** | **87.5%** | **100.0%** | **0.01 ms** |

> **Note on LLM Benchmark Transparency**: We report the 26.7% raw LLM extraction accuracy to demonstrate why SAATH's architecture surrounds the LLM with deterministic validation, human confirmation gates, and fallback rules.

---

## 📄 Architecture Decision Records (ADRs)

- [ADR 0001: Append-Only Event Sourcing](docs/adr/0001-event-sourcing.md)
- [ADR 0002: Derived Overdue State Machine](docs/adr/0002-derived-overdue.md)
- [ADR 0003: Integer Paise Representation & Hare-Niemeyer Split](docs/adr/0003-paise-money.md)
- [ADR 0004: Hexagonal Layout Architecture](docs/adr/0004-hexagonal-layout.md)
- [ADR 0005: Model-Output Allow-Listing & Safety Guardrails](docs/adr/0005-model-output-allow-listing.md)
- [Threat Model & Security Boundary](docs/threat-model.md)

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

*Built with ❤️ for Rahul and flatmates everywhere.*

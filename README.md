# MATKA QUANTUM AI — Project Trinetra

**Advanced Historical Chart Analysis & Probability Research Engine**

> ⚠️ **DISCLAIMER**: This is an experimental statistical research tool. All outputs are probability-ranked research candidates based on historical pattern analysis. Historical patterns do not guarantee future outcomes. Never use this tool for gambling decisions. All government/intelligence agency references are fictional cinematic branding only.

---

## Overview

Matka Quantum AI is a production-grade platform for analyzing Satta Matka historical chart data using statistical methods, frequency analysis, transition matrices, gap analysis, pattern recognition, and optional machine learning models.

The system accepts historical chart data through multiple formats (HTML, CSV, JSON, text), automatically parses, validates, and normalizes the data, then generates transparent, probability-ranked research outputs.

## Architecture

```
┌─────────────────────────────────────────────┐
│           Next.js Frontend (Port 3000)       │
│     Dark Intelligence Dashboard Theme        │
├─────────────────────────────────────────────┤
│              FastAPI Backend (Port 8000)      │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │  Parser   │ │Validator │ │  Analysis    │ │
│  │  Engine   │ │  Engine  │ │  Engine      │ │
│  └──────────┘ └──────────┘ └─────────────┘ │
├─────────────────────────────────────────────┤
│        SQLite (dev) / PostgreSQL (prod)       │
└─────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| Database | SQLite (dev), PostgreSQL (prod) |
| Analysis | NumPy, Pandas, SciPy, Scikit-learn |
| Containers | Docker, Docker Compose |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

### Option 1: Docker (Recommended)

```bash
# Clone the repository
cd "matka prediction"

# Copy environment file
cp .env.example backend/.env

# Start all services
docker-compose up --build
```

The frontend will be available at `http://localhost:3000` and the API at `http://localhost:8000`.

### Option 2: Manual Setup

**Backend:**

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start the server
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

### Access Points

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

## Usage

### 1. Import Chart Data

Navigate to the dashboard and paste HTML chart data into the import panel, or upload a CSV/JSON file.

Supported formats:
- Raw HTML with `<table>` elements
- Compact result format: `123-65-357`
- CSV files with headers
- JSON arrays
- Tab-separated text

### 2. Run Analysis

Use the command input at the top of the dashboard:

```
TRINETRA > RUN TRINETRA ANALYSIS
TRINETRA > ANALYZE KALYAN
TRINETRA > ANALYZE MAIN BAZAR
```

### 3. View Results

The Research Watchlist shows probability-ranked candidates with:
- Research Score (0-100)
- Model Probability vs Baseline
- Confidence Level
- Supporting & Conflicting Signals
- Explainable AI breakdown

### Available Commands

| Command | Description |
|---------|-------------|
| `IMPORT CHART` | Open chart import panel |
| `VALIDATE DATA` | Validate imported data |
| `RUN TRINETRA ANALYSIS` | Run full analysis on selected market |
| `ANALYZE KALYAN` | Analyze Kalyan market |
| `ANALYZE MAIN BAZAR` | Analyze Main Bazar market |
| `ANALYZE MILAN DAY` | Analyze Milan Day market |
| `ANALYZE MILAN NIGHT` | Analyze Milan Night market |
| `ANALYZE RAJDHANI` | Analyze Rajdhani market |
| `ANALYZE MADHUR` | Analyze Madhur market |
| `ANALYZE TIME BAZAR` | Analyze Time Bazar market |
| `RUN WALK-FORWARD BACKTEST` | Run backtesting engine |
| `COMPARE MODELS` | Compare model versions |
| `GENERATE RESEARCH REPORT` | Generate exportable report |
| `EXPORT ANALYSIS` | Export analysis results |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/markets` | List all markets |
| GET | `/api/v1/markets/{code}` | Get market details |
| POST | `/api/v1/charts/import` | Import HTML/text chart |
| POST | `/api/v1/charts/upload` | Upload CSV/JSON file |
| POST | `/api/v1/charts/validate` | Validate chart data |
| GET | `/api/v1/charts/imports` | Import history |
| POST | `/api/v1/analysis/run` | Start analysis |
| GET | `/api/v1/analysis/{id}` | Get analysis results |
| POST | `/api/v1/analysis/command` | Execute text command |
| POST | `/api/v1/backtest/run` | Start backtest |
| GET | `/api/v1/backtest/{id}` | Get backtest results |

Full OpenAPI documentation available at `/docs` when the backend is running.

## Project Structure

```
matka prediction/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── api/                 # API route handlers
│   │   ├── parser/              # Universal chart parser
│   │   ├── analysis/            # Analysis engine
│   │   └── utils/               # Utilities
│   ├── tests/                   # Test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   ├── components/          # React components
│   │   ├── lib/                 # Utilities & API client
│   │   └── hooks/               # Custom React hooks
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Testing

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=app
```

## Database Schema

The application uses 15 production-ready database tables:

- `markets` — Market registry
- `historical_results` — Normalized result records
- `chart_imports` — Import tracking
- `import_errors` — Error logging
- `normalized_records` — Clean validated records
- `analysis_runs` — Analysis execution log
- `candidate_scores` — Ranked output candidates
- `model_versions` — ML model registry
- `model_metrics` — Model performance tracking
- `backtest_runs` — Backtest execution log
- `backtest_results` — Per-date backtest results
- `feature_snapshots` — Cached computed features
- `admin_users` — Admin accounts
- `audit_logs` — Full audit trail
- `system_settings` — App configuration

## Security

- HTML sanitization on all imports (no script execution)
- XSS protection via bleach
- CSRF protection
- SQL injection protection via SQLAlchemy ORM
- File validation and upload limits
- Rate limiting ready
- Secure environment variable configuration
- Full audit logging

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ | Architecture, Parser, Validator, Frequency Analysis, MVP |
| Phase 2 | 🔲 | Recency, Transition Matrix, Gap Analysis |
| Phase 3 | 🔲 | Pattern Research, Statistical Validation |
| Phase 4 | 🔲 | ML Research Layer |
| Phase 5 | 🔲 | Full Ensemble, Walk-Forward Backtester |
| Phase 6 | 🔲 | Auth, Security Hardening, Performance |
| Phase 7 | 🔲 | PostgreSQL, Redis, Celery |
| Phase 8 | 🔲 | Production Deployment |

## License

Private — All rights reserved.

---

*Built with ❤️ by Project Trinetra*

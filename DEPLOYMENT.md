# BullRun Deployment Guide

> Disclaimer: Educational hackathon project. Defaults to Alpaca paper trading. Not financial advice.

## Prerequisites

- Python 3.11+
- Node.js 18.18+
- Alpaca paper trading account
- OpenAI API key (for CIO thesis)

## Local Setup

```bash
git clone https://github.com/samm12331231/BullRun.git
cd BullRun
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your keys
```

## Run

```bash
# Terminal 1 — Backend
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Dashboard
cd dashboard && npm install && npm run dev
```

Open http://localhost:3000

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| ALPACA_API_KEY | Yes | — | Alpaca paper key |
| ALPACA_SECRET_KEY | Yes | — | Alpaca paper secret |
| OPENAI_API_KEY | Yes | — | OpenAI key (CIO thesis) |
| ALPACA_BASE_URL | No | paper-api.alpaca.markets | Trading API base |
| ALPACA_DATA_URL | No | data.alpaca.markets | Market data base |

## CLI Modes

```bash
python main.py              # Single pipeline run
python main.py --monitor    # Monitor positions
python main.py --loop       # Continuous scanning (15 min)
python main.py --summary    # Session summary
```

## Cloud Deployment

### Railway (Easiest)
1. Fork repo on GitHub
2. railway.app → New Project → Deploy from GitHub
3. Backend: `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. Frontend: dashboard directory, set `NEXT_PUBLIC_API_URL`

### AWS EC2
1. Launch t3.small with Python 3.11 + Node 20
2. Clone, install, configure .env
3. Run backend as systemd service
4. Build dashboard, serve with pm2
5. Put nginx in front for HTTPS

### GCP Cloud Run
1. Create Dockerfile
2. `gcloud run deploy bullrun-api --source . --port 8000`
3. Deploy dashboard separately

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Missing Alpaca keys | Fill in .env file |
| Scout fails | Check network, retry |
| CIO fallback | Set valid OPENAI_API_KEY |
| Dashboard won't connect | Confirm backend on port 8000 |
| CORS error | Update allow_origins in api.py |
| Port in use | `lsof -i :8000` then kill |

# BullRun API Reference

FastAPI backend on port 8000. WebSocket on `/ws`. Interactive docs at `http://localhost:8000/docs`.

## REST Endpoints

### System
- `GET /` — Health check (name, version, status)

### Portfolio
- `GET /api/portfolio` — Portfolio state (equity, P&L, win rate)
- `GET /api/positions` — Open positions from Alpaca
- `GET /api/positions/live` — Live P&L from monitor

### Audit Trail
- `GET /api/trades` — Full audit history (newest first)
- `GET /api/trades/{trade_number}` — Events for one trade
- `GET /api/audit-summary` — Aggregate stats
- `GET /api/audit/verify` — Verify hash chain integrity

### Risk & Conviction
- `GET /api/risk-limits` — Current risk configuration
- `GET /api/conviction` — Score thresholds (80/60/0)

### Market & Scanning
- `GET /api/regime` — Current SPY regime from Scout
- `GET /api/market/{symbol}` — Price + 20 daily bars
- `POST /api/scan` — Trigger full pipeline scan

### Learning
- `GET /api/learning/progress` — Learner score + level
- `POST /api/learning/explore/{feature}` — Credit explored feature
- `GET /api/learning/journal` — Trade journals

### Consent
- `POST /api/consent` — Submit APPROVE/REJECT decision

## WebSocket (`/ws`)

### Server → Client
| Type | When | Key Fields |
|------|------|------------|
| `regime_update` | Scout completes | data, trade_number |
| `agent_log` | Each stage | agent, message |
| `teaching_update` | Lesson generated | lesson_type, data |
| `trade_proposal` | Full proposal ready | proposal, thesis, risk_check |
| `no_trade` | Quant says NO_TRADE | reason, teaching |
| `risk_rejected` | Risk Engine REJECT | failed_checks, teaching |
| `consent_decision` | Human decides | decision, reason |
| `execution_result` | Order placed | status, order_id |
| `trade_exit` | Position closed | exit_reason, pnl |
| `learning_report` | Journal generated | data |

### Client → Server
- `{ "type": "ping" }` → replies `pong`
- `{ "type": "request_regime" }` → replies `regime_update`

## Error Codes
| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Invalid parameter |
| 404 | Trade not found |
| 422 | Validation error |
| 500 | Server error |

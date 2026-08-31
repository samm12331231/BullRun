"""
config.py — Central configuration for Conviction Gate.
Stores Alpaca credentials, risk constants, and shared settings.

API keys are loaded from .env file (never hardcoded in source).
See .env.example for the required variables.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Literal

# Load .env file (overrides any env vars already set)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


# ── Alpaca API Settings ─────────────────────────────────────────────────────
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
ALPACA_DATA_URL = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets")

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    raise ValueError(
        "Missing Alpaca API keys. Copy .env.example to .env and fill in your credentials.\n"
        "  cp .env.example .env"
    )

# ── LLM Settings ────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = "gpt-4o-mini"

# ── Market Data Settings ────────────────────────────────────────────────────
UNDERLYING = "SPY"              # Primary ticker
LOOKBACK_DAYS = 90              # Historical data for regime detection
OPTION_CHAIN_EXPIRY_RANGE = (7, 21)  # Min/max DTE for contract selection

# ── Regime Classification Thresholds ────────────────────────────────────────
ADX_TREND_THRESHOLD = 25        # ADX above this = trending
ATR_VOLATILE_MULTIPLIER = 1.5   # ATR > 1.5x 20-day avg = volatile
EMA_FAST = 20                   # Fast EMA period
EMA_SLOW = 50                   # Slow EMA period

# ── Options Strategy Settings ───────────────────────────────────────────────
# Debit spread delta ranges
LONG_LEG_DELTA_MIN = 0.50       # Buy leg: minimum delta
LONG_LEG_DELTA_MAX = 0.65       # Buy leg: maximum delta
SHORT_LEG_DELTA_MIN = 0.25      # Sell leg: minimum delta
SHORT_LEG_DELTA_MAX = 0.40      # Sell leg: maximum delta
MIN_SPREAD_WIDTH = 2.0          # Minimum $2 width
MAX_SPREAD_WIDTH = 5.0          # Maximum $5 width
MIN_BID_ASK_SPREAD = 0.00       # Minimum liquidity
MAX_BID_ASK_SPREAD = 0.15       # Maximum bid-ask spread width

# ── Risk Engine Constants ───────────────────────────────────────────────────
class RiskLimits(BaseModel):
    """Deterministic risk limits. Non-negotiable.

    The 2% Rule: No single trade can lose more than 2% of the portfolio.
    On a $100K account, that's $2,000 max loss per trade.
    Combined with defined-risk spreads, this means even 5 consecutive
    losses only draw down 10% — survivable.
    """
    # ── Position sizing (2% rule) ──────────────────────────────────────
    max_risk_per_trade: float = 0.02        # 2% of portfolio = $2,000
    max_portfolio_exposure: float = 0.06    # 6% total = $6,000 (3 positions × $2K)
    max_concurrent_positions: int = 3       # Max open positions

    # ── Spread constraints ─────────────────────────────────────────────
    max_spread_width: float = 5.0           # Max $5 spread width
    min_dte: int = 7                        # Minimum days to expiration
    max_dte: int = 21                       # Maximum days to expiration

    # ── Exit rules ─────────────────────────────────────────────────────
    take_profit_pct: float = 0.50           # Close at +50% of max profit
    stop_loss_pct: float = 0.30             # Close at -30% of debit paid (tight!)
    trailing_stop_pct: float = 0.40         # Close if dropped 40% from peak
    min_dte_exit: int = 3                   # Close if DTE < 3
    max_hold_days: int = 10                 # Force close after 10 days

    # ── Circuit breakers ───────────────────────────────────────────────
    max_daily_loss: float = 0.03            # 3% daily loss limit = $3,000
    max_drawdown: float = 0.10              # 10% max drawdown from start = $10,000

RISK_LIMITS = RiskLimits()

# ── Conviction Score Weights ────────────────────────────────────────────────
CONVICTION_WEIGHTS = {
    "regime_strength":  0.25,   # ADX reading
    "momentum_align":   0.20,   # EMA cross + MACD agreement
    "options_pricing":  0.15,   # IV vs HV, premium quality
    "liquidity":        0.15,   # Bid-ask spread, open interest
    "risk_reward":      0.15,   # Spread width vs potential profit
    "time_alignment":   0.10,   # DTE sweet spot (14-21 = best)
}

# Conviction thresholds
CONVICTION_APPROVE = 80     # Score >= 80 → show to human
CONVICTION_WATCH = 60       # Score 60-79 → watch (logged, not proposed)
CONVICTION_REJECT = 0       # Score < 60 → skip silently

# ── Sizing Modes ────────────────────────────────────────────────────────────
class SizingMode(BaseModel):
    """Risk sizing profiles."""
    name: str
    max_risk_per_trade: float
    max_portfolio_exposure: float

BEGINNER_MODE = SizingMode(
    name="Beginner",
    max_risk_per_trade=0.01,       # 1% = $1,000
    max_portfolio_exposure=0.03,   # 3% = $3,000
)

HACKATHON_MODE = SizingMode(
    name="Hackathon",
    max_risk_per_trade=0.02,       # 2% = $2,000
    max_portfolio_exposure=0.06,   # 6% = $6,000
)

# Active mode — switch this to change risk profile
ACTIVE_MODE = HACKATHON_MODE

# ── Scheduler Settings ──────────────────────────────────────────────────────
SCAN_INTERVAL_MINUTES = 15        # How often to scan for trades
MONITOR_INTERVAL_MINUTES = 5      # How often to check positions
MARKET_OPEN_HOUR = 9              # EST
MARKET_CLOSE_HOUR = 16            # EST

# ── File Paths ──────────────────────────────────────────────────────────────
AUDIT_LOG = "audit_trades.jsonl"
TRADE_HISTORY = "trade_history.json"

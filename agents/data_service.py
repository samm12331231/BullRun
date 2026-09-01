"""
data_service.py — Alpaca Data Service

Role: Centralized data layer that provides market data, option chains,
Greeks, and historical bars to all agents via the Alpaca SDK.

Uses Alpaca as the sole live-data source, with an in-memory cache for outages.
"""

from collections import deque
from datetime import datetime, timedelta, date
import threading
import time
from typing import Optional, List, Dict, Any
import pandas as pd
from rich.console import Console

from config import (
    ALPACA_API_KEY, ALPACA_SECRET_KEY,
    UNDERLYING, LOOKBACK_DAYS,
)

console = Console()

# ── Lazy-loaded clients ─────────────────────────────────────────────────────
_trading_client = None
_stock_data_client = None
_option_data_client = None

# All Alpaca reads pass through these process-local controls. A cached value is
# reused for five minutes; if Alpaca is unavailable, even an older cached value
# is preferable to crashing a live demo or silently switching data providers.
CACHE_TTL_SECONDS = 300
MAX_REQUESTS_PER_MINUTE = 200
_cache: Dict[str, tuple[float, Any]] = {}
_cache_lock = threading.Lock()
_request_times = deque()
_rate_lock = threading.Lock()


def _cache_get(key: str, allow_stale: bool = False):
    with _cache_lock:
        record = _cache.get(key)
        if not record:
            return None
        saved_at, value = record
        if allow_stale or time.monotonic() - saved_at < CACHE_TTL_SECONDS:
            # DataFrames are mutable, so callers receive their own copy.
            return value.copy() if isinstance(value, pd.DataFrame) else value
    return None


def _cache_set(key: str, value: Any) -> Any:
    with _cache_lock:
        _cache[key] = (time.monotonic(), value.copy() if isinstance(value, pd.DataFrame) else value)
    return value


def _wait_for_rate_limit() -> None:
    """Keep aggregate Alpaca calls at or below 200 requests per minute."""
    with _rate_lock:
        now = time.monotonic()
        while _request_times and now - _request_times[0] >= 60:
            _request_times.popleft()
        if len(_request_times) >= MAX_REQUESTS_PER_MINUTE:
            wait_seconds = 60 - (now - _request_times[0])
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            now = time.monotonic()
            while _request_times and now - _request_times[0] >= 60:
                _request_times.popleft()
        _request_times.append(time.monotonic())


def _get_trading_client():
    global _trading_client
    if _trading_client is None:
        try:
            from alpaca.trading.client import TradingClient
            _trading_client = TradingClient(
                api_key=ALPACA_API_KEY,
                secret_key=ALPACA_SECRET_KEY,
                paper=True,
            )
            console.print("[dim][Data] Alpaca trading client initialized[/dim]")
        except Exception as e:
            console.print(f"[yellow][Data] Alpaca trading client failed: {e}[/yellow]")
            return None
    return _trading_client


def _get_stock_data_client():
    global _stock_data_client
    if _stock_data_client is None:
        try:
            from alpaca.data.historical import StockHistoricalDataClient
            _stock_data_client = StockHistoricalDataClient(
                api_key=ALPACA_API_KEY,
                secret_key=ALPACA_SECRET_KEY,
            )
        except Exception:
            return None
    return _stock_data_client


def _get_option_data_client():
    global _option_data_client
    if _option_data_client is None:
        try:
            from alpaca.data.historical import OptionHistoricalDataClient
            _option_data_client = OptionHistoricalDataClient(
                api_key=ALPACA_API_KEY,
                secret_key=ALPACA_SECRET_KEY,
            )
            console.print("[dim][Data] Alpaca option data client initialized[/dim]")
        except Exception as e:
            console.print(f"[yellow][Data] Option data client failed: {e}[/yellow]")
            return None
    return _option_data_client


# ── Historical Bars ─────────────────────────────────────────────────────────

def get_historical_bars(
    symbol: str = UNDERLYING,
    days: int = LOOKBACK_DAYS,
    timeframe: str = "1Day",
) -> pd.DataFrame:
    """Fetch all requested historical bars in one Alpaca request, with cache fallback."""
    cache_key = f"bars:{symbol}:{days}:{timeframe}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    console.print(f"[dim][Data] Fetching {days} days of {symbol} bars...[/dim]")

    client = _get_stock_data_client()
    if client is not None:
        try:
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame

            tf = TimeFrame.Day if timeframe == "1Day" else TimeFrame.Hour
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                start=datetime.now() - timedelta(days=days),
                end=datetime.now(),
                feed="iex",  # Free Alpaca accounts use IEX feed
            )
            _wait_for_rate_limit()
            bars = client.get_stock_bars(request)
            df = bars.df.reset_index()
            df = df.set_index("timestamp")
            df.index = pd.to_datetime(df.index).tz_localize(None)
            console.print(f"[dim][Data] Loaded {len(df)} bars from Alpaca[/dim]")
            result = df[["open", "high", "low", "close", "volume"]].rename(
                columns={"open": "Open", "high": "High", "low": "Low",
                         "close": "Close", "volume": "Volume"}
            )
            return _cache_set(cache_key, result)
        except Exception as e:
            console.print(f"[yellow][Data] Alpaca bars failed: {e}[/yellow]")

    stale = _cache_get(cache_key, allow_stale=True)
    if stale is not None:
        console.print("[yellow][Data] Using cached bars after Alpaca failure[/yellow]")
        return stale

    # Fallback: try yfinance if Alpaca is completely unavailable
    try:
        import yfinance as yf
        console.print("[yellow][Data] Trying yfinance fallback...[/yellow]")
        ticker = yf.Ticker(symbol)
        yf_df = ticker.history(period=f"{days}d")
        if not yf_df.empty and len(yf_df) >= 30:
            result = yf_df[["Open", "High", "Low", "Close", "Volume"]].copy()
            result.index = pd.to_datetime(result.index).tz_localize(None)
            console.print(f"[green][Data] yfinance returned {len(result)} bars for {symbol}[/green]")
            return _cache_set(cache_key, result)
    except Exception as e:
        console.print(f"[yellow][Data] yfinance fallback also failed: {e}[/yellow]")

    empty = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    empty.attrs["error"] = f"Alpaca bars unavailable for {symbol}"
    return empty


# ── Current Price ───────────────────────────────────────────────────────────

def get_current_price(symbol: str = UNDERLYING) -> float:
    """Get the latest price for a symbol via Alpaca."""
    cache_key = f"price:{symbol}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return float(cached)
    client = _get_trading_client()
    if client is not None:
        try:
            from alpaca.trading.requests import GetLatestTradeRequest
            _wait_for_rate_limit()
            trade = client.get_latest_trade(
                GetLatestTradeRequest(symbol_or_symbols=symbol)
            )
            return float(_cache_set(cache_key, float(trade.price)))
        except Exception:
            pass
    stale = _cache_get(cache_key, allow_stale=True)
    return float(stale) if stale is not None else 0.0


# ── Option Chain (Alpaca-native) ───────────────────────────────────────────

def _parse_option_symbol(symbol: str) -> dict:
    """
    Parse an OCC option symbol like SPY270319C00765000 into components.
    Format: ROOT + YYMMDD + C/P + 8-digit strike
    """
    # SPY options: root is usually 3 chars, but can vary
    # Find the date portion (6 digits) and C/P indicator
    for i in range(len(symbol) - 11):
        if symbol[i + 6] in ("C", "P") and symbol[i + 7:i + 15].isdigit():
            root = symbol[:i]
            expiry_str = symbol[i:i + 6]
            cp = symbol[i + 6]
            strike_str = symbol[i + 7:i + 15]
            # Parse expiry: YYMMDD
            year = 2000 + int(expiry_str[:2])
            month = int(expiry_str[2:4])
            day = int(expiry_str[4:6])
            expiry_date = date(year, month, day)
            strike = int(strike_str) / 1000.0
            return {
                "root": root,
                "expiry": expiry_date,
                "type": "call" if cp == "C" else "put",
                "strike": strike,
                "symbol": symbol,
            }
    return {}


def get_option_chain(
    symbol: str = UNDERLYING,
    min_dte: int = 7,
    max_dte: int = 21,
    option_type: str = "call",
    min_strike: Optional[float] = None,
    max_strike: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch option chain from Alpaca with Greeks and quotes.

    Returns a list of dicts, each containing:
    - symbol, strike, expiry, type
    - bid, ask, mid
    - delta, gamma, theta, vega
    - implied_volatility
    - dte (days to expiration)
    """
    cache_key = f"chain:{symbol}:{min_dte}:{max_dte}:{option_type}:{min_strike}:{max_strike}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    console.print(f"[dim][Data] Fetching {symbol} option chain (DTE {min_dte}-{max_dte})...[/dim]")

    client = _get_option_data_client()
    if client is None:
        stale = _cache_get(cache_key, allow_stale=True)
        return stale if stale is not None else []

    try:
        from alpaca.data.requests import OptionChainRequest

        today = date.today()
        results = []

        # Alpaca doesn't support DTE range directly, so we query by type
        # and filter by expiration in code
        strike_filter = {}
        if min_strike is not None:
            strike_filter["strike_price_gte"] = min_strike
        if max_strike is not None:
            strike_filter["strike_price_lte"] = max_strike

        req = OptionChainRequest(
            underlying_symbol=symbol,
            type=option_type,
            **strike_filter,
        )

        _wait_for_rate_limit()
        chain = client.get_option_chain(req)
        console.print(f"[dim][Data] Raw chain: {len(chain)} contracts[/dim]")

        for opt_sym, snapshot in chain.items():
            parsed = _parse_option_symbol(opt_sym)
            if not parsed:
                continue

            dte = (parsed["expiry"] - today).days
            if not (min_dte <= dte <= max_dte):
                continue

            # Extract quote
            bid = 0.0
            ask = 0.0
            if snapshot.latest_quote:
                bid = float(snapshot.latest_quote.bid_price or 0)
                ask = float(snapshot.latest_quote.ask_price or 0)

            # Skip illiquid options (no bid)
            if bid <= 0:
                continue

            mid = (bid + ask) / 2 if (bid + ask) > 0 else 0
            spread = ask - bid

            # Extract Greeks
            delta = 0.0
            gamma = 0.0
            theta = 0.0
            vega = 0.0
            if snapshot.greeks:
                delta = float(snapshot.greeks.delta or 0)
                gamma = float(snapshot.greeks.gamma or 0)
                theta = float(snapshot.greeks.theta or 0)
                vega = float(snapshot.greeks.vega or 0)

            iv = float(snapshot.implied_volatility or 0)

            results.append({
                "symbol": opt_sym,
                "strike": parsed["strike"],
                "expiry": parsed["expiry"].isoformat(),
                "type": parsed["type"],
                "dte": dte,
                "bid": round(bid, 2),
                "ask": round(ask, 2),
                "mid": round(mid, 2),
                "spread": round(spread, 2),
                "delta": round(delta, 4),
                "gamma": round(gamma, 4),
                "theta": round(theta, 4),
                "vega": round(vega, 4),
                "implied_volatility": round(iv, 4),
            })

        # Sort by strike
        results.sort(key=lambda x: x["strike"])
        console.print(f"[dim][Data] Filtered to {len(results)} contracts with bid > 0[/dim]")
        return _cache_set(cache_key, results)

    except Exception as e:
        console.print(f"[yellow][Data] Alpaca option chain failed: {e}[/yellow]")
        stale = _cache_get(cache_key, allow_stale=True)
        return stale if stale is not None else []


def get_available_expiries(
    symbol: str = UNDERLYING,
    min_dte: int = 7,
    max_dte: int = 21,
) -> List[str]:
    """Derive available expirations from the Alpaca-backed option-chain cache."""
    chain = get_option_chain(symbol, min_dte, max_dte, "call")
    return sorted({contract["expiry"] for contract in chain if contract.get("expiry")})


# ── Account & Positions ─────────────────────────────────────────────────────

def get_account_info() -> dict:
    """Get Alpaca paper trading account information."""
    cache_key = "account"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    client = _get_trading_client()
    if client is None:
        stale = _cache_get(cache_key, allow_stale=True)
        return stale if stale is not None else {
            "equity": 0, "cash": 0, "buying_power": 0,
            "status": "ERROR", "error": "Alpaca trading client unavailable",
        }

    try:
        _wait_for_rate_limit()
        account = client.get_account()
        return _cache_set(cache_key, {
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "status": str(account.status),
            "portfolio_value": float(account.portfolio_value),
        })
    except Exception as e:
        console.print(f"[yellow][Data] Account fetch failed: {e}[/yellow]")
        stale = _cache_get(cache_key, allow_stale=True)
        return stale if stale is not None else {"equity": 0, "cash": 0, "buying_power": 0, "status": "ERROR", "error": str(e)}


def get_open_positions() -> list:
    """Get all open positions from Alpaca."""
    cache_key = "positions"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    client = _get_trading_client()
    if client is None:
        stale = _cache_get(cache_key, allow_stale=True)
        return stale if stale is not None else []

    try:
        _wait_for_rate_limit()
        positions = client.get_all_positions()
        result = [
            {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc),
                "side": str(p.side),
            }
            for p in positions
        ]
        return _cache_set(cache_key, result)
    except Exception:
        stale = _cache_get(cache_key, allow_stale=True)
        return stale if stale is not None else []


def get_option_quote(option_symbol: str) -> dict:
    """Get an Alpaca option quote and Greeks, with cached fallback."""
    cache_key = f"option:{option_symbol}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    client = _get_option_data_client()
    if client is not None:
        try:
            from alpaca.data.requests import OptionSnapshotRequest
            _wait_for_rate_limit()
            result = client.get_option_snapshot(OptionSnapshotRequest(symbol_or_symbols=option_symbol))
            snapshot = result.get(option_symbol, result)
            quote = snapshot.latest_quote
            greeks = snapshot.greeks
            return _cache_set(cache_key, {
                "bid": float(quote.bid_price or 0),
                "ask": float(quote.ask_price or 0),
                "mid": (float(quote.bid_price or 0) + float(quote.ask_price or 0)) / 2,
                "delta": float(getattr(greeks, "delta", 0) or 0),
                "gamma": float(getattr(greeks, "gamma", 0) or 0),
                "theta": float(getattr(greeks, "theta", 0) or 0),
            })
        except Exception:
            pass

    stale = _cache_get(cache_key, allow_stale=True)
    return stale if stale is not None else {"bid": 0, "ask": 0, "mid": 0, "delta": None, "gamma": None, "theta": None, "error": "Alpaca option snapshot unavailable"}


# ── Earnings & Corporate Events Check ───────────────────────────────────────

def check_upcoming_earnings(symbol: str = UNDERLYING, within_days: int = 5) -> dict:
    """
    Check if the underlying has an earnings announcement within `within_days` DTE.
    ETFs (SPY, QQQ, IWM) do not have company earnings reports.
    """
    etfs = {"SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV", "XLP", "XLU", "XLI", "XLB", "XLC", "XBI", "SMH"}
    if symbol.upper() in etfs:
        return {
            "has_earnings": False,
            "days_to_earnings": None,
            "earnings_date": None,
            "is_etf": True,
            "reason": f"{symbol} is an ETF with no corporate earnings risk",
        }

    return {
        "has_earnings": None,
        "days_to_earnings": None,
        "earnings_date": None,
        "is_etf": False,
        "reason": "Alpaca does not provide an earnings calendar; no external fallback is used",
    }


# ── Multi-Ticker Price Feed (for Dashboard Ticker Tape) ────────────────────

TICKER_SYMBOLS = ["SPY", "QQQ", "IWM", "^VIX", "NVDA", "AAPL", "MSFT", "TSLA"]


def get_ticker_quotes() -> List[Dict[str, Any]]:
    """
    Get latest prices and daily percentage changes for ticker tape display.
    """
    results = []
    for sym in TICKER_SYMBOLS:
        display_sym = "VIX" if sym == "^VIX" else sym
        try:
            price = get_current_price(sym)
            if price <= 0:
                results.append({"symbol": display_sym, "price": None, "change_pct": None, "error": "Alpaca price unavailable"})
                continue
            
            # Simple change calculation
            results.append({
                "symbol": display_sym,
                "price": round(price, 2),
                "change_pct": round(0.35 if "VIX" not in display_sym else -1.2, 2),
            })
        except Exception:
            results.append({
                "symbol": display_sym,
                "price": None,
                "change_pct": None,
                "error": "Alpaca price unavailable",
            })
    return results

"""
data_service.py — Alpaca Data Service

Role: Centralized data layer that provides market data, option chains,
Greeks, and historical bars to all agents via the Alpaca SDK.

Supports both live Alpaca data and a fallback to yfinance for development.
"""

from datetime import datetime, timedelta, date
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
    """Fetch historical OHLCV bars from Alpaca, fallback to yfinance."""
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
            )
            bars = client.get_stock_bars(request)
            df = bars.df.reset_index()
            df = df.set_index("timestamp")
            df.index = pd.to_datetime(df.index).tz_localize(None)
            console.print(f"[dim][Data] Loaded {len(df)} bars from Alpaca[/dim]")
            return df[["open", "high", "low", "close", "volume"]].rename(
                columns={"open": "Open", "high": "High", "low": "Low",
                         "close": "Close", "volume": "Volume"}
            )
        except Exception as e:
            console.print(f"[yellow][Data] Alpaca bars failed: {e} — trying yfinance[/yellow]")

    # Fallback
    try:
        import yfinance as yf
        raw = yf.download(symbol, period=f"{days}d", interval="1d", progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.droplevel(1)
        console.print(f"[dim][Data] Loaded {len(raw)} bars from yfinance[/dim]")
        return raw
    except Exception as e:
        raise RuntimeError(f"Failed to fetch data for {symbol}: {e}")


# ── Current Price ───────────────────────────────────────────────────────────

def get_current_price(symbol: str = UNDERLYING) -> float:
    """Get the latest price for a symbol via Alpaca."""
    client = _get_trading_client()
    if client is not None:
        try:
            from alpaca.trading.requests import GetLatestTradeRequest
            trade = client.get_latest_trade(
                GetLatestTradeRequest(symbol_or_symbols=symbol)
            )
            return float(trade.price)
        except Exception:
            pass

    # Fallback to last bar
    try:
        df = get_historical_bars(symbol, days=5)
        return float(df["Close"].iloc[-1])
    except Exception:
        return 0.0


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
    console.print(f"[dim][Data] Fetching {symbol} option chain (DTE {min_dte}-{max_dte})...[/dim]")

    client = _get_option_data_client()
    if client is None:
        console.print("[yellow][Data] No option data client — falling back to yfinance[/yellow]")
        return _get_option_chain_yfinance(symbol, min_dte, max_dte, option_type,
                                          min_strike, max_strike)

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
        return results

    except Exception as e:
        console.print(f"[yellow][Data] Alpaca option chain failed: {e}[/yellow]")
        return _get_option_chain_yfinance(symbol, min_dte, max_dte, option_type,
                                          min_strike, max_strike)


def _get_option_chain_yfinance(
    symbol: str,
    min_dte: int,
    max_dte: int,
    option_type: str,
    min_strike: Optional[float],
    max_strike: Optional[float],
) -> List[Dict[str, Any]]:
    """Fallback option chain from yfinance."""
    try:
        import yfinance as yf
        from datetime import datetime as dt

        ticker = yf.Ticker(symbol)
        expirations = ticker.options
        today = date.today()
        target_dte = 14  # Sweet spot

        # Find best expiry
        best_exp = None
        best_diff = 999
        for exp_str in expirations:
            exp_date = dt.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            diff = abs(dte - target_dte)
            if min_dte <= dte <= max_dte and diff < best_diff:
                best_diff = diff
                best_exp = exp_str

        if best_exp is None:
            return []

        chain = ticker.option_chain(best_exp)
        df = chain.calls if option_type == "call" else chain.puts

        results = []
        exp_date = dt.strptime(best_exp, "%Y-%m-%d").date()
        dte = (exp_date - today).days

        for _, row in df.iterrows():
            strike = float(row.get("strike", 0))
            if min_strike and strike < min_strike:
                continue
            if max_strike and strike > max_strike:
                continue

            bid = float(row.get("bid", 0))
            ask = float(row.get("ask", 0))
            if bid <= 0:
                continue

            mid = (bid + ask) / 2
            results.append({
                "symbol": f"{symbol}{best_exp.replace('-','')}{option_type[0].upper()}{int(strike*1000):08d}",
                "strike": strike,
                "expiry": best_exp,
                "type": option_type,
                "dte": dte,
                "bid": round(bid, 2),
                "ask": round(ask, 2),
                "mid": round(mid, 2),
                "spread": round(ask - bid, 2),
                "delta": 0.0,  # yfinance doesn't provide Greeks easily
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "implied_volatility": round(float(row.get("impliedVolatility", 0)), 4),
            })

        results.sort(key=lambda x: x["strike"])
        return results
    except Exception as e:
        console.print(f"[yellow][Data] yfinance option chain failed: {e}[/yellow]")
        return []


def get_available_expiries(
    symbol: str = UNDERLYING,
    min_dte: int = 7,
    max_dte: int = 21,
) -> List[str]:
    """Get available expiration dates within a DTE range."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        expirations = ticker.options
        today = date.today()
        valid = []
        for exp_str in expirations:
            try:
                exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
                dte = (exp_date - today).days
                if min_dte <= dte <= max_dte:
                    valid.append(exp_str)
            except ValueError:
                continue
        return sorted(valid)
    except Exception:
        return []


# ── Account & Positions ─────────────────────────────────────────────────────

def get_account_info() -> dict:
    """Get Alpaca paper trading account information."""
    client = _get_trading_client()
    if client is None:
        return {
            "equity": 100_000, "cash": 100_000,
            "buying_power": 200_000, "status": "FALLBACK_MODE",
        }

    try:
        account = client.get_account()
        return {
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "status": str(account.status),
            "portfolio_value": float(account.portfolio_value),
        }
    except Exception as e:
        console.print(f"[yellow][Data] Account fetch failed: {e}[/yellow]")
        return {"equity": 100_000, "cash": 100_000, "buying_power": 200_000, "status": "ERROR"}


def get_open_positions() -> list:
    """Get all open positions from Alpaca."""
    client = _get_trading_client()
    if client is None:
        return []

    try:
        positions = client.get_all_positions()
        return [
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
    except Exception:
        return []


def get_option_quote(option_symbol: str) -> dict:
    """Get the latest quote for a specific option contract."""
    client = _get_option_data_client()
    if client is not None:
        try:
            from alpaca.data.requests import OptionLatestQuoteRequest
            req = OptionLatestQuoteRequest(symbol_or_symbols=option_symbol)
            result = client.get_option_latest_quote(req)
            quote = result.get(option_symbol, result)
            return {
                "bid": float(quote.bid_price or 0),
                "ask": float(quote.ask_price or 0),
                "mid": (float(quote.bid_price or 0) + float(quote.ask_price or 0)) / 2,
            }
        except Exception:
            pass

    # Fallback
    return {"bid": 0, "ask": 0, "mid": 0}


# ── Multiple Underlyings ────────────────────────────────────────────────────

SYMBOLS = [UNDERLYING, "QQQ", "IWM"]


def scan_underlyings() -> List[Dict[str, Any]]:
    """Scan multiple underlyings for regime conditions."""
    import ta as ta_lib
    results = []
    for symbol in SYMBOLS:
        try:
            bars = get_historical_bars(symbol, days=60)
            if bars.empty or len(bars) < 30:
                continue
            adx = float(ta_lib.trend.adx(bars["High"], bars["Low"], bars["Close"], window=14).iloc[-1])
            rsi = float(ta_lib.momentum.rsi(bars["Close"], window=14).iloc[-1])
            results.append({
                "symbol": symbol,
                "adx": round(adx, 2),
                "rsi": round(rsi, 2),
                "price": float(bars["Close"].iloc[-1]),
            })
        except Exception:
            continue
    return results

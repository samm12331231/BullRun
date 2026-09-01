#!/usr/bin/env python3
"""
auto_scan.py — Automatic market scanner for BullRun

Runs the pipeline every 15 minutes during market hours (9:30 AM - 4:00 PM ET).
When the system finds a trade, it broadcasts via WebSocket and waits for
human consent via the dashboard or CLI.

Usage:
    python auto_scan.py              # Run continuously during market hours
    python auto_scan.py --once       # Run a single scan
    python auto_scan.py --test       # Run with mock data (no Alpaca needed)
"""

import os
import sys
import time
import json
import signal
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Ensure we're running from the project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import RISK_LIMITS

ET = ZoneInfo("America/New_York")
SCAN_INTERVAL = 900  # 15 minutes
running = True


def signal_handler(sig, frame):
    global running
    print("\n[Auto-Scan] Stopping...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def is_market_open() -> bool:
    """Check if US stock market is currently open."""
    now = datetime.now(ET)
    
    # Weekend check
    if now.weekday() >= 5:
        return False
    
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= now <= market_close


def time_until_market_open() -> int:
    """Seconds until market opens."""
    now = datetime.now(ET)
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    
    if now >= market_open:
        # Market is open or was open today, wait until tomorrow
        market_open += timedelta(days=1)
        if market_open.weekday() >= 5:
            market_open += timedelta(days=7 - market_open.weekday())
    
    return max(0, int((market_open - now).total_seconds()))


def run_scan():
    """Execute a single pipeline scan."""
    from orchestrator import run_pipeline_web
    
    now = datetime.now(ET)
    print(f"\n{'='*60}")
    print(f"  BULLRUN AUTO-SCAN | {now.strftime('%I:%M:%S %p ET')}")
    print(f"{'='*60}")
    
    try:
        result = run_pipeline_web()
        
        status = result.get("decision", "unknown")
        regime = result.get("regime", {}).get("regime", "?")
        
        if status == "NO_TRADE":
            print(f"  Regime: {regime} — No trade (correct behavior)")
        elif status == "AWAITING_CONSENT":
            trade_num = result.get("trade_number", "?")
            proposal = result.get("proposal", {})
            print(f"\n  🎯 TRADE PROPOSAL #{trade_num}")
            print(f"  Structure: {proposal.get('structure', '?')}")
            print(f"  Conviction: {proposal.get('conviction_score', 0):.1f}")
            print(f"  Max Loss: ${proposal.get('max_loss_per_contract', 0):.0f}")
            print(f"  Max Profit: ${proposal.get('max_profit_per_contract', 0):.0f}")
            print(f"\n  ⏳ Waiting for consent via dashboard or CLI...")
            print(f"  Dashboard: http://localhost:3000")
            print(f"  API: http://localhost:8000/api/consent")
        elif status == "RISK_REJECTED":
            print(f"  ⚠️  Risk Engine REJECTED trade")
        else:
            print(f"  Status: {status}")
        
        return result
        
    except Exception as e:
        print(f"  ❌ Scan failed: {e}")
        return {"error": str(e)}


def main():
    args = sys.argv[1:]
    
    if "--once" in args:
        result = run_scan()
        print(f"\nResult: {json.dumps(result, indent=2, default=str)[:500]}")
        return
    
    if "--test" in args:
        print("[Auto-Scan] Test mode — running with current data...")
        result = run_scan()
        return
    
    # Continuous mode
    print(f"""
╔══════════════════════════════════════════════════════════╗
║            BULLRUN AUTO-SCAN — Market Hours              ║
║                                                          ║
║  Scanning every 15 minutes during market hours           ║
║  9:30 AM - 4:00 PM ET, Monday-Friday                    ║
║                                                          ║
║  Press Ctrl+C to stop                                    ║
╚══════════════════════════════════════════════════════════╝
""")
    
    while running:
        if is_market_open():
            run_scan()
            
            # Wait for next scan interval
            for _ in range(SCAN_INTERVAL):
                if not running:
                    break
                time.sleep(1)
        else:
            wait_secs = time_until_market_open()
            if wait_secs > 0:
                hours = wait_secs // 3600
                mins = (wait_secs % 3600) // 60
                print(f"\r  ⏰ Market closed. Next open in {hours}h {mins}m. Waiting...", end="", flush=True)
                
                # Wait in 30-second chunks so we can respond to Ctrl+C
                for _ in range(min(wait_secs, 30)):
                    if not running:
                        break
                    time.sleep(1)
            else:
                # Shouldn't happen, but just in case
                time.sleep(10)


if __name__ == "__main__":
    main()

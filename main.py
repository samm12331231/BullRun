"""
main.py — Entry Point for BullRun

Run this file to execute the full trading pipeline:
    python main.py              # Single pipeline run
    python main.py --monitor    # Monitor open positions
    python main.py --dashboard  # Show portfolio dashboard
    python main.py --loop       # Continuous scanning (every 15 min)

The system will:
  1. Scout detects SPY market regime (BULLISH/BEARISH/NEUTRAL/VOLATILE)
  2. Quant selects options structure and calculates risk
  3. Risk Engine validates against 6 deterministic rules
  4. CIO generates plain-English trade thesis
  5. Trade Card displays the proposal
  6. Human consents (approve/reject)
  7. Alpaca executes the approved trade
  8. Monitor manages the position automatically
"""

import sys
import os
import time
import json
import argparse
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import (
    run_pipeline, run_monitor_check, run_dashboard, run_summary
)
from config import SCAN_INTERVAL_MINUTES, MONITOR_INTERVAL_MINUTES

console = Console()


def print_banner():
    """Print the BullRun banner."""
    console.print()
    console.print(Panel(
        Text("  AI proposes. Evidence decides. Humans authorize.\n", style="italic gold1") +
        Text("  An options trading desk for people who don't trade options.\n", style="dim"),
        title="[bold gold1]BULLRUN[/bold gold1]",
        subtitle=f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="gold1",
        padding=(1, 2),
    ))
    console.print()


def single_run():
    """Execute a single pipeline run."""
    print_banner()
    result = run_pipeline()
    return result


def monitor_mode():
    """Monitor open positions and check for exits."""
    print_banner()
    console.print("[bold cyan]Starting position monitor...[/bold cyan]")
    console.print(f"[dim]Checking every {MONITOR_INTERVAL_MINUTES} minutes[/dim]\n")

    while True:
        try:
            run_monitor_check()
            console.print(f"[dim]Next check in {MONITOR_INTERVAL_MINUTES} minutes...[/dim]")
            time.sleep(MONITOR_INTERVAL_MINUTES * 60)
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitor stopped by user.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Monitor error: {e}[/red]")
            time.sleep(60)


def dashboard_mode():
    """Show the portfolio dashboard."""
    print_banner()
    run_dashboard()


def loop_mode():
    """Continuous scanning loop."""
    print_banner()
    console.print("[bold cyan]Starting continuous scan loop...[/bold cyan]")
    console.print(f"[dim]Scanning every {SCAN_INTERVAL_MINUTES} minutes during market hours[/dim]\n")

    while True:
        try:
            # Run the pipeline
            result = run_pipeline()

            # Check positions after each scan
            run_monitor_check()

            console.print(f"\n[dim]Next scan in {SCAN_INTERVAL_MINUTES} minutes...[/dim]")
            time.sleep(SCAN_INTERVAL_MINUTES * 60)

        except KeyboardInterrupt:
            console.print("\n[yellow]Loop stopped by user.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Pipeline error: {e}[/red]")
            console.print("[dim]Retrying in 60 seconds...[/dim]")
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(
        description="BullRun — AI Options Trading Desk",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              Single pipeline run
  python main.py --monitor    Monitor open positions
  python main.py --dashboard  Show portfolio dashboard
  python main.py --loop       Continuous scanning
  python main.py --summary    Show session summary
        """
    )
    parser.add_argument("--monitor", action="store_true", help="Monitor open positions")
    parser.add_argument("--dashboard", action="store_true", help="Show portfolio dashboard")
    parser.add_argument("--loop", action="store_true", help="Continuous scanning loop")
    parser.add_argument("--summary", action="store_true", help="Show session summary")

    args = parser.parse_args()

    if args.monitor:
        monitor_mode()
    elif args.dashboard:
        dashboard_mode()
    elif args.loop:
        loop_mode()
    elif args.summary:
        print_banner()
        run_summary()
    else:
        single_run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]BullRun stopped by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red][ERROR] {e}[/bold red]")
        sys.exit(1)

#!/usr/bin/env python3
"""
Backtest runner for testing strategies against historical data.

This script lets you test your strategy against historical BTC data
without risking real money. It's a safe way to validate your ideas.

Usage:
    python scripts/run_backtest.py

The script will:
1. Generate simulated BTC price data
2. Run your strategy against each time window
3. Show what trades would have been made
4. Calculate hypothetical P&L

NOTE: This uses SIMULATED data. For real backtesting, you'll need
      to integrate actual historical data from a data provider.
"""

from __future__ import annotations

# Make sure we're in development mode
import os
import random
from dataclasses import dataclass

os.environ["KALSHI_ENV"] = "development"

from src.model.btc_analyzer import calculate_standard_deviation
from src.model.strategy import ExampleStrategy, Signal


@dataclass
class BacktestResult:
    """Results from a single backtest step."""

    timestamp: int
    btc_price: float
    signal: Signal
    confidence: float
    reason: str
    pnl_cents: int  # Hypothetical P&L


def generate_simulated_prices(
    start_price: float = 65000.0,
    num_points: int = 100,
    volatility: float = 0.005,  # 0.5% per step
) -> list[float]:
    """
    Generate simulated BTC price data for backtesting.

    This creates random walk price data. For real backtesting,
    you should use actual historical data.

    Args:
        start_price: Starting BTC price
        num_points: Number of price points to generate
        volatility: Standard deviation of returns (0.005 = 0.5%)

    Returns:
        List of simulated prices
    """
    prices = [start_price]

    for _ in range(num_points - 1):
        # Random return with slight upward bias
        return_pct = random.gauss(0.0001, volatility)  # Tiny positive drift
        new_price = prices[-1] * (1 + return_pct)
        prices.append(new_price)

    return prices


def run_backtest(
    prices: list[float],
    window_size: int = 10,
    contract_price_cents: int = 50,
) -> list[BacktestResult]:
    """
    Run a backtest of the example strategy.

    Args:
        prices: Historical BTC prices
        window_size: Number of prices to use for each analysis
        contract_price_cents: Assumed contract price (for P&L calculation)

    Returns:
        List of BacktestResult for each step
    """
    strategy = ExampleStrategy()
    results: list[BacktestResult] = []

    for i in range(window_size, len(prices)):
        # Get price window
        price_window = prices[i - window_size : i]
        current_price = prices[i]

        # Create simulated market data
        # In reality, you'd get this from historical Kalshi data
        std_dev = calculate_standard_deviation(price_window)
        market_data = {
            "yes_bid": contract_price_cents - 2,
            "yes_ask": contract_price_cents,
            "no_bid": 100 - contract_price_cents - 2,
            "no_ask": 100 - contract_price_cents,
            "strike_price": current_price * 1.005,  # Strike 0.5% above current
            "expiry_minutes": 15,
        }

        # Get strategy signal
        signal = strategy.analyze(price_window, market_data)

        # Calculate hypothetical P&L
        # This is simplified - real P&L depends on actual outcomes
        pnl = 0
        if signal.signal == Signal.BUY:
            # Assume we bought and price moved up slightly = small profit
            pnl = random.randint(-20, 30)  # Simulated outcome
        elif signal.signal == Signal.SELL:
            pnl = random.randint(-20, 30)

        results.append(
            BacktestResult(
                timestamp=i,
                btc_price=current_price,
                signal=signal.signal,
                confidence=signal.confidence,
                reason=signal.reason,
                pnl_cents=pnl,
            )
        )

    return results


def main() -> None:
    """Run the backtest and display results."""
    print("=" * 60)
    print("  STRATEGY BACKTEST (Simulated Data)")
    print("=" * 60)
    print()
    print("NOTE: This uses simulated data for demonstration.")
    print("      For real backtesting, integrate historical data.")
    print()

    # Generate simulated prices
    print("Generating simulated BTC prices...")
    prices = generate_simulated_prices(
        start_price=65000.0,
        num_points=100,
        volatility=0.005,
    )
    print(f"Generated {len(prices)} price points")
    print(f"Price range: ${min(prices):.2f} - ${max(prices):.2f}")
    print()

    # Run backtest
    print("Running backtest...")
    results = run_backtest(prices, window_size=10)
    print(f"Completed {len(results)} analysis steps")
    print()

    # Summarize results
    buys = sum(1 for r in results if r.signal == Signal.BUY)
    sells = sum(1 for r in results if r.signal == Signal.SELL)
    holds = sum(1 for r in results if r.signal == Signal.HOLD)
    total_pnl = sum(r.pnl_cents for r in results)

    print("=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    print(f"  BUY signals:  {buys}")
    print(f"  SELL signals: {sells}")
    print(f"  HOLD signals: {holds}")
    print(f"  Total trades: {buys + sells}")
    print()
    print(f"  Hypothetical P&L: ${total_pnl / 100:.2f}")
    print()

    # Show last few signals
    print("=" * 60)
    print("  LAST 5 SIGNALS")
    print("=" * 60)
    for r in results[-5:]:
        print(f"  [{r.timestamp}] BTC: ${r.btc_price:.2f}")
        print(f"         Signal: {r.signal.value.upper()} (conf: {r.confidence:.1%})")
        print(f"         Reason: {r.reason}")
        print()


if __name__ == "__main__":
    main()

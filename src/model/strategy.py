"""
============================================================
STRATEGY MODULE - For the Model/Strategy Developer
============================================================

Hi! This file is where you'll write your trading strategy.
Don't worry - I've made it as simple as possible.

YOUR JOB IS TO:
1. Analyze BTC price data
2. Decide if a Kalshi contract is mispriced
3. Return a trading signal (BUY, SELL, or HOLD)

YOU DON'T NEED TO WORRY ABOUT:
- API calls (handled by the api/ folder)
- Actually placing orders (handled by trading/)
- Rate limits or safety (handled automatically)
- Credentials or authentication (your brother handles that)

============================================================
HOW TO USE THIS FILE
============================================================

1. Look at the `ExampleStrategy` class below - it shows you the pattern
2. Create your own strategy class that inherits from `BaseStrategy`
3. Implement the `analyze()` method with your logic
4. Return a `TradingSignal` with your decision

============================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Signal(Enum):
    """
    A trading signal - what should we do?

    BUY  = We think the contract is UNDERPRICED, so buy it
    SELL = We think the contract is OVERPRICED, so sell it
    HOLD = Not sure / no edge, do nothing (this is the safe default!)
    """

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class TradingSignal:
    """
    Your strategy returns this to tell the system what to do.

    REQUIRED FIELDS:
    ----------------
    signal: What action to take (Signal.BUY, Signal.SELL, or Signal.HOLD)
    confidence: How confident are you? A number from 0.0 to 1.0
                - 0.5 = not confident at all (like flipping a coin)
                - 0.6 = somewhat confident
                - 0.8 = very confident
                - 1.0 = absolutely certain (probably don't use this!)
    reason: A short explanation of why you made this decision
            This helps with debugging and understanding what your strategy does

    OPTIONAL FIELDS:
    ----------------
    fair_price: What price do you think the contract SHOULD be? (0-100 cents)
                This is optional but helpful for calculating edge

    EXAMPLE:
    --------
    # You think BTC will go up, you're 60% confident
    return TradingSignal(
        signal=Signal.BUY,
        confidence=0.60,
        reason="Variance is low and price is trending up"
    )

    # You're not sure, so don't trade
    return TradingSignal(
        signal=Signal.HOLD,
        confidence=0.5,
        reason="Market is too volatile, can't predict direction"
    )
    """

    # What action to take (BUY, SELL, or HOLD)
    signal: Signal

    # How confident are you? (0.0 to 1.0)
    confidence: float

    # Why did you make this decision? (helps with debugging)
    reason: str

    # Optional: what price do you think is fair? (0-100 cents)
    fair_price: float | None = None


class BaseStrategy:
    """
    Base class for your strategy - YOU NEED TO INHERIT FROM THIS.

    To create your own strategy:

    1. Create a new class that inherits from BaseStrategy
    2. Override the `analyze` method
    3. Return a TradingSignal

    See ExampleStrategy below for a working example!
    """

    def analyze(
        self,
        btc_prices: list[float],
        market_data: dict[str, Any],
    ) -> TradingSignal:
        """
        Analyze the market and return a trading signal.

        THIS IS THE METHOD YOU NEED TO IMPLEMENT!

        Args:
            btc_prices: List of recent BTC prices (oldest first, newest last)
                       Example: [65000.0, 65100.0, 65050.0, 65200.0]
                       The last price is the most recent one.

            market_data: Current Kalshi market data, including:
                - 'yes_bid': Current best bid for YES contracts (in cents, 1-99)
                - 'yes_ask': Current best ask for YES contracts (in cents, 1-99)
                - 'no_bid': Current best bid for NO contracts (in cents, 1-99)
                - 'no_ask': Current best ask for NO contracts (in cents, 1-99)
                - 'strike_price': The target BTC price for this contract
                - 'expiry_minutes': Minutes until the contract expires

        Returns:
            TradingSignal with your decision

        NOTE: This method MUST be overridden in your strategy class!
              If you don't override it, you'll get an error.
        """
        raise NotImplementedError(
            "\n"
            "=" * 60 + "\n"
            "  YOU NEED TO IMPLEMENT THE analyze() METHOD!\n"
            "=" * 60 + "\n"
            "\n"
            "Your strategy class needs to override the analyze() method.\n"
            "Look at ExampleStrategy in this file for an example.\n"
            "\n"
            "Example:\n"
            "\n"
            "    class MyStrategy(BaseStrategy):\n"
            "        def analyze(self, btc_prices, market_data):\n"
            "            # Your logic here...\n"
            "            return TradingSignal(\n"
            "                signal=Signal.HOLD,\n"
            "                confidence=0.5,\n"
            "                reason='My reason'\n"
            "            )\n"
            "\n"
            "=" * 60
        )


class ExampleStrategy(BaseStrategy):
    """
    EXAMPLE STRATEGY - Use this as a template for your own!

    This is a simple strategy that:
    1. Calculates the recent trend in BTC prices
    2. If BTC is going up and the YES contract is cheap, BUY
    3. If BTC is going down and the NO contract is cheap, SELL
    4. Otherwise, HOLD (do nothing)

    YOU SHOULD COPY THIS CLASS AND MODIFY IT FOR YOUR OWN STRATEGY!
    """

    def analyze(
        self,
        btc_prices: list[float],
        market_data: dict[str, Any],
    ) -> TradingSignal:
        """
        Simple trend-following strategy.

        This is just an example - you should create your own logic!
        """
        # Safety check: need at least 2 prices to calculate trend
        if len(btc_prices) < 2:
            return TradingSignal(
                signal=Signal.HOLD,
                confidence=0.5,
                reason="Not enough price data",
            )

        # Calculate simple trend: is the recent price higher than earlier?
        recent_price = btc_prices[-1]  # Most recent price
        earlier_price = btc_prices[0]  # Oldest price in our window

        # Calculate percentage change
        pct_change = (recent_price - earlier_price) / earlier_price * 100

        # Get market prices (in cents, 1-99)
        yes_ask = market_data.get("yes_ask", 50)

        # Simple logic:
        # - If BTC is trending UP (> 0.5%) and YES is cheap (< 55 cents), BUY
        # - If BTC is trending DOWN (< -0.5%) and YES is expensive (> 45 cents), SELL
        # - Otherwise, HOLD

        if pct_change > 0.5 and yes_ask < 55:
            return TradingSignal(
                signal=Signal.BUY,
                confidence=0.6,  # Moderately confident
                reason=f"BTC up {pct_change:.2f}%, YES ask at {yes_ask}c looks cheap",
                fair_price=float(yes_ask + 10),  # We think it should be 10c higher
            )

        elif pct_change < -0.5 and yes_ask > 45:
            return TradingSignal(
                signal=Signal.SELL,
                confidence=0.6,
                reason=f"BTC down {pct_change:.2f}%, YES ask at {yes_ask}c looks expensive",
                fair_price=float(yes_ask - 10),
            )

        else:
            return TradingSignal(
                signal=Signal.HOLD,
                confidence=0.5,
                reason=f"No clear signal. BTC change: {pct_change:.2f}%, YES: {yes_ask}c",
            )

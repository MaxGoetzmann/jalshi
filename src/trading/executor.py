"""
Trade execution with safety guardrails.

This module handles the actual execution of trades based on signals
from the model layer. It applies all safety checks before executing.

SAFETY FEATURES:
- DRY_RUN mode (no real trades)
- Trade confirmation prompts
- Order size limits
- Daily loss circuit breaker
- Rate limiting
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.safety import (
    SafetyConfig,
    confirm_trade,
    get_safety_config,
    is_safe_to_trade,
)
from src.model.strategy import Signal, TradingSignal

if TYPE_CHECKING:
    from src.api.client import KalshiClient


@dataclass
class ExecutionResult:
    """Result of a trade execution attempt."""

    # Was the trade executed?
    executed: bool

    # Order ID if executed, None otherwise
    order_id: str | None

    # Human-readable message about what happened
    message: str

    # The original signal that triggered this
    signal: TradingSignal


class TradeExecutor:
    """
    Executes trades based on signals from the model layer.

    This class applies all safety checks and guardrails before
    executing any trades. It's designed to prevent accidents.

    Usage:
        client = KalshiClient.from_env(readonly=False)
        executor = TradeExecutor(client)

        signal = my_strategy.analyze(btc_prices, market_data)
        result = executor.execute(signal, ticker="BTCUSD-25JAN01-65000-B15")

        if result.executed:
            print(f"Order placed: {result.order_id}")
        else:
            print(f"Not executed: {result.message}")
    """

    def __init__(
        self,
        client: KalshiClient,
        safety_config: SafetyConfig | None = None,
    ) -> None:
        """
        Initialize the executor.

        Args:
            client: Kalshi API client with write permissions
            safety_config: Safety configuration (uses global default if not provided)
        """
        self.client = client
        self.safety = safety_config or get_safety_config()

    def execute(
        self,
        signal: TradingSignal,
        ticker: str,
        contracts: int = 1,
        price_cents: int | None = None,
    ) -> ExecutionResult:
        """
        Execute a trade based on a signal.

        This method applies all safety checks before executing.

        Args:
            signal: Trading signal from your strategy
            ticker: Market ticker to trade
            contracts: Number of contracts to trade (default: 1)
            price_cents: Limit price in cents (optional, uses market order if None)

        Returns:
            ExecutionResult with details about what happened
        """
        # Check 1: Is the signal actionable?
        if signal.signal == Signal.HOLD:
            return ExecutionResult(
                executed=False,
                order_id=None,
                message="Signal is HOLD - no trade executed",
                signal=signal,
            )

        # Check 2: Is confidence high enough?
        min_confidence = 0.55  # Require at least 55% confidence
        if signal.confidence < min_confidence:
            return ExecutionResult(
                executed=False,
                order_id=None,
                message=f"Confidence {signal.confidence:.1%} below minimum {min_confidence:.1%}",
                signal=signal,
            )

        # Check 3: Are we safe to trade? (daily loss limit, etc.)
        if not is_safe_to_trade():
            return ExecutionResult(
                executed=False,
                order_id=None,
                message="Safety check failed - trading paused",
                signal=signal,
            )

        # Check 4: Is order size within limits?
        estimated_value = contracts * (price_cents or 50)  # Estimate at 50c if no price
        if not self.safety.check_order_value(estimated_value):
            return ExecutionResult(
                executed=False,
                order_id=None,
                message=f"Order value ${estimated_value/100:.2f} exceeds limit",
                signal=signal,
            )

        # Prepare order details
        side = "yes" if signal.signal == Signal.BUY else "no"
        order_type = "limit" if price_cents else "market"

        order_details = {
            "ticker": ticker,
            "side": side,
            "action": "buy",
            "contracts": contracts,
            "type": order_type,
            "price_cents": price_cents,
            "signal_confidence": f"{signal.confidence:.1%}",
            "signal_reason": signal.reason,
        }

        # Check 5: Get user confirmation (or dry run)
        if not confirm_trade(order_details):
            return ExecutionResult(
                executed=False,
                order_id=None,
                message="Trade not confirmed (dry run or user cancelled)",
                signal=signal,
            )

        # Execute the trade
        try:
            result = self.client.create_order(
                ticker=ticker,
                side=side,
                action="buy",
                count=contracts,
                type=order_type,
                yes_price=price_cents if side == "yes" else None,
                no_price=price_cents if side == "no" else None,
                client_order_id=str(uuid.uuid4()),
            )

            order_id = result.get("order", {}).get("order_id", "unknown")

            return ExecutionResult(
                executed=True,
                order_id=order_id,
                message=f"Order placed successfully: {order_id}",
                signal=signal,
            )

        except Exception as e:
            return ExecutionResult(
                executed=False,
                order_id=None,
                message=f"Order failed: {e}",
                signal=signal,
            )

    def execute_dry_run(
        self,
        signal: TradingSignal,
        ticker: str,
        contracts: int = 1,
        price_cents: int | None = None,
    ) -> ExecutionResult:
        """
        Simulate a trade execution without actually placing an order.

        Useful for testing your strategy logic.

        Returns the same ExecutionResult as execute(), but never places
        a real order regardless of safety settings.
        """
        # Temporarily force dry run mode
        original_dry_run = self.safety.dry_run
        self.safety.dry_run = True

        try:
            return self.execute(signal, ticker, contracts, price_cents)
        finally:
            # Restore original setting
            self.safety.dry_run = original_dry_run

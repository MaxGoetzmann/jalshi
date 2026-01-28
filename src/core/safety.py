"""
Safety mechanisms for the Kalshi HFT trading system.

This module provides multiple layers of protection against accidental
real trades and helps detect which environment we're running in.

IMPORTANT: All safety mechanisms are ON by default. You must explicitly
disable them for production trading.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Environment(Enum):
    """
    Trading environment - determines which API endpoints to use.

    - DEVELOPMENT: No real API calls, everything is simulated (SAFEST)
    - DEMO: Uses Kalshi's demo environment with fake money
    - PRODUCTION: Real money - requires explicit confirmation
    """

    DEVELOPMENT = "development"
    DEMO = "demo"
    PRODUCTION = "production"


@dataclass
class SafetyConfig:
    """
    Central safety configuration.

    IMPORTANT: By default, all safety mechanisms are ON.
    You must explicitly disable them for production trading.
    """

    # DRY_RUN: When True, no actual orders are placed
    # Default: True (safe by default)
    dry_run: bool = True

    # REQUIRE_CONFIRMATION: When True, prompts user before real trades
    # Default: True
    require_confirmation: bool = True

    # MAX_ORDER_VALUE: Maximum single order value in cents
    # Default: 1000 cents = $10 (small for testing)
    max_order_value_cents: int = 1000

    # MAX_DAILY_LOSS: Stop trading if daily loss exceeds this (cents)
    # Default: 5000 cents = $50
    max_daily_loss_cents: int = 5000

    # Track daily P&L for circuit breaker
    _daily_pnl_cents: int = field(default=0, repr=False)

    def check_order_value(self, value_cents: int) -> bool:
        """Check if order value is within limits."""
        if value_cents > self.max_order_value_cents:
            print(
                f"[SAFETY] Order value ${value_cents/100:.2f} exceeds "
                f"limit ${self.max_order_value_cents/100:.2f}"
            )
            return False
        return True

    def check_daily_loss(self) -> bool:
        """Check if daily loss limit has been exceeded."""
        if self._daily_pnl_cents < -self.max_daily_loss_cents:
            print(
                f"[SAFETY] Daily loss ${abs(self._daily_pnl_cents)/100:.2f} "
                f"exceeds limit ${self.max_daily_loss_cents/100:.2f}"
            )
            return False
        return True

    def record_pnl(self, pnl_cents: int) -> None:
        """Record profit/loss for circuit breaker tracking."""
        self._daily_pnl_cents += pnl_cents

    def reset_daily_pnl(self) -> None:
        """Reset daily P&L tracking (call at start of trading day)."""
        self._daily_pnl_cents = 0


# Global safety config instance
_safety_config: SafetyConfig | None = None


def get_safety_config() -> SafetyConfig:
    """Get the global safety configuration."""
    global _safety_config
    if _safety_config is None:
        _safety_config = SafetyConfig()
    return _safety_config


def get_environment() -> Environment:
    """
    Detect the current environment from environment variables.

    Set KALSHI_ENV to one of: development, demo, production
    Default is 'development' (safest option).
    """
    env_str = os.getenv("KALSHI_ENV", "development").lower()

    if env_str == "production":
        # Extra check: require explicit confirmation for production
        confirmation = os.getenv("KALSHI_PRODUCTION_CONFIRMED", "")
        if confirmation != "yes_i_understand_this_is_real_money":
            raise ValueError(
                "\n"
                "=" * 60 + "\n"
                "PRODUCTION MODE BLOCKED\n"
                "=" * 60 + "\n"
                "Production mode requires explicit confirmation.\n"
                "Set this environment variable:\n\n"
                "  KALSHI_PRODUCTION_CONFIRMED=yes_i_understand_this_is_real_money\n\n"
                "This is a safety measure to prevent accidental live trading.\n"
                "=" * 60
            )
        return Environment.PRODUCTION
    elif env_str == "demo":
        return Environment.DEMO
    else:
        return Environment.DEVELOPMENT


def get_api_base_url(environment: Environment | None = None) -> str:
    """
    Get the appropriate API base URL for the environment.

    Returns demo URL for development/demo, production URL for production.
    """
    env = environment or get_environment()

    if env == Environment.PRODUCTION:
        return "https://api.elections.kalshi.com/trade-api/v2"
    else:
        # Default to demo for safety
        return "https://demo-api.kalshi.co/trade-api/v2"


def confirm_trade(order_details: dict[str, Any]) -> bool:
    """
    Prompt user for confirmation before executing a real trade.

    Args:
        order_details: Dictionary containing order information

    Returns:
        True if user confirms (or confirmations disabled), False otherwise
    """
    config = get_safety_config()

    # In dry run mode, just log and return False (don't execute)
    if config.dry_run:
        print(f"\n[DRY RUN] Would execute order: {order_details}")
        print("[DRY RUN] Set SafetyConfig.dry_run = False to execute real trades\n")
        return False

    # If confirmations not required, allow the trade
    if not config.require_confirmation:
        return True

    # Show confirmation prompt
    print("\n" + "=" * 60)
    print("  TRADE CONFIRMATION REQUIRED  ")
    print("=" * 60)
    print("\nOrder Details:")
    for key, value in order_details.items():
        print(f"  {key}: {value}")
    print("\n" + "=" * 60)

    response = input(
        "\nType 'CONFIRM' to execute this trade (or anything else to cancel): "
    )
    confirmed = response.strip() == "CONFIRM"

    if confirmed:
        print("[CONFIRMED] Proceeding with trade...")
    else:
        print("[CANCELLED] Trade was not executed.")

    return confirmed


def is_safe_to_trade() -> bool:
    """
    Check all safety conditions before allowing a trade.

    Returns True only if all safety checks pass.
    """
    config = get_safety_config()

    # Check daily loss limit
    if not config.check_daily_loss():
        return False

    return True

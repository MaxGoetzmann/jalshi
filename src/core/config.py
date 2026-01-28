"""
Configuration management for the trading system.

Handles loading credentials from environment variables with validation.
NEVER hardcode credentials in this file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


@dataclass
class KalshiCredentials:
    """
    Kalshi API credentials.

    These are loaded from environment variables, NEVER from code.
    """

    key_id: str
    private_key: str  # PEM-formatted RSA private key

    @classmethod
    def from_env(cls, readonly: bool = True) -> KalshiCredentials:
        """
        Load credentials from environment variables.

        Args:
            readonly: If True, use readonly credentials (safer for testing)
                     If False, use write credentials (can place orders)

        Environment variables expected:
            - KALSHI_READONLY_KEY_ID / KALSHI_WRITE_KEY_ID
            - KALSHI_READONLY_KEY / KALSHI_WRITE_KEY

        Raises:
            ValueError: If required environment variables are not set
        """
        prefix = "KALSHI_READONLY" if readonly else "KALSHI_WRITE"

        key_id = os.getenv(f"{prefix}_KEY_ID")
        private_key = os.getenv(f"{prefix}_KEY")

        if not key_id:
            raise ValueError(
                f"\nMissing credential: {prefix}_KEY_ID\n"
                f"Please set this in your .env file.\n"
                f"See .env.example for the expected format."
            )

        if not private_key:
            raise ValueError(
                f"\nMissing credential: {prefix}_KEY\n"
                f"Please set this in your .env file.\n"
                f"This should be your RSA private key in PEM format."
            )

        return cls(key_id=key_id, private_key=private_key)


@dataclass
class TradingConfig:
    """
    Trading configuration parameters.

    These can be tuned without changing code by setting environment variables.
    """

    # BTC analysis parameters
    btc_lookback_hours: int = 4  # Hours of BTC data for variance calculation

    # Trading parameters
    min_edge_percent: float = 2.0  # Minimum edge % to place trade
    max_position_size: int = 10  # Max contracts per position

    @classmethod
    def from_env(cls) -> TradingConfig:
        """Load trading config from environment variables or use defaults."""
        return cls(
            btc_lookback_hours=int(os.getenv("BTC_LOOKBACK_HOURS", "4")),
            min_edge_percent=float(os.getenv("MIN_EDGE_PERCENT", "2.0")),
            max_position_size=int(os.getenv("MAX_POSITION_SIZE", "10")),
        )

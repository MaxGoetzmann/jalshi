"""
Pytest configuration and shared fixtures.

This file contains test fixtures that can be used across all tests.
"""

from __future__ import annotations

import os
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def ensure_development_mode() -> None:
    """Ensure all tests run in development mode (no real API calls)."""
    os.environ["KALSHI_ENV"] = "development"
    # Clear any production confirmation
    os.environ.pop("KALSHI_PRODUCTION_CONFIRMED", None)


@pytest.fixture
def sample_btc_prices() -> list[float]:
    """Sample BTC price data for testing strategies."""
    return [
        65000.0,
        65100.0,
        65050.0,
        65200.0,
        65150.0,
        65300.0,
        65250.0,
        65400.0,
    ]


@pytest.fixture
def sample_market_data() -> dict[str, Any]:
    """Sample Kalshi market data for testing strategies."""
    return {
        "yes_bid": 48,
        "yes_ask": 50,
        "no_bid": 49,
        "no_ask": 52,
        "strike_price": 65500,
        "expiry_minutes": 15,
    }


@pytest.fixture
def volatile_btc_prices() -> list[float]:
    """Highly volatile BTC price data for testing."""
    return [
        65000.0,
        66000.0,  # +1.5%
        64500.0,  # -2.3%
        66500.0,  # +3.1%
        64000.0,  # -3.8%
        67000.0,  # +4.7%
    ]


@pytest.fixture
def stable_btc_prices() -> list[float]:
    """Stable BTC price data with minimal movement."""
    return [
        65000.0,
        65010.0,
        64990.0,
        65005.0,
        65015.0,
        65000.0,
    ]

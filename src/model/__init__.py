"""Model layer for trading strategy development."""

from .btc_analyzer import (
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_standard_deviation,
    calculate_variance,
    detect_trend,
    estimate_probability,
)
from .strategy import BaseStrategy, Signal, TradingSignal

__all__ = [
    "BaseStrategy",
    "TradingSignal",
    "Signal",
    "calculate_returns",
    "calculate_variance",
    "calculate_standard_deviation",
    "calculate_sharpe_ratio",
    "detect_trend",
    "estimate_probability",
]

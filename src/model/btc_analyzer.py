"""
============================================================
BTC PRICE ANALYZER - Helper Functions for Your Strategy
============================================================

This file contains helper functions for analyzing BTC prices.
Use these in your strategy to calculate things like:

- Volatility (how much is BTC moving?)
- Trend (is BTC going up or down?)
- Sharpe ratio (risk-adjusted returns)
- Probability estimates

All functions have lots of comments to explain what they do!
Just import them into your strategy and use them.

EXAMPLE USAGE:
--------------
    from src.model.btc_analyzer import (
        calculate_variance,
        calculate_sharpe_ratio,
        detect_trend,
        estimate_probability,
    )

    # In your strategy's analyze() method:
    variance = calculate_variance(btc_prices)
    trend = detect_trend(btc_prices)
    sharpe = calculate_sharpe_ratio(btc_prices)

============================================================
"""

from __future__ import annotations

import math


def calculate_returns(prices: list[float]) -> list[float]:
    """
    Calculate the percentage returns between consecutive prices.

    WHAT ARE "RETURNS"?
    -------------------
    Returns measure how much the price changed as a percentage.
    - If BTC goes from $65,000 to $65,650, that's a +1% return
    - If BTC goes from $65,000 to $64,350, that's a -1% return

    Args:
        prices: List of BTC prices, oldest first, newest last
                Example: [65000, 65500, 65200, 65800]

    Returns:
        List of percentage returns (one less than input length)
        Example: [0.77, -0.46, 0.92]  (these are percentages!)

    Example:
        >>> prices = [100, 105, 103]
        >>> calculate_returns(prices)
        [5.0, -1.9047...]  # First +5%, then about -1.9%
    """
    # Need at least 2 prices to calculate any returns
    if len(prices) < 2:
        return []

    returns = []
    for i in range(1, len(prices)):
        # Percentage change formula: (new - old) / old * 100
        old_price = prices[i - 1]
        new_price = prices[i]
        pct_change = (new_price - old_price) / old_price * 100
        returns.append(pct_change)

    return returns


def calculate_variance(prices: list[float]) -> float:
    """
    Calculate the variance of price returns.

    WHAT IS VARIANCE?
    -----------------
    Variance measures how "spread out" the returns are.
    - High variance = BTC is moving a lot (volatile, unpredictable)
    - Low variance = BTC is relatively stable (calmer, more predictable)

    Think of it like this:
    - If BTC moves 0.1%, 0.2%, -0.1%, 0.15% - that's LOW variance
    - If BTC moves 5%, -3%, 4%, -6% - that's HIGH variance

    Args:
        prices: List of BTC prices

    Returns:
        Variance of returns (higher number = more volatile)

    Example:
        >>> stable = [100, 101, 100, 101, 100]     # Barely moving
        >>> volatile = [100, 110, 95, 115, 90]     # Big swings
        >>> calculate_variance(stable)   # Returns ~1.0 (low)
        >>> calculate_variance(volatile) # Returns ~100+ (high)
    """
    returns = calculate_returns(prices)

    # Need at least 2 returns to calculate variance
    if len(returns) < 2:
        return 0.0

    # Step 1: Calculate the average (mean) return
    mean_return = sum(returns) / len(returns)

    # Step 2: Calculate squared differences from the mean
    # This measures how far each return is from the average
    squared_diffs = [(r - mean_return) ** 2 for r in returns]

    # Step 3: Average the squared differences
    # We use (n-1) instead of n for "sample variance" - don't worry about why
    variance = sum(squared_diffs) / (len(squared_diffs) - 1)

    return variance


def calculate_standard_deviation(prices: list[float]) -> float:
    """
    Calculate standard deviation (volatility) of returns.

    WHAT IS STANDARD DEVIATION?
    ---------------------------
    Standard deviation is just the square root of variance.
    It's easier to interpret because it's in the same units as returns
    (percentages).

    Example interpretation:
    - If this returns 2.0, it means BTC typically moves about 2%
      between each of your price samples

    Args:
        prices: List of BTC prices

    Returns:
        Standard deviation of returns (in percentage points)
    """
    variance = calculate_variance(prices)
    return math.sqrt(variance) if variance > 0 else 0.0


def calculate_sharpe_ratio(
    prices: list[float],
    risk_free_rate: float = 0.0,
) -> float:
    """
    Calculate the Sharpe ratio - measures risk-adjusted returns.

    WHAT IS THE SHARPE RATIO?
    -------------------------
    The Sharpe ratio compares returns to risk (volatility).
    It answers: "Are we being rewarded for the risk we're taking?"

    - Higher Sharpe = better (more return per unit of risk)
    - Negative Sharpe = losing money on average
    - Zero Sharpe = no excess returns

    INTERPRETATION:
    ---------------
    - < 0   : Losing money (bad!)
    - 0-0.5 : Below average
    - 0.5-1 : Okay
    - 1-2   : Good
    - > 2   : Excellent (rare)

    Args:
        prices: List of BTC prices
        risk_free_rate: The "safe" return rate (usually ~0 for short periods)
                       For 15-minute contracts, this is basically 0

    Returns:
        Sharpe ratio (higher is better)
    """
    returns = calculate_returns(prices)

    # Need at least 2 returns
    if len(returns) < 2:
        return 0.0

    # Calculate average return
    mean_return = sum(returns) / len(returns)

    # Calculate standard deviation
    std_dev = calculate_standard_deviation(prices)

    # Avoid division by zero
    if std_dev == 0:
        return 0.0

    # Sharpe ratio formula: (average return - risk free rate) / volatility
    sharpe = (mean_return - risk_free_rate) / std_dev
    return sharpe


def detect_trend(prices: list[float], window: int = 5) -> str:
    """
    Detect if BTC is trending up, down, or sideways.

    HOW IT WORKS:
    -------------
    Compares the average of recent prices to earlier prices.
    If recent prices are higher, it's an uptrend.
    If recent prices are lower, it's a downtrend.
    Otherwise, it's sideways (no clear direction).

    Args:
        prices: List of BTC prices (oldest first, newest last)
        window: How many recent prices to consider (default: 5)

    Returns:
        "up", "down", or "sideways"

    Example:
        >>> prices = [100, 101, 102, 103, 104]  # Steadily increasing
        >>> detect_trend(prices)
        "up"

        >>> prices = [100, 99, 98, 97, 96]  # Steadily decreasing
        >>> detect_trend(prices)
        "down"

        >>> prices = [100, 101, 99, 100, 101]  # Going back and forth
        >>> detect_trend(prices)
        "sideways"
    """
    # Need enough prices to analyze
    if len(prices) < window:
        return "sideways"

    # Get the most recent prices
    recent = prices[-window:]

    # Compare first half to second half
    half = window // 2
    first_half_avg = sum(recent[:half]) / half
    second_half_avg = sum(recent[half:]) / (window - half)

    # Calculate percentage change between halves
    pct_change = (second_half_avg - first_half_avg) / first_half_avg * 100

    # Threshold: need at least 0.5% move to call it a trend
    if pct_change > 0.5:
        return "up"
    elif pct_change < -0.5:
        return "down"
    else:
        return "sideways"


def estimate_probability(
    current_price: float,
    strike_price: float,
    std_dev: float,
    minutes_to_expiry: int,
) -> float:
    """
    Estimate probability that BTC will be ABOVE the strike price at expiry.

    HOW IT WORKS:
    -------------
    Uses a normal distribution assumption (bell curve) to estimate
    the probability that BTC will end up above a certain price.

    This is a simplified model - your strategy might use more
    sophisticated methods! But this gives you a starting point.

    Args:
        current_price: Current BTC price (e.g., 65000)
        strike_price: Target price in the Kalshi contract (e.g., 65500)
        std_dev: Volatility from calculate_standard_deviation()
        minutes_to_expiry: Minutes until contract expires (e.g., 15)

    Returns:
        Probability (0.0 to 1.0) that BTC will be ABOVE strike price
        - 0.0 = definitely below
        - 0.5 = 50/50
        - 1.0 = definitely above

    Example:
        >>> # BTC at 65000, strike at 65500, 0.5% volatility, 15 min to expiry
        >>> estimate_probability(65000, 65500, 0.5, 15)
        0.35  # About 35% chance of being above $65,500

        >>> # BTC at 65000, strike at 64500 (below current!)
        >>> estimate_probability(65000, 64500, 0.5, 15)
        0.65  # About 65% chance of staying above $64,500
    """
    # If no volatility data, return 50/50
    if std_dev == 0:
        return 0.5

    # Scale volatility by time
    # Volatility scales with square root of time
    # 15 minutes is our "base" timeframe
    time_factor = math.sqrt(minutes_to_expiry / 15)
    scaled_std = std_dev * time_factor

    # Calculate how many standard deviations away the strike is
    # This is called a "z-score"
    price_diff_pct = (strike_price - current_price) / current_price * 100
    z_score = price_diff_pct / scaled_std if scaled_std > 0 else 0

    # Convert z-score to probability using the error function
    # This is the CDF (cumulative distribution function) of a normal distribution
    # Don't worry about the math - just know it converts z-score to probability
    prob_below = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))
    prob_above = 1 - prob_below

    return prob_above


def calculate_edge(
    estimated_probability: float,
    market_price_cents: int,
) -> float:
    """
    Calculate your "edge" - how much the market is mispriced.

    WHAT IS EDGE?
    -------------
    Edge is the difference between what you think something is worth
    and what the market is pricing it at.

    - Positive edge = market is underpricing, potential buying opportunity
    - Negative edge = market is overpricing, potential selling opportunity
    - Zero edge = market is fairly priced, no opportunity

    Args:
        estimated_probability: Your estimate of probability (0.0 to 1.0)
        market_price_cents: Current market price in cents (1-99)

    Returns:
        Edge as a percentage. Positive = underpriced, negative = overpriced

    Example:
        >>> # You think there's 60% chance, but market says 50 cents (50%)
        >>> calculate_edge(0.60, 50)
        10.0  # You have 10% edge - might want to BUY

        >>> # You think there's 40% chance, but market says 50 cents (50%)
        >>> calculate_edge(0.40, 50)
        -10.0  # Negative edge - might want to SELL (or avoid)
    """
    # Convert market price to probability (price in cents = probability * 100)
    market_probability = market_price_cents / 100.0

    # Edge = your estimate - market's estimate
    edge = (estimated_probability - market_probability) * 100

    return edge

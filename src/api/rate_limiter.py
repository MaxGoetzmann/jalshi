"""
Rate limiting for Kalshi API calls.

Kalshi has rate limits to prevent abuse. This module helps you stay
within those limits to avoid getting temporarily banned.

Rate Limit Info:
- Tier-based per-second limits (check your account tier)
- 20 orders per batch maximum
- 200,000 max open orders

This module provides a token bucket rate limiter that automatically
throttles requests to stay within limits.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from threading import Lock


@dataclass
class RateLimiterConfig:
    """Rate limiter configuration."""

    # Maximum requests per second (conservative default)
    requests_per_second: float = 10.0

    # Maximum burst size (requests that can be made instantly)
    burst_size: int = 20


class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    Thread-safe implementation that prevents exceeding API rate limits.
    Automatically sleeps if you're making requests too fast.

    Usage:
        limiter = RateLimiter()

        # Option 1: Call acquire() before each request
        limiter.acquire()
        response = client.get("/markets")

        # Option 2: Use as context manager
        with limiter:
            response = client.get("/markets")
    """

    def __init__(self, config: RateLimiterConfig | None = None) -> None:
        """
        Initialize rate limiter.

        Args:
            config: Rate limiter configuration. Uses defaults if not provided.
        """
        self.config = config or RateLimiterConfig()
        self._timestamps: deque[float] = deque()
        self._lock = Lock()

    def acquire(self) -> None:
        """
        Acquire permission to make an API call.

        Blocks (sleeps) if the rate limit would be exceeded.
        Always call this before making an API request.
        """
        with self._lock:
            now = time.time()

            # Remove timestamps older than 1 second
            while self._timestamps and self._timestamps[0] < now - 1.0:
                self._timestamps.popleft()

            # If at limit, wait until we can make another request
            if len(self._timestamps) >= self.config.requests_per_second:
                sleep_time = self._timestamps[0] + 1.0 - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                # Remove the oldest timestamp after sleeping
                if self._timestamps:
                    self._timestamps.popleft()

            # Record this request
            self._timestamps.append(time.time())

    def __enter__(self) -> RateLimiter:
        """Context manager entry - acquires rate limit token."""
        self.acquire()
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit - nothing to clean up."""
        pass

    @property
    def current_rate(self) -> float:
        """Get current request rate (requests in last second)."""
        with self._lock:
            now = time.time()
            # Count requests in the last second
            return sum(1 for ts in self._timestamps if ts > now - 1.0)

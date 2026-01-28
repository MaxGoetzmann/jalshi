"""
Kalshi API client wrapper.

This module provides a clean interface for interacting with the Kalshi API.
It handles authentication, rate limiting, and response parsing automatically.
"""

from __future__ import annotations

from typing import Any

import httpx

from src.core.config import KalshiCredentials
from src.core.safety import Environment, get_api_base_url, get_environment

from .auth import KalshiAuth
from .rate_limiter import RateLimiter


class KalshiClient:
    """
    Client for the Kalshi API.

    Handles authentication, rate limiting, and request/response handling.

    Usage:
        # For readonly operations (fetching market data)
        client = KalshiClient.from_env(readonly=True)
        markets = client.get_markets()

        # For trading operations
        client = KalshiClient.from_env(readonly=False)
        order = client.create_order(...)
    """

    def __init__(
        self,
        auth: KalshiAuth,
        environment: Environment | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """
        Initialize the client.

        Args:
            auth: Authentication handler
            environment: Trading environment (defaults to current env)
            rate_limiter: Rate limiter (creates default if not provided)
        """
        self.auth = auth
        self.environment = environment or get_environment()
        self.base_url = get_api_base_url(self.environment)
        self.rate_limiter = rate_limiter or RateLimiter()

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=30.0,
        )

    @classmethod
    def from_env(
        cls,
        readonly: bool = True,
        environment: Environment | None = None,
    ) -> KalshiClient:
        """
        Create a client using credentials from environment variables.

        Args:
            readonly: If True, use readonly credentials (can't place orders)
                     If False, use write credentials (can place orders)
            environment: Override the environment detection

        Returns:
            Configured KalshiClient instance
        """
        creds = KalshiCredentials.from_env(readonly=readonly)
        auth = KalshiAuth(key_id=creds.key_id, private_key_pem=creds.private_key)
        return cls(auth=auth, environment=environment)

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., "/markets")
            params: Query parameters
            json: JSON body for POST/PUT requests

        Returns:
            Parsed JSON response

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        # Rate limit
        self.rate_limiter.acquire()

        # Build full path for auth signature
        full_path = f"/trade-api/v2{path}"
        headers = self.auth.get_auth_headers(method, full_path)

        response = self._client.request(
            method=method,
            url=path,
            params=params,
            json=json,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> KalshiClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit - close the client."""
        self.close()

    # =========================================================================
    # Market Data Endpoints
    # =========================================================================

    def get_markets(
        self,
        event_ticker: str | None = None,
        series_ticker: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """
        Get available markets.

        Args:
            event_ticker: Filter by event ticker
            series_ticker: Filter by series ticker
            limit: Maximum results to return
            cursor: Pagination cursor

        Returns:
            Dictionary with 'markets' list and 'cursor' for pagination
        """
        params: dict[str, Any] = {"limit": limit}
        if event_ticker:
            params["event_ticker"] = event_ticker
        if series_ticker:
            params["series_ticker"] = series_ticker
        if cursor:
            params["cursor"] = cursor

        return self._request("GET", "/markets", params=params)

    def get_market(self, ticker: str) -> dict[str, Any]:
        """
        Get details for a specific market.

        Args:
            ticker: Market ticker (e.g., "BTCUSD-25JAN01-65000-B15")

        Returns:
            Market details including prices, volume, etc.
        """
        return self._request("GET", f"/markets/{ticker}")

    def get_orderbook(self, ticker: str, depth: int = 10) -> dict[str, Any]:
        """
        Get the order book for a market.

        Args:
            ticker: Market ticker
            depth: Number of price levels to return

        Returns:
            Order book with 'yes' and 'no' sides
        """
        return self._request(
            "GET", f"/markets/{ticker}/orderbook", params={"depth": depth}
        )

    # =========================================================================
    # Trading Endpoints (require write credentials)
    # =========================================================================

    def get_balance(self) -> dict[str, Any]:
        """
        Get account balance.

        Returns:
            Dictionary with 'balance' in cents
        """
        return self._request("GET", "/portfolio/balance")

    def get_positions(self) -> dict[str, Any]:
        """
        Get current positions.

        Returns:
            Dictionary with 'market_positions' list
        """
        return self._request("GET", "/portfolio/positions")

    def create_order(
        self,
        ticker: str,
        side: str,  # "yes" or "no"
        action: str,  # "buy" or "sell"
        count: int,
        type: str = "limit",  # "limit" or "market"
        yes_price: int | None = None,  # Price in cents (1-99)
        no_price: int | None = None,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new order.

        IMPORTANT: This will place a REAL order if not in dry run mode!

        Args:
            ticker: Market ticker
            side: "yes" or "no" contracts
            action: "buy" or "sell"
            count: Number of contracts
            type: "limit" or "market"
            yes_price: Limit price for YES in cents (1-99)
            no_price: Limit price for NO in cents (1-99)
            client_order_id: Optional client-generated order ID

        Returns:
            Created order details
        """
        body: dict[str, Any] = {
            "ticker": ticker,
            "side": side,
            "action": action,
            "count": count,
            "type": type,
        }

        if yes_price is not None:
            body["yes_price"] = yes_price
        if no_price is not None:
            body["no_price"] = no_price
        if client_order_id:
            body["client_order_id"] = client_order_id

        return self._request("POST", "/portfolio/orders", json=body)

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        """
        Cancel an existing order.

        Args:
            order_id: The order ID to cancel

        Returns:
            Cancelled order details
        """
        return self._request("DELETE", f"/portfolio/orders/{order_id}")

"""
RSA authentication for the Kalshi API.

Kalshi uses RSA signatures for API authentication. This module handles
signing requests with your private key.
"""

from __future__ import annotations

import base64
import time
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey


class KalshiAuth:
    """
    Handles RSA authentication for Kalshi API requests.

    Usage:
        auth = KalshiAuth(key_id="your-key-id", private_key_pem="-----BEGIN RSA...")
        headers = auth.get_auth_headers("GET", "/trade-api/v2/markets")
    """

    def __init__(self, key_id: str, private_key_pem: str) -> None:
        """
        Initialize authentication with credentials.

        Args:
            key_id: Your Kalshi API key ID
            private_key_pem: Your RSA private key in PEM format
        """
        self.key_id = key_id
        self._private_key = self._load_private_key(private_key_pem)

    def _load_private_key(self, pem_string: str) -> RSAPrivateKey:
        """Load RSA private key from PEM string."""
        # Handle both raw key and escaped newlines
        pem_bytes = pem_string.replace("\\n", "\n").encode()
        return serialization.load_pem_private_key(pem_bytes, password=None)

    def _sign_message(self, message: str) -> str:
        """Sign a message with the private key and return base64-encoded signature."""
        signature = self._private_key.sign(
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode()

    def get_auth_headers(self, method: str, path: str) -> dict[str, str]:
        """
        Generate authentication headers for an API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., "/trade-api/v2/markets")

        Returns:
            Dictionary of headers to include in the request
        """
        timestamp = str(int(time.time() * 1000))  # Milliseconds

        # Message format: timestamp + method + path
        message = f"{timestamp}{method.upper()}{path}"
        signature = self._sign_message(message)

        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
        }

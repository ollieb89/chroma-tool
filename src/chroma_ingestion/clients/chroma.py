"""Chroma HttpClient wrapper and initialization.

This module provides initialization and utility functions for the Chroma
HttpClient, following best practices for client management and configuration.
"""

from typing import Any

import chromadb

from chroma_ingestion.config import get_chroma_config

# Global client instance (singleton pattern)
# Use `Any` for the client type annotation because some third-party stubs
# expose callables that mypy may not consider valid types. This avoids
# spurious mypy errors while preserving runtime behavior.
_client: Any | None = None


def get_chroma_client() -> Any:
    """Get or initialize the Chroma HttpClient.

    Uses a singleton pattern to ensure a single client instance is reused
    across the application. Connects to a local ChromaDB HTTP server.
    Configuration is loaded from environment variables.

    Returns:
        chromadb.HttpClient: Initialized Chroma HttpClient

    Raises:
        ValueError: If required configuration is missing or invalid
    """
    global _client

    if _client is None:
        config = get_chroma_config()
        # Coerce types to satisfy downstream expectations: host=str, port=int
        host = str(config.get("host", "localhost"))
        port = int(config.get("port", 9500))

        _client = chromadb.HttpClient(host=host, port=port)

    return _client


def reset_client() -> None:
    """Reset the global client instance.

    Useful for testing or when you need to reinitialize with new configuration.
    """
    global _client
    _client = None

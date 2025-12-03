"""Compatibility shim for tests that import `ingestion`.

Expose `CodeIngester` from the package implementation so older import
paths continue to work during test runs.
"""

from chroma_ingestion.ingestion.base import CodeIngester

__all__ = ["CodeIngester"]

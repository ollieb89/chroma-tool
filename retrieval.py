"""Compatibility shim for tests that import `retrieval`.

Expose `CodeRetriever` and `MultiCollectionSearcher` from the package
implementation so older import paths continue to work during test runs.
"""

from chroma_ingestion.clients.chroma import get_chroma_client as _get_chroma_client
from chroma_ingestion.retrieval.retriever_clean import (
    CodeRetriever,
    MultiCollectionSearcher,
)

# Expose `get_chroma_client` at module-level so integration tests can patch it
get_chroma_client = _get_chroma_client

__all__ = ["CodeRetriever", "MultiCollectionSearcher", "get_chroma_client"]

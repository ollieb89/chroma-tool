"""Retrieval module for semantic search and query.

This package-level module re-exports the clean retrieval implementation so
tests and the CLI can import `chroma_ingestion.retrieval.CodeRetriever` while
we repair the original `retriever.py` in-place.
"""

from chroma_ingestion.retrieval.retriever_clean import CodeRetriever, MultiCollectionSearcher

__all__ = [
    "CodeRetriever",
    "MultiCollectionSearcher",
]

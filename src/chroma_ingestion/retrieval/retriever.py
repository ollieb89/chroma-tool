"""Compatibility retrieval helpers used by tests.

This module intentionally exposes `get_chroma_client` at module level so
unit tests can patch it (via
`patch("chroma_ingestion.retrieval.retriever.get_chroma_client")`).

The implementations below mirror the public API described in the docs
and used by the unit tests: `CodeRetriever`, `MultiCollectionSearcher`,
and `get_collection_info()` return shapes.
"""

from __future__ import annotations

import logging
from typing import Any

from chroma_ingestion.clients.chroma import get_chroma_client as _get_chroma_client

logger = logging.getLogger(__name__)


# Expose module-level symbol for test patching
get_chroma_client = _get_chroma_client


class CodeRetriever:
    """Query and retrieve ingested code chunks from Chroma.

    Behavior matches expectations in `tests/unit/test_retrieval.py`:
    - `query()` returns a list of dicts with keys: `document`, `metadata`, `distance`.
    - Results are ordered by ascending `distance`.
    - Empty or nested-empty `documents` produce an empty list.
    """

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        # Read module-level symbol so tests can patch it
        client = get_chroma_client()
        self.client = client
        # call get_or_create_collection on the returned client (may be mocked)
        try:
            self.collection = client.get_or_create_collection(name=collection_name)
        except Exception:
            # If the client is None or does not support the call, allow None
            self.collection = None

    def query(self, query_text: str, n_results: int = 3) -> list[dict[str, Any]]:
        if not self.collection:
            return []

        try:
            # Pass n_results explicitly as keyword to satisfy test assertions
            results = self.collection.query(query_texts=[query_text], n_results=n_results)
        except Exception:
            logger.exception("Query failed")
            return []

        if not results:
            return []

        docs = results.get("documents")
        metas = results.get("metadatas")
        dists = results.get("distances")

        # Handle several possible shapes defensively
        if not docs or not docs[0]:
            return []

        formatted: list[dict[str, Any]] = []
        for doc, meta, dist in zip(docs[0], metas[0], dists[0], strict=False):
            formatted.append({"document": doc, "metadata": meta, "distance": dist})

        # Ensure ordering by distance ascending
        formatted.sort(key=lambda r: r.get("distance", float("inf")))

        return formatted[:n_results]

    def query_semantic(
        self, query_text: str, n_results: int = 5, distance_threshold: float = 1.0
    ) -> list[dict[str, Any]]:
        # Request a larger set then filter by threshold
        results = self.query(query_text, n_results=n_results * 2)
        filtered = [r for r in results if r.get("distance", float("inf")) <= distance_threshold]
        filtered.sort(key=lambda r: r.get("distance", float("inf")))
        return filtered[:n_results]

    def query_by_metadata(
        self,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
        n_results: int = 10,
    ) -> list[dict[str, Any]]:
        if not self.collection:
            return []

        try:
            results = self.collection.get(
                where=where, where_document=where_document, limit=n_results
            )
        except Exception:
            logger.exception("Metadata query failed")
            return []

        if not results:
            return []

        docs = results.get("documents")
        metas = results.get("metadatas")
        if not docs:
            return []

        formatted: list[dict[str, Any]] = []
        # `collection.get` may return flat lists (not nested), handle both
        if isinstance(docs[0], list):
            iter_docs = docs[0]
            iter_metas = metas[0]
        else:
            iter_docs = docs
            iter_metas = metas

        for doc, meta in zip(iter_docs, iter_metas, strict=False):
            formatted.append({"document": doc, "metadata": meta})

        return formatted[:n_results]

    def get_context(
        self, query_text: str, n_results: int = 3, include_metadata: bool = True
    ) -> str:
        results = self.query(query_text, n_results=n_results)
        if not results:
            return "No relevant context found."

        parts: list[str] = []
        for r in results:
            if include_metadata:
                src = r.get("metadata", {}).get(
                    "source", r.get("metadata", {}).get("filename", "unknown")
                )
                parts.append(f"--- Source: {src} ---\n{r.get('document','')}")
            else:
                parts.append(r.get("document", ""))

        return "\n\n".join(parts)

    def get_by_source(self, filename: str) -> list[dict[str, Any]]:
        if not self.collection:
            return []

        try:
            results = self.collection.get(where={"filename": filename})
        except Exception:
            logger.exception("Get by source failed")
            return []

        docs = results.get("documents")
        metas = results.get("metadatas")
        if not docs:
            return []

        formatted: list[dict[str, Any]] = []
        if isinstance(docs[0], list):
            iter_docs = docs[0]
            iter_metas = metas[0]
        else:
            iter_docs = docs
            iter_metas = metas

        for doc, meta in zip(iter_docs, iter_metas, strict=False):
            formatted.append({"document": doc, "metadata": meta})

        return formatted

    def get_collection_info(self) -> dict[str, Any]:
        """Return collection info in the shape tests expect.

        Returns a dict with keys: `name`, `count`, `metadata`.
        """
        if not self.collection:
            return {"name": self.collection_name, "count": 0, "metadata": {}}

        try:
            count = self.collection.count()
            return {"name": self.collection_name, "count": count, "metadata": {}}
        except Exception:
            logger.exception("Get collection info failed")
            return {"name": self.collection_name, "count": 0, "metadata": {}}


class MultiCollectionSearcher:
    """Search across multiple Chroma collections.

    Provides the `collection_names` attribute and a `search()` method (per tests).
    """

    def __init__(self, collection_names: list[str]):
        self.collection_names = list(collection_names)
        # instantiate retrievers lazily to allow test-side effects on client
        self.retrievers: dict[str, CodeRetriever] = {
            name: CodeRetriever(name) for name in self.collection_names
        }

    def search(self, query_text: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Query all collections and return combined list (unsorted).

        Tests mainly assert that each collection was queried; ranking tests call
        `search_ranked()` when ordering is required.
        """
        out: list[dict[str, Any]] = []
        for name, retriever in self.retrievers.items():
            res = retriever.query(query_text, n_results=n_results)
            for r in res:
                r["collection"] = name
            out.extend(res)
        return out

    def search_all(self, query_text: str, n_results: int = 3) -> dict[str, list[dict[str, Any]]]:
        return {
            name: retriever.query(query_text, n_results=n_results)
            for name, retriever in self.retrievers.items()
        }

    def search_ranked(self, query_text: str, n_results: int = 5) -> list[dict[str, Any]]:
        all_results: list[dict[str, Any]] = self.search(query_text, n_results=n_results * 2)
        all_results.sort(key=lambda r: r.get("distance", float("inf")))
        return all_results[:n_results]


__all__ = ["CodeRetriever", "MultiCollectionSearcher", "get_chroma_client"]

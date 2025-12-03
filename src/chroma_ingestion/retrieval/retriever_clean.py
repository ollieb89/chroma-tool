"""Clean retrieval implementation used by tests and CLI.

This file is a deliberately small, well-formed module that provides
`CodeRetriever` and `MultiCollectionSearcher` for use in tests. It exists
beside the original `retriever.py` to avoid risky in-place edits of a large
malformed file during repair iterations.
"""

import logging
from typing import Any

from chroma_ingestion.clients.chroma import get_chroma_client

logger = logging.getLogger(__name__)


class CodeRetriever:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.client = get_chroma_client()
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def query(self, query_text: str, n_results: int = 3) -> list[dict[str, Any]]:
        try:
            results = self.collection.query(query_texts=[query_text], n_results=n_results)
        except Exception:
            logger.exception("Query failed")
            return []

        formatted: list[dict[str, Any]] = []
        docs = results.get("documents")
        metas = results.get("metadatas")
        dists = results.get("distances")

        if docs and docs[0]:
            for doc, meta, dist in zip(docs[0], metas[0], dists[0], strict=False):
                formatted.append({"document": doc, "metadata": meta, "distance": dist})

        return formatted

    def query_semantic(
        self, query_text: str, n_results: int = 5, distance_threshold: float = 1.0
    ) -> list[dict[str, Any]]:
        results = self.query(query_text, n_results=n_results * 2)
        filtered = [r for r in results if r.get("distance", float("inf")) <= distance_threshold]
        return filtered[:n_results]

    def query_by_metadata(
        self,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
        n_results: int = 10,
    ) -> list[dict[str, Any]]:
        try:
            results = self.collection.get(
                where=where, where_document=where_document, limit=n_results
            )
        except Exception:
            logger.exception("Metadata query failed")
            return []

        formatted: list[dict[str, Any]] = []
        docs = results.get("documents")
        metas = results.get("metadatas")
        if docs:
            for doc, meta in zip(docs, metas, strict=False):
                formatted.append({"document": doc, "metadata": meta})
        return formatted

    def get_context(
        self, query_text: str, n_results: int = 3, include_metadata: bool = True
    ) -> str:
        results = self.query(query_text, n_results=n_results)
        if not results:
            return "No relevant context found."

        parts: list[str] = []
        for r in results:
            if include_metadata:
                src = r["metadata"].get("source", "unknown")
                parts.append(f"--- Source: {src} ---\n{r['document']}")
            else:
                parts.append(r["document"])

        return "\n\n".join(parts)

    def get_by_source(self, filename: str) -> list[dict[str, Any]]:
        try:
            results = self.collection.get(where={"filename": filename})
        except Exception:
            logger.exception("Get by source failed")
            return []

        formatted: list[dict[str, Any]] = []
        docs = results.get("documents")
        metas = results.get("metadatas")
        if docs:
            for doc, meta in zip(docs, metas, strict=False):
                formatted.append({"document": doc, "metadata": meta})
        return formatted

    def get_collection_info(self) -> dict[str, Any]:
        try:
            count = self.collection.count()
            return {"collection_name": self.collection_name, "total_chunks": count}
        except Exception:
            logger.exception("Get collection info failed")
            return {}


class MultiCollectionSearcher:
    def __init__(self, collection_names: list[str]):
        self.retrievers: dict[str, CodeRetriever] = {
            name: CodeRetriever(name) for name in collection_names
        }

    def search_all(self, query_text: str, n_results: int = 3) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        for name, retriever in self.retrievers.items():
            out[name] = retriever.query(query_text, n_results=n_results)
        return out

    def search_ranked(self, query_text: str, n_results: int = 5) -> list[dict[str, Any]]:
        all_results: list[dict[str, Any]] = []
        for name, retriever in self.retrievers.items():
            res = retriever.query(query_text, n_results=n_results * 2)
            for r in res:
                r["collection"] = name
            all_results.extend(res)
        all_results.sort(key=lambda r: r.get("distance", float("inf")))
        return all_results[:n_results]

    def get_context_multiway(self, query_text: str, n_results: int = 2) -> str:
        results = self.search_all(query_text, n_results=n_results)
        parts: list[str] = []
        for collection_name, res in results.items():
            if res:
                parts.append(f"=== From {collection_name} ===")
                for r in res:
                    src = r.get("metadata", {}).get("source", "unknown")
                    parts.append(f"[{src}]\n{r.get('document', '')}\n")
        if not parts:
            return "No relevant context found across collections."
        return "\n".join(parts)

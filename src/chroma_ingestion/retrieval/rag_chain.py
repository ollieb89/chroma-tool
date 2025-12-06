"""RAG (Retrieval-Augmented Generation) chain for agent discovery.

Provides semantic search over ingested agents with optional LLM-based response generation.
Uses Chroma as the vector store and LangChain for orchestration.
"""

from __future__ import annotations

import logging
from typing import Any

from chroma_ingestion.clients.chroma import get_chroma_client
from chroma_ingestion.retrieval.retriever import CodeRetriever

logger = logging.getLogger(__name__)


class RAGChain:
    """Retrieval-Augmented Generation chain for semantic agent discovery.

    Uses Chroma for semantic search and optionally integrates with an LLM
    for generating contextual responses based on retrieved agent documentation.
    """

    def __init__(
        self,
        collection_name: str = "agents_discovery",
        n_results: int = 5,
        distance_threshold: float = 0.5,
    ):
        """Initialize RAG chain.

        Args:
            collection_name: Chroma collection to query
            n_results: Number of results to retrieve (default: 5)
            distance_threshold: Maximum distance for inclusion (lower = more similar)
        """
        self.collection_name = collection_name
        self.n_results = n_results
        self.distance_threshold = distance_threshold
        self.retriever = CodeRetriever(collection_name)

    def retrieve(
        self,
        query: str,
        n_results: int | None = None,
        threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve agents matching the query.

        Args:
            query: Natural language search query
            n_results: Override default number of results
            threshold: Override default distance threshold

        Returns:
            List of retrieved documents with metadata and scores
        """
        n = n_results or self.n_results
        thresh = threshold or self.distance_threshold

        logger.info("🔍 Retrieving agents for query: %s", query)

        # Query Chroma collection
        results = self.retriever.query(query, n_results=n)

        if not results:
            logger.warning("⚠️  No results found for query: %s", query)
            return []

        # Filter by threshold
        filtered = [r for r in results if r.get("distance", 1.0) <= thresh]

        if not filtered:
            logger.warning(
                "⚠️  No results below threshold %.2f. Found %d results with lower confidence.",
                thresh,
                len(results),
            )
            return results  # Return all results anyway

        logger.info("✅ Found %d matching agents", len(filtered))
        return filtered

    def format_results(self, results: list[dict[str, Any]]) -> str:
        """Format retrieved results as readable text.

        Args:
            results: List of retrieved documents

        Returns:
            Formatted string with results
        """
        if not results:
            return "No agents found matching your query."

        output = f"Found {len(results)} matching agents:\n\n"

        for i, result in enumerate(results, 1):
            distance = result.get("distance", 0)
            confidence = max(0, 1.0 - distance)
            filename = result.get("metadata", {}).get("filename", "Unknown")
            source = result.get("metadata", {}).get("source", "Unknown")
            agent_name = (
                result.get("metadata", {}).get("agent_name") or filename
            )

            output += f"{i}. {agent_name}\n"
            output += f"   📍 Source: {source}\n"
            output += f"   ⭐ Confidence: {confidence * 100:.1f}%\n"
            output += f"   Preview: {result.get('document', '')[:100].strip()}...\n\n"

        return output

    def query(
        self,
        query: str,
        n_results: int | None = None,
        format_output: bool = True,
        include_raw: bool = False,
    ) -> dict[str, Any] | str:
        """Execute RAG query: retrieve agents and format results.

        Args:
            query: Search query
            n_results: Override default results count
            format_output: Return formatted string (True) or dict (False)
            include_raw: Include raw result data in output dict

        Returns:
            Formatted string or dict with results
        """
        results = self.retrieve(query, n_results=n_results)

        if format_output:
            return self.format_results(results)

        # Return structured dict
        return {
            "query": query,
            "results_count": len(results),
            "results": results if include_raw else [
                {
                    "agent_name": r.get("metadata", {}).get("agent_name", "Unknown"),
                    "source": r.get("metadata", {}).get("source", "Unknown"),
                    "confidence": max(0, 1.0 - r.get("distance", 1.0)),
                    "distance": r.get("distance", 1.0),
                }
                for r in results
            ],
        }

    def get_collection_stats(self) -> dict[str, Any]:
        """Get statistics about the collection.

        Returns:
            Dictionary with collection stats
        """
        try:
            client = get_chroma_client()
            collection = client.get_collection(self.collection_name)
            count = collection.count()

            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "status": "ready",
            }
        except Exception as e:
            logger.error("Error getting collection stats: %s", e)
            return {
                "collection_name": self.collection_name,
                "status": "error",
                "error": str(e),
            }

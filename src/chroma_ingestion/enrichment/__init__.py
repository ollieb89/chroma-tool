"""Semantic enrichment module for agent metadata inference.

Provides tools for automatically inferring category, tech stack, and descriptions
for documents using RAG-based analysis.
"""

from chroma_ingestion.enrichment.metadata_inferrer import MetadataInferrer

__all__ = ["MetadataInferrer"]

"""Code extraction and ingestion module for Chroma.

This module provides intelligent code-aware chunking and storage of text and code
into Chroma Cloud. It uses RecursiveCharacterTextSplitter to preserve semantic
structure and maintains metadata for source tracking.

Supports:
- Python files (.py)
- Markdown files (.md, .agent.md, .prompt.md)
- Agent definitions and prompts
"""

import glob
import logging
import os
from datetime import datetime
from typing import Any

from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from chroma_ingestion.clients.chroma import get_chroma_client
from chroma_ingestion.config import get_chroma_config

# Module logger
logger = logging.getLogger(__name__)


class CodeIngester:
    """Intelligent code/document ingestion for Chroma with semantic splitting.

    This class handles:
    - Recursive file discovery (Python, Markdown, Agent files)
    - Code-aware or markdown-aware chunking
    - Batch upsert to Chroma Cloud
    - Metadata tracking (file path, chunk index, file type)
    """

    def __init__(
        self,
        target_folder: str,
        collection_name: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        batch_size: int = 100,
        file_patterns: list[str] | None = None,
    ):
        """Initialize the code ingester.

        Args:
            target_folder: Root folder to recursively scan for files
            collection_name: Name of Chroma collection to store chunks
            chunk_size: Approximate tokens per chunk (default: 1000)
            chunk_overlap: Token overlap between chunks (default: 200)
            file_patterns: File patterns to ingest (default: *.py, *.md, *.agent.md, *.prompt.md)
        """
        self.target_folder = target_folder
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        # Ensure overlap is smaller than chunk_size to avoid splitter errors.
        if chunk_overlap >= chunk_size:
            # If user supplied an overlap >= chunk_size, adjust to a sensible fraction
            # (10% of chunk_size) to preserve splitting behavior while remaining safe.
            self.chunk_overlap = max(0, chunk_size // 10)
        else:
            self.chunk_overlap = chunk_overlap
        self.batch_size = batch_size
        self.file_patterns = file_patterns or [
            "**/*.py",
            "**/*.md",
            "**/*.agent.md",
            "**/*.prompt.md",
        ]

        # Initialize Chroma client and collection
        self.client = get_chroma_client()
        self.collection = self.client.get_or_create_collection(name=collection_name)

        # Configure splitter - use markdown for all files (more general)
        self.splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.MARKDOWN,
            chunk_size=chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def prepare_metadata(self, file_path: str, chunk_index: int) -> dict[str, Any]:
        """Prepare metadata dict for a given file chunk.

        This helper centralizes metadata construction so unit tests and other
        ingesters can reuse consistent keys.
        """
        return {
            "source": file_path,
            "filename": os.path.basename(file_path),
            "chunk_index": chunk_index,
            "folder": os.path.dirname(file_path),
            "file_type": os.path.splitext(file_path)[1],
        }

    def discover_files(self) -> list[str]:
        """Discover files in target folder recursively.

        Returns:
            List of absolute paths to matching files
        """
        all_files = []
        for pattern in self.file_patterns:
            full_pattern = os.path.join(self.target_folder, pattern)
            files = glob.glob(full_pattern, recursive=True)
            all_files.extend(files)

        return sorted(list(set(all_files)))  # Remove duplicates and sort

    def ingest_files(self, batch_size: int | None = None) -> tuple[int, int]:
        """Ingest files from target folder into Chroma.

        Uses semantic splitting to preserve document structure.
        Batch upserts to avoid memory limits.

        Args:
            batch_size: Number of chunks to upsert per batch

        Returns:
            Tuple of (total_files_processed, total_chunks_ingested)
        """
        # Allow caller to override batch_size; otherwise use configured default
        batch_size = batch_size or self.batch_size

        # Log runtime audit info: which Chroma host/port and collection we will use
        try:
            cfg = get_chroma_config()
            host = cfg.get("host")
            port = cfg.get("port")
        except Exception:
            host = "unknown"
            port = "unknown"

        logger.info("[INGEST] Starting ingestion at %sZ", datetime.utcnow().isoformat())
        logger.info(
            "[INGEST] Chroma host=%s port=%s collection=%s",
            host,
            port,
            self.collection_name,
        )

        py_files = self.discover_files()

        if not py_files:
            logger.info("❌ No matching files found in: %s", self.target_folder)
            return 0, 0

        logger.info("📂 Scanning: %s", self.target_folder)
        logger.info("📦 Found %d file(s)", len(py_files))

        documents: list[str] = []
        ids: list[str] = []
        metadatas: list[dict[str, Any]] = []
        files_processed = 0

        # Process each file
        for file_path in py_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Create semantic chunks
                chunks = self.splitter.create_documents([content])

                if chunks:
                    files_processed += 1
                    for i, chunk in enumerate(chunks):
                        # Unique ID: use full file path + chunk index to avoid
                        # collisions when multiple files share the same basename
                        # (e.g., many README.md files). Use normalized path for
                        # readability.
                        normalized_path = os.path.normpath(file_path)
                        doc_id = f"{normalized_path}:{i}"

                        documents.append(chunk.page_content)
                        ids.append(doc_id)
                        metadatas.append(
                            {
                                "source": file_path,
                                "filename": os.path.basename(file_path),
                                "chunk_index": i,
                                "folder": os.path.dirname(file_path),
                                "file_type": os.path.splitext(file_path)[1],
                            }
                        )

            except Exception as e:
                logger.warning("⚠️  Could not read %s: %s", file_path, e)

        # Batch upsert to Chroma Cloud
        if documents:
            logger.info("🚀 Ingesting %d chunks into Chroma Cloud...", len(documents))

            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i : i + batch_size]
                batch_ids = ids[i : i + batch_size]
                batch_metas = metadatas[i : i + batch_size]

                self.collection.upsert(
                    documents=batch_docs,
                    ids=batch_ids,
                    metadatas=batch_metas,
                )
                logger.info(
                    "  ✓ Batch %d complete (%d chunks)", i // batch_size + 1, len(batch_docs)
                )

            logger.info(
                "✅ Done! Ingested %d chunks from %d file(s)", len(documents), files_processed
            )
            return files_processed, len(documents)
        else:
            logger.info("❌ No documents created.")
            return files_processed, 0

    def get_collection_stats(self) -> dict[str, Any]:
        """Get statistics about the ingested collection.

        Returns:
            Dictionary with collection metadata
        """
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "target_folder": self.target_folder,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }

    def run(self, batch_size: int | None = None) -> tuple[int, int]:
        """Run the ingestion using the configured settings.

        This is a convenience wrapper used by the CLI. It delegates to
        `ingest_files` and returns the same (files_processed, chunks_ingested)
        tuple.
        """
        return self.ingest_files(batch_size=batch_size)

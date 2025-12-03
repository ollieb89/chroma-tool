"""Agent-specific ingestion with enhanced metadata extraction.

Extends CodeIngester with agent-aware features:
- YAML frontmatter parsing
- Tech stack keyword extraction
- Category classification
- Rich metadata for semantic analysis
"""

import glob
import logging
import os
from typing import Any, ClassVar

import yaml

from chroma_ingestion.ingestion.base import CodeIngester

# Module logger
logger = logging.getLogger(__name__)


class AgentIngester(CodeIngester):
    """Specialized ingester for agent definition files.

    Extracts structured metadata from agent frontmatter and content:
    - Frontmatter parsing (YAML)
    - Tech stack keyword extraction
    - Category classification
    - Section-aware chunking
    """

    # Tech stack keywords to extract
    TECH_KEYWORDS: ClassVar[dict[str, list[str]]] = {
        "frontend": [
            "nextjs",
            "next.js",
            "react",
            "typescript",
            "tailwind",
            "css",
            "html",
            "ui",
            "ux",
        ],
        "backend": ["python", "fastapi", "api", "rest", "graphql", "websocket", "middleware"],
        "database": ["postgresql", "postgres", "sql", "neon", "prisma", "sqlalchemy", "database"],
        "testing": [
            "playwright",
            "vitest",
            "jest",
            "testing",
            "test",
            "e2e",
            "unit",
            "integration",
        ],
        "ai_ml": ["ai", "ml", "machine learning", "llm", "embeddings", "vector", "rag", "prompt"],
        "devops": ["docker", "deployment", "ci/cd", "kubernetes", "vercel", "railway", "cloud"],
        "security": ["security", "auth", "authentication", "jwt", "oauth", "vulnerability"],
    }

    # Category classification keywords
    CATEGORY_KEYWORDS: ClassVar[dict[str, list[str]]] = {
        "frontend": ["frontend", "react", "nextjs", "ui", "ux", "component"],
        "backend": ["backend", "api", "python", "fastapi", "server"],
        "architecture": ["architect", "system", "design", "infrastructure"],
        "testing": ["test", "qa", "quality", "playwright", "debug"],
        "ai_ml": ["ai", "ml", "data", "engineer", "scientist", "prompt"],
        "devops": ["devops", "deploy", "cloud", "incident", "performance"],
        "security": ["security", "audit", "vulnerability"],
        "quality": ["review", "refactor", "code quality", "best practice"],
        "database": ["database", "sql", "postgres", "neon", "graphql"],
        "planning": ["plan", "requirement", "pm", "product", "task"],
    }

    def __init__(
        self,
        target_folder: str | list[str],
        collection_name: str = "agents_analysis",
        chunk_size: int = 1500,  # Larger for agent files
        chunk_overlap: int = 300,
        exclusions: list[str] | None = None,
        batch_size: int = 50,
    ):
        """Initialize agent ingester with multiple source folders.

        Args:
            source_folders: List of absolute paths to agent folders
            collection_name: Name of Chroma collection
            chunk_size: Tokens per chunk (larger for agents)
            chunk_overlap: Token overlap between chunks
            exclusions: List of filenames to exclude
        """
        # Normalize input: accept either a single target_folder or a list of folders
        if isinstance(target_folder, list | tuple):
            self.source_folders = list(target_folder)
        else:
            self.source_folders = [target_folder]

        self.exclusions = exclusions or []

        # Initialize parent with first folder (we'll override discovery)
        super().__init__(
            target_folder=self.source_folders[0] if self.source_folders else ".",
            collection_name=collection_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            batch_size=batch_size,
            file_patterns=["**/*.md", "**/*.agent.md", "**/*.prompt.md"],
        )

        # Keep `batch_size` attribute consistent with parent
        self.batch_size = batch_size

    def parse_agent_metadata(self, file_path: str) -> dict[str, Any]:
        """Parse agent file and return a minimal metadata dict expected by tests.

        Tests expect keys like `name`, `description`, and `tags`. This method
        reads the file, extracts YAML frontmatter if present, and returns a
        dict with those keys (falling back to sensible defaults).
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return {}

        frontmatter, _ = self.parse_frontmatter(content)

        # Normalize to test-expected keys
        return {
            "name": frontmatter.get("name")
            or os.path.basename(file_path).replace(".agent.md", "").replace(".md", ""),
            "description": frontmatter.get("description", ""),
            "tags": frontmatter.get("tags", []),
        }

    def discover_files(self) -> list[str]:
        """Discover agent files across all source folders.

        Returns:
            Sorted list of unique absolute file paths
        """
        all_files = []
        for folder in self.source_folders:
            for pattern in self.file_patterns:
                full_pattern = os.path.join(folder, pattern)
                files = glob.glob(full_pattern, recursive=True)
                all_files.extend(files)

        # Filter exclusions and duplicates
        filtered = [
            f
            for f in all_files
            if (
                os.path.basename(f) not in self.exclusions
                and "__init__.py" not in f
                and "README.md" not in os.path.basename(f)
            )
        ]

        return sorted(list(set(filtered)))

    def parse_frontmatter(self, content: str) -> tuple[dict[str, Any], str]:
        """Parse YAML frontmatter from agent file.

        Args:
            content: Full file content

        Returns:
            Tuple of (frontmatter_dict, remaining_content)
        """
        frontmatter: dict[str, Any] = {}
        body = content

        # Check for YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                except yaml.YAMLError as e:
                    logger.warning("YAML parse error: %s", e)

        return frontmatter, body

    def extract_tech_stack(self, content: str) -> list[str]:
        """Extract tech stack keywords from content.

        Args:
            content: Full file content

        Returns:
            List of identified tech keywords
        """
        content_lower = content.lower()
        found_tech = set()

        for keywords in self.TECH_KEYWORDS.values():
            for keyword in keywords:
                if keyword in content_lower:
                    found_tech.add(keyword)

        return sorted(list(found_tech))

    def classify_category(self, filename: str, content: str) -> str:
        """Classify agent into a category.

        Args:
            filename: Agent filename
            content: Full file content

        Returns:
            Classified category name
        """
        text = (filename + " " + content).lower()

        category_scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            category_scores[category] = score

        # Return highest scoring category
        return max(category_scores, key=lambda k: category_scores[k], default="general")

    def extract_metadata(self, file_path: str, content: str) -> tuple[dict[str, Any], str]:
        """Extract rich metadata from agent file.

        Args:
            file_path: Absolute file path
            content: Full file content

        Returns:
            Tuple of (metadata_dict, body_content)
        """
        frontmatter, body = self.parse_frontmatter(content)
        filename = os.path.basename(file_path)

        # Parse agent name from filename or title
        agent_name = frontmatter.get(
            "name",
            filename.replace(".md", "").replace(".agent", "").replace(".prompt", ""),
        )

        metadata = {
            "source": file_path,
            "filename": filename,
            "agent_name": agent_name,
            "description": frontmatter.get("description", "")[:500],  # Truncate
            "model": frontmatter.get("model", ""),
            "tools": ",".join(frontmatter.get("tools", [])) if frontmatter.get("tools") else "",
            "category": self.classify_category(filename, content),
            "tech_stack": ",".join(
                self.extract_tech_stack(content)
            ),  # Chroma requires string, not list
            "folder": os.path.dirname(file_path),
            "file_type": os.path.splitext(file_path)[1],
            "source_collection": self._get_source_collection(file_path),
        }

        return metadata, body

    def _get_source_collection(self, file_path: str) -> str:
        """Identify which source collection a file belongs to.

        Args:
            file_path: Absolute file path

        Returns:
            Source collection name
        """
        if ".github/agents" in file_path:
            return "github_agents"
        elif "ccs/.claude/agents" in file_path:
            return "ccs_claude"
        elif "ghc_tools/agents" in file_path:
            return "ghc_tools"
        elif "scf/src/superclaude" in file_path:
            return "superclaude"
        else:
            return "unknown"

    def ingest_agents(self, batch_size: int = 50, verbose: bool = True) -> tuple[int, int]:
        """Ingest agent files with enhanced metadata.

        Args:
            batch_size: Chunks per batch upsert
            verbose: Print progress messages

        Returns:
            Tuple of (files_processed, chunks_ingested)
        """
        agent_files = self.discover_files()

        if not agent_files:
            if verbose:
                print("❌ No agent files found")
            return 0, 0

        if verbose:
            print(
                f"📂 Found {len(agent_files)} agent files across {len(self.source_folders)} folders"
            )

        documents: list[str] = []
        ids: list[str] = []
        metadatas: list[dict[str, Any]] = []
        files_processed = 0
        files_failed = 0

        for file_path in agent_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Extract enhanced metadata
                base_metadata, body = self.extract_metadata(file_path, content)

                # Create semantic chunks
                chunks = self.splitter.create_documents([content])

                if chunks:
                    files_processed += 1
                    for i, chunk in enumerate(chunks):
                        # Use agent name + normalized path + chunk index to ensure
                        # uniqueness across files with same agent_name.
                        normalized_path = os.path.normpath(file_path)
                        doc_id = (
                            f"{base_metadata.get('agent_name','unknown')}:{normalized_path}:{i}"
                        )

                        # Add chunk-specific metadata
                        chunk_metadata = {
                            **base_metadata,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                        }

                        documents.append(chunk.page_content)
                        ids.append(doc_id)
                        metadatas.append(chunk_metadata)

            except Exception as e:
                files_failed += 1
                logger.warning("Could not process %s: %s", os.path.basename(file_path), e)

        # Batch upsert
        if documents:
            logger.info(
                "Ingesting %d chunks into collection '%s'...", len(documents), self.collection_name
            )

            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i : i + batch_size]
                batch_ids = ids[i : i + batch_size]
                batch_metas = metadatas[i : i + batch_size]

                self.collection.upsert(documents=batch_docs, ids=batch_ids, metadatas=batch_metas)
                logger.info("Batch %d complete (%d chunks)", i // batch_size + 1, len(batch_docs))

            logger.info("Done! Ingested %d chunks from %d agents", len(documents), files_processed)
            if files_failed > 0:
                logger.warning("%d files failed to process", files_failed)

            return files_processed, len(documents)

        logger.info("No documents created.")
        return files_processed, 0

    def run(self, batch_size: int | None = None) -> tuple[int, int]:
        """Run agent ingestion (convenience wrapper for CLI).

        Delegates to `ingest_agents` so the CLI can uniformly call `run()` on
        either `CodeIngester` or `AgentIngester` instances.
        """
        return self.ingest_agents(batch_size=batch_size or self.batch_size, verbose=True)

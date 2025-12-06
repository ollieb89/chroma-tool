"""Metadata inference engine for semantic enrichment of agent documents.

Uses RAG-based similarity analysis to automatically infer category, tech stack,
and descriptions for documents that lack enriched metadata.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from chroma_ingestion.retrieval.rag_chain import RAGChain

logger = logging.getLogger(__name__)

# Known technology keywords for validation
TECH_KEYWORDS = {
    "frontend": ["react", "nextjs", "vue", "svelte", "angular", "typescript", "jsx", "tailwind", "shadcn", "storybook"],
    "backend": ["fastapi", "flask", "django", "express", "nodejs", "python", "golang", "rust", "java", "api", "rest"],
    "testing": ["playwright", "vitest", "pytest", "jest", "mocha", "cucumber", "e2e", "testing", "qa", "test"],
    "security": ["authentication", "oauth", "jwt", "encryption", "owasp", "security", "cryptography", "password", "auth"],
    "devops": ["docker", "kubernetes", "ci/cd", "github actions", "gitlab", "jenkins", "terraform", "ansible", "devops"],
    "database": ["postgresql", "mongodb", "mysql", "sql", "sqlalchemy", "prisma", "orm", "database", "redis"],
    "ai_ml": ["ai", "machine learning", "llm", "gpt", "langchain", "vectordb", "embedding", "transformer", "neural"],
    "architecture": ["design", "pattern", "microservice", "architecture", "system", "scalability", "performance"],
    "documentation": ["readme", "doc", "guide", "tutorial", "example", "howto", "markdown"],
    "planning": ["requirements", "prd", "task", "planning", "roadmap", "specification", "design doc"],
}

# Category mapping (inferred from tech stacks)
CATEGORY_KEYWORDS = {
    "frontend": ["react", "nextjs", "vue", "ui", "component", "css", "tailwind", "shadcn"],
    "backend": ["fastapi", "flask", "api", "endpoint", "server", "python", "golang", "express"],
    "testing": ["test", "playwright", "pytest", "vitest", "spec", "e2e", "qa"],
    "security": ["auth", "security", "encryption", "owasp", "jwt", "oauth"],
    "devops": ["docker", "kubernetes", "ci/cd", "deploy", "infrastructure"],
    "database": ["database", "sql", "mongodb", "orm", "sqlalchemy", "prisma"],
    "ai_ml": ["ai", "ml", "llm", "gpt", "langchain", "embedding"],
    "architecture": ["architecture", "design", "pattern", "system"],
    "documentation": ["readme", "guide", "tutorial", "doc"],
    "planning": ["requirements", "prd", "planning", "task"],
}


@dataclass
class EnrichedMetadata:
    """Enriched metadata for a document."""

    agent_name: str
    category: str
    tech_stack: List[str]
    description: str
    confidence_scores: Dict[str, float]
    inferred: bool = True


class MetadataInferrer:
    """Infer metadata for documents using semantic similarity and RAG."""

    def __init__(self, rag_chain: Optional[RAGChain] = None, use_keywords: bool = True):
        """Initialize metadata inferrer.

        Args:
            rag_chain: RAGChain instance for semantic analysis (optional)
            use_keywords: Use keyword matching as fallback/validation
        """
        self.rag = rag_chain
        self.use_keywords = use_keywords

    def extract_agent_name(self, doc_text: str, filename: Optional[str] = None) -> str:
        """Extract agent name from document.

        Args:
            doc_text: Document content
            filename: Original filename (optional)

        Returns:
            Inferred agent name
        """
        # Try to extract from filename first
        if filename:
            # Remove extensions and path
            name = filename.replace(".md", "").replace(".py", "").replace("/", "-")
            if name and len(name) > 2:
                return name

        # Try first line as title
        lines = doc_text.split("\n")
        for line in lines:
            line = line.strip().lstrip("#").strip()
            if line and len(line) > 5 and len(line) < 100:
                return line.lower().replace(" ", "-")[:50]

        # Fallback
        return "unknown-agent"

    def infer_category(self, doc_text: str) -> Tuple[str, float]:
        """Infer category from document content.

        Uses keyword matching and optionally RAG similarity.

        Args:
            doc_text: Document content (first 500 chars)

        Returns:
            Tuple of (category, confidence_score)
        """
        if not doc_text:
            return "unknown", 0.0

        # Keyword-based inference
        text_lower = doc_text.lower()[:1000]  # First 1000 chars
        scores = {}

        for category, keywords in CATEGORY_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                scores[category] = matches / len(keywords)

        if scores:
            best_category = max(scores, key=scores.get)
            confidence = scores[best_category]
            logger.info(f"  Inferred category: {best_category} ({confidence:.2f})")
            return best_category, min(confidence, 0.99)

        return "unknown", 0.0

    def infer_tech_stack(self, doc_text: str) -> Tuple[List[str], float]:
        """Extract technology keywords from document.

        Args:
            doc_text: Document content

        Returns:
            Tuple of (tech_stack_list, confidence_score)
        """
        if not doc_text:
            return [], 0.0

        text_lower = doc_text.lower()
        found_techs = set()
        matches_per_tech = {}

        # Search all tech keywords
        for category, techs in TECH_KEYWORDS.items():
            for tech in techs:
                if tech in text_lower:
                    found_techs.add(tech)
                    matches_per_tech[tech] = text_lower.count(tech)

        # Sort by frequency and take top 5-10
        sorted_techs = sorted(found_techs, key=lambda t: matches_per_tech.get(t, 1), reverse=True)
        tech_stack = sorted_techs[:10]

        if tech_stack:
            confidence = min(len(tech_stack) / 10, 1.0)  # More techs = higher confidence
            logger.info(f"  Inferred tech stack: {tech_stack} ({confidence:.2f})")
            return tech_stack, confidence

        return [], 0.0

    def infer_description(self, doc_text: str, max_length: int = 200) -> Tuple[str, float]:
        """Generate description from document content.

        Extracts summary from first non-title lines or uses first 200 chars.

        Args:
            doc_text: Document content
            max_length: Maximum description length

        Returns:
            Tuple of (description, confidence_score)
        """
        if not doc_text:
            return "", 0.0

        lines = doc_text.split("\n")
        description_lines = []

        for line in lines[1:]:  # Skip title
            line = line.strip()
            if line and not line.startswith("#"):
                description_lines.append(line)
            if len("\n".join(description_lines)) > max_length:
                break

        description = " ".join(description_lines)[:max_length].strip()

        if description:
            confidence = min(len(description) / max_length, 1.0)
            return description, confidence

        return "", 0.0

    def enrich_document(
        self,
        doc_id: str,
        doc_text: str,
        filename: Optional[str] = None,
    ) -> EnrichedMetadata:
        """Enrich single document with inferred metadata.

        Args:
            doc_id: Document ID
            doc_text: Document content
            filename: Original filename (optional)

        Returns:
            EnrichedMetadata with all inferred fields
        """
        logger.info(f"Enriching document: {doc_id}")

        agent_name = self.extract_agent_name(doc_text, filename)
        category, category_conf = self.infer_category(doc_text)
        tech_stack, tech_conf = self.infer_tech_stack(doc_text)
        description, desc_conf = self.infer_description(doc_text)

        confidence_scores = {
            "category": category_conf,
            "tech_stack": tech_conf,
            "description": desc_conf,
            "overall": (category_conf + tech_conf + desc_conf) / 3,
        }

        return EnrichedMetadata(
            agent_name=agent_name,
            category=category,
            tech_stack=tech_stack,
            description=description,
            confidence_scores=confidence_scores,
        )

    def enrich_collection(
        self,
        collection_name: str,
        batch_size: int = 100,
        dry_run: bool = False,
        skip_existing: bool = True,
    ) -> Dict:
        """Enrich all documents in a Chroma collection.

        Args:
            collection_name: Name of collection to enrich
            batch_size: Number of documents to process per batch
            dry_run: If True, don't save changes to Chroma
            skip_existing: Skip documents that already have metadata

        Returns:
            Summary dict with processing stats
        """
        from chroma_ingestion.clients.chroma import get_chroma_client

        client = get_chroma_client()
        collection = client.get_collection(name=collection_name)
        total_docs = collection.count()

        logger.info(f"Starting enrichment of {collection_name} ({total_docs} documents)")

        processed = 0
        enriched = 0
        failed = []
        skipped = 0

        try:
            # Get all documents in batches
            for offset in range(0, total_docs, batch_size):
                batch_results = collection.get(limit=batch_size, offset=offset)
                batch_ids = batch_results.get("ids", [])
                batch_docs = batch_results.get("documents", [])
                batch_metadata = batch_results.get("metadatas", [])

                logger.info(f"Processing batch {offset // batch_size + 1} ({len(batch_ids)} docs)...")

                for doc_id, doc_text, metadata in zip(batch_ids, batch_docs, batch_metadata):
                    processed += 1
                    try:
                        # Skip if already enriched
                        if skip_existing and metadata.get("category"):
                            skipped += 1
                            continue

                        # Enrich document
                        enriched_meta = self.enrich_document(
                            doc_id,
                            doc_text or "",
                            filename=metadata.get("filename"),
                        )

                        # Update metadata in Chroma (unless dry run)
                        if not dry_run:
                            import json

                            updated_metadata = {
                                **metadata,
                                "category": enriched_meta.category,
                                "tech_stack": json.dumps(enriched_meta.tech_stack),  # Convert to JSON string
                                "description": enriched_meta.description,
                                "enrichment_confidence": enriched_meta.confidence_scores["overall"],
                                "enriched": "true",
                            }

                            # Update document with new metadata
                            collection.update(
                                ids=[doc_id],
                                documents=[doc_text],
                                metadatas=[updated_metadata],
                            )

                        enriched += 1

                    except Exception as e:
                        logger.error(f"Failed to enrich {doc_id}: {e}")
                        failed.append((doc_id, str(e)))

        except Exception as e:
            logger.error(f"Error during collection enrichment: {e}")

        logger.info(f"✅ Enrichment complete: {enriched} docs enriched, {skipped} skipped, {len(failed)} failed")

        return {
            "collection": collection_name,
            "total_documents": total_docs,
            "processed": processed,
            "enriched": enriched,
            "skipped": skipped,
            "failed_count": len(failed),
            "failed_ids": failed,
            "dry_run": dry_run,
        }

    def compare_with_known(self, enriched_meta: EnrichedMetadata, known_meta: dict) -> Dict:
        """Compare inferred metadata with known/verified metadata.

        Useful for validation and confidence calibration.

        Args:
            enriched_meta: Inferred metadata
            known_meta: Known/verified metadata

        Returns:
            Comparison report with matches and mismatches
        """
        import json

        # Parse tech_stack if it's a JSON string
        known_techs = known_meta.get("tech_stack", [])
        if isinstance(known_techs, str):
            try:
                known_techs = json.loads(known_techs)
            except (json.JSONDecodeError, TypeError):
                known_techs = []

        report = {
            "category_match": enriched_meta.category == known_meta.get("category"),
            "category_actual": known_meta.get("category"),
            "category_inferred": enriched_meta.category,
            "tech_stack_overlap": set(enriched_meta.tech_stack) & set(known_techs),
            "tech_stack_actual": known_techs,
            "tech_stack_inferred": enriched_meta.tech_stack,
            "overall_confidence": enriched_meta.confidence_scores["overall"],
        }

        return report

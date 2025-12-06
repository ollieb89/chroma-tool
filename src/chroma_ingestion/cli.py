"""Command-line interface for chroma-ingestion.

Provides CLI commands for ingesting code files into ChromaDB and searching
the ingested code using semantic queries.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from chroma_ingestion import (
    AgentIngester,
    CodeIngester,
    CodeRetriever,
    __version__,
)

logger = logging.getLogger(__name__)


def configure_logging(debug: bool = False, log_file: str | None = None) -> None:
    """Configure root logging for the CLI."""
    root = logging.getLogger()
    # Avoid adding multiple handlers in tests/runs
    if root.handlers:
        for h in list(root.handlers):
            root.removeHandler(h)

    level = logging.DEBUG if debug else logging.INFO
    root.setLevel(level)

    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    formatter = logging.Formatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        root.addHandler(fh)


@click.group()
@click.version_option(version=__version__)
@click.option("--debug", is_flag=True, help="Enable debug logging.")
@click.option("--log-file", type=click.Path(), default=None, help="Write logs to this file.")
@click.pass_context
def main(ctx, debug: bool, log_file: str | None) -> None:
    """Chroma Ingestion - Semantic code search for ChromaDB.

    A semantic-aware code extraction and storage system that intelligently
    chunks code repositories and stores them in ChromaDB for AI agent
    retrieval and context generation.
    """
    # Configure logging once for the CLI run
    configure_logging(debug=debug, log_file=log_file)
    logger.info("Starting chroma-ingest CLI (debug=%s, log_file=%s)", debug, log_file)
    # Keep click context for subcommands if needed
    ctx.obj = {"debug": debug, "log_file": log_file}


@main.command()
@click.argument("folder", type=click.Path(exists=True))
@click.option(
    "--collection",
    default="code_context",
    help="ChromaDB collection name to ingest into.",
)
@click.option(
    "--chunk-size",
    type=int,
    default=1000,
    help="Token size per chunk (default: 1000).",
)
@click.option(
    "--chunk-overlap",
    type=int,
    default=200,
    help="Token overlap between chunks (default: 200).",
)
@click.option(
    "--batch-size",
    type=int,
    default=100,
    help="Chunks per batch upsert (default: 100).",
)
@click.option(
    "--agents",
    is_flag=True,
    help="Use AgentIngester for .agent.md files instead of CodeIngester.",
)
@click.option(
    "--verify",
    is_flag=True,
    help="Run verification queries after ingestion.",
)
def ingest(
    folder: str,
    collection: str,
    chunk_size: int,
    chunk_overlap: int,
    batch_size: int,
    agents: bool,
    verify: bool,
) -> None:
    """Ingest code files into ChromaDB.

    Discovers code files in FOLDER, intelligently chunks them using
    code-aware splitting, and stores them in ChromaDB with metadata.

    Example:
        chroma-ingest ingest ./my-project --collection my_agents --verify
    """
    try:
        folder_path = Path(folder).resolve()

        if agents:
            logger.info("🤖 Starting agent ingestion from %s", folder_path)
            ingester = AgentIngester(
                target_folder=str(folder_path),
                collection_name=collection,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                batch_size=batch_size,
            )
        else:
            logger.info("📂 Starting code ingestion from %s", folder_path)
            ingester = CodeIngester(
                target_folder=str(folder_path),
                collection_name=collection,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                batch_size=batch_size,
            )

        # Run ingestion
        ingester.run()
        logger.info("✅ Ingestion complete! Stored in collection: %s", collection)

        # Run verification if requested
        if verify:
            logger.info("🔍 Running verification queries...")
            retriever = CodeRetriever(collection)
            info = retriever.get_collection_info()
            # `get_collection_info()` returns {'total_chunks': count}
            total = info.get("total_chunks", info.get("count", 0))
            logger.info("📊 Collection stats: %s chunks ingested", total)

    except Exception as e:
        logger.exception("❌ Error during ingestion: %s", e)
        sys.exit(1)


@main.command()
@click.argument("query")
@click.option(
    "--collection",
    default="code_context",
    help="ChromaDB collection to search.",
)
@click.option(
    "-n",
    "--num-results",
    type=int,
    default=5,
    help="Number of results to return (default: 5).",
)
@click.option(
    "--threshold",
    type=float,
    default=0.5,
    help="Distance threshold (lower = more similar, 0.0-1.0).",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results as JSON.",
)
def search(
    query: str,
    collection: str,
    num_results: int,
    threshold: float,
    output_json: bool,
) -> None:
    """Search ingested code with semantic queries.

    Performs semantic search on the specified collection using natural language.

    Example:
        chroma-ingest search "authentication middleware" --num-results 3
    """
    try:
        retriever = CodeRetriever(collection)
        logger.info("🔍 Searching for: %s", query)

        results = retriever.query(query, n_results=num_results)

        if not results:
            logger.warning("❌ No results found.")
            return

        # Filter by threshold if specified
        filtered_results = [r for r in results if r.get("distance", 1.0) <= threshold]

        if not filtered_results:
            click.echo(
                f"⚠️  No results below threshold {threshold}. "
                f"Found {len(results)} results with lower confidence."
            )
            return

        click.echo(f"✅ Found {len(filtered_results)} results:\n")

        if output_json:
            import json

            logger.info(json.dumps(filtered_results, indent=2))
        else:
            for i, result in enumerate(filtered_results, 1):
                distance = result.get("distance", 0)
                confidence = max(0, 1.0 - distance)
                filename = result.get("metadata", {}).get("filename", "Unknown")
                source = result.get("metadata", {}).get("source", "Unknown")

                logger.info("%d. %s (confidence: %.2f%%)", i, filename, confidence * 100)
                logger.info("   📍 %s", source)
                logger.info("   %s...", result["document"][:150].strip())
                logger.info("")

    except Exception as e:
        logger.exception("❌ Search error: %s", e)
        sys.exit(1)


@main.command()
@click.option(
    "--collection",
    default="code_context",
    help="ChromaDB collection to get info about.",
)
def info(collection: str) -> None:
    """Display information about a collection.

    Shows statistics about the ingested code in the specified collection.

    Example:
        chroma-ingest info --collection my_agents
    """
    try:
        retriever = CodeRetriever(collection)
        info_dict = retriever.get_collection_info()

        logger.info("📊 Collection: %s", collection)
        logger.info("   Chunks: %s", info_dict.get("total_chunks", info_dict.get("count", 0)))

        # Display additional metadata if available
        if "metadata_count" in info_dict:
            logger.info("   Metadata entries: %s", info_dict["metadata_count"])

    except Exception as e:
        logger.exception("❌ Error: %s", e)
        sys.exit(1)


@main.command("list-collections")
@click.option(
    "--limit",
    type=int,
    default=100,
    help="Maximum number of collections to list (default: 100).",
)
@click.option(
    "--offset",
    type=int,
    default=0,
    help="Offset for pagination (default: 0).",
)
def list_collections_cmd(limit: int, offset: int) -> None:
    """List all collections in ChromaDB.

    Shows all available collections with their document counts and basic metadata.

    Example:
        chroma-ingest list-collections
        chroma-ingest list-collections --limit 10 --offset 20
    """
    try:
        from chroma_ingestion.clients.chroma import get_chroma_client

        client = get_chroma_client()
        collections = client.list_collections(limit=limit, offset=offset)

        if not collections:
            logger.info("📭 No collections found.")
            return

        logger.info("📚 Collections (%d):\n", len(collections))

        # Display as a formatted table
        for i, collection in enumerate(collections, 1):
            try:
                doc_count = collection.count()
                metadata = collection.metadata or {}
                metadata_str = " | ".join(f"{k}={v}" for k, v in list(metadata.items())[:2])

                if metadata_str:
                    logger.info(
                        "%d. %s (docs: %d) [%s]",
                        i,
                        collection.name,
                        doc_count,
                        metadata_str,
                    )
                else:
                    logger.info("%d. %s (docs: %d)", i, collection.name, doc_count)
            except Exception as e:
                logger.warning("%d. %s (error: %s)", i, collection.name, str(e))

    except Exception as e:
        logger.exception("❌ Error listing collections: %s", e)
        sys.exit(1)


@main.command("rag-query")
@click.argument("query")
@click.option(
    "--collection",
    default="agents_discovery",
    help="Chroma collection to search (default: agents_discovery).",
)
@click.option(
    "-n",
    "--num-results",
    type=int,
    default=5,
    help="Number of results to return (default: 5).",
)
@click.option(
    "--threshold",
    type=float,
    default=0.5,
    help="Distance threshold (lower = more similar, 0.0-1.0, default: 0.5).",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results as JSON.",
)
def rag_query(
    query: str,
    collection: str,
    num_results: int,
    threshold: float,
    output_json: bool,
) -> None:
    """Perform semantic search on agents using RAG.

    Queries ingested agents/prompts/instructions using semantic similarity.
    Great for finding agents matching your needs.

    Example:
        chroma-ingest rag-query "nextjs testing framework"
        chroma-ingest rag-query "security authentication" --num-results 10
        chroma-ingest rag-query "python fastapi" --collection agents_discovery
    """
    try:
        from chroma_ingestion.retrieval.rag_chain import RAGChain

        rag = RAGChain(
            collection_name=collection,
            n_results=num_results,
            distance_threshold=threshold,
        )

        logger.info("🔍 Searching agents for: %s", query)

        if output_json:
            import json

            result = rag.query(query, format_output=False, include_raw=False)
            logger.info(json.dumps(result, indent=2))
        else:
            result = rag.query(query, format_output=True)
            logger.info(result)

    except Exception as e:
        logger.exception("❌ Query error: %s", e)
        sys.exit(1)


@main.command("audit-agents")
@click.option(
    "--collection",
    default="agents_raw",
    help="Chroma collection to audit (default: agents_raw).",
)
@click.option(
    "--similarity",
    type=float,
    default=0.7,
    help="Similarity threshold for consolidation (0.0-1.0, default: 0.7).",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results as JSON.",
)
def audit_agents(
    collection: str,
    similarity: float,
    output_json: bool,
) -> None:
    """Audit agent portfolio for quality, coverage, and consolidation opportunities.

    Analyzes all agents in the collection and produces a comprehensive report
    showing category distribution, tech stack coverage, gaps, and consolidation
    candidates (agents that could be merged).

    Example:
        chroma-ingest audit-agents
        chroma-ingest audit-agents --collection agents_raw --similarity 0.65
        chroma-ingest audit-agents --json
    """
    try:
        from chroma_ingestion.audit.agent_auditor import AgentAuditor

        auditor = AgentAuditor(collection_name=collection)
        
        logger.info("📊 Auditing agent portfolio...")
        auditor.load_agents(limit=100000)  # Load all agents (26K+ documents)
        auditor.analyze_coverage()
        auditor.find_consolidation_candidates(similarity_threshold=similarity)

        if output_json:
            import json

            summary = auditor.get_audit_summary()
            logger.info(json.dumps(summary, indent=2, default=str))
        else:
            report = auditor.generate_report()
            logger.info(report)

    except Exception as e:
        logger.exception("❌ Audit error: %s", e)
        sys.exit(1)


@main.command("enrich-collection")
@click.argument("collection")
@click.option(
    "--batch-size",
    type=int,
    default=100,
    help="Documents to process per batch (default: 100).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview enrichment without saving changes.",
)
@click.option(
    "--skip-existing",
    is_flag=True,
    default=True,
    help="Skip documents that already have category metadata.",
)
def enrich_collection(
    collection: str,
    batch_size: int,
    dry_run: bool,
    skip_existing: bool,
) -> None:
    """Enrich collection documents with inferred metadata.

    Analyzes document content to automatically infer category, tech stack,
    and description metadata for documents lacking enriched information.

    Useful for enriching agents_raw collection to enable full portfolio
    analysis on all 26K documents.

    Example:
        chroma-ingest enrich-collection agents_raw
        chroma-ingest enrich-collection agents_raw --batch-size 50
        chroma-ingest enrich-collection agents_raw --dry-run
    """
    try:
        from chroma_ingestion.enrichment.metadata_inferrer import MetadataInferrer

        inferrer = MetadataInferrer()
        
        logger.info(f"🔍 Starting enrichment of {collection}...")
        if dry_run:
            logger.info("⚠️  Running in DRY-RUN mode (no changes will be saved)")

        result = inferrer.enrich_collection(
            collection_name=collection,
            batch_size=batch_size,
            dry_run=dry_run,
            skip_existing=skip_existing,
        )

        logger.info(f"📊 Enrichment Summary:")
        logger.info(f"  Total documents: {result['total_documents']}")
        logger.info(f"  Processed: {result['processed']}")
        logger.info(f"  Enriched: {result['enriched']}")
        logger.info(f"  Skipped: {result['skipped']}")
        logger.info(f"  Failed: {result['failed_count']}")

        if result["failed_count"] > 0:
            logger.warning(f"⚠️  {result['failed_count']} documents failed to enrich:")
            for doc_id, error in result["failed_ids"][:5]:  # Show first 5
                logger.warning(f"    - {doc_id}: {error}")
            if len(result["failed_ids"]) > 5:
                logger.warning(f"    ... and {len(result['failed_ids']) - 5} more")

        if not dry_run and result["enriched"] > 0:
            logger.info(f"✅ Successfully enriched {result['enriched']} documents")
        elif dry_run:
            logger.info(f"✅ Dry-run complete: would enrich {result['enriched']} documents")

    except Exception as e:
        logger.exception("❌ Enrichment error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

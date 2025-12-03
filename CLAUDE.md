# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Chroma Ingestion** is a semantic-aware code extraction and storage system that chunks code repositories and stores them in ChromaDB for AI agent retrieval. It's a RAG system for large codebase indexing.

## Build, Test & Lint Commands

All automation uses **Nox** (configured in `noxfile.py`):

```bash
# Testing
nox -s test                      # Run pytest with coverage
nox -s test -- tests/unit        # Specific test subset
pytest -v --cov=chroma_ingestion # Direct pytest

# Code Quality
nox -s lint                      # Ruff linter
nox -s fmt                       # Ruff formatter
nox -s type_check                # mypy (strict mode)

# Documentation
nox -s docs                      # Build mkdocs

# All checks
nox -s lint test type_check      # Full quality gate
```

## CLI Commands

```bash
# Ingestion
chroma-ingest <folder> --collection <name> --verify
chroma-ingest --agents    # Use AgentIngester for .agent.md files

# Search
chroma-search "query" --collection <name> -n 5 --threshold 0.8

# Info
chroma-info --collection <name>
```

## Architecture

### Singleton Client Pattern (MANDATORY)

```python
# CORRECT - use factory function
from chroma_ingestion.clients.chroma import get_chroma_client
client = get_chroma_client()

# WRONG - creates connection pool issues
client = chromadb.HttpClient(host='localhost', port=9500)
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `clients/chroma.py` | Singleton HttpClient factory |
| `ingestion/base.py` | CodeIngester - semantic chunking, batch upsert |
| `ingestion/agents.py` | AgentIngester - YAML frontmatter, tech stack extraction |
| `retrieval/retriever.py` | CodeRetriever, MultiCollectionSearcher |
| `cli.py` | Click-based CLI interface |
| `config.py` | Environment configuration (CHROMA_HOST, CHROMA_PORT) |

### Chunking Strategy

Uses LangChain's Markdown splitter for all file types:
```python
splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.MARKDOWN,
    chunk_size=1000,
    chunk_overlap=200,
)
```

### Metadata Tracking (Required)

Every chunk must include:
```python
metadata = {
    "source": str(file_path),
    "filename": os.path.basename(file_path),
    "chunk_index": chunk_num,
    "folder": os.path.dirname(file_path),
    "file_type": os.path.splitext(file_path)[1],
}
```

### Distance Scoring

- < 0.8: Excellent match
- 0.8-1.0: Good match
- 1.0-1.2: Acceptable match
- \> 1.2: Poor match

## Testing

**Fixtures** (in `tests/conftest.py`):
- `tmp_code_folder` - Temp folder with sample files
- `sample_agent_files` - Agent .md files with YAML frontmatter
- `mock_chroma_client` - Mocked ChromaDB client
- `chroma_config`, `ingestion_params`, `sample_query`

**Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`

**Coverage**: Minimum 80% with branch coverage

## Configuration

Environment variables (defaults work for local dev):
```bash
CHROMA_HOST=localhost  # default
CHROMA_PORT=9500       # default
```

## Code Quality

- **Line length**: 100
- **Type hints**: 100% coverage, mypy strict mode
- **Pre-commit hooks**: ruff format, ruff check, mypy

## Batch Upsert Pattern

Always batch ingestions (100-500 chunks):
```python
for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    collection.upsert(documents=batch, ids=ids_batch, metadatas=meta_batch)
```

Use `upsert()` not `add()` to handle duplicates gracefully.

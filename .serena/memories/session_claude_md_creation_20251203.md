# Session: CLAUDE.md Creation for vibe-tools and chroma

**Date**: 2025-12-03
**Session Type**: Documentation/Configuration

## Task Completed

Created root-level CLAUDE.md files for both repositories in the workspace:

### 1. /home/ob/Development/Tools/vibe-tools/CLAUDE.md

Created comprehensive guidance file covering:
- **Repository Overview**: Monorepo for AI-assisted development platform
- **Component Table**: 5 main subprojects (scf, SuperAgent-MCP, SuperFlag_Framework, ccp, ghc_tools)
- **Build Commands**: UV/Makefile for Python, npm for TypeScript components
- **Python Environment Rules**: UV-only requirement (critical)
- **Core Architecture**: PM Agent patterns, pytest plugin, parallel execution
- **Asset Conventions**: YAML frontmatter for agents, instructions, prompts, chatmodes
- **Git Workflow**: Branch structure with worktree guidance
- **MCP Integration**: Priority server listing

Note: Existing `scf/CLAUDE.md` provides detailed SuperClaude Framework-specific guidance.

### 2. /home/ob/Development/Tools/chroma/CLAUDE.md

Created comprehensive guidance file covering:
- **Build Commands**: Nox automation (test, lint, fmt, type_check, docs)
- **CLI Commands**: chroma-ingest, chroma-search, chroma-info
- **Singleton Client Pattern**: Mandatory for connection pool management
- **Key Modules**: clients/chroma.py, ingestion/base.py, retrieval/retriever.py
- **Chunking Strategy**: LangChain Markdown splitter (1000 tokens, 200 overlap)
- **Metadata Requirements**: source, filename, chunk_index, folder, file_type
- **Distance Scoring**: Thresholds for match quality (<0.8 excellent, 0.8-1.0 good, etc.)
- **Testing**: Fixtures, markers, 80% coverage minimum
- **Code Quality**: 100 line length, mypy strict mode

Incorporated key information from existing `.github/copilot-instructions.md`.

## Key Discoveries

1. **vibe-tools** already had detailed `scf/CLAUDE.md` - root file serves as entry point
2. **chroma** had comprehensive `.github/copilot-instructions.md` - consolidated into CLAUDE.md
3. Both projects use modern Python tooling (UV for vibe-tools, Nox for chroma)
4. Both projects emphasize type safety and strict code quality

## Files Created

- `/home/ob/Development/Tools/vibe-tools/CLAUDE.md`
- `/home/ob/Development/Tools/chroma/CLAUDE.md`

## Cross-Session Relevance

These CLAUDE.md files will guide future Claude Code sessions working in these repositories, providing quick access to build commands, architecture patterns, and critical conventions.

#!/bin/bash

# Chroma-Agent Integration Setup Script
# This script sets up the dual-collection architecture for agent evolution

set -e  # Exit on error

echo "🚀 Chroma-Agent Integration Setup"
echo "=================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Workspace paths
CHROMA_DIR="/home/ob/Development/Tools/chroma"
VIBE_TOOLS_DIR="/home/ob/Development/Tools/vibe-tools"
AGENT_DISCOVERY_DIR="$VIBE_TOOLS_DIR/agent-discovery-system"

# Step 1: Check prerequisites
echo "${YELLOW}Step 1: Checking prerequisites...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi
echo "${GREEN}✓ Docker is running${NC}"

# Check if Chroma directory exists
if [ ! -d "$CHROMA_DIR" ]; then
    echo "${RED}❌ Chroma directory not found at $CHROMA_DIR${NC}"
    exit 1
fi
echo "${GREEN}✓ Chroma directory found${NC}"

# Check if vibe-tools directory exists
if [ ! -d "$VIBE_TOOLS_DIR" ]; then
    echo "${RED}❌ Vibe-tools directory not found at $VIBE_TOOLS_DIR${NC}"
    exit 1
fi
echo "${GREEN}✓ Vibe-tools directory found${NC}"

echo ""

# Step 2: Start Chroma server
echo "${YELLOW}Step 2: Starting Chroma server...${NC}"
cd "$CHROMA_DIR"

# Check if Chroma is already running
if docker ps | grep -q chroma; then
    echo "${GREEN}✓ Chroma server already running${NC}"
else
    docker-compose up -d
    echo "${GREEN}✓ Chroma server started${NC}"
    echo "  Waiting 5 seconds for server to initialize..."
    sleep 5
fi

# Verify Chroma is accessible
if ! curl -s http://localhost:9500/api/v1/heartbeat > /dev/null 2>&1; then
    echo "${YELLOW}⚠️  Chroma server might not be ready yet. Waiting 10 more seconds...${NC}"
    sleep 10
fi
echo ""

# Step 3: Ingest raw collection from all agent sources
echo "${YELLOW}Step 3: Ingesting raw baseline collection...${NC}"
echo "  Sources:"
echo "    - $VIBE_TOOLS_DIR/ghc_tools/"
echo "    - $VIBE_TOOLS_DIR/agents/"
echo "    - $VIBE_TOOLS_DIR/SuperAgent-MCP/"
echo "    - $VIBE_TOOLS_DIR/scf/ (agents)"
echo "  Collection: agents_raw"
echo ""

# Ingest ghc_tools (primary agent source)
echo "  Ingesting ghc_tools/..."
chroma-ingest ingest "$VIBE_TOOLS_DIR/ghc_tools" \
    --collection agents_raw

# Ingest agents directory if it exists
if [ -d "$VIBE_TOOLS_DIR/agents" ]; then
    echo "  Ingesting agents/..."
    chroma-ingest ingest "$VIBE_TOOLS_DIR/agents" \
        --collection agents_raw
fi

# Ingest SuperAgent-MCP agents if directory exists
if [ -d "$VIBE_TOOLS_DIR/SuperAgent-MCP" ]; then
    echo "  Ingesting SuperAgent-MCP/..."
    chroma-ingest ingest "$VIBE_TOOLS_DIR/SuperAgent-MCP" \
        --collection agents_raw
fi

# Ingest scf agents if directory exists
if [ -d "$VIBE_TOOLS_DIR/scf" ]; then
    echo "  Ingesting scf/..."
    chroma-ingest ingest "$VIBE_TOOLS_DIR/scf" \
        --collection agents_raw
fi

# Run final verification
echo "  Running verification..."
chroma-ingest info --collection agents_raw

echo ""
echo "${GREEN}✓ Raw collection ingested from all sources${NC}"
echo ""

# Step 4: Ingest enriched collection
echo "${YELLOW}Step 4: Ingesting enriched metadata collection...${NC}"
echo "  Collection: agents_discovery"
echo ""

cd "$AGENT_DISCOVERY_DIR"
uv run agent-discover ingest \
    --vibe-tools "$VIBE_TOOLS_DIR" \
    --clear

echo ""
echo "${GREEN}✓ Enriched collection ingested${NC}"
echo ""

# Step 5: Show collection stats
echo "${YELLOW}Step 5: Collection Statistics${NC}"
echo ""

echo "Raw collection (agents_raw):"
cd "$CHROMA_DIR"
chroma-ingest info --collection agents_raw
echo ""

echo "Enriched collection (agents_discovery):"
cd "$AGENT_DISCOVERY_DIR"
uv run agent-discover stats
echo ""

# Step 6: Run sample searches
echo "${YELLOW}Step 6: Running sample searches...${NC}"
echo ""

echo "Testing raw collection search:"
cd "$CHROMA_DIR"
chroma-ingest search "nextjs typescript" \
    --collection agents_raw \
    -n 3 \
    --threshold 1.2
echo ""

echo "Testing enriched collection search:"
cd "$AGENT_DISCOVERY_DIR"
uv run agent-discover search "nextjs typescript" -n 3
echo ""

# Step 7: Summary
echo "${GREEN}=================================="
echo "✅ Setup Complete!"
echo "==================================${NC}"
echo ""
echo "Collections created:"
echo "  1. agents_raw (ingested from ghc_tools, agents, SuperAgent-MCP, scf)"
echo "  2. agents_discovery (enriched with metadata)"
echo ""

# Show chunk counts
echo "Collection sizes:"
cd "$CHROMA_DIR"
chroma-ingest info --collection agents_raw | grep -i "chunks" || echo "  agents_raw: See output above"
cd "$AGENT_DISCOVERY_DIR"
uv run agent-discover stats | grep -i "chunks" || echo "  agents_discovery: See output above"
echo ""
echo "Next steps:"
echo "  1. Review baseline_metrics.txt for search quality"
echo "  2. Run similarity analysis (see INTEGRATION_QUICK_START.md)"
echo "  3. Start Phase 2: Analysis & Clustering"
echo ""
echo "Quick commands:"
echo "  Search raw:      chroma-ingest search 'query' --collection agents_raw -n 5 --threshold 1.2"
echo "  Search enriched: uv run agent-discover search 'query' -n 5"
echo "  Stats:           uv run agent-discover stats"
echo ""
echo "📚 Documentation:"
echo "  - Quick Start: $CHROMA_DIR/INTEGRATION_QUICK_START.md"
echo "  - Full Guide:  $CHROMA_DIR/CHROMA_AGENT_INTEGRATION_BRAINSTORM.md"
echo ""

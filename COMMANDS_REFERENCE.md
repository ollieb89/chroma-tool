# Quick Command Reference

**Copy-paste ready commands for your workspace**

---

## Prerequisites

```bash
# Start Chroma server (run once)
cd /home/ob/Development/Tools/chroma
docker-compose up -d

# Check server is running
docker ps | grep chroma
curl http://localhost:9500/api/v1/heartbeat
```

---

## Setup (One-Time)

```bash
# Automated setup (recommended)
cd /home/ob/Development/Tools/chroma
./setup_agent_integration.sh

# Or manual setup:
# 1. Ingest raw collection from all agent sources
cd /home/ob/Development/Tools/chroma

# Ingest ghc_tools
chroma-ingest ingest /home/ob/Development/Tools/vibe-tools/ghc_tools \
    --collection agents_raw

# Ingest additional agent sources
chroma-ingest ingest /home/ob/Development/Tools/vibe-tools/agents \
    --collection agents_raw

chroma-ingest ingest /home/ob/Development/Tools/vibe-tools/SuperAgent-MCP \
    --collection agents_raw

chroma-ingest ingest /home/ob/Development/Tools/vibe-tools/scf \
    --collection agents_raw

# Verify
chroma-ingest info --collection agents_raw

# 2. Ingest enriched collection
cd /home/ob/Development/Tools/vibe-tools/agent-discovery-system
uv run agent-discover ingest \
    --vibe-tools /home/ob/Development/Tools/vibe-tools \
    --clear
```

---

## Common Operations

### Search Agents

```bash
# Raw collection (threshold 1.2 for acceptable matches)
cd /home/ob/Development/Tools/chroma
chroma-ingest search "nextjs typescript" \
    --collection agents_raw \
    -n 5 \
    --threshold 1.2

# Enriched collection
cd /home/ob/Development/Tools/vibe-tools/agent-discovery-system
uv run agent-discover search "nextjs typescript" -n 5

# More permissive search (see all results)
chroma-ingest search "nextjs typescript" \
    --collection agents_raw \
    -n 10 \
    --threshold 2.0
```

### Collection Info

```bash
# Raw collection stats
cd /home/ob/Development/Tools/chroma
chroma-ingest info --collection agents_raw

# Enriched collection stats
cd /home/ob/Development/Tools/vibe-tools/agent-discovery-system
uv run agent-discover stats
uv run agent-discover list --type agent
uv run agent-discover list --category frontend
```

### Discovery & Generation

```bash
cd /home/ob/Development/Tools/vibe-tools/agent-discovery-system

# Discover agents for a codebase
uv run agent-discover discover --path /home/ob/Development/Tools/chroma

# Generate AGENTS.md (dry-run first)
uv run agent-discover generate \
    --path /home/ob/Development/Tools/chroma \
    --dry-run

# Generate for real
uv run agent-discover generate \
    --path /home/ob/Development/Tools/chroma \
    --output ./
```

---

## Baseline Testing Queries

```bash
cd /home/ob/Development/Tools/chroma

# Save baseline results
{
    echo "# Baseline Query Results - $(date)"
    echo ""

    echo "## Query 1: NextJS TypeScript"
    chroma-ingest search "nextjs typescript server components" \
        --collection agents_raw -n 3 --threshold 1.2

    echo ""
    echo "## Query 2: React Accessibility"
    chroma-ingest search "react accessibility wcag 2.1" \
        --collection agents_raw -n 3 --threshold 1.2

    echo ""
    echo "## Query 3: Python FastAPI"
    chroma-ingest search "python fastapi async authentication" \
        --collection agents_raw -n 3 --threshold 1.2

    echo ""
    echo "## Query 4: Playwright Testing"
    chroma-ingest search "playwright e2e testing ci/cd" \
        --collection agents_raw -n 3 --threshold 1.2

    echo ""
    echo "## Query 5: Security OWASP"
    chroma-ingest search "security owasp top 10 vulnerabilities" \
        --collection agents_raw -n 3 --threshold 1.2

} > baseline_metrics_$(date +%Y%m%d).txt

echo "✅ Baseline results saved to baseline_metrics_$(date +%Y%m%d).txt"
```

---

## Python Analysis Scripts

```bash
cd /home/ob/Development/Tools/vibe-tools/agent-discovery-system

# Interactive Python session
uv run python

# In Python:
from agent_discovery.ingester import AgentRetriever

retriever = AgentRetriever("agents_discovery")

# Get all frontend agents
frontend = retriever.search_by_category("frontend", n_results=20)
print(f"Found {len(frontend)} frontend agents")

# Find similar agents
for agent in frontend[:3]:
    name = agent['metadata']['agent_name']
    similar = retriever.search(agent['document'][:500], n_results=5)
    print(f"\n{name} is similar to:")
    for s in similar:
        print(f"  - {s['metadata']['agent_name']} (distance: {s['distance']:.2f})")
```

---

## Troubleshooting

```bash
# Check Chroma is running
docker ps | grep chroma
curl http://localhost:9500/api/v1/heartbeat

# Restart Chroma
cd /home/ob/Development/Tools/chroma
docker-compose restart

# Check logs
docker-compose logs -f

# Re-ingest if collection is empty
chroma-ingest ingest /home/ob/Development/Tools/vibe-tools/ghc_tools \
    --collection agents_raw \
    --verify

# Clear and re-ingest enriched collection
cd /home/ob/Development/Tools/vibe-tools/agent-discovery-system
uv run agent-discover ingest \
    --vibe-tools /home/ob/Development/Tools/vibe-tools \
    --clear
```

---

## Distance Threshold Guide

| Threshold | Use Case | Expected Results |
|-----------|----------|------------------|
| 0.5 | Very strict | Only near-perfect matches (default, too strict for agents) |
| 0.8 | Excellent | High-quality matches recommended for code search |
| 1.0 | Good | Quality matches for general use |
| **1.2** | **Acceptable** | **Recommended for agent search** |
| 1.5 | Permissive | Broader matches, useful for exploration |
| 2.0 | Very permissive | See all results regardless of distance |

**Rule of thumb**: Start with `--threshold 1.2` for agent searches.

---

## Workspace Paths

| Resource | Path |
|----------|------|
| Chroma | `/home/ob/Development/Tools/chroma` |
| Vibe-tools | `/home/ob/Development/Tools/vibe-tools` |
| Agent Discovery | `/home/ob/Development/Tools/vibe-tools/agent-discovery-system` |
| Agent Sources | `/home/ob/Development/Tools/vibe-tools/ghc_tools` |
| Setup Script | `/home/ob/Development/Tools/chroma/setup_agent_integration.sh` |

---

## Next Steps

After setup, proceed to:

1. **Week 1 Tasks** (see INTEGRATION_QUICK_START.md)
   - Run 10 test queries
   - Document baseline distances
   - Identify weak matches

2. **Week 2 Tasks** (see CHROMA_AGENT_INTEGRATION_BRAINSTORM.md)
   - Build similarity matrices
   - Find consolidation candidates
   - Document cross-pollination opportunities

3. **Week 3 Tasks**
   - Apply enhancements to 10 agents
   - Create `agents_evolved` collection
   - A/B test against baseline

---

**Quick Links**:
- Setup Script: `./setup_agent_integration.sh`
- Quick Start: `INTEGRATION_QUICK_START.md`
- Full Guide: `CHROMA_AGENT_INTEGRATION_BRAINSTORM.md`
- Session Memory: `.serena/memories/chroma_agent_integration_session_20251203.md`

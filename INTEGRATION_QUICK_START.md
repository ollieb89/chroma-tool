# Chroma-Agent Integration: Quick Start Guide

**TL;DR**: Use Chroma's semantic ingestion to build a multi-tier agent database, then apply similarity analysis and cross-pollination to generate improved agent variants.

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

**Start Chroma server first:**
```bash
cd /home/ob/Development/Tools/chroma
docker-compose up -d  # Start Chroma in background
```

### Fix volume permissions (host action)

If the Chroma container fails to start as a non-root user due to volume permissions, run the helper script from the host to fix the named volume ownership. This requires `sudo` on the host because Docker's named volumes live under `/var/lib/docker`.

On the host (run from the repository root):

```bash
cd /home/ob/Development/Tools/chroma
./fix_chroma_volume_permissions.sh
```

The script will stop the `chroma` service if running, `chown` the volume to `1000:1000`, and restart the `chroma` service. After running it, verify health with:

```bash
docker ps --filter name=chroma-test --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker inspect --format='{{json .State.Health}}' chroma-test
docker compose logs --no-color --tail 200 chroma
```

If you cannot run `sudo` on the host or prefer a simpler fallback, you can run the container as root (less secure) by re-adding `user: root` to the `chroma` service in `docker-compose.yml`.

Note: The Docker image now contains a hardened entrypoint (`docker-entrypoint.sh`) that will idempotently fix ownership of common persist paths and verify they are writable before dropping privileges to the application user. If the entrypoint cannot make a path writable it will fail with a clear hint showing the `docker run --rm -v chroma_data:/data ... chown -R 1000:1000 /data` command to fix the host volume.


### 1. Set Up Dual Collections

```bash
# Collection 1: Raw baseline (chroma-ingestion)
# Now ingests from ALL agent sources: ghc_tools, agents, SuperAgent-MCP, scf
cd /home/ob/Development/Tools/chroma
./setup_agent_integration.sh  # Automated (recommended)

# Or manually:
chroma-ingest ingest /home/ob/Development/Tools/vibe-tools/ghc_tools --collection agents_raw
chroma-ingest ingest /home/ob/Development/Tools/vibe-tools/agents --collection agents_raw
chroma-ingest ingest /home/ob/Development/Tools/vibe-tools/SuperAgent-MCP --collection agents_raw
chroma-ingest ingest /home/ob/Development/Tools/vibe-tools/scf --collection agents_raw

# Collection 2: Enriched metadata (agent-discovery)
cd /home/ob/Development/Tools/vibe-tools/agent-discovery-system
uv run agent-discover ingest --vibe-tools /home/ob/Development/Tools/vibe-tools --clear
```

### 2. Run Baseline Discovery

```bash
# Test current performance (from agent-discovery-system directory)
cd /home/ob/Development/Tools/vibe-tools/agent-discovery-system

uv run agent-discover discover --path /home/ob/Development/Tools/chroma
uv run agent-discover search "nextjs typescript testing"
uv run agent-discover stats
```

### 3. Analyze Similarities

```python
from agent_discovery.ingester import AgentRetriever

retriever = AgentRetriever("agents_discovery")

# Find similar agents in a category
frontend_agents = retriever.search_by_category("frontend", n_results=20)

# Build similarity matrix
for agent in frontend_agents[:5]:
    name = agent['metadata']['agent_name']
    similar = retriever.search(agent['document'][:500], n_results=5)
    print(f"{name} is similar to:")
    for s in similar:
        print(f"  - {s['metadata']['agent_name']} (distance: {s['distance']:.2f})")
```

---

## 🎯 Key Integration Patterns

### Pattern 1: Semantic Diffing

**Find unique capabilities between agents**:

```python
def find_unique_capabilities(source_agent: str, target_agent: str):
    """Extract what source has that target lacks."""
    retriever = AgentRetriever("agents_discovery")

    source_chunks = retriever.collection.get(where={"agent_name": source_agent})

    unique = []
    for chunk in source_chunks['documents']:
        results = retriever.search(
            query=chunk,
            where={"agent_name": target_agent},
            n_results=1
        )

        if not results or results[0]['distance'] > 1.0:
            unique.append(chunk)

    return unique
```

### Pattern 2: Cross-Pollination

**Transfer capabilities between related agents**:

```python
def enhance_agent_with_related_capabilities(agent_name: str, category: str):
    """Enhance agent with best practices from category."""
    retriever = AgentRetriever("agents_discovery")

    # Get agent's current content
    agent = retriever.collection.get(where={"agent_name": agent_name})

    # Find best-performing agents in same category
    category_agents = retriever.search_by_category(category, n_results=10)

    # Extract top patterns
    enhancements = []
    for related in category_agents:
        if related['metadata']['agent_name'] != agent_name:
            unique = find_unique_capabilities(
                related['metadata']['agent_name'],
                agent_name
            )
            if unique:
                enhancements.extend(unique[:2])  # Top 2 unique capabilities

    return enhancements
```

### Pattern 3: Consolidation Detection

**Identify agents that should be merged**:

```python
def find_merge_candidates(threshold: float = 0.6):
    """Find agents with high overlap."""
    retriever = AgentRetriever("agents_discovery")
    all_agents = retriever.get_all_agents(limit=500)

    candidates = []
    for i, agent1 in enumerate(all_agents):
        for agent2 in all_agents[i+1:]:
            meta1, meta2 = agent1['metadata'], agent2['metadata']

            # Same category + high tech stack overlap = merge candidate
            tech1 = set(meta1.get('tech_stack', '').split(','))
            tech2 = set(meta2.get('tech_stack', '').split(','))
            overlap = len(tech1 & tech2) / max(len(tech1), len(tech2))

            if (meta1.get('category') == meta2.get('category') and
                overlap > threshold):
                candidates.append({
                    'agent1': meta1['agent_name'],
                    'agent2': meta2['agent_name'],
                    'overlap': overlap,
                    'category': meta1['category']
                })

    return sorted(candidates, key=lambda x: x['overlap'], reverse=True)
```

---

## 📊 Success Metrics

| Metric | Baseline | Target | How to Measure |
|--------|----------|--------|----------------|
| Average Distance | 0.95 | < 0.80 | Run test query suite |
| Coverage (< 0.8) | 40% | > 60% | % of queries with excellent matches |
| Agent Count | 340 | 250-300 | Post-consolidation |
| Unique Tech Stack | 80 | > 100 | Distinct tech_stack values |

---

## 🔄 Evolution Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: INGEST → agents_raw + agents_discovery             │
│  Stage 2: ANALYZE → Similarity matrices + Clusters           │
│  Stage 3: ENHANCE → Cross-pollinate + Consolidate            │
│  Stage 4: VALIDATE → Quality checks + A/B testing            │
│  Stage 5: DEPLOY → agents_evolved → Production               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Essential Commands

```bash
# Chroma Ingestion (from /home/ob/Development/Tools/chroma)
chroma-ingest ingest <folder> --collection <name> --verify
chroma-ingest search "<query>" --collection <name> -n 5 --threshold 1.2
chroma-ingest info --collection <name>

# Agent Discovery (from /home/ob/Development/Tools/vibe-tools/agent-discovery-system)
uv run agent-discover ingest --vibe-tools /home/ob/Development/Tools/vibe-tools --clear
uv run agent-discover discover --path <codebase>
uv run agent-discover generate --path <codebase> --dry-run
uv run agent-discover search "<query>"
uv run agent-discover list --type agent --category testing
uv run agent-discover stats
```

---

## 🎯 Immediate Action Items

### Week 1: Baseline
- [ ] Set up dual collections (raw + enriched)
- [ ] Run 10 test queries and document distances
- [ ] Identify 3 weak matches (distance > 1.2)

### Week 2: Analysis
- [ ] Build similarity matrices for each category
- [ ] Find 5 consolidation candidates
- [ ] Document cross-pollination opportunities

### Week 3: Enhancement
- [ ] Apply enhancements to 10 agents
- [ ] Create `agents_evolved` collection
- [ ] A/B test against baseline

### Week 4: Deployment
- [ ] Validate improvements (>10% distance reduction)
- [ ] Deploy evolved agents
- [ ] Document learnings

---

## 📚 Reference Documents

- **Full Brainstorm**: `CHROMA_AGENT_INTEGRATION_BRAINSTORM.md`
- **Chroma Docs**: `chroma/README.md`, `chroma/CLAUDE.md`
- **Agent Discovery Docs**: `vibe-tools/agent-discovery-system/README.md`

---

## ⚠️ Critical Constraints

1. **Singleton Client**: MUST use `get_chroma_client()` factory
2. **Metadata Types**: Only string, int, float, bool (lists as CSV)
3. **Distance Calibration**: Thresholds drift with model updates
4. **Chunk Overlap**: Must be < chunk_size (use 10-20%)

---

## 🚨 Quick Troubleshooting

**No results found**:
- Check Chroma server is running: `docker ps | grep chroma`
- Check collection exists: `uv run agent-discover stats`
- Verify ingestion: `chroma-ingest info --collection agents_raw`

**Poor match quality** (default threshold 0.5 is too strict):
- Use higher threshold: `--threshold 1.2` (acceptable matches)
- For exploration: `--threshold 2.0` (see all results)
- Test different chunk sizes (1000 → 1500)

**Duplicate agents in results**:
- Expected behavior (multiple chunks per agent)
- Use deduplication in code (already implemented)

---

**Next Step**: Run the Week 1 baseline tasks, then review the full brainstorm document for detailed implementation strategies.

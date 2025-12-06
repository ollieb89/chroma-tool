"""Agent auditor: analyze agent portfolio for quality, coverage, and consolidation."""

from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from typing import Any

from chroma_ingestion.clients.chroma import get_chroma_client
from chroma_ingestion.retrieval.rag_chain import RAGChain

logger = logging.getLogger(__name__)


class AgentAuditor:
    """Analyze agents in Chroma for value, coverage, and consolidation opportunities.

    Provides insights on:
    - Tech stack coverage (which technologies are well-represented)
    - Category balance (are some categories over/under-represented)
    - Consolidation candidates (similar agents that could merge)
    - Coverage gaps (missing tech stacks or categories)
    - Value metrics (agent complexity, specificity)
    """

    def __init__(self, collection_name: str = "agents_raw"):
        """Initialize auditor.

        Args:
            collection_name: Collection to analyze (default: agents_raw)
        """
        self.collection_name = collection_name
        self.rag = RAGChain(collection_name=collection_name)
        self.agents: list[dict[str, Any]] = []
        self.coverage_analysis: dict[str, Any] = {}
        self.consolidation_candidates: list[dict[str, Any]] = []

    def load_agents(self, limit: int = 1000) -> int:
        """Load all agents from collection.

        Aggregates document chunks by file path to create unique "agents".

        Args:
            limit: Maximum chunks to load (will aggregate into fewer unique agents)

        Returns:
            Number of unique agents loaded
        """
        try:
            client = get_chroma_client()
            collection = client.get_collection(self.collection_name)

            # Get all chunks
            results = collection.get(limit=limit)

            if not results or not results.get("documents"):
                logger.warning("⚠️  No agents found in collection")
                return 0

            # Aggregate chunks by file path (everything before the `:`)
            agents_by_file: dict[str, dict[str, Any]] = {}
            
            for doc_id, meta in zip(results.get("ids", []), results.get("metadatas", [])):
                # Extract file path (everything before `:chunk_number`)
                file_path = doc_id.split(':')[0]
                
                # Parse tech_stack from JSON string
                tech_stack = []
                tech_stack_raw = meta.get("tech_stack", "")
                if tech_stack_raw:
                    if isinstance(tech_stack_raw, str):
                        try:
                            # Try to parse as JSON array
                            if tech_stack_raw.startswith('['):
                                tech_stack = json.loads(tech_stack_raw)
                            else:
                                # Fallback to comma-separated
                                tech_stack = [t.strip() for t in tech_stack_raw.split(",") if t.strip()]
                        except json.JSONDecodeError:
                            tech_stack = [t.strip() for t in tech_stack_raw.split(",") if t.strip()]
                    else:
                        tech_stack = tech_stack_raw if isinstance(tech_stack_raw, list) else []
                
                if file_path not in agents_by_file:
                    # First chunk for this file
                    agents_by_file[file_path] = {
                        "name": file_path.split('/')[-1],  # Use filename as agent name
                        "path": file_path,
                        "type": meta.get("agent_type", "agent"),
                        "category": meta.get("category", "unknown"),
                        "tech_stack": tech_stack,
                        "description": meta.get("description", ""),
                        "source": meta.get("source", "unknown"),
                        "complexity": meta.get("complexity", "unknown"),
                        "chunk_count": 1,
                        "raw_metadata": meta,
                    }
                else:
                    # Subsequent chunk - merge data
                    agents_by_file[file_path]["chunk_count"] += 1
                    agents_by_file[file_path]["tech_stack"] = list(set(
                        agents_by_file[file_path]["tech_stack"] + tech_stack
                    ))

            # Convert to list
            self.agents = list(agents_by_file.values())
            logger.info("✅ Loaded %d unique agents from %s", len(self.agents), self.collection_name)
            return len(self.agents)

        except Exception as e:
            logger.error("❌ Error loading agents: %s", e)
            return 0

    def analyze_coverage(self) -> dict[str, Any]:
        """Analyze coverage of agents by category and tech stack.

        Returns:
            Coverage analysis dictionary
        """
        if not self.agents:
            self.load_agents()

        # Count by category
        categories = Counter(a.get("category", "unknown") for a in self.agents)
        
        # Count by tech stack
        all_techs: list[str] = []
        for agent in self.agents:
            all_techs.extend([t.strip() for t in agent.get("tech_stack", []) if t.strip()])
        tech_counts = Counter(all_techs)

        # Count by type
        types = Counter(a.get("type", "unknown") for a in self.agents)

        # Identify gaps (tech stacks with <2 agents)
        gaps = [tech for tech, count in tech_counts.items() if count < 2]

        self.coverage_analysis = {
            "total_agents": len(self.agents),
            "categories": dict(categories.most_common(10)),
            "top_tech_stacks": dict(tech_counts.most_common(15)),
            "agent_types": dict(types),
            "coverage_gaps": gaps[:10],  # Tech stacks with poor coverage
            "category_balance": {
                "most_common": categories.most_common(1)[0] if categories else None,
                "least_common": categories.most_common()[-1] if categories else None,
                "spread": len(categories),
            },
        }

        return self.coverage_analysis

    def find_consolidation_candidates(
        self,
        similarity_threshold: float = 0.7,
        max_candidates: int = 10,
    ) -> list[dict[str, Any]]:
        """Find agents that could be consolidated (similar/overlapping).

        Uses semantic similarity and metadata overlap to identify candidates.

        Args:
            similarity_threshold: Similarity score threshold for candidates
            max_candidates: Maximum pairs to return

        Returns:
            List of consolidation candidate pairs
        """
        if not self.agents:
            self.load_agents()

        logger.info("🔍 Analyzing %d agents for consolidation opportunities...", len(self.agents))

        candidates: list[dict[str, Any]] = []

        # Group agents by category
        by_category = defaultdict(list)
        for agent in self.agents:
            cat = agent.get("category", "unknown")
            by_category[cat].append(agent)

        # Within each category, find similar agents
        for category, agents_in_cat in by_category.items():
            if len(agents_in_cat) < 2:
                continue

            # Simple similarity: tech stack overlap
            for i, agent1 in enumerate(agents_in_cat):
                for agent2 in agents_in_cat[i + 1 :]:
                    # Skip self-comparison (compare by name AND path for safety)
                    if (agent1.get("name") == agent2.get("name") and 
                        agent1.get("path") == agent2.get("path")):
                        continue
                    
                    tech1 = set(a.strip() for a in agent1.get("tech_stack", []) if a.strip())
                    tech2 = set(a.strip() for a in agent2.get("tech_stack", []) if a.strip())

                    if tech1 and tech2:
                        overlap = len(tech1 & tech2) / max(len(tech1), len(tech2))

                        # Skip 100% overlap with same name (likely duplicates from different processes)
                        if overlap >= 0.99 and agent1.get("name") == agent2.get("name"):
                            continue

                        if overlap >= similarity_threshold:
                            candidates.append({
                                "agent1": agent1["name"],
                                "agent2": agent2["name"],
                                "category": category,
                                "overlap_score": overlap,
                                "shared_techs": list(tech1 & tech2),
                                "recommendation": (
                                    f"Consider merging {agent1['name']} and {agent2['name']} "
                                    f"(share {overlap*100:.0f}% tech stack in {category})"
                                ),
                            })

        # Sort by overlap and limit
        candidates.sort(key=lambda x: x["overlap_score"], reverse=True)
        self.consolidation_candidates = candidates[:max_candidates]

        logger.info("✅ Found %d consolidation candidates", len(self.consolidation_candidates))
        return self.consolidation_candidates

    def generate_report(self, include_details: bool = False) -> str:
        """Generate a comprehensive audit report.

        Args:
            include_details: Include full agent lists

        Returns:
            Formatted report string
        """
        # Ensure analysis is done
        if not self.coverage_analysis:
            self.analyze_coverage()
        if not self.consolidation_candidates:
            self.find_consolidation_candidates()

        report = "\n" + "=" * 80 + "\n"
        report += "🔍 AGENT PORTFOLIO AUDIT REPORT\n"
        report += "=" * 80 + "\n\n"

        # Summary
        coverage = self.coverage_analysis
        report += f"📊 SUMMARY\n"
        report += f"{'─' * 40}\n"
        report += f"Total Agents: {coverage['total_agents']}\n"
        report += f"Categories Represented: {coverage['category_balance']['spread']}\n"
        report += f"Unique Tech Stacks: {len(coverage['top_tech_stacks'])}\n"
        report += f"Consolidation Candidates: {len(self.consolidation_candidates)}\n"
        report += f"Coverage Gaps: {len(coverage['coverage_gaps'])} tech stacks\n\n"

        # Category Balance
        report += f"📈 CATEGORY DISTRIBUTION\n"
        report += f"{'─' * 40}\n"
        for cat, count in sorted(coverage["categories"].items(), key=lambda x: x[1], reverse=True):
            pct = (count / coverage["total_agents"]) * 100
            bar = "█" * int(pct / 5)
            report += f"{cat:20} {count:3d} agents  {pct:5.1f}% {bar}\n"
        report += "\n"

        # Top Tech Stacks
        report += f"🛠️  TOP TECH STACKS\n"
        report += f"{'─' * 40}\n"
        for tech, count in list(coverage["top_tech_stacks"].items())[:8]:
            report += f"{tech:20} {count:3d} agents\n"
        report += "\n"

        # Coverage Gaps
        report += f"⚠️  COVERAGE GAPS (< 2 agents)\n"
        report += f"{'─' * 40}\n"
        if coverage["coverage_gaps"]:
            for tech in coverage["coverage_gaps"][:10]:
                report += f"• {tech}\n"
        else:
            report += "✅ No significant gaps detected\n"
        report += "\n"

        # Consolidation Candidates
        report += f"🔗 CONSOLIDATION CANDIDATES\n"
        report += f"{'─' * 40}\n"
        if self.consolidation_candidates:
            # Load agents for path display
            agents_by_name = {a["name"]: a for a in self.agents}
            
            for i, cand in enumerate(self.consolidation_candidates[:5], 1):
                agent1_name = cand['agent1']
                agent2_name = cand['agent2']
                agent1_path = agents_by_name.get(agent1_name, {}).get("path", agent1_name)
                agent2_path = agents_by_name.get(agent2_name, {}).get("path", agent2_name)
                
                # Extract just the relative path for readability
                agent1_short = agent1_path.replace("/home/ollie/Tools/vibe-tools/", "")
                agent2_short = agent2_path.replace("/home/ollie/Tools/vibe-tools/", "")
                
                report += (
                    f"{i}. {agent1_short} ↔\n   {agent2_short}\n"
                    f"   Overlap: {cand['overlap_score']*100:.0f}% | "
                    f"Shared: {', '.join(cand['shared_techs'][:3])}\n\n"
                )
        else:
            report += "✅ No consolidation needed\n"
        report += "\n"

        # Value Metrics
        report += f"⭐ VALUE ASSESSMENT\n"
        report += f"{'─' * 40}\n"
        report += f"Portfolio Health: {'🟢 Good' if len(self.consolidation_candidates) < 5 else '🟡 Fair' if len(self.consolidation_candidates) < 10 else '🔴 Review'}\n"
        report += f"Specialization: {'🟢 Diverse' if coverage['category_balance']['spread'] >= 8 else '🟡 Moderate' if coverage['category_balance']['spread'] >= 5 else '🔴 Limited'}\n"
        report += f"Tech Coverage: {'🟢 Comprehensive' if len(coverage['top_tech_stacks']) >= 10 else '🟡 Good' if len(coverage['top_tech_stacks']) >= 5 else '🔴 Narrow'}\n"

        report += "\n" + "=" * 80 + "\n"

        return report

    def get_audit_summary(self) -> dict[str, Any]:
        """Get audit results as structured dict.

        Returns:
            Dictionary with audit findings
        """
        if not self.coverage_analysis:
            self.analyze_coverage()
        if not self.consolidation_candidates:
            self.find_consolidation_candidates()

        return {
            "timestamp": None,
            "collection": self.collection_name,
            "coverage": self.coverage_analysis,
            "consolidation_candidates": self.consolidation_candidates,
            "agent_count": len(self.agents),
            "health_score": max(0, 100 - (len(self.consolidation_candidates) * 10)),
        }

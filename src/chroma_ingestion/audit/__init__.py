"""Agent audit and analysis module.

Analyzes ingested agents for quality, coverage, and consolidation opportunities.
"""

from chroma_ingestion.audit.agent_auditor import AgentAuditor

__all__ = ["AgentAuditor"]
